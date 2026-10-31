/** Explicitly finish an unexecuted, freshly observed ground/disarmed session. No AP writes. */
export function groundRecoveryCheck(link,q){
 if(q.confirmSimulation!==true||q.groundDisarmConfirmed!==true)throw Error('EXPLICIT_SIMULATOR_GROUND_DISARM_REVIEW_REQUIRED');
 if(q.session!==link.sessionId||q.boot!==link.boot)throw Error('GROUND_RECOVERY_EXACT_SESSION_BOOT');
 if(link.stage!=='ARMED_HOME_REVIEW'||link.autoSeen||link.failure||link.ambiguous||link.pending)throw Error('GROUND_RECOVERY_UNEXECUTED_UNAMBIGUOUS_IDLE_ONLY');link.fresh();
 if(![0,33,245].every(id=>link.freshness(id,1500)))throw Error('GROUND_RECOVERY_FRESH_OBSERVATIONS_REQUIRED');const s=link.snapshot(),height=link.samples[33]?.fields.relative_alt/1000;if(s.armed!==false||link.samples[0].fields.base_mode&128||link.samples[245]?.fields.landed_state!==1||!Number.isFinite(height)||Math.abs(height)>.5)throw Error('GROUND_RECOVERY_OBSERVED_DISARM_LANDED_NEAR_GROUND_REQUIRED');
 return{atMs:link.now(),heartbeatAtMs:link.samples[0].at,positionAtMs:link.samples[33].at,landedAtMs:link.samples[245].at,armed:false,landedState:1,relativeHomeM:height,session:link.sessionId,boot:link.boot,noAutoObserved:true};
}
export async function reviewGroundRecovery(link,q){const before=groundRecoveryCheck(link,q);link.record('FIELD02_GROUND_RECOVERY_INTENT',{before,homeReviewSha256:link.homeReview?.sha256??null,authorityRestorable:false,requiresManualNewConnection:true});await link.until(()=>[0,33,245].every(id=>link.samples[id]?.at>before.atMs),2000);const after=groundRecoveryCheck(link,q);link.record('FIELD02_GROUND_RECOVERY_OBSERVED',{before,after,requiresManualNewConnection:true,disposition:'CLOSE_INCOMPLETE_NO_AUTO_RECONNECT',noAPCommands:true});return{before,after};}
