/** Delegated HTTP QA of root-authored FIELD01 app, own ports/evidence only.
 * Actual app/compiler/store/HTTP; direct synthetic storage seeds are explicitly test fixtures.
 * No flight command, SITL, Android, browser/CUA, network download or existing workspace.
 */
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import http from 'node:http';
import { join,resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID,createHash } from 'node:crypto';
import { createField01 } from '../../pilot/field01/app.mjs';
import { fixture } from '../../pilot/field01/evidence/fixtures.mjs';
import { default92,edit92,document92,sha92,validateDocument92 } from '../../pilot/field01/.stage/assets/mission92.mjs';
import { inspect94 } from '../../pilot/field01/.stage/assets/offline94.mjs';
const repo=resolve(fileURLToPath(new URL('../..',import.meta.url))),stamp=new Date().toISOString().replace(/[:.]/g,'-');
const out=join(repo,'evidence/field01',`evidence-app-http-tests-${stamp}`);await fs.mkdir(out,{recursive:true});
const origin='http://127.0.0.1:8890',results=[];let app,csrf,head,model,uncompiled,compiledDocument,seedCapture;
const hash=v=>createHash('sha256').update(v).digest('hex');
async function test(name,fn){const at=performance.now();try{const detail=await fn();results.push({name,status:'PASS',elapsedMs:performance.now()-at,...detail});}
  catch(e){results.push({name,status:'FAIL',elapsedMs:performance.now()-at,error:e.stack});}}
async function exists(path){try{await fs.lstat(path);return true;}catch(e){if(e.code==='ENOENT')return false;throw e;}}
async function request(path,{method='GET',value,raw,headers={}}={}){
  if(headers.Host){return new Promise((yes,no)=>{const req=http.request({hostname:'127.0.0.1',port:8890,path,method,headers},res=>{
    const chunks=[];res.on('data',b=>chunks.push(b));res.on('end',()=>{const bytes=Buffer.concat(chunks),type=res.headers['content-type'];
      yes({status:res.statusCode,type,bytes,body:type==='application/json'?JSON.parse(bytes):null});});});req.on('error',no);req.end();});}
  const response=await fetch(origin+path,{method,headers:{...(method==='POST'?{'Origin':origin,'X-Field-Csrf':csrf,'Content-Type':'application/json'}:{}),...headers},
    ...(method==='POST'?{body:raw??JSON.stringify(value??{})}:{}),signal:AbortSignal.timeout(10000)});
  const bytes=Buffer.from(await response.arrayBuffer()),type=response.headers.get('content-type');
  return {status:response.status,type,bytes,body:type==='application/json'?JSON.parse(bytes):null};
}
function rejection(r,pattern){assert.equal(r.status,409);assert.equal(r.body.ok,false);assert.equal(r.body.automaticRetry,false);if(pattern)assert.match(r.body.error,pattern);}
async function getState(){const r=await request('/api/state');assert.equal(r.status,200);assert.equal(r.body.ok,true);return r.body;}
async function save(document,expected=head){return request('/api/native82',{method:'POST',value:{action:'save',expected,body:JSON.stringify(document)}});}
const delay=ms=>new Promise(r=>setTimeout(r,ms));

// An intentional owned bind collision probes startup rollback without touching the live app.
await test('startup port collision rolls back owned media listener and writer lock automatically',async()=>{
  const blocker=http.createServer((_,res)=>res.end('OWNED_TEST_BLOCKER'));await new Promise((yes,no)=>{blocker.once('error',no);blocker.listen(8890,'127.0.0.1',yes);});
  let candidate;const root=join(out,'startup-collision');
  try{candidate=await createField01({out:root,port:8890,mediaPort:8891,allowSITL:false});
    await assert.rejects(candidate.listen(),/EADDRINUSE/);
    const observations={mediaStillListening:candidate.media.server.listening,writerLockRetained:await exists(join(root,'workspace/writer.lock'))};
    await fs.writeFile(join(out,'startup-collision-observation.json'),JSON.stringify(observations,null,2));
    assert.equal(observations.mediaStillListening,false,'failed app startup must close its owned media listener');
    assert.equal(observations.writerLockRetained,false,'failed app startup must release its own writer lock');
  }finally{await candidate?.close('HTTP_QA_OWNED_STARTUP_FAILURE_CLEANUP');await new Promise(r=>blocker.close(r));}
});

try {
  app=await createField01({out:join(out,'nominal'),port:8890,mediaPort:8891,allowSITL:false});await app.listen();
  await test('bootstrap exposes explicit host/synthetic scope and exact origin',async()=>{
    const r=await request('/api/bootstrap');assert.equal(r.status,200);assert.equal(r.body.simulationOnly,true);assert.equal(r.body.allowSITL,false);
    assert.equal(r.body.authorityRestored,false);assert.equal(r.body.mediaOrigin,'http://127.0.0.1:8891');assert.match(r.body.csrf,/^[a-f0-9]{48}$/);csrf=r.body.csrf;
    const s=await getState();assert.equal(s.store.authority,'NONE');assert.equal(s.authorityRestored,false);assert.equal(s.workspace.token,'ROOT');head='ROOT';
  });
  await test('wrong origin/host and missing/wrong CSRF cannot mutate or disclose bootstrap',async()=>{
    rejection(await request('/api/bootstrap',{headers:{Origin:'http://evil.invalid'}}),/HOST_ORIGIN/);
    rejection(await request('/api/bootstrap',{headers:{Host:'localhost:8890'}}),/HOST_ORIGIN/);
    for(const headers of [{Origin:'http://evil.invalid'},{Origin:''},{'X-Field-Csrf':''},{'X-Field-Csrf':'bad'},{'Content-Type':'text/plain'}]){
      rejection(await request('/api/join',{method:'POST',headers,value:{}}));
    }
    assert.equal(app.payload.stations.size,0);assert.equal((await getState()).workspace.token,'ROOT');
  });
  await test('malformed/oversized JSON bodies and unsupported routes preserve state; service remains responsive',async()=>{
    rejection(await request('/api/join',{method:'POST',raw:'{'}));
    rejection(await request('/api/join',{method:'POST',raw:'null'}));
    rejection(await request('/api/not-a-route',{method:'POST',value:{}}),/ROUTE_ALLOWLIST/);
    let oversize;
    try{const r=await request('/api/join',{method:'POST',raw:JSON.stringify({padding:'x'.repeat(1200001)})});rejection(r,/BODY_BOUND/);oversize='HTTP_409';}
    catch(e){assert(/fetch failed|socket|aborted|terminated/i.test(e.message),e.message);oversize='CONNECTION_CLOSED';}
    assert.equal((await getState()).workspace.token,'ROOT');assert.equal(app.payload.stations.size,0);return {oversizeDisposition:oversize};
  });
  await test('fresh polygon model saved with CAS, compile binds exact committed model and stale head is refused',async()=>{
    model=await default92('polygon');const i=await inspect94(model);model=await edit92(model,{featureId:i.document.features[0].id,
      options:{...model.draft.options,datumAcknowledged:true}});uncompiled=document92(model);
    rejection(await request('/api/compile',{method:'POST',value:{expected:'ROOT',document:uncompiled}}),/COMPILE_SAVED_MODEL_REQUIRED/);
    const saved=await save(uncompiled);assert.equal(saved.status,200);head=saved.body.result.token;assert.match(head,/^[a-f0-9]{64}$/);
    rejection(await save(uncompiled,'ROOT'),/WORKSPACE_CAS/);
    rejection(await request('/api/compile',{method:'POST',value:{expected:'ROOT',document:uncompiled}}),/COMMITTED_IDLE_WORKSPACE_REQUIRED/);
    const other=structuredClone(uncompiled);other.mission=await edit92(model,{name:'Different saved model'});
    rejection(await request('/api/compile',{method:'POST',value:{expected:head,document:other}}),/COMPILE_SAVED_MODEL_REQUIRED/);
    const compiled=await request('/api/compile',{method:'POST',value:{expected:head,document:uncompiled}});assert.equal(compiled.status,200);
    assert.equal(compiled.body.result.compiled.modelSha256,model.sha256);assert.equal(compiled.body.result.compiled.modelRevision,model.revision);
    compiledDocument=document92(model,compiled.body.result.compiled);const final=await save(compiledDocument);assert.equal(final.status,200);
    assert.notEqual(final.body.result.token,head);head=final.body.result.token;
    const loaded=await request('/api/native82',{method:'POST',value:{action:'load'}});assert.equal(loaded.status,200);
    assert.equal(loaded.body.result.token,head);assert.deepEqual(JSON.parse(Buffer.from(loaded.body.result.bodyBase64,'base64')),compiledDocument);
    assert.equal((await getState()).store.recordCount,2);
    await fs.writeFile(join(out,'compiled-workspace.json'),JSON.stringify(compiledDocument,null,2));
    return {modelSha256:model.sha256,planSha256:compiledDocument.compiled.plan.sha256,workspaceHead:head};
  });
  await test('tampered and integrity-valid divergent compiled plans are refused without changing committed head',async()=>{
    const badHash=structuredClone(compiledDocument);badHash.compiled.plan.sha256='0'.repeat(64);
    rejection(await save(badHash),/COMPILE92_PLAN_SHA/);assert.equal((await getState()).workspace.token,head);
    const altered=structuredClone(compiledDocument);altered.compiled.plan.compiled.items[0].param1+=1;
    altered.compiled.plan.missionSha256=await sha92(altered.compiled.plan.compiled.items);
    const {sha256,...base}=altered.compiled.plan;altered.compiled.plan.sha256=await sha92(base);
    await validateDocument92(altered);rejection(await save(altered),/LOCAL_COMPILE_REPLAY_MISMATCH/);
    assert.equal((await getState()).workspace.token,head);assert.equal(app.store.records().filter(r=>r.kind==='WORKSPACE_SAVED').length,2);
    const badDatum=structuredClone(uncompiled);badDatum.mission.draft.altitudeDatum='WGS84_ELLIPSOID';
    rejection(await save(badDatum),/MISSION92_HOME_DATUM_CAMERA/);assert.equal((await getState()).workspace.token,head);
  });
  await test('rejected-workspace evidence is bounded by count, item bytes and total bytes',async()=>{
    const invalid=structuredClone(compiledDocument);invalid.compiled.plan.sha256='0'.repeat(64);
    for(let i=0;i<12;i++)rejection(await save(invalid),/COMPILE92_PLAN_SHA/);
    const oversized={...uncompiled,extraPadding:'x'.repeat(140000)};rejection(await save(oversized),/MISSION92_SCHEMA/);
    const names=(await fs.readdir(join(out,'nominal'))).filter(n=>n.startsWith('rejected-'));
    let total=0;for(const name of names){const st=await fs.stat(join(out,'nominal',name));assert(st.size<=131072);total+=st.size;}
    assert(names.length>0&&names.length<=8);assert(total<=524288);assert.equal((await getState()).workspace.token,head);
    return {retainedRejectedItems:names.length,rejectedBytes:total};
  });
  await test('no flight connection means payload discovery/grants/capture are denied and no rights restored',async()=>{
    const joined=await request('/api/join',{method:'POST',value:{}});assert.equal(joined.status,200);assert.equal(joined.body.result.actualImages,0);
    const q={...joined.body.result,modelSha256:model.sha256,planSha256:compiledDocument.compiled.plan.sha256,
      flightRun:'fabricated-run',flightBoot:'fabricated-boot',deviceId:'mock-survey'};
    rejection(await request('/api/discover',{method:'POST',value:q}),/FLIGHT_SESSION_BOOT_OR_HEALTH/);
    rejection(await request('/api/grant',{method:'POST',value:q}),/FLIGHT_SESSION_BOOT_OR_HEALTH/);
    rejection(await request('/api/command',{method:'POST',value:{...q,action:'capture',commandId:randomUUID()}}),/FLIGHT_SESSION_BOOT_OR_HEALTH/);
    assert.equal((await getState()).captures.length,0);assert.equal(app.payload.adapter.calls,0);
  });
  await test('HTTP capture review/download and durable TAR handoff retain exact test-seeded synthetic bytes',async()=>{
    seedCapture='capture-'+randomUUID();const f=fixture(seedCapture);await app.store.commit(seedCapture,f);
    // Test-only direct storage seed, not an app camera capture or media observation.
    await delay(1550);const s=await getState(),r=s.captures.find(r=>r.captureId===seedCapture);assert.equal(r.state,'COMMITTED');
    assert.equal(r.sidecar.position.method,'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC');assert.equal(r.receipt.actualImages,0);
    const jpeg=await request('/capture/'+seedCapture);assert.equal(jpeg.status,200);assert.equal(jpeg.type,'image/jpeg');assert.deepEqual(jpeg.bytes,Buffer.from(f.originalBytes));
    rejection(await request('/capture/not-an-id'),/CAPTURE_ID/);
    const handoff=await request('/api/handoff',{method:'POST',value:{captureId:seedCapture}});assert.equal(handoff.status,200);assert.equal(handoff.type,'application/x-tar');
    const snapshot=app.store.snapshot();assert.equal(snapshot.handoffs.length,1);assert.equal(snapshot.handoffs[0].state,'COMMITTED');
    const archive=join(out,'nominal/workspace/handoffs',snapshot.handoffs[0].transferId+'.tar');assert.deepEqual(await fs.readFile(archive),handoff.bytes);
    await fs.writeFile(join(out,'http-handoff.tar'),handoff.bytes);return {testOnlyStorageSeed:true,tarSha256:hash(handoff.bytes),actualImages:0};
  });
  await test('corrupt capture is quarantined by review/download/export; pending capture survives without success receipt',async()=>{
    const original=join(out,'nominal/workspace/captures',seedCapture,'original.jpg');const bytes=await fs.readFile(original);bytes[50]^=1;
    await fs.chmod(original,0o600);await fs.writeFile(original,bytes);
    rejection(await request('/capture/'+seedCapture),/CAPTURE_FILE_INTEGRITY/);
    const before=app.store.snapshot().handoffs.length;rejection(await request('/api/handoff',{method:'POST',value:{captureId:seedCapture}}),/CAPTURE_FILE_INTEGRITY/);
    assert.equal(app.store.snapshot().handoffs.length,before);
    const id='capture-'+randomUUID(),f=fixture(id);let calls=0;f.guard=()=>{if(++calls===2)throw Error('QA_EXPLICIT_REVOKE');};
    await assert.rejects(app.store.commit(id,f),/CAPTURE_PENDING_UNCERTAIN/);
    await delay(1550);const s=await getState();assert.equal(s.captures.find(r=>r.captureId===seedCapture).state,'QUARANTINE');
    assert.equal(s.captures.find(r=>r.captureId===id).state,'PENDING');assert.equal(s.store.poisoned,true);assert.equal(s.store.authority,'NONE');
    rejection(await request('/capture/'+id),/CAPTURE_NOT_COMMITTED/);assert.equal(s.workspace.token,head);
    return {corruptCapture:seedCapture,pendingCapture:id,testOnlyStorageFaults:true};
  });
} catch(e) {results.push({name:'APP_SETUP_OR_UNCAUGHT',status:'FAIL',error:e.stack});}
finally {await app?.close('HTTP_QA_COMPLETE');}

await test('owned normal app closure releases writer lock and both listeners',async()=>{
  assert.equal(await exists(join(out,'nominal/workspace/writer.lock')),false);assert.equal(app.server.listening,false);assert.equal(app.media.server.listening,false);
});
const summary={scope:'FIELD01_DELEGATED_NONFLIGHT_HTTP_QA_REAL_APP_COMPILER_STORE_NEW_OWNED_WORKSPACE',actualImages:0,
  appAuthor:'root',qaAuthor:'delegated_evidence_builder',independentHumanReview:false,
  passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length,
  limitations:['No flight commands or SITL, browser, Android or physical camera used',
    'Capture bytes/review faults seeded directly through own Store01 API, not claimed as app media capture',
    'QA author implemented Store01; its storage review is not independent','Rejection count/bytes checked with small repeated requests, no disk stress fill'],results};
await fs.writeFile(join(out,'results.json'),JSON.stringify(summary,null,2));
console.log(JSON.stringify({passed:summary.passed,failed:summary.failed,evidence:out}));
if(summary.failed){console.error(JSON.stringify(results.filter(r=>r.status==='FAIL'),null,2));process.exitCode=1;}
