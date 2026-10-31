// Fixed local simulator-only benchmark, not a browser input or a hardware driver.
import {spawn}from'node:child_process';import fs from 'node:fs';import path from 'node:path';import {createHash}from'node:crypto';
const R=process.cwd(),E=path.join(R,'evidence/io59'),BASE='http://127.0.0.1:8812';
const requestId=process.argv[2],reserved=JSON.parse(fs.readFileSync(path.join(E,'reservations',requestId+'.json')));
if(reserved.requestId!==requestId)throw Error('RESERVATION_ID');
const log=fs.openSync(path.join(E,requestId+'-driver.jsonl'),'wx'),rows=[];let token,owner=null,lease=null,seq=0,started=false,ended=false,observer=null;
function record(kind,data){const row={at:new Date().toISOString(),hostNodeNs:String(process.hrtime.bigint()),requestId,kind,data};fs.writeSync(log,JSON.stringify(row)+'\n');rows.push(row)}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function get(route='state'){const r=await fetch(BASE+'/api/'+route,{signal:AbortSignal.timeout(5000)});const d=await r.json();if(!r.ok)throw Error(d.error);return d}
async function post(action,extra={}){
 const data={session:owner?.session,boot:owner?.boot,...extra};record('POST_ONCE_INTENT',{action,data});
 let r;try{r=await fetch(BASE+'/api/flight/'+action,{method:'POST',headers:{origin:BASE,'content-type':'application/json','x-aeris-token':token},body:JSON.stringify(data),signal:AbortSignal.timeout(65000)})}catch(e){record('WRITE_OUTCOME_UNKNOWN_NO_RETRY',{action,error:e.message});throw e}
 const d=await r.json();record('POST_RESPONSE',{action,ok:r.ok,data:d});if(!r.ok)throw Error(d.error);return d
}
async function until(f,ms){const end=performance.now()+ms;while(performance.now()<end){const s=await get();record('OBSERVE',{run:s.run,controllerActive:s.controllerActive,verifying:s.verifying,physics:s.physics,vehicle:s.vehicle,input:s.input,lastError:s.lastError});if(f(s))return s;await wait(100)}throw Error('BENCH_OBSERVATION_DEADLINE')}
try{
 token=(await get('bootstrap')).token;const before=await get();if(before.controllerActive||before.verifying)throw Error('ALREADY_ACTIVE');
 record('BEGIN',{reservation:reserved,physicsHz:1200,speedup:1,capUs:500000,airborneHoldSeconds:20,preflightDeadlineSeconds:55,input:'SYNTHETIC_NEUTRAL_BENCH_DRIVER_NOT_HERA',browserInput:false});
 const s=await post('start',reserved);owner={session:s.session,boot:s.boot,run:s.run};started=true;observer=spawn('python3',['-B','pilot/io59/host-observer.py',owner.run],{stdio:['ignore','ignore','pipe']});record('OWNED_START',owner);fs.writeFileSync(path.join(E,requestId+'-owner.json'),JSON.stringify(owner,null,2)+'\n',{flag:'wx'});
 // Actual EKF absolute-position readiness takes ~41s in retained raw traces.
 // Read configuration AFTER convergence so its30s freshness does not time out.
 await until(s=>s.vehicle?.preflight?.length>0&&s.vehicle.preflight.filter(c=>c.id!=='configuration').every(c=>c.pass),55000);await post('refresh');await post('takeoff');
 const challenge=(await post('verify-lease')).challenge;lease=(await post('claim',{challenge})).lease;
 const start=performance.now();let next=start;let minimumAltitude=Infinity,maximumAltitude=-Infinity;
 while(performance.now()-start<20000){
  const s=await get();if(s.run!==owner.run||s.session!==owner.session||s.boot!==owner.boot||!s.physics||s.vehicle?.armed!==true||s.vehicle?.mode!=='LOITER')throw Error('HOLD_IDENTITY_MODE_OR_PHYSICS');
  const h=-s.physics.position[2];minimumAltitude=Math.min(minimumAltitude,h);maximumAltitude=Math.max(maximumAltitude,h);
  await post('input',{packet:{session:owner.session,boot:owner.boot,lease,seq:seq++,clientAt:performance.now(),focused:true,axes:[0,0,0,0],challenge:s.challenge}});
  // A missed INPUT tick is never replayed as a burst of old control writes.
  // Physics still admits/journals every1200Hz frame independently.
  next=performance.now()+50;await wait(Math.max(0,next-performance.now()));
 }
 record('HOLD_OBSERVED',{minimumAltitude,maximumAltitude,syntheticInputPackets:seq,requestedSeconds:20});
 await post('land');await post('end');ended=true;
 const final=await until(s=>!s.controllerActive&&!s.verifying,140000);record('CLOSED_OBSERVED',{run:final.run,lastError:final.lastError,review:final.review});
 const out=path.join(E,'runs',owner.run);const closure=JSON.parse(fs.readFileSync(out+'/closure.json'));const readback=JSON.parse(fs.readFileSync(out+'/readback.json'));if(closure.error||readback.status!=='PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION')throw Error('RAW_OR_CLOSURE_GATE');
 const receipt={status:'PASS_BOUNDED_COUPLED_CAPTURE',requestId,...reserved,owner,frames:readback.frames,RTF:readback.activeReceiveRTF,minimumAltitude,maximumAltitude,syntheticInputPackets:seq,speedup:1,capUs:500000,fullG1Accepted:false,postRetries:0,rawOriginalOracle:readback.status};
 fs.writeFileSync(path.join(E,requestId+'-driver-result.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(receipt));
}catch(error){
 record('FAILED',{error:error.message,owner,started,ended,noRetry:true});
 // No retry of an unknown mutation. On an observed active owned run, one explicit
 // LAND is a distinct safety action. Unknown/no fresh state requires human review.
 let cleanup=null;
 if(started&&!ended)try{const s=await get();if(s.run===owner.run&&s.controllerActive&&s.physics){if(s.vehicle?.armed===true)await post('land');const t=await get();if(t.physics?.ground&&t.vehicle?.armed===false){await post('end');cleanup='MANAGED_END_REQUESTED'}}}catch(e){cleanup='UNCONFIRMED:'+e.message}
 if(started&&!ended&&cleanup!=='MANAGED_END_REQUESTED'){
  const out=path.join(E,'runs',owner.run);if(!fs.existsSync(out+'/closure.json')){
   for(const [name,data]of [['benchmark-abort.json',{reason:'BENCH_FAILURE_CANONICAL_GUARD_REJECTED',notManagedLand:true,acceptedFlight:false,error:error.message}],['stop-request.json',{reason:'BENCH_SAFETY_ABORT_NO_FLIGHT_ACCEPTANCE',at:new Date().toISOString()}]])if(!fs.existsSync(out+'/'+name))fs.writeFileSync(out+'/'+name,JSON.stringify(data),{flag:'wx'});
   cleanup='OWNED_CIRCUIT_ABORT_REQUESTED_NOT_LAND';
  }
 }
 fs.writeFileSync(path.join(E,requestId+'-driver-result.json'),JSON.stringify({status:'FAIL',requestId,error:error.message,owner,cleanup,postRetries:0,fullG1Accepted:false},null,2)+'\n',{flag:'wx'});console.error(error);process.exitCode=1;
}finally{if(observer&&observer.exitCode===null&&observer.signalCode===null){const stopped=new Promise(r=>observer.once('exit',r));observer.kill('SIGTERM');await stopped}fs.fsyncSync(log);fs.closeSync(log)}
