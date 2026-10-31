import {encodeFull,FullFramer,hex} from '../apstream40/wire.mjs';
export const BINARY='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482';
export const PORT=5896;
export const STREAMS={1:500000,24:500000,30:50000,32:50000,33:100000,36:100000,65:100000,132:100000,193:500000,245:500000};
export const PROFILE={MAV_SYSID:[4,[42]],MAV_GCS_SYSID:[4,[255]],SERIAL0_PROTOCOL:[2,[2]],ARMING_SKIPCHK:[6,[0]],
 PRX1_TYPE:[2,[2]],PRX1_ORIENT:[2,[0]],PRX1_YAW_CORR:[4,[0]],PRX_FILT:[9,[0]],PRX_ALT_MIN:[9,[0]],
 AVOID_ENABLE:[2,[0,2]],AVOID_BEHAVE:[2,[1]],AVOID_MARGIN:[9,[2]],AVOID_BACKUP_SPD:[9,[0]],AVOID_ALT_MIN:[9,[0]],
 FENCE_ENABLE:[2,[1]],FENCE_RADIUS:[9,[50]],FS_GCS_ENABLE:[2,[1]],FS_GCS_TIMEOUT:[9,[5]],FS_OPTIONS:[6,[0]],
 RC1_MIN:[4,[1000]],RC1_MAX:[4,[2000]],RC2_MIN:[4,[1000]],RC2_MAX:[4,[2000]],RC4_MIN:[4,[1000]],RC4_MAX:[4,[2000]]};
export function manifest(m){if(m?.scope!=='OWNED_REAL_SITL76'||m.binarySha256!==BINARY||!/^[a-f0-9]{64}$/.test(m.containerId??'')||!Number.isSafeInteger(m.pid)||m.pid<=0||!m.startedAt||m.target!=='42/1'||!/^run0[123]$/.test(m.session)||m.boot!==m.startedAt)throw Error('OWNED_MANIFEST');}
export function validate(raw){
 const d=new FullFramer(),a=d.push(raw,0,0);if(a.length!==1||d.snapshot().pendingBytes||a[0].rawHex!==hex(raw))throw Error('ONE_FRAME');
 const f=a[0],p=f.fields;if(f.signed||!f.crcVerified||f.system!==255||f.component!==190)throw Error('GCS_IDENTITY');
 if(f.id===0){if(p.type!==6||p.autopilot!==8||p.custom_mode!==0||p.base_mode!==0||p.system_status!==4)throw Error('HEARTBEAT');return f;}
 if(f.id===132){if(p.type!==0||p.id!==p.orientation||p.orientation>7||p.min_distance!==20||p.max_distance!==2000||p.current_distance<20||p.current_distance>2001||p.covariance!==255||p.horizontal_fov!==0||p.vertical_fov!==0||p.quaternion.some(x=>x!==0)||p.signal_quality!==0)throw Error('SENSOR_DOMAIN');return f;}
 if(p.target_system!==42||p.target_component!==1)throw Error('TARGET');
 if(f.id===20){if(!PROFILE[p.param_id]||p.param_index!==-1)throw Error('READ_PROFILE');}
 else if(f.id===23){if(p.param_id!=='AVOID_ENABLE'||p.param_type!==2||![0,2].includes(p.param_value))throw Error('SET_PROFILE');}
 else if(f.id===70){const c=Array.from({length:8},(_,i)=>p['chan'+(i+1)+'_raw']);if(![0,1500].includes(c[0])||![0,1400,1450,1500,1550].includes(c[1])||![0,1500].includes(c[2])||![0,1420,1500,1580].includes(c[3])||c.slice(4).some(v=>v!==65535)||Array.from({length:10},(_,i)=>p['chan'+(i+9)+'_raw']).some(v=>v!==0))throw Error('RC_PROFILE');}
 else if(f.id===84){if(p.coordinate_frame!==1||p.type_mask!==2552||p.x!==0||p.y!==0||p.z!==-5||p.yaw!==0||[p.vx,p.vy,p.vz,p.afx,p.afy,p.afz,p.yaw_rate].some(x=>x!==0))throw Error('RETURN_ORIGIN_ONLY');}
 else if(f.id===76){
  const zeros=ks=>ks.every(i=>p['param'+i]===0);if(p.confirmation!==0)throw Error('NO_RETRY');
  if(p.command===512){if(![148,242].includes(p.param1)||!zeros([2,3,4,5,6,7]))throw Error('DISCOVERY');}
  else if(p.command===511){if(STREAMS[p.param1]!==p.param2||!zeros([3,4,5,6,7]))throw Error('STREAM');}
  else if(p.command===176){if(p.param1!==1||![4,5,9].includes(p.param2)||!zeros([3,4,5,6,7]))throw Error('MODE');}
  else if(p.command===400){if(p.param1!==1||!zeros([2,3,4,5,6,7]))throw Error('NO_FORCE_ARM');}
  else if(p.command===22){if(p.param7!==5||!zeros([1,2,3,4,5,6]))throw Error('TAKEOFF');}
  else throw Error('COMMAND_NOT_ALLOWED');
 } else throw Error('MESSAGE_NOT_ALLOWED');return f;
}
export function packet(id,p,seq=0){const raw=encodeFull(id,p,{system:255,component:190,seq:seq%256});validate(raw);return raw;}
export function sensorGuard(s,m,now){manifest(m);if(s.target!==m.target||s.session!==m.session||s.boot!==m.boot||s.frame!=='BODY_FRD_METRES'||s.clock!=='HOST_MONOTONIC_MS')throw Error('SENSOR_CONTEXT');if(!Number.isSafeInteger(s.at)||s.at>now||now-s.at>200)throw Error('SENSOR_STALE');if(!Number.isInteger(s.bootMs)||s.bootMs<0||s.bootMs>2**32-1||!Array.isArray(s.ranges)||s.ranges.length!==8||s.ranges.some(v=>!Number.isFinite(v)||v<.2||v>20.01))throw Error('SENSOR_RANGE');return true;}
export function rays(position,attitude,wallX=12){
 if(!position||!attitude||![position.x,position.y,position.z,attitude.roll,attitude.pitch,attitude.yaw,wallX].every(Number.isFinite))throw Error('RAY_DOMAIN');
 const {roll:r,pitch:p,yaw:y}=attitude,cr=Math.cos(r),sr=Math.sin(r),cp=Math.cos(p),sp=Math.sin(p),cy=Math.cos(y),sy=Math.sin(y);
 return Array.from({length:8},(_,i)=>{const a=i*Math.PI/4;const dx=cy*cp*Math.cos(a)+(cy*sp*sr-sy*cr)*Math.sin(a);const t=Math.abs(dx)>1e-9?(wallX-position.x)/dx:Infinity;return t>=.2&&t<=20?t:20.01;});
}
