import {FullFramer,encodeFull,unhex,hex} from './wire.mjs';
import {MockJournal} from './journal.mjs';
import {TelemetryAdapter} from '../mavflight37/telemetry.mjs';
import {bind,liveBinding} from '../firmware38/contract.mjs';
import {ParameterReadback} from '../firmware38/readback.mjs';
import {parameterFrame,decodeParameter} from '../firmware38/wire.mjs';
import {mapPolicy,evaluateFailsafe} from '../firmware38/policy.mjs';
import {assessAltitude} from '../firmware38/altitude.mjs';
import {validateProfile} from '../apflight36/preflight.mjs';
import {same,canonical,exact,bounded,int} from '../apflight36/types.mjs';
const PROOFS=new WeakMap();
const NO={operationalAllowed:false,flightAuthority:false,executionProven:false,authenticated:false,networkSent:false,emitsFlightCommand:false};
const TELEMETRY=new Set([0,1,24,33,65,77,147,162,193,242,245]);
export function liveDiscoveryProof(p,t){const w=PROOFS.get(p);return !!w&&canonical(p)===w.canonical&&w.owner.current(t);}
export class APStream40 {
 #contract;#framer=new FullFramer();#journal;#telemetry;#reader=null;#binding=null;
 #phase='WAIT_HEARTBEAT';#reason=null;#heartbeat=null;#pending=null;#used=false;#ack=null;
 #now=null;#lastAt=null;#seq=null;#boot=new Map();#busy=false;#generation=0;#persist;#idFactory;
 #counts={accepted:0,foreign:0,duplicate:0,reordered:0,opaque:0,signed:0,auxiliary:0,unsolicitedVersion:0};
 constructor(contract,{persist=async()=>{},idFactory=()=>crypto.randomUUID()}={}){
  bounded(contract,16384);exact(contract,['format','version','origin','id','revision','target','epoch','profile','encoding','allowLegacy','sourceBundleSha256','expected','references','maxAgeMs','operationalAllowed']);
  if(contract.format!=='aeris-firmware-contract38'||contract.version!==1||contract.origin!=='SYNTHETIC'||contract.operationalAllowed!==false||typeof persist!=='function'||typeof idFactory!=='function')throw Error('REVIEWED_MOCK_CONTRACT');
  this.#contract=structuredClone(contract);this.#persist=persist;this.#idFactory=idFactory;
  this.#journal=new MockJournal(rows=>persist({stream:'FULL_STREAM40',rows}));this.#telemetry=new TelemetryAdapter(contract.target,contract.epoch);
 }
 invalidate(reason){if(this.#phase==='INVALIDATED')return;this.#reason=reason;this.#phase='INVALIDATED';this.#generation++;this.#pending=null;this.#heartbeat=null;this.#framer.close(reason);this.#journal.revoke();this.#reader?.invalidate(reason);this.#telemetry.invalidate(reason);this.#binding=null;}
 disconnect(){this.invalidate('DISCONNECTED_NEW_INSTANCE_REQUIRED');}
 loseOwner(){this.invalidate('OWNER_LOST');}
 tick(t){try{int(t,0,1e12,'now');if(this.#phase==='INVALIDATED')return false;
  if(this.#now!==null&&t<this.#now)throw Error('HOST_CLOCK_REGRESSION');if(this.#lastAt!==null&&(t<this.#lastAt||t-this.#lastAt>1500))throw Error('TRANSPORT_STALE');this.#now=t;this.#framer.tick(t);
  if(this.#pending&&t>this.#pending.deadline)throw Error('DISCOVERY_TIMEOUT');
  if(this.#binding&&!liveBinding(this.#binding,t))throw Error('FIRMWARE_BINDING_STALE');if(this.#reader&&!this.#reader.tick(t))throw Error('READBACK_REVOKED');return true;
 }catch(e){this.invalidate(e.message);return false;}}
 async #record(kind,data,t,effect=()=>{}){try{return await this.#journal.append(kind,data,t,effect);}catch(e){this.invalidate('WRITER_UNCERTAIN:'+e.message);throw e;}}
 async startDiscovery(t){if(this.#busy){this.invalidate('CONCURRENT_DISCOVERY');throw Error('CONCURRENT_DISCOVERY');}
  if(!this.tick(t)||this.#used||!this.#heartbeat||t<this.#heartbeat.atMs||t-this.#heartbeat.atMs>1500)throw Error('FRESH_SELECTED_AP_HEARTBEAT_REQUIRED');
  this.#busy=true;const generation=this.#generation;
  try{const out=await this.#record('REQUEST_VERSION_INTENT_MOCK',{target:this.#contract.target,epoch:this.#contract.epoch,command:512,messageId:148},t,()=>{
   this.#used=true;this.#phase='DISCOVERY_PENDING';this.#pending={atMs:t,deadline:t+1500};
   // One command255 then typed reader0..27: one mock GCS sequence across the seam.
   const b=encodeFull(76,{target_system:this.#contract.target.system,target_component:this.#contract.target.component,command:512,confirmation:0,param1:148},{system:255,component:190,seq:255});
   return {channel:'MOCK_BUFFER_ONLY',id:76,command:512,requestedMessage:148,rawHex:hex(b),...NO};
  });if(generation!==this.#generation||!this.tick(t))throw Error('REVOKED_BEFORE_PUBLICATION');return out;
  }catch(e){this.invalidate(e.message);throw e;}finally{this.#busy=false;}
 }
 #context(meta,t){exact(meta,['origin','target','epoch','receivedAtMs']);int(meta.receivedAtMs,0,1e12,'receipt');
  if(meta.origin!=='MOCK_REPLAY'||!same(meta.target,this.#contract.target)||meta.epoch!==this.#contract.epoch)throw Error('FOREIGN_CONTEXT_SESSION_BOOT_LINK_EPOCH');
  if(meta.receivedAtMs>t||t-meta.receivedAtMs>1500||this.#lastAt!==null&&meta.receivedAtMs<this.#lastAt)throw Error('RECEIPT_CLOCK');
 }
 #admit(f){if(f.system!==this.#contract.target.system||f.component!==this.#contract.target.component){this.#counts.foreign++;return 'FOREIGN';}
  if(!f.known){this.#counts.opaque++;if(this.#used)throw Error('TARGET_OPAQUE_FRAME_UNCERTAIN');this.#heartbeat=null;this.#phase='WAIT_HEARTBEAT';return 'OPAQUE';}
  if(f.signed){this.#counts.signed++;if(this.#used)throw Error('TARGET_SIGNED_UNVERIFIED');this.#heartbeat=null;this.#phase='WAIT_HEARTBEAT';return 'SIGNED_UNVERIFIED';}
  if(f.id===0&&(f.fields.autopilot!==3||f.fields.type!==2)){if(this.#used)throw Error('TARGET_HEARTBEAT_CHANGED');this.#heartbeat=null;this.#phase='WAIT_HEARTBEAT';}
  if(this.#binding){
   if(f.id===148&&!same(f.fields,this.#binding.announcement.fields))throw Error('FIRMWARE_IDENTITY_OR_CAPABILITY_CHANGED');
   if(f.id===22&&Object.hasOwn(this.#reader.values,f.fields.param_id)){const p=parameterFrame(unhex(f.rawHex)),old=this.#reader.values[p.fields.param_id],value=decodeParameter(p.valueBytes,p.fields.param_type,this.#binding.encoding);
    if(value!==old.value||p.fields.param_type!==old.type||p.fields.param_count!==this.#reader.count)throw Error('PARAMETER_CHANGED');}
  }
  if(this.#seq!==null){const d=(f.seq-this.#seq+256)%256;if(d===0){this.#counts.duplicate++;return 'DUPLICATE';}if(d===128)throw Error('SEQUENCE_HALF_RANGE_AMBIGUOUS');if(d>128){this.#counts.reordered++;return 'REORDERED';}}
  if('time_boot_ms'in f.fields){const old=this.#boot.get(f.id),next=f.fields.time_boot_ms;if(old!==undefined&&(next-old+2**32)%2**32>=2**31)throw Error('AP_BOOT_CLOCK_REGRESSION');this.#boot.set(f.id,next);}
  this.#seq=f.seq;this.#counts.accepted++;return 'ACCEPTED';
 }
 #telemetryBridge(f,meta,t){
  this.#telemetry.link.check(meta,t);this.#telemetry.link.lastSeq=f.seq;this.#telemetry.link.sequence=this.#counts.accepted;
  if(TELEMETRY.has(f.id)&&!(f.id===147&&f.fields.id!==0))this.#telemetry.cache.set(f.id,structuredClone({...f,receiptMs:f.firstByteAtMs,target:this.#contract.target,epoch:this.#contract.epoch,sourceSequence:this.#counts.accepted}));
 }
 async receive(chunk,meta,t){if(this.#busy){this.invalidate('CONCURRENT_RECEIVE');throw Error('CONCURRENT_RECEIVE');}if(!this.tick(t))throw Error('INVALIDATED:'+this.#reason);
  this.#busy=true;const generation=this.#generation,out=[];
  try{this.#context(meta,t);if(!(chunk instanceof Uint8Array)||chunk.length>16384)throw Error('CHUNK_BOUND');
   chunk=chunk.slice();meta=structuredClone(meta);
   // Raw chunk intent retained before parse/semantic effects; mock persistence only.
   await this.#record('RX_CHUNK_MOCK',{rawHex:hex(chunk),receivedAtMs:meta.receivedAtMs,context:structuredClone(meta)},t);
   const frames=this.#framer.push(chunk,meta.receivedAtMs,t);this.#lastAt=meta.receivedAtMs;
   for(const f of frames){
    let admission;try{admission=this.#admit(f);}catch(e){await this.#record('FRAME_REJECTED',{rawHex:f.rawHex,id:f.id,reason:e.message,firstByteAtMs:f.firstByteAtMs,lastByteAtMs:f.lastByteAtMs},t);throw e;}
    await this.#record('FRAME_'+admission,{rawHex:f.rawHex,id:f.id,seq:f.seq,known:f.known,crcVerified:f.crcVerified,signed:f.signed,firstByteAtMs:f.firstByteAtMs,lastByteAtMs:f.lastByteAtMs},t);
    if(admission!=='ACCEPTED')continue;const fm={...structuredClone(meta),receivedAtMs:f.firstByteAtMs};this.#telemetryBridge(f,fm,t);
    if(f.id===0){if(f.fields.autopilot===3&&f.fields.type===2){this.#heartbeat={atMs:f.firstByteAtMs};if(!this.#used)this.#phase='PEER_OBSERVED';}else if(this.#used)throw Error('TARGET_HEARTBEAT_CHANGED');}
    if(f.id===77&&this.#pending){const p=f.fields;
     if(f.version===2&&p.command===512&&p.target_system===255&&p.target_component===190){this.#ack={result:p.result,atMs:f.firstByteAtMs,executionProven:false,causalityProven:false};if(![0,5].includes(p.result))throw Error('DISCOVERY_NACK');}
    }
    if(f.id===148&&!this.#binding){
     if(!this.#pending){this.#counts.unsolicitedVersion++;continue;}
     if(f.firstByteAtMs<this.#pending.atMs||f.lastByteAtMs>this.#pending.deadline)throw Error('VERSION_OUTSIDE_REQUEST_WINDOW');
     const b=bind(this.#contract,unhex(f.rawHex),fm,t);if(b.status!=='MATCHED_MOCK')throw Error('FIRMWARE_CONTRACT:'+b.reason);
     this.#binding=b;this.#pending=null;this.#reader=new ParameterReadback(b,{idFactory:this.#idFactory,persist:rows=>this.#persist({stream:'PARAMETERS38',rows:structuredClone(rows)})});this.#phase='READING_PARAMETERS';out.push(await this.#reader.begin(t));
    }else if(this.#reader&&f.id===22){out.push(...await this.#reader.receive(unhex(f.rawHex),fm,t));if(this.#reader.phase==='UNKNOWN')throw Error('TYPED_READBACK:'+this.#reader.reason);if(this.#reader.phase==='MATCHED_MOCK')this.#phase='MOCK_READBACK_READY';}
    else if(!TELEMETRY.has(f.id)&&f.id!==148)this.#counts.auxiliary++;
    // Central validated full-stream sequence bridges skipped semantic message IDs.
    if(this.#reader){this.#reader.link.check(fm,t);this.#reader.link.lastSeq=f.seq;}
   }
   if(generation!==this.#generation||!this.tick(t))throw Error('REVOKED_BEFORE_PUBLICATION');
   if(out.some(p=>!p||p.id!==20||p.networkSent!==false))throw Error('OUTPUT_WHITELIST');return out.map(p=>structuredClone(p));
  }catch(e){this.invalidate(e.message);throw e;}finally{this.#busy=false;}
 }
 current(t){if(this.#busy||!this.tick(t)||this.#phase!=='MOCK_READBACK_READY')return false;try{return !!this.#reader.proof(t);}catch{return false;}}
 proof(t){if(!this.current(t))throw Error('CURRENT_READONLY_WITNESS_REQUIRED');const p={format:'aeris-apstream40-proof',version:1,origin:'MOCK_REPLAY',target:structuredClone(this.#contract.target),epoch:this.#contract.epoch,atMs:t,
  typedReadback:structuredClone(this.#reader.proof(t)),requestedFirmwareObserved:true,requestCausalityProven:false,realFirmwareProven:false,sourceBinaryAssociation:'NOT_CHECKED',restoreAuthorityAllowed:false,...NO};PROOFS.set(p,{owner:this,canonical:canonical(p)});return p;}
 snapshot(t){this.tick(t);return {format:'aeris-apstream40-snapshot',version:1,phase:this.#phase,reason:this.#reason,target:structuredClone(this.#contract.target),epoch:this.#contract.epoch,counts:{...this.#counts},ack:structuredClone(this.#ack),framer:this.#framer.snapshot(),inspectionAvailable:this.current(t),parameterPhase:this.#reader?.phase??null,...NO};}
 async inspect(profile,t,{apState=null,altitude=null}={}){
  if(this.#busy){this.invalidate('INSPECT_DURING_WRITE');throw Error('INSPECT_DURING_WRITE');}if(!this.tick(t))return {status:'UNKNOWN',reason:this.#reason,...NO};this.#busy=true;const generation=this.#generation;
  try{profile=structuredClone(profile);apState=structuredClone(apState);altitude=structuredClone(altitude);bounded({profile,apState,altitude},262144);validateProfile(profile);if(!same(profile.target,this.#contract.target))throw Error('PREFLIGHT_TARGET');
   const preflight=this.#binding?.contract.profile==='PINNED_COPTER471'?await this.#telemetry.assess(profile,t):{assessment:{state:'UNKNOWN'},raw:null,...NO};
   if(generation!==this.#generation||!this.tick(t))throw Error('INSPECTION_REVOKED');let proof=null;try{proof=this.#reader?.proof(t);}catch{}
   return {status:proof?'READONLY_MOCK_INSPECTION':'PARTIAL_UNKNOWN',preflight,policy:proof?mapPolicy(proof,t):{status:'UNKNOWN'},failsafe:proof&&apState?evaluateFailsafe(proof,apState,t):{status:'UNKNOWN'},altitude:proof&&altitude?assessAltitude(proof,altitude,t):{state:'UNKNOWN'},
    normalizedPolicyEquivalent:false,remainingWhProven:false,autopilotEnforcementProven:false,sourceBinaryAssociation:'NOT_CHECKED',...NO};
  }catch(e){this.invalidate(e.message);throw e;}finally{this.#busy=false;}
 }
 audit(){return {fullStream:this.#journal.rows(),parameters:structuredClone(this.#reader?.ledger.rows??[])};}
}
