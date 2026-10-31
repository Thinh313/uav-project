/** Causal in-memory AP peer, no SITL/Android/OS actor. Uses real MAVLink bytes. */
import{createHash}from'node:crypto';import assert from'node:assert/strict';import fs from'node:fs';import{EventEmitter}from'node:events';
import{rcWire}from'../../product/workbench-control.mjs';
import {RootWire,sourceSpanReference}from'../root-wire-param07.mjs';import{encode,Decoder}from'../../../../services/mavlink.mjs';import{sha,HOME}from'../../../../pilot/auto63/compiler.mjs';
const{encodeFull}=await import('../../../../pilot/apstream40/wire.mjs');
const fileSHA=p=>createHash('sha256').update(fs.readFileSync(new URL(p,import.meta.url))).digest('hex'),oldWireAtStart=fileSHA('../root-wire.mjs'),newWireAtStart=fileSHA('../root-wire-param07.mjs');
const now=()=>Number(process.hrtime.bigint()/1000000n),wait=ms=>new Promise(r=>setTimeout(r,ms));
const params=JSON.parse(fs.readFileSync(new URL('../source/aeris_runtime/assets/workbench-profiles/nominal/typed-profile.json',import.meta.url))).parameters;
const context={run:'mock',epoch:'e',boot:'b',operator:'pilot',generation:'g'};
const root={context,profileId:'WORKBENCH_SIM_V1',endpoint:{host:'127.0.0.1',port:5961},fsyncBeforeForward:true,sourceContractRef:{sourceSHA256:'a'.repeat(64)},rootTransportRelativePath:'sessions/mock/raw/transport-journal'};
const item=(seq,command,z=0)=>({seq,command,frame:seq===0?0:3,param1:0,param2:0,param3:0,param4:0,x:Math.round(HOME.lat*1e7),y:Math.round(HOME.lon*1e7),z,current:0,autocontinue:1,mission_type:0});
const items=[item(0,16,10),item(1,22,10),item(2,20,0)],body={compiled:{items},home:HOME,missionSha256:sha(items)},plan={...body,sha256:sha(body)};
class Capture{
 constructor(){this.rows=[];this.n=0;this.committed=0;this.reject=false;this.delay=0;this.flushes=0;this.onFlush=null;}
 append(kind,data){const row={n:++this.n,sha256:sha({n:this.n,kind,data}),kind,data,durable:false};this.rows.push(row);return row;}
 async beforeWire(){this.flushes++;if(this.onFlush)this.onFlush();if(this.delay)await wait(this.delay);if(this.reject)throw Error('INJECTED_FSYNC_EIO');this.committed=this.n;return{durable:true,throughSequence:this.n,head:this.rows.at(-1)?.sha256,lastRef:{mock:true}};}
 async close(){return this.beforeWire();}
}
class Peer extends EventEmitter{
 constructor(capture,{wrongFirmware=false,wrongParam=false,wrongTargetAck=false,noPostAckHeartbeat=false}={}){super();this.capture=capture;this.writable=true;this.destroyed=false;this.decoder=new Decoder();this.sequence=0;this.mode=0;this.armed=false;this.writes=[];this.options={wrongFirmware,wrongParam,wrongTargetAck,noPostAckHeartbeat};this.home={latitude:Math.round(HOME.lat*1e7),longitude:Math.round(HOME.lon*1e7),altitude:10000};this.boot=1000;this.mission=structuredClone(items);setImmediate(()=>{this.emit('connect');this.telemetry();});this.timer=setInterval(()=>this.telemetry(),150);}
 setNoDelay(){}
 emitAP(id,fields={}){if(this.destroyed)return;const raw=Buffer.from(encodeFull(id,fields,{system:42,component:1,seq:this.sequence++&255}));this.emit('data',raw);}
 telemetry(){this.emitAP(0,{autopilot:3,type:2,base_mode:this.armed?128:0,custom_mode:this.mode});this.emitAP(33,{time_boot_ms:this.boot++,lat:this.home.latitude,lon:this.home.longitude,alt:10000,relative_alt:0});this.emitAP(242,this.home);this.emitAP(245,{landed_state:1});this.emitAP(24,{fix_type:3,satellites_visible:10,eph:100});this.emitAP(1,{voltage_battery:24000,onboard_control_sensors_present:270532655,onboard_control_sensors_enabled:270532655,onboard_control_sensors_health:270532655});this.emitAP(193,{flags:55});}
 write(raw,callback){const intent=this.capture.rows.findLast(r=>r.kind==='TX_INTENT'&&r.data.rawHex===raw.toString('hex')||r.kind==='PARAMETER_READ_COHORT_INTENT'&&r.data.rawHex.includes(raw.toString('hex'))||r.kind==='MANUAL_INPUT_TRANSACTION'&&r.data.rawHex===raw.toString('hex')||r.kind==='OWNER_LOSS_SAFETY_CLEANUP_INTENT'&&[r.data.neutralHex,r.data.releaseHex].includes(raw.toString('hex')));assert.ok(intent);assert.ok(this.capture.committed>=intent.n,'physical send before journal barrier');this.writes.push(Buffer.from(raw));for(const m of this.decoder.push(raw)){const f=m.fields;setImmediate(()=>{
   if(m.id===76&&f.command===512&&f.param1===242)setTimeout(()=>this.emitAP(242,this.home),5);
   if(m.id===76&&f.command===512&&f.param1===148)this.emitAP(148,{flight_sw_version:this.options.wrongFirmware?1:67568127,flight_custom_version:[...'dbe79216'].map(c=>c.charCodeAt(0))});
   if(m.id===20)this.emitAP(22,{param_id:f.param_id,param_value:f.param_id==='FS_OPTIONS'&&this.options.wrongParam?16:params[f.param_id].value,param_type:params[f.param_id].mavType,param_count:39,param_index:0});
   if(m.id===44){this.upload=[];this.next=0;this.count=f.count;this.emitAP(51,{seq:0,target_system:255,target_component:190,mission_type:0});}
   if(m.id===73){this.upload.push({...f});if(++this.next<this.count)this.emitAP(51,{seq:this.next,target_system:255,target_component:190,mission_type:0});else{this.mission=this.upload;this.emitAP(47,{type:0,target_system:255,target_component:190,mission_type:0});}}
   if(m.id===43)this.emitAP(44,{count:this.mission.length,target_system:255,target_component:190,mission_type:0});
   if(m.id===51)this.emitAP(73,{...this.mission[f.seq],target_system:255,target_component:190,mission_type:0});
   if(m.id===76&&[176,400].includes(f.command)){if(f.command===176)this.mode=f.param2;else this.armed=f.param1===1;this.emitAP(77,{command:f.command,result:0,target_system:this.options.wrongTargetAck?77:255,target_component:190});if(!this.options.noPostAckHeartbeat)this.emitAP(0,{autopilot:3,type:2,base_mode:this.armed?128:0,custom_mode:this.mode});setTimeout(()=>this.emitAP(242,this.home),5);}
  });}callback?.();return true;}
 end(){this.destroy();}destroy(){if(this.destroyed)return;this.destroyed=true;this.writable=false;clearInterval(this.timer);setImmediate(()=>this.emit('close'));}
}
function make(options={}){const capture=new Capture(),peer=new QueuePeer(capture,options),owner={context,...{clientId:'A',clientEpoch:1,clientInstance:'A'}},operators={active:true,epoch:1,heartbeatAllowed(){return this.active;}},link=new RootWire({compiledPlan:plan,rootContext:root,capture,operators,flightOwner:owner,parameters:params,clock:now,inputPermission:p=>p.authorityEpoch===operators.epoch,rawReference:sourceSpanReference(root),connectSocket:()=>peer});return{capture,peer,operators,link};}
async function stop(s){s.peer.destroy();clearInterval(s.link.heartbeatTimer);clearInterval(s.link.watch);if(s.link.pending)s.link.failPending('TEST_CLOSE');await s.link.txTail;await s.link.rxTail;}
async function enteredAuto(s){await s.link.connect();await s.link.inspect();const c={planSha256:plan.sha256,missionSha256:plan.missionSha256,homeConfirmed:true,session:s.link.sessionId,boot:'b'};await s.link.upload63(c);const h=await s.link.arm(c);await s.link.auto({...c,homeReviewSha256:h.sha256,postArmHomeConfirmed:true});}

class QueuePeer extends Peer{
 constructor(capture,options={}){super(capture,options);this.pending=[];this.replies=[];this.maxPending=0;this.dropped=0;this.paramSent=[];this.paramOptions=options;this.queueTimer=setInterval(()=>{if(this.destroyed)return;if(this.replies.length<5&&this.pending.length)this.replies.push(this.pending.shift());if(this.replies.length&&!this.paramOptions.noReplies){const f=this.replies.shift();if(this.paramOptions.wrongSource)this.emit('data',Buffer.from(encodeFull(22,{param_id:f.param_id,param_value:params[f.param_id].value,param_type:params[f.param_id].mavType},{system:43,component:1,seq:this.sequence++&255})));else this.emitAP(22,{param_id:this.paramOptions.duplicateOnly?'ARMING_SKIPCHK':f.param_id,param_value:this.paramOptions.duplicateOnly?0:f.param_id==='FS_OPTIONS'&&this.paramOptions.wrongParam?16:params[f.param_id].value,param_type:this.paramOptions.duplicateOnly?6:this.paramOptions.wrongType?9:params[f.param_id].mavType,param_count:39,param_index:65535});}},20);}
 write(raw,cb){const m=new Decoder().push(raw)[0];if(m?.id!==20)return super.write(raw,cb);const intent=this.capture.rows.findLast(r=>r.kind==='PARAMETER_READ_COHORT_INTENT'&&r.data.rawHex.includes(raw.toString('hex')));assert.ok(intent&&this.capture.committed>=intent.n);this.writes.push(Buffer.from(raw));this.paramSent.push(m.fields.param_id);if(this.pending.length>=20)this.dropped++;else this.pending.push(m.fields);this.maxPending=Math.max(this.maxPending,this.pending.length);cb?.();return true;}
 destroy(){super.destroy();clearInterval(this.queueTimer);}
}
const groups=[];
{
 const s=make();try{await s.link.connect();await s.link.discoveryJob;assert.equal(s.link.readiness().ready,true);assert.equal(s.link.preflightView().ready,false);await s.link.inspect();assert.equal(s.link.preflightView().ready,true);assert.equal(new Set(s.peer.paramSent).size,39);assert.equal(s.peer.paramSent.length,39);assert.equal(s.peer.dropped,0);assert.ok(s.peer.maxPending<=4);assert.equal(s.capture.rows.filter(r=>r.kind==='PARAMETER_READ_COHORT_INTENT').length,1);assert.ok(s.peer.writes.filter(b=>new Decoder().push(b).some(m=>m.id===0)).length>=2);groups.push('AP20requests5replies-window4-all39typed-exactonce-onecohort-fsync-HBcontinues-disarmed-readiness-before-explicit-preflight');}finally{await stop(s);}
}
{
 const s=make({wrongSource:true});try{await s.link.connect();await wait(180);assert.equal(s.link.parameterCohort.received.size,0);assert.equal(s.peer.paramSent.length,4);const name=s.peer.paramSent[0];s.link.health.parameters.set(name,{at:s.link.now()-1000,bits:params[name].float32Hex,type:params[name].mavType,rawRef:{startOffset:-1}});await wait(30);assert.equal(s.peer.paramSent.length,4);s.operators.active=false;await assert.rejects(s.link.discoveryJob,/OWNER_LOST/);assert.equal(s.peer.paramSent.length,4);await s.link.cleanupPromise;groups.push('foreignsource-and-stale-cachedvalues-cannotadvance-then-ownerloss-stops-without-resend');}finally{await stop(s);}
}
{
 const s=make({wrongParam:true});try{await s.link.connect();await assert.rejects(s.link.discoveryJob,/TYPED_PARAMETER/);assert.ok(s.peer.paramSent.length<39);assert.equal(s.link.readiness().ready,false);groups.push('wrong-float-bits-profile-fails-sourcehealth-before39-ready');}finally{await stop(s);}
}
{
 const s=make({wrongType:true});try{await s.link.connect();await assert.rejects(s.link.discoveryJob,/TYPED_PARAMETER/);assert.equal(s.link.parameterCohort.received.size,0);assert.equal(s.link.readiness().ready,false);groups.push('correctvalue-bits-but-wrong-MAVtype-never-advances-cohort');}finally{await stop(s);}
}
{
 const s=make({duplicateOnly:true});try{await s.link.connect();await wait(180);assert.equal(s.link.parameterCohort.received.size,1);assert.equal(s.peer.paramSent.length,5);s.operators.active=false;await assert.rejects(s.link.discoveryJob,/OWNER_LOST/);groups.push('repeated-fresh-duplicate-name-cannot-count-as-other38-parameters');}finally{await stop(s);}
}
{
 const s=make({noReplies:true});try{await s.link.connect();await assert.rejects(s.link.discoveryJob,/5000MS/);assert.equal(s.peer.paramSent.length,4);assert.equal(s.link.parameterCohort.received.size,0);assert.equal(s.capture.rows.filter(r=>r.kind==='PARAMETER_READ_COHORT_INTENT').length,1);assert.equal(s.link.readiness().ready,false);groups.push('singleabsolute5s-cohort-deadline-no-response-no-resends-no-fullburst-reset');}finally{await stop(s);}
}
{
 const s=make();s.capture.onFlush=()=>{if(s.capture.rows.at(-1)?.kind==='PARAMETER_READ_COHORT_INTENT')s.capture.reject=true;};try{await s.link.connect();await assert.rejects(s.link.discoveryJob,/FSYNC/);assert.equal(s.peer.paramSent.length,0);groups.push('cohort-fsync-EIO-zero-paramphysicalsend');}finally{await stop(s);}
}
{
 const s=make();try{await s.link.connect();await s.link.discoveryJob;let offset=0;s.link.clock=()=>now()+offset;const originalUntil=s.link.until.bind(s.link);let n=0;s.link.until=async(...a)=>{if(++n===2){for(const at of[1000,2000,3000,4000,5000,6000,7000,7990]){offset=at;s.peer.telemetry();await s.link.rxTail;}}return originalUntil(...a);};s.capture.onFlush=()=>{if(s.capture.rows.at(-1)?.kind==='PREFLIGHT_TYPED39_OBSERVED'){offset+=20;s.capture.onFlush=null;}};await assert.rejects(()=>s.link.inspect(),/ABSOLUTE_8000MS/);assert.equal(s.link.inspectionAccepted,false);assert.equal(s.link.preflightView().ready,false);groups.push('7990ms-healthpass-plus20ms-durableflush-never-upgrades-ready-after-original8s-deadline');}finally{await stop(s);}
}
{
 const s=make();let release,paused;const ready=new Promise(r=>paused=r),base=s.capture.beforeWire.bind(s.capture);s.capture.beforeWire=async()=>{if(s.capture.rows.at(-1)?.kind==='TX_INTENT'&&s.capture.rows.at(-1).data.id===76&&!release){await new Promise(r=>{release=r;paused();});}return base();};try{await s.link.connect();await ready;const n=s.peer.writes.length,closed=s.link.close();assert.equal(s.link.heartbeatStopped,true);release();await closed;assert.equal(s.peer.writes.length,n);assert.equal(s.peer.paramSent.length,0);assert.equal(s.link.failure,null);const count=s.capture.rows.length;await wait(30);assert.equal(s.capture.rows.length,count);groups.push('close-paused-discovery-fsync-immediately-stops-timers-and-all-later-physicalsetup-HB-no-postcapture-append');}finally{await stop(s);}
}
assert.equal(fileSHA('../root-wire-param07.mjs'),newWireAtStart);const report={oldWireSHA256:oldWireAtStart,newWireSHA256:newWireAtStart,format:'aeris-param07-response-paced-wire-source-mock',status:'PASS_IN_MEMORY_AP_QUEUE_NOT_ANDROID_SITL',groups,actualActors:0,originalInspectDeadlineMs:8000,cohortDeadlineMs:5000,maximumOutstanding:4};fs.writeFileSync(new URL('../../../../evidence/betasim-integrated01/runtime/param07-causal-mock-final02.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,groups:groups.length}));
