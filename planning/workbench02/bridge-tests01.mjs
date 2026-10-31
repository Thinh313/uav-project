import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {NativeChannel,NativeStorage,shaBytes} from '../../pilot/workbench02/native-bridge.mjs';
import {MockProvider} from '../../pilot/workbench02/mock-provider.mjs';
import {projectUI,projectHTML} from '../../pilot/workbench02/project-ui.mjs';
import {prepareSITL,sitlFixture} from '../../pilot/workbench02/sitl-contract.mjs';
import {createPlan,ENERGY} from '../../pilot/workbench01/core.mjs';
import {parseKml} from '../../pilot/workbench01/kml.mjs';
const root=new URL('../../',import.meta.url), results=[],sha=s=>createHash('sha256').update(s).digest('hex');
const free=()=>{const s=fs.statfsSync(root);return s.bavail*s.bsize;};
const floor=()=>assert.ok(free()>=20*2**30+8*2**20,'PHYSICAL_FLOOR_PLUS_8_MIB');
floor();
async function test(name,fn){try{await fn();results.push({name,status:'PASS'});}catch(e){results.push({name,status:'FAIL',error:String(e.stack)});}}
function harness(platform='MOCK_NATIVE_BRIDGE'){
 const jobs=new Map();let timer=0,q,calls=0,observed=0;
 const env={format:'aeris-native-workbench02',platform,instance:'test-instance',session:'test-session-00000001',foreground:true};
 const provider={environment:()=>JSON.stringify(env),request:raw=>{calls++;q=JSON.parse(raw);}};
 const channel=new NativeChannel(()=>provider,{timers:{setTimeout:fn=>{jobs.set(++timer,fn);return timer;},clearTimeout:id=>jobs.delete(id)}});
 return {channel,storage:new NativeStorage(channel),env,provider,jobs,async dispatched(){const target=++observed,deadline=performance.now()+2000;while(calls<target){assert.ok(performance.now()<deadline,'MOCK_REQUEST_NOT_OBSERVED');await new Promise(resolve=>setImmediate(resolve));}},get calls(){return calls;},get q(){return q;},reply(result,overrides={}){return channel.reply({...q,ok:true,result:{platform,authorityRestored:false,...result},...overrides});},expire(){for(const fn of [...jobs.values()])fn();}};
}
const body='{"workspace":"Tiếng Việt – mock only"}',digest=await shaBytes(body),head='a'.repeat(64);
await test('MOCK save, load after new channel, CAS and explicit export remain mock',async()=>{
 const p=new MockProvider(async s=>{assert.equal(s,body);});let c=new NativeChannel(()=>p);p.receiver=r=>c.reply(r);let s=new NativeStorage(c);
 assert.equal((await s.load()).status,'EMPTY');assert.equal((await s.save(body)).platform,'MOCK_NATIVE_BRIDGE');
 const snapshot={body:p.body,head:p.head};c.close();const p2=new MockProvider(async()=>{},snapshot);c=new NativeChannel(()=>p2);p2.receiver=r=>c.reply(r);s=new NativeStorage(c);
 assert.equal((await s.load()).body,body);const receipt=await s.export(body);assert.equal(receipt.status,'MOCK_SAF_READBACK_ONLY');assert.equal(receipt.authorityRestored,false);
 p2.head='b'.repeat(64);const old=s.head;await assert.rejects(s.save(body),/MOCK_CAS/);assert.equal(s.head,old);c.close();
});
for(const platform of ['MOCK_NATIVE_BRIDGE','ANDROID']){
 await test(`${platform} rejects reply claiming other platform`,async()=>{const h=harness(platform),p=h.channel.call('load');h.reply({platform:platform==='ANDROID'?'MOCK_NATIVE_BRIDGE':'ANDROID'});await assert.rejects(p,/REFUSED/);assert.equal(h.channel.pending.size,0);});
 await test(`${platform} accepts only its export evidence label`,async()=>{const h=harness(platform),p=h.storage.export(body);await h.dispatched();h.reply({status:platform==='ANDROID'?'SAF_READBACK_VERIFIED':'MOCK_SAF_READBACK_ONLY',bodySha256:digest,bytes:Buffer.byteLength(body)});assert.equal((await p).platform,platform);
 const bad=h.storage.export(body);await h.dispatched();h.reply({status:platform==='ANDROID'?'MOCK_SAF_READBACK_ONLY':'SAF_READBACK_VERIFIED',bodySha256:digest,bytes:Buffer.byteLength(body)});await assert.rejects(bad,/NATIVE_SAF_READBACK/);});
}
await test('No authority is restored by successful reply',async()=>{for(const v of [true,undefined,null]){const h=harness(),p=h.channel.call('load');h.reply({authorityRestored:v});await assert.rejects(p,/REFUSED/);}});
await test('EMPTY requires exact ROOT token and null body',async()=>{for(const r of [{head:'not-a-sha',body:null},{head:head,body:null},{head:'ROOT',body:body}]){const h=harness(),p=h.storage.load();h.reply({status:'EMPTY',...r});await assert.rejects(p,/NATIVE_HEAD/);assert.equal(h.storage.head,null);}});
await test('COMMITTED load requires valid head and body',async()=>{for(const r of [{head:'ROOT',body},{head:'A'.repeat(64),body},{head,body:null},{head:42,body}]){const h=harness(),p=h.storage.load();h.reply({status:'COMMITTED',bodySha256:digest,...r});await assert.rejects(p,/NATIVE_HEAD/);assert.equal(h.storage.head,null);}});
await test('Load rejects mismatched body SHA without advancing head',async()=>{const h=harness(),p=h.storage.load();h.reply({status:'COMMITTED',head,body,bodySha256:'0'.repeat(64)});await assert.rejects(p,/NATIVE_LOAD_SHA/);assert.equal(h.storage.head,null);});
await test('Pending or corrupt store cannot be represented as loaded',async()=>{const h=harness(),p=h.storage.load();h.reply({status:'PENDING',head,body});await assert.rejects(p,/READONLY/);});
await test('Valid committed load preserves UTF-8 SHA',async()=>{const h=harness(),p=h.storage.load();h.reply({status:'COMMITTED',head,body,bodySha256:digest});assert.equal((await p).body,body);assert.equal(h.storage.head,head);});
await test('Save rejects malformed commit token, stale previous head and wrong SHA',async()=>{for(const bad of [{head:'ROOT'},{previousHead:'b'.repeat(64)},{bodySha256:'b'.repeat(64)}]){const h=harness();h.storage.head='ROOT';const p=h.storage.save(body);await h.dispatched();h.reply({status:'COMMITTED',head,previousHead:'ROOT',bodySha256:digest,...bad});await assert.rejects(p,/COMMIT_RECEIPT/);assert.equal(h.storage.head,'ROOT');}});
await test('Valid save receipt advances head only after acknowledgement',async()=>{const h=harness();h.storage.head='ROOT';const p=h.storage.save(body);await h.dispatched();assert.equal(h.storage.head,'ROOT');h.reply({status:'COMMITTED',head,previousHead:'ROOT',bodySha256:digest});await p;assert.equal(h.storage.head,head);});
await test('Save requires load and enforces UTF-8 body bound before dispatch',async()=>{const h=harness();await assert.rejects(h.storage.save(body),/LOAD_BEFORE_SAVE/);h.storage.head='ROOT';await assert.rejects(h.storage.save('ấ'.repeat(700000)),/BODY_BOUND/);assert.equal(h.calls,0);});
await test('ID, instance, session, action and version correlation cannot settle pending',async()=>{const h=harness(),p=h.channel.call('load');for(const override of [{id:'unknown'},{instance:'other'},{session:'old-session'},{action:'save'},{version:2}])assert.equal(h.reply({},override),false);assert.equal(h.channel.pending.size,1);h.reply({status:'EMPTY',head:'ROOT',body:null});await p;});
await test('Timeout is unknown, no retry and late reply ignored',async()=>{const h=harness(),p=h.channel.call('load');h.expire();await assert.rejects(p,/UNKNOWN_TIMEOUT_NO_RETRY/);assert.equal(h.calls,1);assert.equal(h.reply({}),false);});
await test('Foreground loss cancels pending save without success',async()=>{const h=harness(),p=h.channel.call('save');h.channel.background();await assert.rejects(p,/FOREGROUND_LOST/);assert.equal(h.reply({}),false);});
await test('Owned picker survives own pause but save never does',async()=>{const h=harness(),p=h.channel.call('pick-json');h.channel.background(true);assert.equal(h.channel.pending.size,1);h.reply({status:'PICK_READ_VERIFIED'});await p;const save=h.channel.call('save');h.channel.background(true);await assert.rejects(save,/FOREGROUND_LOST/);});
await test('Busy has no queue and closed/background environment cannot dispatch',async()=>{const h=harness(),p=h.channel.call('load');assert.throws(()=>h.channel.call('save'),/BUSY_NO_QUEUE/);h.reply({});await p;h.env.foreground=false;assert.throws(()=>h.channel.call('load'),/FOREGROUND_REQUIRED/);h.channel.close();assert.throws(()=>h.channel.call('load'),/CLOSED/);assert.equal(h.calls,1);});
await test('Synchronous native provider failure clears pending timer',async()=>{const h=harness();h.provider.request=()=>{throw Error('NATIVE_IO_FAULT');};await assert.rejects(h.channel.call('load'),/NATIVE_IO_FAULT/);assert.equal(h.channel.pending.size,0);assert.equal(h.jobs.size,0);});
await test('Native error and cancelled picker cannot return success',async()=>{const h=harness(),p=h.channel.call('pick-json');h.reply(null,{ok:false,error:'SAF_CANCELLED_NO_SUCCESS'});await assert.rejects(p,/CANCELLED/);});
await test('Pick verifies hash and KML byte limit',async()=>{const h=harness(),ok=h.storage.pick('kml');h.reply({status:'PICK_READ_VERIFIED',body,bodySha256:digest});assert.equal(await ok,body);const bad=h.storage.pick('kml'),large='x'.repeat(262145);h.reply({status:'PICK_READ_VERIFIED',body:large,bodySha256:await shaBytes(large)});await assert.rejects(bad,/PICK_SHA_BOUND/);});
await test('SAF short readback or wrong SHA cannot succeed',async()=>{for(const bad of [{bytes:1},{bodySha256:'0'.repeat(64)}]){const h=harness(),p=h.storage.export(body);await h.dispatched();h.reply({status:'MOCK_SAF_READBACK_ONLY',bytes:Buffer.byteLength(body),bodySha256:digest,...bad});await assert.rejects(p,/SAF_READBACK/);}});
await test('Pinned UI projection inverse and generated module syntax',async()=>{const p=projectUI();assert.equal(p.inverseExact,true);assert.equal(p.replacements,8);assert.ok(!p.source.includes('localStorage'));assert.match(p.source,/nativeStorage\.save/);const syntax=spawnSync(process.execPath,['--check','--input-type=module'],{input:p.source,encoding:'utf8'});assert.equal(syntax.status,0,syntax.stderr);assert.ok(!projectHTML(false).includes('src="/mock-native.mjs"'));assert.ok(projectHTML(true).includes('src="/mock-native.mjs"'));});
await test('Synthetic mission preparation binds model and refuses bad Home/datum/camera/range',async()=>{const input={...sitlFixture(),energy:structuredClone(ENERGY)};input.options.datumAcknowledged=true;const doc=await parseKml(input.kml),plan=createPlan(doc,input),x=await prepareSITL(plan,{confirmSyntheticHomeAmsl10:true});assert.equal(x.flightDispatch,false);assert.equal(x.operational,false);assert.equal(x.binding.workbenchSha256,plan.sha256);await assert.rejects(prepareSITL(plan),/HOME_AMSL10/);for(const mutate of [d=>d.home.lat+=.001,d=>d.camera.focalLengthMm+=1,d=>d.options.altitudeAglM=60,d=>d.options.datumAcknowledged=false]){const d=structuredClone(input);mutate(d);await assert.rejects(async()=>prepareSITL(createPlan(doc,d),{confirmSyntheticHomeAmsl10:true}));}});
const report={at:new Date().toISOString(),status:results.every(r=>r.status==='PASS')?'PASS':'FAIL',provenance:'NODE_MOCK_AND_STATIC_PROJECTION_NOT_ANDROID_NOT_SAF_NOT_SITL',cases:results.length,passed:results.filter(r=>r.status==='PASS').length,results,bridgeSha256:sha(fs.readFileSync(new URL('pilot/workbench02/native-bridge.mjs',root))),freeBytes:free(),android:'NOT_RUN',sitl:'NOT_RUN',apkBuilt:false};
const attempt=process.argv[2]??'01';assert.match(attempt,/^[0-9]{2}$/);
floor();fs.writeFileSync(new URL('evidence/workbench02/bridge-mock'+attempt+'.json',root),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report,null,2));if(report.status!=='PASS')process.exitCode=1;
