// Storage only. Never a flight/payload transport. No fallback to localStorage.
const pending=new Map();
export const nativeTransport=typeof window.Native82Bridge?.request==='function';
window.native82Result=(id,raw)=>{const p=pending.get(id);if(!p)return;pending.delete(id);clearTimeout(p.timer);try{p.resolve(JSON.parse(raw));}catch(e){p.reject(e);}};
export async function storage82(action,token,body){
 if(!['save','load','export','import','activate','fresh','review-load'].includes(action)&&!action.startsWith('sitl:'))throw Error('STORAGE_ACTION_ONLY');
 if(nativeTransport)return new Promise((resolve,reject)=>{
  const id=crypto.randomUUID(),timer=setTimeout(()=>{pending.delete(id);reject(Error('NATIVE_COMMIT_UNKNOWN_NO_RETRY'));},60000);
  pending.set(id,{resolve,reject,timer});
  window.Native82Bridge.request(id,action,token,body);
 });
 const r=await fetch(action==='load'?'/workspace/load':'/workspace/save',action==='load'?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,body})});
 const d=await r.json();if(!r.ok||!d.ok)throw Error(d.error??'JOURNAL_UNAVAILABLE');return d;
}
