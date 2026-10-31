import {writeFile,mkdir} from 'node:fs/promises';
import {SitlLink} from '../services/sitl.mjs';
import {DEFAULT_SURVEY,surveyPackage,localFrame,DEMO_ORIGIN} from '../app/core/survey.mjs';
const dir=process.env.AERIS_EVIDENCE_DIR??'evidence/flight01';await mkdir(dir,{recursive:true});const link=new SitlLink({timeoutMs:20000});const checks=[];
function check(name,pass,detail={}){checks.push({name,pass,...detail});if(!pass)throw Error(name);}
async function until(fn,ms=30000){const end=Date.now()+ms;while(Date.now()<end){if(fn())return;await new Promise(r=>setTimeout(r,200));}throw Error('Observation timeout');}
try{
 await link.connect();await until(()=>link.freshness(0));await link.readConfiguration();await until(()=>link.preflight().every(c=>c.pass));const ready=link.snapshot();check('actual-autopilot-telemetry',ready.connected&&ready.firmware==='4.7.1',{firmware:ready.firmware,vehicle:ready.vehicle,position:ready.position,preflight:ready.preflight});
 const frame=localFrame(DEMO_ORIGIN);const settings={...DEFAULT_SURVEY,name:'AB01 SITL survey',polygon:[{x:0,y:0},{x:45,y:0},{x:45,y:45},{x:0,y:45}].map(p=>frame.reverse(p)),altitude:15,speed:6,sideOverlap:30,frontOverlap:30};
 const pkg=surveyPackage(settings);await writeFile(`${dir}/ab01-survey.json`,JSON.stringify(pkg,null,2));
 await link.upload(pkg);check('upload-ack-plus-readback',link.mission.state==='verified',{count:link.mission.compiled.items.length,commands:link.mission.compiled.items.map(x=>x.command)});
 await link.command('guided');check('guided-observed',link.snapshot().mode==='GUIDED');
 await link.command('arm');check('armed-observed',link.snapshot().armed===true);
 await link.command('auto');check('auto-observed',link.snapshot().mode==='AUTO');
 await until(()=>link.events.some(e=>e.type==='mission-item-reached'&&e.detail.seq>=3),45000);check('actual-mission-progress',true,{current:link.snapshot().mission.current,relativeAltitude:link.snapshot().position?.relativeAltitude});
 const lastNav=link.mission.compiled.items.filter(i=>i.command===16).at(-1).seq;await until(()=>link.snapshot().armed===false&&link.execution.state==='completed'&&link.events.some(e=>e.type==='mission-item-reached'&&e.detail.seq===lastNav),90000);check('mission-return-and-land',true,{mode:link.snapshot().mode,armed:link.snapshot().armed,relativeAltitude:link.snapshot().position?.relativeAltitude});
 const triggerCommands=link.mission.readback.filter(i=>i.command===206);check('camera-commands-retained',triggerCommands.length>0&&triggerCommands.some(i=>i.param1>0)&&triggerCommands.some(i=>i.param1===0),{count:triggerCommands.length,scope:'Actual autopilot readback of commands; imaging/CAM log verified separately'});
 await writeFile(`${dir}/sitl-journal.json`,JSON.stringify(link.journal(),null,2)+'\n');link.disconnect();check('disconnect-clears-readiness',!link.snapshot().connected&&link.mission.state==='empty');
}catch(e){checks.push({name:'run-error',pass:false,message:e.message});await writeFile(`${dir}/sitl-journal-failed.json`,JSON.stringify(link.journal(),null,2)+'\n');link.disconnect();process.exitCode=1;}
await writeFile(`${dir}/sitl-qa.json`,JSON.stringify({checks,scope:'Real local ArduPilot SITL; no physical vehicle or payload'},null,2)+'\n');console.log(JSON.stringify(checks,null,2));
