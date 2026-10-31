import test from 'node:test';import assert from 'node:assert/strict';
import{Journal,PORTS,TARGET_BUS,validateGcs}from'./bridge.mjs';import{encode,hex}from'../protocol22/wire.mjs';
const context={sessionId:'aproute28',generation:1,configSha256:'a'.repeat(64)};
const make=(p={},meta={})=>{const fields={target_system:42,target_component:100,command:531,param1:2,param2:40,param4:NaN,...p};const bytes=encode(76,fields,{system:255,component:190,...meta});return{bytes,record:{context,rawHex:hex(bytes),targetSystem:fields.target_system,targetComponent:fields.target_component,command:fields.command}};};
test('one GCS port and two fixed separate AP serial buses',()=>{assert.deepEqual(PORTS,{gcs:5774,busA:5775,busB:5776});assert.ok(Object.isFrozen(PORTS));assert.ok(Object.isFrozen(TARGET_BUS));assert.equal(TARGET_BUS[100],'busA');assert.equal(TARGET_BUS[102],'busB');assert.equal(TARGET_BUS[154],'busA');});
test('typed exact camera percent profile admitted',()=>{const x=make();assert.equal(validateGcs(x.bytes,x.record,context).fields.command,531);});
for(const[name,p,meta]of[
 ['arm',{command:400},{}],['mode',{command:176},{}],['AP component1',{target_component:1},{}],['broadcastsys',{target_system:0},{}],['broadcastcomponent',{target_component:0},{}],['foreignsys',{target_system:43},{}],['unknowncomponent',{target_component:110},{}],['retryconfirmation',{confirmation:1},{}],['unknownsender',{}, {system:254}],['unknownsendercomponent',{}, {component:191}],['NaNzoom',{param2:NaN},{}],['overscale',{param2:101},{}],['injecteddevice',{param3:2},{}],['hiddenparameter',{param5:1},{}],['hiddenfocusrate',{param4:4},{}],['discoveryGPS',{command:512,param1:33,param4:0},{}],['discoveryhidden',{command:512,param1:259,param4:0,param2:1},{}]
])test('refuse '+name,()=>{const x=make(p,meta);assert.throws(()=>validateGcs(x.bytes,x.record,context));});
test('wrong reviewed target refused despite matching raw',()=>{const x=make();assert.throws(()=>validateGcs(x.bytes,{...x.record,targetComponent:101},context));});
test('old generation refused',()=>{const x=make();assert.throws(()=>validateGcs(x.bytes,x.record,{...context,generation:2}));});
test('corrupted command CRC refused',()=>{const x=make();x.bytes[12]^=1;assert.throws(()=>validateGcs(x.bytes,{...x.record,rawHex:hex(x.bytes)},context));});
test('concatenated valid commands refused',()=>{const x=make(),b=new Uint8Array(x.bytes.length*2);b.set(x.bytes);b.set(x.bytes,x.bytes.length);assert.throws(()=>validateGcs(b,{...x.record,rawHex:hex(b)},context));});
test('truncated command refused',()=>{const x=make(),b=x.bytes.subarray(0,-1);assert.throws(()=>validateGcs(b,{...x.record,rawHex:hex(b)},context));});
test('signed unsupported frame refused',()=>{const x=make();x.bytes[2]=1;assert.throws(()=>validateGcs(x.bytes,x.record,context));});
test('gimbal direct angle profile/device2 admitted',()=>{const x=make({target_component:154,command:1000,param1:-20,param2:10,param3:NaN,param4:NaN,param7:2});assert.equal(validateGcs(x.bytes,x.record,context).fields.param7,2);});
test('gimbal hidden rate rejected',()=>{const x=make({target_component:154,command:1000,param1:-20,param2:10,param3:0,param4:NaN,param7:2});assert.throws(()=>validateGcs(x.bytes,x.record,context));});
test('raw row exhaustion retains original rows and declares failure',()=>{const j=new Journal({maxRows:2});j.add('RX',{rawHex:'ff'});j.add('TX');assert.throws(()=>j.add('OVERFLOW'));assert.equal(j.rows.length,2);assert.equal(j.failure,'RAW_EVIDENCE_BOUND');assert.deepEqual(j.rows.map(x=>x.n),[1,2]);});
test('raw byte exhaustion never appends partial row',()=>{const j=new Journal({maxBytes:200});j.add('FIRST');assert.throws(()=>j.add('RX',{rawHex:'ff'.repeat(200)}));assert.equal(j.rows.length,1);assert.equal(j.failure,'RAW_EVIDENCE_BOUND');});
for(const options of[{maxRows:0},{maxRows:4097},{maxBytes:0},{maxBytes:3*1024*1024}])test('reject unbounded journal '+JSON.stringify(options),()=>assert.throws(()=>new Journal(options)));
