/** QA-only effective bootstrap cases. Not executed on import. */
import assert from 'node:assert/strict';
import {bootstrapFixture,deferred,drain,observe} from './qa-bootstrap-fixture.mjs';

export async function bootstrapCases(sourcePath) {
  const cases=[];
  // Work resolves first while the timeout callback has deliberately not run.
  // Elapsed-time validation must still reject at and beyond the original limit.
  for(const elapsed of [999.5,1000,1173.4]) {
    const f=bootstrapFixture(sourcePath),work=deferred();
    const result=observe(f.qa.bounded('qa-late-result',()=>work.promise));
    await drain();f.setTime(elapsed);work.resolve({active:true,epoch:7});await drain();
    if(elapsed<1000)assert.equal(result.state,'FULFILLED');
    else {assert.equal(result.state,'REJECTED');assert.match(result.error,/DEADLINE/);}
    f.dispatchDue();await drain();
    assert.equal(f.diagnostics().counts.acknowledged,elapsed<1000?1:0);
    assert.equal(f.diagnostics().counts.failed,elapsed<1000?0:1);
    cases.push({case:'LATE_TIMER_WORK_RESOLVES_FIRST',elapsedMs:elapsed,result:result.state});
  }
  // A real successful activate, followed by an ignored abort and late body.
  const delayed=deferred();let delayHeartbeat=false;
  const f=bootstrapFixture(sourcePath,{fetchImpl:async request=>{
    if(delayHeartbeat&&request.body?.action==='heartbeat') {
      const original=await request.defaultFetch(request.url,request.options);
      return {...original,json:()=>delayed.promise};
    }
    return request.defaultFetch(request.url,request.options);
  }});
  await f.boot();await drain();assert(f.context().clientId);delayHeartbeat=true;
  f.setTime(750);f.heartbeatTick();await drain();
  const hostReply=f.server.view();assert.equal(hostReply.active,true);
  f.setTime(1923.4);f.dispatchDue();await drain();
  assert.equal(f.diagnostics().localSessionActive,false);
  assert.throws(()=>f.context());
  delayed.resolve({ok:true,result:hostReply});await drain();
  assert.equal(f.diagnostics().localSessionActive,false,'LATE_BODY_MUST_NOT_RESTORE_LOCAL_SESSION');
  assert.throws(()=>f.context());
  f.setTime(3750);assert.equal(f.server.tick().active,true,'TTL3000_EXACT_EXISTING_BOUNDARY');
  f.setTime(3750.01);assert.equal(f.server.tick().active,false,'TTL_GT3000_REVOKES');
  assert.equal(f.revocations.filter(x=>x.reason==='CLIENT_HEARTBEAT_EXPIRED').length,1);
  const sentAfterFailure=f.requests.length;
  f.heartbeatTick();await drain();
  assert.equal(f.requests.length,sentAfterFailure,'NO_AUTOMATIC_HEARTBEAT_OR_REACTIVATION_AFTER_LOSS');
  cases.push({case:'LATE_BODY_IGNORED_ABORT_NO_LOCAL_RESTORE_AND_TTL_REVOKE',localActive:false,hostActive:false});

  // Invalid identities cannot refresh a live host session or revive an expired one.
  const g=bootstrapFixture(sourcePath);await g.boot();await drain();const identity=g.context();
  const before=g.server.view().heartbeatAt;
  for(const change of [{clientId:'wrong-id'},{clientEpoch:identity.clientEpoch+1},{clientInstance:'wrong-instance'},{instance:'wrong-instance'}]) {
    assert.throws(()=>g.server.action({action:'heartbeat',instance:'qa-heartbeat-instance',...identity,...change}));
    assert.equal(g.server.view().heartbeatAt,before);
  }
  g.setTime(3000.01);assert.throws(()=>g.server.action({action:'heartbeat',instance:'qa-heartbeat-instance',...identity}));
  assert.equal(g.server.view().active,false);
  assert.equal(g.server.view().authorityRestored,false);
  cases.push({case:'WRONG_ID_EPOCH_INSTANCE_AND_EXPIRED_HOST_REFUSE',heartbeatAtUnchanged:true});
  const background=bootstrapFixture(sourcePath);await background.boot();await drain();
  const retired=background.context();
  await background.browser.field02Lifecycle('background');await drain();
  assert.equal(background.server.view().active,false);assert.throws(()=>background.context());
  const pausedRequests=background.requests.length;
  background.setTime(750);background.heartbeatTick();await drain();
  assert.equal(background.requests.length,pausedRequests);
  await background.browser.field02Lifecycle('foreground');await drain();
  const fresh=background.context();
  assert(fresh.clientEpoch>retired.clientEpoch&&fresh.clientId!==retired.clientId);
  assert.throws(()=>background.server.assert(retired));
  assert.equal(background.server.view().authorityRestored,false);
  cases.push({case:'BACKGROUND_NO_HEARTBEAT_EXPLICIT_FOREGROUND_NEW_EPOCH_ONLY',oldContextRefused:true});
  return {cases,source:f.source,scope:f.classification,
    limits:'Timer/body races are deterministic VM tests with actual bootstrap and ClientSession02; not an effective HTTP handler, TCP latency, Android, or actual G12 cause proof.'};
}
