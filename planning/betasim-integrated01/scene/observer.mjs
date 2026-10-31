/** Read-only scene contract. No transport, flight command or authority API. */
const CONTEXT=['run','epoch','boot','profileId'];
export const need=(v,e)=>{if(!v)throw Error(e);};
const natural=(x,max=0xffffffff)=>Number.isSafeInteger(x)&&x>=0&&x<=max;
const vector=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(x=>typeof x==='number'&&Number.isFinite(x));
export function ns(value){need(typeof value==='string'&&/^(0|[1-9][0-9]{0,18})$/.test(value),'SCENE_CLOCK_ENCODING');const n=BigInt(value);need(n<2n**63n,'SCENE_CLOCK_RANGE');return n;}
export function eventTransportAge({receivedBrowserMs,serverSentNodeMs,clock}){
 need(typeof receivedBrowserMs==='number'&&Number.isFinite(receivedBrowserMs)&&typeof serverSentNodeMs==='number'&&Number.isFinite(serverSentNodeMs)&&clock&&['lowerMs','upperMs','sampledBrowserMs','validUntilBrowserMs','roundtripMs'].every(k=>typeof clock[k]==='number'&&Number.isFinite(clock[k])),'SCENE_EVENT_CLOCK_UNQUALIFIED');
 need(clock.upperMs>=clock.lowerMs&&clock.upperMs-clock.lowerMs<=20&&clock.roundtripMs>=0&&clock.roundtripMs<=20&&clock.validUntilBrowserMs-clock.sampledBrowserMs===60000&&receivedBrowserMs>=clock.sampledBrowserMs&&receivedBrowserMs<clock.validUntilBrowserMs,'SCENE_EVENT_CLOCK_EXPIRED_OR_WIDE');
 const age=receivedBrowserMs+clock.upperMs-serverSentNodeMs;need(age>=0&&age<=250,'SCENE_EVENT_DELAYED_OR_FUTURE');return age;
}
function context(c){need(c&&typeof c==='object'&&!Array.isArray(c)&&Object.keys(c).sort().join(',')===CONTEXT.slice().sort().join(',')&&CONTEXT.every(k=>typeof c[k]==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(c[k])),'SCENE_CONTEXT');return c;}
function deepFreeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(deepFreeze);Object.freeze(x);}return x;}
export function validateFrame(input,binding,{mode='LIVE',sourceBinding=null}={}){
 const f=structuredClone(input);context(binding);context(f?.context);
 need(f?.format==='aeris-sim-scene-frame'&&f.version===1&&f.mode===mode&&['LIVE','SCENE_FIXTURE'].includes(mode),'SCENE_SOURCE_KIND');
 need(typeof f.relayAgeUpperMs==='number'&&Number.isFinite(f.relayAgeUpperMs)&&f.relayAgeUpperMs>=0&&f.relayAgeUpperMs<=60000,'SCENE_RELAY_AGE_UNQUALIFIED');
 need(f.poseSource===(mode==='LIVE'?'ROOT_DURABLE_FDM_STATE':'EXPLICIT_GRAPHICS_FIXTURE'),'SCENE_NOT_FDM_POSE_SOURCE');
 if(mode==='LIVE'){
  const keys=['backendSourceSHA256','modelSourceSHA256','profileSHA256','journalPolicySHA256'];
  need(sourceBinding&&f.sourceBinding&&keys.every(k=>typeof sourceBinding[k]==='string'&&/^[a-f0-9]{64}$/.test(sourceBinding[k])&&f.sourceBinding[k]===sourceBinding[k])&&Object.keys(f.sourceBinding).sort().join(',')===keys.slice().sort().join(','),'SCENE_UNSELECTED_SOURCE_BINDING');
 }
 need(CONTEXT.every(k=>f.context[k]===binding[k]),'SCENE_FOREIGN_CONTEXT');
 need(natural(f.frame)&&typeof f.simulationTimeS==='number'&&Number.isFinite(f.simulationTimeS)&&f.simulationTimeS>=0,'SCENE_FRAME_OR_SIM_TIME');
 const sample=ns(f.sampleHostNs),commit=ns(f.committedHostNs),now=ns(f.rootNowNs);
 need(now>=commit&&commit>=sample,'SCENE_CLOCK_ORDER');
 need(vector(f.positionNedM,3)&&f.positionNedM.every(x=>Math.abs(x)<=1e6),'SCENE_POSITION');
 need(vector(f.quaternionWxyz,4)&&Math.abs(Math.hypot(...f.quaternionWxyz)-1)<=1e-4,'SCENE_UNIT_QUATERNION');
 need(f.rpmEstimated===null||vector(f.rpmEstimated,4)&&f.rpmEstimated.every(x=>x>=0&&x<=100000),'SCENE_RPM');
 const r=f.rawRef;
 need(r&&typeof r.relativePath==='string'&&r.relativePath.length<=240&&!r.relativePath.startsWith('/')&&/^[A-Za-z0-9_./-]+$/.test(r.relativePath)&&!r.relativePath.split('/').some(x=>x==='..'||x===''||x==='.'),'SCENE_RAW_PATH');
 need(natural(r.frame)&&r.frame===f.frame&&natural(r.throughSequence,Number.MAX_SAFE_INTEGER)&&r.throughSequence>0&&natural(r.prefixBytes,Number.MAX_SAFE_INTEGER)&&r.prefixBytes>0&&typeof r.headSHA256==='string'&&/^[a-f0-9]{64}$/.test(r.headSHA256),'SCENE_COMMITTED_RAW_REF');
 need(f.ap&&typeof f.ap==='object','SCENE_AP_OBSERVATION');
 if(f.ap.armed===null)need(f.ap.heartbeatHostNs===null,'SCENE_AP_UNKNOWN');
 else{need(typeof f.ap.armed==='boolean','SCENE_ARMED_OBSERVATION');need(ns(f.ap.heartbeatHostNs)<=now,'SCENE_AP_FUTURE');}
 return deepFreeze(f);
}
export class SceneGate{
 constructor(binding,{mode='LIVE',sourceBinding=null,now=()=>performance.now()}={}){context(binding);this.binding=deepFreeze(structuredClone(binding));this.sourceBinding=deepFreeze(structuredClone(sourceBinding));this.mode=mode;this.now=now;this.frames=[];this.receivedAt=null;this.ageAtReceiveMs=Infinity;this.failure=null;this.active=true;this.lastNow=-Infinity;this.lastRootNowNs=null;}
 time(){const t=this.now();if(typeof t!=='number'||!Number.isFinite(t)||t<this.lastNow){this.failure='SCENE_BROWSER_CLOCK_REGRESSION';throw Error(this.failure);}this.lastNow=t;return t;}
 accept(input,{requestStartedBrowserMs,receivedBrowserMs,eventClock=null,serverSentNodeMs=null}={}){
  const t=this.time();need(this.active&&!this.failure,'SCENE_GATE_CLOSED');
  try{
   let transit;
   if(eventClock!==null){need(requestStartedBrowserMs===undefined&&receivedBrowserMs<=t,'SCENE_EVENT_TRANSPORT_BRACKET');transit=eventTransportAge({receivedBrowserMs,serverSentNodeMs,clock:eventClock});}
   else{need(typeof requestStartedBrowserMs==='number'&&typeof receivedBrowserMs==='number'&&Number.isFinite(requestStartedBrowserMs)&&Number.isFinite(receivedBrowserMs)&&requestStartedBrowserMs<=receivedBrowserMs&&receivedBrowserMs<=t,'SCENE_TRANSPORT_BRACKET');transit=receivedBrowserMs-requestStartedBrowserMs;}
   const f=validateFrame(input,this.binding,{mode:this.mode,sourceBinding:this.sourceBinding}),last=this.frames.at(-1);
   need(this.lastRootNowNs===null||ns(f.rootNowNs)>=this.lastRootNowNs,'SCENE_ROOT_CLOCK_REGRESSION');this.lastRootNowNs=ns(f.rootNowNs);
   // A latest-slot poll can legitimately repeat a frame. It must never renew
   // the pose timestamp or turn an unchanged old pose into fresh data.
   if(last&&f.frame===last.frame){
    need(f.simulationTimeS===last.simulationTimeS&&f.sampleHostNs===last.sampleHostNs&&f.committedHostNs===last.committedHostNs&&['positionNedM','quaternionWxyz','rpmEstimated','rawRef'].every(k=>JSON.stringify(f[k])===JSON.stringify(last[k])),'SCENE_MUTATED_DUPLICATE');
    return last;
   }
   need(!last||f.frame>last.frame&&f.simulationTimeS>last.simulationTimeS&&ns(f.sampleHostNs)>ns(last.sampleHostNs),'SCENE_REPLAY_OR_CLOCK_REGRESSION');
   need(!last||f.rawRef.throughSequence>last.rawRef.throughSequence,'SCENE_RAW_SEQUENCE_REGRESSION');
   need(!last||f.rawRef.relativePath!==last.rawRef.relativePath||f.rawRef.prefixBytes>last.rawRef.prefixBytes,'SCENE_RAW_PREFIX_REGRESSION');
   const age=Number(ns(f.rootNowNs)-ns(f.sampleHostNs))/1e6+f.relayAgeUpperMs+transit+(t-receivedBrowserMs);
   need(age>=0&&age<=250,'SCENE_STALE_250MS');
   if(last&&ns(f.sampleHostNs)-ns(last.sampleHostNs)>250_000_000n)this.frames=[];
   this.frames.push(f);if(this.frames.length>8)this.frames.shift();this.receivedAt=t;this.ageAtReceiveMs=age;return f;
  }catch(e){this.failure=e.message;throw e;}
 }
 state(){const t=this.time(),age=this.receivedAt===null?Infinity:this.ageAtReceiveMs+t-this.receivedAt,frame=this.frames.at(-1)??null,fresh=this.active&&!this.failure&&age<=250;let apFresh=false;
  if(frame&&frame.ap.armed!==null)apFresh=Number(ns(frame.rootNowNs)-ns(frame.ap.heartbeatHostNs))/1e6+(this.ageAtReceiveMs-Number(ns(frame.rootNowNs)-ns(frame.sampleHostNs))/1e6)+(t-this.receivedAt)<=1500;
  return{fresh,ageUpperMs:age,frame,apFresh,mode:this.mode,failure:this.failure,flightAuthority:false};
 }
 /** Visual interpolation only; original frames and physics remain unchanged. */
 pose({delayMs=100}={}){
  need(typeof delayMs==='number'&&delayMs>=0&&delayMs<=150,'SCENE_DISPLAY_DELAY');const s=this.state();if(!s.frame)return null;
  const source=this.frames,latest=s.frame;
  const target=ns(latest.rootNowNs)+BigInt(Math.floor((this.time()-this.receivedAt-delayMs)*1e6));
  let a=source[0],b=a;for(const f of source){if(ns(f.sampleHostNs)<=target)a=f;else{b=f;break;}b=f;}
  const span=ns(b.sampleHostNs)-ns(a.sampleHostNs),u=span>0n?Math.max(0,Math.min(1,Number(target-ns(a.sampleHostNs))/Number(span))):0;
  let q=b.quaternionWxyz.slice();if(q.reduce((v,x,i)=>v+x*a.quaternionWxyz[i],0)<0)q=q.map(x=>-x);
  q=q.map((x,i)=>a.quaternionWxyz[i]+(x-a.quaternionWxyz[i])*u);const norm=Math.hypot(...q);q=q.map(x=>x/norm);
  return{position:a.positionNedM.map((x,i)=>x+(b.positionNedM[i]-x)*u),quaternion:q,rpmEstimated:latest.rpmEstimated??[0,0,0,0],renderSourceFrames:[a.frame,b.frame],interpolationFraction:u,displayDelayMs:delayMs,fresh:s.fresh};
 }
 suspend(){this.active=false;}
 resume(){need(!this.failure,'SCENE_FAILURE_REQUIRES_NEW_GATE');this.receivedAt=null;this.ageAtReceiveMs=Infinity;this.active=true;}
 close(){this.active=false;}
}
export const nedToRender=([n,e,d])=>[e,-d,-n];
export function rotateWxyz(q,v){const [w,x,y,z]=q,[a,b,c]=v,tx=2*(y*c-z*b),ty=2*(z*a-x*c),tz=2*(x*b-y*a);return[a+w*tx+y*tz-z*ty,b+w*ty+z*tx-x*tz,c+w*tz+x*ty-y*tx];}
export function cameraBasisNed(quaternionWxyz,{pitchDeg=-90,yawDeg=0,mountFrdM=[0,0,.1]}={}){
 need(vector(quaternionWxyz,4)&&Math.abs(Math.hypot(...quaternionWxyz)-1)<=1e-4&&vector(mountFrdM,3),'CAMERA_EXTRINSICS');
 need(typeof pitchDeg==='number'&&Number.isFinite(pitchDeg)&&pitchDeg>=-90&&pitchDeg<=30&&typeof yawDeg==='number'&&Number.isFinite(yawDeg)&&yawDeg>=-180&&yawDeg<=180,'CAMERA_GIMBAL_RANGE');
 const p=pitchDeg*Math.PI/180,y=yawDeg*Math.PI/180,f=[Math.cos(p)*Math.cos(y),Math.cos(p)*Math.sin(y),-Math.sin(p)],r=[-Math.sin(y),Math.cos(y),0];
 const up=[r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0]];
 return{mountNedM:rotateWxyz(quaternionWxyz,mountFrdM),forwardNed:rotateWxyz(quaternionWxyz,f),upNed:rotateWxyz(quaternionWxyz,up)};
}
