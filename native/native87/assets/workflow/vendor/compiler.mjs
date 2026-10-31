import {importSurvey,planPolygonSurvey,localFrame} from './survey.mjs';
export const SITL_WORLD=Object.freeze({id:'aeris-flat-world-v1',simulation:true,home:{lat:10.854,lon:106.807,amsl:10},ground:'flat-at-home',maxRadiusM:500});
const f32=x=>Math.fround(x);
const item=(command,params=[0,0,0,0],p=null,altitude=0)=>({command,frame:p?6:2,param1:f32(params[0]??0),param2:f32(params[1]??0),param3:f32(params[2]??0),param4:f32(params[3]??0),x:p?Math.round(p.lat*1e7):0,y:p?Math.round(p.lon*1e7):0,z:f32(altitude),current:0,autocontinue:1,mission_type:0});
/** Compiler intentionally requires a simulator world. Not an operational mission export. */
export function compileSurvey(pkg,world){
 if(JSON.stringify(world)!==JSON.stringify(SITL_WORLD))throw Error('Cần manifest flat-world SITL đã xác nhận.');
 const clean=importSurvey(JSON.stringify(pkg));if(clean.settings.altitudeFrame!=='flat-reference')throw Error('Chưa có DEM/datum cho frame này; không được chuyển ngầm độ cao.');
 const p=planPolygonSurvey(clean.settings);if(!p.feasible)throw Error('Kế hoạch chưa hợp lệ.');const homeFrame=localFrame({lat:world.home.lat,lon:world.home.lon});
 for(const v of clean.settings.polygon){const q=homeFrame.forward(v);if(Math.hypot(q.x,q.y)>world.maxRadiusM)throw Error('Polygon vượt khu thử SITL 500 m.');}
 const altitude=p.effectiveAltitude,frame=localFrame(p.origin),items=[item(16,[0,0,0,0],world.home,0),item(22,[0,0,0,0],world.home,altitude),item(178,[1,p.settings.speed,-1,0])];
 for(const t of p.transects){items.push(item(16,[0,0,0,0],frame.reverse(t.start),altitude),item(206,[p.nominalTriggerSpacing,0,1,0]),item(16,[0,0,0,0],frame.reverse(t.end),altitude),item(206,[0,0,0,0]));}
 items.push(item(20));if(items.length>512)throw Error('Mission vượt 512 item của adapter thử nghiệm.');
 return {version:1,simulation:true,worldId:world.id,altitudeMapping:'flat reference explicitly mapped to relative-home in the simulated flat world only',cameraProvenance:clean.settings.camera.provenance,sourcePackage:clean,items:items.map((v,seq)=>({...v,seq})),transects:p.lineCount};
}
// AP_Mission Copter-4.7.1: float metres → signed integer cm → float metres.
// Source capture reference/AP_Mission-Copter-4.7.1.cpp; do not replace with a loose cm tolerance.
export function arduAltitudeReadback(z){return Math.fround(Math.trunc(Math.fround(Math.fround(z)*100))*Math.fround(.01));}
export function readbackEqual(expected,actual){
 if(expected.length!==actual.length)return false;
 return expected.every((a,i)=>{const b=actual[i];if(!b||a.seq!==b.seq||a.command!==b.command||a.mission_type!==b.mission_type||a.autocontinue!==b.autocontinue)return false;
  // ArduPilot canonicalizes *_INT frames to equivalent global frames on download.
  const frame=x=>x===6?3:x===5?0:x===11?10:x;if(frame(a.frame)!==frame(b.frame)&&i!==0&&![178,206,2001,20].includes(a.command))return false;
  for(const k of ['param1','param2','param3','param4','z']){if(i===0&&k==='z')continue;if(!Number.isFinite(a[k])||!Number.isFinite(b[k]))return false;if(Math.abs(a[k]-b[k])>1e-3&&!(k==='z'&&[16,22].includes(a.command)&&Math.abs(arduAltitudeReadback(a[k])-b[k])<1e-5))return false;}
  // ArduPilot supplies actual home as item 0. Ignore that location, never navigation locations.
  if(i!==0&&(['x','y'].some(k=>!Number.isInteger(b[k])||Math.abs(a[k]-b[k])>1)))return false;
  return true;
 });
}
