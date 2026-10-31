import {APStream40} from './adapter.mjs';
import {dialogue,rx,version,parameters,join,resequence,resequenceAP,signed,opaque} from './fixtures.mjs';
import {encodeFull,FullFramer,hex,unhex} from './wire.mjs';
import {ids} from '../apflight36/fixtures.mjs';
import {exact,bounded,digest,same,int} from '../apflight36/types.mjs';
const no={networkSent:false,flightAuthority:false,executionProven:false,operationalAllowed:false};
const good={phase:'MOCK_READBACK_READY',inspectionAvailable:true,parameters:28,policy:'MAPPED_MOCK',preflight:'UNKNOWN',failsafe:'MODELED_MOCK',altitude:'INSIDE_CONFIGURED_BAND',...no};
const bad={phase:'INVALIDATED',inspectionAvailable:false,parameters:0,policy:'UNKNOWN',preflight:'UNKNOWN',failsafe:'UNKNOWN',altitude:'UNKNOWN',...no};
export async function run(i){exact(i,['contract','profile','apState','altitude','steps','inspectAtMs','writerFault']);bounded(i,1024*1024);if(!Array.isArray(i.steps)||i.steps.length>2048||typeof i.writerFault!=='boolean')throw Error('mock bounds');
 const a=new APStream40(i.contract,{idFactory:ids(),persist:i.writerFault?async()=>{throw Error('INJECTED_WRITER_FAULT');}:undefined}),outputs=[],errors=[];
 for(const s of i.steps){exact(s,s.op==='rx'?['op','rawHex','t','meta']:['op','t']);int(s.t,0,1e12,'step clock');if(!['rx','discover','disconnect','owner','tick'].includes(s.op))throw Error('operation');
  try{if(s.op==='rx')outputs.push(...await a.receive(unhex(s.rawHex),s.meta,s.t));else if(s.op==='discover')outputs.push(await a.startDiscovery(s.t));else if(s.op==='disconnect')a.disconnect();else if(s.op==='owner')a.loseOwner();else a.tick(s.t);}catch(e){errors.push(e.message);}
 }
 const view=await a.inspect(i.profile,i.inspectAtMs,{apState:i.apState,altitude:i.altitude}),snapshot=a.snapshot(i.inspectAtMs);let proof=null;try{proof=a.proof(i.inspectAtMs);}catch{}
 return {a,outputs,errors,view,snapshot,audit:a.audit(),output:{phase:snapshot.phase,inspectionAvailable:!!proof,parameters:proof?Object.keys(proof.typedReadback.values).length:0,policy:view.policy?.status??'UNKNOWN',preflight:view.preflight?.assessment.state??'UNKNOWN',failsafe:view.failsafe?.status??'UNKNOWN',altitude:view.altitude?.state??'UNKNOWN',...no}};
}
export async function replayCase(c){exact(c,['id','input','expected','sha256']);const{sha256,...body}=c;if(await digest(body)!==sha256)throw Error('case SHA');const r=await run(c.input);return {id:c.id,matched:same(r.output,c.expected),output:r.output,snapshot:r.snapshot,errors:r.errors,outputCount:r.outputs.length,outputsSha256:await digest(r.outputs),auditSha256:await digest(r.audit),...no};}
export async function makeCorpus(){const cases=[],add=async(id,fn=null,expected=good)=>{const i=await dialogue();await fn?.(i);const body={id,input:i,expected:structuredClone(expected)};cases.push({...body,sha256:await digest(body)});};
 await add('full-discovery-typed-read');
 await add('fragmented-full-dialogue',i=>{i.steps=i.steps.flatMap(s=>{if(s.op!=='rx')return [s];const b=unhex(s.rawHex),n=Math.floor(b.length/2);return [{...s,rawHex:hex(b.slice(0,n))},{...s,rawHex:hex(b.slice(n))}];});});
 await add('coalesced-version-and-readback',i=>{const part=i.steps.splice(2);i.steps.push(rx(i,join(part.map(s=>unhex(s.rawHex))),20100));});
 await add('auxiliary-over-half-range-without-rewriting',i=>{const extra=Array.from({length:180},()=>rx(i,encodeFull(74,{airspeed:3,groundspeed:2,alt:40}),20003));i.steps.splice(3,0,...extra);resequenceAP(i.steps);});
 await add('sequence-wrap-full',i=>{let n=250;i.steps.forEach(s=>{if(s.op==='rx')s.rawHex=hex(resequence(unhex(s.rawHex),n++%256));});});
 await add('foreign-camera-heartbeat-version',i=>{i.steps.splice(2,0,rx(i,encodeFull(0,{type:30,autopilot:8},{component:100,seq:123}),20001),rx(i,version({sender:{component:100},seq:124}),20001));});
 await add('foreign-opaque-does-not-swallow-boundary',i=>i.steps.splice(3,0,rx(i,opaque(),20003)));
 await add('foreign-signed-keeps-trailer-opaque',i=>i.steps.splice(3,0,rx(i,signed(encodeFull(74,{}, {component:100,seq:88})),20003)));
 await add('wrong-target-ACK-not-proof',i=>{i.steps.splice(2,0,rx(i,encodeFull(77,{command:512,result:2,target_system:44,target_component:190}),20001));resequenceAP(i.steps);});
 await add('ACK-accepted-is-diagnostic',i=>{i.steps.splice(2,0,rx(i,encodeFull(77,{command:512,result:0,target_system:255,target_component:190}),20001));resequenceAP(i.steps);});
 await add('ACK-in-progress-does-not-renew-deadline',i=>{i.steps.splice(2,0,rx(i,encodeFull(77,{command:512,result:5,target_system:255,target_component:190}),20001));resequenceAP(i.steps);});
 await add('old-duplicate-parameter-does-not-refresh',i=>i.steps.splice(4,0,structuredClone(i.steps[3])));
 await add('reordered-same-value-quarantined',i=>i.steps.splice(6,0,{...structuredClone(i.steps[3]),t:20009,meta:rx(i,new Uint8Array([1]),20009).meta}));
 const negatives=[
  ['disconnect-after-ready',i=>i.steps.push({op:'disconnect',t:20110})],['owner-after-ready',i=>i.steps.push({op:'owner',t:20110})],
  ['stale-after-ready',i=>{i.inspectAtMs=22000;}],
  ['foreign-session-context',i=>i.steps[4].meta.target.session='other'],['foreign-boot-context',i=>i.steps[4].meta.target.boot='other'],['foreign-link-context',i=>i.steps[4].meta.target.link='other'],['foreign-epoch',i=>i.steps[4].meta.epoch='other'],
  ['future-receipt',i=>i.steps[4].meta.receivedAtMs++],['host-clock-regression',i=>i.steps[4].t=19000],
  ['changed-firmware-UID',i=>i.steps.push(rx(i,version({seq:38,fields:{uid:'999'}}),20110))],
  ['duplicate-version-changed-capabilities',i=>i.steps.push(rx(i,version({seq:37,fields:{capabilities:'155652'}}),20110))],
  ['duplicate-heartbeat-incompatible-AP',i=>i.steps.push(rx(i,encodeFull(0,{type:2,autopilot:8},{seq:37}),20110))],
  ['typed-parameter-changed',i=>i.steps.push(rx(i,parameters({firstSeq:38,values:{FENCE_ENABLE:0}})[0].raw,20110))],
  ['duplicate-typed-parameter-changed',i=>i.steps.push(rx(i,parameters({firstSeq:37,values:{FENCE_ENABLE:0}})[0].raw,20110))],
  ['typed-parameter-invalid-type',i=>{i.steps[3].rawHex=hex(parameters({firstSeq:2,types:{FENCE_ENABLE:9}})[0].raw);}],
  ['known-corrupt-frame',i=>{const b=unhex(i.steps[4].rawHex);b[b.length-1]^=1;i.steps[4].rawHex=hex(b);}],
  ['signed-selected-AP-version',i=>i.steps[2].rawHex=hex(signed(unhex(i.steps[2].rawHex)))],
  ['opaque-selected-AP-during-discovery',i=>i.steps.splice(2,0,rx(i,opaque({system:1,component:1}),20001))],
  ['discovery-correct-target-NACK',i=>{i.steps.splice(2,0,rx(i,encodeFull(77,{command:512,result:2,target_system:255,target_component:190}),20001));resequenceAP(i.steps);}],
  ['discovery-late-response',i=>{i.steps.splice(2);i.steps.push(rx(i,version({seq:1}),21502));i.inspectAtMs=21502;}],
  ['AP-boot-regression-after-ready',i=>i.steps.push(rx(i,encodeFull(33,{time_boot_ms:1000},{seq:38}),20110))],
  ['auxiliary-AP-boot-regression',i=>{i.steps.splice(3,0,rx(i,encodeFull(30,{time_boot_ms:20000}),20003),rx(i,encodeFull(30,{time_boot_ms:10000}),20003));resequenceAP(i.steps);}],
  ['partial-frame-expiry',i=>{i.steps.push(rx(i,version({seq:38}).slice(0,9),20110));i.inspectAtMs=21611;}],
  ['writer-failure',i=>{i.writerFault=true;}],
 ];for(const[id,fn]of negatives)await add(id,fn,bad);
 await add('request-without-version-not-proof',i=>{i.steps.splice(2);i.inspectAtMs=20120;},{...bad,phase:'DISCOVERY_PENDING'});
 await add('wrong-target-only-version-is-quarantined',i=>{i.steps.splice(2);i.steps.push(rx(i,version({sender:{component:100},seq:1}),20002));},{...bad,phase:'DISCOVERY_PENDING'});
 await add('wrong-system-only-version-is-quarantined',i=>{i.steps.splice(2);i.steps.push(rx(i,version({sender:{system:2},seq:1}),20002));},{...bad,phase:'DISCOVERY_PENDING'});
 await add('wrong-system-parameter-cannot-complete',i=>{const b=unhex(i.steps[3].rawHex);b[5]=2;i.steps[3].rawHex=hex(resequence(b,2));},{...bad,phase:'READING_PARAMETERS'});
 await add('unsolicited-version-before-request',i=>{i.steps=i.steps.filter(s=>s.op!=='discover');},{...bad,phase:'PEER_OBSERVED'});
 await add('missing-AP-state-keeps-failsafe-unknown',i=>{i.apState=null;},{...good,failsafe:'UNKNOWN'});
 await add('missing-reviewed-Home-unknown',i=>{i.altitude.home=null;},{...good,altitude:'UNKNOWN'});
 return {format:'aeris-apstream40-corpus',version:1,origin:'MOCK_REPLAY',cases,...no};
}
export async function replayCorpus(c){exact(c,['format','version','origin','cases',...Object.keys(no)]);bounded(c,8*2**20);if(c.format!=='aeris-apstream40-corpus'||c.version!==1||c.origin!=='MOCK_REPLAY'||!same(Object.fromEntries(Object.keys(no).map(k=>[k,c[k]])),no)||!Array.isArray(c.cases)||c.cases.length>64||new Set(c.cases.map(x=>x.id)).size!==c.cases.length)throw Error('corpus scope');const results=[];for(const x of c.cases)results.push(await replayCase(x));return {status:results.every(r=>r.matched)?'MOCK_PASS':'FAIL',caseCount:results.length,results,corpusSha256:await digest(c),...no};}
