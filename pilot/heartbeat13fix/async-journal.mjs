/** Exact overlap chain/barriers, serialized async IO. Prototype only; no authority. */
import fs from'node:fs/promises';import path from'node:path';import{createHash}from'node:crypto';
export const mono=()=>Number(process.hrtime.bigint())/1e6;
export function createJournal(out,{maxRows=3072,maxBytes=4*2**20,io={},trace=()=>{}}={}){
 if(!Number.isSafeInteger(maxRows)||maxRows<1||maxRows>6144||!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>8*2**20)throw Error('EXACT_EXISTING_JOURNAL_CAPS');
 const file=path.join(out,'overlap-events.jsonl'),ops={open:p=>fs.open(p,'wx',0o600),write:(h,b,o)=>h.write(b,o,b.length-o,null),sync:h=>h.sync(),close:h=>h.close(),...io};
 let fatal=null,closed=false,closing=false,head='0'.repeat(64),bytes=0,reserved=0,pending=0;const rows=[];let tail=Promise.resolve();const handle=ops.open(file);handle.catch(e=>{fatal??=e.message;});
 function healthy(){if(fatal)throw Error('OVERLAP_JOURNAL_POISONED:'+fatal);if(closed||closing)throw Error('OVERLAP_JOURNAL_CLOSED');}
 function enqueue(fn){pending++;const p=tail.then(async()=>{if(fatal)throw Error('OVERLAP_JOURNAL_POISONED:'+fatal);return fn(await handle);});tail=p.catch(e=>{fatal??=e.message;}).finally(()=>pending--);return p;}
 function append(kind,data,durable=false){
  healthy();if(reserved>=maxRows)throw Error('OVERLAP_EVENT_QUOTA');
  const base={seq:reserved+1,hostMonoMs:mono(),kind,data,previousSha256:head},row={...base,sha256:createHash('sha256').update(JSON.stringify(base)).digest('hex')},line=Buffer.from(JSON.stringify(row)+'\n');if(bytes+line.length>maxBytes)throw Error('OVERLAP_JOURNAL_BYTES');reserved++;bytes+=line.length;head=row.sha256;
  return enqueue(async h=>{trace('journal.write.begin',{seq:row.seq});let offset=0,attempts=0;while(offset<line.length){if(++attempts>32)throw Error('SHORT_WRITE_ATTEMPT_BOUND');const r=await ops.write(h,line,offset),n=typeof r==='number'?r:r.bytesWritten;if(!Number.isSafeInteger(n)||n<=0||n>line.length-offset)throw Error('SHORT_OR_ZERO_WRITE');offset+=n;}trace('journal.write.end',{seq:row.seq});if(durable){trace('journal.fsync.begin',{seq:row.seq});await ops.sync(h);trace('journal.fsync.end',{seq:row.seq});}rows.push(row);return{seq:row.seq,sha256:row.sha256};});
 }
 async function flush(){healthy();const r=await enqueue(async h=>{await ops.sync(h);return{head,records:rows.length,bytes};});await tail;return r;}
 function snapshot(){healthy();if(pending)throw Error('JOURNAL_SNAPSHOT_REQUIRES_AWAITED_FLUSH');return structuredClone(rows);}
 async function close(){if(closed){if(fatal)throw Error('OVERLAP_JOURNAL_POISONED:'+fatal);return{head,records:rows.length,bytes};}if(closing)throw Error('JOURNAL_CLOSE_ALREADY_PENDING');closing=true;await tail;let h;try{h=await handle;try{await ops.sync(h);}catch(e){fatal??=e.message;}}finally{if(h)try{await ops.close(h);}catch(e){fatal??=e.message;}closed=true;}if(fatal)throw Error('OVERLAP_JOURNAL_POISONED:'+fatal);return{head,records:rows.length,bytes};}
 return{append,flush,snapshot,close,diagnostics:()=>({pending,reserved,records:rows.length,bytes,fatal,closed,closing,maximumPending:maxRows,maximumQueuedSerializedBytes:maxBytes})};
}
