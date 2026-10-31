// Data-only Android broker. No vehicle transport or restored flight authority.
const encoder=new TextEncoder();
export const shaBytes=async s=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(s)))].map(x=>x.toString(16).padStart(2,'0')).join('');
const need=(x,m)=>{if(!x)throw Error(m);};
export class NativeChannel{
 constructor(provider,{timeoutMs=120000,timers=globalThis}={}){this.provider=provider;this.timeoutMs=timeoutMs;this.timers=timers;this.pending=new Map();this.seq=0;this.closed=false;}
 call(action,args={}){
  need(!this.closed,'NATIVE_CHANNEL_CLOSED');need(['load','save','export','pick-json','pick-kml'].includes(action),'NATIVE_ACTION');
  const env=JSON.parse(this.provider().environment());need(env.format==='aeris-native-workbench02'&&['ANDROID','MOCK_NATIVE_BRIDGE'].includes(env.platform)&&env.foreground===true,'NATIVE_FOREGROUND_REQUIRED');
  need(typeof env.instance==='string'&&typeof env.session==='string'&&env.session.length>=16,'NATIVE_ENVIRONMENT');need(this.pending.size===0,'NATIVE_BUSY_NO_QUEUE');
  const id=env.instance+':'+(++this.seq),request={version:1,id,instance:env.instance,session:env.session,action,args};need(encoder.encode(JSON.stringify(request)).length<=3145728,'NATIVE_REQUEST_BOUND');
  return new Promise((resolve,reject)=>{const timer=this.timers.setTimeout(()=>{this.pending.delete(id);reject(Error('NATIVE_RESULT_UNKNOWN_TIMEOUT_NO_RETRY'));},this.timeoutMs);this.pending.set(id,{request,platform:env.platform,timer,resolve,reject});try{this.provider().request(JSON.stringify(request));}catch(e){this.pending.delete(id);this.timers.clearTimeout(timer);reject(e);}});
 }
 reply(r){const p=this.pending.get(r?.id);if(!p)return false;if(r.version!==1||r.instance!==p.request.instance||r.session!==p.request.session||r.action!==p.request.action)return false;this.pending.delete(r.id);this.timers.clearTimeout(p.timer);if(r.ok!==true)p.reject(Error(r.error??'NATIVE_REFUSED'));else if(r.result?.authorityRestored!==false||r.result?.platform!==p.platform)p.reject(Error('NATIVE_AUTHORITY_RESTORE_REFUSED'));else p.resolve(r.result);return true;}
 background(pickerOwned=false){for(const [id,p]of this.pending){if(pickerOwned&&['export','pick-json','pick-kml'].includes(p.request.action))continue;this.timers.clearTimeout(p.timer);p.reject(Error('NATIVE_RESULT_UNKNOWN_FOREGROUND_LOST'));this.pending.delete(id);}}
 close(){this.background();this.closed=true;}
}
export class NativeStorage{
 constructor(channel){this.channel=channel;this.head=null;}
 async load(){const r=await this.channel.call('load');need(['EMPTY','COMMITTED'].includes(r.status),'NATIVE_PENDING_OR_CORRUPT_READONLY');need(r.status==='EMPTY'?r.head==='ROOT'&&r.body===null:/^[a-f0-9]{64}$/.test(r.head)&&typeof r.body==='string','NATIVE_HEAD');if(r.body!==null){need(typeof r.body==='string'&&encoder.encode(r.body).length<=2097152,'NATIVE_BODY_BOUND');need(await shaBytes(r.body)===r.bodySha256,'NATIVE_LOAD_SHA');}this.head=r.head;return r;}
 async save(body){need(this.head!==null,'NATIVE_LOAD_BEFORE_SAVE');need(encoder.encode(body).length<=2097152,'NATIVE_BODY_BOUND');const expected=await shaBytes(body),oldHead=this.head;const r=await this.channel.call('save',{body,expectedHead:oldHead,bodySha256:expected});need(r.status==='COMMITTED'&&r.bodySha256===expected&&r.previousHead===oldHead&&/^[a-f0-9]{64}$/.test(r.head),'NATIVE_COMMIT_RECEIPT');this.head=r.head;return r;}
 async export(body){need(encoder.encode(body).length<=2097152,'NATIVE_BODY_BOUND');const expected=await shaBytes(body),r=await this.channel.call('export',{body,bodySha256:expected});need(r.status===(r.platform==='ANDROID'?'SAF_READBACK_VERIFIED':'MOCK_SAF_READBACK_ONLY')&&r.bodySha256===expected&&r.bytes===encoder.encode(body).length,'NATIVE_SAF_READBACK');return r;}
 async pick(kind){need(['workspace','kml'].includes(kind),'NATIVE_PICK_KIND');const r=await this.channel.call(kind==='kml'?'pick-kml':'pick-json');need(r.status==='PICK_READ_VERIFIED'&&typeof r.body==='string'&&encoder.encode(r.body).length<=(kind==='kml'?262144:2097152)&&await shaBytes(r.body)===r.bodySha256,'NATIVE_PICK_SHA_BOUND');return r.body;}
}
export function createNativeStorage(){const channel=new NativeChannel(()=>{if(!window.NativeWB02)throw Error('ANDROID_BRIDGE_REQUIRED_NO_LOCALSTORAGE_FALLBACK');return window.NativeWB02;});window.nativeWB02Reply=r=>channel.reply(r);window.addEventListener('wb-native-background',e=>channel.background(e.detail?.pickerOwned===true));return new NativeStorage(channel);}
