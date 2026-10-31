import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {MockFramer45,encodeMockAction} from './framer.mjs';
import {HeraMCU45,replay} from './model.mjs';
import {driver,MockPeer45,mockConfig} from './fixtures.mjs';
import {clone,digest,stable,encodePhysicalMCU,GROUPS,POLICY} from './schema.mjs';
import {admission,receipt} from './io.mjs';
import {existsSync} from 'node:fs';

admission();const results=[];let failed=false;
function test(name,fn){admission();try{fn();results.push({name,pass:true});}catch(e){failed=true;results.push({name,pass:false,error:e.stack});}}
const corpusName=process.argv[2]??'corpus5.json',corpus=JSON.parse(await readFile('evidence/heramcu45/'+corpusName,'utf8'));
test('serialized finalcorpus all76 semantic replay after JSON roundtrip',()=>{assert.equal(corpus.cases.length,76);for(const c of corpus.cases){assert.equal(c.pass,true);assert.equal(replay(c.record,c.record.seal.bodySha256).status,'PASS_MOCK_REPLAY_ONLY');}});
const positive=corpus.cases.find(c=>c.name==='nine calibration results +save+readback').record;
for(const pattern of [[1],[2,3,5,7,11],[4096],[17,8191,61]])test('full workflow mockstream chunkpattern '+pattern,()=>{
 const f=new MockFramer45(),m=new HeraMCU45(positive.context),stream=Buffer.concat(positive.events.map(e=>encodeMockAction(e.body.input)));let pos=0,n=0;
 while(pos<stream.length){const size=pattern[n++%pattern.length];for(const action of f.push(stream.subarray(pos,pos+size)))m.process(action);pos+=size;}
 f.close();assert.equal(stable(m.export()),stable(positive));assert.equal(f.snapshot().pendingHex,'');assert.equal(f.frames,positive.events.length);
});
const action={kind:'TICK',t:1,data:{label:'Việt Nam 😀'}},encoded=encodeMockAction(action);
test('every split boundary including UTF8 preserves action',()=>{for(let n=0;n<=encoded.length;n++){const f=new MockFramer45();const out=[...f.push(encoded.subarray(0,n)),...f.push(encoded.subarray(n))];assert.deepEqual(out,[action]);f.close();}});
test('coalesced mock frames preserve order exactly',()=>{const f=new MockFramer45();assert.deepEqual(f.push(Buffer.concat([encoded,encoded,encoded])),[action,action,action]);f.close();});
test('incomplete close retains pendinghex and terminal',()=>{const f=new MockFramer45();f.push(encoded.subarray(0,-1));assert.throws(()=>f.close(),/INCOMPLETE/);assert.equal(f.snapshot().pendingHex,encoded.subarray(0,-1).toString('hex'));assert.throws(()=>f.push(Buffer.from('\n')),/TERMINAL/);});
test('closed framer cannot silently accept newepoch',()=>{const f=new MockFramer45();f.push(encoded);f.close();assert.throws(()=>f.push(encoded),/TERMINAL/);assert.throws(()=>f.close(),/TERMINAL/);});
for(const [name,b] of [['invalidUTF8',Buffer.from([255,10])],['malformedJSON',Buffer.from('{oops}\n')],['emptyline',Buffer.from('\n')],['wrongcarrier',Buffer.from(JSON.stringify({format:'MAVLINK',version:1,action})+'\n')],['extrafield',Buffer.from(JSON.stringify({format:'MOCK_NDJSON_HERAMCU45',version:1,action,operational:true})+'\n')],['wrongversion',Buffer.from(JSON.stringify({format:'MOCK_NDJSON_HERAMCU45',version:2,action})+'\n')]])test('framer refuses '+name,()=>{const f=new MockFramer45();assert.throws(()=>f.push(b));assert.equal(f.invalid,true);assert.throws(()=>f.push(encoded),/TERMINAL/);});
test('single oversized chunk rejected bounded memory',()=>{const f=new MockFramer45();assert.throws(()=>f.push(Buffer.alloc(POLICY.framerBufferBytes+1)),/CHUNK_BOUND/);assert.equal(f.buffer.length,0);});
test('incomplete mockenvelope >=8192 rejected immediately',()=>{const f=new MockFramer45();assert.throws(()=>f.push(Buffer.alloc(POLICY.envelopeBytes,32)),/ENVELOPE_BOUND/);assert.equal(f.buffer.length,POLICY.envelopeBytes);});
test('mock envelope with newline oversized refused',()=>{const f=new MockFramer45();assert.throws(()=>f.push(Buffer.concat([Buffer.alloc(POLICY.envelopeBytes,32),Buffer.from('\n')])),/ENVELOPE_BOUND/);});
test('encode oversized action refuses before allocation totransport',()=>assert.throws(()=>encodeMockAction({...action,data:{x:'x'.repeat(8192)}}),/ENVELOPE_BOUND/));
test('MAVLink-shaped bytes cannot be accepted as mockcarrier',()=>{const f=new MockFramer45();assert.throws(()=>{f.push(Buffer.from([253,0,0,0,0,1,1,0,0,0,10]));});});
for(const value of [null,{},'known dialect',new Uint8Array([1])])test('physicalcodec remains unconditionally blocked '+String(value),()=>assert.throws(()=>encodePhysicalMCU(value),/WIRE_BLOCKED/));

function rehash(r){let prev=null;for(const event of r.events){event.body.previousSha256=prev;event.sha256=digest(event.body);prev=event.sha256;}const{seal,...body}=r;r.seal={eventCount:r.events.length,tailSha256:prev,bodySha256:digest(body)};return r;}
const mutations=[
 ['finalfalseREADY',r=>r.summary.state='PHYSICAL_READY'],['physicalflag',r=>r.physicalExecutionProven=true],['restoreauthority',r=>r.authorityRestorable=true],['wireverified',r=>r.wireVerified=true],['wrongcontract',r=>r.contractSha256='0'.repeat(64)],['wrongcontext',r=>r.context.boot+='foreign'],['forgedfirstresult',r=>r.events[0].body.result={accepted:true}],['forgedsnapshot',r=>r.events[0].body.snapshot.state='MOCK_READY'],['ackascalibrationresult',r=>{const e=r.events.find(e=>e.body.input.kind==='RX'&&e.body.input.data.kind==='CALIBRATION_RESULT');e.body.input.data.kind='ACK';}],['removedsourceevent',r=>r.events.splice(2,1)],['wrongclock',r=>r.events[2].body.input.t=0],['dropfinalconfigreadback',r=>r.events.splice(r.events.findLastIndex(e=>e.body.input.kind==='RX'&&e.body.input.data.kind==='CONFIG'),1)],['wrongidentity',r=>r.events.find(e=>e.body.input.kind==='RX'&&e.body.input.data.kind==='INFO').body.input.data.data.uuid='0'.repeat(32)]
];
for(const [name,mutate] of mutations)test('rehash cannot promote altered semantics '+name,()=>{const r=clone(positive);mutate(r);rehash(r);assert.throws(()=>replay(r));});
test('historical replay yields no reusable MCU instance/authority',()=>{const out=replay(positive);assert.equal(out.authorityRestorable,false);assert.equal(out.summary.operational,false);assert.equal(typeof out.process,'undefined');assert.equal(out.summary.wireVerified,false);});
test('truncation with retained seal rejected',()=>{const r=clone(positive);r.events.pop();assert.throws(()=>replay(r),/SEAL/);});
test('wrong expected external digest rejects even valid logicalrecord',()=>assert.throws(()=>replay(positive,'0'.repeat(64)),/SEAL/));
test('valid re-sealed prefix is distinct history and fails original digest',()=>{const r=clone(positive);r.events.pop();rehash(r);assert.equal(replay(r).status,'PASS_MOCK_REPLAY_ONLY');assert.throws(()=>replay(r,positive.seal.bodySha256),/SEAL/);});

let bootEvidence;
test('calibration changedrawranges persist across mockpeer reboot with new handshake',()=>{
 const peer=new MockPeer45(),d=driver('cal-persist-a',peer);d.bootstrap();const q=d.doAction('BEGIN_CALIBRATION').body.result;
 for(let i=0;i<9;i++){d.ack('CALIBRATE',q.transaction,'IN_PROGRESS',i,50);d.ack('CALIBRATE',q.transaction,'ACCEPTED',i,100);const result=d.rx('CALIBRATION_RESULT',{step:i,axes:GROUPS[i][1].map(axis=>({axis,samples:[100,2100,4000]})),pressedMask:i===8?32767:0},q.transaction);assert.equal(result.body.error,null);}
 assert.equal(d.model.state,'SAVE_REQUIRED');peer.apply(d.model.candidate);let request=d.doAction('SAVE').body.result;peer.save();d.ack('SAVE',request.transaction);request=d.doAction('READ_CONFIG').body.result;d.rx('CONFIG',peer.applied,request.transaction);assert.equal(d.model.configuration.axes[0].trim,2100);assert.equal(d.model.savedReadbackMock,true);const expected=digest(d.model.configuration);d.doAction('REBOOT');peer.reboot();const x=driver('cal-persist-b',peer);x.bootstrap();assert.equal(digest(x.model.configuration),expected);assert.equal(x.model.configuration.axes[0].trim,2100);assert.equal(x.model.savedReadbackMock,false);assert.equal(x.model.persistenceAcrossBoot,false);assert.ok(x.doAction('PREVIEW',{rawInputs:{6:2100,7:2100,10:2100,11:2100},port:'OUTPUT_PORT_1'}).body.error);replay(d.model.export());replay(x.model.export());bootEvidence={prior:d.model.export(),fresh:x.model.export(),comparison:{expectedConfigSha256:expected,currentConfigSha256:digest(x.model.configuration),equal:true},scope:'External comparison of two mockrecords; noauthorityhydration or deviceflash durability proof'};
});
test('foreign highseq cannot poison next valid reply',()=>{const d=driver('high-seq');d.doAction('CONNECT');const foreign=d.peer.info(d.ctx);foreign.target+='wrong';foreign.sequence=4294967295;d.doAction('RX',foreign);d.rx('INFO',{uuid:'1234567890abcdef1234567890abcdef',dev:'deadbeef',ver:'00000003'});assert.equal(d.model.state,'DISCOVERED');});
test('mapping ACK does not mutate stored peer before explicit save',()=>{const peer=new MockPeer45(),d=driver('unsaved',peer);d.bootstrap();const original=digest(peer.stored),c=mockConfig();c.revision='changed-not-saved';const q=d.doAction('APPLY_MAPPING',c).body.result;peer.apply(c);d.ack('APPLY_MAPPING',q.transaction);assert.equal(digest(peer.stored),original);d.doAction('DISCONNECT');peer.reboot();assert.equal(digest(peer.applied),original);});
for(const kind of ['BEGIN_CALIBRATION','APPLY_MAPPING'])test('new mutation clears historicalsave flag '+kind,()=>{const d=driver('flag-'+kind);d.bootstrap();let q=d.doAction('APPLY_MAPPING',mockConfig()).body.result;d.ack('APPLY_MAPPING',q.transaction);q=d.doAction('SAVE').body.result;d.ack('SAVE',q.transaction);q=d.doAction('READ_CONFIG').body.result;d.rx('CONFIG',mockConfig(),q.transaction);assert.equal(d.model.savedReadbackMock,true);d.doAction(kind,kind==='APPLY_MAPPING'?mockConfig():{});assert.equal(d.model.savedReadbackMock,false);assert.equal(d.model.sources.size,0);replay(d.model.export());});
for(const t of [-1,0.1,Number.MAX_SAFE_INTEGER+1])test('invalidhost clock revokes ready '+t,()=>{const d=driver('clock'+t);d.bootstrap();d.sources();d.doAction('TICK',{},t);assert.equal(d.model.state,'INVALIDATED');assert.equal(d.model.sources.size,0);replay(d.model.export());});

test('RF namespace cannot be confused with RC output port',()=>{const d=driver('rf-distinct');d.bootstrap();d.sources();const e=d.rx('RF',{port:'OUTPUT_PORT_1',status:'CONNECTED',rssiPercent:60});assert.ok(e.body.error);assert.equal(d.model.state,'INVALIDATED');});
let n=1;while(existsSync(`evidence/heramcu45/qa${n}.json`))n++;
await receipt(`qa${n}.json`,{status:failed?'FAIL':'PASS',checks:results.length,passed:results.filter(r=>r.pass).length,results,corpus:corpusName,scope:'Actualhost logicalmock NDJSON; noMAVLink/USB/hardwaretransport'});
if(bootEvidence)await receipt(`mock-reboot-readback${n}.json`,bootEvidence,{compact:true});
console.log(JSON.stringify({status:failed?'FAIL':'PASS',checks:results.length,failures:results.filter(r=>!r.pass)}));assert.equal(failed,false);
