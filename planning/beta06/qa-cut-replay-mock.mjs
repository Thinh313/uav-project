import{evaluateCut,exactChain}from'./qa-cut-replay.mjs';import assert from'node:assert/strict';import fs from'node:fs/promises';import{createHash}from'node:crypto';
const run='s'+'1'.repeat(20),sha=b=>createHash('sha256').update(b).digest('hex');
function fixture(){
 const client={clientId:'client',clientEpoch:3,clientInstance:'instance'},identity={...client,stationId:'station',payloadId:'mockRGB',flightRun:run,flightBoot:'boot',modelSha256:'a'.repeat(64),planSha256:'b'.repeat(64)},lease={...identity,untilHostMonoMs:20000},q={run,boot:'boot',modelSha256:identity.modelSha256,planSha256:identity.planSha256,...client,confirmSimulation:true};
 const raw=[{n:1,hostNs:'12000000000',kind:'FIELD01_INTENT',data:{route:'cut',request:q}},{n:2,kind:'FIELD02_CLIENT_AUTHORITY_REVOKED',data:{reason:'FAULT_CUT',authorityRestored:false}},{n:3,kind:'FIELD02_C2_SOCKET_CUT',data:{actualTCPDisconnect:true,noReconnect:true}},{n:4,kind:'FIELD01_FAULT',data:{route:'cut',notFlightCompletion:true}},{n:5,kind:'FIELD01_CLOSING',data:{aborted:true,observed:{transport:'disconnected',armed:null,mode:null,position:null,attitude:null,completion:{complete:false}}}}];
 const wal=[{seq:1,hash:'1'.repeat(64),kind:'PAYLOAD_LEASE_OBSERVED',data:{...lease,gatewaySession:'gateway',hostMonoMs:8000}},{seq:2,hash:'2'.repeat(64),kind:'PAYLOAD_AUTHORITY_INVALIDATED',data:{reason:'FLIGHT_CUT',hostMonoMs:10100,pre:{authorityRestored:false,flightRun:run,flightBoot:'boot',modelSha256:identity.modelSha256,planSha256:identity.planSha256,gatewaySession:'gateway',client,observedAtHostMonoMs:10000,leases:[lease]},post:{authorityRestored:false,leaseCount:0,leases:[],observedAtHostMonoMs:10200}}}];
 return{run,raw,wal,review:{run,mode:'sitl',accepted:false,aborted:true,execution:{complete:false},authorityRestorable:false}};
}
const rows=[];function test(name,f){try{f();rows.push({name,status:'PASS'});}catch(e){rows.push({name,status:'FAIL',error:e.message});}}
test('strict_positive_synthetic_fixture_only',()=>assert.equal(evaluateCut(fixture()).liveLeaseProofs[0].unexpiredRemainingAtPreMs,10000));
for(const [name,mutate]of[
 ['lease_under_5s',x=>x.wal[1].data.pre.leases[0].untilHostMonoMs=14999],
 ['wrong_client_instance',x=>x.wal[1].data.pre.client.clientInstance='wrong'],
 ['old_grant_wrong_payload',x=>x.wal[0].data.payloadId='wrong'],
 ['clear_after_fault_intent',x=>x.wal[1].data.post.observedAtHostMonoMs=12001],
 ['actual_socket_cut_false',x=>x.raw[2].data.actualTCPDisconnect=false],
 ['reconnected_wire',x=>x.raw.push({n:6,kind:'RX_RAW',data:{}})],
 ['postcut_armed_false_still_wrong_known_value',x=>x.raw[4].data.observed.armed=false],
 ['later_lease_regained',x=>x.wal.push({seq:3,kind:'PAYLOAD_LEASE_OBSERVED',data:{flightRun:run}})],
 ['later_old_command_intent',x=>x.wal.push({seq:3,kind:'PAYLOAD_COMMAND_INTENT',data:{flightRun:run}})],
 ['mission_accepted_invalid',x=>x.review.accepted=true],
 ['wrong_boot',x=>x.raw[0].data.request.boot='other'],
 ['missing_durable_grant',x=>x.wal.shift()],
])test(name,()=>{const f=fixture();mutate(f);assert.throws(()=>evaluateCut(f));});
test('exact_raw_chain_tamper_and_torn_reject',()=>{const b=JSON.stringify({at:'fixture',data:{},hostNs:'1',kind:'A',n:1,previous:''});const bytes=Buffer.from(b.slice(0,-1)+',"sha256":"'+sha(b)+'"}\n');assert.equal(exactChain(bytes,'raw').rows.length,1);assert.throws(()=>exactChain(Buffer.from(bytes.toString().replace('fixture','tamper')),'raw'));assert.throws(()=>exactChain(bytes.subarray(0,-1),'raw'));});
const result={at:new Date().toISOString(),status:rows.every(r=>r.status==='PASS')?'PASS_F1_REPLAYER_SYNTHETIC_ADVERSARIAL_ONLY':'FAIL',sources:{'planning/beta06/qa-cut-replay.mjs':sha(await fs.readFile('planning/beta06/qa-cut-replay.mjs'))},rows,scope:'Synthetic evaluator/chain fixtures only. No actual BETA06 cut, socket, AP, lease or native test was performed.'};await fs.writeFile('evidence/beta06/qa-cut-replayer-mock01.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:result.status,groups:rows.length,failures:rows.filter(r=>r.status==='FAIL')}));if(result.status==='FAIL')process.exitCode=1;
