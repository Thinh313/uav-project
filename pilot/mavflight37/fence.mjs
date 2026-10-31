import {validateFence,fenceItems} from '../apflight36/fence.mjs';
import {canonical,digest,int,same} from '../apflight36/types.mjs';
import {Ledger} from '../apflight36/ledger.mjs';
import {ReplayLink,MockBuffer} from './session.mjs';
const ITEM_KEYS=['seq','frame','command','current','autocontinue','param1','param2','param3','param4','x','y','z','mission_type'];
const ISSUED_PROOFS=new WeakMap();
export function liveIssuedProof(proof,t){const issued=ISSUED_PROOFS.get(proof);return!!issued&&issued.owner.tick(t)&&issued.owner.phase==='WIRE_READBACK_MATCHED'&&canonical(proof)===issued.canonical}
export async function compileFence(plan){
 plan=structuredClone(plan);validateFence(plan);const abstract=fenceItems(plan);if(abstract.length>64)throw Error('wire subset <=64 items');
 const quantized=structuredClone(plan);let maximumCoordinateErrorM=0,maximumRadiusErrorM=0;
 const coordinate=p=>{const q=p.map(x=>Math.round(x*1e7)/1e7),dy=(q[1]-p[1])*Math.PI/180*6371008.8,dx=(q[0]-p[0])*Math.PI/180*6371008.8*Math.cos(p[1]*Math.PI/180);maximumCoordinateErrorM=Math.max(maximumCoordinateErrorM,Math.hypot(dx,dy));return q};
 for(const r of quantized.regions){if(r.shape==='CIRCLE'){r.center=coordinate(r.center);const q=Math.fround(r.radiusM);maximumRadiusErrorM=Math.max(maximumRadiusErrorM,Math.abs(q-r.radiusM));r.radiusM=q}else r.geometry.coordinates[0]=r.geometry.coordinates[0].map(coordinate)}
 validateFence(quantized);if(maximumCoordinateErrorM>.02||maximumRadiusErrorM>.001)throw Error('quantization budget');
 const items=fenceItems(quantized).map((i,seq)=>{const point=i.kind==='CIRCLE'?i.center:i.point;return{seq,frame:0,command:i.kind==='CIRCLE'?(i.inclusion?5003:5004):(i.inclusion?5001:5002),current:0,autocontinue:0,param1:i.kind==='CIRCLE'?i.radiusM:i.vertices,param2:0,param3:0,param4:0,x:Math.round(point[1]*1e7),y:Math.round(point[0]*1e7),z:0,mission_type:1}});
 return{sourcePlan:plan,sourcePlanSha256:await digest(plan),quantizedPlan:quantized,quantizedPlanSha256:await digest(quantized),items,wireItemsSha256:await digest(items),maximumCoordinateErrorM,maximumRadiusErrorM,altitudeAndActionEncoded:false,configurationScope:'SEPARATE_READONLY_RAW_PARAMETERS'};
}
function parameterMap(values){if(!values||typeof values!=='object'||Array.isArray(values)||Object.keys(values).length<1||Object.keys(values).length>16)throw Error('1..16 readonly parameter expectations');for(const[k,v]of Object.entries(values))if(!/^[A-Z][A-Z0-9_]{0,15}$/.test(k)||typeof v!=='number'||!Number.isFinite(v)||!Number.isFinite(Math.fround(v)))throw Error('parameter expectation');return structuredClone(values)}
/** One transaction/instance. UUIDs are confined to the mock journal, never serialized. */
export class FenceAdapter{
 constructor(target,epoch,{expectedParameters,gcs,persist,idFactory}={}){this.link=new ReplayLink(target,epoch);this.output=new MockBuffer(target,gcs);this.parameters=parameterMap(expectedParameters);this.ledger=new Ledger(persist,idFactory);this.phase='EMPTY';this.compiled=null;this.sent=new Set();this.duplicates=new Map();this.read=new Map();this.rawParameters={};this.pending=null;this.deadline=null;this.ackOpaque=null;this.proofValue=null;this.used=false;this.busy=false;this.received=[]}
 invalidate(reason){this.phase='UNKNOWN';this.reason=reason;this.proofValue=null;this.pending=null;this.link.close(reason);this.ledger.revoke()}
 async record(kind,data,t,effect=()=>{}){try{return await this.ledger.append(kind,data,t,effect)}catch(e){this.invalidate('WRITER_UNCERTAIN');throw e}}
 fields(extra={}){return{target_system:this.link.target.system,target_component:this.link.target.component,mission_type:1,...extra}}
 async begin(plan,t){int(t,0,1e12,'begin time');if(this.used||this.busy||this.link.closed)throw Error('one transaction per fresh replay link');this.busy=true;
  try{const compiled=await compileFence(plan);const packet=await this.record('WIRE_UPLOAD_INTENT_MOCK',{compiled},t,()=>{this.used=true;this.compiled=compiled;this.phase='UPLOAD';this.deadline=t+5000;return this.output.packet(44,this.fields({count:compiled.items.length}))});return packet}finally{this.busy=false}
 }
 recipient(f){return f.version===2&&f.fields.mission_type===1&&f.fields.target_system===this.output.gcs.system&&f.fields.target_component===this.output.gcs.component}
 async receive(bytes,meta,t){if(this.busy){this.invalidate('CONCURRENT_RECEIVE');throw Error('concurrent receive')}this.busy=true;const out=[];
  try{if(this.phase==='UNKNOWN')throw Error('invalidated');if(this.deadline!==null&&t>this.deadline){this.invalidate('TRANSACTION_TIMEOUT');throw Error(this.reason)}
   for(const f of this.link.receive(bytes,meta,t)){const p=f.fields;if(![22,44,47,51,73].includes(f.id))continue;
    if(f.id!==22&&!this.recipient(f))continue;
    if(f.id===51&&this.phase==='UPLOAD'){
     int(p.seq,0,this.compiled.items.length-1,'request seq');const duplicate=this.sent.has(p.seq);
     if(!duplicate&&p.seq!==this.sent.size)continue;
     if(duplicate){if(p.seq!==this.sent.size-1)continue;const n=(this.duplicates.get(p.seq)??0)+1;if(n>2){this.invalidate('DUPLICATE_REQUEST_BUDGET');throw Error(this.reason)}this.duplicates.set(p.seq,n)}
     out.push(await this.record('ITEM_REQUEST_AND_MOCK_BUFFER',{rawHex:f.rawHex,seq:p.seq,duplicate},t,()=>{this.sent.add(p.seq);return this.output.packet(73,this.fields(this.compiled.items[p.seq]))}));
    }else if(f.id===47&&this.phase==='UPLOAD'){
     if(this.sent.size!==this.compiled.items.length)continue;if(p.type!==0){this.invalidate('UPLOAD_NACK_'+p.type);continue}
     out.push(await this.record('ACK_ONLY_BEGIN_READBACK',{rawHex:f.rawHex,opaqueId:p.opaque_id},t,()=>{this.ackOpaque=p.opaque_id||null;this.phase='READ_COUNT';return this.output.packet(43,this.fields())}));
    }else if(f.id===44&&this.phase==='READ_COUNT'){
     if(p.count!==this.compiled.items.length||this.ackOpaque&&p.opaque_id&&this.ackOpaque!==p.opaque_id){this.invalidate('COUNT_OR_OPAQUE_MISMATCH');continue}
     out.push(await this.record('READBACK_COUNT',{rawHex:f.rawHex,count:p.count,opaqueId:p.opaque_id},t,()=>{this.phase='READ_ITEMS';return this.output.packet(51,this.fields({seq:0}))}));
    }else if(f.id===73&&this.phase==='READ_ITEMS'){
     if(p.seq!==this.read.size||p.seq>=this.compiled.items.length)continue;
     const meaningful=Object.fromEntries(ITEM_KEYS.map(k=>[k,p[k]]));if(!same(meaningful,this.compiled.items[p.seq])){this.invalidate('WIRE_ITEM_MISMATCH');continue}
     const packets=await this.record('READBACK_ITEM_MATCHED',{rawHex:f.rawHex,seq:p.seq},t,()=>{this.read.set(p.seq,meaningful);if(this.read.size<this.compiled.items.length)return[this.output.packet(51,this.fields({seq:this.read.size}))];this.phase='READ_PARAMETERS';return[this.output.packet(47,this.fields({type:0})),this.requestNextParameter(t)]});out.push(...packets);
    }else if(f.id===22&&this.phase==='READ_PARAMETERS'){
     if(!this.pending||p.param_id!==this.pending.name||f.invalidText.length)continue;
     if(p.param_type!==9||!Number.isFinite(p.param_value)||Math.fround(this.parameters[p.param_id])!==p.param_value||p.param_count<1||p.param_index>=p.param_count){this.invalidate('READONLY_PARAMETER_MISMATCH');continue}
     const packet=await this.record('READONLY_PARAMETER_MATCHED',{rawHex:f.rawHex,name:p.param_id,value:p.param_value,type:p.param_type},t,()=>{this.rawParameters[p.param_id]=p.param_value;this.pending=null;return this.requestNextParameter(t)});if(packet)out.push(packet);
     if(!this.pending){await this.record('WIRE_AND_RAW_CONFIG_MATCHED',{sourcePlanSha256:this.compiled.sourcePlanSha256,wireItemsSha256:this.compiled.wireItemsSha256},t,()=>{this.phase='WIRE_READBACK_MATCHED';this.deadline=null;this.proofValue={format:'aeris-fence-wire-proof37',version:1,origin:'MOCK_MAVLINK_REPLAY',target:structuredClone(this.link.target),epoch:this.link.epoch,atMs:t,compiled:structuredClone(this.compiled),rawParameters:structuredClone(this.rawParameters),normalizedConfigProven:false,altitudeDatumProven:false,executionProven:false,autopilotEnforcementProven:false,operationalAllowed:false,authenticated:false}})}
    }
   }if(this.link.closed)this.invalidate(this.link.reason);return out;
  }catch(e){if(this.link.closed||this.ledger.blocked)this.invalidate(this.link.reason??e.message);throw e}finally{this.busy=false}
 }
 requestNextParameter(t){const name=Object.keys(this.parameters).find(k=>!Object.hasOwn(this.rawParameters,k));if(!name)return null;this.pending={name,atMs:t};return this.output.packet(20,{target_system:this.link.target.system,target_component:this.link.target.component,param_id:name,param_index:-1})}
 tick(t){if(this.phase==='UNKNOWN')return false;if(this.deadline!==null&&t>this.deadline||!this.link.tick(t)){this.invalidate('TIMEOUT_OR_STALE');return false}return true}
 proof(t){if(!this.tick(t)||this.phase!=='WIRE_READBACK_MATCHED')throw Error('wire proof unavailable');const result=structuredClone(this.proofValue);ISSUED_PROOFS.set(result,{owner:this,canonical:canonical(result)});return result}
 snapshot(t){this.tick(t);return{phase:this.phase,reason:this.reason??null,readCount:this.read.size,uploadItems:this.sent.size,rawParameters:structuredClone(this.rawParameters),proofAvailable:this.phase==='WIRE_READBACK_MATCHED',operationalAllowed:false,executionProven:false,networkSent:false}}
 disconnect(){this.invalidate('DISCONNECTED_NEW_CONTEXT_REQUIRED')}
}
