/** One full frozen G15 scan per message. No test hooks, caches, retries or changed policy. */
import {parentPort} from 'node:worker_threads';
import {scan,POLICY,policySha256} from '../beta06g15/quota.mjs';
let busy=false;
parentPort.on('message',async message=>{
  if(busy)throw Error('QUOTA_WORKER_OVERLAP');
  busy=true;
  const start=performance.now();
  try{
    if(!message||Object.keys(message).sort().join()!=='id,policySha256,verifyHashes'||!Number.isSafeInteger(message.id)||message.id<1||typeof message.verifyHashes!=='boolean'||message.policySha256!==policySha256)throw Error('QUOTA_WORKER_REQUEST');
    const usage=await scan({verifyHashes:message.verifyHashes});
    const result=JSON.stringify({id:message.id,policySha256,historySha256:POLICY.history.sha256,verifyHashes:message.verifyHashes,workerDurationMs:performance.now()-start,usage});
    if(Buffer.byteLength(result)>64*1024)throw Error('QUOTA_WORKER_RESULT_BYTES');
    parentPort.postMessage(result);
  }catch(error){parentPort.postMessage(JSON.stringify({id:message?.id,error:String(error.message).slice(0,512)}));}
  finally{busy=false;}
});
