import {parentPort,workerData} from 'node:worker_threads';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';

const hash=b=>createHash('sha256').update(b).digest('hex');
const mono=()=>Number(process.hrtime.bigint())/1e6;
const out=workerData.out, maxBytes=workerData.maxBytes;
let head='0'.repeat(64),seq=0,bytes=0,barriers=0,closed=false,fatal=null;
const PHYSICAL_ROWS=1024,RAW_TARGET=1024*1024;let packedRows=[],packedBytes=0,packed=null;
const blocks=[],timing={blocks:0,maxWriteMs:0,maxCompressMs:0,maxFsyncMs:0,maxQueueWaitMs:0,totalWriteMs:0,totalFsyncMs:0};
function save(name,body){if(bytes+body.length>maxBytes)throw Error('TRACE_BYTE_QUOTA');const p=path.join(out,name);const fd=fs.openSync(p,'wx',0o600);try{let at=0;while(at<body.length){const n=fs.writeSync(fd,body,at,body.length-at);if(n<=0)throw Error('TRACE_SHORT_WRITE');at+=n;}}finally{fs.closeSync(fd);}bytes+=body.length;return{file:name,bytes:body.length,sha256:hash(body)};}
function syncFiles(){const t=mono();for(const b of blocks){if(b.durable)continue;const fd=fs.openSync(path.join(out,b.file),'r');try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}b.durable=true;}const fd=fs.openSync(out,'r');try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}const ms=mono()-t;timing.totalFsyncMs+=ms;timing.maxFsyncMs=Math.max(timing.maxFsyncMs,ms);return{startHostMs:t,endHostMs:mono(),durationMs:ms};}
function durableSave(name,body){const r=save(name,body),fd=fs.openSync(path.join(out,name),'r');try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}const d=fs.openSync(out,'r');try{fs.fsyncSync(d);}finally{fs.closeSync(d);}return r;}
function fail(error){fatal=String(error.message??error).slice(0,240);parentPort.postMessage({op:'fatal',fatal,seq,head,bytes});}
function flushPhysical(){
 if(!packedRows.length)return;
 if(workerData.test?.crashAfterBlock===blocks.length+1)process.exit(79);
 const raw=Buffer.from(packedRows.join('\n')+'\n'),ct=mono(),compressed=gzipSync(raw,{level:1}),compressMs=mono()-ct,t=mono();
 if(packedRows.length>PHYSICAL_ROWS||raw.length>2*1024*1024)throw Error('TRACE_PHYSICAL_PACK_BOUND');
 const saved=save('trace-block-'+String(blocks.length+1).padStart(6,'0')+'.jsonl.gz',compressed),writeMs=mono()-t,aggregationWaitMs=ct-packed.workerStartHostMs;
 blocks.push({...saved,rawBytes:raw.length,rawSha256:hash(raw),seqStart:packed.seqStart,seqEnd:packed.seqEnd,previous:packed.previous,head:packed.head,firstHostMs:packed.firstHostMs,lastHostMs:packed.lastHostMs,queueWaitMs:packed.queueWaitMs,compressMs,writeMs,postedHostMs:packed.postedHostMs,workerStartHostMs:packed.workerStartHostMs,compressStartHostMs:ct,writeStartHostMs:t,writeEndHostMs:mono(),aggregationWaitMs,incomingMessages:packed.incomingMessages,durable:false});
 timing.blocks++;timing.maxQueueWaitMs=Math.max(timing.maxQueueWaitMs,packed.queueWaitMs);timing.maxWriteMs=Math.max(timing.maxWriteMs,writeMs);timing.maxCompressMs=Math.max(timing.maxCompressMs,compressMs);timing.maxAggregationWaitMs=Math.max(timing.maxAggregationWaitMs??0,aggregationWaitMs);timing.totalWriteMs+=writeMs;
 const written=packed.seqEnd,writtenHead=packed.head;packedRows=[];packedBytes=0;packed=null;
 parentPort.postMessage({op:'written',seq:written,head:writtenHead,bytes,block:blocks.at(-1),timing});
}
function emitReceipt(label,final=false,mainFatal=null){flushPhysical();const fsyncSpan=syncFiles();const receipt={format:'aeris-betavideo03-full-trace',version:1,scope:'FULL_HOST_TRACE_THROUGH_ACCEPTED_SEQUENCE',label,final,complete:!fatal&&!mainFatal,fatal:fatal??mainFatal,events:seq,head,bytesBeforeReceipt:bytes,blocks:blocks.map(({durable,...b})=>b),timing:{...timing},fsyncSpan,clockDomain:'NODE_HRTIME_MS',physicalPacking:{maximumRows:PHYSICAL_ROWS,rawTargetBytes:RAW_TARGET,maximumRawBytes:2*RAW_TARGET,acknowledgment:'AFTER_PHYSICAL_WRITE_ONLY;DURABILITY_REQUIRES_BARRIER'},at:new Date().toISOString()};const body=Buffer.from(JSON.stringify(receipt)+'\n');const name=final?'trace-closure.json':'trace-barrier-'+String(++barriers).padStart(5,'0')+'.json';const saved=durableSave(name,body);return{...saved,receipt};}
let operationChain=Promise.resolve();
parentPort.on('message',m=>{operationChain=operationChain.then(async()=>{try{
 if(closed)throw Error('TRACE_WORKER_CLOSED');
 if(m.op==='block'){
  if(fatal)throw Error(fatal);if(workerData.test?.delayMs)await new Promise(r=>setTimeout(r,workerData.test.delayMs));
  if(!Array.isArray(m.events)||m.events.length<1||m.events.length>128)throw Error('TRACE_INCOMING_MESSAGE_BOUND');
  const workerStartHostMs=mono(),queueWaitMs=workerStartHostMs-m.postedHostMs,previous=head,first=seq+1,rows=[];let nextHead=head,nextSeq=seq,rawBytes=0;
  for(const event of m.events){if(event.seq!==nextSeq+1)throw Error('TRACE_WORKER_SEQUENCE');const row={...event,previous:nextHead},sha256=hash(JSON.stringify(row)),line=JSON.stringify({...row,sha256});rows.push(line);rawBytes+=Buffer.byteLength(line)+1;nextHead=sha256;nextSeq++;}
  // Flush the previous physical pack BEFORE adding a message that would exceed
  // the row/raw target. The <=128-row incoming message itself is never split,
  // lost or acknowledged as written before its immutable gzip exists.
  if(packedRows.length&&(packedRows.length+rows.length>PHYSICAL_ROWS||packedBytes+rawBytes>RAW_TARGET))flushPhysical();
  if(rawBytes>2*RAW_TARGET)throw Error('TRACE_INCOMING_RAW_BOUND');
  if(!packed)packed={seqStart:first,previous,firstHostMs:m.events[0].hostMonoMs,postedHostMs:m.postedHostMs,workerStartHostMs,queueWaitMs,incomingMessages:0};
  packedRows.push(...rows);packedBytes+=rawBytes;seq=nextSeq;head=nextHead;Object.assign(packed,{seqEnd:seq,head,lastHostMs:m.events.at(-1).hostMonoMs,queueWaitMs:Math.max(packed.queueWaitMs,queueWaitMs),incomingMessages:packed.incomingMessages+1});
  if(packedRows.length>=PHYSICAL_ROWS||packedBytes>=RAW_TARGET)flushPhysical();
 }else if(m.op==='barrier'||m.op==='close'){
  const result=emitReceipt(m.label,m.op==='close',m.mainFatal);parentPort.postMessage({op:'receipt',id:m.id,...result});
  if(m.op==='close'){closed=true;parentPort.close();}
 }else throw Error('TRACE_WORKER_OPERATION');
}catch(error){fail(error);}});});
parentPort.postMessage({op:'ready'});
