import {Preflight43,ticketValid,validateReadOnlyTX} from './adapter.mjs';
import {profile43,STREAMS,stable} from './profile.mjs';
import {transcript,context,parameter,telemetry,frame,nonfiniteParameter} from './fixtures.mjs';
import {hex,unhex,encodeFull} from '../apstream40/wire.mjs';
export function executeFixture(f){const a=new Preflight43(f.profile,f.context),rows=[];let intent=null,ticket=null,error=null;for(const act of f.actions){try{let out;switch(act.kind){case'RX':a.receive(unhex(act.rawHex),{origin:f.context.origin,context:act.context??f.context,receivedAtMs:act.receipt??act.at},act.now??act.at);break;case'DISCOVER':intent=a.discover(act.at);out={rawHex:intent.rawHex};break;case'WRITTEN':a.written(intent,act.at);break;case'BEGIN':out=a.beginCycle(act.at);break;case'READ_NEXT':intent=a.readNext(act.at);out={rawHex:intent.rawHex};break;case'STREAM':intent=a.stream(act.id,act.at);out={rawHex:intent.rawHex};break;case'FAIL_WRITER':a.writerFailed();break;case'CLOSE':a.invalidate('SOCKET_CLOSED');break;case'TICKET':ticket=a.ticket(act.at);out=ticket;break;case'CHECK_TICKET':out={valid:ticketValid(act.clone?structuredClone(ticket):ticket,a,act.at)};break;case'ASSESS':out=a.assess(act.at);break;default:throw Error('UNKNOWN_FIXTURE_ACTION');}rows.push({kind:act.kind,at:act.at,out:out??null});}catch(e){error=e.message;rows.push({kind:act.kind,at:act.at,error});break;}}const at=rows.at(-1)?.at??0;return {error,rows,assessment:a.assess(Math.max(at,0)),snapshot:a.snapshot(Math.max(at,0))};}
function base(name,expected,modify){const f=transcript();f.name=name;f.expected=expected;modify?.(f);return f;}
export function corpus43(){const cases=[];const add=(n,e,m)=>cases.push(base(n,e,m));
 add('qualified20type READY','READY_SCOPED_READONLY',f=>f.actions.push({kind:'ASSESS',at:100}));
 add('strictnegativeprofile radius31','BLOCKED',f=>{f.profile=profile43(true);f.actions.push({kind:'ASSESS',at:100});});
 for(const [name,mutation] of [
 ['oldfirmware',f=>{const i=f.actions.findIndex(a=>a.kind==='RX'&&a.at===2);const v=JSON.parse(JSON.stringify((awaitless()).latest[148].fields));v.flight_sw_version=67567871;f.actions[i].rawHex=hex(frame(148,v,1));}],
 ['wrongparameter type',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===22).rawHex=hex(parameter('MAV_SYSID',9,{type:9}));}],
 ['fractionalinteger',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===22).rawHex=hex(parameter('MAV_SYSID',9,{value:42.5}));}],
 ['countzero',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===22).rawHex=hex(parameter('MAV_SYSID',9,{count:0}));}],
 ['countchanged',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===24).rawHex=hex(parameter('MAV_GCS_SYSID',10,{count:1370}));}],
 ['badindex',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===22).rawHex=hex(parameter('MAV_SYSID',9,{index:1369}));}],
 ['nonfinitefloat',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===32).rawHex=hex(nonfiniteParameter('BATT_ARM_VOLT',14));}],
 ])add(name,'INVALIDATED',mutation);
 add('partialcohort missing response','UNKNOWN',f=>{f.actions=f.actions.slice(0,f.actions.findIndex(a=>a.kind==='RX'&&a.at===60));f.actions.push({kind:'ASSESS',at:100});});
 add('parameterage expired whiletelemetryfresh','UNKNOWN',f=>{let s=f.seq;for(const at of [2000,4000,6000,8000,10000,11000])for(const id of [0,1,24,33,162,193,242,245])f.actions.push({kind:'RX',rawHex:hex(telemetry(id,s++,at)),at});f.actions.push({kind:'ASSESS',at:11000});});
 add('heartbeat hardloss','INVALIDATED',f=>f.actions.push({kind:'ASSESS',at:4000}));
 add('clockregression','INVALIDATED',f=>f.actions.push({kind:'ASSESS',at:10}));
 add('writerfailed','INVALIDATED',f=>f.actions.push({kind:'FAIL_WRITER',at:100},{kind:'ASSESS',at:100}));
 add('socketclose','INVALIDATED',f=>f.actions.push({kind:'CLOSE',at:100},{kind:'ASSESS',at:100}));
 add('wrongcontext','INVALIDATED',f=>f.actions.push({kind:'RX',rawHex:hex(telemetry(0,f.seq)),at:100,context:context('other')}));
 add('future receipt','INVALIDATED',f=>f.actions.push({kind:'RX',rawHex:hex(telemetry(0,f.seq)),at:100,receipt:101}));
 add('fractionalhostclock','INVALIDATED',f=>f.actions.push({kind:'ASSESS',at:100.5}));
 add('unsafe config observed','BLOCKED',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===42).rawHex=hex(parameter('FENCE_MARGIN',19,{value:40}));f.actions.push({kind:'ASSESS',at:100});});
 for(const [name,id,mut,state] of [['armed',0,x=>x.base_mode|=128,'BLOCKED'],['criticalsystemstate',0,x=>x.system_status=5,'BLOCKED'],['reserved GPS fix',24,x=>x.fix_type=255,'UNKNOWN'],['EKF constantposition',193,x=>x.flags|=128,'BLOCKED'],['notlanded',245,x=>x.landed_state=2,'BLOCKED'],['APprearm unhealthy',1,x=>x.onboard_control_sensors_health&=~268435456,'BLOCKED'],['voltage unknown sentinel',1,x=>x.voltage_battery=65535,'UNKNOWN'],['lowvoltage',1,x=>x.voltage_battery=10000,'BLOCKED'],['HDOP sentinel',24,x=>x.eph=65535,'UNKNOWN'],['HDOP not accuracyM',24,x=>x.eph=250,'BLOCKED'],['GPS nofix',24,x=>x.fix_type=1,'BLOCKED'],['EKF uninitialized',193,x=>x.flags=1024,'BLOCKED'],['fence breached',162,x=>x.breach_status=1,'BLOCKED'],['altitudedatum mismatch',33,x=>x.alt+=5000,'BLOCKED']])add(name,state,f=>{const fields=structuredClone(awaitless().latest[id].fields);if(id===242)fields.q=[0,0,0,0];if('time_boot_ms'in fields)fields.time_boot_ms=100;mut(fields);f.actions.push({kind:'RX',rawHex:hex(frame(id,fields,f.seq)),at:100},{kind:'ASSESS',at:100});});
 add('ACK cannot supply version','UNKNOWN',f=>{f.actions=f.actions.slice(0,3);f.actions.push({kind:'RX',rawHex:hex(frame(77,{command:512,result:0,target_system:255,target_component:190},1)),at:2},{kind:'ASSESS',at:100});});
 add('unsolicited version ignored','UNKNOWN',f=>{f.actions=f.actions.filter(a=>!['DISCOVER','WRITTEN','BEGIN','READ_NEXT'].includes(a.kind));f.actions=f.actions.slice(0,9);f.actions.push({kind:'ASSESS',at:100});});
 add('changedduplicate invalidatescohort','UNKNOWN',f=>{f.actions.push({kind:'RX',rawHex:hex(parameter('GPS_HDOP_GOOD',f.seq-1,{value:180})),at:100},{kind:'ASSESS',at:100});});
 add('foreignparam cannotcomplete','UNKNOWN',f=>{f.actions.find(a=>a.kind==='RX'&&a.at===60).rawHex=hex(parameter('GPS_HDOP_GOOD',28,{system:43}));f.actions.push({kind:'ASSESS',at:100});});
 add('snapshot ticket cloning refused','READY_SCOPED_READONLY',f=>f.actions.push({kind:'TICKET',at:100},{kind:'CHECK_TICKET',clone:true,at:100}));
 return {format:'aeris-preflight43-corpus',version:1,origin:'MOCK_REPLAY_NO_NETWORK',cases};
}
import {baseline} from './fixtures.mjs';function awaitless(){return baseline;}
export function replayCorpus43(c){if(c.format!=='aeris-preflight43-corpus'||c.origin!=='MOCK_REPLAY_NO_NETWORK')throw Error('CORPUS_ORIGIN');return c.cases.map(f=>{const r=executeFixture(f);return {name:f.name,expected:f.expected,actual:r.assessment.state,pass:r.assessment.state===f.expected,error:r.error,reasons:r.assessment.reasons,rows:r.rows};});}
