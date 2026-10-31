/** Zero queued jobs. One operation on a bounded worker; failure never retried.
 * All mutable-workspace admission stays with the caller. Timed-out jobs remain
 * uncertain and are drained or terminated only by explicit host closure.
 */
import{Worker}from'node:worker_threads';import{performance}from'node:perf_hooks';
export function createArchiveWorker({historyRoot,onSpan=()=>{},workerURL=new URL('./archive-worker.mjs',import.meta.url),deadlineMs=15000}={}){
 if(deadlineMs!==15000)throw Error('FIXED_ARCHIVE_WORKER_DEADLINE');let pending=null,worker=null,closed=false,fatal=null,operationId=0;
 async function request(operation,args={}){
  if(closed)throw Error('ARCHIVE_WORKER_CLOSED');if(fatal)throw Error('ARCHIVE_WORKER_FAILED_NO_RETRY:'+fatal);if(pending)throw Error('ARCHIVE_WORKER_BUSY_NO_QUEUE');
  const id=++operationId,start=performance.now();let drain;pending=new Promise(r=>{drain=r;});
  return new Promise((resolve,reject)=>{
   let settled=false,response=null,error=null,timer;
   const fail=(e,terminal=true)=>{error??=e;if(terminal)fatal??=e.message;if(!settled){settled=true;clearTimeout(timer);reject(e);}};
   try{worker=new Worker(workerURL,{workerData:{operation,args,historyRoot},resourceLimits:{maxOldGenerationSizeMb:512,stackSizeMb:4}});}catch(e){pending=null;drain();fail(e);return;}
   timer=setTimeout(()=>fail(Error('ARCHIVE_WORKER_DEADLINE_UNCERTAIN_NO_RETRY')),deadlineMs);
   worker.once('message',m=>{if(response)return fail(Error('ARCHIVE_WORKER_DUPLICATE_RESPONSE'));if(!m||typeof m.ok!=='boolean')return fail(Error('ARCHIVE_WORKER_RESPONSE_SCHEMA'));response=m;try{onSpan({operation,id,durationMs:performance.now()-start,spans:m.spans??[],ok:m.ok});}catch(e){fail(e);}if(!m.ok){error=Error(m.error??'ARCHIVE_WORKER_FAILED');if(operation==='archive')fatal??=error.message;}});
   worker.once('error',fail);
   worker.once('exit',code=>{
    clearTimeout(timer);worker=null;pending=null;drain();
    if(code!==0&&!error)fail(Error('ARCHIVE_WORKER_EXIT_'+code));
    if(!response&&!error)fail(Error('ARCHIVE_WORKER_EXIT_WITHOUT_RESULT'));
    if(error&&!settled){settled=true;reject(error);}
    if(!settled&&!error){settled=true;if(response.result?.bytes)response.result.bytes=Buffer.from(response.result.bytes);resolve(response.result);}
   });
  });
 }
 async function idle(){if(!pending)return;let t;try{await Promise.race([pending,new Promise((_,reject)=>{t=setTimeout(()=>reject(Error('ARCHIVE_WORKER_DRAIN_DEADLINE')),15000);})]);}finally{clearTimeout(t);}}
 return{
  archive:args=>request('archive',args),qualify:args=>request('qualify',args),read:run=>request('read',{run}),list:()=>request('list'),quality:run=>request('quality',{run}),idle,
  snapshot:()=>({busy:!!pending,closed,fatal,operationId,authorityRestorable:false}),
  async close(){closed=true;try{await idle();}catch(e){fatal??=e.message;await worker?.terminate();throw Error('ARCHIVE_WORKER_CLOSE_UNCERTAIN_RETAIN_FILES');}return{closed:true,fatal,operationId,authorityRestorable:false};}
 };
}
