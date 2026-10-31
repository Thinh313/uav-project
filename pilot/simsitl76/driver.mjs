import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {connect76} from './client.mjs';
import {PROFILE,STREAMS} from './contract.mjs';
const out=process.argv[2];if(!/^evidence\/simsitl76\/run0[123]$/.test(out))throw Error('OUTPUT_SCOPE');
const put=(n,v)=>writeFile(out+'/'+n,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const launch=JSON.parse(await readFile(out+'/launch.json','utf8'));const m={scope:'OWNED_REAL_SITL76',binarySha256:launch.binarySha256,containerId:launch.containerId,pid:launch.pid,startedAt:launch.startedAt,target:'42/1',session:out.split('/').at(-1),boot:launch.startedAt};
const checks=[],phases=[];let c,landRequested=false,failure=null;
const armed=o=>!!(o.latest[0]?.fields.base_mode&128),mode=o=>o.latest[0]?.fields.custom_mode;
function check(id,data={}){checks.push({id,pass:true,...data});console.log(JSON.stringify(checks.at(-1)));}
async function hold(ms){const at=c.now();await c.wait(()=>c.now()-at>=ms,ms+2000);}
async function setmode(v){await c.command(176,{param1:1,param2:v},'MODE:'+v);await c.wait(o=>mode(o)===v,4000);}
async function origin(){await c.release();await setmode(4);await c.emit(84,{target_system:42,target_component:1,coordinate_frame:1,type_mask:2552,x:0,y:0,z:-5,yaw:0},'RETURN_NED_ORIGIN_YAW0');await c.wait(o=>o.latest[32]&&Math.hypot(o.latest[32].fields.x,o.latest[32].fields.y)<.8&&Math.abs(o.latest[32].fields.z+5)<.5&&Math.abs(o.latest[30]?.fields.yaw)<.12,25000);await setmode(5);c.axes();await hold(1500);}
async function phase(name,pitch,yaw,duration){const start=c.obs.frames.length,at=c.now();await c.mark(name+'_START',{pitch,yaw});c.axes(pitch,yaw);await hold(duration);c.axes();await c.mark(name+'_END');const frames=c.obs.frames.slice(start).filter(f=>f.label==='ACCEPTED');phases.push({name,at,endAt:c.now(),frames:frames.length});return frames;}
try{
 c=await connect76(m,out+'/wire.jsonl');await c.wait(o=>o.latest[0],15000);await c.command(512,{param1:148},'FIRMWARE_DISCOVERY');await c.wait(o=>o.latest[148],4000);
 for(const [id,interval] of Object.entries(STREAMS))await c.command(511,{param1:Number(id),param2:interval},'STREAM:'+id);
 for(const n of Object.keys(PROFILE))await c.read(n);
 await c.wait(o=>o.latest[24]?.fields.fix_type>=3&&o.latest[24]?.fields.satellites_visible>=10&&(o.latest[193]?.fields.flags&1)&&(o.latest[193]?.fields.flags&16)&&o.latest[32]&&o.latest[30],65000);
 await c.command(512,{param1:242},'HOME_DISCOVERY');await c.wait(o=>o.latest[242],4000);
 await c.wait(o=>o.frames.some(f=>f.id===132&&f.label==='ACCEPTED'&&f.fields.orientation===0&&f.fields.current_distance>900&&f.fields.current_distance<1400),8000);
 for(const n of Object.keys(PROFILE))await c.read(n); // fresh preflight after EKF startup, not stale initial reads
 await put('preflight.json',c.obs.snapshot());check('R76-01-firmware-config-ekf-home-proximity');
 await setmode(4);await c.command(400,{param1:1},'NORMAL_ARM');await c.wait(armed,4000);await c.command(22,{param7:5},'TAKEOFF_5M');await c.wait(o=>armed(o)&&o.latest[245]?.fields.landed_state===2&&o.latest[33]?.fields.relative_alt>4500,35000);await setmode(5);c.axes();await hold(1500);
 for(const [ps,ys] of [[1,1],[-1,1],[1,-1],[-1,-1]]){
  const initial=c.obs.latest[30].fields.pitch,frames=await phase('PITCH_YAW_'+ps+'_'+ys,1500+ps*50,1500+ys*80,1500);
  const a=frames.filter(f=>f.id===30).map(f=>f.fields),rc=frames.filter(f=>f.id===65).map(f=>f.fields);assert.ok(a.length>=5&&rc.some(f=>f.chan2_raw===1500+ps*50&&f.chan4_raw===1500+ys*80),'RC_ECHO');
  const pd=Math.max(...a.map(f=>ps*(f.pitch-initial))),yr=Math.max(...a.map(f=>ys*f.yawspeed));assert.ok(pd>.01&&yr>.03,'SIGNED_RESPONSE');assert.ok(a.every(f=>Math.abs(f.pitch)<.6&&Math.abs(f.roll)<.6));assert.ok(c.obs.latest[33].fields.relative_alt>3000&&c.obs.latest[33].fields.relative_alt<7000);check('R76-02-signed-'+ps+'-'+ys,{attitudes:a.length,peakSignedPitchDelta:pd,peakSignedYawRate:yr});await hold(2000);await origin();
 }
 await c.setAvoid(0);await c.mark('BASELINE_START',{virtualWallX:12,physicalContact:false});const baseStart=c.obs.frames.length; c.axes(1400,1500);await c.wait(o=>o.latest[32].fields.x>12.3,18000);c.axes();await c.mark('BASELINE_END');const baseline=c.obs.frames.slice(baseStart).filter(f=>f.label==='ACCEPTED'&&f.id===32).map(f=>f.fields);assert.ok(baseline.some(f=>f.x+.3>=12));check('R76-03-baseline-crossed-virtual-plane',{maximumX:Math.max(...baseline.map(f=>f.x))});
 // Stop synthetic rays outside the virtual half-space; return to origin explicitly.
 c.sensors(false);await origin();c.sensors(true);await c.setAvoid(2);await hold(1000);
 const enabledStart=c.obs.frames.length;await c.mark('AVOID_ENABLED_START',{virtualWallX:12,margin:2});c.axes(1400,1500);await hold(16000);c.axes();await c.mark('AVOID_ENABLED_END');
 const enabled=c.obs.frames.slice(enabledStart).filter(f=>f.label==='ACCEPTED'&&f.id===32);assert.ok(enabled.length>30&&Math.max(...enabled.map(f=>f.fields.x))>7);
 const clearance=Math.min(...enabled.map(f=>12-f.fields.x-.3)),tail=enabled.filter(f=>f.at>=enabled.at(-1).at-3000),speed=Math.max(...tail.map(f=>Math.abs(f.fields.vx)));assert.ok(clearance>=1.2&&speed<=.5,'AVOID_CLEARANCE_OR_STOP');
 const distances=c.obs.frames.slice(enabledStart).filter(f=>f.label==='ACCEPTED'&&f.id===132&&f.fields.orientation===0);assert.ok(distances.length>10&&distances.some(f=>f.fields.current_distance<350));check('R76-03-enabled-braking',{minimumSurfaceClearanceM:clearance,tailMaxForwardSpeedMps:speed,observedProximityFrames:distances.length});
 await hold(1000);await c.mark('SENSOR_DROPOUT_START');c.sensors(false);const dropStart=c.obs.frames.length,lastBoot=c.obs.latest[30].fields.time_boot_ms;await c.wait(o=>o.latest[30].fields.time_boot_ms-lastBoot>2500,8000);
 const drop=c.obs.frames.slice(dropStart).filter(f=>f.label==='ACCEPTED'),lastAtt=drop.filter(f=>f.id===30).at(-1),lastDistance=drop.filter(f=>f.id===132&&f.fields.orientation===0).at(-1);
 assert.ok(lastAtt&&(!lastDistance||lastAtt.fields.time_boot_ms-lastDistance.fields.time_boot_ms>700),'PROXIMITY_STILL_FRESH_AFTER_DROPOUT');check('R76-04-dropout-output-expired',{lastDistanceBootMs:lastDistance?.fields.time_boot_ms??null,lastAttitudeBootMs:lastAtt.fields.time_boot_ms,notProofOfAircraftFailstop:true});
 await c.mark('SENSOR_RESTORE');c.sensors(true);const restore=c.obs.frames.length;await c.wait(o=>o.frames.slice(restore).some(f=>f.id===132&&f.label==='ACCEPTED'&&f.fields.orientation===0),5000);check('R76-04-proximity-restored');
 await c.release();landRequested=true;await setmode(9);await c.wait(o=>!armed(o)&&o.latest[245]?.fields.landed_state===1&&Math.abs(o.latest[33]?.fields.relative_alt)<500,65000);await c.mark('LANDED_DISARMED');check('R76-02-landed-disarmed');await put('observed-final.json',c.obs.snapshot());
}catch(e){failure=e.stack;console.error(e.stack);if(c?.alive()&&armed(c.obs)&&!landRequested){try{await c.mark('EXPLICIT_FAILURE_CLEANUP_LAND');await c.release();landRequested=true;await setmode(9);await c.wait(o=>!armed(o)&&o.latest[245]?.fields.landed_state===1,60000);}catch(clean){failure+='\nCleanup: '+clean.stack;}}}
finally{if(c)try{await c.close();}catch(e){failure=(failure??'')+'\nClosure: '+e.stack;}await put(failure?'driver-failure.json':'driver-result.json',{status:failure?'FAIL':'PASS_SCOPED_INTERNAL_SITL',error:failure,checks,phases,physics:'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32',actualHardware:false,signature:false});if(failure)process.exitCode=1;}
