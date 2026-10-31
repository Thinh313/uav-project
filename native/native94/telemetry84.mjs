import{createHash}from'node:crypto';
import{stable}from'../../pilot/mapping51/common.mjs';
const hash=x=>createHash('sha256').update(stable(x)).digest('hex');
export function envelope84(link,instance,sequence){
 const at=link?.clock?.()??performance.now(),ages={},stamps={};
 for(const [name,id]of Object.entries({heartbeat:0,position:33,attitude:30,gps:24,health:1,home:242})){
  const s=link?.samples?.[id];ages[name]=s?Math.max(0,at-s.at):null;stamps[name]=s?.at??null;
 }
 return{format:'aeris-fly84-envelope',instance,sequence,hostUtc:new Date().toISOString(),ageMs:ages,sampleStamp:stamps,clock:'HOST_MONOTONIC_AGES_ONLY',tailOnly:true};
}
export function geography84(link,plan,run,instance){
 if(link.trace.length>1200)throw Error('REVIEW_TRACK_BOUND_NO_TRUNCATION');
 const body={format:'aeris-geography84',version:1,hashScheme:'CANONICAL_KEYS_V1',run,instance,session:link.sessionId,boot:link.boot,
  planSha256:plan.sha256,missionSha256:plan.missionSha256,datum:'WGS84_DEGREES_MSL_METRES_RELATIVE_HOME_METRES',
  timeBasis:'HOST_MONOTONIC_MS_PER_INSTANCE_NOT_WALL_CLOCK',home:link.boundHome??link.observedHome(),
  route:plan.compiled.items.filter(i=>[16,22].includes(i.command)&&i.seq!==0).map(i=>({seq:i.seq,lat:i.x/1e7,lon:i.y/1e7})),
  qualificationPolicy:'GPS3D_FRESH_SELECTED_SOURCE_V1',
  points:structuredClone(link.trace),fullWithinBound:true,pointBound:1200};
 return{...body,sha256:hash(body)};
}
