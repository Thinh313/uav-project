import test from 'node:test';
import assert from 'node:assert/strict';
import {localFrame,planPolygonSurvey,DEFAULT_SURVEY,DEMO_CAMERA,surveyPackage,importSurvey,pointInPolygon} from '../app/core/survey.mjs';
import {MissionSession,MissionLibrary,planDigest} from '../app/core/session.mjs';
import {capabilityProfile,InputAdapter} from '../app/core/device.mjs';
const close=(a,b,t=1e-5)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
const frame=localFrame({lat:0,lon:0});
const site=poly=>({...structuredClone(DEFAULT_SURVEY),polygon:poly.map(([x,y])=>frame.reverse({x,y})),altitude:20,speed:5,sideOverlap:50,frontOverlap:50,camera:{...DEMO_CAMERA,sensorWidth:10,sensorHeight:5,focalLength:10,imageWidth:1000,minInterval:1}});
const rectangle=()=>site([[-50,-30],[50,-30],[50,30],[-50,30]]);
const event=(s,extra={})=>({vehicleId:s.vehicleId,sessionId:s.sessionId,transactionId:s.transaction?.id,...extra});
async function upload(s,settings=rectangle()){const pkg=surveyPackage(settings);await s.beginUpload(pkg);s.ack(event(s,{result:'accepted'}));assert.equal(await s.readback(event(s,{package:pkg})),true);return pkg;}
test('G1 geocentric reference: WGS84 equator one degree longitude',()=>{
 const f=localFrame({lat:0,lon:0});const p=f.forward({lat:0,lon:1});close(p.x,111313.83923667614,1e-6);close(p.y,0,1e-9);
 assert.throws(()=>f.reverse({x:6000,y:0}),/phạm vi/);
});
test('G1 local frame round-trip across hemispheres and realistic site extents',()=>{
 for(const origin of [{lat:10.854,lon:106.807},{lat:-33.86,lon:151.21},{lat:60,lon:10},{lat:0,lon:-79}]){
  const f=localFrame(origin);for(const x of [-1200,0,1200])for(const y of [-900,0,900]){const p=f.forward(f.reverse({x,y}));close(p.x,x,1e-6);close(p.y,y,1e-6);}
 }
});
test('G1 independent analytic rectangle: area, spacing, per-line shots, connectors and time',()=>{
 const p=planPolygonSurvey(rectangle());close(p.area,6000);close(p.footprintWidth,20);close(p.footprintHeight,10);close(p.lineSpacing,10);assert.equal(p.lineCount,9);assert.equal(p.photoCount,117);close(p.distance,620);close(p.nominalSeconds,124);close(p.gsdCm,2);assert.equal(p.feasible,true);
});
test('G1 winding reversal does not change survey geometry or shot count',()=>{
 const s=rectangle(),a=planPolygonSurvey(s),b=planPolygonSurvey({...s,polygon:s.polygon.toReversed()});close(a.area,b.area);assert.equal(a.lineCount,b.lineCount);assert.equal(a.photoCount,b.photoCount);close(a.distance,b.distance);
});
test('G1 rotated sweep endpoints and interiors remain clipped for 24 angles',()=>{
 for(let heading=0;heading<180;heading+=7.5){const p=planPolygonSurvey({...rectangle(),heading});for(const t of p.transects){assert.ok(pointInPolygon({x:(t.start.x+t.end.x)/2,y:(t.start.y+t.end.y)/2},p.polygonLocal));assert.ok(t.length>0);assert.ok(t.shots>=2);close(Math.abs((t.end.x-t.start.x)*Math.cos(heading*Math.PI/180)-(t.end.y-t.start.y)*Math.sin(heading*Math.PI/180)),0,1e-6);}assert.equal(p.photoCount,p.transects.reduce((n,t)=>n+t.shots,0));}
});
test('G1 concave U splits scan into separate segments and blocks unsafe connectors',()=>{
 const p=planPolygonSurvey({...site([[-60,-50],[60,-50],[60,50],[20,50],[20,-10],[-20,-10],[-20,50],[-60,50]]),heading:90});
 assert.ok(p.transects.some((t,i)=>i&&t.strip===p.transects[i-1].strip));assert.equal(p.hasOutsideConnector,true);assert.equal(p.feasible,false);assert.match(p.warnings.join(' '),/đoạn nối/);
});
test('G1 invalid polygons rejected: self-intersection, duplicate, tiny, dateline, oversized',()=>{
 for(const poly of [[[0,0],[100,100],[0,100],[100,0]],[[0,0],[100,0],[100,100],[0,0]],[[0,0],[1,0],[0,1]],[[0,0],[3100,0],[3100,100],[0,100]]])assert.throws(()=>planPolygonSurvey(site(poly)));
 assert.throws(()=>planPolygonSurvey({...rectangle(),polygon:[{lat:0,lon:179.99},{lat:0,lon:-179.99},{lat:.01,lon:179.99}]}));
});
test('G1 bad units and unknown/invalid fields rejected before generating route',()=>{
 for(const patch of [{heading:180},{speed:'6'},{altitude:NaN},{sideOverlap:100},{unknown:true},{camera:{...DEMO_CAMERA,focalLength:0}},{camera:{...DEMO_CAMERA,imageWidth:1000.5}}])assert.throws(()=>planPolygonSurvey({...rectangle(),...patch}));
});
test('G1 target GSD derives altitude; changing target never applies overlap twice',()=>{
 const s={...rectangle(),targetGsdCm:1},p=planPolygonSurvey(s);close(p.effectiveAltitude,10);close(p.settings.altitude,10);close(p.gsdCm,1);close(p.nominalTriggerSpacing,2.5);
 assert.throws(()=>planPolygonSurvey({...s,targetGsdCm:20}),/GSD mục tiêu/);
});
test('G1 missing camera/AGL/DEM keeps photo count and footprint null and blocks readiness',()=>{
 for(const patch of [{camera:null},{altitudeFrame:'terrain'},{altitudeFrame:'relative-launch'},{altitudeFrame:'amsl'}]){const p=planPolygonSurvey({...rectangle(),...patch});assert.equal(p.feasible,false);assert.equal(p.photoCount,null);assert.equal(p.footprintWidth,null);assert.equal(p.gsdCm,null);assert.equal(p.distance,null);}
});
test('G1 capture interval boundary and workload bounds',()=>{
 assert.equal(planPolygonSurvey(rectangle()).feasible,true);assert.equal(planPolygonSurvey({...rectangle(),camera:{...rectangle().camera,minInterval:1.01}}).feasible,false);
 assert.throws(()=>planPolygonSurvey({...rectangle(),altitude:5,sideOverlap:95,frontOverlap:95,camera:{...DEMO_CAMERA,sensorWidth:1,sensorHeight:1,focalLength:200}}),/vượt/);
});
test('U1 v2 semantic round-trip, draft with missing terrain and input nonmutation',()=>{
 for(const s of [rectangle(),{...rectangle(),heading:40,targetGsdCm:1.5},{...rectangle(),altitudeFrame:'terrain'}]){const before=JSON.stringify(s),pkg=surveyPackage(s),restored=importSurvey(JSON.stringify(pkg));assert.deepEqual(restored,pkg);assert.deepEqual(planPolygonSurvey(restored.settings),planPolygonSurvey(pkg.settings));assert.equal(JSON.stringify(s),before);}
});
test('U1 package cannot smuggle operational flags, derived figures or unknown formats',()=>{
 const p=surveyPackage(rectangle());for(const patch of [{version:1},{operational:true},{coordinateSystem:'local'},{format:'Plan'},{photoCount:1234},{model:'terrain-ready'}])assert.throws(()=>importSurvey(JSON.stringify({...p,...patch})));
 assert.throws(()=>importSurvey('null'));assert.throws(()=>importSurvey('x'.repeat(256*1024+1)));
});
test('I1 upload ACK alone does not permit start; mismatched session ACK is ignored',async()=>{
 const s=new MissionSession();await s.beginUpload(surveyPackage(rectangle()));assert.equal(s.ack(event(s,{sessionId:'other',result:'accepted'})),false);assert.throws(()=>s.start());s.ack(event(s,{result:'accepted'}));assert.equal(s.state,'accepted');assert.throws(()=>s.start());
});
test('I1 readback mismatch fails transaction and preserves prior onboard mission',async()=>{
 const s=new MissionSession();await upload(s);const before=structuredClone(s.onboard);await s.beginUpload(surveyPackage({...rectangle(),name:'new plan'}));s.ack(event(s,{result:'accepted'}));assert.equal(await s.readback(event(s,{package:surveyPackage(rectangle())})),false);assert.equal(s.state,'failed');assert.deepEqual(s.onboard,before);assert.throws(()=>s.start());
});
test('I1 start/pause/resume progress uses observed vehicle/session and never skips ahead on resume',async()=>{
 const s=new MissionSession();await upload(s);s.start();assert.equal(s.observeProgress({vehicleId:s.vehicleId,sessionId:'wrong',completedTransects:1}),false);s.observeProgress({vehicleId:s.vehicleId,sessionId:s.sessionId,completedTransects:2});s.pause();assert.equal(s.progress,2);assert.equal(s.observeProgress({vehicleId:s.vehicleId,sessionId:s.sessionId,completedTransects:3}),false);s.start();assert.equal(s.progress,2);assert.equal(s.observeProgress({vehicleId:s.vehicleId,sessionId:s.sessionId,completedTransects:1}),false);s.observeProgress({vehicleId:s.vehicleId,sessionId:s.sessionId,completedTransects:9});assert.equal(s.state,'completed');
});
test('I1 concurrent upload attempts cannot race plan ownership; abort blocks late readback',async()=>{
 const s=new MissionSession(),pkg=surveyPackage(rectangle()),first=s.beginUpload(pkg);await assert.rejects(s.beginUpload(pkg),/Phiên/);await first;s.ack(event(s,{result:'accepted'}));const pending=s.readback(event(s,{package:pkg}));s.abort();assert.equal(await pending,false);assert.equal(s.state,'aborted');
});
test('I1 reject invalid readiness and preserve state for rejected upload',async()=>{
 const s=new MissionSession();await assert.rejects(s.beginUpload(surveyPackage({...rectangle(),altitudeFrame:'terrain'})),/kiểm tra/);assert.equal(s.state,'empty');await s.beginUpload(surveyPackage(rectangle()));s.ack(event(s,{result:'rejected'}));assert.equal(s.state,'failed');
});
test('I1 persisted session restores checked plan without asserting aircraft execution',async()=>{
 const s=new MissionSession();await upload(s);s.start();s.observeProgress({vehicleId:s.vehicleId,sessionId:s.sessionId,completedTransects:1});const snap=s.snapshot(),r=await MissionSession.restore(snap);assert.equal(r.state,'uploaded');assert.equal(r.progress,1);const bad=structuredClone(snap);bad.onboard.package.settings.speed=6;await assert.rejects(MissionSession.restore(bad),/digest/);
});
test('U1 named library stores multiple immutable missions and fails loud on corruption',()=>{
 const values=new Map(),store={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v)},lib=new MissionLibrary(store);const s=rectangle();lib.save(s);lib.save({...s,name:'Mission B'});assert.equal(lib.list().length,2);lib.save({...s,speed:4});assert.equal(lib.list().length,2);assert.equal(lib.list().find(e=>e.package.settings.name===s.name).package.settings.speed,4);values.set(lib.key,'bad');assert.throws(()=>lib.save(s),/JSON/);assert.equal(values.get(lib.key),'bad');
});
test('I1 SHA-256 plan digest ignores key order and changes with mission settings',async()=>{
 const p=surveyPackage(rectangle()),r=Object.fromEntries(Object.entries(p).reverse());assert.equal(await planDigest(p),await planDigest(r));assert.notEqual(await planDigest(p),await planDigest(surveyPackage({...rectangle(),heading:30})));
});
test('I1 capability seam refuses browser evidence as Android observation',()=>{
 assert.ok(Object.values(capabilityProfile().fields).every(f=>f.state==='unknown'&&f.value===null));const observation={androidBuild:{state:'observed',value:'fixture-build',source:'replay fixture',atMs:0}};assert.throws(()=>capabilityProfile(observation),/Browser/);assert.equal(capabilityProfile(observation,'replay').fields.androidBuild.state,'observed');assert.throws(()=>capabilityProfile({androidBuild:{state:'observed',value:'x'}},'android-device'));
});
test('I1 input adapter needs explicit mapping, calibration and attachment; no invented flight bindings',()=>{
 const i=new InputAdapter();assert.throws(()=>i.bind('L1','AUTO'));i.bind('fixture-next','select-next-transect');assert.equal(i.interpret({channel:'fixture-next',pressed:true}),null);i.attach({transport:'replay',source:'fixture',calibration:'fixture-v1'});assert.equal(i.interpret({channel:'fixture-next',pressed:true}).action,'select-next-transect');i.detach();assert.equal(i.interpret({channel:'fixture-next',pressed:true}),null);
});
