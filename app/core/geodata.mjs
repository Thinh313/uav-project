import {assertGeoPolicy} from './geo-policy.mjs';
import {GEO_PINS} from './geo-pins.mjs';
import {planPolygonSurvey,localFrame} from './survey.mjs';
import {compileSurvey,SITL_WORLD} from './compiler.mjs';
export {GEO_PINS};
const stable=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?`[${x.map(stable).join(',')}]`:`{${Object.keys(x).sort().map(k=>`${JSON.stringify(k)}:${stable(x[k])}`).join(',')}}`;
export async function sha256(text){const b=typeof text==='string'?new TextEncoder().encode(text):text;const d=await crypto.subtle.digest('SHA-256',b);return [...new Uint8Array(d)].map(x=>x.toString(16).padStart(2,'0')).join('');}
export function requestIdentity(request){return stable(request);}
export async function verifyGeoBundle(bundle){
 if(!bundle||bundle.format!=='aeris-offline-geodata'||bundle.version!==1||typeof bundle.manifest!=='string'||!bundle.assets||Object.keys(bundle).some(k=>!['format','version','manifest','assets'].includes(k)))throw Error('Gói dữ liệu ngoại tuyến không hỗ trợ.');
 if(bundle.manifest.length>24000||await sha256(bundle.manifest)!==GEO_PINS.manifestSha256)throw Error('Manifest khác bản nguồn đã khóa.');
 const m=JSON.parse(bundle.manifest);if(m.id!==GEO_PINS.id||m.operational!==false)throw Error('Metadata không hợp lệ.');
 if(Object.keys(bundle.assets).length!==2)throw Error('Thiếu/thừa asset địa lý.');
 for(const[name,pin]of Object.entries(GEO_PINS.assets)){const text=bundle.assets[name];if(typeof text!=='string'||new TextEncoder().encode(text).length!==pin.bytes||await sha256(text)!==pin.sha256)throw Error(`Asset ${name} thiếu hoặc sai hash.`);}
 const dsm=JSON.parse(bundle.assets['dsm.json']),basemap=JSON.parse(bundle.assets['basemap.json']);validateGrid(dsm);if(basemap.type!=='FeatureCollection'||basemap.features.length>2000)throw Error('Basemap ngoài phạm vi.');
 return {manifest:m,grid:dsm,basemap,verified:true,bundle:structuredClone(bundle)};
}
export function validateGrid(g){if(!g||g.version!==1||g.model!=='DSM'||g.verticalDatum!=='EGM2008'||g.unit!=='m'||g.coordinateSystem!=='WGS84'||g.pixelInterpretation!=='point')throw Error('Grid thiếu datum/unit/model.');if(!Number.isInteger(g.rows)||!Number.isInteger(g.cols)||g.rows<2||g.cols<2||g.rows*g.cols>20000||g.values.length!==g.rows*g.cols||![g.west,g.north,g.stepLon,g.stepLat].every(Number.isFinite)||g.stepLon<=0||g.stepLat<=0)throw Error('Grid không hợp lệ.');}
export function sampleSurface(grid,p){
 validateGrid(grid);if(!p||!Number.isFinite(p.lat)||!Number.isFinite(p.lon))return null;
 let x=(p.lon-grid.west)/grid.stepLon,y=(grid.north-p.lat)/grid.stepLat;
 if(x< -1e-8||y< -1e-8||x>grid.cols-1+1e-8||y>grid.rows-1+1e-8)return null;x=Math.max(0,Math.min(grid.cols-1,x));y=Math.max(0,Math.min(grid.rows-1,y));
 const ix=Math.min(grid.cols-2,Math.floor(x)),iy=Math.min(grid.rows-2,Math.floor(y)),tx=x-ix,ty=y-iy;const values=[grid.values[iy*grid.cols+ix],grid.values[iy*grid.cols+ix+1],grid.values[(iy+1)*grid.cols+ix],grid.values[(iy+1)*grid.cols+ix+1]];
 if(values.some(v=>!Number.isFinite(v)||v< -500||v>9000))return null;
 return values[0]*(1-tx)*(1-ty)+values[1]*tx*(1-ty)+values[2]*(1-tx)*ty+values[3]*tx*ty;
}
function assertRequest(request,geo){
 if(!request||request.format!=='aeris-survey-run'||![1,2].includes(request.version)||request.simulation!==true||request.geoId!==GEO_PINS.id||request.geoHash!==GEO_PINS.manifestSha256||Object.keys(request).some(k=>!['format','version','simulation','geoId','geoHash','verticalPolicy','package',...(request.version===2?['reviewPolicy']:[])].includes(k)))throw Error('Yêu cầu nhiệm vụ thiếu nguồn/hash/schema.');
 if(request.version===2)assertGeoPolicy(request.reviewPolicy);
 if(!geo?.verified||geo.manifest.id!==request.geoId)throw Error('Cần gói địa lý đã kiểm hash.');if(!['sim-flat','sim-dsm-offset'].includes(request.verticalPolicy))throw Error('Chưa có geoid/launch reference cho nhiệm vụ bay thực.');
}
export function makeGeoRequest(pkg,verticalPolicy='sim-flat'){return {format:'aeris-survey-run',version:1,simulation:true,geoId:GEO_PINS.id,geoHash:GEO_PINS.manifestSha256,verticalPolicy,package:structuredClone(pkg)};}
export function compileGeoSurvey(request,geo){
 assertRequest(request,geo);const base=compileSurvey(request.package,SITL_WORLD),plan=planPolygonSurvey(request.package.settings),frame=localFrame(plan.origin),home={lat:SITL_WORLD.home.lat,lon:SITL_WORLD.home.lon},homeSurface=sampleSurface(geo.grid,home);
 if(homeSurface===null)throw Error('Thiếu DSM tại Home.');const route=[home,...plan.waypoints.map(p=>frame.reverse(p)),home];let distance=0;const samples=[];
 for(let i=1;i<route.length;i++){const a=frame.forward(route[i-1]),b=frame.forward(route[i]),length=Math.hypot(a.x-b.x,a.y-b.y),steps=Math.max(1,Math.ceil(length/10));
  if(samples.length+steps+1>12000)throw Error('Profile vượt 12.000 mẫu.');
  for(let j=0;j<=steps;j++){if(i>1&&j===0)continue;const t=j/steps,p=frame.reverse({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t}),height=sampleSurface(geo.grid,p);
   if(height===null)throw Error('DSM thiếu/vượt vùng phủ dọc đường bay.');samples.push({distance:distance+length*t,lat:p.lat,lon:p.lon,surfaceEgm2008:height,targetRelativeHome:request.verticalPolicy==='sim-dsm-offset'?plan.effectiveAltitude+height-homeSurface:plan.effectiveAltitude});}
  distance+=length;
 }
 for(const p of plan.settings.polygon)if(sampleSurface(geo.grid,p)===null)throw Error('Polygon vượt vùng phủ DSM.');
 const items=structuredClone(base.items);
 if(request.verticalPolicy==='sim-dsm-offset')for(const i of items){if(i.seq>0&&[16,22].includes(i.command)){const h=sampleSurface(geo.grid,{lat:i.x/1e7,lon:i.y/1e7});if(h===null)throw Error('Thiếu DSM tại waypoint.');i.z=Math.fround(plan.effectiveAltitude+h-homeSurface);if(i.z<5||i.z>120)throw Error('Độ cao SITL sau mapping cần 5–120 m.');}}
 // Evaluate linear waypoint interpolation, not an imaginary continuously terrain-following path.
 let minClearance=Infinity;
 for(let i=1;i<route.length;i++){const a=frame.forward(route[i-1]),b=frame.forward(route[i]),length=Math.hypot(b.x-a.x,b.y-a.y),steps=Math.max(1,Math.ceil(length/10)),ha=sampleSurface(geo.grid,route[i-1]),hb=sampleSurface(geo.grid,route[i]);
  for(let j=0;j<=steps;j++){const t=j/steps,p=frame.reverse({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t}),h=sampleSurface(geo.grid,p);const commandAltitude=plan.effectiveAltitude+(request.verticalPolicy==='sim-dsm-offset'?(ha-homeSurface)*(1-t)+(hb-homeSurface)*t:0);minClearance=Math.min(minClearance,commandAltitude-(h-homeSurface));}
 }
 if(minClearance<5)throw Error('Envelope nội suy thấp hơn 5 m trên DSM; cần tăng cao hoặc đổi tuyến.');
 return {...base,sourceRequest:structuredClone(request),geoId:request.geoId,geoHash:request.geoHash,verticalPolicy:request.verticalPolicy,altitudeMapping:request.verticalPolicy==='sim-dsm-offset'?'DSM EGM2008 differences mapped to virtual SITL home; simulator ground remains flat':'Explicit flat-world SITL altitude; real DSM is planning context',items,profile:{datum:'EGM2008',model:'DSM',homeSurface,nominalResolutionM:30,samples,minLinearClearanceM:minClearance,groundPhysics:'flat-sitl',operational:false},sourcePackage:request.package};
}
export async function loadGeoBundle(){const names=['manifest.json','basemap.json','dsm.json'];const [manifest,basemap,dsm]=await Promise.all(names.map(async name=>{const r=await fetch(`/data/${name}`);if(!r.ok)throw Error(`Không đọc được ${name}; cài gói offline.`);return r.text();}));return verifyGeoBundle({format:'aeris-offline-geodata',version:1,manifest,assets:{'basemap.json':basemap,'dsm.json':dsm}});}
