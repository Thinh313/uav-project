/** Builder checks of actual retained GUI-exported SITL raw + two synthetic capture TARs.
 * No new SITL/media/physical capture is performed. Invalid candidates are retained.
 */
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {promisify} from 'node:util';
import {execFile} from 'node:child_process';
import {exportDeliverySet} from '../../pilot/field01/evidence/delivery-set.mjs';
import {jsonBytes,sha256,makeTar} from '../../pilot/field01/evidence/schema.mjs';
const run=promisify(execFile),repo=resolve(fileURLToPath(new URL('../..',import.meta.url))),stamp=new Date().toISOString().replace(/[:.]/g,'-');
const out=join(repo,'evidence/field01',`evidence-delivery-set-tests-${stamp}`);await fs.mkdir(out,{recursive:true});
const flight={archive:join(repo,'evidence/field01/app07/flight-e3bf4ca0-6788-4205-94fc-2591c83342ee.tar'),
  manifestSha256:'475c70026727b99ae7f12610e48b014c7b2f0facac9c88f94e1b6d677d90cafc',expectedRun:'sb5d91f31ba82446984dc'};
const captureArchives=['9eebcd51-ab41-4141-bc17-0183fd00fadb.tar','410bb7ea-dc82-4397-84b9-c15fa55765fb.tar'].map(n=>join(repo,'evidence/field01/app01/workspace/handoffs',n));
const results=[];let valid;
const exists=async p=>{try{await fs.lstat(p);return true;}catch(e){if(e.code==='ENOENT')return false;throw e;}};
async function test(name,fn){const at=performance.now();try{const detail=await fn();results.push({name,status:'PASS',elapsedMs:performance.now()-at,...detail});}
  catch(e){results.push({name,status:'FAIL',elapsedMs:performance.now()-at,error:e.stack});}}
async function receive(folder,sha,{state=join(out,'receiver-state'),receiver='field01-evaluator',sender='aeris-field01-synthetic',checkOnly=false}={}){
  const args=['-B',join(repo,'pilot/field01/evidence/receive-set.py'),folder,'--index-sha256',sha,'--receiver',receiver,'--sender',sender,
    ...(checkOnly?['--check-only']:['--state',state])];let process;
  try{process=await run('python3',args,{cwd:repo,timeout:60000,maxBuffer:131072});}catch(e){process=e;}
  return JSON.parse(process.stdout.trim());
}
function unpack(data){const files={};let offset=0;for(let i=0;i<3;i++){const h=data.subarray(offset,offset+512),name=h.subarray(0,100).toString('ascii').split('\0')[0],size=parseInt(h.subarray(124,136).toString('ascii'),8);
  files[name]=data.subarray(offset+512,offset+512+size);offset+=512+Math.ceil(size/512)*512;}return files;}
async function variant(name,mutate){const root=join(out,name),index=JSON.parse(await fs.readFile(valid.indexPath,'utf8'));
  const files={'flight.tar':await fs.readFile(join(valid.out,'flight.tar')),'capture-01.tar':await fs.readFile(join(valid.out,'capture-01.tar')),'capture-02.tar':await fs.readFile(join(valid.out,'capture-02.tar'))};
  await mutate(index,files);await fs.mkdir(root);for(const [n,b]of Object.entries(files))await fs.writeFile(join(root,n),b,{flag:'wx'});
  const bytes=jsonBytes(index);await fs.writeFile(join(root,'index.json'),bytes,{flag:'wx'});return{root,sha:sha256(bytes)};}
function changedCapture(data,change){const files=unpack(data),s=JSON.parse(files['sidecar.json']),m=JSON.parse(files['manifest.json']);change(s,m);
  const sb=jsonBytes(s);m.files[1]={path:'sidecar.json',sizeBytes:sb.length,sha256:sha256(sb)};const{packageId,...base}=m;m.packageId=sha256(jsonBytes(base));
  return makeTar([['original.jpg',files['original.jpg']],['sidecar.json',sb],['manifest.json',jsonBytes(m)]]);}
function updateDescriptor(index,path,data){const d=path==='flight.tar'?index.flight:index.captures.find(c=>c.path===path);d.sizeBytes=data.length;d.sha256=sha256(data);}
async function rejected(name,set,pattern){const state=join(out,'rejected-state-'+name),got=await receive(set.root,set.sha,{state});
  assert.equal(got.status,'QUARANTINE');assert.match(got.reason,pattern);assert.equal(got.restoredAuthority,'NONE');assert.equal(await exists(state),false,'all validation must finish before any state directory/ledger write');
  await fs.writeFile(join(out,name+'-receipt.json'),JSON.stringify(got,null,2));}

await test('actual accepted SITL + RGB/thermal synthetic capture pair exports immutable exact TAR bytes',async()=>{
  valid=await exportDeliverySet({out:join(out,'valid-set'),deliveryId:'delivery-actual-sitl-'+stamp,flight,captureArchives});
  assert.equal(valid.receipt.status,'VALIDATED_NO_LEDGER_WRITE');assert.equal(valid.receipt.acceptedSimulatorExecution,true);
  assert.equal(valid.receipt.captureCount,2);assert.equal(valid.receipt.actualImages,0);assert.equal(valid.receipt.qualifiedForSurvey,false);
  assert.equal(valid.receipt.sensorExposureAccuracy,'UNKNOWN');assert.equal(valid.receipt.sensorClockUncertainty,'UNKNOWN');
  assert.equal(valid.receipt.restoredAuthority,'NONE');assert.equal(valid.receipt.physicalFlightProven,false);assert.equal(valid.receipt.authenticityProven,false);
  assert.deepEqual(await fs.readFile(join(valid.out,'flight.tar')),await fs.readFile(flight.archive));
  for(let i=0;i<2;i++)assert.deepEqual(await fs.readFile(join(valid.out,`capture-0${i+1}.tar`)),await fs.readFile(captureArchives[i]));
  assert.equal(sha256(await fs.readFile(valid.indexPath)),valid.indexSha256);
  assert.deepEqual(valid.receipt.captureBindings.map(c=>c.feed),['rgb','thermal']);
  assert(valid.receipt.captureBindings.every(c=>c.hostReferenceDeltaMs<=1500&&c.positionMethod==='NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC'));
  await fs.writeFile(join(out,'export-receipt.json'),JSON.stringify(valid,null,2));return {indexSha256:valid.indexSha256,totalBytes:valid.totalBytes,actualImages:0};
});

await test('readonly validation makes no receiver ledger, durable receive commits one receipt and restart rejects replay',async()=>{
  const state=join(out,'receiver-state');assert.equal(await exists(state),false);
  const check=await receive(valid.out,valid.indexSha256,{checkOnly:true});assert.equal(check.status,'VALIDATED_NO_LEDGER_WRITE');assert.equal(await exists(state),false);
  const accepted=await receive(valid.out,valid.indexSha256);assert.equal(accepted.status,'ACCEPTED_DURABLE_DELIVERY');assert.equal(accepted.journal.seq,1);
  assert.equal(accepted.restoredAuthority,'NONE');assert.equal(accepted.authorityRestorable,false);
  const ledger=join(state,'delivery-receipts.jsonl'),before=await fs.readFile(ledger);assert.equal(await exists(join(state,'delivery-receiver.lock')),false);
  const replay=await receive(valid.out,valid.indexSha256);assert.equal(replay.status,'QUARANTINE');assert.match(replay.reason,/DELIVERY_REPLAY/);assert.deepEqual(await fs.readFile(ledger),before);
  assert.equal(await exists(join(state,'delivery-receiver.lock')),false);await fs.writeFile(join(out,'accepted-receipt.json'),JSON.stringify(accepted,null,2));
});

await test('existing output is never overwritten and duplicate input path is refused',async()=>{
  const before=await fs.readFile(valid.indexPath);await assert.rejects(exportDeliverySet({out:valid.out,flight,captureArchives}),e=>e.code==='EEXIST');
  assert.deepEqual(await fs.readFile(valid.indexPath),before);
  await assert.rejects(exportDeliverySet({out:join(out,'duplicate-input-path'),flight,captureArchives:[captureArchives[0],captureArchives[0]]}),/DUPLICATE_PATH/);
  assert.equal(await exists(join(out,'duplicate-input-path')),false);
});

await test('mock-flight RGB/thermal pair is refused before any overall receiver state write',async()=>{
  const set=await variant('wrong-mock-pair',async(index,files)=>{
    for(const [i,name]of ['7be44b76-6eec-4589-b551-a8686fe44dd2.tar','cd8c1ac0-afbf-4e7b-9acc-3d639845ef61.tar'].entries()){
      const path=`capture-0${i+1}.tar`;files[path]=await fs.readFile(join(repo,'evidence/field01/app01/workspace/handoffs',name));updateDescriptor(index,path,files[path]);}});
  await rejected('wrong-mock-pair',set,/CAPTURE_FLIGHT_CONTEXT_LINK_MISMATCH/);
});

await test('wrong receiver/sender and expected index hash are refused before any ledger write',async()=>{
  const set={root:valid.out,sha:valid.indexSha256};
  for(const [name,options]of [['receiver',{receiver:'wrong-receiver'}],['sender',{sender:'wrong-sender'}]]){
    const state=join(out,'wrong-'+name+'-state'),got=await receive(set.root,set.sha,{state,...options});assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/INDEX_SCHEMA_OR_RECEIVER/);assert.equal(await exists(state),false);}
  const state=join(out,'wrong-hash-state'),got=await receive(set.root,'0'.repeat(64),{state});assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/INDEX_SHA/);assert.equal(await exists(state),false);
});

await test('corrupt, missing and duplicate capture archive members are refused without receiver state',async()=>{
  const corrupt=await variant('corrupt',async(_index,files)=>{files['capture-01.tar']=Buffer.from(files['capture-01.tar']);files['capture-01.tar'][1000]^=1;});await rejected('corrupt',corrupt,/DELIVERY_MEMBER_SHA_OR_SIZE/);
  const missing=await variant('missing',async(_index,files)=>{delete files['capture-02.tar'];});await rejected('missing',missing,/DELIVERY_EXACT_FILE_SET/);
  const duplicate=await variant('duplicate',async(index,files)=>{files['capture-02.tar']=files['capture-01.tar'];updateDescriptor(index,'capture-02.tar',files['capture-02.tar']);});
  await rejected('duplicate',duplicate,/DELIVERY_DUPLICATE_CAPTURE_PACKAGE_OR_TRANSFER/);
});

await test('integrity-valid wrong run/boot/model/plan capture bindings are refused against actual accepted flight',async()=>{
  for(const [key,value]of [['flightRun','s'+'0'.repeat(20)],['flightBoot','wrong-boot'],['modelSha256','1'.repeat(64)],['planSha256','2'.repeat(64)]]){
    const set=await variant('wrong-'+key,async(index,files)=>{files['capture-01.tar']=changedCapture(files['capture-01.tar'],(s,m)=>{s.context[key]=value;m.context[key]=value;m.link[key]=value;});updateDescriptor(index,'capture-01.tar',files['capture-01.tar']);});
    await rejected('wrong-'+key,set,/CAPTURE_FLIGHT_CONTEXT_LINK_MISMATCH/);
  }
});

await test('validly rehashed reference coordinates cannot invent an observed raw position or survey qualification',async()=>{
  const coordinate=await variant('invented-coordinate',async(index,files)=>{files['capture-01.tar']=changedCapture(files['capture-01.tar'],s=>s.position.latitudeDeg+=0.001);updateDescriptor(index,'capture-01.tar',files['capture-01.tar']);});
  await rejected('invented-coordinate',coordinate,/CAPTURE_RAW_HOST_REFERENCE_MISMATCH/);
  const survey=await variant('false-survey',async(index,files)=>{files['capture-01.tar']=changedCapture(files['capture-01.tar'],s=>s.position.qualifiedForSurvey=true);updateDescriptor(index,'capture-01.tar',files['capture-01.tar']);});
  await rejected('false-survey',survey,/SIDECAR_REFERENCE_POSITION/);
});

await test('relabeling delivery ID cannot replay an already accepted flight/capture set',async()=>{
  const set=await variant('replay-renamed',async(index)=>{index.deliveryId='different-delivery-id';});
  const got=await receive(set.root,set.sha);assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/DELIVERY_REPLAY/);assert.equal(got.restoredAuthority,'NONE');
});

await test('wrong expected flight manifest hash and symlinked delivery member are refused',async()=>{
  const manifest=await variant('wrong-flight-manifest',async(index)=>{index.flight.manifestSha256='0'.repeat(64);});await rejected('wrong-flight-manifest',manifest,/FLIGHT_RECEIVER_REJECTED/);
  const symlink=await variant('symlink-member',async(_index,files)=>{delete files['capture-02.tar'];});await fs.symlink(captureArchives[1],join(symlink.root,'capture-02.tar'));
  await rejected('symlink-member',symlink,/Too many levels|symbolic|ELOOP/i);
});

await test('oversized TAR input is refused before export directory creation',async()=>{
  for(const [name,size,options]of [['capture',4*2**20+1,{captureArchives:null}],['flight',32*2**20+1,{flight:null}]]){
    const file=join(out,'oversized-'+name+'.tar'),h=await fs.open(file,'wx');try{await h.truncate(size);}finally{await h.close();}
    const target=join(out,'oversized-'+name+'-output');await assert.rejects(exportDeliverySet({out:target,flight,captureArchives,
      ...(options.captureArchives===null?{captureArchives:[file]}:{flight:{...flight,archive:file}})}),/DELIVERY_INPUT_BOUND/);assert.equal(await exists(target),false);
  }
});

await test('torn/corrupt overall ledger and retained stale lock refuse new receipt without authority restoration',async()=>{
  const existing=await fs.readFile(join(out,'receiver-state/delivery-receipts.jsonl'));
  for(const [name,contents]of [['torn',existing.subarray(0,-1)],['corrupt',Buffer.from(existing.toString().replace('ACCEPTED_DURABLE_DELIVERY','ALTERED_DURABLE_DELIVERY'))]]){
    const state=join(out,'ledger-'+name);await fs.mkdir(state);await fs.writeFile(join(state,'delivery-receipts.jsonl'),contents);
    const got=await receive(valid.out,valid.indexSha256,{state});assert.equal(got.status,'QUARANTINE');assert.match(got.reason,/DELIVERY_LEDGER_(TORN|HASH|CHAIN)/);assert.equal(got.restoredAuthority,'NONE');
    assert.deepEqual(await fs.readFile(join(state,'delivery-receipts.jsonl')),contents);assert.equal(await exists(join(state,'delivery-receiver.lock')),false);
  }
  const state=join(out,'stale-lock');await fs.mkdir(state);await fs.writeFile(join(state,'delivery-receiver.lock'),'RETAINED_TEST_STALE_LOCK');
  const got=await receive(valid.out,valid.indexSha256,{state});assert.equal(got.status,'QUARANTINE');assert.equal(await exists(join(state,'delivery-receiver.lock')),true);
  assert.equal(await exists(join(state,'delivery-receipts.jsonl')),false);
});

const summary={scope:'FIELD01_BUILDER_DELIVERY_SET_CHECKS_RETAINED_ACTUAL_ACCEPTED_SITL_RAW_AND_SYNTHETIC_JPEGS',actualImages:0,
  passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length,
  independentHumanReview:false,sourceFlightRun:flight.expectedRun,sourceFlightManifestSha256:flight.manifestSha256,
  limitations:['No new SITL, flight, camera, GNSS, Android or media run','Synthetic capture bytes remain synthetic; physical exposure accuracy/clock uncertainty UNKNOWN',
    'Hashes/context/raw reference integrity do not prove source authenticity','One accepted flight run is receivable once per overall receiver ledger; incremental resend is refused',
    'Exporter and aggregate receiver share an author; flight Node decoder and existing Python capture validator are reused separately'],results};
await fs.writeFile(join(out,'results.json'),JSON.stringify(summary,null,2));console.log(JSON.stringify({passed:summary.passed,failed:summary.failed,evidence:out}));
if(summary.failed){console.error(JSON.stringify(results.filter(r=>r.status==='FAIL'),null,2));process.exitCode=1;}
