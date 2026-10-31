import{hex}from'../pilot/apstream40/wire.mjs';import {geoPlan,geoSnapshot,homeCheck} from '../app/core/geo-quality.mjs';
import {sha256,requestIdentity} from '../app/core/geodata.mjs';
import net from '../../socket.mjs';
import {EventEmitter} from '../../events.mjs';
const randomUUID=()=>crypto.randomUUID();
import {Decoder,encode} from './mavlink.mjs';
import {compileSurvey,readbackEqual,SITL_WORLD} from '../app/core/compiler.mjs';
import {compileQgc} from '../app/core/qgc.mjs';
import {compileGeoSurvey} from '../app/core/geodata.mjs';
import {localFrame} from '../app/core/survey.mjs';
import {PROFILE_REF,CONFIGURATION_NAMES,evaluateConfiguration,makeProfileSnapshot,assertProfileReference,assertMissionProfile} from '../app/core/vehicle-profile.mjs';
const MODES={0:'STABILIZE',3:'AUTO',4:'GUIDED',5:'LOITER',6:'RTL',9:'LAND',16:'POSHOLD'};
const clone=x=>structuredClone(x);
export const PARAMETER_READ_ALLOWLIST=Object.freeze(['FS_GCS_ENABLE','FS_GCS_TIMEOUT','FS_OPTIONS','MAV_GCS_SYSID']);
export class SitlLink extends EventEmitter{
 constructor({port=5760,clock=()=>performance.now(),timeoutMs=10000,geodata=null}={}){super();if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid simulator port');this.port=port;this.geodata=geodata;this.expected=null;this.resumeRequired=false;this.gapSample=null;this.clock=clock;this.timeoutMs=timeoutMs;this.socket=null;this.sessionId=null;this.events=[];this.frames=[];this.generation=0;this.reset();}
 reset(){this.geoReview=null;this.lastGeoGuard=null;this.resumeRequired=false;this.lastProfileGuard=null;this.configuration=null;this.gapSample=null;this.decoder=new Decoder();this.samples={};this.vehicle=null;this.sequence=0;this.transport='disconnected';this.mission={state:'empty',compiled:null,readback:null};this.execution={state:'idle',reached:[]};this.pending=null;this.commandState=null;this.ambiguous=false;}
 event(type,detail={}){const e={index:this.events.length?this.events.at(-1).index+1:1,time:new Date().toISOString(),sessionId:this.sessionId,type,detail:clone(detail)};this.events.push(e);this.events=this.events.slice(-5000);this.emit('event',e);}
 async connect(){
  if(this.socket)throw Error('Phiên SITL đã mở.');this.reset();const generation=++this.generation;this.sessionId=globalThis.direct95Connecting?.session??randomUUID();this.transport='connecting';this.event('connect-request',{endpoint:`127.0.0.1:${this.port}`,simulation:true});
  const s=net.createConnection({host:'127.0.0.1',port:this.port});this.socket=s;s.setNoDelay(true);
  s.on('data',bytes=>{if(generation!==this.generation)return;for(const m of this.decoder.push(bytes))this.receive({...m,receivedAt95:s.receivedAt95});});
  s.on('error',e=>this.event('transport-error',{message:e.message}));
  s.on('close',()=>{if(generation!==this.generation)return;this.event('before-disconnect',{reason:'transport'});this.failPending('Kết nối bị đóng; trạng thái cần kiểm tra lại.');clearInterval(this.heartbeatTimer);this.socket=null;this.transport='disconnected';this.vehicle=null;this.samples={};this.configuration=null;this.mission={state:'empty',compiled:null,readback:null};this.execution={state:'idle',reached:[]};this.commandState=null;this.event('disconnected');});
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{s.destroy();reject(Error('Kết nối SITL timeout.'));},5000);s.once('connect',()=>{clearTimeout(timer);resolve();});s.once('error',e=>{clearTimeout(timer);reject(e);});});
  if(generation!==this.generation||this.socket!==s)throw Error('Phiên kết nối đã bị hủy.');this.transport='connected';this.sendHeartbeat();this.heartbeatTimer=setInterval(()=>this.sendHeartbeat(),1000);return this.snapshot();
 }
 disconnect(){this.event('before-disconnect',{reason:'operator'});this.failPending('Phiên đã ngắt.');clearInterval(this.heartbeatTimer);const s=this.socket;this.socket=null;this.generation++;s?.destroy();this.vehicle=null;this.samples={};this.configuration=null;this.lastProfileGuard=null;this.geoReview=null;this.lastGeoGuard=null;this.transport='disconnected';this.mission={state:'empty',compiled:null,readback:null};this.execution={state:'idle',reached:[]};this.commandState=null;this.ambiguous=false;this.event('disconnected');}
 sendHeartbeat(){if(this.socket?.writable)this.send(0,{custom_mode:0,type:6,autopilot:8,base_mode:0,system_status:4,mavlink_version:3});}
 send(id,fields={}){if(!this.socket?.writable)throw Error('SITL chưa kết nối.');const b=encode(id,fields,{seq:this.sequence++});this.socket.write(b);this.frames.push({direction:'out',id,fields:clone(fields),hex:hex(b),sessionId:this.sessionId});this.frames=this.frames.slice(-10000);}
 target(fields={}){return {target_system:this.vehicle.system,target_component:this.vehicle.component,...fields};}
 receive(m){
  const at=m.receivedAt95??this.clock();this.frames.push({direction:'in',...clone(m),sessionId:this.sessionId});this.frames=this.frames.slice(-10000);
  if(!this.vehicle){if(m.id!==0||m.fields.autopilot!==3||m.fields.type!==2||m.component!==1)return;this.vehicle={system:m.system,component:m.component};this.event('autopilot-discovered',this.vehicle);
   for(const id of [148,242])this.send(76,this.target({command:512,param1:id}));
   for(const id of [1,24,30,33,42,193,242,245])this.send(76,this.target({command:511,param1:id,param2:200000}));}
  if(m.system!==this.vehicle.system||m.component!==this.vehicle.component){this.event('foreign-frame-ignored',{id:m.id,system:m.system,component:m.component});return;}
  const f=m.fields;
  if([0,1,24,30,33,42,148,193,242,245].includes(m.id)){
   const previous=this.samples[m.id];const boot=f.time_boot_ms;
   if(m.id===0){this.invalidateHeartbeatGap();const requestedMode=this.pending?.kind==='command'?({guided:4,auto:3,hold:5,rtl:6})[this.pending.name]:null;
    if(previous&&(previous.fields.base_mode&128)&&(f.base_mode&128)&&previous.fields.custom_mode===3&&f.custom_mode!==3&&requestedMode!==f.custom_mode){this.invalidateExecution('autopilot-mode-deviation',{from:3,to:f.custom_mode,operatorCommand:false});}}

   if(boot!==undefined&&previous?.fields.time_boot_ms!==undefined&&boot<previous.fields.time_boot_ms){this.invalidateConfiguration('boot-regression');this.invalidateExecution('boot-regression',{before:previous.fields.time_boot_ms,after:boot});this.failPending('Autopilot restart hoặc telemetry không đúng thứ tự.');this.ambiguous=true;this.mission.state='unknown';return;}
   this.samples[m.id]={at,fields:clone(f)};
  }
  if(m.id===148&&this.configuration&&f.flight_sw_version!==this.configuration.firmware.flightSwVersion)this.invalidateConfiguration('firmware-change');
  if(m.id===22&&this.configuration&&CONFIGURATION_NAMES.includes(f.param_id)){const old=this.configuration.parameters[f.param_id];if(old&&(old.value!==f.param_value||old.type!==f.param_type))this.invalidateConfiguration('parameter-change:'+f.param_id);}
  if(m.id===253)this.event('autopilot-status',{severity:f.severity,text:f.text});
  if(m.id===46){this.event('mission-item-reached',{seq:f.seq});if(['running','paused','returning','interrupted','observed-active','observed-armed'].includes(this.execution.state)&&f.seq<(this.mission.compiled?.items.length??0)&&!this.execution.reached.includes(f.seq))this.execution.reached.push(f.seq);}
  this.observeExecution();
  const p=this.pending;if(!p)return;
  // Mission replies must address this GCS and mission type 0. Broadcast command ACK extensions may be zero.
  if([40,44,47,51,73].includes(m.id)&&(f.target_system!==255||f.target_component!==190||f.mission_type!==0))return;
  if(p.kind==='mission')this.missionMessage(m,p);
  if(p.kind==='configuration'){if(m.id===148)p.firmware={version:`${f.flight_sw_version>>>24}.${(f.flight_sw_version>>>16)&255}.${(f.flight_sw_version>>>8)&255}`,flightSwVersion:f.flight_sw_version,encoding:'ardupilot-c-cast',capabilities:f.capabilities??null,observedAtUTC:new Date().toISOString(),at};if(m.id===22&&p.names.includes(f.param_id))p.values[f.param_id]={value:f.param_value,type:f.param_type,index:f.param_index,observedAtUTC:new Date().toISOString(),at};if(p.firmware&&p.names.every(n=>p.values[n])){this.configuration={format:'aeris-configuration-observation',version:1,simulation:true,id:p.observationId,sessionId:this.sessionId,vehicle:clone(this.vehicle),autopilot:this.samples[0].fields.autopilot,vehicleType:this.samples[0].fields.type,startedAtUTC:p.startedAtUTC,completedAtUTC:new Date().toISOString(),firmware:p.firmware,parameters:p.values};this.event('configuration-read',{readOnly:true,profileSnapshot:this.profileSnapshot()});this.resolvePending(this.configurationReport());}}
  if(p.kind==='parameters'&&m.id===22&&p.names.includes(f.param_id)){if(Number.isFinite(f.param_value)){p.values[f.param_id]={value:f.param_value,type:f.param_type,index:f.param_index};if(p.names.every(n=>p.values[n])){this.event('parameters-read',{readOnly:true,values:p.values});this.resolvePending(clone(p.values));}}}
  if(p.kind==='command'){
   if(m.id===77&&f.command===p.command){if(f.target_system&&f.target_system!==255||f.target_component&&f.target_component!==190)return;
    if([0,5].includes(f.result)){p.accepted=f.result===0;if(p.accepted){p.ackAt=at;p.observed=false;}this.commandState={name:p.name,state:p.accepted?'accepted':'in-progress'};this.event('command-ack',{name:p.name,result:f.result});}
    else{this.commandState={name:p.name,state:'rejected',result:f.result};this.rejectPending(Error(`ArduPilot từ chối lệnh (${f.result}).`));return;}}
   // Both ACK and a fresh post-send heartbeat are required; not a persisted UI value.
   if(m.id===0&&p.accepted&&at>=p.ackAt&&p.observe(f)){p.observed=true;}
   if(p.accepted&&p.observed){this.commandState={name:p.name,state:'observed'};this.event('command-observed',{name:p.name});if(p.name==='auto')this.execution.state='running';else if(p.name==='guided'&&['running','paused','returning','interrupted','observed-active','observed-armed'].includes(this.execution.state))this.invalidateExecution('operator-mode-interruption',{requestedMode:4});else if(p.name==='hold'&&['running','observed-active','observed-armed'].includes(this.execution.state))this.execution.state='paused';else if(p.name==='rtl'&&['running','paused','interrupted','observed-active','observed-armed'].includes(this.execution.state))this.execution.state='returning';this.resolvePending(this.snapshot());}
  }
 }
 observeExecution(){
  if(!['running','paused','returning','interrupted','observed-active','observed-armed'].includes(this.execution.state)||!this.freshness(0))return;const hb=this.samples[0].fields;
  if(!(hb.base_mode&128)&&this.freshness(245)&&this.samples[245].fields.landed_state===1){const final=(this.mission.compiled?.items.length??0)-1;this.execution.state=!this.resumeRequired&&this.execution.reached.includes(final)?'completed':'stopped';this.resumeRequired=false;this.event('mission-execution-ended',{state:this.execution.state,reached:clone(this.execution.reached),groundObserved:true});}
 }
 invalidateExecution(type,detail={}){if(this.mission.state==='verified')this.mission.state='unknown';if(['running','paused','returning','observed-active','observed-armed'].includes(this.execution.state))this.execution.state='interrupted';if(this.samples[0]?.fields.base_mode&128)this.resumeRequired=true;this.event(type,{...detail,readbackInvalidated:true,resumeRequired:this.resumeRequired});}
 invalidateHeartbeatGap(){const hb=this.samples[0];if(hb&&this.clock()-hb.at>3000&&this.gapSample!==hb){this.gapSample=hb;this.invalidateConfiguration('heartbeat-gap');this.invalidateExecution('heartbeat-gap',{gapMs:this.clock()-hb.at});if(this.pending){this.ambiguous=true;this.failPending('Heartbeat gap trong giao dịch; cần kết nối lại.');}}}
 freshness(id,max=3000){const s=this.samples[id];return !!s&&this.clock()-s.at<=max;}
 snapshot(){this.invalidateHeartbeatGap();const hb=this.samples[0]?.fields,pos=this.samples[33]?.fields,gps=this.samples[24]?.fields,health=this.samples[1]?.fields,version=this.samples[148]?.fields;
  return {simulation:true,adapter:'loopback-tcp-sitl-v1',sessionId:this.sessionId,transport:this.transport,connected:this.transport==='connected'&&this.freshness(0),vehicle:clone(this.vehicle),mode:this.freshness(0)?MODES[hb.custom_mode]??`MODE ${hb.custom_mode}`:null,modeId:this.freshness(0)?hb.custom_mode:null,armed:this.freshness(0)?!!(hb.base_mode&128):null,
   heartbeatAgeMs:this.samples[0]?Math.round(this.clock()-this.samples[0].at):null,
   home:this.freshness(0)&&this.freshness(242)?this.observedHome():null,
   position:this.freshness(0)&&this.freshness(33)?{lat:pos.lat/1e7,lon:pos.lon/1e7,relativeAltitude:pos.relative_alt/1000,amsl:pos.alt/1000,groundSpeed:Math.hypot(pos.vx,pos.vy)/100}:null,
   gps:this.freshness(0)&&this.freshness(24)?{fix:gps.fix_type,satellites:gps.satellites_visible}:null,
   health:this.freshness(0)&&this.freshness(1)?{voltage:health.voltage_battery===65535?null:health.voltage_battery/1000,remaining:health.battery_remaining<0?null:health.battery_remaining,enabled:health.onboard_control_sensors_enabled,healthy:health.onboard_control_sensors_health}:null,
   firmware:version?`${version.flight_sw_version>>>24}.${(version.flight_sw_version>>>16)&255}.${(version.flight_sw_version>>>8)&255}`:null,
   expectedRequest:clone(this.expected?.sourceRequest??this.expected?.sourcePackage??null),mission:{execution:clone(this.execution),state:this.mission.state,count:this.mission.compiled?.items.length??0,current:this.freshness(0)&&this.freshness(42)?this.samples[42].fields.seq:null,readbackMatches:this.mission.state==='verified',resumeRequired:this.resumeRequired},
   geoReview:this.geoReview?{requestSha256:this.geoReview.requestSha256,policy:this.geoReview.plan.analysis.policy,approvedAt:this.geoReview.approvedAt,scope:this.geoReview.plan.analysis.fieldQuality}:null,configuration:this.configurationReport(),command:clone(this.commandState),busy:!!this.pending,ambiguous:this.ambiguous,preflight:this.preflight(),decoder:clone(this.decoder.stats),events:clone(this.events.slice(-100))};
 }
 observedHome(){const h=this.samples[242]?.fields;if(!h||![h.latitude,h.longitude,h.altitude].every(Number.isFinite))return null;const lat=h.latitude/1e7,lon=h.longitude/1e7,amsl=h.altitude/1000;if(Math.abs(lat)>80||Math.abs(lon)>180||amsl< -500||amsl>9000)return null;const q=localFrame({lat:SITL_WORLD.home.lat,lon:SITL_WORLD.home.lon}).forward({lat,lon});return {lat,lon,amsl,horizontalDeltaM:Math.hypot(q.x,q.y),amslDeltaM:amsl-SITL_WORLD.home.amsl,reference:'HOME_POSITION / AMSL; simulated world only'};}
 preflight(){this.invalidateHeartbeatGap();const checks=[];const add=(id,pass,detail)=>checks.push({id,pass,detail});const hb=this.samples[0]?.fields,gps=this.samples[24]?.fields,h=this.samples[1]?.fields,home=this.observedHome();
  add('link',this.transport==='connected'&&this.freshness(0),'Heartbeat ≤3 s');add('position',this.freshness(33),'Position ≤3 s');add('gps',this.freshness(24)&&gps.fix_type>=3&&gps.satellites_visible>=6,'GPS fix ≥3 / ≥6 satellites');
  const ekf=this.samples[193]?.fields;add('estimator',this.freshness(193)&&(ekf.flags&55)===55&&!(ekf.flags&1024),'EKF attitude / velocity / absolute position ready');const required=1|2|4|32;add('sensors',this.freshness(1)&&(h.onboard_control_sensors_health&required)===required,'Gyro / accel / compass / GPS health');
  add('autopilot-prearm',this.freshness(1)&&!!(h.onboard_control_sensors_enabled&0x10000000)&&!!(h.onboard_control_sensors_health&0x10000000),'ArduPilot pre-arm checks ready');add('home',this.freshness(0)&&this.freshness(242)&&!!home&&home.horizontalDeltaM<=1&&Math.abs(home.amslDeltaM)<=.5,'Fresh Home: horizontal ≤1 m / AMSL ≤0.5 m from SITL reference');add('firmware',!!this.samples[148]&&((this.samples[148].fields.flight_sw_version>>>8)===0x040701),'Pinned ArduCopter 4.7.1 observed');add('session',!this.ambiguous,'No unresolved command/transfer outcome');const profile=this.configurationReport();add('configuration',profile.pass,'Profile '+profile.state+': '+(profile.pass?'4 tham số/firmware khớp, tuổi ≤30 s':profile.checks.find(c=>!c.pass)?.reason));return checks;
 }
 beginPending(kind,detail){this.invalidateHeartbeatGap();if(this.pending)throw Error('Đang có giao dịch.');if(this.ambiguous)throw Error('Trạng thái chưa rõ; ngắt và kết nối lại để kiểm tra.');if(!this.freshness(0)||!this.vehicle)throw Error('Heartbeat SITL chưa sẵn sàng hoặc đã cũ.');
  const promise=new Promise((resolve,reject)=>{this.pending={kind,...detail,resolve,reject,retries:0,sentAt:this.clock()};});
  this.pending.timer=setTimeout(()=>{if(kind!=='configuration')this.ambiguous=true;if(kind==='mission')this.mission.state='unknown';else if(kind==='command')this.commandState={name:this.pending?.name,state:'unknown'};this.failPending(kind==='configuration'?'Đọc cấu hình timeout; dữ liệu chưa đủ, có thể đọc lại.':'Giao dịch timeout; kết quả chưa rõ, cần kết nối lại.');},this.timeoutMs);return promise;
 }
 clearPending(){const p=this.pending;if(p){clearTimeout(p.timer);clearInterval(p.retryTimer);this.pending=null;}return p;}
 resolvePending(value){this.clearPending()?.resolve(value);}
 rejectPending(error){this.clearPending()?.reject(error);}
 failPending(message){if(this.pending){this.event('transaction-failed',{kind:this.pending.kind,message});this.rejectPending(Error(message));}}
 compileRequest(pkg){return pkg?.format==='aeris-qgc-run'?compileQgc(pkg):pkg?.format==='aeris-survey-run'?compileGeoSurvey(pkg,this.geodata):compileSurvey(pkg,SITL_WORLD);}
 async upload(pkg){const compiled=this.compileRequest(pkg);assertMissionProfile(compiled);if(!this.preflight().every(c=>c.pass))throw Error('Preflight SITL chưa đạt.');if(this.samples[0].fields.base_mode&128)throw Error('Không thay nhiệm vụ khi đang armed.');
  this.requireConfiguration('upload');if(pkg?.format==='aeris-survey-run'&&pkg.version===2)await this.requireGeography('upload',compiled);else this.requireHome('upload');const promise=this.beginPending('mission',{phase:'upload',compiled,sent:new Set(),download:[],expectedCount:null,nextDownload:0});this.expected=clone(compiled);this.mission={state:'uploading',compiled,readback:null};this.execution={state:'idle',reached:[]};this.resumeRequired=false;this.event('mission-upload-request',{count:compiled.items.length,world:compiled.worldId});this.send(44,this.target({count:compiled.items.length,mission_type:0}));
  const p=this.pending;p.retryTimer=setInterval(()=>{if(this.pending!==p)return;if(++p.retries>8)return;
   if(p.phase==='upload'&&p.sent.size===0)this.send(44,this.target({count:compiled.items.length,mission_type:0}));
   if(p.phase==='download')this.requestDownload(p);},800);return promise;
 }
 requestDownload(p){if(p.expectedCount===null)this.send(43,this.target({mission_type:0}));else this.send(51,this.target({seq:p.nextDownload,mission_type:0}));}
 missionMessage(m,p){const f=m.fields;
  if(p.phase==='upload'){
   if([51,40].includes(m.id)){if(f.seq>=p.compiled.items.length){this.mission.state='failed';this.failPending('Autopilot yêu cầu seq ngoài mission.');return;}this.send(73,this.target(p.compiled.items[f.seq]));p.sent.add(f.seq);}
   if(m.id===47){if(f.type!==0){this.mission.state='failed';this.failPending(`MISSION_ACK rejected (${f.type}).`);return;}
    if(p.sent.size!==p.compiled.items.length){this.event('premature-ack-ignored');return;}
    p.phase='download';p.retries=0;this.mission.state='verifying';this.event('mission-upload-accepted',{notExecution:true});this.requestDownload(p);}
  }else{
   if(m.id===44){if(f.count!==p.compiled.items.length){this.mission.state='failed';this.failPending('Readback count không khớp.');return;}p.expectedCount=f.count;p.nextDownload=0;this.requestDownload(p);}
   if(m.id===73&&p.expectedCount!==null){if(f.seq!==p.nextDownload)return;p.download.push(f);p.nextDownload++;if(p.nextDownload<p.expectedCount){this.requestDownload(p);return;}
    this.send(47,this.target({type:0,mission_type:0}));const matches=readbackEqual(p.compiled.items,p.download);this.mission.readback=clone(p.download);this.mission.state=matches?'verified':'failed';this.event('mission-readback',{matches,count:p.download.length});if(matches){this.expected=clone(p.compiled);if(p.recovery){const hb=this.samples[0]?.fields;this.resumeRequired=this.freshness(0)&&!!(hb.base_mode&128);this.execution={state:this.freshness(0)&&(hb.base_mode&128)?(hb.custom_mode===3?'observed-active':'observed-armed'):'idle',reached:[]};this.event('mission-recovery-verified',{observedMode:this.snapshot().mode,executionHistoryRestored:false});}this.resolvePending(this.snapshot());}else this.failPending('Mission readback khác nội dung đã gửi.');}
  }
 }
 invalidateConfiguration(reason){if(this.configuration&&!this.configuration.invalidated){this.configuration.invalidated=reason;this.event('configuration-invalidated',{reason,readOnly:true});}}
 configurationObservation(){if(!this.configuration)return null;const o=clone(this.configuration),age=x=>{const {at,...v}=x;return {...v,ageMs:this.clock()-at};};o.firmware=age(o.firmware);o.parameters=Object.fromEntries(Object.entries(o.parameters).map(([n,v])=>[n,age(v)]));return o;}
 configurationReport(){return evaluateConfiguration(this.configurationObservation(),{sessionId:this.sessionId,vehicle:this.vehicle});}
 profileSnapshot(){return makeProfileSnapshot(this.configurationObservation(),{sessionId:this.sessionId,vehicle:clone(this.vehicle)});}
 requireConfiguration(action){const snapshot=this.profileSnapshot();if(!snapshot.comparison.pass){this.event('profile-guard-rejected',{action,profileSnapshot:snapshot});throw Error('Profile chưa đạt: '+snapshot.comparison.state+'; đọc lại cấu hình.');}this.lastProfileGuard={action,snapshot:clone(snapshot)};this.event('profile-guard',{action,readOnly:true,profileSnapshot:snapshot});}
 geoContext(){const h=this.observedHome(),age=id=>this.samples[id]?this.clock()-this.samples[id].at:null;return {sessionId:this.sessionId,vehicle:clone(this.vehicle),home:h?{lat:h.lat,lon:h.lon,amsl:h.amsl}:null,homeAgeMs:age(242),heartbeatAgeMs:age(0)};}
 async planGeography(request){if(this.pending)throw Error('Transaction busy');const compiled=this.compileRequest(request);return geoPlan(request,compiled,this.geodata,this.geoContext());}
 async reviewGeography(request,{planSha256,confirmation,note}={}){if(this.pending)throw Error('Transaction busy');if(request?.version!==2||request?.format!=='aeris-survey-run')throw Error('Reviewed survey v2 required');const plan=await this.planGeography(request),current=this.geoContext();if(this.pending||!homeCheck(current).pass||current.sessionId!==plan.anchor.sessionId||requestIdentity(current.vehicle)!==requestIdentity(plan.anchor.vehicle)||requestIdentity(current.home)!==requestIdentity(plan.anchor.home))throw Error('Home/session changed while computing review; compare again');if(!plan.home.pass||!plan.analysis.canReviewSITL||planSha256!==plan.sha256||confirmation!==plan.sha256.slice(0,12)||typeof note!=='string'||!note.trim()||note.length>2000)throw Error('Geo/Home/policy plan stale or explicit review missing');this.geoReview={requestSha256:plan.requestSha256,sessionId:this.sessionId,vehicle:clone(this.vehicle),planSha256:plan.sha256,plan,approvedAt:new Date().toISOString(),note:note.trim()};this.event('geography-reviewed',{readOnly:true,requestSha256:plan.requestSha256,policy:plan.analysis.policy});return {reviewed:true,approval:clone(this.geoReview)};}
 requireHome(action){const context=this.geoContext(),home=homeCheck(context);if(!home.pass){this.geoReview=null;this.lastGeoGuard=null;this.event('geo-guard-rejected',{action,home});throw Error('Fresh matching Home required before '+action);}this.lastGeoGuard=null;this.event('home-guard',{action,context,home,readOnly:true});}
 async requireGeography(action,compiled){const context=this.geoContext(),home=homeCheck(context);if(!home.pass){this.geoReview=null;this.lastGeoGuard=null;this.event('geo-guard-rejected',{action,home});throw Error('Fresh matching Home required before '+action);}const request=compiled?.sourceRequest??compiled?.sourcePackage;if(request?.format==='aeris-survey-run'&&request.version===2){try{const snapshot=await geoSnapshot(request,compiled,this.geodata,context,this.geoReview,action);const current=this.geoContext();if(requestIdentity(this.geoReview)!==requestIdentity(snapshot.approval)||(action!=='upload'&&this.expected&&requestIdentity(this.expected.sourceRequest??this.expected.sourcePackage)!==requestIdentity(request))||!homeCheck(current).pass||current.sessionId!==context.sessionId||requestIdentity(current.vehicle)!==requestIdentity(context.vehicle)||requestIdentity(current.home)!==requestIdentity(context.home)||this.pending||Date.now()-Date.parse(snapshot.approval.approvedAt)<0||Date.now()-Date.parse(snapshot.approval.approvedAt)>30000)throw Error('Home/session/review changed during snapshot computation');this.requireConfiguration(action);this.lastGeoGuard={action,snapshot};this.event('geo-guard',{action,readOnly:true,geoSnapshot:snapshot});}catch(e){this.lastGeoGuard=null;this.event('geo-guard-rejected',{action,reason:e.message});throw e;}}else{this.lastGeoGuard=null;this.event('home-guard',{action,context,home,readOnly:true});}}
 async readConfiguration(ref=PROFILE_REF){assertProfileReference(ref);const promise=this.beginPending('configuration',{names:[...CONFIGURATION_NAMES],values:{},firmware:null,observationId:randomUUID(),startedAtUTC:new Date().toISOString()});this.configuration=null;this.event('configuration-read-request',{profile:PROFILE_REF,readOnly:true});this.send(76,this.target({command:512,param1:148}));for(const name of CONFIGURATION_NAMES)this.send(20,this.target({param_id:name,param_index:-1}));return promise;}
 async readParameters(names=PARAMETER_READ_ALLOWLIST){
  if(!Array.isArray(names)||names.length<1||names.length>4||new Set(names).size!==names.length||names.some(n=>!PARAMETER_READ_ALLOWLIST.includes(n)))throw Error('Parameter read ngoài allowlist simulator.');
  const promise=this.beginPending('parameters',{names:[...names],values:{}});for(const name of names)this.send(20,this.target({param_id:name,param_index:-1}));return promise;
 }
 async recover(request=null){
  const compiled=request?this.compileRequest(request):clone(this.expected);if(!compiled)throw Error('Chưa có nhiệm vụ kỳ vọng để đối chiếu.');
  const promise=this.beginPending('mission',{phase:'download',recovery:true,compiled,download:[],expectedCount:null,nextDownload:0});this.mission={state:'verifying',compiled,readback:null};this.execution={state:'idle',reached:[]};this.event('mission-recovery-request',{readOnly:true,count:compiled.items.length});this.requestDownload(this.pending);
  const p=this.pending;p.retryTimer=setInterval(()=>{if(this.pending===p&&++p.retries<=8)this.requestDownload(p);},800);return promise;
 }
 reviewResume(request){this.invalidateHeartbeatGap();if(!this.freshness(0)||this.pending||this.ambiguous||this.mission.state!=='verified'||!(this.samples[0]?.fields.base_mode&128)||!this.resumeRequired)throw Error('Cần link mới, readback khớp và phiên armed đang yêu cầu review.');const compiled=this.compileRequest(request);if(JSON.stringify(compiled.sourceRequest??compiled.sourcePackage)!==JSON.stringify(this.expected?.sourceRequest??this.expected?.sourcePackage)||!readbackEqual(compiled.items,this.mission.readback))throw Error('Nguồn review không khớp nhiệm vụ trên autopilot.');this.resumeRequired=false;this.event('operator-resume-reviewed',{readOnly:true,autoCommandSent:false});return this.snapshot();}
 async command(name){const hb=this.samples[0]?.fields;if(!hb)throw Error('Chưa có heartbeat.');const mode=(id)=>({command:176,param1:1,param2:id,observe:f=>f.custom_mode===id});const map={guided:mode(4),auto:mode(3),hold:mode(5),rtl:mode(6),arm:{command:400,param1:1,observe:f=>!!(f.base_mode&128)}};
  const spec=map[name];if(!spec)throw Error('Lệnh không hỗ trợ.');if(name==='arm'&&(!this.preflight().every(c=>c.pass)||hb.custom_mode!==4))throw Error('Cần preflight đạt và GUIDED trước khi arm SITL.');
  if(name==='auto'&&(this.mission.state!=='verified'||!(hb.base_mode&128)||['completed','stopped'].includes(this.execution.state)))throw Error('Cần readback khớp và armed trước AUTO.');
  if(name==='auto'&&this.resumeRequired)throw Error('Cần xác nhận review lại nguồn sau gián đoạn trước AUTO.');
  if(['arm','auto'].includes(name))this.requireConfiguration(name);if(name==='auto')assertMissionProfile(this.expected);if(['arm','auto'].includes(name)){if(this.expected?.sourceRequest?.format==='aeris-survey-run'&&this.expected.sourceRequest.version===2)await this.requireGeography(name,this.expected);else this.requireHome(name);}const promise=this.beginPending('command',{name,command:spec.command,observe:spec.observe,accepted:false,observed:false});this.commandState={name,state:'sent'};this.event('command-sent',{name,simulation:true});this.send(76,this.target({command:spec.command,param1:spec.param1,param2:spec.param2??0}));return promise;
 }
 journal(){return {version:1,simulation:true,world:SITL_WORLD,sessionId:this.sessionId,events:clone(this.events),frames:clone(this.frames),mission:clone(this.mission),expectedRequest:clone(this.expected?.sourceRequest??this.expected?.sourcePackage??null),observed:this.snapshot()};}
}
