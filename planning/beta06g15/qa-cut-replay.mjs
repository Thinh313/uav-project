import{writeProof}from'../../pilot/beta06g15/proof-writer.mjs';
/** Independent read-only F1 evaluator. No bearer token, command, socket or process operations. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const sha=b=>createHash('sha256').update(b).digest('hex');
export function exactChain(bytes,style){
 assert(bytes.length<=96*2**20,'INPUT_BOUND');const s=bytes.toString();assert(s.endsWith('\n'),'TORN_JOURNAL');
 const lines=s.trimEnd().split('\n'),rows=lines.map(JSON.parse);let head=style==='wal'?'0'.repeat(64):'';
 for(let i=0;i<rows.length;i++){const r=rows[i];if(style==='wal'){const{hash,...body}=r;assert.equal(r.seq,i+1);assert.equal(r.previousHash,head);assert.equal(sha(JSON.stringify(body)),hash);head=hash;}else{assert.equal(r.n,i+1);assert.equal(r.previous,head);assert.equal(sha(lines[i].replace(/,"sha256":"[a-f0-9]{64}"}$/,'}')),r.sha256);head=r.sha256;}}
 return{rows,head};
}
const ms=r=>Number(BigInt(r.hostNs))/1e6;
const identityKeys=['stationId','clientId','clientEpoch','clientInstance','payloadId','flightRun','flightBoot','modelSha256','planSha256'];
export function evaluateCut({run,wal,raw,review}){
 assert.equal(review.run,run);assert.equal(review.mode,'sitl');assert.equal(review.accepted,false);assert.equal(review.aborted,true);assert.equal(review.execution.complete,false);assert.equal(review.authorityRestorable,false);
 const intents=raw.filter(r=>r.kind==='FIELD01_INTENT'&&r.data.route==='cut');assert.equal(intents.length,1,'ONE_CUT_INTENT');const intent=intents[0],q=intent.data.request;
 assert.equal(q.run,run);assert.equal(q.confirmSimulation,true);
 const cuts=raw.filter(r=>r.kind==='FIELD02_C2_SOCKET_CUT');assert.equal(cuts.length,1);const cut=cuts[0];assert(cut.n>intent.n);assert.equal(cut.data.actualTCPDisconnect,true);assert.equal(cut.data.noReconnect,true);
 const revoked=raw.find(r=>r.kind==='FIELD02_CLIENT_AUTHORITY_REVOKED'&&r.n>intent.n&&r.n<cut.n);assert(revoked);assert.equal(revoked.data.reason,'FAULT_CUT');assert.equal(revoked.data.authorityRestored,false);
 const fault=raw.find(r=>r.kind==='FIELD01_FAULT'&&r.data.route==='cut'&&r.n>cut.n);assert(fault);assert.equal(fault.data.notFlightCompletion,true);
 const closing=raw.find(r=>r.kind==='FIELD01_CLOSING'&&r.n>cut.n);assert(closing);assert.equal(closing.data.aborted,true);const o=closing.data.observed;
 assert.equal(o.transport,'disconnected');for(const k of ['armed','mode','position','attitude'])assert.equal(o[k],null,'POST_CUT_UNKNOWN_'+k);assert.equal(o.completion.complete,false);
 const afterWire=raw.filter(r=>r.n>cut.n&&['TX_RAW','RX_RAW','SESSION'].includes(r.kind));assert.equal(afterWire.length,0,'NO_RECONNECT_OR_AFTER_CUT_WIRE');
 const invs=wal.filter(r=>r.kind==='PAYLOAD_AUTHORITY_INVALIDATED'&&r.data.reason==='FLIGHT_CUT'&&r.data.pre?.flightRun===run);assert.equal(invs.length,1,'ONE_DURABLE_FLIGHT_CUT_CLEAR');
 const r=invs[0],d=r.data,pre=d.pre,post=d.post;assert.equal(pre.authorityRestored,false);assert.equal(post.authorityRestored,false);assert.equal(post.leaseCount,0);assert.deepEqual(post.leases,[]);assert.equal(pre.flightBoot,q.boot);assert.equal(pre.modelSha256,q.modelSha256);assert.equal(pre.planSha256,q.planSha256);
 for(const k of ['clientId','clientEpoch','clientInstance'])assert.equal(pre.client[k],q[k]);
 assert(pre.observedAtHostMonoMs<=d.hostMonoMs&&d.hostMonoMs<=post.observedAtHostMonoMs);assert(post.observedAtHostMonoMs<=ms(intent),'CLEAR_OBSERVATION_PRECEDES_RAW_INTENT_NODE_DOMAIN');
 const leases=pre.leases.filter(l=>l.flightRun===run&&l.untilHostMonoMs-pre.observedAtHostMonoMs>=5000);assert(leases.length,'EXACT_LIVE_LEASE_5S_REQUIRED');
 const proof=leases.map(l=>{for(const k of ['clientId','clientEpoch','clientInstance'])assert.equal(l[k],pre.client[k]);assert.equal(l.flightBoot,pre.flightBoot);assert.equal(l.modelSha256,pre.modelSha256);assert.equal(l.planSha256,pre.planSha256);
  const grant=wal.filter(x=>x.kind==='PAYLOAD_LEASE_OBSERVED'&&x.seq<r.seq&&identityKeys.every(k=>x.data[k]===l[k])&&x.data.gatewaySession===pre.gatewaySession).at(-1);assert(grant,'EXACT_DURABLE_GRANT');assert.equal(grant.data.untilHostMonoMs,l.untilHostMonoMs);assert(grant.data.hostMonoMs<=pre.observedAtHostMonoMs);
  return{grantSeq:grant.seq,grantHash:grant.hash,identity:Object.fromEntries(identityKeys.map(k=>[k,l[k]])),unexpiredRemainingAtPreMs:l.untilHostMonoMs-pre.observedAtHostMonoMs};});
 const after=wal.filter(x=>x.seq>r.seq);const regained=after.filter(x=>x.kind==='PAYLOAD_LEASE_OBSERVED'&&x.data.flightRun===run);assert.equal(regained.length,0,'NO_AUTHORITY_REGAIN_AFTER_CUT');
 const commandCandidates=after.filter(x=>x.kind==='PAYLOAD_COMMAND_INTENT'&&JSON.stringify(x.data).includes(run));assert.equal(commandCandidates.length,0,'NO_LATER_OLD_RUN_COMMAND_INTENT');
 return{cutIntentRecord:intent.n,socketCutRecord:cut.n,clientRevokedRecord:revoked.n,closingRecord:closing.n,clearSeq:r.seq,clearHash:r.hash,preObservedAtHostMonoMs:pre.observedAtHostMonoMs,clearObservedAtHostMonoMs:d.hostMonoMs,postObservedAtHostMonoMs:post.observedAtHostMonoMs,rawFaultIntentHostMonoMs:ms(intent),liveLeaseProofs:proof,postCutTelemetry:'DISCONNECTED_AND_UNKNOWN',afterCutWireRecords:0,laterLeaseRegains:0,laterOldRunCommandIntents:0,flightConclusion:{accepted:false,aborted:true,executionComplete:false}};
}
async function main(){
 const[run,walPath,out]=process.argv.slice(2);assert(/^s[a-f0-9]{20}$/.test(run??''));assert(/^evidence\/beta06\/generation15\/[a-zA-Z0-9_./-]+\.jsonl$/.test(walPath??'')&&!walPath.includes('..'));assert(/^evidence\/beta06\/generation15\/qa[-a-zA-Z0-9_/]+\.json$/.test(out??'')&&!out.includes('..'));
 const dir=path.join('evidence/beta06/generation15/flight/runs',run),files={};for(const n of ['raw.jsonl','review.json','request.json','closure.json'])files[n]=await fs.readFile(path.join(dir,n));const w=await fs.readFile(walPath),errors=[];let checks=null,raw,wal;
 try{raw=exactChain(files['raw.jsonl'],'raw');wal=exactChain(w,'wal');const review=JSON.parse(files['review.json']),request=JSON.parse(files['request.json']);assert.equal(request.mode,'sitl');assert.equal(request.run,run);assert.equal(review.rawHead,raw.head);assert.equal(review.rawRecords,raw.rows.length);for(const n of ['raw.jsonl','request.json','closure.json'])assert.equal(review.filesSha256[n],sha(files[n]));checks=evaluateCut({run,raw:raw.rows,wal:wal.rows,review});}catch(e){errors.push({message:e.message,stack:e.stack});}
 const result={at:new Date().toISOString(),status:errors.length?'FAIL_INDEPENDENT_F1_REPLAY':'PASS_ACTUAL_TCP_CUT_DURABLE_LIVE_LEASE_INVALIDATION_INCOMPLETE_FLIGHT',run,input:{...Object.fromEntries(Object.entries(files).map(([n,b])=>[n,{bytes:b.length,sha256:sha(b)}])),wal:{path:walPath,bytes:w.length,sha256:sha(w)}},checks,errors,clockBasis:'Only Node hrtime hostNs and corresponding Node payload-observation monotonic timestamps are ordered. Python/guest/UTC clocks are not numerically combined.',durabilityBasis:'Exact persisted hash-chain receipt precedes raw fault intent; frozen source awaits payload.settled before flight.action. Observation timestamps do not independently measure fsync completion.',oldContextProbe:'NOT_CHECKED_BY_THIS_REPLAYER. Require separate actual correlated server-negative acknowledgement, identify exact guard hit; transport errors/unknown receipts never count as refusal.',scope:'Owned localhost SITL TCP socket destruction with synthetic payload authority only. No physical link failure, post-cut trajectory/RTL/landing, hardware failsafe, AP reboot, new MAVLink boot or mission completion inferred.'};await writeProof(out,result,{kind:'fault'});console.log(JSON.stringify({status:result.status,errors:errors.map(x=>x.message)}));if(errors.length)process.exitCode=1;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)await main();
