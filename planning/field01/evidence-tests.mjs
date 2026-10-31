/** FIELD01 Builder self-checks: actual async local fs, synthetic bytes, independent Python receiver. */
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { execFile } from 'node:child_process';
import { Store01 } from '../../pilot/field01/evidence/store01.mjs';
import { fixture } from '../../pilot/field01/evidence/fixtures.mjs';
import { jsonBytes,sha256,makeTar } from '../../pilot/field01/evidence/schema.mjs';
const run=promisify(execFile), repo=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const runId=new Date().toISOString().replace(/[:.]/g,'-');
const root=join(repo,'evidence/field01',`evidence-tests-${runId}`);
await fs.mkdir(root,{recursive:true});
const results=[];
async function test(name,fn){const start=performance.now();try{const detail=await fn();results.push({name,status:'PASS',elapsedMs:performance.now()-start,...detail});}
  catch(e){results.push({name,status:'FAIL',error:e.stack,elapsedMs:performance.now()-start});}}
const storeAt=name=>join(root,name);
const receive=async(path,state='receiver',receiver='field01-evaluator',sender='aeris-field01-synthetic')=>{
  let output;try{output=await run('python3',[join(repo,'pilot/field01/evidence/receiver.py'),path,'--state',storeAt(state),'--receiver',receiver,'--sender',sender]);}
  catch(e){output=e;}
  return JSON.parse(output.stdout.trim());
};
let tar, exported, original;

await test('serial async WAL hash chain + stale head CAS + caller snapshot + restart no authority',async()=>{
  const store=await Store01({root:storeAt('nominal')});
  try {
    const payload={workspace:{name:'before',modelSha256:'1'.repeat(64)}};
    const p=store.append('WORKSPACE_SAVED',payload);payload.workspace.name='mutated';await p;
    assert.equal(store.records()[0].data.workspace.name,'before');
    const before=store.snapshot().head;
    const records=await Promise.all(Array.from({length:12},(_,i)=>store.append('OPERATOR_NOTE',{i})));
    assert.deepEqual(records.map(r=>r.seq),Array.from({length:12},(_,i)=>i+2));
    await assert.rejects(store.append('OPERATOR_NOTE',{}, {expectedHead:before}),/STALE_EXPECTED_HEAD/);
    await assert.rejects(store.append('CAPTURE_COMMITTED',{}),/RECORD_KIND/);
    const recs=store.records();recs[0].data.workspace.name='external';assert.equal(store.records()[0].data.workspace.name,'before');
    assert.equal(store.snapshot().authority,'NONE');
  }finally{await store.close();}
  const again=await Store01({root:storeAt('nominal')});
  try{assert.equal(again.records().length,13);assert.equal(again.snapshot().authority,'NONE');assert.equal(again.snapshot().readOnly,false);
    const r=await again.append('RESTART_OBSERVATION',{restoredAuthority:'NONE'});assert.equal(r.seq,14);
  }finally{await again.close();}
});

await test('capture immutable bytes + sidecar MSL/reference-only + durable handoff TAR3',async()=>{
  const store=await Store01({root:storeAt('captures')});
  try {
    const f=fixture();original=Buffer.from(f.originalBytes);
    const promise=store.commit('capture-001',f);f.originalBytes[50]^=1;f.sidecar.context.flightRun='changed';
    const receipt=await promise;assert.equal(receipt.status,'COMMITTED');assert.equal(receipt.authority,'NONE');
    const read=await store.read('capture-001');assert.deepEqual(read.originalBytes,original);
    assert.equal(read.sidecar.position.datum,'MSL');assert.equal(read.sidecar.position.sensorTimeUncertaintyMs,null);
    assert.equal(read.sidecar.position.method,'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC');
    assert.equal(read.sidecar.position.qualifiedForSurvey,false);assert.equal(read.sidecar.context.flightRun,'fixture-flight');
    assert.equal(receipt.originalSha256,sha256(original));assert.equal((await store.review()).rows[0].state,'COMMITTED');
    await assert.rejects(store.commit('capture-001',fixture()),/CAPTURE_REPLAY/);
    exported=await store.handoff('capture-001',{transferId:'transfer-001',senderId:'aeris-field01-synthetic',receiverId:'field01-evaluator'});
    assert.equal(exported.receipt.status,'EXPORTED');tar=exported.bytes;
    assert.equal(exported.receipt.tarSha256,sha256(tar));
    await assert.rejects(store.handoff('capture-001',{transferId:'transfer-001',senderId:'aeris-field01-synthetic',receiverId:'field01-evaluator'}),/TRANSFER_REPLAY/);
    await fs.writeFile(join(root,'package.tar'),tar);
    return {originalSha256:sha256(original),tarSha256:sha256(tar),actualImages:0};
  }finally{await store.close();}
});

await test('independent Python receiver accepts exact bytes, restart refuses replay and restores no authority',async()=>{
  const p=join(root,'package.tar');
  const wrong=await receive(p,'receiver','wrong-receiver');assert.equal(wrong.status,'QUARANTINE');assert.match(wrong.reason,/RECEIVER_OR_SENDER/);
  const accepted=await receive(p);assert.equal(accepted.receipt.status,'ACCEPTED');assert.equal(accepted.receipt.actualImages,0);
  assert.equal(accepted.restoredAuthority,'NONE');assert.equal(accepted.receipt.originalSha256,sha256(original));
  assert.equal(accepted.receipt.positionMethod,'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC');
  assert.equal(accepted.receipt.qualifiedForSurvey,false);assert.equal(accepted.receipt.sensorClockUncertainty,'UNKNOWN');
  const replay=await receive(p);assert.equal(replay.status,'QUARANTINE');assert.match(replay.reason,/TRANSFER_REPLAY/);
  await fs.writeFile(join(root,'receiver-accepted.json'),JSON.stringify(accepted,null,2));
});

await test('independent receiver rejects corrupt/missing/extra/links/swapped context and fresh-transfer capture replay',async()=>{
  const store=await Store01({root:storeAt('captures')});
  let data;try{data=await store.read('capture-001');}finally{await store.close();}
  const sidecar=jsonBytes(data.sidecar),manifest=jsonBytes(exported.manifest),badOriginal=Buffer.from(original);badOriginal[50]^=1;
  const archives={
    corrupt:makeTar([['original.jpg',badOriginal],['sidecar.json',sidecar],['manifest.json',manifest]]),
    missing:makeTar([['original.jpg',original],['manifest.json',manifest]]),
    extra:Buffer.concat([tar,Buffer.alloc(512)]),
    truncation:tar.subarray(0,tar.length-512),
  };
  const link=Buffer.from(tar);link[156]=50;link.fill(32,148,156);let sum=0;for(let i=0;i<512;i++)sum+=link[i];link.write(sum.toString(8).padStart(6,'0')+'\0 ',148,8,'ascii');archives.symlink=link;
  const swapped=structuredClone(data.sidecar);swapped.context.flightBoot='foreign-boot';
  const sb=jsonBytes(swapped),mb=structuredClone(exported.manifest);mb.files[1]={path:'sidecar.json',sizeBytes:sb.length,sha256:sha256(sb)};
  const {packageId,...base}=mb;mb.packageId=sha256(jsonBytes(base));
  archives.context=makeTar([['original.jpg',original],['sidecar.json',sb],['manifest.json',jsonBytes(mb)]]);
  for(const [name,bytes]of Object.entries(archives)){
    const path=join(root,`bad-${name}.tar`);await fs.writeFile(path,bytes);const got=await receive(path,`reject-${name}`);
    assert.equal(got.status,'QUARANTINE',name);await fs.writeFile(join(root,`bad-${name}-receipt.json`),JSON.stringify(got,null,2));
  }
  const m=structuredClone(exported.manifest);m.transferId='fresh-transfer';const {packageId:unused,...b}=m;m.packageId=sha256(jsonBytes(b));
  const path=join(root,'fresh-transfer-replay.tar');await fs.writeFile(path,makeTar([['original.jpg',original],['sidecar.json',sidecar],['manifest.json',jsonBytes(m)]]));
  const got=await receive(path);assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/CAPTURE_REPLAY/);
});

await test('capture provenance gates refuse ellipsoid/survey/time certainty/bad JPEG/link mismatch; unknown position retained',async()=>{
  const store=await Store01({root:storeAt('schema')});
  try {
    for(const [name,mutate]of [
      ['ellipsoid',f=>f.sidecar.position.datum='WGS84_ELLIPSOID'],
      ['survey',f=>f.sidecar.position.qualifiedForSurvey=true],
      ['sensor certainty',f=>f.sidecar.position.sensorTimeUncertaintyMs=0],
      ['physical exposure',f=>f.sidecar.timing.physicalExposureTime='MEASURED'],
      ['wrong boot',f=>f.link.flightBoot='different'],
      ['bad JPEG',f=>{f.originalBytes=new Uint8Array([255,216,255,217]);}],
      ['unknown missing reason',f=>f.sidecar.position=null],
    ]){const f=fixture('refuse');mutate(f);await assert.rejects(store.commit('refuse',f),undefined,name);}
    assert.equal(store.records().length,0);
    const f=fixture('unlocated');f.sidecar.position=null;f.sidecar.timing.reason='NO_SITL_BRACKET';
    await store.commit('unlocated',f);assert.equal((await store.read('unlocated')).sidecar.position,null);
  }finally{await store.close();}
});

await test('independent receiver rejects integrity-valid false survey/datum/time/source claims',async()=>{
  for(const [name,mutate]of [
    ['ellipsoid',s=>s.position.datum='WGS84_ELLIPSOID'],
    ['survey',s=>s.position.qualifiedForSurvey=true],
    ['sensor-certainty',s=>s.position.sensorTimeUncertaintyMs=0],
    ['physical-exposure',s=>s.timing.physicalExposureTime='MEASURED'],
    ['invented-interpolation',s=>s.position.method='SENSOR_SYNCHRONIZED_INTERPOLATED'],
    ['actual-images',s=>s.actualImages=1],
    ['boolean-schema',s=>s.schemaVersion=true],
    ['unlocated-without-reason',s=>s.position=null],
  ]){
    const s=fixture().sidecar;mutate(s);const sb=jsonBytes(s),m=structuredClone(exported.manifest);
    m.files[1]={path:'sidecar.json',sizeBytes:sb.length,sha256:sha256(sb)};
    const {packageId,...base}=m;m.packageId=sha256(jsonBytes(base));
    const file=join(root,`false-${name}.tar`);await fs.writeFile(file,makeTar([['original.jpg',original],['sidecar.json',sb],['manifest.json',jsonBytes(m)]]));
    const got=await receive(file,`reject-false-${name}`);assert.equal(got.status,'QUARANTINE',name);
    await fs.writeFile(join(root,`false-${name}-receipt.json`),JSON.stringify(got,null,2));
  }
});

await test('fsync delayed 180ms keeps event-loop health ticking; receipt waits for fsync',async()=>{
  let delay=false,release,entered;
  const waiting=new Promise(r=>entered=r);
  const store=await Store01({root:storeAt('responsive'),hooks:{at:async stage=>{if(delay&&stage==='journal.fsync'){entered();await new Promise(r=>release=r);}}}});
  try {
    let ticks=0,settled=false;const interval=setInterval(()=>ticks++,5);delay=true;
    const pending=store.append('RESPONSIVENESS_PROBE',{}).then(x=>{settled=true;return x;});
    await waiting;await new Promise(r=>setTimeout(r,180));assert.equal(settled,false);assert(ticks>=12,`ticks=${ticks}`);
    release();await pending;clearInterval(interval);assert.equal(settled,true);return {healthTicks:ticks,injectedFsyncWaitMs:180};
  }finally{delay=false;await store.close();}
});

await test('WAL fsync uncertainty poisons writer; later append is refused and bytes retained',async()=>{
  let inject=false;const path=storeAt('fsync-fault');const store=await Store01({root:path,hooks:{at:async s=>{if(inject&&s==='journal.fsync')throw new Error('INJECTED_EIO');}}});
  try {inject=true;await assert.rejects(store.append('FAIL_SYNC',{}),/UNCERTAIN/);assert.equal(store.snapshot().poisoned,true);
    await assert.rejects(store.append('NO_FURTHER_WRITE',{}),/UNCERTAIN/);assert((await fs.stat(join(path,'journal.jsonl'))).size>0);
  }finally{inject=false;await store.close();}
});

await test('capture file sync failure retains pending files and guard revocation retains pending without commit',async()=>{
  for(const type of ['file-sync','guard']){
    let armed=false,guardCalls=0;const path=storeAt(type);
    const store=await Store01({root:path,hooks:{at:async s=>{if(armed&&type==='file-sync'&&s==='capture.sidecar.fsync')throw new Error('INJECTED_CAPTURE_EIO');}}});
    try {armed=true;const f=fixture('pending');f.guard=()=>{if(type==='guard'&&++guardCalls===2)throw new Error('AUTHORITY_REVOKED');};
      await assert.rejects(store.commit('pending',f),/PENDING_UNCERTAIN/);assert.equal(store.snapshot().poisoned,true);
      assert.equal((await store.review()).rows[0].state,'PENDING');assert.equal(store.records().filter(r=>r.kind==='CAPTURE_COMMITTED').length,0);
      assert((await fs.stat(join(path,'captures/pending/original.jpg'))).size>0);
    }finally{armed=false;await store.close();}
    const again=await Store01({root:path});try{assert.equal((await again.review()).rows[0].state,'PENDING');assert.equal(again.snapshot().authority,'NONE');}
    finally{await again.close();}
  }
});

await test('crash leaves writer lock, read-only restart, pending retained without authority',async()=>{
  const stages=['capture.original.fsync','capture.directory.fsync'];
  for(const stage of stages){const path=storeAt(`crash-${stage}`);let exit;
    try{await run(process.execPath,[join(repo,'pilot/field01/evidence/crash-worker.mjs'),path,stage]);}catch(e){exit=e.code;}
    assert.equal(exit,71);assert((await fs.stat(join(path,'writer.lock'))).isFile());
    const again=await Store01({root:path});try{assert.equal(again.snapshot().readOnly,true);assert.equal(again.snapshot().authority,'NONE');
      await assert.rejects(again.append('FORBIDDEN',{}),/LOCK_PRESENT/);assert.equal((await again.review()).rows[0].state,'PENDING');
    }finally{await again.close();}
    assert((await fs.stat(join(path,'writer.lock'))).isFile());
  }
});

await test('single writer lock refuses peer; close releases only own lock',async()=>{
  const path=storeAt('writer-owner'),a=await Store01({root:path}),b=await Store01({root:path});
  try{assert.equal(a.snapshot().readOnly,false);assert.equal(b.snapshot().readOnly,true);await b.close();assert((await fs.stat(join(path,'writer.lock'))).isFile());}
  finally{await a.close();}
  await assert.rejects(fs.stat(join(path,'writer.lock')),e=>e.code==='ENOENT');
});

await test('record, capture and byte quotas reject before intent with no automatic deletion',async()=>{
  const r=await Store01({root:storeAt('record-quota'),limits:{maxRecords:2}});
  try{await r.append('ONE',{});await r.append('TWO',{});await assert.rejects(r.append('THREE',{}),/RECORD_QUOTA/);assert.equal(r.snapshot().poisoned,false);}
  finally{await r.close();}
  const c=await Store01({root:storeAt('capture-quota'),limits:{maxCaptures:1}});
  try{await c.commit('one',fixture('one'));await assert.rejects(c.commit('two',fixture('two')),/CAPTURE_QUOTA/);assert.equal((await c.read('one')).receipt.status,'COMMITTED');}
  finally{await c.close();}
  const b=await Store01({root:storeAt('byte-quota'),limits:{maxBytes:4096}});
  try{await assert.rejects(b.commit('one',fixture('one')),/STORE_QUOTA/);assert.equal(b.records().length,0);assert.equal(b.snapshot().poisoned,false);}
  finally{await b.close();}
});

await test('static symlinks in root ancestry, journal, capture path, receiver state and archive refused',async()=>{
  const target=storeAt('symlink-target');await fs.mkdir(target);
  const alias=storeAt('symlink-alias');await fs.symlink(target,alias,'dir');await assert.rejects(Store01({root:join(alias,'child')}),/SYMLINK_OR_TYPE/);
  const jr=storeAt('symlink-journal');await fs.mkdir(jr);await fs.writeFile(join(target,'journal'),Buffer.alloc(0));await fs.symlink(join(target,'journal'),join(jr,'journal.jsonl'));
  const a=await Store01({root:jr});try{assert.equal(a.snapshot().readOnly,true);assert.equal(a.snapshot().poisoned,true);}finally{await a.close();}
  const path=storeAt('symlink-capture');const c=await Store01({root:path});
  try{await fs.symlink(target,join(path,'captures','one'),'dir');await assert.rejects(c.commit('one',fixture('one')),/PENDING_UNCERTAIN/);}
  finally{await c.close();}
  const state=storeAt('receiver-state-link');await fs.symlink(target,state,'dir');
  let got=await receive(join(root,'package.tar'),'receiver-state-link');assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/SYMLINK/);
  const packageAlias=join(root,'package-link.tar');await fs.symlink(join(root,'package.tar'),packageAlias);
  got=await receive(packageAlias,'receiver-package-link');assert.equal(got.status,'QUARANTINE');
});

await test('corrupt/torn journals are observation-only and receiver never restores rights',async()=>{
  for(const name of ['corrupt','torn']){
    const path=storeAt(`${name}-journal`);const s=await Store01({root:path});await s.append('NOTE',{});await s.close();
    const file=join(path,'journal.jsonl'),data=await fs.readFile(file);
    await fs.chmod(file,0o600);await fs.writeFile(file,name==='corrupt'?Buffer.from(data.toString().replace('NOTE','N0TE')):data.subarray(0,-1));
    const again=await Store01({root:path});try{assert.equal(again.snapshot().readOnly,true);assert.equal(again.snapshot().poisoned,true);assert.equal(again.snapshot().authority,'NONE');}
    finally{await again.close();}
  }
  const state=storeAt('receiver-corrupt');await fs.mkdir(state);await fs.writeFile(join(state,'receipts.jsonl'),'{}\n');
  const got=await receive(join(root,'package.tar'),'receiver-corrupt');assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/JOURNAL/);
});

const summary={scope:'FIELD01_BUILDER_SELF_CHECK_SYNTHETIC_LOCAL_FS_AND_PYTHON_RECEIVER',independentHumanReview:false,
  actualImages:0,authorityRestored:'NONE',passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length,
  retainedEvidence:root,limitations:['No actual camera or exposure/GNSS measurements','Injected fsync delays/errors are synthetic fault tests',
    'JPEG structure gate does not decode or certify safety','Filesystem ancestors must remain operator-controlled; Node lacks openat',
    'Crash locks intentionally retained as evidence; no stale lock automatic deletion','Hashes prove integrity, not source authenticity'],results};
await fs.writeFile(join(root,'results.json'),JSON.stringify(summary,null,2));
console.log(JSON.stringify({passed:summary.passed,failed:summary.failed,retainedEvidence:root}));
if(summary.failed){console.error(JSON.stringify(results.filter(r=>r.status==='FAIL'),null,2));process.exitCode=1;}
