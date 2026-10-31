import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {UnionFramer} from './framer.mjs';
import {FlightAdapter39,liveInspection} from './adapter.mjs';
import {dialogue,meta,parameters,version,join} from './fixtures.mjs';
import {sourceHashes,append} from './evidence.mjs';
import {resequence,run} from './corpus.mjs';
import {encode,unhex,hex,crc,DEFINITIONS} from '../mavflight37/wire.mjs';
import {contract} from '../firmware38/contract.mjs';
import {TARGET,CLOCK,ids,profile} from '../apflight36/fixtures.mjs';
import {validateLedger} from '../apflight36/ledger.mjs';
import {replayCorpus as replay36} from '../apflight36/corpus.mjs';
import {replayCorpus as replay37} from '../mavflight37/scenarios.mjs';
import {replayCorpus as replay38} from '../firmware38/corpus.mjs';

const results=[];async function check(name,fn){try{await fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false,error:e.stack});}}
const old=JSON.parse(await readFile('evidence/mavflight37/js-vectors4.json','utf8'));
const fw=JSON.parse(await readFile('evidence/firmware38/js-vectors3.json','utf8'));
let splits=0,vectorCount=0;
for(const [group,vectors]of [['m37',old.vectors],['f38',fw.vectors]])for(const [k,v]of vectors.entries()){
 await check('union oracle/splits '+group+'/'+k,()=>{
  const b=unhex(v.rawHex);const complete=new UnionFramer().push(b,100,100);
  assert.equal(complete.length,1);assert.equal(complete[0].rawHex,v.rawHex);
  if(group==='m37'||v.kind==='VERSION')assert.deepEqual(complete[0].fields,v.expected);
  for(let n=1;n<b.length;n++){const f=new UnionFramer();assert.equal(f.push(b.slice(0,n),100,100).length,0);
   const p=f.push(b.slice(n),120,120);assert.equal(p.length,1);assert.equal(p[0].rawHex,v.rawHex);
   assert.equal(p[0].firstByteAtMs,100);assert.equal(p[0].lastByteAtMs,120);splits++;
  }vectorCount++;
 });
}
const hb=(seq=1,t=0)=>encode(0,{type:2,autopilot:3,base_mode:129,custom_mode:3},{system:1,component:1,seq});
await check('mixed v1/version/v2 preserves exact order',()=>{const v1=encode(0,{}, {system:1,component:1,seq:0,version:1});const b=join([v1,version(),hb()]);const fs=new UnionFramer().push(b,100,100);assert.deepEqual(fs.map(f=>f.rawHex),[hex(v1),hex(version()),hex(hb())]);});
await check('every-byte fragmentation with exact receipt lineage',()=>{const raw=version(),f=new UnionFramer();let seen=[];for(let n=0;n<raw.length;n++)seen.push(...f.push(raw.slice(n,n+1),100+n,100+n));assert.equal(seen.length,1);assert.equal(seen[0].firstByteAtMs,100);assert.equal(seen[0].lastByteAtMs,99+raw.length);});
await check('seeded fragmentation/coalescence exact bytes',()=>{const raws=[version(),...parameters().map(p=>p.raw),hb(29)],stream=join(raws);for(let seed=1;seed<=8;seed++){const f=new UnionFramer();let pos=0,x=seed,out=[];while(pos<stream.length){x=(Math.imul(x,1664525)+1013904223)>>>0;const n=1+x%80;out.push(...f.push(stream.slice(pos,pos+n),100+Math.floor(pos/10),100+Math.floor(pos/10)));pos+=n;}assert.deepEqual(out.map(p=>p.rawHex),raws.map(hex));assert.equal(f.snapshot().pendingBytes,0);}});
await check('noise tolerated with disclosed bounded count',()=>{const f=new UnionFramer();assert.equal(f.push(join([Uint8Array.of(1,2,3),version()]),100,100).length,1);assert.equal(f.snapshot().noiseBytes,3);});
await check('noise bound closes framer',()=>{const f=new UnionFramer();assert.throws(()=>f.push(new Uint8Array(65),100,100),/NOISE_BOUND/);assert.equal(f.snapshot().closed,true);});
await check('chunk bound rejects before allocation',()=>assert.throws(()=>new UnionFramer().push(new Uint8Array(4097),100,100),/CHUNK_BOUND/));
await check('empty chunk cannot refresh receipt',()=>assert.throws(()=>new UnionFramer().push(new Uint8Array(),100,100),/CHUNK_BOUND/));
await check('CRC error cannot hide later firmware announcement',()=>{const bad=hb();bad[bad.length-1]^=1;const f=new UnionFramer();assert.throws(()=>f.push(join([bad,version()]),100,100),/FRAME_CRC/);assert.equal(f.snapshot().closed,true);});
for(const flag of [1,2,3])await check('incompatibility flag '+flag,()=>{const b=version();b[2]=flag;const f=new UnionFramer();assert.throws(()=>f.push(b.slice(0,10),100,100),/SIGNED_OR_INCOMPATIBLE_FRAME/);});
await check('unknown id cannot silently swallow version',()=>{const b=hb();b[7]=200;assert.throws(()=>new UnionFramer().push(join([b,version()]),100,100),/MESSAGE_OUTSIDE/);});
await check('v1 version148 deliberately unsupported',()=>assert.throws(()=>new UnionFramer().push(Uint8Array.of(254,60,0,1,1,148),100,100),/MESSAGE_OUTSIDE/));
await check('v1 invalid length rejected before payload',()=>assert.throws(()=>new UnionFramer().push(Uint8Array.of(254,8,0,1,1,0),100,100),/PAYLOAD_LENGTH/));
await check('zero sender rejected',()=>{const b=version();b[5]=0;assert.throws(()=>new UnionFramer().push(b,100,100),/FRAME_SENDER_ZERO/);});
await check('partial header expires without another packet',()=>{const f=new UnionFramer();f.push(version().slice(0,3),100,100);assert.throws(()=>f.tick(1601),/PARTIAL_FRAME_STALE/);});
await check('first-byte freshness boundary inclusive',()=>{const f=new UnionFramer(),b=version();f.push(b.slice(0,5),100,100);assert.equal(f.push(b.slice(5),1600,1600)[0].firstByteAtMs,100);});
await check('first-byte age cannot borrow final fragment',()=>{const f=new UnionFramer(),b=version();f.push(b.slice(0,5),100,100);assert.throws(()=>f.push(b.slice(5),1601,1601),/PARTIAL_FRAME_STALE/);});
await check('batch frame cap blocks entire result',()=>assert.throws(()=>new UnionFramer().push(join(Array(65).fill(hb())),100,100),/BATCH_FRAME_BOUND/));

async function full(options={}){const i=await dialogue(),a=new FlightAdapter39(i.contract,{idFactory:ids(),...options}),outputs=[];
 for(const s of i.steps)outputs.push(...await a.receive(unhex(s.rawHex),s.meta,s.t));return {a,i,outputs};}
await check('typed read full mock and readonly output whitelist',async()=>{const {a,outputs}=await full();assert.equal(outputs.length,28);for(const p of outputs){assert.equal(p.id,20);assert.equal(p.networkSent,false);const f=new UnionFramer().push(unhex(p.rawHex),100,100)[0];assert.equal(f.fields.target_system,1);assert.equal(f.fields.param_index,-1);}const p=a.proof(20120);assert.equal(Object.keys(p.typedReadback.values).length,28);assert.equal(p.flightAuthority,false);assert.equal(liveInspection(p,20120),true);});
await check('serialized/tampered proof cannot restore authority',async()=>{const{a}=await full(),p=a.proof(20120);assert.equal(liveInspection(structuredClone(p),20120),false);p.typedReadback.values.FENCE_ENABLE.value=0;assert.equal(liveInspection(p,20120),false);assert.equal(a.proof(20120).typedReadback.values.FENCE_ENABLE.value,1);});
await check('snapshot cannot construct resumed reader',async()=>{const{a,i}=await full(),s=a.snapshot(20120);assert.throws(()=>new FlightAdapter39(s));const fresh=new FlightAdapter39(i.contract);assert.equal(fresh.snapshot(20120).inspectionAvailable,false);assert.throws(()=>fresh.proof(20120));});
for(const [name,action]of [['disconnect',a=>a.disconnect()],['owner',a=>a.loseOwner()],['focus',a=>a.loseOwner('FOCUS_LOST')],['stale',a=>a.tick(22000)]])await check('all proofs revoked '+name,async()=>{const{a}=await full(),p=a.proof(20120);action(a);assert.equal(liveInspection(p,20120),false);assert.throws(()=>a.proof(20120));await assert.rejects(a.receive(hb(37),meta(20121),20121));});
await check('contract caller mutation cannot change reviewed identity',async()=>{const i=await dialogue(),a=new FlightAdapter39(i.contract);i.contract.expected.uid='999';assert.equal((await a.receive(version(),meta(20000),20000)).length,1);});
await check('boot clock wrap distinct from regression',async()=>{const i=await dialogue(),a=new FlightAdapter39(i.contract);await a.receive(version(),meta(20000),20000);for(const[seq,t]of [[1,4294967290],[2,10]])await a.receive(encode(33,{time_boot_ms:t},{system:1,component:1,seq}),meta(20001+seq),20001+seq);assert.equal(a.snapshot(20004).phase,'READING');});
await check('receipt domain monotonic independent AP milliseconds',async()=>{const{a}=await full();await assert.rejects(a.receive(hb(37),meta(19000),20120),/CONTEXT_RECEIPT_CLOCK/);assert.equal(a.snapshot(20120).phase,'INVALIDATED');});
await check('writer may not mutate internal rows',async()=>{const{a}=await full({persist:async e=>{e.rows[0].kind='EXTERNAL_MUTATION';}});await validateLedger(a.audit().session);await validateLedger(a.audit().parameters);assert.notEqual(a.audit().session[0].kind,'EXTERNAL_MUTATION');});
await check('intent persisted before first mock buffer',async()=>{const commits=[],i=await dialogue(),a=new FlightAdapter39(i.contract,{idFactory:ids(),persist:async e=>commits.push(e)});const out=await a.receive(version(),meta(20000),20000);assert.equal(commits.at(-1).stream,'PARAMETERS38');assert.equal(commits.at(-1).rows[0].kind,'READONLY_NAMED_READ_INTENT');assert.equal(out.length,1);});
for(const mode of ['disconnect','concurrent','inspect'])await check('revoke during journal await '+mode,async()=>{
 let release,entered;const pending=new Promise(r=>entered=r),wait=new Promise(r=>release=r);const i=await dialogue();const a=new FlightAdapter39(i.contract,{persist:async e=>{if(e.stream==='PARAMETERS38'){entered();await wait;}}});
 const rx=a.receive(version(),meta(20000),20000);await pending;
 if(mode==='disconnect')a.disconnect();else if(mode==='concurrent')await assert.rejects(a.receive(hb(),meta(20001),20001),/CONCURRENT_RECEIVE/);
 else await assert.rejects(a.inspect(i.profile,20000),/INSPECTION_DURING_WRITE/);
 release();await assert.rejects(rx);assert.equal(a.snapshot(20001).phase,'INVALIDATED');assert.throws(()=>a.proof(20001));
});
await check('revoke on later frame discards whole coalesced output',async()=>{const i=await dialogue(),a=new FlightAdapter39(i.contract),v=version({seq:1,fields:{board_version:39}});await assert.rejects(a.receive(join([version(),v]),meta(20000),20000),/FIRMWARE_ANNOUNCEMENT_CHANGED/);assert.equal(a.snapshot(20000).inspectionAvailable,false);});
for(const seq of [36,0])await check('quarantined version conflict revokes issued witness '+seq,async()=>{const{a}=await full(),p=a.proof(20100);await assert.rejects(a.receive(version({seq,fields:{board_version:39}}),meta(20101),20101),/QUARANTINED_FIRMWARE_CONFLICT/);assert.equal(liveInspection(p,20101),false);});
for(const seq of [36,1])await check('quarantined parameter conflict revokes issued witness '+seq,async()=>{const{a}=await full(),p=a.proof(20100);await assert.rejects(a.receive(parameters({firstSeq:seq,values:{FENCE_ENABLE:0}})[0].raw,meta(20101),20101),/QUARANTINED_PARAMETER_CONFLICT/);assert.equal(liveInspection(p,20101),false);});
await check('late same announcement stays quarantined without renewal',async()=>{const{a}=await full();assert.equal((await a.receive(version(),meta(21400),21400)).length,0);assert.equal(a.tick(21501),false);});
await check('firmware split first receipt preserved in proof',async()=>{const i=await dialogue(),a=new FlightAdapter39(i.contract),v=version();await a.receive(v.slice(0,15),meta(20000),20000);await a.receive(v.slice(15),meta(20100),20100);assert.equal(a.snapshot(21500).phase,'READING');assert.equal(a.tick(21501),false);});
await check('missing lower-layer witnesses cannot become READY preflight',async()=>{const{a,i}=await full(),r=await a.inspect(i.profile,20120,{apState:i.apState,altitude:i.altitude});assert.equal(r.preflight.assessment.state,'UNKNOWN');assert.equal(r.policy.status,'MAPPED_MOCK');assert.equal(r.policy.battery.remainingWh,null);assert.equal(r.normalizedPolicyEquivalent,false);assert.equal(r.geofenceUploadReadbackProven,false);assert.equal(r.flightAuthority,false);});
await check('missing AP state never inferred from telemetry',async()=>{const{a,i}=await full(),r=await a.inspect(i.profile,20120);assert.equal(r.failsafe.status,'UNKNOWN');assert.equal(r.altitude.state,'UNKNOWN');});
await check('generic bytewise profile cannot inherit Copter telemetry interpretation',async()=>{const i=await dialogue();i.contract=contract(TARGET,CLOCK.epoch,{profile:'GENERIC_BYTEWISE_MOCK',encoding:'BYTEWISE',allowLegacy:false});const a=new FlightAdapter39(i.contract,{idFactory:ids()});await a.receive(version({review:i.contract}),meta(20000),20000);for(const p of parameters({encoding:'BYTEWISE'}))await a.receive(p.raw,meta(p.t),p.t);const r=await a.inspect(i.profile,20120,{apState:i.apState});assert.equal(r.preflight.raw,null);assert.equal(r.policy.status,'UNKNOWN');assert.equal(r.failsafe.status,'UNKNOWN');assert.equal(a.snapshot(20120).inspectionAvailable,true);});
await check('ACK and fence status remain observations',async()=>{const{a,i}=await full();await a.receive(encode(77,{command:400,result:0,target_system:255,target_component:190},{system:1,component:1,seq:37}),meta(20100),20100);await a.receive(encode(162,{breach_status:1,breach_count:1,breach_time:20000,breach_type:3},{system:1,component:1,seq:38}),meta(20101),20101);const r=await a.inspect(i.profile,20120);assert.equal(r.preflight.raw.commandAck.executionProven,false);assert.equal(r.preflight.raw.fenceBreach.physicalExecutionProven,false);assert.equal(r.executionProven,false);});
await check('context mismatched AP-side state remains UNKNOWN',async()=>{const{a,i}=await full();i.apState.target.boot='other';const r=await a.inspect(i.profile,20120,{apState:i.apState});assert.equal(r.failsafe.status,'UNKNOWN');});
await check('journal storage error after first output revokes',async()=>{let n=0;const i=await dialogue(),a=new FlightAdapter39(i.contract,{persist:async e=>{if(e.stream==='PARAMETERS38'&&++n===2)throw Error('DISK_FAULT');}});assert.equal((await a.receive(version(),meta(20000),20000)).length,1);await assert.rejects(a.receive(parameters()[0].raw,meta(20002),20002));assert.equal(a.snapshot(20002).inspectionAvailable,false);});
await check('bounded repeated packets close session with evidence retained',async()=>{const i=await dialogue(),a=new FlightAdapter39(i.contract);await a.receive(version(),meta(20000),20000);let rejected=false;for(let k=0;k<260;k++)try{await a.receive(hb(1),meta(20001),20001);}catch{rejected=true;break;}assert.equal(rejected,true);assert.ok(a.audit().session.length<=256);assert.equal(a.snapshot(20001).phase,'INVALIDATED');});

const regressions={};for(const[name,fn,cp,rp]of [['apflight36',replay36,'evidence/apflight36/corpus6.json','evidence/apflight36/replay6.json'],['mavflight37',replay37,'evidence/mavflight37/corpus4.json','evidence/mavflight37/replay4.json'],['firmware38',replay38,'evidence/firmware38/corpus4.json','evidence/firmware38/replay4.json']])await check('old exact corpus '+name,async()=>{const c=JSON.parse(await readFile(cp,'utf8')),receipt=JSON.parse(await readFile(rp,'utf8'));const actual=await fn(c);assert.deepEqual(actual,receipt.replay);regressions[name]={cases:actual.caseCount,status:actual.status};});
const report={at:new Date().toISOString(),status:results.every(r=>r.pass)?'MOCK_PASS':'FAIL',checkCount:results.length,passed:results.filter(r=>r.pass).length,results,
 oracleVectors:vectorCount,splitPositions:splits,regressions,sourceHashes:await sourceHashes(),networkSent:false,newRuntime_Signature:false};
const path=await append('logic',report);console.log(JSON.stringify({path,status:report.status,checks:report.checkCount,passed:report.passed,oracleVectors:vectorCount,splitPositions:splits,failures:results.filter(r=>!r.pass).map(r=>({name:r.name,error:r.error.split('\n')[0]}))}));if(report.status==='FAIL')process.exitCode=1;
