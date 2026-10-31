import '../../pilot/field01/flight/isolated-loader.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const {Flight01}=await import('../../pilot/field01/flight/flight01.mjs');
const m=await import('../../native/integration03/assets/mission92.mjs'),o=await import('../../native/integration03/assets/offline94.mjs');
const sitl=process.argv.includes('--sitl'),checks=[],report={scope:sitl?'REAL_CACHED_ARDUPILOT_SITL_HOST':'MOCK_PROTOCOL_ONLY',checks};let f;
const ck=(name,value)=>{assert(value,name);checks.push({name,pass:true})};
const req=x=>({...f.state().request,...x});
async function doc(kind){let model=await m.default92(kind),i=await o.inspect94(model);model=await m.edit92(model,{featureId:i.document.features[0].id,options:{...model.draft.options,datumAcknowledged:true}});return m.document92(model,(await o.compile94(model)).compiled);}
async function deny(name,route,extra,pattern){const before=f.current?.capture.n;await assert.rejects(()=>f.action(route,req(extra)),pattern);ck(name,f.current?.capture.n>=before);}
try{
 for(const kind of(sitl?['polygon']:['polygon','corridor'])){
  f=new Flight01();await f.setDocument(await doc(kind));await f.action('connect',req({mode:sitl?'sitl':'mock',confirmSimulation:true}));report.run=f.state().run;ck('actual fixed source and binding',f.state().binding.modelSha256&&f.state().binding.planSha256);
  await deny('write without explicit grant','upload',{},/GRANT/);
  // One readonly cycle only. Waiting does not repeat uncertain writes.
  if(sitl)await new Promise(r=>setTimeout(r,22000));
  await f.action('preflight',req());ck('readonly preflight ready',f.state().live.preflight63.ready);
  await deny('foreign session rejected','grant',{session:'foreign',authorityConfirmed:true},/SESSION/);
  await deny('foreign model rejected','grant',{modelSha256:'0'.repeat(64),authorityConfirmed:true},/BINDING/);
  await f.action('grant',req({authorityConfirmed:true}));await f.action('upload',req());ck('readback verified',f.state().live.readback63.matches);
  await f.action('arm',req());ck('post-arm review required',f.state().live.homeReview.requiresExplicitConfirmation);
  await deny('old home review denied','auto',{},/HOME_CONFIRMATION/);
  await f.action('auto',req({homeReviewSha256:f.state().live.homeReview.sha256,postArmHomeConfirmed:true}));
  await f.current.link.until(()=>f.current.link.completion().complete,sitl?180000:10000);
  ck('navigation RTL ground disarm observed',f.state().live.completion.complete);const pos=f.positions({limit:1})[0];ck('position reference datum/clock honest',pos.altitudeMslM!==null&&pos.sensorTimeUncertaintyMs===null&&pos.ellipsoidAltitudeM===null&&pos.rawRef.sha256);ck('bounded lookup',f.lookupPosition({hostMonoMs:pos.hostMonoMs}).hostReferenceDeltaMs===0);
  const r=await f.action('close',req());ck('nominal evidence accepted',r.accepted&&!f.state().authority);report.nominalReview=r.run;
 }
 if(!sitl)for(const fault of ['loss','boot-regression','reboot','cut','revoke']){
  f=new Flight01();await f.setDocument(await doc('polygon'));await f.action('connect',req({mode:'mock',confirmSimulation:true}));await f.action('preflight',req());await f.action('grant',req({authorityConfirmed:true}));const old=req();
  if(fault==='loss'){f.current.link.socket.fault='loss';await new Promise(r=>setTimeout(r,1800));ck('link stale revokes authority',!f.state().authority);await assert.rejects(()=>f.action('upload',old),/GRANT|FRESH/);await f.action('abort',req({confirmSimulation:true}));}
  else if(fault==='boot-regression'){f.current.link.socket.boot=0;f.current.link.socket.telemetry();await new Promise(r=>setTimeout(r,50));ck('actual mock boot regression revokes authority',!f.state().authority&&!!f.state().live.failure);await assert.rejects(()=>f.action('upload',old),/GRANT|FRESH/);await f.action('abort',req({confirmSimulation:true}));}
  else if(fault==='revoke'){await f.action('revoke',req());await assert.rejects(()=>f.action('upload',old),/GRANT/);await f.action('abort',req({confirmSimulation:true}));}
  else {const r=await f.action(fault,req({confirmSimulation:true}));ck(fault+' never accepted',!r.accepted&&!r.execution.complete);}
  ck(fault+' no authority restore',!f.state().authority&&!new Flight01().state().authority);
 }
 report.status='PASS';fs.writeFileSync('evidence/field01/flight-test-'+(sitl?'sitl':'mock')+'.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}catch(e){report.status='FAIL';report.error=e.message;report.stack=e.stack;fs.writeFileSync('evidence/field01/flight-test-'+(sitl?'sitl':'mock')+'-failure-'+Date.now()+'.json',JSON.stringify(report,null,2)+'\n');console.error(e);if(f?.current)try{await f.action('abort',req({confirmSimulation:true}));}catch(x){console.error(x)}process.exitCode=1;}
