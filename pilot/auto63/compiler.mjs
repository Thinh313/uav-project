import {planMission,CAMERA,OPTIONS} from '../aeris57/domain.mjs';
import {SITL_WORLD,readbackEqual,arduAltitudeReadback} from '../../app/core/compiler.mjs';
import {makeQgcRequest,compileQgc} from '../../app/core/qgc.mjs';
import {localFrame} from '../../app/core/survey.mjs';
import {sha,stable} from '../mapping51/common.mjs';
export {sha,stable,CAMERA};
export const DEFAULTS={...OPTIONS,altitudeAglM:10,speedMS:2,corridorWidthM:8,datumAcknowledged:false};
export const HOME=SITL_WORLD.home,frame=localFrame({lat:HOME.lat,lon:HOME.lon});
const coords=pts=>pts.map(([x,y])=>{const p=frame.reverse({x,y});return `${p.lon},${p.lat},0`}).join(' ');
const kml=body=>`<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>${body}</Document></kml>`;
export const SAMPLES={polygon:kml(`<Placemark><name>Khảo sát sân thử</name><Polygon><outerBoundaryIs><LinearRing><coordinates>${coords([[8,5],[22,5],[22,15],[8,15],[8,5]])}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>`),corridor:kml(`<Placemark><name>Tuyến thử</name><LineString><coordinates>${coords([[8,6],[20,6],[24,12]])}</coordinates></LineString></Placemark>`)};
export async function compile(d){
 if(!d||d.homeConfirmed!==true)throw Error('Xác nhận Home và mô hình mặt đất phẳng của SITL.');
 const acquisition=await planMission(d),p=acquisition.plan;
 if(p.options.altitudeAglM>30||p.legs.length>12||p.metrics.nominalSeconds>120)throw Error('SITL giới hạn cao10–30m,12 transect,120s danh nghĩa.');
 if(p.warnings.includes('CONCAVE_CONNECTOR_OUTSIDE_AOI'))throw Error('Đường nối ra ngoài vùng chưa được kiểm; chỉ review.');
 const inRange=q=>{const a=frame.forward(q);if(Math.hypot(a.x,a.y)>100)throw Error('Tuyến vượt bán kính SITL100m; không tự dời tọa độ.');};
 p.legs.forEach(l=>{inRange(l.start);inRange(l.end)});
 const item=(command,params,pos=null,z=0)=>({type:'SimpleItem',frame:pos?3:2,command,autoContinue:true,params:[...params,pos?.lat??0,pos?.lon??0,z],...(pos?{AltitudeMode:1,Altitude:z,AMSLAltAboveTerrain:null}:{})});
 const h=p.options.altitudeAglM,spacing=p.metrics.footprintAlongM*(1-p.options.frontOverlapPct/100);
 const items=[item(22,[0,0,0,0],HOME,h),item(178,[1,p.options.speedMS,-1,0])];
 for(const l of p.legs)items.push(item(16,[0,0,0,0],l.start,h),item(206,[spacing,0,1,0]),item(16,[0,0,0,0],l.end,h),item(206,[0,0,0,0]));
 items.push(item(20,[0,0,0,0]));items.forEach((v,i)=>v.doJumpId=i+1);
 if(items.length+1>64)throw Error('Mission vượt64 item.');
 const qgc={fileType:'Plan',version:1,groundStation:'AERIS AUTO63',geoFence:{version:2,circles:[],polygons:[]},rallyPoints:{version:2,points:[]},mission:{version:2,firmwareType:3,vehicleType:2,cruiseSpeed:p.options.speedMS,hoverSpeed:2,globalPlanAltitudeMode:1,plannedHomePosition:[HOME.lat,HOME.lon,HOME.amsl],items}};
 const request=makeQgcRequest(JSON.stringify(qgc)),compiled=compileQgc(request);
 const body={format:'aeris-auto63-plan',version:1,simulation:true,acquisition,request,compiled,home:HOME,worldId:SITL_WORLD.id,altitudeDatum:'RELATIVE_HOME_ON_EXPLICIT_SYNTHETIC_FLAT',cameraEvidence:'COMMANDS_ONLY_SYNTHETIC_CAMERA_NO_IMAGES',sourceSha256:p.sourceSha256,missionSha256:sha(compiled.items),scope:'OWNED_SITL_ONLY_NOT_OPERATIONAL_HERA'};
 return{...body,sha256:sha(body)};
}
export function verifyPlan(p){const{sha256,...body}=p;if(sha(body)!==sha256||sha(p.compiled.items)!==p.missionSha256)throw Error('PLAN_SHA_MISMATCH');return p;}
export function compareMission(expected,actual,home){
 if(!home||Math.abs(home.lat-HOME.lat)>1e-6||Math.abs(home.lon-HOME.lon)>1e-6||Math.abs(home.amsl-HOME.amsl)>.5)throw Error('HOME_OBSERVATION_MISMATCH');
 if(!readbackEqual(expected,actual))throw Error('MISSION_READBACK_MISMATCH');
 const z0=actual[0];if(Math.abs(z0.x-Math.round(home.lat*1e7))>1||Math.abs(z0.y-Math.round(home.lon*1e7))>1||Math.abs(z0.z-home.amsl)>.02)throw Error('READBACK_HOME_MISMATCH');
 for(let i=1;i<expected.length;i++){
  const a=expected[i],b=actual[i];if([206,178].includes(a.command)&&['param1','param2','param3','param4'].some(k=>Math.fround(a[k])!==Math.fround(b[k])))throw Error('CAMERA_SPEED_READBACK_MISMATCH');
 }
 return{matches:true,items:expected.length,cameraCommands:expected.filter(i=>i.command===206).length,normalizations:['AP_INT_FRAME_TO_GLOBAL_EQUIVALENT','AP_NAV_ALT_FLOAT_CM_RULE','HOME_FROM_FRESH_OBSERVATION'],notExecution:true,actualImages:0};
}
