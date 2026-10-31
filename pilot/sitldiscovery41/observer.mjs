import {FullFramer,encodeFull,hex,unhex} from '../apstream40/wire.mjs';
import {parameterFrame,decodeParameter} from '../firmware38/wire.mjs';
import {same,canonical,int} from '../apflight36/types.mjs';
const ISSUED=new WeakMap();
export const NAMES=['MAV_SYSID','SERIAL0_PROTOCOL','FS_GCS_ENABLE','FS_GCS_TIMEOUT','FENCE_ENABLE','FENCE_TYPE','BATT_MONITOR','FS_OPTIONS'];
export const DENIED={flightAuthority:false,operationalAllowed:false,authenticated:false,executionProven:false};
export function liveWitness(p,t){const s=ISSUED.get(p);return !!s&&canonical(p)===s.canonical&&s.owner.current(t);}
/** Actual local-SITL observations only; cannot authorize any flight/parameter mutation. */
export class Observer41 {
 #manifest;#framer=new FullFramer();#phase='WAIT_HEARTBEAT';#reason=null;#seq=null;#txSeq=0;#hb=null;#now=-1;#version=null;#pending=null;#requested=false;#values={};#paramPending=null;#generation=0;#boot=new Map();#events=[];#preamble=[];#wireStarted=false;
 constructor(manifest){
  if(manifest.scope!=='OWNED_DISARMED_REAL_SITL_ONLY'||manifest.binarySha256!=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'||manifest.flightVersion!==67568127||manifest.customCommit!=='dbe79216'||!manifest.containerId||!Number.isSafeInteger(manifest.guestVMInitPid)||manifest.guestVMInitPid<=0||manifest.system!==42||manifest.component!==1)throw Error('OWNED_PINNED_SIMULATOR_REQUIRED');
  this.#manifest=structuredClone(manifest);
 }
 loss(reason='SOCKET_CLOSED'){if(this.#phase==='INVALIDATED')return;this.#phase='INVALIDATED';this.#reason=reason;this.#generation++;this.#pending=null;this.#paramPending=null;this.#framer.close(reason);}
 tick(t){int(t,0,1e12,'clock');if(this.#phase==='INVALIDATED')return false;if(t<this.#now||this.#hb&&t-this.#hb.atMs>3000||this.#pending&&t>this.#pending.deadline){this.loss('CLOCK_HEARTBEAT_OR_DISCOVERY_STALE');return false;}this.#now=t;try{this.#framer.tick(t);}catch(e){this.loss(e.message);return false;}return true;}
 frames(bytes,meta,t){if(meta.origin!=='OBSERVED_OWNED_SITL'||!same(meta.context,this.#manifest)||meta.receivedAtMs>t||t-meta.receivedAtMs>1500||!this.tick(t))throw Error('OBSERVATION_CONTEXT_OR_STALE');
  if(!this.#wireStarted){const start=bytes.findIndex(b=>b===253||b===254),prefix=start<0?bytes:bytes.slice(0,start);this.#preamble.push(...prefix);
   if(this.#preamble.length>1024||prefix.some(b=>b!==10&&b!==13&&b!==9&&(b<32||b>126))){this.loss('UNREVIEWED_SITL_PREAMBLE');throw Error(this.#reason);}
   if(start<0)return [];if(this.#preamble.length&&!new TextDecoder().decode(Uint8Array.from(this.#preamble)).includes('Init ArduCopter V4.7.1 (dbe79216)')){this.loss('WRONG_BOOT_BANNER');throw Error(this.#reason);}this.#wireStarted=true;bytes=bytes.slice(start);
  }
  const frames=this.#framer.push(bytes,meta.receivedAtMs,t),out=[];
  for(const f of frames){const target=f.system===42&&f.component===1;let label='ACCEPTED';
   if(!target)label='FOREIGN_TARGET';else if(!f.known||f.signed){this.loss('UNSUPPORTED_OR_UNAUTHENTICATED_SELECTED_FRAME');throw Error(this.#reason);}
   if(target&&this.#version&&f.id===148&&!same(f.fields,this.#version.fields)){this.loss('FIRMWARE_CHANGED');throw Error(this.#reason);}
   if(target&&this.#seq!==null){const d=(f.seq-this.#seq+256)%256;if(!d)label='DUPLICATE';else if(d===128){this.loss('SEQUENCE_AMBIGUOUS');throw Error(this.#reason);}else if(d>128)label='REORDERED';}
   this.#events.push({id:f.id,label,rawHex:f.rawHex,firstByteAtMs:f.firstByteAtMs,lastByteAtMs:f.lastByteAtMs});if(this.#events.length>4096){this.loss('EVIDENCE_BOUND');throw Error(this.#reason);}if(label!=='ACCEPTED')continue;
   this.#seq=f.seq;if('time_boot_ms'in f.fields){const old=this.#boot.get(f.id),v=f.fields.time_boot_ms;if(old!==undefined&&(v-old+2**32)%2**32>=2**31){this.loss('AP_BOOT_REGRESSION');throw Error(this.#reason);}this.#boot.set(f.id,v);}
   if(f.id===0){if(f.fields.type!==2||f.fields.autopilot!==3||f.fields.base_mode&128){this.loss('NOT_DISARMED_SELECTED_COPTER');throw Error(this.#reason);}this.#hb={atMs:f.firstByteAtMs,fields:structuredClone(f.fields)};if(!this.#requested)this.#phase='PEER_OBSERVED';}
   if(f.id===148&&this.#pending){const v=f.fields,bits=BigInt(v.capabilities),cast=!!(bits&131072n),byte=!!(bits&16n);
    if(f.firstByteAtMs<this.#pending.atMs||f.lastByteAtMs>this.#pending.deadline||v.flight_sw_version!==this.#manifest.flightVersion||String.fromCharCode(...v.flight_custom_version)!==this.#manifest.customCommit||cast&&byte||(bits&(8192n|16384n|4n))!==(8192n|16384n|4n)){this.loss('VERSION_BUILD_CAPABILITY_MISMATCH');throw Error(this.#reason);}
    const encoding=cast?'C_CAST':byte?'BYTEWISE':bits&2n?'C_CAST':null;if(!encoding){this.loss('PARAMETER_ENCODING_UNKNOWN');throw Error(this.#reason);}
    this.#version={rawHex:f.rawHex,fields:structuredClone(v),encoding,atMs:f.firstByteAtMs,uidZeroSimulatorException:v.uid==='0',sourceBinaryAssociation:'OBSERVED_VERSION_AND_OWNED_BINARY_METADATA',sourceBuildReproduced:false};this.#pending=null;this.#phase='VERSION_OBSERVED';
   }
   if(f.id===22&&this.#version){const p=parameterFrame(unhex(f.rawHex)),n=p.fields.param_id;
    if(Object.hasOwn(this.#values,n)){const value=decodeParameter(p.valueBytes,p.fields.param_type,this.#version.encoding);if(this.#values[n].value!==value||this.#values[n].type!==p.fields.param_type){this.loss('PARAMETER_CHANGED');throw Error(this.#reason);}}
    if(this.#paramPending?.name===n){if(t>this.#paramPending.deadline||!p.fields.param_count||p.fields.param_index!==65535&&p.fields.param_index>=p.fields.param_count){this.loss('PARAMETER_DEADLINE_OR_INDEX');throw Error(this.#reason);}
     this.#values[n]={type:p.fields.param_type,value:decodeParameter(p.valueBytes,p.fields.param_type,this.#version.encoding),count:p.fields.param_count,index:p.fields.param_index,rawHex:f.rawHex,atMs:f.firstByteAtMs};this.#paramPending=null;
    }
   }
   out.push(f);
  }return out;
 }
 #packet(id,fields){return encodeFull(id,fields,{system:255,component:190,seq:this.#txSeq++%256});}
 heartbeat(){if(this.#phase==='INVALIDATED')throw Error('NO_OUTPUT_AFTER_LOSS');return this.#packet(0,{type:6,autopilot:8,base_mode:0,custom_mode:0,system_status:4});}
 discovery(t){if(!this.tick(t)||this.#requested||!this.#hb||t-this.#hb.atMs>1500)throw Error('FRESH_DISARMED_HEARTBEAT_REQUIRED');this.#requested=true;this.#pending={atMs:t,deadline:t+1500};this.#phase='DISCOVERY_PENDING';return this.#packet(76,{target_system:42,target_component:1,command:512,param1:148,confirmation:0});}
 read(name,t){if(!this.tick(t)||!this.#version||this.#paramPending||!NAMES.includes(name)||Object.hasOwn(this.#values,name))throw Error('ONE_PASS_READONLY_PARAMETER_REQUIRED');this.#paramPending={name,deadline:t+1500};return this.#packet(20,{target_system:42,target_component:1,param_id:name,param_index:-1});}
 current(t){return this.tick(t)&&!!this.#version&&!!this.#hb&&t-this.#hb.atMs<=1500;}
 witness(t){if(!this.current(t))throw Error('LIVE_SITL_WITNESS_REQUIRED');const p={format:'aeris-owned-sitl41-witness',context:structuredClone(this.#manifest),version:structuredClone(this.#version),atMs:t,parameterSnapshot:structuredClone(this.#values),parameterSnapshotOperationallyValid:false,hardwareIdentityProven:false,restorable:false,...DENIED};ISSUED.set(p,{owner:this,canonical:canonical(p)});return p;}
 snapshot(t){this.tick(t);return {phase:this.#phase,reason:this.#reason,context:structuredClone(this.#manifest),version:structuredClone(this.#version),parameters:structuredClone(this.#values),liveWitnessAvailable:this.current(t),disarmedObserved:!!this.#hb,preambleHex:hex(Uint8Array.from(this.#preamble)),frameCount:this.#events.length,events:structuredClone(this.#events),...DENIED};}
}
