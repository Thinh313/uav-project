import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {readFile} from 'node:fs/promises';
import {importQgc,compileQgc,makeQgcRequest,exportQgc,reviewQgc,qgcSha256,compareQgc} from '../app/core/qgc.mjs';import {readbackEqual,SITL_WORLD} from '../app/core/compiler.mjs';import {SitlLink} from '../services/sitl.mjs';
const raw=readFileSync('app/fixtures/qgc/aeris-simple.plan','utf8'),complex=readFileSync('app/fixtures/qgc/aeris-cached-survey.plan','utf8'),upstream=readFileSync('app/fixtures/qgc/upstream-section-v5.1.5.plan','utf8'),run=s=>compileQgc(makeQgcRequest(s));
function change(fn){const p=JSON.parse(raw);fn(p);return JSON.stringify(p);}
test('official legacy fixture normalizes 4+coordinate only for review, retains exact original',()=>{const a=reviewQgc(upstream);assert.equal(a.raw,upstream);assert.equal(a.commands[0].params.length,7);assert.equal(a.compiled,null);assert.match(a.error,/ArduPilot/);});
test('simple preserves null source yaw, records explicit pinned Copter normalization',()=>{const c=run(raw);assert.ok(c.normalizations.length);assert.equal(c.items[1].param4,0);assert.equal(c.sourceRequest.rawPlan,raw);assert.equal(c.items.length,16);});
test('stored complex snapshot flattens same commands, retains polygon/camera original',()=>{const a=run(raw),b=run(complex);assert.deepEqual(a.items,b.items);assert.equal(b.sourceRequest.rawPlan,complex);assert.equal(importQgc(complex).complex.length,1);assert.match(b.sourceKind,/stored complex/);});
test('export roundtrip retains compiled route/speed/camera with correct home/altitude/sequence',()=>{const c=run(complex),o=exportQgc(c),next=run(o.raw);assert.deepEqual(next.items,c.items);assert.equal(JSON.parse(o.raw).mission.items[0].AltitudeMode,1);assert.equal(JSON.parse(o.raw).mission.items[0].doJumpId,1);assert.equal(o.receipt.simulation,true);});
test('server compiles QGC independently from original raw source',()=>{const c=new SitlLink().compileRequest(makeQgcRequest(raw));assert.deepEqual(c.items,run(raw).items);});
const negatives={
 'home relocation':p=>p.mission.plannedHomePosition[0]+=.001,
 'wrong aircraft':p=>p.mission.vehicleType=1,
 'wrong autopilot':p=>p.mission.firmwareType=12,
 'AMSL frame':p=>p.mission.items[0].frame=0,
 'terrain frame':p=>p.mission.items[0].frame=10,
 'altitude metadata mismatch':p=>p.mission.items[0].Altitude+=1,
 'old misleading altitude mode':p=>p.mission.items[0].AltitudeMode=0,
 'nonempty fence':p=>p.geoFence.circles.push({version:1,circle:{center:[10.854,106.807],radius:100},inclusion:true}),
 'nonempty rally':p=>p.rallyPoints.points.push([10.854,106.807,15]),
 'unknown metadata':p=>p.mission.extension='future required behavior',
 'unknown command':p=>p.mission.items[1].command=205,
 'duplicate jump IDs':p=>p.mission.items[1].doJumpId=1,
 'false autoContinue':p=>p.mission.items[0].autoContinue=false,
 'missing takeoff':p=>p.mission.items.shift(),
 'missing RTL':p=>p.mission.items.pop(),
 'missing camera stop':p=>p.mission.items[p.mission.items.length-2].params[0]=10,
 'meaningful null':p=>p.mission.items[0].params[0]=null,
 'unsupported waypoint yaw':p=>p.mission.items[0].params[3]=45,
 'outside world':p=>p.mission.items[2].params[4]+=1,
 'above height cap':p=>{p.mission.items[0].params[6]=121;p.mission.items[0].Altitude=121;},
};for(const [name,fn]of Object.entries(negatives))test('execution rejects '+name,()=>assert.throws(()=>run(change(fn))));
test('empty cache and unsupported complex version rejected without replacement',()=>{for(const fn of [p=>p.mission.items[2].TransectStyleComplexItem.Items=[],p=>p.mission.items[2].version=6]){const p=JSON.parse(complex);fn(p);assert.throws(()=>importQgc(JSON.stringify(p)));}});
test('cached terrain cannot be inferred from relative coordinates',()=>{const p=JSON.parse(complex);p.mission.items[2].TransectStyleComplexItem.CameraCalc.DistanceMode=3;assert.throws(()=>run(JSON.stringify(p)),/relative-home/);});
test('bounded and invalid JSON, params type/length',()=>{for(const s of ['{',' '.repeat(65537),change(p=>p.mission.items[0].params[0]='0'),change(p=>p.mission.items[0].params.pop())])assert.throws(()=>importQgc(s));});
test('explicit simulation profile cannot be changed',()=>{for(const fn of [r=>r.simulation=false,r=>r.worldId='physical',r=>r.profile='other',r=>r.items=[]]){const r=makeQgcRequest(raw);fn(r);assert.throws(()=>compileQgc(r));}assert.throws(()=>compileQgc(makeQgcRequest(raw),{...SITL_WORLD,maxRadiusM:1000}));});
test('readback compares autocontinue and exact altitude mutation',()=>{const c=run(raw),a=structuredClone(c.items);assert.equal(readbackEqual(c.items,a),true);a[3].autocontinue=0;assert.equal(readbackEqual(c.items,a),false);a[3].autocontinue=1;a[3].z+=.01;assert.equal(readbackEqual(c.items,a),false);});

test('heartbeat expiry clears still-fresh live position/GPS/health together',()=>{let clock=4000;const l=new SitlLink({clock:()=>clock});l.transport='connected';l.samples={0:{at:0,fields:{custom_mode:4,base_mode:0}},33:{at:3900,fields:{lat:108540000,lon:1068070000,relative_alt:15000,alt:25000,vx:0,vy:0}},24:{at:3900,fields:{fix_type:3,satellites_visible:12}},1:{at:3900,fields:{voltage_battery:24000,battery_remaining:99}}};assert.equal(l.snapshot().connected,false);for(const k of ['position','gps','health','mode','armed'])assert.equal(l.snapshot()[k],null);});

test('UTF8 BOM is retained for exact export while parsing succeeds',()=>{const bom='\uFEFF'+raw;assert.equal(importQgc(bom).raw,bom);assert.equal(run(bom).sourceRequest.rawPlan,bom);});

test('lineage hash binds exact UTF8 output bytes',async()=>{const {createHash}=await import('node:crypto');assert.equal(await qgcSha256('\uFEFF'+raw),createHash('sha256').update('\uFEFF'+raw).digest('hex'));});

test('Actual desktop corpus: hashes, camera stop changes, regenerated Survey and stable second save',async()=>{const {compareQgc}=await import('../app/core/qgc.mjs');const {createHash}=await import('node:crypto');const corpus=JSON.parse(await readFile('app/fixtures/qgc/desktop/provenance.json','utf8'));assert.equal(corpus.fixtures.length,7);for(const f of corpus.fixtures){const raw=await readFile('app/fixtures/qgc/desktop/'+f.file,'utf8');assert.equal(createHash('sha256').update(raw).digest('hex'),f.sha256);const q=reviewQgc(raw);assert.equal(q.plan.groundStation,'QGroundControl');assert.equal(q.raw,raw);assert.equal(q.compiled,null);}const original=await readFile('app/fixtures/qgc/aeris-simple.plan','utf8'),first=await readFile('app/fixtures/qgc/desktop/aeris-simple-qgc-saved.plan','utf8'),second=await readFile('app/fixtures/qgc/desktop/qgc-reopened-simple.plan','utf8');const d=compareQgc(original,first);assert.equal(d.equal,false);assert.equal(d.changes.filter(c=>c.path.endsWith('.params[2]')).length,3);assert.ok(d.changes.some(c=>c.path==='mission.plannedHomePosition'));assert.ok(compareQgc(first,second).equal);const complex=compareQgc(await readFile('app/fixtures/qgc/aeris-cached-survey.plan','utf8'),await readFile('app/fixtures/qgc/desktop/aeris-cached-survey-qgc-saved.plan','utf8'));assert.ok(complex.changes.some(c=>c.path.endsWith('.params[4]')));});
test('Semantic compare ignores byte formatting only; camera, altitude, fence and unknown extensions stay visible',()=>{const a=raw,p=JSON.parse(a);assert.equal(compareQgc(a,JSON.stringify(p)).equal,true);for(const mutate of [x=>x.mission.items[3].params[2]=0,x=>x.mission.plannedHomePosition[2]+=1,x=>x.mission.items[0].frame=0,x=>x.geoFence.circles.push({unknown:true}),x=>x.extra={a:1},x=>x.mission.items[0].extra=true]){const q=structuredClone(p);mutate(q);assert.equal(compareQgc(a,JSON.stringify(q)).equal,false);}});
test('Actual QGC AMSL and geofence block in isolation even if Home is made matching in test memory',async()=>{const q=JSON.parse(await readFile('app/fixtures/qgc/desktop/qgc-created-amsl-fence.plan','utf8'));assert.ok(q.mission.items.some(i=>i.frame===0&&i.AltitudeMode===2));q.mission.plannedHomePosition=[10.854,106.807,10];assert.throws(()=>compileQgc(makeQgcRequest(JSON.stringify(q))),/Geofence/);q.geoFence.circles=[];q.mission.items[0].params[4]=10.854;q.mission.items[0].params[5]=106.807;assert.throws(()=>compileQgc(makeQgcRequest(JSON.stringify(q))),/relative-home/);});
