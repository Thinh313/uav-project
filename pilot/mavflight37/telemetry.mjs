import {ReplayLink} from './session.mjs';
import {assessPreflight,failsafeExpectations,UNITS,validateProfile} from '../apflight36/preflight.mjs';
import {identity,same,exact,int,bounded} from '../apflight36/types.mjs';
import {liveIssuedProof} from './fence.mjs';
const MODES={0:'STABILIZE',1:'ACRO',3:'AUTO',5:'HOLD',6:'RTL',9:'LAND',16:'HOLD',17:'HOLD'};
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const present=(f,k)=>f.present.includes(k);
export class TelemetryAdapter{
 constructor(target,epoch){this.link=new ReplayLink(target,epoch);this.cache=new Map();this.events=[];this.fenceWireProof=null}
 invalidate(reason){this.link.close(reason);this.cache.clear();this.fenceWireProof=null}
 receive(bytes,meta,t){try{const frames=this.link.receive(bytes,meta,t);if(this.events.length+frames.length>512){this.invalidate('EVIDENCE_BOUND');throw Error('evidence bound')}
   for(const f of frames){this.events.push(structuredClone(f));if(f.id===147&&f.fields.id!==0)continue;this.cache.set(f.id,structuredClone(f))}return frames.length;
  }catch(e){if(this.link.closed)this.invalidate(this.link.reason);throw e}
 }
 attachFence(proof,t){if(!liveIssuedProof(proof,t)||proof?.format!=='aeris-fence-wire-proof37'||proof.origin!=='MOCK_MAVLINK_REPLAY'||!same(proof.target,this.link.target)||proof.epoch!==this.link.epoch||proof.operationalAllowed!==false)throw Error('fence proof binding/live capability');this.fenceWitness=proof;this.fenceWireProof=structuredClone(proof)}
 packet(id,t,age=1500){const f=this.cache.get(id);return!this.link.closed&&f&&f.receiptMs<=t&&t-f.receiptMs<=age?f:null}
 raw(t){int(t,0,1e12,'snapshot time');if(this.link.lastAt!==null&&t<this.link.lastAt||!this.link.tick(t))this.invalidate('SNAPSHOT_STALE');if(this.fenceWitness&&!liveIssuedProof(this.fenceWitness,t))this.fenceWireProof=null;
  const hb=this.packet(0,t),land=this.packet(245,t),gps=this.packet(24,t,3000),ekf=this.packet(193,t),sys=this.packet(1,t),bat=this.packet(147,t,3000),home=this.packet(242,t,30000),pos=this.packet(33,t),fence=this.packet(162,t),ack=this.packet(77,t);
  const partial={},required={},invalid={};
  required.heartbeat=!!hb&&!!land;partial.heartbeat={};if(hb){const f=hb.fields;invalid.heartbeat=f.autopilot!==3||f.type!==2||!(f.base_mode&1)||!Object.hasOwn(MODES,f.custom_mode);partial.heartbeat={armed:!!(f.base_mode&128),mode:MODES[f.custom_mode]??null,landed:land&&[1,2,3,4].includes(land.fields.landed_state)?land.fields.landed_state===1:null,throttleAtMinimum:null}}
  required.gnss=!!gps;partial.gnss={};if(gps){const f=gps.fields;invalid.gnss=![0,1,2,3,4,5,6].includes(f.fix_type);partial.gnss={fix:({0:'NO_FIX',1:'NO_FIX',2:'2D',3:'3D',4:'3D',5:'RTK_FLOAT',6:'RTK_FIXED'})[f.fix_type]??null,satellites:f.satellites_visible===255?null:f.satellites_visible,ephM:present(gps,'h_acc')&&f.h_acc>0?f.h_acc/1000:null,correctionAgeMs:null}}
  // Pinned AP EKF2/3 getVariances() emits sqrt(testRatio); XML calls these "variances".
  required.ekf=!!ekf&&!!sys;partial.ekf={};if(ekf&&sys){const f=ekf.fields,s=sys.fields,ratios=[f.velocity_variance,f.pos_horiz_variance,f.pos_vert_variance,f.compass_variance];invalid.ekf=ratios.some(x=>!finite(x)||x<0||x>10);const initialized=!(f.flags&1024);partial.ekf={attitude:initialized&&!!(f.flags&1),velocity:initialized&&!!(f.flags&2)&&!!(f.flags&4),horizontalPosition:initialized&&!!(f.flags&16),verticalPosition:initialized&&!!(f.flags&32),compass:!!(s.onboard_control_sensors_present&4)&&!!(s.onboard_control_sensors_enabled&4)&&!!(s.onboard_control_sensors_health&4),innovationRatio:invalid.ekf?null:Math.max(...ratios.map(x=>x*x))}}
  required.battery=!!bat;partial.battery={};if(bat){const f=bat.fields;let voltage=null,valid=true,seenGap=false,total=0;
   for(const x of f.voltages){if(x===65535){seenGap=true;continue}if(x===0||seenGap){valid=false;continue}total+=x}
   if(present(bat,'voltages_ext'))for(const x of f.voltages_ext){if(x===0)continue;if(x===65535||seenGap)valid=false;else total+=x}
   if(valid&&total>0)voltage=total/1000;
   partial.battery={voltageV:voltage,temperatureC:f.temperature===32767?null:f.temperature/100,remainingWh:null,uncertaintyWh:null,energyOrigin:null,lowVoltageSinceMs:null,criticalVoltageSinceMs:null};
  }
  required.home=!!home;partial.home=home?{point:[home.fields.longitude/1e7,home.fields.latitude/1e7],amslM:home.fields.altitude/1000,id:null,datumId:null,amslDatumId:null,confirmed:null}:{};
  if(home)invalid.home=Math.abs(home.fields.latitude)>700000000||Math.abs(home.fields.longitude)>1800000000;
  required.link=!!hb;partial.link={downlinkAvailable:!!hb,uplinkVerified:null,rc:null,gcsEverSeenByAP:null,apLastGcsHeartbeatAtMs:null,rcLostSinceMs:null};required.config=false;partial.config={};required.fence=false;partial.fence={};
  const times={heartbeat:[hb,land],gnss:[gps],ekf:[ekf,sys],battery:[bat],home:[home],link:[hb]};
  return{partial,required,invalid,times:Object.fromEntries(Object.entries(times).map(([k,a])=>[k,a.filter(Boolean).map(f=>f.receiptMs)])),
   position:pos?{longitude:pos.fields.lon/1e7,latitude:pos.fields.lat/1e7,amslM:pos.fields.alt/1000,relativeHomeM:pos.fields.relative_alt/1000,timeBootMs:pos.fields.time_boot_ms,bootToHostClock:'NOT_MAPPED',receiptMs:pos.receiptMs}:null,
   gpsDiagnostics:gps?{hdop:gps.fields.eph===65535?null:gps.fields.eph/100,hdopIsMeters:false,rawTimeUsec:gps.fields.time_usec,sourceClock:'BOOT_OR_UNIX_NOT_GUESSED'}:null,
   ekfDiagnostics:ekf?{mapping:'PINNED_COPTER_EKF2_3_MOCK',wireQuantity:'SQRT_INNOVATION_TEST_RATIO',normalizedQuantity:'INNOVATION_TEST_RATIO',realFirmwareCompatibility:'NOT_CHECKED'}:null,
   batteryDiagnostics:bat?{batteryId:0,remainingPercent:bat.fields.battery_remaining===-1?null:bat.fields.battery_remaining,consumedMAh:bat.fields.current_consumed===-1?null:bat.fields.current_consumed,consumedWh:bat.fields.energy_consumed===-1?null:bat.fields.energy_consumed/36,remainingWhKnown:false}:null,
   fenceBreach:fence?{breached:[0,1].includes(fence.fields.breach_status)?fence.fields.breach_status===1:null,count:fence.fields.breach_count,type:fence.fields.breach_type,timeBootMs:fence.fields.breach_time,mitigation:present(fence,'breach_mitigation')?fence.fields.breach_mitigation:null,receiptMs:fence.receiptMs,linkedPlanProven:false,actionCauseProven:false,physicalExecutionProven:false}:null,
   commandAck:ack?{command:ack.fields.command,result:ack.fields.result,receiptMs:ack.receiptMs,transactionCorrelated:false,executionProven:false}:null,
   modeObserved:hb?MODES[hb.fields.custom_mode]??null:null,closed:this.link.closed,reason:this.link.reason,
   operationalAllowed:false,networkSent:false,authentication:'UNSIGNED_NOT_AUTHENTICATED'};
 }
 async assess(profile,t,supplement=null){profile=structuredClone(profile);validateProfile(profile);if(!same(profile.target,this.link.target))throw Error('profile target');const raw=this.raw(t),sources=Object.fromEntries(Object.keys(UNITS).map(k=>[k,null])),provenance={};
  let extra={};if(supplement!==null){supplement=structuredClone(supplement);bounded(supplement,131072);exact(supplement,['format','origin','target','epoch','sources']);if(supplement.format!=='aeris-explicit-mock-supplement37'||supplement.origin!=='SYNTHETIC_ONLY'||!same(supplement.target,this.link.target)||supplement.epoch!==this.link.epoch)throw Error('synthetic supplement context');if(Object.keys(supplement.sources).some(k=>!Object.hasOwn(UNITS,k)))throw Error('supplement lane');extra=supplement.sources}
  for(const k of Object.keys(UNITS)){const s=extra[k],base=raw.partial[k]??{},times=raw.times[k]??[];let value=null;
   if(raw.closed||raw.invalid[k])continue;
   if(s){exact(s,['origin','sourceId','target','epoch','sequence','atMs','unit','value']);if(s.origin!=='SYNTHETIC'||s.epoch!==this.link.epoch||!same(s.target,this.link.target)||s.unit!==UNITS[k])throw Error('supplement provenance');int(s.atMs,0,1e12,'supplement time');if(s.atMs>t||t-s.atMs>profile.maxAgeMs[k])continue;times.push(s.atMs)}
   if(k==='config'){if(s&&this.fenceWireProof&&t-this.fenceWireProof.atMs<=1500){value=s.value;times.push(this.fenceWireProof.atMs)}}
   else if(k==='fence'){if(s&&this.fenceWireProof&&t-this.fenceWireProof.atMs<=1500&&s.value.planSha256===this.fenceWireProof.compiled.sourcePlanSha256){value=s.value;times.push(this.fenceWireProof.atMs)}}
   else if(raw.required[k]){value={...(s?.value??{})};for(const[key,v]of Object.entries(base))if(v!==null)value[key]=v;for(const[key,v]of Object.entries(base))if(v===null&&!Object.hasOwn(value,key))value[key]=null;
    if(k==='gnss'&&!s)value.correctionAgeMs=null;
    if(Object.entries(value).some(([key,v])=>v===null&&!['correctionAgeMs','apLastGcsHeartbeatAtMs','rcLostSinceMs','lowVoltageSinceMs','criticalVoltageSinceMs'].includes(key))||k==='link'&&value.gcsEverSeenByAP===null)value=null;
   }
   if(value!==null&&times.length){sources[k]={origin:'SYNTHETIC',sourceId:'mavflight37-'+k,target:structuredClone(this.link.target),epoch:this.link.epoch,sequence:this.link.sequence,atMs:Math.min(...times),unit:UNITS[k],value};provenance[k]={wireFields:Object.keys(base).filter(key=>base[key]!==null),syntheticSupplementUsed:!!s,physicalEvidence:false}}
  }
  const input={format:'aeris-preflight36',version:1,profile,target:structuredClone(this.link.target),clock:{epoch:this.link.epoch,nowMs:t},sources};
  return{assessment:await assessPreflight(input),failsafe:await failsafeExpectations(input),input,raw,provenance,explicitSyntheticSupplements:supplement!==null,wireOnlyComplete:false,operationalAllowed:false,executionProven:false,emitsFlightCommand:false};
 }
}
