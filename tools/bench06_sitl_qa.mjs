import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {makeFreeze,assertCurrentFreeze} from './bench06_freeze.mjs';
import {BENCH_TRIALS,sealBenchmark,validateBenchmarkRun,benchmarkReport} from '../app/core/benchmark.mjs';
import {validateExecutionRecord} from '../app/core/execution-record.mjs';
const origin='http://127.0.0.1:8788',directory=process.env.AERIS_EVIDENCE_DIR||'evidence/bench06',checks=[],trials=[],negativeChecks=[];await mkdir(directory,{recursive:true});
let state,freeze,suite,armRequested=false,activeCase=null;
const check=(name,pass,detail={})=>{checks.push({name,pass,...detail});console.log(name,pass?'PASS':'FAIL');if(!pass)throw Error(name);};
async function get(route){const r=await fetch(origin+'/api/'+route),d=await r.json();if(!r.ok)throw Error(d.error);return d;}
async function poll(){state=await get('sitl/status');return state;}
async function request(route,body={}){await poll();const r=await fetch(origin+'/api/'+route,{method:'POST',headers:{Origin:origin,'Content-Type':'application/json','X-Aeris-Token':state.apiToken},body:JSON.stringify({sessionId:state.sessionId,...body})});return {status:r.status,data:await r.json()};}
async function post(route,body={}){const r=await request(route,body);if(r.status!==200)throw Error(r.data.error);return r.data;}
async function until(fn,ms=90000){const end=Date.now()+ms;while(true){await poll();if(fn(state))return;if(Date.now()>end)throw Error('Observation timeout '+state.mode+' '+state.mission?.execution?.state);await new Promise(r=>setTimeout(r,200));}}
async function record(id){for(let n=0;n<40;n++){try{return await validateExecutionRecord(await get('executions/'+id));}catch(e){if(n===39)throw e;await new Promise(r=>setTimeout(r,100));}}}
try{
 await poll();if(state.transport!=='disconnected'||state.archive?.activeId)throw Error('Preview has an active connection/attempt; refusing to interrupt another operator.');
 ({suite,freeze}=await makeFreeze());
 await writeFile(directory+'/freeze.json',JSON.stringify(freeze,null,2)+'\n');
 check('pre-run-source-runtime-freeze',true,{sha256:freeze.sha256,sourceFiles:Object.keys(freeze.build.files).length});
 await post('sitl/connect');await until(s=>s.armed===false&&s.preflight.filter(c=>c.id!=='configuration').every(c=>c.pass),60000);
 for(const planned of BENCH_TRIALS){
  activeCase=planned.caseId+'-'+planned.kind;await assertCurrentFreeze(freeze);await until(s=>s.armed===false&&s.connected);
  const before={checkedAt:new Date().toISOString(),sessionId:state.sessionId,armed:state.armed};
  await post('sitl/disconnect');execFileSync('docker',['restart','aeris-sitl'],{timeout:30000});
  await new Promise(r=>setTimeout(r,1500));await post('sitl/connect');await until(s=>s.armed===false&&s.preflight.filter(c=>c.id!=='configuration').every(c=>c.pass),60000);
  const reset={container:'aeris-sitl',action:'restart',before,after:{checkedAt:new Date().toISOString(),sessionId:state.sessionId,armed:state.armed}};
  const cfg=await post('sitl/configuration');check(activeCase+' fresh matching profile',cfg.pass,{sessionId:state.sessionId});
  const c=suite.cases.find(c=>c.id===planned.caseId);await post('executions/source-context',{request:c.request,lineage:c.provenance.derivation?{sourceRaw:c.provenance.derivation.sourceRaw,options:c.provenance.derivation.options}:null});
  await post('sitl/upload',{package:c.request});await poll();const id=state.archive.activeId;
  check(activeCase+' exact mission readback',state.mission.readbackMatches&&state.expectedRequest&&id,{recordId:id});
  await post('sitl/command',{name:'guided'});armRequested=true;await post('sitl/command',{name:'arm'});await post('sitl/command',{name:'auto'});
  await until(s=>s.armed&&s.mode==='AUTO'&&s.position?.relativeAltitude>8);check(activeCase+' AUTO observed airborne',true,{position:state.position});
  if(planned.kind==='interrupted'){await post('sitl/command',{name:'hold'});check(activeCase+' HOLD observed',state.modeId===5||(await poll()).modeId===5);await post('sitl/command',{name:'rtl'});}
  await until(s=>s.armed===false&&['completed','stopped'].includes(s.mission.execution.state));armRequested=false;
  const sealed=await record(id);trials.push({...planned,method:'automated-sitl',reset,record:sealed});
  const expected=planned.kind==='completed'?'COMPLETED':'STOPPED';check(activeCase+' conservative sealed outcome',sealed.summary.outcome===expected,{summary:sealed.summary});
  const journal=await get('sitl/journal');check(activeCase+' no PARAM_SET',journal.frames.filter(f=>f.direction==='out').every(f=>f.id!==23));
  await writeFile(directory+'/'+activeCase+'-record.json',JSON.stringify(sealed,null,2)+'\n');await writeFile(directory+'/'+activeCase+'-journal.json',JSON.stringify(journal)+'\n');
 }
 await post('sitl/configuration');
 for(const c of suite.cases.filter(c=>!c.expected.accepted)){const before=await get('sitl/journal'),result=await request('sitl/upload',{package:c.request}),after=await get('sitl/journal'),frames=after.frames.slice(before.frames.length);check(c.id+' rejected before mission wire writes',result.status===409&&result.data.error===c.expected.error&&frames.filter(f=>f.direction==='out').every(f=>f.id===0),{status:result.status,error:result.data.error});negativeChecks.push({caseId:c.id,sourceSha256:c.expected.sourceSha256,status:result.status,error:result.data.error,frames});}
 await assertCurrentFreeze(freeze);check('post-run source/runtime unchanged from freeze',true);await poll();check('final actual simulator disarmed',state.armed===false&&state.configuration.pass);
 const run=await sealBenchmark({format:'aeris-benchmark-run',version:1,simulation:true,suite,freeze,trials,negativeChecks,comparator:{arm:'B',application:'RAGAS',status:'NOT_CHECKED',build:null,runtime:null,observations:[]}});await validateBenchmarkRun(run,{suiteSha256:suite.sha256});const report=benchmarkReport(run);check('four bound trials and four negative guards complete',report.armA.status==='ENGINEERING_PASS');check('B and human/native measures remain unmeasured',report.armB.status==='NOT_CHECKED'&&report.comparison.winner===null&&report.comparison.operatorTaskSeconds===null);
 await writeFile(directory+'/run.json',JSON.stringify(run,null,2)+'\n');await writeFile(directory+'/report.json',JSON.stringify(report,null,2)+'\n');await post('sitl/disconnect');
}catch(e){checks.push({name:'campaign-error',pass:false,message:e.stack});console.error(e.message);process.exitCode=1;try{await writeFile(directory+'/failed-journal.json',JSON.stringify(await get('sitl/journal'))+'\n');}catch{}}
finally{
 if(armRequested){try{await poll();if(state.armed){await post('sitl/command',{name:'rtl'});await until(s=>s.armed===false);}check('cleanup observed disarmed',state.armed===false);}catch(e){checks.push({name:'cleanup',pass:false,message:e.message});}}
 try{await poll();if(state.armed===false&&state.sessionId)await post('sitl/disconnect');}catch{}
 await writeFile(directory+'/sitl-qa.json',JSON.stringify({scope:'Actual dedicated ArduCopter4.7.1 loopback speedup5. Automated engineering pilot, no physical device or RAGAS trial.',checks,completedTrials:trials.map(t=>({caseId:t.caseId,kind:t.kind,id:t.record.id}))},null,2)+'\n');
}
console.log(JSON.stringify({pass:checks.filter(c=>c.pass).length,fail:checks.filter(c=>!c.pass).length}));
