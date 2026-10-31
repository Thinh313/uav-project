import {TransportBroker} from '../transport25/broker.mjs';
import {MockTransport} from '../transport25/mock.mjs';
import {CONFIG} from '../transport25/fixtures.mjs';
import {Authority,MockIdentity} from './authority.mjs';
import {clone,canonical,sha,exact,phaseOneUnknown,mockCamera,validateDescriptor,validateOperation,SCOPE_NOTE,tagUnavailable,deepFreeze} from './contracts.mjs';
export const CONFIG65=deepFreeze({...clone(CONFIG),bindings:CONFIG.bindings.map(b=>({...b,label:{front:'Phase One integration seam · mock',center:'Thermal proxy · mock',rear:'Corona fixed camera · mock'}[b.id]}))});
export const SYNTHETIC_PROFILES=deepFreeze({front:mockCamera(),center:mockCamera('THERMAL_SEAM_FIXTURE'),rear:{...mockCamera('CORONA_SEAM_FIXTURE'),controls:['capture','zoomPercent','focusPercent']}});
const terminal=new Set(['OBSERVATION_CONSISTENT_UNATTRIBUTED','REJECTED','TIMED_OUT_UNCERTAIN','INVALIDATED']);
const ackStage=a=>!a?'UNKNOWN':a.result===0?'ACCEPTED':a.result===5?'IN_PROGRESS':'REJECTED';
export class CustomerMockSession {
 #port=new MockTransport();#broker;#auth;#identity=new MockIdentity();#profiles;#records=[];#declarations=[];#bindingState=new Map();#now;#corpusHash;#incomplete=false;
 constructor({now,profiles={front:phaseOneUnknown()},corpusSha256='0'.repeat(64)}={}){
  if(typeof now!=='function'||!/^[a-f0-9]{64}$/.test(corpusSha256))throw Error('MOCK_CLOCK_AND_CORPUS_DIGEST_REQUIRED');
  this.#profiles=clone(profiles);for(const [key,d]of Object.entries(this.#profiles)){if(!CONFIG65.bindings.some(b=>b.id===key))throw Error('PROFILE_BINDING_UNKNOWN');validateDescriptor(d);}
  this.#now=now;this.#corpusHash=corpusSha256;this.#broker=new TransportBroker({transport:this.#port,sessionId:'cyber65-mock',now});
  this.#auth=new Authority({identity:this.#identity,now,scopes:['aircraft',...CONFIG65.bindings.flatMap(b=>['camera:'+b.id,...b.gimbalKey?['gimbal:'+b.id]:[]])]});
 }
 get authority(){return this.#auth;}credential(subject){return this.#identity.issue(subject);}
 context(){return this.#auth.context();}
 async connect(){await this.#broker.connect(CONFIG65);this.#bindingState.clear();return this.#auth.connect(this.#broker.context());}
 #sync(){
  const p=this.#broker.snapshot();let a=this.#auth.snapshot();
  if(p.phase!=='CONNECTED'&&a.phase==='CONNECTED'){try{this.#auth.disconnect('TRANSPORT_'+p.phase);}catch{}a=this.#auth.snapshot();}
  for(const b of CONFIG65.bindings){
   const camera=p.protocol?.cameras.find(x=>x.key===b.cameraKey),gimbal=p.protocol?.gimbals.find(x=>x.key===b.gimbalKey);
   const s=canonical({camera:camera?{valid:camera.valid,generation:camera.generation}:null,gimbal:gimbal?{valid:gimbal.valid,generation:gimbal.generation}:null});
   if(this.#bindingState.has(b.id)&&this.#bindingState.get(b.id)!==s){this.#auth.invalidateScope('camera:'+b.id,'DISCOVERY_GENERATION_CHANGED');if(b.gimbalKey)this.#auth.invalidateScope('gimbal:'+b.id,'DISCOVERY_GENERATION_CHANGED');}
   this.#bindingState.set(b.id,s);
  }
  for(const r of this.#records){
   const t=p.transactions.find(t=>t.id===r.transportId);if(!t)continue;
   if(!r.finalized&&!this.#auth.valid(r.authorityTicket))r.override='AUTHORITY_REVOKED_UNCERTAIN_NO_RETRY';
   r.protocolState=t.state;r.protocol=clone(t);
   if(terminal.has(t.state)||r.override)r.finalized=true;
  }
  return p;
 }
 deliver(bytes,options){try{this.#port.deliver(bytes,options);}catch(e){this.#incomplete=true;try{this.#auth.disconnect('MOCK_RECEIVE_FAILURE_NO_RESUME');}catch{}this.#sync();throw e;}this.#sync();}
 loseLink(linkId='mock-a'){this.#port.down(linkId);this.#sync();}
 failNext(mode){this.#port.failNext(mode);}
 select(bindingId){this.#broker.select(bindingId);}
 disconnect(){this.#broker.disconnect();this.#auth.disconnect();this.#sync();}
 request(credential,input){
  exact(input,['bindingId','operation','value','context']);this.#sync();
  const b=CONFIG65.bindings.find(x=>x.id===input.bindingId);if(!b)throw Error('EXPLICIT_BINDING_REQUIRED');
  const d=this.#profiles[b.id];if(!d)throw Error('UNKNOWN_PAYLOAD_PROFILE');
  const op=validateOperation(d,input.operation,input.value),scope=(op.operation==='gimbal'?'gimbal:':'camera:')+b.id;
  const ticket=this.#auth.ticket(credential,scope,input.context);
  if(this.#records.length>=128)throw Error('REVIEW_TRANSACTION_BOUND');
  const context=this.#broker.context();
  const t=this.#broker.request({bindingId:b.id,operation:op.operation,value:op.value,context});
  const r={id:'intent-'+(this.#records.length+1),bindingId:b.id,semanticOperation:input.operation,unit:op.unit,profileSha256:sha(d),authorityTicket:ticket,transportId:t.id,protocolState:t.override||t.protocol.state,protocol:clone(t),override:null,finalized:false};this.#records.push(r);return clone(r);
 }
 declareSyntheticFile(input){
  exact(input,['intentId','sha256','bytes','origin']);const r=this.#records.find(x=>x.id===input.intentId);
  if(!r||r.semanticOperation!=='capture'||input.origin!=='SYNTHETIC_DECLARATION_NO_PHYSICAL_FILE'||!/^[a-f0-9]{64}$/.test(input.sha256)||!Number.isSafeInteger(input.bytes)||input.bytes<0||input.bytes>16*1024**2||this.#declarations.length>=64)throw Error('BOUNDED_SYNTHETIC_FILE_DECLARATION_REQUIRED');
  if(this.#declarations.some(x=>x.intentId===input.intentId))throw Error('DUPLICATE_DECLARATION');
  this.#declarations.push({...clone(input),bindingId:r.bindingId,physicalFileVerified:false,exposureProven:false});
 }
 snapshot(){const transport=this.#sync(),authority=this.#auth.snapshot();return tagUnavailable({format:'aeris-cyber65-review',version:1,origin:'SYNTHETIC_LOCAL_MOCK_REPLAY',scope:SCOPE_NOTE,corpusSha256:this.#corpusHash,context:this.context(),profiles:clone(this.#profiles),unknownClientProfile:phaseOneUnknown(),lidar:{model:null,api:null,status:'UNMAPPED_NOT_SUPPORTED'},authority,transport,transactions:clone(this.#records).map(r=>({...r,state:r.override||r.protocolState,causalExecutionProven:false,physicalMediaVerified:false,captureStages:{intent:'RECORDED_MOCK',send:r.protocol.sendStatus,ack:ackStage(r.protocol.protocol?.ack),observation:r.protocol.protocol?.observation?'CONSISTENT_UNATTRIBUTED':'NONE',syntheticExposureMetadata:r.protocol.protocol?.observation?.id===263,exposureProven:false,fileDeclaration:this.#declarations.some(d=>d.intentId===r.id)?'SYNTHETIC_DECLARATION_ONLY':'NONE',physicalFileVerified:false,actualImages:0}})),syntheticFileDeclarations:clone(this.#declarations),actualImages:0,hardwareSupport:'NOT_CHECKED',twoPhysicalStations:'NOT_CHECKED',historyComplete:!this.#incomplete&&transport.historyComplete&&authority.historyComplete,automaticRetries:0,flightCommandsEncoded:0});}
 review(){const body=this.snapshot();return {body,sha256:sha(body)};}
}

export function inspectHistoricalReview(text,{expectedCorpusSha256,expectedReplaySha256}){
 if(typeof text!=='string'||Buffer.byteLength(text)>2*1024**2)throw Error('REVIEW_BYTE_BOUND');
 const v=JSON.parse(text);exact(v,['body','sha256']);const b=v.body;
 exact(b,['format','version','origin','scope','corpusSha256','context','profiles','unknownClientProfile','lidar','authority','transport','transactions','syntheticFileDeclarations','actualImages','hardwareSupport','twoPhysicalStations','historyComplete','automaticRetries','flightCommandsEncoded']);
 if(v.sha256!==sha(b)||v.sha256!==expectedReplaySha256||b.corpusSha256!==expectedCorpusSha256)throw Error('TRUSTED_REPLAY_DIGEST_REQUIRED');
 if(b.format!=='aeris-cyber65-review'||b.version!==1||b.origin!=='SYNTHETIC_LOCAL_MOCK_REPLAY'||b.actualImages!==0||b.hardwareSupport!=='NOT_CHECKED'||b.twoPhysicalStations!=='NOT_CHECKED'||b.flightCommandsEncoded!==0||b.automaticRetries!==0||b.historyComplete!==true||b.transactions.some(t=>t.causalExecutionProven!==false||t.physicalMediaVerified!==false||t.captureStages?.exposureProven!==false||t.captureStages?.physicalFileVerified!==false||t.captureStages?.actualImages!==0)||b.syntheticFileDeclarations.some(f=>f.physicalFileVerified!==false||f.exposureProven!==false))throw Error('FALSE_OR_INCOMPLETE_EVIDENCE_SCOPE');
 return {kind:'HISTORICAL_INSPECTION_ONLY',authorityRestored:false,actualImages:0,review:clone(b)};
}
