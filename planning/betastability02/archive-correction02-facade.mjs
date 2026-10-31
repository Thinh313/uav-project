/** Proposal facade. Queue length zero, one active operation, terminal failure.
 * Caller keeps archiveBusy across session close -> durable archive. It must not
 * admit other workspace mutations during snapshot. Heartbeat stays available.
 */
import{Worker}from'node:worker_threads';import{performance}from'node:perf_hooks';
export function createArchiveWorker({historyRoot,deadlineMs=15000,onSpan=()=>{},workerURL=new URL('./archive-correction02-worker.mjs',import.meta.url)}={}){
 if(deadlineMs!==15000)throw Error('FIXED_ARCHIVE_WORKER_DEADLINE');let pending=null,closed=false,fatal=null,operationId=0,worker=null;
 async function request(operation,args={}){
  if(closed)throw Error('ARCHIVE_WORKER_CLOSED');if(fatal)throw Error('ARCHIVE_WORKER_FAILED_NO_RETRY:'+fatal);if(pending)throw Error('ARCHIVE_WORKER_BUSY_NO_QUEUE');
  const id=++operationId,start=performance.now();let resolveDrain;const drained=new Promise(r=>{resolveDrain=r;});pending=drained;
  const task=new Promise((resolve,reject)=>{
   let settled=false,timer;
   const finish=(error,result)=>{if(settled)return;settled=true;clearTimeout(timer);if(error){fatal=error.message;reject(error);}else resolve(result);};
   try{worker=new Worker(workerURL,{workerData:{operation,args,historyRoot},resourceLimits:{maxOldGenerationSizeMb:512,stackSizeMb:4}});}catch(e){finish(e);pending=null;resolveDrain();return;}
   timer=setTimeout(()=>finish(Error('ARCHIVE_WORKER_DEADLINE_UNCERTAIN_NO_RETRY')),deadlineMs);
   worker.once('message',m=>{if(!m||typeof m.ok!=='boolean')return finish(Error('ARCHIVE_WORKER_RESPONSE_SCHEMA'));onSpan({operation,id,durationMs:performance.now()-start,spans:m.spans??[],ok:m.ok});if(!m.ok)return finish(Error(m.error??'ARCHIVE_WORKER_FAILED'));if(m.result?.bytes)m.result.bytes=Buffer.from(m.result.bytes);finish(null,m.result);});
   worker.once('error',e=>finish(e));
   worker.once('exit',code=>{finish(Error('ARCHIVE_WORKER_EXIT_WITHOUT_RESULT_'+code));worker=null;pending=null;resolveDrain();});
  });
  return task;
 }
 return{
  archive:args=>request('archive',args),read:run=>request('read',{run}),list:()=>request('list'),quality:run=>request('quality',{run}),
  snapshot:()=>({busy:!!pending,closed,fatal,operationId,authorityRestorable:false}),
  async close(){closed=true;if(pending)await pending;return{closed:true,fatal,operationId,authorityRestorable:false};}
 };
}
