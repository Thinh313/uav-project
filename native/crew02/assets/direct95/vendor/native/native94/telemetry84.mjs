import{sha256Text}from'../../../../workflow/preflight/sha256.mjs';
import{stable}from'../../pilot/mapping51/common.mjs';
const hash=x=>sha256Text(stable(x));
export function envelope84(link,instance,sequence){
 const at=link?.clock?.()??performance.now(),ages={},stamps={};
 for(const [name,id]of Object.entries({heartbeat:0,position:33,attitude:30,gps:24,health:1,home:242})){
  const s=link?.samples?.[id];ages[name]=s?Math.max(0,at-s.at):null;stamps[name]=s?.at??null;
 }
 return{format:'aeris-fly84-envelope',instance,sequence,hostUtc:new Date().toISOString(),ageMs:ages,sampleStamp:stamps,clock:'ANDROID_MONOTONIC_AGES_ONLY',tailOnly:true};
}
export function sealedRawReference84(native,run){
 const raw=native?.raw;if(native?.ok!==true||native.open!==false||native.run!==run||!/^s[a-f0-9]{20}$/.test(run)||native.authorityRestorable!==false||native.closureStorageError!==null||raw?.closed!==true||raw.failed!==false||!Number.isSafeInteger(raw.records)||raw.records<1||!Number.isSafeInteger(raw.bytes)||raw.bytes<raw.records||raw.bytes>32*1024*1024||typeof raw.head!=='string'||!/^[a-f0-9]{64}$/.test(raw.head))throw Error('REVIEW_SEALED_NATIVE_RAW_REQUIRED');
 return{format:'aeris-sealed-native-raw-reference',version:1,run,head:raw.head,records:raw.records,bytes:raw.bytes,closed:true,failed:false};
}
export function geography84(link,plan,run,instance,sealedNative=null){
 if(!Array.isArray(link.trace)||link.trace.length>10000)throw Error('REVIEW_TRACE_SOURCE_BOUND');const overflow=link.trace.length>1200;
 const body={format:'aeris-geography84',version:1,hashScheme:'CANONICAL_KEYS_V1',run,instance,session:link.sessionId,boot:link.boot,
  planSha256:plan.sha256,missionSha256:plan.missionSha256,datum:'WGS84_DEGREES_MSL_METRES_RELATIVE_HOME_METRES',
  timeBasis:'ANDROID_MONOTONIC_MS_PER_INSTANCE_NOT_WALL_CLOCK',home:link.boundHome??link.observedHome(),
  route:plan.compiled.items.filter(i=>[16,22].includes(i.command)&&i.seq!==0).map(i=>({seq:i.seq,lat:i.x/1e7,lon:i.y/1e7})),
  qualificationPolicy:'GPS3D_FRESH_SELECTED_SOURCE_V1',
  points:overflow?[]:structuredClone(link.trace),fullWithinBound:!overflow,pointBound:1200,
  ...(overflow?{trackOverflow:true,pointCount:link.trace.length,reason:'WORKSPACE_TRACK_BOUND_RAW_REFERENCE',rawReference:sealedRawReference84(sealedNative,run)}:{})};
 return{...body,sha256:hash(body)};
}
