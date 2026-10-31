import{exact,num,str,canonical,digest,fail,isHash}from'./vendor/common.mjs';
export{exact,num,str,canonical,digest,fail,isHash};
export const int=(v,lo,hi,label)=>{num(v,lo,hi,label);if(!Number.isSafeInteger(v))fail(label+' integer');return v};
export function identity(v){exact(v,['vehicle','system','component','session','boot','link'],'target identity');for(const k of ['vehicle','session','boot','link'])str(v[k],80);int(v.system,1,255,'system');int(v.component,1,255,'component');return v}
export const same=(a,b)=>canonical(a)===canonical(b);
export const clock=v=>{exact(v,['epoch','nowMs'],'clock');str(v.epoch);int(v.nowMs,0,1e12,'nowMs');return v};
export function bounded(v,bytes){if(new TextEncoder().encode(JSON.stringify(v)).length>bytes)fail('byte bound');return v}
export function observation(o,target,c,maxAgeMs,unit){
 exact(o,['origin','sourceId','target','epoch','sequence','atMs','unit','value'],'observation');if(o.origin!=='SYNTHETIC')fail('real source not integrated');str(o.sourceId);identity(o.target);int(o.sequence,0,1e12,'source sequence');int(o.atMs,0,1e12,'observation time');if(o.unit!==unit)fail('unit mismatch');if(!same(target,o.target)||o.epoch!==c.epoch)fail('identity/clock epoch');if(o.atMs>c.nowMs||c.nowMs-o.atMs>maxAgeMs)fail('source stale/future');return o.value;
}
export function modelMargin(origin,extent){return Math.round((1+.007*extent+2*extent*extent*(1+Math.abs(Math.tan(origin[1]*Math.PI/180)))/6371008.8)*1000)/1000+.001}
export const ACTIONS=['NONE','WARN_ONLY','HOLD','RTL','LAND','CONTINUE_AUTO'];
export const action=v=>{if(!ACTIONS.includes(v))fail('unsupported normalized action');return v};
