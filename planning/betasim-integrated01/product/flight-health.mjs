/** Source-derived control guard for the versioned Workbench SIM profile.
 * Original M1 numeric safety bounds are retained; the declared Workbench
 * spatial envelope differs explicitly (150 m radius / 30 m altitude).
 */
import'../../../pilot/field02/flight/isolated-loader.mjs';
import{need,sha,canonical}from'./mission.mjs';
const{FullFramer}=await import('../../../pilot/apstream40/wire.mjs');
const AGE={heartbeat:1500,position:1500,home:3000,land:1500,gps:1500,battery:1500,ekf:1500,parameters:10000};
const critical=1|2|4|8|32|2097152,prearm=1<<28;
export class FlightHealth{
 constructor({context,parameters,record,clock}){need(context?.profileId==='WORKBENCH_SIM_V1'&&typeof record==='function'&&typeof clock==='function','HEALTH_PROFILE_CONTEXT');need(parameters&&Object.keys(parameters).length===39,'HEALTH_EXACT_TYPED_39');this.context=structuredClone(context);this.specs=structuredClone(parameters);this.record=record;this.clock=clock;this.framer=new FullFramer();this.rows={};this.parameters=new Map();this.firmware=false;this.failed=null;this.previousSequence=-1;this.last=-1;this.bootMs=-1;this.confirmedHome=null;this.sealed=false;this.armed=false;this.armIntentUntil=-1;this.armObservedAt=-1;}
 fail(reason){this.failed??=reason;throw Error(reason);}
 armIntent(){const state=this.assess(true);this.armIntentUntil=state.now+5000;return{untilHostMs:this.armIntentUntil,context:this.context};}
 receive(bytes,at,rawRef){try{need(Number.isSafeInteger(at)&&at>=this.last,'HEALTH_CLOCK_REGRESSION');if(this.rows[0]&&at-this.rows[0].at>3000)this.fail('HEALTH_HARD_HEARTBEAT_3000MS');this.last=at;need(rawRef&&rawRef.durable===true,'HEALTH_ROOT_RAW_FSYNC_REFERENCE');
  for(const f of this.framer.push(bytes,at,at)){
   if(f.system!==42||f.component!==1)continue;
   if(!f.crcVerified||f.signed||!f.known)this.fail('HEALTH_CRC_OR_SIGNED_UNKNOWN');
   const delta=this.previousSequence<0?1:(f.seq-this.previousSequence+256)%256;if(delta===128)this.fail('HEALTH_SEQUENCE_AMBIGUOUS');if(delta===0||delta>128)continue;this.previousSequence=f.seq;
   const p=f.fields;if(f.id===242&&(Math.abs(p.latitude)>900000000||Math.abs(p.longitude)>1800000000||p.latitude===0&&p.longitude===0||Math.abs(p.altitude)>10000000))this.fail('HEALTH_HOME_WGS84_DOMAIN');if(f.id===33&&(Math.abs(p.lat)>900000000||Math.abs(p.lon)>1800000000))this.fail('HEALTH_POSITION_WGS84_DOMAIN');
   if(f.id===0){if(p.type!==2||p.autopilot!==3)this.fail('HEALTH_AUTOPILOT_IDENTITY');const next=(p.base_mode&128)!==0;if(next&&!this.armed){if(this.armIntentUntil<at)this.fail('HEALTH_UNREQUESTED_ARM');this.armIntentUntil=-1;this.armObservedAt=at;this.confirmedHome=null;}this.armed=next;}
   if(f.id===148){if(p.flight_sw_version!==67568127||String.fromCharCode(...p.flight_custom_version)!=='dbe79216')this.fail('HEALTH_FIRMWARE_4_7_1');this.firmware=true;}
   if(f.id===22&&Object.hasOwn(this.specs,p.param_id)){
    const raw=Buffer.from(f.rawHex,'hex'),header=raw[0]===253?10:6,bits=raw.subarray(header,header+4).toString('hex'),expected=this.specs[p.param_id];
    if(!Number.isFinite(p.param_value)||p.param_type!==expected.mavType||bits!==expected.float32Hex)this.fail('HEALTH_TYPED_PARAMETER:'+p.param_id);
    this.parameters.set(p.param_id,{at,bits,type:p.param_type,rawRef});
   }
   if(f.id===33){const next=p.time_boot_ms;if(this.bootMs>=0&&(next-this.bootMs+4294967296)%4294967296>=2147483648)this.fail('HEALTH_AP_REBOOT');this.bootMs=next;}
   if([0,1,24,33,193,242,245].includes(f.id))this.rows[f.id]={at,fields:p,rawRef};
   if(f.id===242&&this.confirmedHome&&this.homeHash()!==this.confirmedHome)this.fail('HEALTH_CONFIRMED_HOME_CHANGED');
  }
 }catch(error){this.failed??=error.message;throw error;}
 }
 age(id,limit,now){const row=this.rows[id];need(row&&now-row.at>=0&&now-row.at<=limit,'HEALTH_STALE_'+id);return row.fields;}
 homeHash(){const h=this.rows[242]?.fields;return h?sha({latE7:h.latitude,lonE7:h.longitude,altMSLmm:h.altitude}):null;}
 confirmHome(displayedHash,actionId){const current=this.assess(false);need(current.armed&&this.armObservedAt>=0&&this.rows[242]?.at>this.armObservedAt&&typeof actionId==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(actionId),'HEALTH_POST_ARM_FRESH_HOME_ACTION_REQUIRED');need(this.homeHash()&&displayedHash===this.homeHash(),'HEALTH_EXPLICIT_DISPLAYED_HOME');this.confirmedHome=displayedHash;return displayedHash;}
 assess(ground=false){
  if(this.failed)throw Error(this.failed);const now=this.clock();if(this.rows[0]&&now-this.rows[0].at>3000)this.fail('HEALTH_HARD_HEARTBEAT_3000MS');need(Number.isSafeInteger(now)&&now>=this.last,'HEALTH_CLOCK_REGRESSION');
  const h=this.age(0,AGE.heartbeat,now),p=this.age(33,AGE.position,now),home=this.age(242,AGE.home,now),land=this.age(245,AGE.land,now),gps=this.age(24,AGE.gps,now),battery=this.age(1,AGE.battery,now),ekf=this.age(193,AGE.ekf,now);
  need(this.firmware,'HEALTH_FIRMWARE_REQUIRED');need([3,4,5,6,8].includes(gps.fix_type)&&gps.satellites_visible>=6&&gps.satellites_visible<=254&&gps.eph>=0&&gps.eph<=200,'HEALTH_GPS');
  need(battery.voltage_battery!==65535&&battery.voltage_battery>=21000&&(ekf.flags&~0x037f)===0&&(ekf.flags&55)===55,'HEALTH_BATTERY_EKF');
  const active=battery.onboard_control_sensors_present&battery.onboard_control_sensors_enabled;
  need((active&critical)===critical&&(battery.onboard_control_sensors_health&critical)===critical,'HEALTH_CRITICAL_SENSORS');
  if(ground)need((battery.onboard_control_sensors_present&prearm)!==0&&(battery.onboard_control_sensors_enabled&prearm)!==0&&(battery.onboard_control_sensors_health&prearm)!==0,'HEALTH_PREARM');
  need(Math.abs(p.alt/1000-home.altitude/1000-p.relative_alt/1000)<=1,'HEALTH_ALTITUDE_DATUM');
  const distance=Math.hypot((p.lat-home.latitude)/1e7*111319,(p.lon-home.longitude)/1e7*111319*Math.cos(p.lat/1e7*Math.PI/180)),armed=(h.base_mode&128)!==0;
  if(ground)need(!armed&&land.landed_state===1&&Math.abs(p.relative_alt/1000)<=.4&&distance<=10,'HEALTH_DISARMED_GROUND');
  need(distance<=150&&p.relative_alt/1000<=30,'HEALTH_WORKBENCH_ENVELOPE');
  for(const name of Object.keys(this.specs)){const v=this.parameters.get(name);need(v&&now-v.at>=0&&now-v.at<=AGE.parameters,'HEALTH_PARAMETER_FRESH:'+name);}
  return{ready:true,now,armed,mode:h.custom_mode,landed:land.landed_state,distance,relativeHomeM:p.relative_alt/1000,homeHash:this.homeHash(),confirmedHome:this.confirmedHome===this.homeHash(),ages:AGE,context:this.context,authorityRestorable:false};
 }
 snapshot(binding){const health=this.assess(false);need(canonical(binding.context??this.context)===canonical(this.context),'HEALTH_PRODUCT_CONTEXT');return{...binding,targetSystem:42,targetComponent:1,verifiedOriginal:true,heartbeatHostMs:this.rows[0].at,positionHostMs:this.rows[33].at,homeHostMs:this.rows[242].at,landHostMs:this.rows[245].at,gpsHostMs:this.rows[24].at,batteryHostMs:this.rows[1].at,ekfHostMs:this.rows[193].at,homeConfirmed:health.confirmedHome,homeHash:health.homeHash,relativeHomeM:health.relativeHomeM,homeDistanceM:health.distance,mode:health.mode,armed:health.armed,failsafe:false,uncertain:false,typedProfileVerified:true,firmwareVerified:this.firmware,originalHealthProof:health};}
}
