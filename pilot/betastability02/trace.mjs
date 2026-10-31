import {Worker} from 'node:worker_threads';
import fs from 'node:fs';
import path from 'node:path';

const mono=()=>Number(process.hrtime.bigint())/1e6;
export function boundedTraceData(value){
 let nodes=0;
 const visit=(v,depth)=>{if(++nodes>1024||depth>10)throw Error('TRACE_DATA_COMPLEXITY');if(v===null||typeof v==='boolean')return;if(typeof v==='number'){if(!Number.isFinite(v))throw Error('TRACE_DATA_NUMBER');return;}if(typeof v==='string'){if(v.length>4096)throw Error('TRACE_DATA_STRING');return;}if(typeof v!=='object'||!Array.isArray(v)&&Object.getPrototypeOf(v)!==Object.prototype)throw Error('TRACE_DATA_TYPE');if(Array.isArray(v)){if(v.length>256)throw Error('TRACE_DATA_ARRAY');for(const q of v)visit(q,depth+1);}else{if(Object.keys(v).length>96)throw Error('TRACE_DATA_KEYS');for(const[k,q]of Object.entries(v)){if(k.length>96||['__proto__','prototype','constructor'].includes(k))throw Error('TRACE_DATA_KEY');visit(q,depth+1);}}};
 visit(value,0);const encoded=JSON.stringify(value);if(Buffer.byteLength(encoded)>8192)throw Error('TRACE_EVENT_BYTES');return JSON.parse(encoded);
}
/** Reject untrusted source/viewer batches before appending. The authenticated route
 * also owns producer sequence and timestamp/clock checks, not this generic codec. */
export function validateTraceBatch(q,{role,session,serverBoot}={}){
 if(!q||Object.keys(q).sort().join(',')!=='configId,events,serverBoot,traceId,version'||q.version!==1||!/^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(q.traceId??'')||q.serverBoot!==serverBoot||q.configId!==session?.configId||!['publisher','viewer'].includes(role)||!Array.isArray(q.events)||q.events.length<1||q.events.length>128)throw Error('TRACE_BATCH_CONTEXT');
 return q.events.map(e=>{if(!e||Object.keys(e).sort().join(',')!=='atMs,data,kind,seq'||!Number.isSafeInteger(e.seq)||e.seq<1||!Number.isFinite(e.atMs)||e.atMs<0||!/^\w{1,64}$/.test(e.kind)||!e.kind.startsWith(role==='viewer'?'VIEWER_':'SOURCE_'))throw Error('TRACE_BATCH_EVENT');return{seq:e.seq,kind:e.kind,atMs:e.atMs,data:boundedTraceData(e.data)};});
}
/** Full-stream bounded recorder. append is synchronous and does no disk IO or hash.
 * A worker compresses/writes immutable blocks. Only explicit barriers fsync. */
export function createTrace({out,maxBytes=64*2**20,maxPending=4096,blockRows=128,flushMs=100,_test=null}={}){
 if(!out||!Number.isSafeInteger(maxBytes)||maxBytes<1024||maxBytes>64*2**20||!Number.isSafeInteger(maxPending)||maxPending<1||maxPending>4096||!Number.isSafeInteger(blockRows)||blockRows<1||blockRows>128||!Number.isFinite(flushMs)||flushMs<1||flushMs>1000)throw Error('TRACE_OPTIONS');
 if(_test&&process.env.AERIS_TRACE_TEST!=='1')throw Error('TRACE_TEST_HOOK_FORBIDDEN');
 fs.mkdirSync(out,{recursive:false});out=path.resolve(out);
 const worker=new Worker(new URL('./trace-worker.mjs',import.meta.url),{workerData:{out,maxBytes,test:_test}});
 let accepted=0,written=0,head='0'.repeat(64),bytes=0,fatal=null,closing=false,closed=false,pending=[],timer=null,request=0,ready=false,dead=false,queueBytes=0;
 const jobs=new Map(),timings={};
 const fail=reason=>{if(!fatal)fatal=String(reason).slice(0,240);for(const{id,reject}of jobs.values())reject(Error(fatal));jobs.clear();};
 worker.on('message',m=>{if(m.op==='ready'){ready=true;}else if(m.op==='fatal')fail(m.fatal);else if(m.op==='written'){written=m.seq;head=m.head;bytes=m.bytes;Object.assign(timings,m.timing);}else if(m.op==='receipt'){const job=jobs.get(m.id);if(job){jobs.delete(m.id);if(!m.receipt.complete){fatal??=m.receipt.fatal??'TRACE_INCOMPLETE';job.reject(Object.assign(Error(fatal),{receipt:m}));}else job.resolve(m);}}});
 worker.on('error',e=>fail('TRACE_WORKER_ERROR:'+e.message));worker.on('exit',code=>{dead=true;if(!closed&&(!closing||code!==0))fail('TRACE_WORKER_EXIT:'+code);});
 const flush=()=>{if(timer!==null){clearTimeout(timer);timer=null;}if(!pending.length)return;const events=pending;pending=[];queueBytes=0;worker.postMessage({op:'block',events,postedHostMs:mono()});};
 const snapshot=()=>({format:'aeris-betastability02-trace-live',ready,accepted,written,pending:accepted-written,buffered:pending.length,bufferedBytes:queueBytes,head,bytes,fatal,closing,closed,timing:{...timings},scope:'LIVE_NOT_DURABLE_UNTIL_BARRIER'});
 function append(kind,data){
  if(fatal)throw Error(fatal);if(closing||closed)throw Error('TRACE_CLOSED');
  if(typeof kind!=='string'||!/^[A-Z][A-Z0-9_]{0,63}$/.test(kind))throw Error('TRACE_KIND');
  if(accepted-written>=maxPending){fail('TRACE_PENDING_OVERFLOW');throw Error(fatal);}
  const safe=boundedTraceData(data),event={seq:++accepted,hostMonoMs:mono(),kind,data:safe};pending.push(event);queueBytes+=Buffer.byteLength(JSON.stringify(event));
  if(pending.length>=blockRows)flush();else if(timer===null){timer=setTimeout(flush,flushMs);timer.unref();}
  return accepted;
 }
 function barrier(label='EXPLICIT_BARRIER'){
  if(closing||closed)throw Error('TRACE_CLOSED');if(fatal)return Promise.reject(Error(fatal));if(typeof label!=='string'||label.length>160)throw Error('TRACE_LABEL');flush();const id=++request;
  return new Promise((resolve,reject)=>{jobs.set(id,{id,resolve,reject});worker.postMessage({op:'barrier',id,label,mainFatal:fatal});});
 }
 async function close(label='EXPLICIT_CLOSE'){
  if(closed)throw Error('TRACE_ALREADY_CLOSED');if(dead)throw Error(fatal??'TRACE_WORKER_DEAD');if(closing)throw Error('TRACE_CLOSE_PENDING');closing=true;flush();const id=++request;
  try{return await new Promise((resolve,reject)=>{jobs.set(id,{id,resolve,reject});worker.postMessage({op:'close',id,label,mainFatal:fatal});});}finally{closed=true;if(timer!==null)clearTimeout(timer);await worker.terminate();}
 }
 return{append,barrier,close,snapshot,..._test?{testTerminate:()=>worker.terminate()}: {}};
}
