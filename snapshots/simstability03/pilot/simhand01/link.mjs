import{encodeRC}from'../simtrain53/rc.mjs';
import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
const ROOT=fileURLToPath(new URL('../../',import.meta.url)),P=path.join(ROOT,'pilot/simtrain53/link.mjs');
export function trainingProjection(){let s=fs.readFileSync(P,'utf8');s=s.replaceAll('simtrain53','simhand01').replaceAll('SIMTRAIN53','SIMHAND01');s=s.replace("'aeris-simhand01'","'aeris-simhand01-'+this.run");s=s.replace(/from\s*(['"])(\.[^'"]+)\1/g,(_,q,p)=>'from '+JSON.stringify(new URL(p,pathToFileURL(P)).href));s=s.replaceAll(new URL('./authority.mjs',pathToFileURL(P)).href,new URL('../simtrain53/authority.mjs',import.meta.url).href);s=s.replace('return this.authority.claim(this.sessionId,this.boot,challenge);',"return this.authority.claim(this.sessionId,this.boot,challenge);");s=s.replace("await super.command('hold');this.record('TAKEOFF_PHYSICS_AND_LOITER_OBSERVED'","this.record('TAKEOFF_PHYSICS_AND_GUIDED_OBSERVED'");return s;}
const BaseTrainingLink=(await import('data:text/javascript;base64,'+Buffer.from(trainingProjection()).toString('base64'))).TrainingLink;

export function requestObservedHeartbeatStream(link){if(link.closed||link.vehicle?.system!==42||link.vehicle?.component!==1)throw Error('OBSERVED_HEARTBEAT_TARGET_REQUIRED');const fields=link.target({command:511,param1:0,param2:100000});link.send(76,fields);link.record('HEARTBEAT_STREAM_REQUEST',{...fields,requestedHz:10,scope:'TELEMETRY_REQUEST_NOT_EXECUTION_OR_FRESHNESS_PROOF'},true);}
const MANUAL_NEUTRAL=[1500,1500,1500,1500,65535,65535,65535,65535], MANUAL_RELEASE=[0,0,0,0,65535,65535,65535,65535];
// Only the new adapter owns terminal cleanup. Reference link/physics remain immutable.
export class TrainingLink extends BaseTrainingLink {
 constructor(...args){super(...args);this.manualGeneration=0;this.manualWireOwned=false;this.manualTerminal=null;const revoke=this.authority.revoke.bind(this.authority);this.authority.release=()=>{};this.authority.revoke=reason=>{revoke(reason);if(this.manualWireOwned&&!this.suppressManualRevoke&&!this.manualTerminal)void this.releaseManual(reason).catch(e=>{if(!this.closed)try{this.record('MANUAL_RELEASE_UNCONFIRMED',{reason,error:e.message},true);}catch{}});};}
 cancelManual(reason){++this.manualGeneration;if(this.manualModeTransaction?.pending===this.pending&&this.pending)this.failPending('MANUAL_HANDOFF_CANCELLED:'+reason);}
 async observedManualMode(mode,name,generation){
  this.checkControl();if(this.manualTerminal||generation!==this.manualGeneration)throw Error('MANUAL_HANDOFF_CANCELLED');
  if(mode!==4&&this.samples[0].fields.custom_mode===mode)return;
  const pending=this.beginPending('command',{name,command:176,observe:f=>f.custom_mode===mode,accepted:false,observed:false});const transaction={generation,pending:this.pending};this.manualModeTransaction=transaction;
  const timer=setTimeout(()=>{if(this.manualModeTransaction===transaction&&this.pending===transaction.pending)this.failPending('MANUAL_MODE_DEADLINE5000');},5000);
  try{this.send(76,this.target({command:176,param1:1,param2:mode}));await pending;this.checkControl();if(this.manualTerminal||generation!==this.manualGeneration||this.samples[0].fields.custom_mode!==mode)throw Error('MANUAL_HANDOFF_CANCELLED');}
  finally{clearTimeout(timer);if(this.manualModeTransaction===transaction)this.manualModeTransaction=null;}
 }
 async claim(challenge){
  this.checkControl();if(this.manualTerminal||this.manualClaimTask||this.manualReleaseTask)throw Error('MANUAL_HANDOFF_BUSY');
  const hb=this.samples[0].fields;if(!(hb.base_mode&128)||hb.custom_mode!==4)throw Error('ARMED_GUIDED_HOLD_REQUIRED');
  if(!this.attestedAt||performance.now()-this.attestedAt>1000)throw Error('FRESH_ATTESTATION_REQUIRED');
  if(!this.authority.valid(challenge))throw Error('CHALLENGE_STALE');this.authority.challenges.delete(challenge);
  const generation=++this.manualGeneration,session=this.sessionId,boot=this.boot;this.suppressManualRevoke=true;try{this.authority.revoke('EXPLICIT_PENDING_HANDOFF');}finally{this.suppressManualRevoke=false;}
  const work=(async()=>{try{
   this.record('MANUAL_HANDOFF_REQUESTED',{generation,session,boot,callerChallengeReserved:true,leaseActive:false,deadlineMs:5000},true);
   this.rc(MANUAL_NEUTRAL,'EXPLICIT_NEUTRAL_HANDOFF_SAFETY_ONLY');this.manualWireOwned=true;this.manualWireIdentity={socket:this.socket,session:this.sessionId,boot:this.boot,run:this.run};
   await this.observedManualMode(5,'manual-handoff',generation);this.checkControl();
   if(generation!==this.manualGeneration||session!==this.sessionId||boot!==this.boot||this.manualTerminal||!(this.samples[0].fields.base_mode&128)||this.samples[0].fields.custom_mode!==5)throw Error('MANUAL_HANDOFF_CANCELLED');
   this.suppressManualRevoke=true;let lease;try{lease=this.authority.claim(session,boot,this.authority.issue());}finally{this.suppressManualRevoke=false;}
   this.record('MANUAL_HANDOFF_READY',{generation,lease,mode:5,state:this.authority.state,ttlMs:200,firstNeutralInputRequired:true},true);return lease;
  }catch(e){if(!this.manualTerminal&&generation===this.manualGeneration)await this.releaseManual('HANDOFF_FAILED:'+e.message);throw e;}})();
  this.manualClaimTask=work;try{return await work;}finally{if(this.manualClaimTask===work)this.manualClaimTask=null;}
 }
 sendOwnedStaleNeutral(reason){
  const owned=this.manualWireIdentity;
  if(this.manualTerminal||this.closed||this.closingTraining||!this.manualWireOwned||!owned||!this.socket?.writable||this.socket!==owned.socket||this.sessionId!==owned.session||this.boot!==owned.boot||this.run!==owned.run||this.vehicle?.system!==42||this.vehicle?.component!==1||this.ambiguous)throw Error('OWNED_STALE_NEUTRAL_WIRE_UNCONFIRMED');
  const epoch=JSON.parse(fs.readFileSync(this.out+'/backend-state/epoch.json'));
  if(epoch.run!==owned.run||epoch.epoch!==owned.boot||epoch.status!=='LIVE')throw Error('OWNED_STALE_NEUTRAL_EPOCH_UNCONFIRMED');
  const b=encodeRC(MANUAL_NEUTRAL,{seq:this.sequence++});this.record('RC_FIXED_NEUTRAL_SAFETY_INTENT',{channels:MANUAL_NEUTRAL,reason,run:this.run,session:this.sessionId,boot:this.boot,rawHex:b.toString('hex'),scope:'PREVIOUSLY_OWNED_WIRE_STALE_NEUTRAL_ONLY_NOT_EXECUTION_OR_FRESH_HOLD'},true);
  const queued=this.socket.write(b);this.record('RC_FIXED_NEUTRAL_LOCAL_WRITE_RETURN',{queued,notExecution:true},true);
 }
 async releaseManual(reason='EXPLICIT_RELEASE'){
  if(this.manualReleaseTask)return this.manualReleaseTask;
  this.cancelManual(reason);this.suppressManualRevoke=true;try{this.authority.revoke(reason);}finally{this.suppressManualRevoke=false;}
  if(this.manualTerminal||!this.manualWireOwned)return;if(this.manualReleaseTask)return this.manualReleaseTask;
  const generation=this.manualGeneration,session=this.sessionId,boot=this.boot;
  const work=(async()=>{try{this.checkControl();}catch(e){if(['FRESH_OBSERVED_SESSION_REQUIRED','PHYSICS_STALE_OR_FUTURE','CLOCK_BRACKET_STALE'].includes(e.message)){try{this.sendOwnedStaleNeutral(reason);}catch(safetyError){this.record('RC_FIXED_NEUTRAL_UNCONFIRMED',{reason,error:safetyError.message},true);throw safetyError;}}throw e;}if(!(this.samples[0].fields.base_mode&128)){this.rc(MANUAL_RELEASE,'DISARMED_MANUAL_RELEASE');this.manualWireOwned=false;return;}
   this.rc(MANUAL_NEUTRAL,'MANUAL_RELEASE_NEUTRAL_SAFETY_ONLY');await this.observedManualMode(4,'manual-release',generation);
   if(this.manualTerminal||generation!==this.manualGeneration||session!==this.sessionId||boot!==this.boot)throw Error('MANUAL_RELEASE_CANCELLED');
   this.rc(MANUAL_RELEASE,'OBSERVED_GUIDED_THEN_MANUAL_RELEASE');this.manualWireOwned=false;this.manualWireIdentity=null;this.record('MANUAL_GUIDED_RELEASE_OBSERVED',{generation,mode:4,authorityRestored:false},true);
  })();this.manualReleaseTask=work;try{return await work;}finally{if(this.manualReleaseTask===work)this.manualReleaseTask=null;}
 }
 async command(name){if(name==='hold'){await this.releaseManual('OPERATOR_GUIDED_HOLD');this.checkControl();if(this.samples[0].fields.custom_mode!==4)await super.command('guided');return this.snapshot();}return super.command(name);}
 async prepare(){this.manualTerminal=null;return super.prepare();}
 async land(){this.manualTerminal='LAND';this.cancelManual('LAND_PREEMPTS_MANUAL');this.suppressManualRevoke=true;try{this.authority.revoke('LAND_PREEMPTS_MANUAL');}finally{this.suppressManualRevoke=false;}const result=await super.land();if(this.manualWireOwned){this.rc(MANUAL_RELEASE,'OBSERVED_LAND_GROUND_DISARM_RELEASE');this.manualWireOwned=false;}return result;}

 receive(message){if(this.closed||this.closingTraining)return;const discovery=!this.vehicle;super.receive(message);if(discovery&&this.vehicle&&message.id===0){try{requestObservedHeartbeatStream(this);}catch(e){this.expire('HEARTBEAT_STREAM_REQUEST_FAILED:'+e.message);}}}
 async closeTraining(reason='SESSION_CLOSED'){
  if(this.closed)return;if(this.closeTrainingTask)return this.closeTrainingTask;this.manualTerminal='CLOSING';this.cancelManual(reason);
  this.closeTrainingTask=(async()=>{
   this.authority.revoke(reason);
   if(this.pending)this.failPending('SESSION_CLOSED:'+reason);
   this.closingTraining=true;
   await super.closeTraining();
  })();return this.closeTrainingTask;
 }
}
