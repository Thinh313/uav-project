import {encodeFull,FullFramer,hex} from '../apstream40/wire.mjs';
export const BINARY='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482';
export const PROFILE={MAV_SYSID:[4,[42]],MAV_GCS_SYSID:[4,[255]],SERIAL0_PROTOCOL:[2,[2]],ARMING_SKIPCHK:[6,[0]],BATT_MONITOR:[2,[4]],BATT_ARM_VOLT:[9,[0,50]],FENCE_ENABLE:[2,[1]],FENCE_TYPE:[2,[2]],FENCE_ACTION:[2,[1]],FENCE_RADIUS:[9,[10,30]],FENCE_MARGIN:[9,[2,40]],FS_GCS_ENABLE:[2,[1]],FS_GCS_TIMEOUT:[9,[5]],FS_OPTIONS:[6,[0]],RTL_ALT_M:[9,[10]],RTL_ALT_FINAL_M:[9,[0]],RTL_LOIT_TIME:[6,[1000]]};
export const REQUEST_IDS=[148,242];export const STREAM_IDS=[1,24,33,162,193,245];
export function assertManifest(m){if(m?.scope!=='OWNED_REAL_SITL_FLIGHT_TEST_ONLY'||m.binarySha256!==BINARY||!/^[a-f0-9]{64}$/.test(m.containerId??'')||!Number.isSafeInteger(m.pid)||m.pid<=0||!m.startedAt||m.system!==42||m.component!==1||!m.session)throw Error('OWNED_SIMULATOR_MANIFEST');}
export function validateTX(raw){
 const d=new FullFramer(),fs=d.push(raw,0,0);if(fs.length!==1||d.snapshot().pendingBytes||fs[0].rawHex!==hex(raw))throw Error('EXACT_SINGLE_PACKET');
 const f=fs[0],p=f.fields;if(f.signed||!f.crcVerified||f.system!==255||f.component!==190)throw Error('LOCAL_GCS_REQUIRED');
 if(f.id===0){if(p.type!==6||p.autopilot!==8||p.base_mode!==0||p.custom_mode!==0||p.system_status!==4)throw Error('GCS_HEARTBEAT_PROFILE');return f;}
 if(p.target_system!==42||p.target_component!==1)throw Error('EXACT_SIMULATOR_TARGET');
 if(f.id===20){if(!PROFILE[p.param_id]||p.param_index!==-1)throw Error('NAMED_READ_PROFILE');}
 else if(f.id===23){const r=PROFILE[p.param_id];if(!r||p.param_type!==r[0]||!r[1].includes(p.param_value))throw Error('TYPED_SET_PROFILE');}
 else if(f.id===76){
  if(p.confirmation!==0)throw Error('NO_RETRY');const zeros=ks=>ks.every(k=>p['param'+k]===0);
  if(p.command===512){if(!REQUEST_IDS.includes(p.param1)||!zeros([2,3,4,5,6,7]))throw Error('REQUEST_PROFILE');}
  else if(p.command===511){if(!STREAM_IDS.includes(p.param1)||p.param2!==500000||!zeros([3,4,5,6,7]))throw Error('STREAM_PROFILE');}
  else if(p.command===176){if(p.param1!==1||![4,6,9].includes(p.param2)||!zeros([3,4,5,6,7]))throw Error('MODE_PROFILE');}
  else if(p.command===400){if(![0,1].includes(p.param1)||!zeros([2,3,4,5,6,7]))throw Error('NO_FORCE_ARM');}
  else if(p.command===22){if(p.param7!==10||!zeros([1,2,3,4,5,6]))throw Error('TAKEOFF_PROFILE');}
  else throw Error('COMMAND_NOT_ALLOWED');
 }else if(f.id===86){if(p.coordinate_frame!==6||p.type_mask!==3576||p.alt!==10||p.lat_int<108530000||p.lat_int>108550000||p.lon_int!==1068070000||[p.vx,p.vy,p.vz,p.afx,p.afy,p.afz,p.yaw,p.yaw_rate].some(x=>x!==0))throw Error('LOCAL_SURVEY_POSITION_PROFILE');}
 else throw Error('OUTPUT_NOT_ALLOWED');return f;
}
export function packet(id,p,seq=0){const b=encodeFull(id,p,{system:255,component:190,seq});validateTX(b);return b;}
export const target={target_system:42,target_component:1};
