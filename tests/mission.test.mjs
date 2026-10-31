import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DEFAULT_SETTINGS, planSurvey, missionPackage, importMission } from '../app/core/mission.mjs';
const fixtures = JSON.parse(readFileSync(new URL('../app/fixtures/golden-surveys.json', import.meta.url)));
const near = (a,b) => assert.ok(Math.abs(a-b) < 1e-8, `${a} != ${b}`);
for (const fixture of fixtures.cases) test(`REQ-003 golden: ${fixture.id}`, () => {
  const p = planSurvey(fixture.settings);
  for (const [key,value] of Object.entries(fixture.expected)) near(p[key],value);
});
test('REQ-003 coverage and spacing properties over 36 independent input combinations', () => {
  for (const width of [30,200,360,800]) for (const height of [30,100,220]) for (const overlap of [0,50,80]) {
    const p=planSurvey({...DEFAULT_SETTINGS,width,height,sideOverlap:overlap,frontOverlap:overlap});
    const x=p.transects.map(t=>t.start.x);
    assert.ok(x[0]-p.footprintWidth/2<=1e-8);
    assert.ok(x.at(-1)+p.footprintWidth/2>=width-1e-8);
    assert.ok(p.lineSpacing<=p.nominalLineSpacing+1e-8);
    assert.ok(p.triggerSpacing<=p.nominalTriggerSpacing+1e-8);
    assert.ok(p.waypoints.every(q=>q.x>=0&&q.x<=width&&q.y>=0&&q.y<=height));
    assert.equal(p.transects.every((t,i)=>i%2?t.start.y===height:t.start.y===0),true);
    assert.equal(p.photoCount,p.lineCount*p.shotsPerLine);
  }
});
test('REQ-003 use cruise speed and square metres without area factor drift', () => {
  const slow=planSurvey(DEFAULT_SETTINGS),fast=planSurvey({...DEFAULT_SETTINGS,speed:12});
  assert.equal(slow.area,360*220);near(slow.nominalSeconds,fast.nominalSeconds*2);near(slow.distance,fast.distance);
});
test('REQ-004 non-divisible shot spacing is used for camera interval feasibility', () => {
  const p=planSurvey({...fixtures.cases[2].settings,minInterval:8});
  assert.equal(p.feasible,false);assert.equal(p.warnings.length,1);
  assert.throws(()=>missionPackage(p.settings),/chu kỳ camera/);
});
test('REQ-004 exact camera interval boundary is accepted', () => {
  const p=planSurvey({...fixtures.cases[0].settings,minInterval:10});assert.equal(p.feasible,true);
});
test('REQ-004 reject nonfinite values, strings, zero lens, excess overlap and unknown fields', () => {
  for (const patch of [{width:NaN},{altitude:Infinity},{speed:'6'},{focalLength:0},{sideOverlap:100},{imageWidth:1.5},{arbitrary:'ignored'}])
    assert.throws(()=>planSurvey({...DEFAULT_SETTINGS,...patch}));
  assert.throws(()=>planSurvey(null));assert.throws(()=>planSurvey([]));
});
test('REQ-004 bounded mission prevents pathological allocation/shot counts', () => {
  assert.throws(()=>planSurvey({...DEFAULT_SETTINGS,width:3000,height:3000,altitude:5,sensorWidth:1,sensorHeight:1,focalLength:200,sideOverlap:95,frontOverlap:95}),/giới hạn/);
});
test('REQ-005 semantic round-trip preserves fixture settings and derived result', () => {
  for (const f of fixtures.cases) {
    const pkg=missionPackage(f.settings),restored=importMission(JSON.stringify(pkg));
    assert.deepEqual(restored,pkg);assert.deepEqual(planSurvey(restored.settings),planSurvey(f.settings));
  }
});
test('REQ-005 generation and validation do not mutate caller input', () => {
  const s={...DEFAULT_SETTINGS},before=JSON.stringify(s);const p=planSurvey(s);p.settings.width=400;
  assert.equal(JSON.stringify(s),before);
});
test('REQ-005 refuse unsupported schema, .plan, operational flag and injected derived fields', () => {
  const p=missionPackage(DEFAULT_SETTINGS);
  for (const patch of [{version:2},{format:'Plan'},{operational:true},{model:'terrain-v1'},{photoCount:999}]) assert.throws(()=>importMission(JSON.stringify({...p,...patch})));
  assert.throws(()=>importMission('{'));assert.throws(()=>importMission('null'));assert.throws(()=>importMission('x'.repeat(256*1024+1)));
});
