import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {diskFloor} from '../../pilot/betaworkbench03/session.mjs';

// Separate read-only receiver: no session creation, flight command, journal repair,
// producer-side accepted flag or engineeringGate is sufficient by itself.
const root=path.resolve('evidence/betaworkbench03');
const sha=b=>createHash('sha256').update(b).digest('hex');
const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function chain(file,store=false){
 const bytes=fs.readFileSync(file,'utf8');assert(bytes.endsWith('\n'),'TORN_TAIL');
 let head=store?'0'.repeat(64):'',n=0;const rows=[];
 for(const line of bytes.trimEnd().split('\n')){
  const r=JSON.parse(line),key=store?'hash':'sha256',{[key]:digest,...body}=r;
  assert.equal(store?r.seq:r.n,++n);assert.equal(store?r.previousHash:r.previous,head);
  assert.equal(sha(canonical(body)),digest);assert.equal(canonical(r),line);
  head=digest;rows.push(r);
 }return{head,n,rows};
}
const main=path.join(root,'browser07/session'),wal=chain(path.join(main,'workspace/journal.jsonl'),true);
const reviews=wal.rows.filter(r=>r.kind==='BETA_FLIGHT_REVIEW').map(r=>r.data);assert.equal(reviews.length,1);
const review=reviews[0],raw=chain(path.join(main,review.run,'raw.jsonl'));
assert.equal(review.rawHead,raw.head);assert.equal(review.rawRecords,raw.n);
assert.equal(canonical(read(path.join(main,review.run,'review.json'))),canonical(review));
assert(review.accepted&&review.execution.complete&&review.execution.groundDisarmed&&review.execution.autoObserved);
assert.equal(review.source,'MOCK_PROTOCOL_NOT_ARDUPILOT');assert.equal(review.actualImages,0);
assert.equal(review.mockDelivery.pendingAtClose,0);assert.equal(review.mockDelivery.error,null);
const model=wal.rows.find(r=>r.kind==='BETA_MODEL_BOUND').data;
for(const k of Object.keys(model.binding))assert.equal(review[k],model.binding[k]);
for(const k of ['TX_RAW','READBACK_VERIFIED','POST_ARM_READBACK','BETA_CLOSE_INTENT'])assert(raw.rows.some(r=>r.kind===k),k);
let captures=0;
for(const entry of fs.readdirSync(path.join(main,'workspace/captures'))){
 const dir=path.join(main,'workspace/captures',entry),manifest=read(path.join(dir,'manifest.json')),sidecarBytes=fs.readFileSync(path.join(dir,'sidecar.json')),s=JSON.parse(sidecarBytes);
 assert.equal(sha(fs.readFileSync(path.join(dir,'original.jpg'))),manifest.originalSha256);
 assert.equal(sha(sidecarBytes),manifest.sidecarSha256);assert.equal(s.file.sha256,manifest.originalSha256);
 for(const [k,v]of Object.entries({modelSha256:review.modelSha256,planSha256:review.planSha256,flightRun:review.run,flightBoot:review.boot}))assert.equal(s.context[k],v);
 assert.equal(s.actualImages,0);assert.equal(s.sourceKind,'SYNTHETIC');assert.equal(s.position.qualifiedForSurvey,false);assert.equal(s.timing.physicalExposureTime,'UNKNOWN');
 assert(wal.rows.some(r=>r.kind==='CAPTURE_COMMITTED'&&r.data.captureId===entry),'COMMITTED_CAPTURE_WAL');captures++;
}
assert.equal(captures,1);
const reportFile=path.join(root,'browser06/media/report-01.json'),report=read(reportFile),binding=read(path.join(root,'browser06/binding-report-01.json'));
assert.equal(binding.rawReport.sha256,sha(fs.readFileSync(reportFile)));
assert.equal(binding.overlapStatus,'BINDING_RECORDED_AUTO_OVERLAP_NOT_CHECKED');
assert.equal(report.sampleCount,report.samples.length);const fps=1000*report.samples.length/report.durationMs;
assert(Math.abs(fps-report.displayedFps)<1e-9);assert(report.durationMs>=30000);
const upper=report.samples.map(s=>s.latencyUpperMs).sort((a,b)=>a-b),p95=upper[Math.min(upper.length-1,Math.floor(upper.length*.95))];
assert(Number.isFinite(p95)&&p95<300);assert(fps>=24);assert.equal(report.clockUnknownSamples,0);
assert.equal(report.overflow,0);assert.equal(report.stopReason,null);assert.equal(report.visualCoverageFailures.length,0);
for(const key of ['decoderErrors','apiFailures','consumerDrops','timestampMisses','unexpectedFreeze'])assert.equal(report.counters[key]-report.counterBaseline[key],0,key);
assert.equal(report.physicalLatency,'NOT_MEASURED');
// A failed close remains a failed attempt even though its retained raw is valid.
const failedRoot=path.join(root,'browser06/session'),failedWal=chain(path.join(failedRoot,'workspace/journal.jsonl'),true);
assert(!failedWal.rows.some(r=>r.kind==='BETA_FLIGHT_REVIEW'));
const failedFlight=fs.readdirSync(failedRoot).find(x=>/^m[a-f0-9]{20}$/.test(x)),failedRaw=chain(path.join(failedRoot,failedFlight,'raw.jsonl'));
const out={at:new Date().toISOString(),status:'PASS_WITH_DECLARED_UNRUN_GATES',scope:'READ_ONLY_BYTE_CHAIN_AND_CONTEXT_RECHECK_BY_SAME_ASSISTANT_NOT_INDEPENDENT_ANDROID_OR_AP_ACCEPTANCE',browser07:{run:review.run,rawRecords:raw.n,rawHead:raw.head,walRecords:wal.n,captures,actualImages:0,authorityRestored:false},browser06:{attemptStatus:'FAILED_CLOSE_RETAINED_NOT_ACCEPTED',rawRecords:failedRaw.n,rawHead:failedRaw.head,reviewCommitted:false,video:{samples:report.samples.length,durationMs:report.durationMs,fps,p95UpperMs:p95,initialReadyMs:report.initialReadyMs,physicalLatency:'NOT_MEASURED',codecOrAppColdness:'NOT_ATTESTED',airborneOverlap:'NOT_CHECKED',scope:'IAB_RECEIVER_SYNTHETIC_LOOPBACK_NOT_ANDROID'}},androidSaf:'NOT_RUN',actualSitl:'NOT_RUN'};
diskFloor();fs.writeFileSync(path.join(root,'receiver-verification01.json'),JSON.stringify(out,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(out,null,2));
