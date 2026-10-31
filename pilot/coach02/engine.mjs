import{CONTRACT,PROFILES,EXERCISES,zero,initialModel,stepModel,targetAt,errorAt,validAxes,need,KEY_CODES,axesForKeys}from'./contract.mjs';
const equalContext=(a,b)=>['sessionId','hostBoot','operatorId','sourceClockId','sourceKind','exerciseId','profileId'].every(k=>a[k]===b[k]);
const codeKeys=new Set(['KeyW','KeyS','KeyA','KeyD','KeyR','KeyF','KeyQ','KeyE']);
export function createState(context,challenge,hostMs){
 need(Object.hasOwn(PROFILES,context.profileId)&&Object.hasOwn(EXERCISES,context.exerciseId),'EXERCISE_PROFILE');need(/^m[a-f0-9]{32}$/.test(context.sessionId),'SESSION_ID');
 need(['BROWSER_KEYBOARD_MOCK','AXES_PANEL_MOCK','SCRIPTED_MOCK'].includes(context.sourceKind),'SOURCE_KIND');
 for(const k of ['sessionId','hostBoot','operatorId','sourceClockId'])need(typeof context[k]==='string'&&context[k].length>0&&context[k].length<=80,'CONTEXT_TEXT');
 need(typeof challenge.nonce==='string'&&challenge.nonce.length>0&&challenge.nonce.length<=80,'CHALLENGE_NONCE');
 need(Number.isFinite(challenge.t1)&&Number.isFinite(challenge.t2)&&challenge.t2>=challenge.t1&&hostMs>=challenge.t2,'CHALLENGE_CLOCK');
 return{context:structuredClone(context),challenge:structuredClone(challenge),nextSeq:1,lastHostMs:hostMs,lastSourceMs:null,lastKeySeq:0,lastKeySourceMs:0,clock:null,neutralAtHostMs:null,generation:0,lease:null,axes:zero(),model:initialModel(),ticks:0,simTimeS:0,finished:false,completed:false,reason:null,flags:[],rejections:0};
}
const flag=(s,c)=>{if(!s.flags.includes(c))s.flags.push(c);};
function invalidate(s,reason){s.lease=null;s.axes=zero();s.neutralAtHostMs=null;flag(s,reason);}
function recordKeys(s,action){const events=action.keyEvents??[];need(Array.isArray(events)&&events.length<=32,'KEY_EVENTS_BOUND');let seq=s.lastKeySeq,time=s.lastKeySourceMs;for(const e of events){need(s.context.sourceKind==='BROWSER_KEYBOARD_MOCK'&&codeKeys.has(e.code)&&typeof e.down==='boolean'&&e.seq===seq+1&&Number.isFinite(e.sourceTimeMs)&&e.sourceTimeMs<=action.sourceTimeMs&&e.sourceTimeMs>=time&&(e.rawDOMTimestamp===null||Number.isFinite(e.rawDOMTimestamp)),'KEY_EVENT_CONTEXT');seq=e.seq;time=e.sourceTimeMs;}s.lastKeySeq=seq;s.lastKeySourceMs=time;}
function correlate(s,t,now){
 need(s.clock,'CLOCK_NOT_SYNCED');need(Number.isFinite(t)&&t>=0,'SOURCE_TIME');
 if(s.lastSourceMs!==null&&t<s.lastSourceMs){invalidate(s,'SOURCE_CLOCK_REGRESSION');s.clock=null;throw Error('SOURCE_CLOCK_REGRESSION');}
 const age=now-s.clock.syncedAtHostMs;need(age>=0&&age<=CONTRACT.clockMaxAgeMs,'CLOCK_EXPIRED');
 const drift=Math.abs(t-s.clock.anchorSourceMs)*CONTRACT.clockDriftPpm/1e6,lower=t+s.clock.offsetLowerMs-drift,upper=t+s.clock.offsetUpperMs+drift;
 need(lower<=now,'INPUT_FUTURE_CLOCK');const ageUpperMs=now-lower;need(ageUpperMs<=CONTRACT.inputAgeMaxMs,'INPUT_STALE');
 need(upper-lower<=CONTRACT.clockMaxWidthMs+10,'CLOCK_UNCERTAINTY');s.lastSourceMs=t;
 return{lowerHostMs:lower,upperHostMs:Math.min(upper,now),ageUpperMs,offsetWidthMs:upper-lower,hostClock:s.context.hostBoot,sourceClock:s.context.sourceClockId,method:'FOUR_TIMESTAMP_INTERVAL_WITH_DRIFT_NOT_SHARED_CLOCK'};
}
export function apply(previous,action,hostMs){
 const s=structuredClone(previous);let bounds=null;
 const result=(accepted,code)=>({state:s,outcome:{accepted,code,bounds}});
 try{
  need(Number.isFinite(hostMs)&&hostMs>=s.lastHostMs,'HOST_CLOCK_REGRESSION');s.lastHostMs=hostMs;
  need(!s.finished,'SESSION_FINISHED');
  if(action.kind==='hostAbort'){need(action.hostBoot===s.context.hostBoot,'HOST_BOOT_CONTEXT');s.finished=true;s.reason='OBSERVER_RESTART_INCOMPLETE';invalidate(s,action.reason??'OBSERVER_RESTART');return result(true,'HOST_ABORTED');}
  if(s.lease&&hostMs-s.lease.lastHostMs>CONTRACT.leaseMs)invalidate(s,'LEASE_EXPIRED');
  need(equalContext(action,s.context),'CONTEXT_MISMATCH');need(action.seq===s.nextSeq,'REQUEST_SEQUENCE');s.nextSeq++;
  if(action.kind!=='tick'&&action.keyEvents){try{recordKeys(s,action);}catch(e){flag(s,e.message);if(!['revoke','finish'].includes(action.kind))throw e;}}
  need(!s.finished,'SESSION_FINISHED');
  if(action.kind==='finish'){
   s.finished=true;s.reason=s.completed?'EXERCISE_OBSERVED_COMPLETE':'USER_STOP_INCOMPLETE';s.lease=null;s.axes=zero();return result(true,'FINISHED');
  }
  if(action.kind==='revoke'){
   s.lease=null;s.axes=zero();s.neutralAtHostMs=null;if(s.ticks&&!s.completed)flag(s,action.reason==='BACKGROUND'?'BACKGROUND_INTERRUPTION':'AUTHORITY_REVOKED');return result(true,'REVOKED');
  }
  if(action.kind==='challenge'){need(typeof action.serverNonce==='string'&&Number.isFinite(action.t1)&&Number.isFinite(action.t2)&&action.t2>=action.t1&&action.t2<=hostMs,'CHALLENGE_CLOCK');s.challenge={nonce:action.serverNonce,t1:action.t1,t2:action.t2};s.clock=null;s.lease=null;s.axes=zero();s.neutralAtHostMs=null;if(s.ticks)flag(s,'RECLOCK_DURING_EXERCISE');return result(true,'CHALLENGE_ISSUED');}
  if(action.kind==='sync'){
   const q=s.challenge;need(action.nonce===q.nonce&&hostMs-q.t2<=1000,'CLOCK_CHALLENGE');need([action.t0,action.t3,action.sourceTimeMs].every(Number.isFinite)&&action.t3>=action.t0&&action.sourceTimeMs>=action.t3,'SYNC_SOURCE_TIMES');
   const lower=q.t2-action.t3,upper=q.t1-action.t0,rtt=action.t3-action.t0;need(rtt<=CONTRACT.clockMaxRttMs&&upper>=lower&&upper-lower<=CONTRACT.clockMaxWidthMs,'SYNC_UNCERTAINTY');
   if(s.ticks)flag(s,'RECLOCK_DURING_EXERCISE');s.lease=null;s.axes=zero();s.neutralAtHostMs=null;s.clock={offsetLowerMs:lower,offsetUpperMs:upper,anchorSourceMs:action.sourceTimeMs,syncedAtHostMs:hostMs,sourceClockId:s.context.sourceClockId,hostClockId:s.context.hostBoot};s.lastSourceMs=action.sourceTimeMs;return result(true,'SYNCED');
  }
  bounds=correlate(s,action.sourceTimeMs,hostMs);
  if(action.kind==='neutral'){
   need(validAxes(action.axes)&&Object.values(action.axes).every(x=>x===0)&&(!action.heldCodes||Array.isArray(action.heldCodes)&&action.heldCodes.length===0),'NEUTRAL_REQUIRED');s.axes=zero();s.neutralAtHostMs=hostMs;return result(true,'NEUTRAL_OBSERVED');
  }
  if(action.kind==='grant'){
   need(!action.heldCodes||Array.isArray(action.heldCodes)&&action.heldCodes.length===0,'NEUTRAL_REQUIRED');need(!s.completed,'EXERCISE_COMPLETE');need(!s.lease,'ALREADY_GRANTED');need(s.neutralAtHostMs!==null&&hostMs-s.neutralAtHostMs<=CONTRACT.neutralFreshMs&&Object.values(s.axes).every(x=>x===0),'FRESH_NEUTRAL_REQUIRED');
   s.generation++;s.lease={id:s.context.sessionId+'-lease-'+s.generation,generation:s.generation,operatorId:s.context.operatorId,createdSourceMs:action.sourceTimeMs,lastHostMs:hostMs};return result(true,'GRANTED');
  }
  need(action.kind==='tick','ACTION_KIND');need(!s.completed,'EXERCISE_COMPLETE');need(s.lease&&action.leaseId===s.lease.id,'CURRENT_LEASE_REQUIRED');need(validAxes(action.axes),'AXES_RANGE');need(action.sourceTimeMs>(s.lastTickSourceMs??-Infinity),'DUPLICATE_INPUT_TIME');
  need(Array.isArray(action.keyEvents)&&action.keyEvents.length<=32,'KEY_EVENTS_BOUND');
  if(action.heldCodes!==undefined){need(s.context.sourceKind==='BROWSER_KEYBOARD_MOCK'&&Array.isArray(action.heldCodes)&&action.heldCodes.length<=8&&new Set(action.heldCodes).size===action.heldCodes.length&&action.heldCodes.every(k=>KEY_CODES.has(k)),'HELD_KEYS');const expected=axesForKeys(new Set(action.heldCodes));need(Object.keys(expected).every(k=>expected[k]===action.axes[k]),'KEY_AXES_MISMATCH');}
  recordKeys(s,action);
  s.axes=structuredClone(action.axes);s.model=stepModel(s.model,s.axes,PROFILES[s.context.profileId]);s.ticks++;s.simTimeS=s.ticks*CONTRACT.dtS;s.lastTickSourceMs=action.sourceTimeMs;s.lease.lastHostMs=hostMs;
  if(Math.abs(s.model.x)>25||Math.abs(s.model.y)>25||s.model.z<2||s.model.z>20){invalidate(s,'REFERENCE_ENVELOPE');s.finished=true;s.reason='REFERENCE_ENVELOPE';}
  s.completed=s.ticks>=Math.round(EXERCISES[s.context.exerciseId].durationS/CONTRACT.dtS);if(s.completed)s.lease=null;
  return result(true,'STEP_OBSERVED');
 }catch(e){s.rejections++;flag(s,e.message);if(['SYNC_UNCERTAINTY','CLOCK_CHALLENGE','SYNC_SOURCE_TIMES','CHALLENGE_CLOCK'].includes(e.message)){s.clock=null;s.lease=null;s.axes=zero();s.neutralAtHostMs=null;}if(['INPUT_STALE','CLOCK_EXPIRED','INPUT_FUTURE_CLOCK','CLOCK_UNCERTAINTY','HOST_CLOCK_REGRESSION','DUPLICATE_INPUT_TIME'].includes(e.message)){s.lease=null;s.axes=zero();s.neutralAtHostMs=null;}return result(false,e.message);}
}
export function effectiveView(s,now){const v=structuredClone(s);if(v.lease&&now-v.lease.lastHostMs>CONTRACT.leaseMs){v.lease=null;v.axes=zero();v.effectiveAuthority='EXPIRED_NOT_RESTORED';}else v.effectiveAuthority=v.lease?'MOCK_ONLY_GRANTED':'NONE';v.target=targetAt(v.context.exerciseId,v.simTimeS);v.effectiveClock=v.clock&&now-v.clock.syncedAtHostMs<=CONTRACT.clockMaxAgeMs?'SYNCED_BOUNDED':'UNAVAILABLE_OR_EXPIRED';v.physicalHidVerified=false;v.operational=false;v.authorityRestorable=false;return v;}
const canonicalKeys=keys=>[...keys].sort().join(',');
const p95=values=>values.length?[...values].sort((a,b)=>a-b)[Math.max(0,Math.ceil(values.length*.95)-1)]:null;
export function assess(context,rows,finalState){
 const exercise=EXERCISES[context.exerciseId],ticks=rows.filter(r=>r.data?.action?.kind==='tick'&&r.data.outcome.accepted),samples=ticks.map(r=>({record:r.n,...errorAt(r.data.state.model,targetAt(context.exerciseId,r.data.state.simTimeS))}));
 const within=samples.filter(e=>e.horizontalM<=exercise.horizontalToleranceM&&e.altitudeM<=exercise.altitudeToleranceM&&e.headingDeg<=exercise.headingToleranceDeg).length;
 let variation=0;const slew=[];for(let i=1;i<ticks.length;i++){const a=ticks[i-1].data.action,b=ticks[i].data.action,dt=(b.sourceTimeMs-a.sourceTimeMs)/1000;if(dt>0){const delta=Math.hypot(...Object.keys(b.axes).map(k=>b.axes[k]-a.axes[k]));variation+=delta;slew.push(delta/dt);}}
 const firstGrant=rows.find(r=>r.data?.action?.kind==='grant'&&r.data.outcome.accepted),last=ticks.at(-1),sourceDurationMs=firstGrant&&last?last.data.action.sourceTimeMs-firstGrant.data.action.sourceTimeMs:null;
 let keyboardCorrelation=null;if(context.sourceKind==='BROWSER_KEYBOARD_MOCK'&&ticks.some(r=>r.data.action.heldCodes!==undefined)){const held=new Set();keyboardCorrelation=true;for(const row of rows){const a=row.data?.action;if(!a)continue;for(const e of a.keyEvents??[]){if(e.down)held.add(e.code);else held.delete(e.code);}if(a.kind==='tick'&&row.data.outcome.accepted){if(!Array.isArray(a.heldCodes)||canonicalKeys(held)!==canonicalKeys(new Set(a.heldCodes)))keyboardCorrelation=false;}if(a.kind==='revoke'||a.kind==='hostAbort')held.clear();}}
 const gates={recordingClosed:finalState.finished,allExerciseSteps:ticks.length===Math.round(exercise.durationS/CONTRACT.dtS),authorityAndClockNoGap:finalState.flags.length===0,sourceTimelineCoversSimulation:sourceDurationMs!==null&&sourceDurationMs>=exercise.durationS*1000*.8,referenceAccuracy:samples.length>0&&within/samples.length>=exercise.minimumWithinFraction};
 if(keyboardCorrelation!==null)gates.keyboardSnapshotsMatchEvents=keyboardCorrelation;
 return{...(keyboardCorrelation!==null?{keyboardSnapshotCorrelation:keyboardCorrelation?'MATCHED_RECORDED_EVENTS':'UNQUALIFIED_EVENT_SNAPSHOT_MISMATCH'}:{}),format:'aeris-manual02-review',version:1,sessionId:context.sessionId,context,contract:CONTRACT,exercise,profile:PROFILES[context.profileId],verdict:Object.values(gates).every(Boolean)?'PASS_REFERENCE_EXERCISE':!gates.recordingClosed||!gates.allExerciseSteps?'INCOMPLETE':'REFERENCE_REQUIREMENTS_NOT_MET',gates,observedSteps:ticks.length,simulatedDurationS:finalState.simTimeS,sourceDurationMs,simToSourceRatio:sourceDurationMs>0?finalState.simTimeS*1000/sourceDurationMs:null,withinReferenceFraction:samples.length?within/samples.length:null,horizontalErrorP95M:p95(samples.map(e=>e.horizontalM)),altitudeErrorP95M:p95(samples.map(e=>e.altitudeM)),headingErrorP95Deg:p95(samples.map(e=>e.headingDeg)),normalizedStickVariation:variation,normalizedSlewP95PerS:p95(slew),keyEventsRecorded:finalState.lastKeySeq,keyEventsReported:rows.reduce((a,r)=>a+(Array.isArray(r.data?.action?.keyEvents)?r.data.action.keyEvents.length:0),0),clockFailures:finalState.flags,trace:ticks.map(r=>({record:r.n,tS:r.data.state.simTimeS,sourceTimeMs:r.data.action.sourceTimeMs,receiverHostMs:r.data.hostMs,position:r.data.state.model,target:targetAt(context.exerciseId,r.data.state.simTimeS),axes:r.data.action.axes,leaseId:r.data.action.leaseId,clockBounds:r.data.outcome.bounds})),evidenceRows:samples.filter(e=>e.horizontalM>exercise.horizontalToleranceM||e.altitudeM>exercise.altitudeToleranceM||e.headingDeg>exercise.headingToleranceDeg).slice(0,12),source:'MOCK_REFERENCE_MODEL',humanPilotSkillCertified:false,learnedAI:false,actualAircraft:false,authorityRestorable:false,limits:['Velocity reference, not calibrated Hera dynamics or attitude/motor flight','Key callback timestamps are not physical HID measurement','Scripted reference runs are not human or learned-AI performance','Checksum/replay is not source authentication','No total pilot skill score or physical transfer qualification']};
}
