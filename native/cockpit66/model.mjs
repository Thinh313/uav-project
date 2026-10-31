import {CustomerMockSession,SYNTHETIC_PROFILES,CONFIG65} from './portable/cyber65/session.mjs';
import {sha,canonical,clone,exact} from './portable/cyber65/contracts.mjs';
import {Frames} from './portable/transport25/fixtures.mjs';
export const MODEL_VERSION=1;
export const PAYLOADS=Object.freeze([{id:'front',name:'Phase One',detail:'Camera + gimbal',scope:'camera:front'},{id:'center',name:'Thermal',detail:'Proxy camera',scope:'camera:center'},{id:'rear',name:'Corona',detail:'Camera cố định',scope:'camera:rear'},{id:'lidar',name:'LiDAR',detail:'Chưa có adapter',scope:null}]);
const actorOK=a=>['pilot-a','payload-b'].includes(a),payloadOK=p=>PAYLOADS.some(x=>x.id===p);
const shapes={open:['type'],view:['type','actor'],select:['type','payload'],claim:['type','actor','payload'],release:['type','actor','payload'],claimAircraft:['type','actor'],transfer:['type','actor','payload','to'],accept:['type','actor'],decline:['type','actor'],command:['type','actor','payload','operation','value','reply'],fault:['type','fault'],suspend:['type','reason']};
export function validateAction(a){exact(a,shapes[a?.type]??[]);if(!shapes[a.type]||canonical(a).length>2048)throw Error('ACTION_SCHEMA');if('actor'in a&&!actorOK(a.actor)||'to'in a&&!actorOK(a.to)||'payload'in a&&!payloadOK(a.payload))throw Error('ACTION_IDENTITY');if(a.type==='command'&&(!['capture','zoomPercent','focusPercent','gimbalAngle'].includes(a.operation)||!['normal','ack-only','wrong-target'].includes(a.reply)))throw Error('COMMAND_SCHEMA');if(a.type==='fault'&&!['payload-loss','pilot-loss','link-loss','expire'].includes(a.fault))throw Error('FAULT_SCHEMA');if(a.type==='suspend'&&!['focus','pause','hidden','pagehide','storage','manual'].includes(a.reason))throw Error('LIFECYCLE_SCHEMA');return clone(a);}
export class Cockpit {
 constructor({corpusSha256}){if(!/^[a-f0-9]{64}$/.test(corpusSha256))throw Error('CORPUS_SHA');this.corpusSha256=corpusSha256;this.clock=0;this.actor='payload-b';this.selected='front';this.run=0;this.bundle=null;this.tape=[];this.busy=false;this.incomplete=false;this.suspended=false;this.lifecycleEpoch=0;this.last={status:'IDLE',message:'Chưa mở phiên mock'};this.#newCore();}
 #newCore(){this.core=new CustomerMockSession({now:()=>this.clock,profiles:SYNTHETIC_PROFILES,corpusSha256:this.corpusSha256});this.actors={'pilot-a':this.core.credential('pilot-a'),'payload-b':this.core.credential('payload-b')};this.alive={'pilot-a':true,'payload-b':true};this.frames=new Frames();this.images={front:10,center:10,rear:10};}
 scopes(payload){const b=CONFIG65.bindings.find(x=>x.id===payload);if(!b)throw Error('PAYLOAD_UNSUPPORTED');return ['camera:'+payload,...b.gimbalKey?['gimbal:'+payload]:[]];}
 #pump(){if(this.core.snapshot().authority.phase==='CONNECTED')for(const a of ['pilot-a','payload-b'])if(this.alive[a])this.core.authority.heartbeat(this.actors[a],this.core.context());}
 async #perform(a){
  if(a.type==='open'){this.#newCore();await this.core.connect();for(const b of this.frames.bootFrames())this.core.deliver(b);this.core.deliver(this.frames.cam(1,2,2,450,1000));if(this.selected!=='front'&&this.selected!=='lidar')this.core.select(this.selected);this.run++;this.bundle=null;this.suspended=false;this.#pump();return;}
  if(a.type==='view'){this.actor=a.actor;return;}
  if(a.type==='select'){this.selected=a.payload;if(a.payload!=='lidar'&&this.core.snapshot().transport.configuration)this.core.select(a.payload);return;}
  if(a.type==='suspend'){this.suspended=true;this.bundle=null;this.core.disconnect();return;}
  if(this.suspended)throw Error('EXPLICIT_NEW_SESSION_REQUIRED');
  if('actor'in a&&a.actor!==this.actor)throw Error('VIEW_ACTOR_MISMATCH');
  this.#pump();const c=this.core.context(),auth=this.core.authority,credential=this.actors[a.actor];
  if(a.type==='claimAircraft'){auth.claim(credential,'aircraft',c,'ACCEPT_EXCLUSIVE_MOCK_SCOPE');return;}
  if(a.type==='claim'){
   const scopes=this.scopes(a.payload),s=auth.snapshot();if(scopes.some(scope=>s.grants.some(g=>g.scope===scope)||s.pending.some(g=>g.scope===scope)))throw Error('PAYLOAD_ALREADY_OWNED');
   try{for(const scope of scopes)auth.claim(credential,scope,c,'ACCEPT_EXCLUSIVE_MOCK_SCOPE');}catch(e){for(const scope of scopes)auth.invalidateScope(scope,'BUNDLE_CLAIM_FAILED');throw e;}return;
  }
  if(a.type==='release'){for(const scope of this.scopes(a.payload)){const g=auth.snapshot().grants.find(g=>g.scope===scope);if(g&&g.owner!==a.actor)throw Error('CURRENT_OWNER_REQUIRED');}for(const scope of this.scopes(a.payload))if(auth.snapshot().grants.some(g=>g.scope===scope))auth.release(credential,scope,c);if(this.bundle?.payload===a.payload)this.bundle=null;return;}
  if(a.type==='transfer'){
   if(this.bundle)throw Error('TRANSFER_ALREADY_PENDING');const scopes=this.scopes(a.payload),s=auth.snapshot();if(scopes.some(scope=>s.grants.find(g=>g.scope===scope)?.owner!==a.actor)||a.to===a.actor)throw Error('ALL_SCOPES_CURRENT_OWNER_REQUIRED');
   try{const transfers=scopes.map(scope=>auth.transfer(credential,scope,a.to,c));this.bundle={payload:a.payload,from:a.actor,to:a.to,transfers};}catch(e){for(const scope of scopes)auth.invalidateScope(scope,'PARTIAL_TRANSFER_REVOKED');this.bundle=null;throw e;}return;
  }
  if(a.type==='accept'||a.type==='decline'){
   const b=this.bundle;if(!b||b.to!==a.actor)throw Error('RECIPIENT_CONFIRMATION_REQUIRED');const s=auth.snapshot();
   try{if(b.transfers.some(t=>!s.pending.some(p=>p.id===t.id&&p.scope===t.scope&&p.to===a.actor)))throw Error('TRANSFER_EXPIRED_OR_CHANGED');for(const t of b.transfers)auth[a.type](credential,t.id,c);}catch(e){for(const t of b.transfers)auth.invalidateScope(t.scope,'BUNDLE_CONSENT_FAILED');throw e;}finally{this.bundle=null;}return;
  }
  if(a.type==='fault'){
   if(a.fault==='link-loss')this.core.loseLink();else if(a.fault==='expire'){this.clock+=1601;this.core.snapshot();}else{const who=a.fault==='pilot-loss'?'pilot-a':'payload-b';auth.lose(this.actors[who],c);this.alive[who]=false;}this.bundle=null;return;
  }
  if(a.type==='command'){
   const b=CONFIG65.bindings.find(b=>b.id===a.payload);if(!b)throw Error('PAYLOAD_UNSUPPORTED');
   if(a.operation==='capture'){const p=this.core.snapshot().transport.protocol?.cameras.find(p=>p.key===b.cameraKey);if(p?.valid&&!p.lastImage){const [system,component,device]=b.cameraKey.split('/').map(Number);this.core.deliver(this.frames.image(component,device,this.images[a.payload],String(9007199254740993n+BigInt(this.clock)*1000n),1000+this.clock));}} // explicit synthetic peer baseline; no exposure/file is proven
   this.core.request(credential,{bindingId:a.payload,operation:a.operation,value:a.value,context:c});this.clock+=10;
   const cam=b.cameraKey.split('/').map(Number),g=b.gimbalKey?.split('/').map(Number),cmd={capture:2000,zoomPercent:531,focusPercent:532,gimbalAngle:1000}[a.operation],component=a.operation==='gimbalAngle'?g[1]:cam[1],device=a.operation==='gimbalAngle'?0:cam[2];
   this.core.deliver(this.frames.ack(cmd,a.reply==='wrong-target'?(component===100?101:100):component,device));
   if(a.reply!=='normal')return;
   const boot=1000+this.clock;if(a.operation==='capture')this.core.deliver(this.frames.image(cam[1],cam[2],++this.images[a.payload],String(9007199254740993n+BigInt(this.clock)*1000n),boot));
   else if(a.operation==='gimbalAngle')this.core.deliver(this.frames.attitude(g[2],a.value.pitchDeg,a.value.yawDeg,boot));
   else this.core.deliver(this.frames.settings(cam[1],cam[2],a.operation==='zoomPercent'?a.value:40,a.operation==='focusPercent'?a.value:50,boot));return;
  }
  throw Error('ACTION_NOT_IMPLEMENTED');
 }
 async dispatch(input){const a=validateAction(input);if(this.busy)throw Error('UI_ACTION_PENDING');if(this.tape.length>=96){this.pauseNow('manual');throw Error('TAPE_QUOTA_NO_EVICTION');}this.busy=true;const epoch=this.lifecycleEpoch;this.clock+=20;let error=null;
  try{await this.#perform(a);}catch(e){error=e.message;}
  if(epoch!==this.lifecycleEpoch){this.incomplete=true;this.suspended=true;try{this.core.disconnect();}catch{}error='LIFECYCLE_CHANGED_DURING_ACTION';}
  this.last={status:error?'REFUSED':'OK_MOCK',type:a.type,message:error??'Đã xử lý trong mock'};this.busy=false;
  this.tape.push({action:a,expectedError:error,afterSha256:sha(this.checkpoint())});return {ok:error===null,error};
 }
 pauseNow(reason='focus'){this.lifecycleEpoch++;this.suspended=true;this.bundle=null;if(!this.busy)this.clock+=20;try{this.core.disconnect();}catch{}if(this.busy){this.incomplete=true;this.last={status:'UNCERTAIN',message:'Lifecycle interruption; snapshot incomplete'};return;}if(this.tape.length<96){this.last={status:'OK_MOCK',type:'suspend',message:'Đã xử lý trong mock'};this.tape.push({action:{type:'suspend',reason},expectedError:null,afterSha256:sha(this.checkpoint())});}else this.incomplete=true;}
 checkpoint(){return {format:'aeris-cockpit66-checkpoint',version:MODEL_VERSION,clockMode:'EXPLICIT_STEP_MOCK_NOT_REAL_TIME',clockMs:this.clock,actor:this.actor,selected:this.selected,run:this.run,bundle:clone(this.bundle),suspended:this.suspended,incomplete:this.incomplete,last:clone(this.last),core:this.core.review(),actualImages:0};}
 summary(){const s=this.checkpoint(),r=s.core.body;return {...s,grants:r.authority.grants,pending:r.authority.pending,phase:r.authority.phase,historyComplete:!this.incomplete&&r.historyComplete,transactions:r.transactions,scopes:this.selected==='lidar'?[]:this.scopes(this.selected)};}
}
export async function replayTape(corpusSha256,tape){if(!Array.isArray(tape)||tape.length>96)throw Error('TAPE_BOUND');const m=new Cockpit({corpusSha256});for(const item of tape){exact(item,['action','expectedError','afterSha256']);const result=await m.dispatch(item.action);if(result.error!==item.expectedError||sha(m.checkpoint())!==item.afterSha256)throw Error('SEMANTIC_TAPE_MISMATCH');}return m.checkpoint();}
export function makeCapsule(m){const body={format:'aeris-cockpit66-workspace',version:MODEL_VERSION,origin:'SYNTHETIC_MOCK_ONLY',corpusSha256:m.corpusSha256,tape:clone(m.tape),checkpoint:m.checkpoint(),authorityRestorable:false,operational:false,actualImages:0};if(canonical(body).length>524288)throw Error('WORKSPACE_BYTE_QUOTA_NO_EVICTION');return {body,sha256:sha(body)};}
export async function inspectCapsule(raw,corpusSha256){if(typeof raw!=='string'||new TextEncoder().encode(raw).length>524288)throw Error('WORKSPACE_BOUND');const x=JSON.parse(raw);exact(x,['body','sha256']);const b=x.body;exact(b,['format','version','origin','corpusSha256','tape','checkpoint','authorityRestorable','operational','actualImages']);if(b.format!=='aeris-cockpit66-workspace'||b.version!==MODEL_VERSION||b.origin!=='SYNTHETIC_MOCK_ONLY'||b.corpusSha256!==corpusSha256||b.authorityRestorable!==false||b.operational!==false||b.actualImages!==0||sha(b)!==x.sha256)throw Error('WORKSPACE_SCOPE_OR_SHA');if(b.checkpoint.incomplete)throw Error('INCOMPLETE_WORKSPACE_INSPECTION_REQUIRED');const reproduced=await replayTape(corpusSha256,b.tape);if(sha(reproduced)!==sha(b.checkpoint))throw Error('WORKSPACE_REHASHED_STATE');return {capsule:x,prefs:{actor:b.checkpoint.actor,selected:b.checkpoint.selected},historical:clone(b.checkpoint),authorityRestored:false};}
