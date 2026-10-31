import {encode,hex,unhex,crc,DEFINITIONS} from './wire.mjs';
import {FenceAdapter} from './fence.mjs';
import {TelemetryAdapter} from './telemetry.mjs';
import {TARGET,CLOCK,plan,preflight,rectangle,xy,ids} from '../apflight36/fixtures.mjs';
import {digest,same,exact,bounded} from '../apflight36/types.mjs';
// Arbitrary mock parameter expectations, not vehicle recommendations or normalized AP defaults.
export const EXPECTED_PARAMETERS={FENCE_ENABLE:1,FENCE_TYPE:4,FENCE_ACTION:1,FENCE_OPTIONS:0,FS_GCS_ENABLE:1,FS_GCS_TIMEOUT:5,FS_OPTIONS:0,FS_THR_ENABLE:1,FS_EKF_ACTION:1,BATT_FS_LOW_ACT:2,BATT_FS_CRT_ACT:1,BATT_LOW_VOLT:20.4,BATT_CRT_VOLT:19.2,BATT_LOW_TIMER:10};
export const meta=t=>({origin:'MOCK_REPLAY',target:structuredClone(TARGET),epoch:CLOCK.epoch,receivedAtMs:t});
const address={target_system:255,target_component:190,mission_type:1};
export function fieldFloat(raw,id,name,value){const b=unhex(raw),d=DEFINITIONS[id],f=d.fields.find(f=>f.name===name);if(b[0]!==253||10+f.offset+4>b.length-2)throw Error('mutation bound');new DataView(b.buffer).setFloat32(10+f.offset,value,true);const c=crc(b.subarray(1,-2),d.crc);b[b.length-2]=c&255;b[b.length-1]=c>>8;return hex(b)}
export async function fenceCase(id,{polygon=false,mutate=()=>{},expected='WIRE_READBACK_MATCHED',sequence=0,writerFault=false}={}){
 const p=structuredClone(plan());if(polygon)p.regions=[{id:'polygon',inclusion:true,shape:'POLYGON',geometry:rectangle(-500,-500,500,500)},{id:'exclusion',inclusion:false,shape:'CIRCLE',center:xy(100,100),radiusM:20.123456}];
 const{compileFence}=await import('./fence.mjs'),compiled=await compileFence(p),steps=[{op:'begin'}];
 for(let i=0;i<compiled.items.length;i++)steps.push({op:'rx',id:51,fields:{...address,seq:i}});
 steps.push({op:'rx',id:47,fields:{...address,type:0,opaque_id:42}},{op:'rx',id:44,fields:{...address,count:compiled.items.length,opaque_id:42}});
 for(const item of compiled.items)steps.push({op:'rx',id:73,fields:{...address,...item}});
 for(const[name,value]of Object.entries(EXPECTED_PARAMETERS))steps.push({op:'rx',id:22,fields:{param_id:name,param_value:value,param_type:9,param_count:100,param_index:steps.length}});
 mutate(steps);let packetSeq=sequence;
 const sealedSteps=steps.map((s,i)=>{const t=s.t??19000+i;if(s.op!=='rx')return{...s,t};const fields=structuredClone(s.fields),version=s.version??2;if(version===1)for(const f of DEFINITIONS[s.id].fields)if(f.extension)delete fields[f.name];let rawHex=hex(encode(s.id,fields,{system:s.system??1,component:s.component??1,seq:s.seqOverride??packetSeq++%256,version}));if(s.corrupt){const b=unhex(rawHex);b[b.length-1]^=1;rawHex=hex(b)}return{op:'rx',t,rawHex,meta:s.meta??meta(t),nowMs:s.nowMs??t}});
 const body={id,kind:'FENCE',input:{plan:p,expectedParameters:EXPECTED_PARAMETERS,steps:sealedSteps,writerFault},expected:{phase:expected,proofAvailable:expected==='WIRE_READBACK_MATCHED',operationalAllowed:false,executionProven:false,networkSent:false}};
 return{...body,sha256:await digest(body)};
}
export async function runFence(input){exact(input,['plan','expectedParameters','steps','writerFault']);if(typeof input.writerFault!=='boolean'||!Array.isArray(input.steps)||input.steps.length>256)throw Error('fence replay bound');for(const step of input.steps){if(!['begin','rx','disconnect','tick'].includes(step.op))throw Error('forbidden replay operation');exact(step,step.op==='rx'?['op','t','rawHex','meta','nowMs']:['op','t'])}const s=new FenceAdapter(TARGET,CLOCK.epoch,{expectedParameters:input.expectedParameters,idFactory:ids(),persist:input.writerFault?async()=>{throw Error('INJECTED_WRITER_FAILURE')}:undefined}),outputs=[],errors=[];let t=19000;
 for(const step of input.steps){t=Math.max(t,step.t);try{if(step.op==='begin')outputs.push(await s.begin(input.plan,step.t));else if(step.op==='rx')outputs.push(...await s.receive(unhex(step.rawHex),step.meta,step.nowMs));else if(step.op==='disconnect')s.disconnect();else if(step.op==='tick')s.tick(step.t);else throw Error('forbidden replay operation')}catch(e){errors.push(e.message)}}
 const snapshot=s.snapshot(t);let proof=null;try{proof=s.proof(t)}catch{}return{adapter:s,proof,outputs,errors,ledger:s.ledger.rows,output:{phase:snapshot.phase,proofAvailable:snapshot.proofAvailable,operationalAllowed:false,executionProven:false,networkSent:false}};
}
export async function telemetryCase(id,mutate=()=>{},expected={state:'READY_MOCK',gcs:'NOT_TRIGGERED',rc:'NOT_TRIGGERED',battery:'NOT_TRIGGERED'}){
 const base=structuredClone(await preflight()),items=[
  {id:0,fields:{type:2,autopilot:3,base_mode:129,custom_mode:3,system_status:4}},
  {id:245,fields:{landed_state:2}},
  {id:24,fields:{time_usec:'20000000',fix_type:3,satellites_visible:16,lat:108540000,lon:1068070000,alt:10000,eph:80,h_acc:800}},
  {id:193,fields:{flags:55,velocity_variance:.4,pos_horiz_variance:.3,pos_vert_variance:.2,compass_variance:.1}},
  {id:1,fields:{onboard_control_sensors_present:4,onboard_control_sensors_enabled:4,onboard_control_sensors_health:4}},
  {id:147,fields:{id:0,temperature:3500,voltages:[24000,...Array(9).fill(65535)],voltages_ext:Array(4).fill(0),current_consumed:5000,energy_consumed:3600,battery_remaining:80}},
  {id:242,fields:{latitude:108540000,longitude:1068070000,altitude:10000,q:[1,0,0,0]}},
  {id:33,fields:{time_boot_ms:20000,lat:108540000,lon:1068070000,alt:10000,relative_alt:0}},
 ];
 const input={profile:base.profile,supplement:{format:'aeris-explicit-mock-supplement37',origin:'SYNTHETIC_ONLY',target:TARGET,epoch:CLOCK.epoch,sources:base.sources},items,attachFence:true,nowMs:20000};mutate(input);
 input.frames=input.items.map((s,i)=>{const t=s.t??20000;let rawHex=hex(encode(s.id,s.fields,{system:s.system??1,component:s.component??1,seq:i}));if(s.nanField)rawHex=fieldFloat(rawHex,s.id,s.nanField,NaN);return{rawHex,meta:meta(t),nowMs:t}});delete input.items;
 const body={id,kind:'TELEMETRY',input,expected:{...expected,executionProven:false,operationalAllowed:false}};return{...body,sha256:await digest(body)};
}
export async function runTelemetry(input){const t=new TelemetryAdapter(TARGET,CLOCK.epoch);let fence=null;
 if(input.attachFence){const c=await fenceCase('attachment');fence=await runFence(c.input);t.attachFence(fence.proof,20000)}
 const errors=[];for(const f of input.frames)try{t.receive(unhex(f.rawHex),f.meta,f.nowMs)}catch(e){errors.push(e.message)}
 let result;try{result=await t.assess(input.profile,input.nowMs,input.supplement)}catch(e){return{output:{state:'REJECTED',gcs:'UNKNOWN',rc:'UNKNOWN',battery:'UNKNOWN',executionProven:false,operationalAllowed:false},errors:[...errors,e.message],adapter:t}}
 const family=k=>result.failsafe.expectations.find(e=>e.family===k)?.trigger??'UNKNOWN';return{output:{state:result.assessment.state,gcs:family('GCS'),rc:family('RC'),battery:family('BATTERY'),executionProven:false,operationalAllowed:false},result,errors,adapter:t,fence};
}
export async function replayCase(c){exact(c,['id','kind','input','expected','sha256']);bounded(c,262144);const{sha256,...body}=c;if(await digest(body)!==sha256)throw Error('case hash');let r;if(c.kind==='FENCE')r=await runFence(c.input);else if(c.kind==='TELEMETRY')r=await runTelemetry(c.input);else throw Error('case kind');return{caseId:c.id,matched:same(r.output,c.expected),output:r.output,errors:r.errors,operationalAllowed:false}}
export async function makeCorpus(){const cases=[],add=async(...args)=>cases.push(await fenceCase(...args));
 await add('circle-full');await add('polygon-exclusion-full',{polygon:true});await add('sequence-wrap-full',{sequence:250});
 await add('ack-not-proof',{mutate:s=>s.splice(3),expected:'READ_COUNT'});
 await add('partial-readback',{mutate:s=>s.splice(4),expected:'READ_ITEMS'});
 await add('wire-item-mismatch',{mutate:s=>s.find(x=>x.id===73).fields.param1=999,expected:'UNKNOWN'});
 await add('count-mismatch',{mutate:s=>s.find(x=>x.id===44).fields.count=2,expected:'UNKNOWN'});
 await add('opaque-id-mismatch',{mutate:s=>s.find(x=>x.id===44).fields.opaque_id=43,expected:'UNKNOWN'});
 for(const[name,mutation]of[['wrong-system',x=>x.system=2],['wrong-component',x=>x.component=100],['wrong-recipient',x=>x.fields.target_component=0],['wrong-mission-type',x=>x.fields.mission_type=0],['v1-cannot-fence',x=>x.version=1]])await add(name,{mutate:s=>s.filter(x=>x.op==='rx'&&x.id!==22).forEach(mutation),expected:'UPLOAD'});
 await add('partial-config',{mutate:s=>s.pop(),expected:'READ_PARAMETERS'});
 await add('config-mismatch',{mutate:s=>s.find(x=>x.id===22).fields.param_value=0,expected:'UNKNOWN'});
 await add('parameter-encoding-not-guessed',{mutate:s=>s.find(x=>x.id===22).fields.param_type=6,expected:'UNKNOWN'});
 await add('disconnect-invalidates',{mutate:s=>s.push({op:'disconnect'}),expected:'UNKNOWN'});
 await add('stale-invalidates',{mutate:s=>s.push({op:'tick',t:22000}),expected:'UNKNOWN'});
 await add('writer-failure',{writerFault:true,expected:'UNKNOWN'});
 await add('duplicate-request-bounded',{mutate:s=>s.splice(2,0,structuredClone(s[1]))});
 await add('duplicate-request-over-budget',{mutate:s=>s.splice(2,0,...Array.from({length:3},()=>structuredClone(s[1]))),expected:'UNKNOWN'});
 await add('reboot-invalidates',{mutate:s=>s.splice(2,0,{op:'rx',id:33,fields:{time_boot_ms:1000}},{op:'rx',id:33,fields:{time_boot_ms:500}}),expected:'UNKNOWN'});
 await add('crc-corruption',{mutate:s=>s[1].corrupt=true,expected:'UPLOAD'});
 await add('foreign-outer-context',{mutate:s=>s.filter(x=>x.op==='rx').forEach(x=>x.meta={...meta(19000),target:{...TARGET,boot:'foreign'}}),expected:'UNKNOWN'});
 const healthy={state:'READY_MOCK',gcs:'NOT_TRIGGERED',rc:'NOT_TRIGGERED',battery:'NOT_TRIGGERED'},unknown={state:'UNKNOWN',gcs:'UNKNOWN',rc:'UNKNOWN',battery:'UNKNOWN'};
 const tel=async(...a)=>cases.push(await telemetryCase(...a));await tel('explicit-supplements-ready');await tel('wire-only-unknown',i=>i.supplement=null,unknown);
 await tel('gnss-2d-blocked',i=>i.items.find(f=>f.id===24).fields.fix_type=2,{...healthy,state:'BLOCKED'});
 await tel('hdop-not-meters',i=>{i.supplement=null;i.items.find(f=>f.id===24).fields.h_acc=0},unknown);
 await tel('nan-ekf-unknown',i=>i.items.find(f=>f.id===193).nanField='velocity_variance',{...healthy,state:'UNKNOWN'});
 await tel('ekf-square-root-ratio-threshold',i=>{i.profile.limits.maxInnovationRatio=1.5;i.items.find(f=>f.id===193).fields.velocity_variance=1.4},{...healthy,state:'BLOCKED'});
 await tel('stale-ekf-fresh-battery',i=>{const e=i.items.splice(i.items.findIndex(f=>f.id===193),1)[0];e.t=18000;i.items.unshift(e)}, {...healthy,state:'UNKNOWN'});
 await tel('home-mismatch',i=>i.items.find(f=>f.id===242).fields.altitude=12000,{...healthy,state:'UNKNOWN'});
 await tel('AP-heartbeat-history-unknown',i=>{i.supplement.sources.link.value.gcsEverSeenByAP=null;i.supplement.sources.link.value.apLastGcsHeartbeatAtMs=null},{...healthy,state:'UNKNOWN',gcs:'UNKNOWN',rc:'UNKNOWN'});
 await tel('gcs-model-only',i=>i.supplement.sources.link.value.apLastGcsHeartbeatAtMs=0,{...healthy,gcs:'TRIGGER_MODEL'});
 await tel('rc-model-only',i=>{i.supplement.sources.link.value.rc='OBSERVED_LOST';i.supplement.sources.link.value.rcLostSinceMs=0},{...healthy,state:'BLOCKED',rc:'TRIGGER_MODEL'});
 await tel('battery-critical-model-only',i=>i.supplement.sources.battery.value.remainingWh=5,{...healthy,state:'BLOCKED',battery:'CRITICAL_MODEL'});
 await tel('normalized-config-mismatch',i=>i.supplement.sources.config.value.gcs.action='LAND',{...healthy,state:'BLOCKED'});
 await tel('foreign-primary-peer',i=>i.items.forEach(f=>f.component=100),unknown);
 await tel('stale-snapshot',i=>i.nowMs=24000,unknown);
 await tel('no-fence-proof',i=>i.attachFence=false,unknown);
 await tel('ack-and-breach-not-execution',i=>{i.items[0].fields.custom_mode=6;i.items.push({id:77,fields:{command:400,result:0,target_system:255,target_component:190}},{id:162,fields:{breach_status:1,breach_count:1,breach_time:19000,breach_type:3}})});
 return{format:'aeris-mavflight-corpus37',version:1,origin:'MOCK_ONLY',cases,operationalAllowed:false};
}
export async function replayCorpus(c){exact(c,['format','version','origin','cases','operationalAllowed']);if(c.format!=='aeris-mavflight-corpus37'||c.version!==1||c.origin!=='MOCK_ONLY'||c.operationalAllowed!==false||!Array.isArray(c.cases)||c.cases.length>64||new Set(c.cases.map(x=>x.id)).size!==c.cases.length)throw Error('corpus scope');const results=[];for(const x of c.cases)results.push(await replayCase(x));return{status:results.every(r=>r.matched)?'MOCK_PASS':'FAIL',caseCount:results.length,corpusSha256:await digest(c),results,operationalAllowed:false,networkSent:false}};
