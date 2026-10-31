import fs from'node:fs';import assert from'node:assert/strict';import path from'node:path';import {Controller,E}from'./controller-v5.mjs';import{compile,SAMPLES,DEFAULTS,compareMission,sha}from'./compiler.mjs';import{inspectKml}from'../aeris57/domain.mjs';import{replay,save}from'./journal.mjs';import{wait}from'./link.mjs';
const attempt=process.argv[2];if(!/^q\d+$/.test(attempt))throw Error('ATTEMPT');const out=E+'/tests/'+attempt;fs.mkdirSync(out);const checks=[];const ck=(n,v)=>{assert.ok(v,n);checks.push({name:n,pass:true})};let c;
async function make(kind='polygon'){const kml=SAMPLES[kind],d=await inspectKml(kml);return{kml,featureId:d.features[0].id,options:{...DEFAULTS,datumAcknowledged:true},homeConfirmed:true}}
const ctx=(extra={})=>({instance:c.instance,run:c.current?.run,session:c.current?.link.sessionId,boot:c.current?.link.boot,planSha256:c.plan?.sha256,missionSha256:c.plan?.missionSha256,homeConfirmed:true,...extra});
async function rejects(name,fn,pattern){await assert.rejects(fn,pattern);ck(name,true)}
try{
 for(const kind of['polygon','corridor']){
  c=new Controller(out+'/'+kind);const d=await make(kind);await c.action('plan',ctx({...d,expectedHead:c.store.head}));ck(kind+' source/mission SHA retained',c.plan.sha256&&c.plan.sourceSha256&&c.plan.missionSha256);await c.action('connect',ctx({mode:'mock'}));
  await rejects(kind+' AUTO before readback denied',()=>c.action('auto',ctx()),/READBACK|readback/);
  await c.action('preflight',ctx());ck(kind+' readonly20typed+extra ready',c.current.link.preflightView().ready&&c.current.link.inspectionGate.assessment.armPermission===false);
  await rejects(kind+' wrong session denied',()=>c.action('upload',ctx({session:'foreign'})),/OWNED/);
  await rejects(kind+' wrong plan digest denied',()=>c.action('upload',ctx({planSha256:'0'.repeat(64)})),/CONFIRMATION/);
  await c.action('upload',ctx());ck(kind+' complete readback includes camera',c.current.link.readback.items===c.plan.compiled.items.length&&c.current.link.readback.cameraCommands>0);
  await rejects(kind+' edit while connected denied',()=>c.action('plan',ctx({...d,expectedHead:c.store.head})),/CLOSE_SESSION/);
  await c.action('arm',ctx());ck(kind+' Home updated on arm and readback rechecked',c.current.link.homeReview.preArmHome.amsl!==c.current.link.homeReview.postArmHome.amsl);await rejects(kind+' old confirmation cannot start AUTO',()=>c.action('auto',ctx()),/POST_ARM/);await c.action('auto',ctx({homeReviewSha256:c.current.link.homeReview.sha256,postArmHomeConfirmed:true}));ck(kind+' AUTO observed not ACK-only',c.current.link.autoSeen);
  await c.current.link.until(()=>c.current.link.completion().complete,7000);const review=await c.action('close',ctx());ck(kind+' reached NAV+RTL+ground/disarm reviewed',review.accepted&&review.execution.missingNavigation.length===0&&review.actualImages===0);
  const cold=new Controller(out+'/'+kind);ck(kind+' cold workspace retains plan / no authority',cold.plan.sha256===review.planSha256&&!cold.current&&!cold.state().authorityRestored);ck(kind+' cold review SHA exact',cold.review(review.run).rawHead===review.rawHead);ck(kind+' full raw chain replay',replay(E+'/runs/'+review.run+'/raw.jsonl').rows.length===review.rawRecords);
 }
 for(const fault of['readback','loss','reboot','foreign','stale']){
  c=new Controller(out+'/'+fault);await c.action('plan',ctx({...await make(),expectedHead:c.store.head}));await c.action('connect',ctx({mode:'mock'}));await c.action('preflight',ctx());
  if(fault==='readback'){c.current.link.socket.fault='readback';await rejects('camera mutation blocks verification',()=>c.action('upload',ctx()),/READBACK|readback/)}
  if(fault==='foreign'){c.current.link.socket.fault='foreign';await wait(1700);await rejects('foreign responses cannot sustain own freshness',()=>c.action('upload',ctx()),/FRESH|READY/)}
  if(fault==='loss'){c.current.link.socket.fault='loss';await wait(1700);await rejects('lost heartbeat blocks upload',()=>c.action('upload',ctx()),/FRESH|READY/)}
  if(fault==='reboot'){c.current.link.socket.boot=0;c.current.link.socket.telemetry();await wait(50);await rejects('boot regression blocks old confirmation',()=>c.action('upload',ctx()),/FRESH|READY|UNCERTAIN/)}
  if(fault==='stale'){c.current.link.extra.AUTO_OPTIONS.at-=11000;await rejects('stale typed AUTO_OPTIONS blocks upload',()=>c.action('upload',ctx()),/READY/)}
  const r=await c.action('abort',ctx({confirmAbort:true}));ck(fault+' aborted evidence never accepted',!r.accepted&&r.aborted);
 }
 const d=await make();await rejects('no explicit Home datum confirmation',()=>compile({...d,homeConfirmed:false}),/Home/);await rejects('KML altitude mode absolute refused',()=>compile({...d,kml:d.kml.replace('<Polygon>','<Polygon><altitudeMode>absolute</altitudeMode>')}),/INSPECTION/);
 await rejects('remote KML not relocated',async()=>{const kml=d.kml.replaceAll('106.807','107.807'),doc=await inspectKml(kml);await compile({...d,kml,featureId:doc.features[0].id})},/bán kính|EXTENT/);
 // Cold workspace corruption must block writes, without touching originals.
 const corrupt=out+'/corrupt';fs.mkdirSync(corrupt);fs.writeFileSync(corrupt+'/000001.json','{');const bad=new Controller(corrupt);ck('corrupt workspace blocks authority',!!bad.store.error&&!bad.current);
 const torn=out+'/torn.jsonl';fs.writeFileSync(torn,'{');assert.throws(()=>replay(torn),/TORN/);ck('torn raw refused',true);
 save(out+'/result.json',{status:'PASS_SCOPED_MOCK_E2E',checks,actualSITL:false});console.log(JSON.stringify({status:'PASS_SCOPED_MOCK_E2E',checks:checks.length}));
}catch(e){save(out+'/failure.json',{error:e.message,stack:e.stack,checks});console.error(e);if(c?.current)try{await c.close(true)}catch{}process.exitCode=1}
