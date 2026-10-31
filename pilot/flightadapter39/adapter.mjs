import {UnionFramer} from './framer.mjs';
import {TelemetryAdapter} from '../mavflight37/telemetry.mjs';
import {unhex} from '../mavflight37/wire.mjs';
import {bind,liveBinding} from '../firmware38/contract.mjs';
import {ParameterReadback,liveReadProof} from '../firmware38/readback.mjs';
import {mapPolicy,evaluateFailsafe} from '../firmware38/policy.mjs';
import {assessAltitude} from '../firmware38/altitude.mjs';
import {parameterFrame,decodeParameter} from '../firmware38/wire.mjs';
import {Ledger} from '../apflight36/ledger.mjs';
import {validateProfile} from '../apflight36/preflight.mjs';
import {canonical,exact,same,int,bounded} from '../apflight36/types.mjs';

const ISSUED=new WeakMap();
const DENIED={operationalAllowed:false,executionProven:false,authenticated:false,
  flightAuthority:false,networkSent:false,emitsFlightCommand:false};
export function liveInspection(proof,t){const w=ISSUED.get(proof);return !!w&&
  canonical(proof)===w.canonical&&w.owner.current(t);}

/** No socket, command API, restore API or automatic renewal. Readonly mock inspection. */
export class FlightAdapter39 {
  #contract; #framer=new UnionFramer(); #telemetry; #reader=null; #binding=null;
  #audit; #phase='WAITING_FIRMWARE'; #reason=null; #busy=false; #generation=0;
  #lastNow=null; #lastAt=null; #seq=null; #boot=new Map();
  #counts={accepted:0,foreign:0,duplicate:0,reordered:0}; #persist; #idFactory;
  constructor(contract,{persist=async()=>{},idFactory=()=>crypto.randomUUID()}={}){
    bounded(contract,16384);
    exact(contract,['format','version','origin','id','revision','target','epoch','profile','encoding',
      'allowLegacy','sourceBundleSha256','expected','references','maxAgeMs','operationalAllowed']);
    if(contract.format!=='aeris-firmware-contract38'||contract.version!==1||contract.origin!=='SYNTHETIC'||
      contract.operationalAllowed!==false||typeof persist!=='function'||typeof idFactory!=='function')throw Error('REVIEWED_CONTRACT_REQUIRED');
    this.#contract=structuredClone(contract);
    // The full source-bound contract is validated by F38 bind, not a restored witness.
    this.#telemetry=new TelemetryAdapter(this.#contract.target,this.#contract.epoch);
    this.#persist=persist;this.#idFactory=idFactory;
    this.#audit=new Ledger(rows=>persist({stream:'SESSION39',rows:structuredClone(rows)}),idFactory);
  }
  invalidate(reason){
    if(this.#phase==='INVALIDATED')return;
    this.#phase='INVALIDATED';this.#reason=reason;this.#generation++;
    this.#framer.close(reason);this.#reader?.invalidate(reason);
    this.#telemetry.invalidate(reason);this.#audit.revoke();this.#binding=null;
  }
  disconnect(){this.invalidate('DISCONNECTED_NEW_INSTANCE_REQUIRED');}
  loseOwner(reason='OWNER_LOST'){this.invalidate(reason);}
  tick(t){
    try{int(t,0,1e12,'adapter clock');if(this.#phase==='INVALIDATED')return false;
      if(this.#lastNow!==null&&t<this.#lastNow)throw Error('HOST_NOW_REGRESSION');
      if(this.#lastAt!==null&&(t<this.#lastAt||t-this.#lastAt>1500))throw Error('SESSION_RECEIPT_STALE');
      this.#lastNow=t;this.#framer.tick(t);
      if(this.#binding&&!liveBinding(this.#binding,t))throw Error('FIRMWARE_BINDING_STALE');
      if(this.#reader&&!this.#reader.tick(t))throw Error('READBACK_REVOKED');
      return true;
    }catch(e){this.invalidate(e.message);return false;}
  }
  current(t){
    if(this.#busy||!this.tick(t)||this.#phase!=='MOCK_READBACK_READY')return false;
    try{return liveReadProof(this.#reader.proof(t),t);}catch{return false;}
  }
  #context(meta,t){
    exact(meta,['origin','target','epoch','receivedAtMs']);
    if(meta.origin!=='MOCK_REPLAY'||!same(meta.target,this.#contract.target)||meta.epoch!==this.#contract.epoch)throw Error('FOREIGN_SESSION_BOOT_LINK_OR_EPOCH');
    int(meta.receivedAtMs,0,1e12,'receipt');
    if(meta.receivedAtMs>t||t-meta.receivedAtMs>1500||this.#lastAt!==null&&meta.receivedAtMs<this.#lastAt)throw Error('CONTEXT_RECEIPT_CLOCK');
  }
  async #record(kind,data,t,effect=()=>{}){
    try{return await this.#audit.append(kind,data,t,effect);}catch(e){this.invalidate('SESSION_WRITER_UNCERTAIN:'+e.message);throw e;}
  }
  #admit(f){
    const target=this.#contract.target;
    if(f.system!==target.system||f.component!==target.component){this.#counts.foreign++;return 'FOREIGN_SENDER';}
    if(this.#seq!==null){const d=(f.seq-this.#seq+256)%256;
      if(!d){this.#counts.duplicate++;return 'DUPLICATE';}
      if(d===128)throw Error('AMBIGUOUS_SEQUENCE_HALF_RANGE');
      if(d>128){this.#counts.reordered++;return 'REORDERED';}
    }
    if('time_boot_ms' in f.fields){const previous=this.#boot.get(f.id),v=f.fields.time_boot_ms;
      if(previous!==undefined&&(v-previous+2**32)%2**32>=2**31)throw Error('AP_BOOT_CLOCK_REGRESSION');
      this.#boot.set(f.id,v);
    }
    this.#seq=f.seq;this.#counts.accepted++;
    if(this.#counts.accepted+this.#counts.foreign+this.#counts.duplicate+this.#counts.reordered>256)throw Error('SESSION_FRAME_BOUND');
    return 'ACCEPTED';
  }
  async receive(chunk,meta,nowMs){
    if(this.#busy){this.invalidate('CONCURRENT_RECEIVE');throw Error('CONCURRENT_RECEIVE');}
    if(!this.tick(nowMs))throw Error('ADAPTER_INVALID:'+this.#reason);
    this.#busy=true;const generation=this.#generation,out=[];
    try{
      this.#context(meta,nowMs);
      const frames=this.#framer.push(chunk,meta.receivedAtMs,nowMs);this.#lastAt=meta.receivedAtMs;
      for(const f of frames){
        const admission=this.#admit(f);
        await this.#record('FRAME_'+admission,{id:f.id,seq:f.seq,rawHex:f.rawHex,
          firstByteAtMs:f.firstByteAtMs,lastByteAtMs:f.lastByteAtMs},nowMs);
        if(admission!=='ACCEPTED'){
          // Quarantine never grants freshness. Conflicting same-target identity/config
          // still makes an existing witness uncertain, even under a repeated sequence.
          if(admission!=='FOREIGN_SENDER'&&this.#binding){
            if(f.id===148&&!same(f.fields,this.#binding.announcement.fields))throw Error('QUARANTINED_FIRMWARE_CONFLICT');
            if(f.id===22&&Object.hasOwn(this.#reader.values,f.fields.param_id)){
              const p=parameterFrame(unhex(f.rawHex)),old=this.#reader.values[p.fields.param_id];
              const value=decodeParameter(p.valueBytes,p.fields.param_type,this.#binding.encoding);
              if(value!==old.value||p.fields.param_type!==old.type||p.fields.param_count!==this.#reader.count)throw Error('QUARANTINED_PARAMETER_CONFLICT');
            }
          }
          continue;
        }
        const framedMeta={...structuredClone(meta),receivedAtMs:f.firstByteAtMs};
        if(f.id===148){
          if(this.#binding){
            if(!same(f.fields,this.#binding.announcement.fields))throw Error('FIRMWARE_ANNOUNCEMENT_CHANGED');
            // Identical announcement neither refreshes binding nor restarts readback.
          }else{
            const b=bind(this.#contract,unhex(f.rawHex),framedMeta,nowMs);
            if(b.status!=='MATCHED_MOCK')throw Error('FIRMWARE_CONTRACT:'+b.reason);
            this.#binding=b;
            this.#reader=new ParameterReadback(b,{idFactory:this.#idFactory,
              persist:rows=>this.#persist({stream:'PARAMETERS38',rows:structuredClone(rows)})});
            this.#phase='READING';const packet=await this.#reader.begin(nowMs);if(packet)out.push(packet);
          }
        }else{
          this.#telemetry.receive(unhex(f.rawHex),framedMeta,nowMs);
          if(this.#reader)out.push(...await this.#reader.receive(unhex(f.rawHex),framedMeta,nowMs));
          if(this.#reader?.phase==='UNKNOWN')throw Error('PARAMETER_READBACK:'+this.#reader.reason);
          if(this.#reader?.phase==='MATCHED_MOCK')this.#phase='MOCK_READBACK_READY';
        }
      }
      if(generation!==this.#generation||!this.tick(nowMs))throw Error('REVOKED_BEFORE_PUBLICATION');
      if(out.some(p=>p.id!==20||p.channel!=='MOCK_BUFFER_ONLY'||p.networkSent!==false))throw Error('OUTBOUND_SCOPE');
      return out.map(p=>structuredClone(p));
    }catch(e){this.invalidate(e.message);throw e;}finally{this.#busy=false;}
  }
  snapshot(t){this.tick(t);return {format:'aeris-flightadapter39-snapshot',version:1,
    origin:'MOCK_REPLAY',target:structuredClone(this.#contract.target),epoch:this.#contract.epoch,
    phase:this.#phase,reason:this.#reason,atMs:t,counts:{...this.#counts},framer:this.#framer.snapshot(),
    parameterPhase:this.#reader?.phase??null,inspectionAvailable:this.current(t),
    restoreAuthorityAllowed:false,...DENIED};}
  proof(t){
    if(!this.current(t))throw Error('CURRENT_READONLY_INSPECTION_REQUIRED');
    const p={format:'aeris-flightadapter39-inspection',version:1,origin:'MOCK_REPLAY',
      target:structuredClone(this.#contract.target),epoch:this.#contract.epoch,atMs:t,
      readonly:true,typedReadback:structuredClone(this.#reader.proof(t)),restoreAuthorityAllowed:false,...DENIED};
    ISSUED.set(p,{owner:this,canonical:canonical(p)});return p;
  }
  async inspect(profile,t,{supplement=null,apState=null,altitude=null}={}){
    if(this.#busy){this.invalidate('INSPECTION_DURING_WRITE');throw Error('INSPECTION_DURING_WRITE');}
    if(!this.tick(t))return {status:'UNKNOWN',reason:this.#reason,...DENIED};
    const generation=this.#generation;this.#busy=true;
    try{
      profile=structuredClone(profile);supplement=structuredClone(supplement);
      apState=structuredClone(apState);altitude=structuredClone(altitude);
      bounded({profile,supplement,apState,altitude},262144);
      validateProfile(profile);if(!same(profile.target,this.#contract.target))throw Error('PREFLIGHT_TARGET');
      const preflight=this.#binding?.contract.profile==='PINNED_COPTER471'
        ?await this.#telemetry.assess(profile,t,supplement)
        :{assessment:{state:'UNKNOWN',reason:'fresh pinned-Copter mapping unavailable'},
          wireOnlyComplete:false,raw:null,...DENIED};
      if(generation!==this.#generation||!this.tick(t))throw Error('INSPECTION_REVOKED');
      let typed=null;try{typed=this.#reader?.proof(t);}catch{}
      const policy=typed?mapPolicy(typed,t):{status:'UNKNOWN',reason:'full typed readback unavailable',operationalAllowed:false};
      const failsafe=typed&&apState?evaluateFailsafe(typed,apState,t):{status:'UNKNOWN',reason:'explicit AP-side mock state required',...DENIED};
      const height=typed&&altitude?assessAltitude(typed,altitude,t):{state:'UNKNOWN',reason:'explicit reviewed altitude references required',...DENIED};
      return {format:'aeris-flightadapter39-review',version:1,status:typed?'READONLY_MOCK_INSPECTION':'PARTIAL_UNKNOWN',
        target:structuredClone(this.#contract.target),epoch:this.#contract.epoch,atMs:t,preflight,
        policy,failsafe,altitude:height,normalizedPolicyEquivalent:false,remainingWhProven:false,
        geofenceUploadReadbackProven:false,autopilotEnforcementProven:false,realFirmwareProven:false,...DENIED};
    }catch(e){this.invalidate(e.message);throw e;}finally{this.#busy=false;}
  }
  audit(){return {session:structuredClone(this.#audit.rows),parameters:structuredClone(this.#reader?.ledger.rows??[])};}
}
