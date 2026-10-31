export {BINARY,PROFILE,STREAMS,packet,validate,rays} from '../simsitl76/contract.mjs';
import {BINARY} from '../simsitl76/contract.mjs';
export const PORT=5897;
export const SCHEDULE=Object.freeze({rep01:['BASELINE','ENABLED'],rep02:['ENABLED','BASELINE'],rep03:['ENABLED','BASELINE'],rep04:['BASELINE','ENABLED']});
export function manifest(m){if(m?.scope!=='OWNED_REAL_SIMDROP77'||m.binarySha256!==BINARY||!/^[a-f0-9]{64}$/.test(m.containerId??'')||!Number.isSafeInteger(m.pid)||m.pid<=0||!m.startedAt||m.target!=='42/1'||!/^run0[1-6]$/.test(m.session)||m.boot!==m.startedAt)throw Error('OWNED_MANIFEST77');}
export function sensorGuard(s,m,now){manifest(m);if(s.target!==m.target||s.session!==m.session||s.boot!==m.boot||s.frame!=='BODY_FRD_METRES'||s.clock!=='HOST_MONOTONIC_MS')throw Error('SENSOR_CONTEXT');if(!Number.isSafeInteger(s.at)||s.at>now||now-s.at>200)throw Error('SENSOR_STALE');if(!Number.isInteger(s.bootMs)||s.bootMs<0||s.bootMs>2**32-1||!Array.isArray(s.ranges)||s.ranges.length!==8||s.ranges.some(v=>!Number.isFinite(v)||v<.2||v>20.01))throw Error('SENSOR_RANGE');return true;}
export function classify({minimumClearanceM,guestDurationMs,tailMaxSpeedMps}){
 if(![minimumClearanceM,guestDurationMs,tailMaxSpeedMps].every(Number.isFinite)||guestDurationMs<0||tailMaxSpeedMps<0)throw Error('FINITE_METRICS');
 if(minimumClearanceM<=0)return 'UNSAFE_VIRTUAL_CONTACT';
 if(minimumClearanceM<1.2)return 'UNSAFE_CLEARANCE_LOSS';
 if(guestDurationMs>=8000&&tailMaxSpeedMps<=.5)return 'SAFE_STOP_OBSERVED';
 return 'INCONCLUSIVE';
}
