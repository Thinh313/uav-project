import {SimulationLink} from './link.mjs';
import {readFile,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
const [run,rawDuration]=process.argv.slice(2),duration=Number(rawDuration);
if(![450,550,900,3200].includes(duration))throw Error('Explicit pause allowlist');
const E=`evidence/sim32-pacing02/runs/${run}`,link=new SimulationLink(run);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let paused=false,pid=null,probe={requestedPauseMs:duration,noArmOrMission:true,automaticCommandReplay:false};
async function until(fn,ms=10000){const end=Date.now()+ms;while(Date.now()<end){try{if(fn())return;}catch{}await sleep(50);}throw Error('Probe observation deadline');}
try{
 await link.connect();await until(()=>link.freshness(0));await link.readSimulatorConfiguration();
 await sleep(4000);link.attest();probe.frameBefore=link.physics().frame;
 const launch=JSON.parse(await readFile(E+'/launch.json','utf8'));pid=launch.backendPid;
 const command=execFileSync('ps',['-p',String(pid),'-o','command='],{encoding:'utf8'});
 if(!command.includes(`/pilot/sim32-pacing02/backend.py ${run} `))throw Error('Owned backend PID mismatch');
 probe.pauseBeginHostNs=process.hrtime.bigint().toString();process.kill(pid,'SIGSTOP');paused=true;
 if(duration===3200){
  await sleep(1800);probe.stalePhysicsObserved=false;
  try{link.physics();}catch(e){probe.stalePhysicsObserved=e.message.includes('stale');}
  const before=link.frames.filter(x=>x.direction==='out'&&x.id===76).length;
  try{await link.command('guided');probe.controlBlockedWhileStale=false;}catch(e){probe.controlBlockedWhileStale=e.message.includes('stale');}
  probe.noControlBytesWhileStale=before===link.frames.filter(x=>x.direction==='out'&&x.id===76).length;
  await sleep(Math.max(0,duration-Number(process.hrtime.bigint()-BigInt(probe.pauseBeginHostNs))/1e6));
 }else{await sleep(duration);}
 process.kill(pid,'SIGCONT');paused=false;probe.resumeHostNs=process.hrtime.bigint().toString();
 probe.actualPauseMs=Number(BigInt(probe.resumeHostNs)-BigInt(probe.pauseBeginHostNs))/1e6;
 await sleep(6000);
 try{const s=link.physics();probe.frameAfter=s.frame;probe.freshAfterResume=true;probe.backendResumedAfterStaleBoundary=duration===3200&&s.frame>probe.frameBefore;}
 catch(e){probe.freshAfterResume=false;probe.afterResumeError=e.message;}
 if(duration<3000){if(!probe.freshAfterResume||probe.frameAfter<=probe.frameBefore)throw Error('Ground probe did not regain observed frame continuity');await link.readSimulatorConfiguration();}
 probe.controlCommandsSent=link.frames.filter(x=>x.direction==='out'&&x.id===76&&[400,176].includes(x.fields.command)).length;
 if(probe.controlCommandsSent!==0)throw Error('Ground probe unexpectedly sent control');
 probe.status=duration===3200&&probe.backendResumedAfterStaleBoundary?'STALE_SUSPENSION_GAP_OBSERVED':'CAP_CAPTURE_PENDING_RAW_VERIFICATION';
}catch(e){probe.status='PROBE_FAILED';probe.error=e.stack;process.exitCode=1;}
finally{
 if(paused&&pid){process.kill(pid,'SIGCONT');probe.unpausedForOwnedClosure=true;}
 await writeFile(E+'/pause-probe.json',JSON.stringify(probe,null,2)+'\n',{flag:'wx'});
 await writeFile(E+'/probe-review.json',JSON.stringify(link.review(),null,2)+'\n',{flag:'wx'});
 link.disconnect();
 try{execFileSync('python3',['-B','pilot/sim32-pacing02/runtime.py','stop',run],{timeout:25000});}
 catch(e){console.error('Closure failure',e.message);process.exitCode=1;}
 console.log(JSON.stringify(probe));
}
