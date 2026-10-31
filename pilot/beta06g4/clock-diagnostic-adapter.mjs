import{createHash}from'node:crypto';import{validateClockEvents}from'../clockvideo05/media/clock-journal.mjs';
/** Diagnostic-only routing metadata normalization; no calibration or control values change. */
export function normalizeClockDiagnostics(q,role,expectedViewerId){
 if(!q||!Array.isArray(q.events)||q.events.length<1||q.events.length>32)throw Error('CLOCK_DIAGNOSTIC_SCHEMA');
 const identityKeys=['run','boot','configId','feed','profileId'],six=[...identityKeys,'viewerId'].sort().join(),normalizations=[];
 const events=q.events.map((e,index)=>{const s=e?.session,keys=s&&typeof s==='object'&&!Array.isArray(s)?Object.keys(s).sort():[];
  if(role==='publisher'&&keys.join()===six){if(typeof expectedViewerId!=='string'||s.viewerId!==expectedViewerId)throw Error('CLOCK_DIAGNOSTIC_VIEWER_TARGET');normalizations[index]={normalization:'EXACT_PUBLISHER_ROUTING_VIEWER_ID_REMOVED',inputSessionKeys:keys,inputSessionObjectJsonSha256:createHash('sha256').update(JSON.stringify(s)).digest('hex'),viewerTargetVerified:true};return{...e,session:Object.fromEntries(identityKeys.map(k=>[k,s[k]]))};}
  normalizations[index]=null;return e;
 });
 const validated=validateClockEvents({...q,events},role);return{events:validated,normalizations};
}
