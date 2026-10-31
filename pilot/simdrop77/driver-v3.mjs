import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {connect77} from './client-v2.mjs';
import {PROFILE,STREAMS,SCHEDULE,classify} from './contract.mjs';
const out=process.argv[2];if(!/^evidence\/simdrop77\/run0[1-6]$/.test(out))throw Error('OUTPUT_SCOPE');
const put=(n,v)=>writeFile(out+'/'+n,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const launch=JSON.parse(await readFile(out+'/launch.json','utf8')),order=SCHEDULE[launch.replication];assert.ok(order);
const m={scope:'OWNED_REAL_SIMDROP77',binarySha256:launch.binarySha256,containerId:launch.containerId,pid:launch.pid,startedAt:launch.startedAt,target:'42/1',session:out.split('/').at(-1),boot:launch.startedAt};
const checks=[],trials=[];let c,landRequested=false,failure=null,loss=null;
const armed=o=>!!(o.latest[0]?.fields.base_mode&128),mode=o=>o.latest[0]?.fields.custom_mode;
function check(id,data={}){checks.push({id,pass:true,...data});console.log(JSON.stringify(checks.at(-1)));}
async function hold(ms){const at=c.now();await c.wait(()=>c.now()-at>=ms,ms+2500);}
async function setmode(v){await c.command(176,{param1:1,param2:v},'MODE:'+v);await c.wait(o=>mode(o)===v,4000);}
async function origin(){await c.sensors(false);await c.release();await setmode(4);await c.emit(84,{target_system:42,target_component:1,coordinate_frame:1,type_mask:2552,x:0,y:0,z:-5,yaw:0},'RETURN_NED_ORIGIN_YAW0');await c.wait(o=>o.latest[32]&&Math.hypot(o.latest[32].fields.x,o.latest[32].fields.y)<.8&&Math.abs(o.latest[32].fields.z+5)<.5&&Math.abs(o.latest[30]?.fields.yaw)<.12,25000);await setmode(5);c.axes();await c.sensors(true);await hold(1500);}
function metrics(start){const f=c.obs.frames.slice(start).filter(f=>f.label==='ACCEPTED'&&f.id===32);assert.ok(f.length>20);const tail=f.filter(p=>p.at>=f.at(-1).at-3000);return {samples:f.length,minimumClearanceM:Math.min(...f.map(p=>12-p.fields.x-.3)),maximumX:Math.max(...f.map(p=>p.fields.x)),tailMaxSpeedMps:Math.max(...tail.map(p=>Math.abs(p.fields.vx)))};}
async function trial(name){await c.setAvoid(name==='BASELINE'?0:2);await hold(1000);const start=c.obs.frames.length;await c.mark(name+'_START',{replication:launch.replication,order,requestedRC2:1400});c.axes(1400,1500);
 if(name==='BASELINE')await c.wait(o=>o.latest[32].fields.x>12.3,18000);else await hold(16000);
 await c.mark(name+'_END');c.axes();const result=metrics(start);if(name==='BASELINE')assert.ok(result.maximumX>12.3);else assert.ok(result.maximumX>7&&result.minimumClearanceM>=1.2&&result.tailMaxSpeedMps<=.5);
 trials.push({name,...result});check('CONTROL_'+name,result);await origin();}
try{
 c=await connect77(m,out+'/wire.jsonl');await c.wait(o=>o.latest[0],15000);await c.command(512,{param1:148},'FIRMWARE_DISCOVERY');await c.wait(o=>o.latest[148],4000);
 for(const [id,interval]of Object.entries(STREAMS))await c.command(511,{param1:Number(id),param2:interval},'STREAM:'+id);
 for(const n of Object.keys(PROFILE))await c.read(n);
 await c.wait(o=>o.latest[24]?.fields.fix_type>=3&&o.latest[24]?.fields.satellites_visible>=10&&(o.latest[193]?.fields.flags&1)&&(o.latest[193]?.fields.flags&16)&&o.latest[32]&&o.latest[30],65000);
 await c.command(512,{param1:242},'HOME_DISCOVERY');await c.wait(o=>o.latest[242],4000);for(const n of Object.keys(PROFILE))await c.read(n);
 await c.wait(o=>o.frames.some(f=>f.id===132&&f.label==='ACCEPTED'&&f.fields.orientation===0&&f.fields.current_distance>900&&f.fields.current_distance<1400),8000);await put('preflight.json',c.obs.snapshot());check('PREFLIGHT');
 await setmode(4);await c.command(400,{param1:1},'NORMAL_ARM');await c.wait(armed,4000);await c.command(22,{param7:5},'TAKEOFF_5M');await c.wait(o=>armed(o)&&o.latest[245]?.fields.landed_state===2&&o.latest[33]?.fields.relative_alt>4500,35000);await setmode(5);c.axes();await hold(1500);
 for(const name of order)await trial(name);
 await c.setAvoid(2);await hold(1000);const approach=c.obs.frames.length;await c.mark('DROP_APPROACH_START');c.axes(1400,1500);await hold(16000);await c.mark('DROP_APPROACH_END');const before=metrics(approach);assert.ok(before.maximumX>7&&before.minimumClearanceM>=1.2&&before.tailMaxSpeedMps<=.5);check('DROP_VALID_SENSOR_STABLE',before);
 const start=c.obs.frames.length;await c.mark('DROP_REQUEST',{rc2Unchanged:1400});await c.sensors(false);const boot=c.obs.latest[30].fields.time_boot_ms;await c.mark('DROP_CUT_COMMITTED',{bootMs:boot,rc2:1400});
 await c.wait(o=>o.latest[30].fields.time_boot_ms-boot>=8000||o.latest[32].fields.x>12.3,15000);
 const duration=c.obs.latest[30].fields.time_boot_ms-boot;await c.mark('DROP_END',{reason:c.obs.latest[32].fields.x>12.3?'VIRTUAL_PLANE_BOUND':'GUEST_8S',guestDurationMs:duration});
 loss={...metrics(start),guestDurationMs:duration};loss.classification=classify(loss);console.log(JSON.stringify({finding:loss.classification,...loss}));
 // This is the experimenter's intervention, after the observation endpoint.
 c.axes();await c.mark('EXPERIMENTER_NEUTRAL_AFTER_ENDPOINT');await c.sensors(true);const restored=c.obs.frames.length;await c.mark('SENSOR_RESTORE_REQUEST');await c.wait(o=>o.frames.slice(restored).some(f=>f.label==='ACCEPTED'&&f.id===132),6000);check('PROXIMITY_RESTORED');
 await c.release();landRequested=true;await setmode(9);await c.wait(o=>!armed(o)&&o.latest[245]?.fields.landed_state===1&&Math.abs(o.latest[33]?.fields.relative_alt)<500,65000);await c.mark('LANDED_DISARMED');check('LANDED_DISARMED');await put('observed-final.json',c.obs.snapshot());
}catch(e){failure=e.stack;console.error(e.stack);if(c?.alive()&&armed(c.obs)&&!landRequested){try{await c.mark('EXPLICIT_FAILURE_CLEANUP_LAND');await c.sensors(false);await c.release();landRequested=true;await setmode(9);await c.wait(o=>!armed(o)&&o.latest[245]?.fields.landed_state===1,60000);}catch(clean){failure+='\nCleanup: '+clean.stack;}}}
finally{if(c)try{await c.close();}catch(e){failure=(failure??'')+'\nClosure: '+e.stack;}await put(failure?'driver-failure.json':'driver-result.json',{status:failure?'FAIL':'OBSERVATIONS_COMPLETE_NOT_SAFETY_PASS',error:failure,replication:launch.replication,order,checks,trials,loss,physics:'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32',actualHardware:false});if(failure)process.exitCode=1;}
