/** Delegated integration QA of root-authored Payload01 using real async Store01.
 * Flight/media/clock and JPEG are explicitly synthetic fixtures. No SITL/camera run.
 */
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import { join,resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { Payload01 } from '../../pilot/field01/gateway.mjs';
import { Store01 } from '../../pilot/field01/evidence/store01.mjs';
import { syntheticJpegBytes } from '../../pilot/field01/evidence/fixtures.mjs';
const repo=resolve(fileURLToPath(new URL('../..',import.meta.url))), runId=new Date().toISOString().replace(/[:.]/g,'-');
const out=join(repo,'evidence/field01',`evidence-gateway-tests-${runId}`);await fs.mkdir(out,{recursive:true});
const results=[];
async function test(name,fn){const at=performance.now();try{const detail=await fn();results.push({name,status:'PASS',elapsedMs:performance.now()-at,...detail});}
  catch(e){results.push({name,status:'FAIL',elapsedMs:performance.now()-at,error:e.stack});}}
async function setup(name,{hooks={}}={}){
  let now=1000,lookup={latitudeDeg:10.5,longitudeDeg:106.5,altitudeMslM:12.5,relativeHomeM:2.5,
    hostMonoMs:999,method:'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC',run:'fixture-flight',boot:'fixture-flight-boot',session:'fixture-flight-session',modelSha256:'1'.repeat(64),planSha256:'2'.repeat(64)};
  const state={run:'fixture-flight',request:{run:'fixture-flight',boot:'fixture-flight-boot',session:'fixture-flight-session'},source:'MOCK_SIMULATION_NO_VEHICLE',
    live:{transport:'connected',heartbeatAgeMs:0},latestPosition:{hostMonoMs:1000}};
  const workspace={document:{mission:{sha256:'1'.repeat(64)},compiled:{plan:{sha256:'2'.repeat(64)}}},pending:false};
  const frame={frameId:'frame-001',feed:'rgb',sourceRun:'fixture-source',sourceBoot:'fixture-source-boot',configId:'fixture-config',
    sourceTimestampUs:900000,referenceHostMonoMs:1000,sourceHostBounds:{lowerMs:990,upperMs:1010}};
  let readable=true;
  const media={readFrame:q=>{assert(readable&&q&&q.frameId===frame.frameId,'STALE_FRAME');return structuredClone(frame);}};
  const flight={state:()=>structuredClone(state),lookupPosition:({hostMonoMs,maxDeltaMs})=>{assert.equal(hostMonoMs,1000);assert.equal(maxDeltaMs,1500);return structuredClone(lookup);}};
  const root=join(out,name),store=await Store01({root,hooks}),gateway=new Payload01({store,flight,media,workspace:()=>workspace,clock:()=>now});
  async function prepare(){const station=gateway.join(),q={...station,modelSha256:workspace.document.mission.sha256,planSha256:workspace.document.compiled.plan.sha256,
    flightRun:state.run,flightBoot:state.request.boot,deviceId:'mock-survey'};
    const d=await gateway.discover(q);q.generation=d.generation;await gateway.select(q);const grant=await gateway.grant(q);return {...q,token:grant.token};}
  const capture=q=>({...q,commandId:randomUUID(),action:'capture',args:{},frame:{frameId:frame.frameId},jpegBase64:Buffer.from(syntheticJpegBytes()).toString('base64')});
  return {root,store,gateway,prepare,capture,state,workspace,frame,clock:v=>now=v,
    freshTelemetry:()=>{state.live.transport='connected';state.live.heartbeatAgeMs=0;state.latestPosition={hostMonoMs:now};},
    lookup:v=>lookup=v,reference:()=>structuredClone(lookup),staleFrame:()=>readable=false};
}

await test('session, station, model/plan, flight boot/health gates precede adapter invocation',async()=>{
  const h=await setup('identity');try{const q=await h.prepare(),before=h.gateway.adapter.calls;
    for(const change of [{gatewaySession:'wrong'},{stationId:'wrong'},{modelSha256:'3'.repeat(64)},{planSha256:'4'.repeat(64)},
      {flightRun:'wrong'},{flightBoot:'wrong'},{token:'wrong'}])await assert.rejects(h.gateway.command({...h.capture(q),...change}));
    h.state.live.failure='LINK_LOST';await assert.rejects(h.gateway.command(h.capture(q)),/FLIGHT_SESSION_BOOT_OR_HEALTH/);
    h.state.live={transport:'connected',heartbeatAgeMs:0};h.workspace.pending=true;await assert.rejects(h.gateway.command(h.capture(q)),/COMMITTED_COMPILED_WORKSPACE/);
    assert.equal(h.gateway.adapter.calls,before);assert.equal(h.store.snapshot().captures.length,0);
  }finally{await h.store.close();}
});

await test('exclusive lease, expired lease, stale discovery, command replay and readback correlation',async()=>{
  const h=await setup('lease');try{const q=await h.prepare();
    await assert.rejects(h.prepare(),/DEVICE_OWNED/);
    const command={...q,commandId:randomUUID(),action:'iso',args:{iso:400}};
    const got=await h.gateway.command(command);assert.equal(got.status,'MOCK_READBACK');assert.equal(got.observed.iso,400);
    assert.equal(got.actualHardwareExecution,'NOT_CHECKED');await assert.rejects(h.gateway.command(command),/COMMAND_REPLAY_OR_QUOTA/);
    h.clock(61001);h.freshTelemetry();await assert.rejects(h.gateway.command(h.capture(q)),/PAYLOAD_AUTHORITY_REQUIRED/);
    h.clock(121001);h.freshTelemetry();await assert.rejects(h.gateway.command(h.capture(q)),/DISCOVERY_STALE_BOOT_OR_LINK/);
    assert.equal(h.gateway.adapter.calls,1);
  }finally{await h.store.close();}
});

await test('heartbeat/transport/position freshness are independent of error flags and revoke leases without restore',async()=>{
  for(const [name,change]of [
    ['heartbeat-old',h=>h.state.live.heartbeatAgeMs=1501],
    ['heartbeat-missing',h=>delete h.state.live.heartbeatAgeMs],
    ['heartbeat-future',h=>h.state.live.heartbeatAgeMs=-1],
    ['heartbeat-nan',h=>h.state.live.heartbeatAgeMs=NaN],
    ['transport-closed',h=>h.state.live.transport='closed'],
    ['position-old',h=>h.clock(2501)],
    ['position-missing',h=>h.state.latestPosition=null],
    ['position-null-time',h=>h.state.latestPosition.hostMonoMs=null],
    ['position-future',h=>h.state.latestPosition.hostMonoMs=1001],
    ['position-nan',h=>h.state.latestPosition.hostMonoMs=NaN],
  ]){
    const h=await setup(name);try{const q=await h.prepare();change(h);assert(!h.state.error&&!h.state.live.failure);
      await assert.rejects(h.gateway.command(h.capture(q)),/FLIGHT_FRESHNESS_REQUIRED/);
      assert.equal(h.gateway.leases.size,0);assert.equal(h.gateway.status(q).leaseOwned,false);assert.equal(h.gateway.status(q).flightFresh,false);
      assert.equal(h.gateway.adapter.calls,0);assert.equal(h.store.snapshot().captures.length,0);
      h.clock(1000);h.freshTelemetry();await assert.rejects(h.gateway.command(h.capture(q)),/DISCOVERY_STALE_BOOT_OR_LINK/);
      assert.equal(h.gateway.leases.size,0);
    }finally{await h.store.close();}
  }
  const h=await setup('inclusive-freshness-boundary');try{const q=await h.prepare();h.clock(2500);h.state.live.heartbeatAgeMs=1500;
    const result=await h.gateway.command({...q,commandId:randomUUID(),action:'iso',args:{iso:400}});
    assert.equal(result.status,'MOCK_READBACK');assert.equal(h.gateway.status(q).positionAgeMs,1500);
  }finally{await h.store.close();}
});

await test('stale telemetry during command intent fsync prevents adapter dispatch and revokes authority',async()=>{
  let h,armed=false;h=await setup('stale-during-command-intent',{hooks:{at:async stage=>{
    if(armed&&stage==='journal.fsync'){armed=false;h.state.live.heartbeatAgeMs=1501;}
  }}});
  try{const q=await h.prepare();armed=true;await assert.rejects(h.gateway.command(h.capture(q)),/FLIGHT_FRESHNESS_REQUIRED/);
    assert.equal(h.gateway.adapter.calls,0);assert.equal(h.gateway.leases.size,0);assert.equal(h.store.snapshot().captures.length,0);
  }finally{armed=false;await h.store.close();}
});

await test('stale position during adapter await returns UNKNOWN, revokes authority and never commits JPEG',async()=>{
  const h=await setup('stale-during-adapter');try{const q=await h.prepare(),invoke=h.gateway.adapter.invoke.bind(h.gateway.adapter);
    h.gateway.adapter.invoke=async(...args)=>{const r=invoke(...args);await Promise.resolve();h.clock(2501);return r;};
    const result=await h.gateway.command(h.capture(q));assert.equal(result.status,'UNKNOWN');assert.equal(result.actualImages,0);
    assert.equal(h.gateway.leases.size,0);assert.equal(h.store.snapshot().captures.length,0);
    assert(h.store.records().some(r=>r.kind==='PAYLOAD_COMMAND_UNKNOWN'&&r.data.reason==='FLIGHT_FRESHNESS_REQUIRED'));
  }finally{await h.store.close();}
});

await test('stale transport during readback fsync cannot publish active readback authority',async()=>{
  let h,armed=false;h=await setup('stale-during-readback',{hooks:{at:async stage=>{
    if(armed&&stage==='journal.fsync'&&h.store.records().at(-1)?.kind==='PAYLOAD_COMMAND_INTENT'){
      armed=false;h.state.live.transport='closed';}
  }}});
  try{const q=await h.prepare();armed=true;const result=await h.gateway.command({...q,commandId:randomUUID(),action:'iso',args:{iso:400}});
    assert.equal(result.status,'UNKNOWN');assert.equal(result.authorityRestored,false);assert.equal(h.gateway.leases.size,0);
    assert(h.store.records().some(r=>r.kind==='PAYLOAD_READBACK_AUTHORITY_ENDED'));
  }finally{armed=false;await h.store.close();}
});

await test('stale heartbeat during capture file sync is stopped by guard with pending evidence retained',async()=>{
  let h,armed=false;h=await setup('stale-during-capture-files',{hooks:{at:async stage=>{
    if(armed&&stage==='capture.directory.fsync'){armed=false;h.state.live.heartbeatAgeMs=1501;}
  }}});
  try{const q=await h.prepare();armed=true;await assert.rejects(h.gateway.command(h.capture(q)),/CAPTURE_PENDING_UNCERTAIN:FLIGHT_FRESHNESS_REQUIRED/);
    assert.equal(h.gateway.leases.size,0);assert.equal((await h.store.review()).rows[0].state,'PENDING');
    assert.equal(h.store.records().filter(r=>r.kind==='CAPTURE_COMMITTED').length,0);
  }finally{armed=false;await h.store.close();}
});

await test('capture commits unchanged JPEG + exact source/session/link context and nearest MSL method',async()=>{
  const h=await setup('capture');try{const q=await h.prepare(),request=h.capture(q),result=await h.gateway.command(request);
    assert.equal(result.status,'SYNTHETIC_REFERENCE_COMMITTED');assert.equal(result.actualImages,0);assert.equal(result.qualifiedForSurvey,false);
    const saved=await h.store.read(result.captureId),s=saved.sidecar;
    assert.deepEqual(saved.originalBytes,Buffer.from(request.jpegBase64,'base64'));
    assert.equal(s.position.method,'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC');assert.equal(s.position.datum,'MSL');
    assert.equal(s.position.altitudeMslM,12.5);assert.equal(s.position.relativeHomeM,2.5);assert.equal(s.position.sensorTimeUncertaintyMs,null);
    assert.equal(s.timing.physicalExposureTime,'UNKNOWN');assert.equal(s.context.gatewaySession,q.gatewaySession);
    assert.equal(s.context.stationId,q.stationId);assert.equal(s.context.flightBoot,q.flightBoot);assert.equal(s.context.payloadId,'mock-survey');
    assert.equal(s.context.sourceRun,h.frame.sourceRun);assert.equal(s.context.sourceBoot,h.frame.sourceBoot);assert.equal(s.context.configId,h.frame.configId);
    assert.equal(saved.manifest.link.modelSha256,q.modelSha256);assert.equal(saved.manifest.link.planSha256,q.planSha256);
    const kinds=h.store.records().map(r=>r.kind);assert(kinds.indexOf('PAYLOAD_COMMAND_INTENT')<kinds.indexOf('CAPTURE_INTENT'));
    assert(kinds.indexOf('CAPTURE_INTENT')<kinds.indexOf('CAPTURE_COMMITTED'));
    await fs.writeFile(join(out,'gateway-capture-receipt.json'),JSON.stringify({sidecar:s,receipt:saved.receipt},null,2));
  }finally{await h.store.close();}
});

await test('missing position retains unlocated JPEG with explicit reason; stale frame and invalid JPEG never commit',async()=>{
  const h=await setup('unlocated');try{const q=await h.prepare();h.lookup(null);
    const got=await h.gateway.command(h.capture(q)),saved=await h.store.read(got.captureId);
    assert.equal(saved.sidecar.position,null);assert(saved.sidecar.timing.reason);assert.equal(saved.receipt.actualImages,0);
    const count=h.store.snapshot().captures.length;const bad=h.capture(q);bad.jpegBase64='AA==';await assert.rejects(h.gateway.command(bad),/ORIGINAL_JPEG/);
    h.staleFrame();await assert.rejects(h.gateway.command(h.capture(q)),/STALE_FRAME/);assert.equal(h.store.snapshot().captures.length,count);
  }finally{await h.store.close();}
});

await test('wrong lookup run/boot/model/plan/session is retained unlocated, never relabeled into current context',async()=>{
  for(const [key,value]of [['run','prior-run'],['boot','prior-boot'],['modelSha256','3'.repeat(64)],['planSha256','4'.repeat(64)],['session','prior-session']]){
    const h=await setup('wrong-position-'+key);try{const q=await h.prepare(),old=h.reference();old[key]=value;h.lookup(old);
      const result=await h.gateway.command(h.capture(q)),saved=await h.store.read(result.captureId);
      assert.equal(result.position,null);assert.equal(saved.sidecar.position,null);assert.equal(saved.sidecar.timing.reason,'POSITION_CONTEXT_MISMATCH');
      assert.equal(saved.sidecar.context.flightRun,q.flightRun);assert.equal(saved.sidecar.context.flightBoot,q.flightBoot);
      assert.equal(saved.receipt.actualImages,0);assert.equal(saved.manifest.link.modelSha256,q.modelSha256);
    }finally{await h.store.close();}
  }
});

await test('rapid reconnect with fresh current telemetry cannot reuse fresh prior-run position history',async()=>{
  const h=await setup('rapid-reconnect-old-position');try{const oldQuery=await h.prepare(),prior=h.reference();
    h.gateway.invalidate('EXPLICIT_RECONNECT');h.state.run='fixture-next-flight';h.state.request={run:h.state.run,boot:'fixture-next-boot',session:'fixture-next-session'};h.freshTelemetry();
    const next=await h.prepare();assert.notEqual(next.flightRun,oldQuery.flightRun);assert.notEqual(next.flightBoot,oldQuery.flightBoot);
    assert.equal(h.gateway.status(next).flightFresh,true);h.lookup(prior);
    const result=await h.gateway.command(h.capture(next)),saved=await h.store.read(result.captureId);
    assert.equal(saved.sidecar.context.flightRun,next.flightRun);assert.equal(saved.sidecar.context.flightBoot,next.flightBoot);
    assert.equal(saved.sidecar.position,null);assert.equal(saved.sidecar.timing.reason,'POSITION_CONTEXT_MISMATCH');
    assert.equal(saved.manifest.link.flightRun,next.flightRun);assert.equal(saved.receipt.actualImages,0);
  }finally{await h.store.close();}
});

await test('wrong target, absent readback/event/file and quality fault retain zero capture results',async()=>{
  const h=await setup('fault-results');try{const q=await h.prepare();
    for(const fault of ['wrongTarget','lostFeedback','noEvent','noFile']){
      await h.gateway.fault({...q,fault});const got=await h.gateway.command(h.capture(q));assert.match(got.status,/^UNKNOWN/);assert.equal(got.actualImages,0);
    }
    for(const fault of ['badGnss','corruptFile']){await h.gateway.fault({...q,fault});await assert.rejects(h.gateway.command(h.capture(q)),/MOCK_CAPTURE_QUALITY_FAULT/);}
    assert.equal(h.store.snapshot().captures.length,0);
    assert.equal(h.store.records().filter(r=>r.kind==='PAYLOAD_COMMAND_UNKNOWN').length,2);
    assert.equal(h.store.records().filter(r=>r.kind==='PAYLOAD_CAPTURE_UNKNOWN').length,2);
  }finally{await h.store.close();}
});

await test('500ms adapter timeout is UNKNOWN, bounded one invocation, no automatic retry or JPEG commit',async()=>{
  const h=await setup('timeout');try{const q=await h.prepare();let calls=0,aborted=false;
    h.gateway.adapter.invoke=(_id,_action,_args,{signal})=>{calls++;h.state.live.heartbeatAgeMs=1501;return new Promise((_,reject)=>signal.addEventListener('abort',()=>{aborted=true;reject(Error('MOCK_ABORTED'));},{once:true}));};
    const at=performance.now(),got=await h.gateway.command(h.capture(q)),elapsedMs=performance.now()-at;
    assert.equal(got.status,'UNKNOWN');assert.equal(got.execution,'NOT_CONFIRMED');assert.equal(got.actualImages,0);
    assert.equal(calls,1);assert.equal(aborted,true);assert(elapsedMs>=450&&elapsedMs<2000);assert.equal(h.store.snapshot().captures.length,0);
    assert.equal(h.gateway.leases.size,0);assert.equal(h.gateway.revocation,'FLIGHT_FRESHNESS_LOST');
    return {timeoutElapsedMs:elapsedMs,adapterCalls:calls};
  }finally{await h.store.close();}
});

await test('disconnect/reboot and flight invalidation revoke old authority and discovery',async()=>{
  for(const fault of ['disconnect','reboot']){
    const h=await setup(fault);try{const q=await h.prepare();await h.gateway.fault({...q,fault});
      assert.equal(h.gateway.status(q).leaseOwned,false);assert.equal(h.gateway.leases.size,0);
      await assert.rejects(h.gateway.command(h.capture(q)),/DISCOVERY_STALE_BOOT_OR_LINK/);assert.equal(h.gateway.adapter.calls,0);
    }finally{await h.store.close();}
  }
  const h=await setup('flight-invalidation');try{const q=await h.prepare();h.gateway.invalidate('FLIGHT_REBOOT');
    await assert.rejects(h.gateway.command(h.capture(q)),/DISCOVERY_STALE_BOOT_OR_LINK/);assert.equal(h.gateway.leases.size,0);
  }finally{await h.store.close();}
});

await test('revocation during async file fsync stops commit guard and retains pending without receipt',async()=>{
  let entered,release,delay=false;const waiting=new Promise(r=>entered=r);
  const h=await setup('revoke-during-files',{hooks:{at:async stage=>{if(delay&&stage==='capture.directory.fsync'){entered();await new Promise(r=>release=r);}}}});
  try{const q=await h.prepare();delay=true;const pending=h.gateway.command(h.capture(q));await waiting;
    h.gateway.invalidate('EXPLICIT_ASYNC_REVOKE');release();await assert.rejects(pending,/CAPTURE_PENDING_UNCERTAIN/);
    assert.equal(h.gateway.leases.size,0);assert.equal(h.store.snapshot().poisoned,true);
    const review=await h.store.review();assert.equal(review.rows.length,1);assert.equal(review.rows[0].state,'PENDING');
    assert.equal(h.store.records().filter(r=>r.kind==='CAPTURE_COMMITTED').length,0);
  }finally{delay=false;await h.store.close();}
});

await test('revocation during final receipt fsync keeps durable bytes but reports ended authority',async()=>{
  let enabled=false,fired=false,h;
  h=await setup('late-revoke',{hooks:{at:async stage=>{if(enabled&&!fired&&stage==='journal.fsync'&&h.store.records().at(-1)?.kind==='CAPTURE_INTENT'){
    fired=true;h.gateway.invalidate('REVOKED_DURING_FINAL_RECEIPT_SYNC');}}}});
  try{const q=await h.prepare();enabled=true;const got=await h.gateway.command(h.capture(q));
    assert.equal(fired,true);assert.equal(got.status,'EVIDENCE_COMMITTED_AUTHORITY_ENDED');assert.equal(got.authorityRestored,false);
    assert.equal(got.actualImages,0);assert.equal(h.gateway.leases.size,0);assert.equal((await h.store.read(got.captureId)).receipt.status,'COMMITTED');
    assert(h.store.records().some(r=>r.kind==='PAYLOAD_CAPTURE_AUTHORITY_ENDED_AFTER_COMMIT'));
  }finally{enabled=false;await h.store.close();}
});

await test('clean restart retains bytes/history and new gateway restores no session/station/lease/command authority',async()=>{
  const h=await setup('restart');const q=await h.prepare();const got=await h.gateway.command(h.capture(q));await h.store.close();
  const store=await Store01({root:h.root}),gateway=new Payload01({store,flight:{state:()=>h.state},media:{},workspace:()=>h.workspace,clock:()=>1000});
  try{assert.notEqual(gateway.session,q.gatewaySession);assert.equal(gateway.stations.size,0);assert.equal(gateway.leases.size,0);
    assert.equal(gateway.commands.size,0);assert.equal(store.snapshot().authority,'NONE');assert.equal((await store.read(got.captureId)).receipt.actualImages,0);
    await assert.rejects(gateway.command(h.capture(q)),/GATEWAY_SESSION_OR_STATION/);assert.equal(gateway.adapter.calls,0);
  }finally{await store.close();}
});

const summary={scope:'FIELD01_PAYLOAD_GATEWAY_INTEGRATION_ACTUAL_ASYNC_STORE_SYNTHETIC_FLIGHT_MEDIA_CLOCK',actualImages:0,
  gatewayAuthor:'root_with_delegated_freshness_repair',freshnessRepairAuthor:'delegated_evidence_builder',testsAuthor:'delegated_evidence_builder',independentHumanReview:false,
  passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length,
  limitations:['Flight/media/clock are fakes; this is not SITL, physical camera or browser evidence',
    'Tests author also implemented Store01 and the gateway freshness repair; those assessments are not independent',
    'No measured operator effort advantage; deterministic policy/storage has no LLM runtime baseline'],results};
await fs.writeFile(join(out,'results.json'),JSON.stringify(summary,null,2));
console.log(JSON.stringify({passed:summary.passed,failed:summary.failed,evidence:out}));
if(summary.failed){console.error(JSON.stringify(results.filter(r=>r.status==='FAIL'),null,2));process.exitCode=1;}
