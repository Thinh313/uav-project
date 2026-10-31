export const CONTRACT=Object.freeze({id:'COACH02_MANUAL_REFERENCE_V1',dtS:.05,inputAgeMaxMs:200,leaseMs:200,neutralFreshMs:200,clockMaxRttMs:200,clockMaxWidthMs:50,clockMaxAgeMs:30000,clockDriftPpm:100,maxRows:2000,maxRunBytes:8*2**20,maxStoreBytes:64*2**20,source:'MOCK_VELOCITY_REFERENCE_NOT_HERA_6DOF_OR_ARDUPILOT',axesUnits:'NORMALIZED_BODY_VELOCITY_AND_YAW_RATE_NOT_PWM',frames:'POSITION_ENU_M_HEADING_DEG_CLOCKWISE_FROM_NORTH',clockSourceMethod:'PERFORMANCE_NOW_HANDLER_RECEIPT_NOT_PHYSICAL_HID_TIME'});
export const PROFILES=Object.freeze({unloaded:{id:'unloaded',tauS:.55,speedMS:3,climbMS:1.2,yawRateDegS:45,windEastMS:.35,windNorthMS:.1},loaded:{id:'loaded',tauS:.95,speedMS:3,climbMS:1.2,yawRateDegS:45,windEastMS:.35,windNorthMS:.1}});
export const EXERCISES=Object.freeze({hover:{id:'hover',name:'Giữ vị trí',durationS:20,horizontalToleranceM:1.5,altitudeToleranceM:.8,headingToleranceDeg:8,minimumWithinFraction:.9},straight:{id:'straight',name:'Bay thẳng và dừng',durationS:20,horizontalToleranceM:2,altitudeToleranceM:.8,headingToleranceDeg:10,minimumWithinFraction:.9},turn:{id:'turn',name:'Xoay hướng và ổn định',durationS:18,horizontalToleranceM:1.5,altitudeToleranceM:.8,headingToleranceDeg:10,minimumWithinFraction:.9}});
export const zero=()=>({roll:0,pitch:0,throttle:0,yaw:0});
export const need=(v,m)=>{if(!v)throw Error(m);};
export const wrap=a=>((a+180)%360+360)%360-180;
export function validAxes(a){return a&&Object.keys(a).sort().join(',')==='pitch,roll,throttle,yaw'&&Object.values(a).every(v=>Number.isFinite(v)&&Math.abs(v)<=1);}
const smooth=(t,start,end)=>{const u=Math.max(0,Math.min(1,(t-start)/(end-start)));return{p:u*u*(3-2*u),v:u>0&&u<1?6*u*(1-u)/(end-start):0};};
export function targetAt(id,t){const a=smooth(t,3,13),b=smooth(t,4,12);return{x:0,y:id==='straight'?12*a.p:0,z:10,yaw:id==='turn'?90*b.p:0,vx:0,vy:id==='straight'?12*a.v:0,vz:0,yawRate:id==='turn'?90*b.v:0};}
export const initialModel=()=>({x:0,y:0,z:10,vx:0,vy:0,vz:0,yaw:0,yawRate:0});
export function stepModel(model,axes,profile){
 need(validAxes(axes),'AXES_RANGE');const dt=CONTRACT.dtS,a=1-Math.exp(-dt/profile.tauS),r=model.yaw*Math.PI/180;
 const desired={vx:(axes.roll*Math.cos(r)+axes.pitch*Math.sin(r))*profile.speedMS+profile.windEastMS,vy:(axes.pitch*Math.cos(r)-axes.roll*Math.sin(r))*profile.speedMS+profile.windNorthMS,vz:axes.throttle*profile.climbMS,yawRate:axes.yaw*profile.yawRateDegS};
 const next={...model};for(const key of ['vx','vy','vz','yawRate'])next[key]=model[key]+a*(desired[key]-model[key]);
 next.x+=(model.vx+next.vx)*dt/2;next.y+=(model.vy+next.vy)*dt/2;next.z+=(model.vz+next.vz)*dt/2;next.yaw=wrap(model.yaw+(model.yawRate+next.yawRate)*dt/2);return next;
}
export function errorAt(model,target){return{horizontalM:Math.hypot(model.x-target.x,model.y-target.y),altitudeM:Math.abs(model.z-target.z),headingDeg:Math.abs(wrap(model.yaw-target.yaw))};}
export function scriptedAxes(model,target,p){const k=1.8,e=target.vx+k*(target.x-model.x)-p.windEastMS,n=target.vy+k*(target.y-model.y)-p.windNorthMS,r=model.yaw*Math.PI/180,clip=v=>Math.max(-1,Math.min(1,v));return{roll:clip((e*Math.cos(r)-n*Math.sin(r))/p.speedMS),pitch:clip((e*Math.sin(r)+n*Math.cos(r))/p.speedMS),throttle:clip((target.vz+k*(target.z-model.z))/p.climbMS),yaw:clip((target.yawRate+2*wrap(target.yaw-model.yaw))/p.yawRateDegS)};}
export const KEY_CODES=new Set(['KeyW','KeyS','KeyA','KeyD','KeyR','KeyF','KeyQ','KeyE']);
export function axesForKeys(keys){return{roll:Number(keys.has('KeyD'))-Number(keys.has('KeyA')),pitch:Number(keys.has('KeyW'))-Number(keys.has('KeyS')),throttle:Number(keys.has('KeyR'))-Number(keys.has('KeyF')),yaw:Number(keys.has('KeyE'))-Number(keys.has('KeyQ'))};}
