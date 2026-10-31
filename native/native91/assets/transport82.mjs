// Storage only. Never a flight/payload transport. No fallback to localStorage.
const pending=new Map();
export const nativeTransport=typeof window.Native82Bridge?.request==='function';
window.native82Result=(id,raw)=>{const p=pending.get(id);if(!p)return;pending.delete(id);clearTimeout(p.timer);try{p.resolve(JSON.parse(raw));}catch(e){p.reject(e);}};
export async function storage82(action,token,body){
 if(!['bundle-export88','bundle-status88','file-status87','file-reconcile87','save','load','export','import','activate','fresh','review-load','review-list','review-get'].includes(action)&&!action.startsWith('sitl:')&&!action.startsWith('diag91:'))throw Error('STORAGE_ACTION_ONLY');
 if(nativeTransport)return new Promise((resolve,reject)=>{
  const id=crypto.randomUUID(),timer=setTimeout(()=>{pending.delete(id);reject(Error(['export','import','file-reconcile87','bundle-export88'].includes(action)?'FILE_OPERATION_PENDING_READ_STATUS_NO_RETRY':'NATIVE_COMMIT_UNKNOWN_NO_RETRY'));},60000);
  pending.set(id,{resolve,reject,timer});
  window.Native82Bridge.request(id,action,token,body);
 });
 // Preview history is a read-only, SHA-preserved NATIVE84 archive. No live telemetry or authority.
 if(document.body.dataset.qa85==='browser'&&['review-list','review-get'].includes(action)){
  const q=JSON.parse(body),u=new URL('/qa85/history',location.origin);u.searchParams.set('action',action);if(q.token)u.searchParams.set('token',q.token);if(q.head)u.searchParams.set('head',q.head);
  const response=await fetch(u);const data=await response.json();if(!response.ok)throw Error(data.error);return data;
 }
 const r=await fetch(action==='load'?'/workspace/load':'/workspace/save',action==='load'?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,body})});
 const d=await r.json();if(!r.ok||!d.ok)throw Error(d.error??'JOURNAL_UNAVAILABLE');return d;
}
