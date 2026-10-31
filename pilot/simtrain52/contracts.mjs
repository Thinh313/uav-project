export const FLOOR=20*1024**3;
const finite=(v,a,b)=>typeof v==='number'&&Number.isFinite(v)&&v>=a&&v<=b;
const str=s=>typeof s==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(s);
const exact=(o,keys)=>{if(!o||typeof o!=='object'||Array.isArray(o)||Object.keys(o).sort().join(',')!==keys.split(',').sort().join(','))throw Error('SCHEMA')};
export function admission({freeBytes,rawBytes,walBytes,mediaBytes,stagingBytes,runtimeBytes,marginBytes}){let total=0;for(const [k,v]of Object.entries({freeBytes,rawBytes,walBytes,mediaBytes,stagingBytes,runtimeBytes,marginBytes})){if(!Number.isSafeInteger(v)||v<0)throw Error('BUDGET_'+k);if(k!=='freeBytes')total+=v;}if(!Number.isSafeInteger(total))throw Error('BUDGET_OVERFLOW');return {admitted:freeBytes>=FLOOR+total,floorBytes:FLOOR,peakBytes:total,requiredFreeBytes:FLOOR+total,deficitBytes:Math.max(0,FLOOR+total-freeBytes),simulatorPermission:false};}
export function normalize(raw,c){exact(c,'min,center,max,deadzone,expo,invert');if(!finite(raw,-10,10)||!finite(c.min,-2,2)||!finite(c.center,-2,2)||!finite(c.max,-2,2)||!(c.min<c.center&&c.center<c.max)||c.center-c.min<.1||c.max-c.center<.1||!finite(c.deadzone,0,.4)||!finite(c.expo,0,1)||typeof c.invert!=='boolean')throw Error('CALIBRATION');let x=Math.max(-1,Math.min(1,(raw-c.center)/(raw>=c.center?c.max-c.center:c.center-c.min)));const s=Math.sign(x),a=Math.abs(x);x=a<=c.deadzone?0:s*(a-c.deadzone)/(1-c.deadzone);return (c.invert?-1:1)*((1-c.expo)*x+c.expo*x*x*x);}
export const DEFAULT_CAL={min:-1,center:0,max:1,deadzone:.06,expo:.3,invert:false};
export class InputSession{
 constructor(){this.state='DISCONNECTED';this.session=null;this.boot=null;this.device=null;this.seq=-1;this.last=null;this.lastAt=null;this.axes=[0,0,0,0];this.requestedMode=null;this.observedMode=null;this.owner=null;this.pending=null;this.clock=null;this.reason='NEW';this.terminal=false;}
 connect({session,boot,device,owner,clock}){if(![session,boot,device,owner,clock].every(str))throw Error('IDENTITY');this.session=session;this.boot=boot;this.device=device;this.owner=owner;this.clock=clock;this.seq=-1;this.last=null;this.lastAt=null;this.axes=[0,0,0,0];this.state='NEUTRAL_REQUIRED';this.observedMode=null;this.requestedMode=null;this.pending=null;this.reason='EXPLICIT_NEW_SESSION';this.terminal=false;}
 revoke(reason){this.axes=[0,0,0,0];this.pending=null;this.owner=null;this.state='REVOKED';this.reason=reason;this.terminal=true;}
 receive(e,now,cal=Array(4).fill(DEFAULT_CAL)){
  try{exact(e,'session,boot,device,owner,clock,seq,atMs,axes,focused,connected');if(!finite(now,0,1e12)||!finite(e.atMs,0,1e12)||!Number.isSafeInteger(e.seq)||e.seq<0||!Array.isArray(e.axes)||e.axes.length!==4||!Array.isArray(cal)||cal.length!==4||typeof e.focused!=='boolean'||typeof e.connected!=='boolean')throw Error('INPUT_SHAPE');}catch(error){this.revoke('MALFORMED_INPUT');throw error}
  if(this.terminal||this.state==='DISCONNECTED')throw Error('NEW_CONNECTION_REQUIRED');
  if(this.last!==null&&(now<this.last||now-this.last>200)){this.revoke(now<this.last?'CLOCK_REGRESSION':'SUSPENDED_INPUT');return false;}
  if(this.lastAt!==null&&e.atMs<this.lastAt){this.revoke('INPUT_TIMESTAMP_REGRESSION');return false;}
  if(['session','boot','device','owner','clock'].some(k=>e[k]!==this[k])){this.revoke('WRONG_IDENTITY');return false;}
  if(e.seq<=this.seq){this.revoke('SEQUENCE_REPLAY');return false;}
  if(!e.focused||!e.connected){this.revoke(!e.focused?'FOCUS_LOST':'DEVICE_LOST');return false;}
  if(now<e.atMs||now-e.atMs>200){this.revoke('STALE_INPUT');return false;}
  let axes;try{axes=e.axes.map((x,i)=>normalize(x,cal[i]))}catch(error){this.revoke('INVALID_AXIS');throw error}
  this.seq=e.seq;this.last=now;this.lastAt=e.atMs;
  if(this.state==='NEUTRAL_REQUIRED'&&!axes.every(x=>Math.abs(x)<=.02)){this.axes=[0,0,0,0];return false;}
  this.axes=axes;this.state='MOCK_INPUT_ACTIVE';this.reason='MONITOR_ONLY_NO_TRANSPORT';return true;
 }
 tick(now){if(!finite(now,0,1e12))throw Error('CLOCK');if(this.last!==null&&(now<this.last||now-this.last>200))this.revoke(now<this.last?'CLOCK_REGRESSION':'STALE_INPUT');}
 requestMode(mode,now,nonce){this.tick(now);if(this.state!=='MOCK_INPUT_ACTIVE'||!str(nonce)||!['STABILIZE','ALT_HOLD','LOITER','GUIDED','AUTO','RTL'].includes(mode)||this.pending)throw Error('MODE_REQUEST_REFUSED');this.requestedMode=mode;this.pending={mode,nonce,atMs:now};return {...this.pending,scope:'MOCK_NO_WIRE'};}
 ack(nonce){if(!this.pending||this.pending.nonce!==nonce)throw Error('ACK_UNCORRELATED');return {accepted:true,execution:'UNKNOWN',observedMode:this.observedMode};}
 observeMode({session,boot,mode,atMs},now){this.tick(now);if(this.state!=='MOCK_INPUT_ACTIVE'||session!==this.session||boot!==this.boot||!finite(atMs,0,1e12)||now<atMs||now-atMs>200||!['STABILIZE','ALT_HOLD','LOITER','GUIDED','AUTO','RTL'].includes(mode))throw Error('MODE_OBSERVATION_REFUSED');this.observedMode=mode;if(this.pending?.mode===mode)this.pending=null;}
 snapshot(){return structuredClone({state:this.state,axes:this.axes,requestedMode:this.requestedMode,observedMode:this.observedMode,reason:this.reason,terminal:this.terminal,operational:false,transport:'NONE_MOCK_MONITOR_ONLY'})}
}
