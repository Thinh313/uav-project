/** Planning-only bounded fetch seam. NOT loaded by app or used in ended run. */
export async function boundedLifeJson(fetcher,url,options,{deadlineMs=1000,setTimer=setTimeout,clearTimer=clearTimeout,onEvent=()=>{},Controller=AbortController}={}){
 if(!Number.isFinite(deadlineMs)||deadlineMs<=0||deadlineMs>1000)throw Error('LIFECYCLE_DEADLINE_MAX1000');
 const controller=new Controller();let timer,done=false;onEvent({kind:'REQUEST_BEGIN',deadlineMs});
 const timeout=new Promise((_,reject)=>{timer=setTimer(()=>{if(done)return;onEvent({kind:'REQUEST_DEADLINE'});controller.abort();reject(Error('LIFECYCLE_REQUEST_DEADLINE'));},deadlineMs);});
 // No session mutation in this inner promise: a late fetch/body cannot commit state after timeout.
 const response=(async()=>{const r=await fetcher(url,{...options,signal:controller.signal});const v=await r.json();if(!r.ok||!v?.ok)throw Error(v?.error??'LIFECYCLE_HTTP_OR_JSON_REJECTED');return v;})();
 try{const v=await Promise.race([response,timeout]);done=true;onEvent({kind:'REQUEST_ACK'});return v;}catch(e){done=true;onEvent({kind:'REQUEST_FAILED',error:String(e.message??e).slice(0,128)});throw e;}finally{done=true;clearTimer(timer);}
}
