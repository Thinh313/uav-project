import {SimulationLink} from './link.mjs';
import {readFile,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const [run,rawMs]=process.argv.slice(2),ms=Number(rawMs);
if(![450,550,900,1400,3200].includes(ms))throw Error('Pause allowlist');
const E=`evidence/sim32-pipe03/runs/${run}`,link=new SimulationLink(run),checks=[];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let pid=null,paused=false;
async function wait(fn,t=15000){const end=Date.now()+t;while(Date.now()<end){if(await fn())return;await sleep(30);}throw Error('Fault observation deadline');}
function check(name,pass,detail){checks.push({name,pass:!!pass,detail});if(!pass)throw Error(name);}
try{
 await link.connect();await wait(()=>link.freshness(0));await link.readSimulatorConfiguration();
 await wait(async()=>{try{return !!JSON.parse(await readFile(E+'/pause-ready.json','utf8'));}catch{return false;}});
 const ready=JSON.parse(await readFile(E+'/pause-ready.json','utf8'));pid=ready.pid;paused=true;
 const cmd=execFileSync('ps',['-p',String(pid),'-o','command='],{encoding:'utf8'});
 if(!cmd.includes(`/pilot/sim32-pipe03/backend.py ${run} `))throw Error('Foreign backend PID');
 const nodeBegin=process.hrtime.bigint();await sleep(ms);process.kill(pid,'SIGCONT');paused=false;const nodeEnd=process.hrtime.bigint();
 await sleep(2000);
 if(ms>=1400){
  await wait(async()=>{try{return !!JSON.parse(await readFile(E+'/backend-summary.json','utf8'));}catch{return false;}});
  const summary=JSON.parse(await readFile(E+'/backend-summary.json','utf8'));
  check('epoch terminal; no automatic revival',summary.epochTerminal&&['STALE_OR_SUSPENDED','DUPLICATE_FRAME_NO_REPLAY'].includes(summary.epochReason),summary.epochReason);
  check('no repeated model or cached sensor echo',summary.frames===ready.committedFrames+(ms===1400?1:0),{frozen:ready.committedFrames,final:summary.frames});
  const before=link.frames.filter(x=>x.direction==='out'&&x.id===76&&[176,400].includes(x.fields.command)).length;
  let refused=false;try{await link.command('guided');}catch(e){refused=e.message.includes('stale')||e.message.includes('epoch');}
  check('terminal epoch blocks command before wire',refused&&before===link.frames.filter(x=>x.direction==='out'&&x.id===76&&[176,400].includes(x.fields.command)).length);
 }else{
  const physics=link.physics();check('short pause continues same live epoch',physics.epoch===ready.epoch&&physics.frame>ready.framePending);
  await link.readSimulatorConfiguration();check('actual speedup1/rate1200 unchanged',link.simConfiguration.pass);
 }
 check('Node/backend calibration has qualified domain',link.clockCalibration.matches>=1&&!link.clockCalibration.error,{matches:link.clockCalibration.matches,domain:link.backendDomain});
 await writeFile(E+'/fault-probe.json',JSON.stringify({status:'PASS',requestedPauseMs:ms,nodePauseMs:Number(nodeEnd-nodeBegin)/1e6,clockDomain:'host-node-hrtime',ready,checks,noArmOrMission:true,automaticRetries:0},null,2)+'\n',{flag:'wx'});
}catch(e){checks.push({name:'probe',pass:false,error:e.stack});await writeFile(E+'/fault-probe.json',JSON.stringify({status:'FAIL',checks},null,2)+'\n',{flag:'wx'});process.exitCode=1;}
finally{
 if(paused&&pid)process.kill(pid,'SIGCONT');
 await writeFile(E+'/fault-review.json',JSON.stringify(link.review(),null,2)+'\n',{flag:'wx'});
 link.disconnect();execFileSync('python3',['-B','pilot/sim32-pipe03/runtime.py','stop',run],{timeout:25000});
 console.log(JSON.stringify({run,status:checks.every(x=>x.pass)?'PASS':'FAIL',checks}));
}
