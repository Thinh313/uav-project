import {FlightAdapter39} from './adapter.mjs';
import {dialogue,meta,version,parameters,join} from './fixtures.mjs';
import {hex,unhex,encode} from '../mavflight37/wire.mjs';
import {contract} from '../firmware38/contract.mjs';
import {TARGET,CLOCK,ids} from '../apflight36/fixtures.mjs';
import {digest,same,exact,bounded,int} from '../apflight36/types.mjs';

const no={networkSent:false,executionProven:false,flightAuthority:false,operationalAllowed:false};
const good={phase:'MOCK_READBACK_READY',inspectionAvailable:true,paramCount:28,policyStatus:'MAPPED_MOCK',
  preflightState:'UNKNOWN',failsafeStatus:'MODELED_MOCK',altitudeState:'INSIDE_CONFIGURED_BAND',...no};
const invalid={phase:'INVALIDATED',inspectionAvailable:false,paramCount:0,policyStatus:'UNKNOWN',preflightState:'UNKNOWN',failsafeStatus:'UNKNOWN',altitudeState:'UNKNOWN',...no};
export async function run(i){
 exact(i,['contract','profile','apState','altitude','steps','inspectAtMs','writerFault']);bounded(i,262144);
 if(!Array.isArray(i.steps)||i.steps.length>128||typeof i.writerFault!=='boolean')throw Error('bounded mock input');
 const a=new FlightAdapter39(i.contract,{idFactory:ids(),persist:i.writerFault?async()=>{throw Error('INJECTED_WRITER_FAULT');}:undefined}),outputs=[],errors=[];
 for(const s of i.steps){
  exact(s,s.op==='rx'?['op','rawHex','t','meta']:['op','t']);int(s.t,0,1e12,'step clock');
  if(!['rx','disconnect','owner','tick'].includes(s.op))throw Error('unknown operation');
  try{if(s.op==='rx')outputs.push(...await a.receive(unhex(s.rawHex),s.meta,s.t));
   else if(s.op==='disconnect')a.disconnect();else if(s.op==='owner')a.loseOwner();else a.tick(s.t);
  }catch(e){errors.push(e.message);}
 }
 const snap=a.snapshot(i.inspectAtMs);let proof=null,view;
 try{proof=a.proof(i.inspectAtMs);}catch{}
 view=await a.inspect(i.profile,i.inspectAtMs,{apState:i.apState,altitude:i.altitude});
 return {output:{phase:snap.phase,inspectionAvailable:!!proof,paramCount:proof?Object.keys(proof.typedReadback.values).length:0,
   policyStatus:view.policy?.status??'UNKNOWN',preflightState:view.preflight?.assessment.state??'UNKNOWN',
   failsafeStatus:view.failsafe?.status??'UNKNOWN',altitudeState:view.altitude?.state??'UNKNOWN',...no},
  snapshot:snap,outputs,errors,audit:a.audit(),view};
}
export async function replayCase(c){exact(c,['id','input','expected','sha256']);const{sha256,...body}=c;
 if(await digest(body)!==sha256)throw Error('case SHA');const r=await run(c.input);
 return {id:c.id,matched:same(r.output,c.expected),output:r.output,errors:r.errors,
  outputCount:r.outputs.length,outputsSha256:await digest(r.outputs),auditSha256:await digest(r.audit),snapshot:r.snapshot,...no};
}
export async function makeCorpus(){
 const cases=[];const add=async(id,fn=null,expected=good)=>{const i=await dialogue();i.writerFault=false;await fn?.(i);
  const body={id,input:i,expected:structuredClone(expected)};cases.push({...body,sha256:await digest(body)});};
 await add('typed-read-wire-only-preflight-unknown');
 await add('coalesced-version-parameters-telemetry',i=>{const all=join(i.steps.map(s=>unhex(s.rawHex)));i.steps=[{op:'rx',rawHex:hex(all),t:20100,meta:meta(20100)}];});
 await add('fragment-every-frame',i=>{i.steps=i.steps.flatMap(s=>{const b=unhex(s.rawHex),n=Math.floor(b.length/2);return [{...s,rawHex:hex(b.slice(0,n))},{...s,rawHex:hex(b.slice(n))}];});});
 await add('sequence-wrap',i=>{i.steps.forEach((s,k)=>{s.rawHex=hex(resequence(unhex(s.rawHex),(250+k)%256));});});
 await add('duplicate-parameter-quarantined',i=>i.steps.splice(2,0,structuredClone(i.steps[1])));
 await add('late-reordered-quarantined',i=>i.steps.splice(4,0,{...structuredClone(i.steps[1]),t:20007,meta:meta(20007)}));
 await add('foreign-component-does-not-advance',i=>i.steps.splice(1,0,{op:'rx',rawHex:hex(encode(0,{type:2,autopilot:3},{system:1,component:100,seq:120})),t:20001,meta:meta(20001)}));
 await add('same-announcement-no-restart',i=>{i.steps.push({op:'rx',rawHex:hex(version({seq:37})),t:20100,meta:meta(20100)});});
 const badcases=[
  ['changed-firmware-build',i=>i.steps.push({op:'rx',rawHex:hex(version({seq:37,fields:{board_version:39}})),t:20100,meta:meta(20100)})],
  ['changed-firmware-capabilities',i=>i.steps.push({op:'rx',rawHex:hex(version({seq:37,fields:{capabilities:'155652'}})),t:20100,meta:meta(20100)})],
  ['duplicate-sequence-changed-firmware',i=>i.steps.push({op:'rx',rawHex:hex(version({seq:36,fields:{board_version:39}})),t:20100,meta:meta(20100)})],
  ['reordered-sequence-changed-firmware',i=>i.steps.push({op:'rx',rawHex:hex(version({seq:0,fields:{board_version:39}})),t:20100,meta:meta(20100)})],
  ['disconnect-revokes-all',i=>i.steps.push({op:'disconnect',t:20100})],
  ['owner-loss-revokes-all',i=>i.steps.push({op:'owner',t:20100})],
  ['stale-session',i=>{i.inspectAtMs=22000;}],
  ['same-version-not-freshness-renewal',i=>{i.steps.push({op:'rx',rawHex:hex(version({seq:37})),t:21400,meta:meta(21400)});i.inspectAtMs=21501;}],
  ['wrong-session',i=>i.steps[4].meta.target.session='old'],['wrong-boot',i=>i.steps[4].meta.target.boot='old'],
  ['wrong-link',i=>i.steps[4].meta.target.link='other'],['wrong-epoch',i=>i.steps[4].meta.epoch='other'],
  ['future-receipt',i=>i.steps[4].meta.receivedAtMs=i.steps[4].t+1],
  ['now-regression',i=>i.steps[4].t=19000],
  ['parameter-wrong-type',i=>{i.steps[1].rawHex=hex(parameters({types:{FENCE_ENABLE:9}})[0].raw);}],
  ['parameter-index-invalid',i=>{i.steps[1].rawHex=hex(parameters({index:501})[0].raw);}],
  ['parameter-count-invalid',i=>{i.steps[1].rawHex=hex(parameters({count:2})[0].raw);}],
  ['parameter-changes-after-proof',i=>i.steps.push({op:'rx',rawHex:hex(parameters({firstSeq:37,values:{FENCE_ENABLE:0}})[0].raw),t:20100,meta:meta(20100)})],
  ['duplicate-sequence-changed-parameter',i=>i.steps.push({op:'rx',rawHex:hex(parameters({firstSeq:36,values:{FENCE_ENABLE:0}})[0].raw),t:20100,meta:meta(20100)})],
  ['reordered-sequence-changed-parameter',i=>i.steps.push({op:'rx',rawHex:hex(parameters({firstSeq:1,values:{FENCE_ENABLE:0}})[0].raw),t:20100,meta:meta(20100)})],
  ['writer-failure',i=>{i.writerFault=true;}],
  ['corrupt-CRC',i=>{const b=unhex(i.steps[5].rawHex);b[b.length-1]^=1;i.steps[5].rawHex=hex(b);}],
  ['signed-frame',i=>{const b=unhex(i.steps[5].rawHex);b[2]=1;i.steps[5].rawHex=hex(b);}],
  ['unknown-message',i=>{const b=unhex(i.steps[5].rawHex);b[7]=200;i.steps[5].rawHex=hex(b);}],
  ['sequence-half-range',i=>{i.steps[1].rawHex=hex(resequence(unhex(i.steps[1].rawHex),128));}],
  ['AP-boot-regression',i=>{i.steps.push({op:'rx',rawHex:hex(encode(33,{time_boot_ms:1000},{system:1,component:1,seq:37})),t:20100,meta:meta(20100)});}],
  ['partial-frame-after-ready-expired',i=>{i.steps.push({op:'rx',rawHex:hex(version({seq:37}).slice(0,9)),t:20100,meta:meta(20100)});i.inspectAtMs=21601;}],
 ];for(const[id,fn]of badcases)await add(id,fn,invalid);
 await add('partial-parameters',i=>{i.steps.splice(20,9);},{...good,phase:'READING',inspectionAvailable:false,paramCount:0,policyStatus:'UNKNOWN',failsafeStatus:'UNKNOWN',altitudeState:'UNKNOWN'});
 await add('missing-AP-state',i=>{i.apState=null;},{...good,failsafeStatus:'UNKNOWN'});
 await add('missing-altitude-reference',i=>{i.altitude.home=null;},{...good,altitudeState:'UNKNOWN'});
 await add('unknown-battery-voltage-source',i=>{i.apState.value.battery.voltageSource='OTHER';},{...good,failsafeStatus:'PARTIAL_UNKNOWN'});
 await add('bytewise-protocol-without-Copter-policy',i=>{
  i.contract=contract(TARGET,CLOCK.epoch,{profile:'GENERIC_BYTEWISE_MOCK',encoding:'BYTEWISE',allowLegacy:false});
  i.steps[0].rawHex=hex(version({review:i.contract}));parameters({encoding:'BYTEWISE'}).forEach((p,k)=>i.steps[k+1].rawHex=hex(p.raw));
 },{...good,policyStatus:'UNKNOWN',failsafeStatus:'UNKNOWN',altitudeState:'UNKNOWN'});
 return {format:'aeris-flightadapter39-corpus',version:1,origin:'MOCK_REPLAY',cases,...no};
}
import {crc,DEFINITIONS} from '../mavflight37/wire.mjs';
export function resequence(b,seq){b=b.slice();b[b[0]===253?4:2]=seq;const id=b[0]===253?b[7]+b[8]*256+b[9]*65536:b[5],c=crc(b.subarray(1,-2),id===148?178:DEFINITIONS[id].crc);b[b.length-2]=c&255;b[b.length-1]=c>>8;return b;}
export async function replayCorpus(c){exact(c,['format','version','origin','cases',...Object.keys(no)]);bounded(c,4*2**20);
 if(c.format!=='aeris-flightadapter39-corpus'||c.version!==1||c.origin!=='MOCK_REPLAY'||!same(Object.fromEntries(Object.keys(no).map(k=>[k,c[k]])),no)||!Array.isArray(c.cases)||c.cases.length>64||new Set(c.cases.map(x=>x.id)).size!==c.cases.length)throw Error('corpus scope/bounds');
 const results=[];for(const x of c.cases)results.push(await replayCase(x));
 return {status:results.every(r=>r.matched)?'MOCK_PASS':'FAIL',caseCount:results.length,results,corpusSha256:await digest(c),...no};
}
