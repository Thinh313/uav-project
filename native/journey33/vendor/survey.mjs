/** WGS84 → ECEF → local ENU. Bounded design geometry; no DEM or vehicle transport. */
const A=6378137, F=1/298.257223563, E2=F*(2-F), RAD=Math.PI/180, EPS=1e-7;
const copy=x=>structuredClone(x), finite=(v)=>typeof v==='number'&&Number.isFinite(v);
const exact=(x,keys,label)=>{if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).some(k=>!keys.includes(k)))throw Error(`${label}: dữ liệu không hỗ trợ.`);};
function coordinate(p){exact(p,['lat','lon'],'Tọa độ');if(!finite(p.lat)||!finite(p.lon)||Math.abs(p.lat)>80||Math.abs(p.lon)>180)throw Error('Tọa độ cần latitude ±80°, longitude ±180°.');return p;}
function ecef(p){const phi=p.lat*RAD,lam=p.lon*RAD,n=A/Math.sqrt(1-E2*Math.sin(phi)**2);return [n*Math.cos(phi)*Math.cos(lam),n*Math.cos(phi)*Math.sin(lam),n*(1-E2)*Math.sin(phi)];}
export function localFrame(origin){
 coordinate(origin);const base=ecef(origin),phi=origin.lat*RAD,lam=origin.lon*RAD;
 const east=[-Math.sin(lam),Math.cos(lam),0],north=[-Math.sin(phi)*Math.cos(lam),-Math.sin(phi)*Math.sin(lam),Math.cos(phi)],up=[Math.cos(phi)*Math.cos(lam),Math.cos(phi)*Math.sin(lam),Math.sin(phi)];
 return {origin:copy(origin),forward(p){coordinate(p);const xyz=ecef(p).map((v,i)=>v-base[i]);return {x:xyz.reduce((s,v,i)=>s+v*east[i],0),y:xyz.reduce((s,v,i)=>s+v*north[i],0)};},reverse(p){
  if(!finite(p.x)||!finite(p.y)||Math.hypot(p.x,p.y)>5000)throw Error('Điểm vượt phạm vi phép chiếu.');
  // Intersect the ENU vertical line with the WGS84 ellipsoid, not the tangent plane.
  const b=A*(1-F),xyz=base.map((v,i)=>v+east[i]*p.x+north[i]*p.y),q=(v,w)=>(v[0]*w[0]+v[1]*w[1])/A**2+v[2]*w[2]/b**2;
  const aa=q(up,up),bb=2*q(xyz,up),cc=q(xyz,xyz)-1,disc=bb*bb-4*aa*cc;
  if(disc<0)throw Error('Không đảo được phép chiếu.');
  const z=-2*cc/(bb+Math.sqrt(disc)),r=xyz.map((v,i)=>v+up[i]*z);
  return {lat:Math.atan2(r[2],Math.hypot(r[0],r[1])*(1-E2))/RAD,lon:Math.atan2(r[1],r[0])/RAD};
 }};
}
export function polygonArea(poly){return Math.abs(poly.reduce((s,p,i)=>{const n=poly[(i+1)%poly.length];return s+p.x*n.y-n.x*p.y;},0))/2;}
const cross=(a,b,c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
const on=(a,b,p)=>Math.abs(cross(a,b,p))<EPS&&p.x>=Math.min(a.x,b.x)-EPS&&p.x<=Math.max(a.x,b.x)+EPS&&p.y>=Math.min(a.y,b.y)-EPS&&p.y<=Math.max(a.y,b.y)+EPS;
function intersects(a,b,c,d){const x=cross(a,b,c),y=cross(a,b,d),z=cross(c,d,a),w=cross(c,d,b);return x*y<0&&z*w<0||on(a,b,c)||on(a,b,d)||on(c,d,a)||on(c,d,b);}
export function pointInPolygon(p,poly){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if(on(a,b,p))return true;if((a.y>p.y)!==(b.y>p.y)&&p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x)inside=!inside;}return inside;}
function segmentInside(a,b,poly){
 const ts=[0,1],dx=b.x-a.x,dy=b.y-a.y;
 for(let i=0;i<poly.length;i++){
  const c=poly[i],d=poly[(i+1)%poly.length],ex=d.x-c.x,ey=d.y-c.y,den=dx*ey-dy*ex;
  if(Math.abs(den)<EPS)continue;
  const t=((c.x-a.x)*ey-(c.y-a.y)*ex)/den,u=((c.x-a.x)*dy-(c.y-a.y)*dx)/den;
  if(t>0&&t<1&&u>=0&&u<=1)ts.push(t);
 }
 ts.sort((x,y)=>x-y);
 return ts.every((t,i)=>i===0||pointInPolygon({x:a.x+dx*(t+ts[i-1])/2,y:a.y+dy*(t+ts[i-1])/2},poly));
}
export const DEMO_ORIGIN=Object.freeze({lat:10.854,lon:106.807});
export const DEMO_CAMERA=Object.freeze({name:'Camera mẫu · chưa hiệu chuẩn',provenance:'demo',sensorWidth:13.2,sensorHeight:8.8,focalLength:8.8,imageWidth:5472,minInterval:1});
const demoFrame=localFrame(DEMO_ORIGIN);
export const DEFAULT_SURVEY=Object.freeze({name:'Khảo sát mẫu 01',polygon:[{x:-180,y:-110},{x:180,y:-110},{x:160,y:110},{x:-150,y:140}].map(p=>demoFrame.reverse(p)),altitude:60,altitudeFrame:'flat-reference',speed:6,heading:0,sideOverlap:80,frontOverlap:80,targetGsdCm:null,camera:DEMO_CAMERA});
export function validateSurvey(input){
 exact(input,['name','polygon','altitude','altitudeFrame','speed','heading','sideOverlap','frontOverlap','targetGsdCm','camera'],'Nhiệm vụ');
 const s=copy(input);
 if(typeof s.name!=='string'||!s.name.trim()||s.name.length>80)throw Error('Tên nhiệm vụ cần 1–80 ký tự.');s.name=s.name.trim();
 const ranges={altitude:[5,120],speed:[.5,20],heading:[0,179.9],sideOverlap:[0,95],frontOverlap:[0,95]};
 for(const[k,[lo,hi]]of Object.entries(ranges))if(!finite(s[k])||s[k]<lo||s[k]>hi)throw Error(`${k}: cần số từ ${lo} đến ${hi}.`);
 if(!['flat-reference','relative-launch','terrain','amsl'].includes(s.altitudeFrame))throw Error('Frame độ cao không hỗ trợ.');
 if(s.targetGsdCm!==null&&(!finite(s.targetGsdCm)||s.targetGsdCm<.1||s.targetGsdCm>20))throw Error('GSD mục tiêu cần 0,1–20 cm/px.');
 if(!Array.isArray(s.polygon)||s.polygon.length<3||s.polygon.length>64)throw Error('Polygon cần 3–64 đỉnh.');s.polygon.forEach(coordinate);
 // Dateline crossing and duplicate closing vertices are rejected explicitly.
 if(Math.max(...s.polygon.map(p=>p.lon))-Math.min(...s.polygon.map(p=>p.lon))>1)throw Error('Polygon vượt vùng cục bộ hoặc cắt kinh tuyến 180°.');
 const origin={lat:s.polygon.reduce((a,p)=>a+p.lat,0)/s.polygon.length,lon:s.polygon.reduce((a,p)=>a+p.lon,0)/s.polygon.length},frame=localFrame(origin),poly=s.polygon.map(p=>frame.forward(p));
 for(let i=0;i<poly.length;i++)for(let j=i+1;j<poly.length;j++){
  if(Math.hypot(poly[i].x-poly[j].x,poly[i].y-poly[j].y)>3000)throw Error('Khu vực vượt phạm vi 3 km của planner.');
  if(Math.hypot(poly[i].x-poly[j].x,poly[i].y-poly[j].y)<.01)throw Error('Polygon có đỉnh trùng nhau.');
 }
 for(let i=0;i<poly.length;i++)for(let j=i+1;j<poly.length;j++){
  if(j===i+1||i===0&&j===poly.length-1)continue;
  if(intersects(poly[i],poly[(i+1)%poly.length],poly[j],poly[(j+1)%poly.length]))throw Error('Polygon tự giao; cần sửa ranh giới.');
 }
 for(let i=0;i<poly.length;i++){
  const a=poly[(i+poly.length-1)%poly.length],b=poly[i],c=poly[(i+1)%poly.length];
  if(Math.abs(cross(a,b,c))<EPS&&(a.x-b.x)*(c.x-b.x)+(a.y-b.y)*(c.y-b.y)>0)throw Error('Cạnh polygon chồng lên nhau.');
 }
 if(polygonArea(poly)<100)throw Error('Diện tích cần ít nhất 100 m².');
 if(s.camera!==null){
  exact(s.camera,['name','provenance','sensorWidth','sensorHeight','focalLength','imageWidth','minInterval'],'Camera');
  if(typeof s.camera.name!=='string'||!s.camera.name.trim()||s.camera.name.length>80||!['demo','operator-input'].includes(s.camera.provenance))throw Error('Camera cần tên và provenance đúng.');
  for(const[k,[lo,hi]]of Object.entries({sensorWidth:[1,100],sensorHeight:[1,100],focalLength:[1,200],imageWidth:[100,20000],minInterval:[.05,60]}))if(!finite(s.camera[k])||s.camera[k]<lo||s.camera[k]>hi)throw Error(`Camera ${k}: cần ${lo}–${hi}.`);
  if(!Number.isInteger(s.camera.imageWidth))throw Error('Ảnh ngang cần số nguyên.');
 }
 return {settings:s,frame,poly};
}
export function planPolygonSurvey(input){
 const {settings:s,frame,poly}=validateSurvey(input),camera=s.camera;
 const flat=s.altitudeFrame==='flat-reference';
 let height=s.altitude;
 if(s.targetGsdCm!==null&&camera&&flat){height=s.targetGsdCm/100*camera.imageWidth*camera.focalLength/camera.sensorWidth;if(height<5||height>120)throw Error('GSD mục tiêu yêu cầu độ cao ngoài 5–120 m.');}
 // No footprint/AGL may be fabricated when altitude datum/terrain is unknown.
 if(flat&&camera&&s.targetGsdCm!==null)s.altitude=height;
 const footprintWidth=camera&&flat?height*camera.sensorWidth/camera.focalLength:null;
 const footprintHeight=camera&&flat?height*camera.sensorHeight/camera.focalLength:null;
 const spacing=footprintWidth?footprintWidth*(1-s.sideOverlap/100):null,trigger=footprintHeight?footprintHeight*(1-s.frontOverlap/100):null;
 const rad=s.heading*RAD,cs=Math.cos(rad),sn=Math.sin(rad),rot=p=>({x:p.x*cs-p.y*sn,y:p.x*sn+p.y*cs}),unrot=p=>({x:p.x*cs+p.y*sn,y:-p.x*sn+p.y*cs});
 const p=poly.map(rot),min=Math.min(...p.map(q=>q.x)),max=Math.max(...p.map(q=>q.x)),width=max-min;
 const transects=[];let photoCount=null,distance=0,lineSpacing=null;
 if(spacing){
  // Centre strips no farther apart than nominal spacing, covering the cross-track bounds.
  const usable=Math.max(0,width-footprintWidth),count=usable===0?1:Math.ceil(usable/spacing-1e-9)+1;
  if(count>2000)throw Error('Nhiệm vụ vượt 2.000 tuyến.');lineSpacing=count>1?usable/(count-1):0;photoCount=0;
  for(let i=0;i<count;i++){
   const x=count===1?(min+max)/2:min+footprintWidth/2+i*lineSpacing,hits=[];
   for(let j=0;j<p.length;j++){
    const a=p[j],b=p[(j+1)%p.length];
    if((a.x<=x&&b.x>x)||(b.x<=x&&a.x>x))hits.push(a.y+(x-a.x)*(b.y-a.y)/(b.x-a.x));
   }
   hits.sort((a,b)=>a-b);if(hits.length%2)throw Error('Giao tuyến polygon không hợp lệ.');
   const segments=[];for(let j=0;j<hits.length;j+=2)if(hits[j+1]-hits[j]>EPS)segments.push([hits[j],hits[j+1]]);
   if(i%2)segments.reverse();
   for(const[a,b]of segments){
    const start=unrot({x,y:i%2?b:a}),end=unrot({x,y:i%2?a:b}),length=b-a;
    const shots=Math.ceil(length/trigger-1e-9)+1;
    transects.push({index:transects.length+1,strip:i+1,start,end,length,shots,startGeo:frame.reverse(start),endGeo:frame.reverse(end)});photoCount+=shots;
    if(photoCount>20000||transects.length>2000)throw Error('Nhiệm vụ vượt 20.000 ảnh hoặc 2.000 đoạn tuyến.');
   }
  }
  if(!transects.length)throw Error('Không tạo được tuyến trong polygon.');
 }
 const waypoints=transects.flatMap(t=>[t.start,t.end]);
 for(let i=1;i<waypoints.length;i++)distance+=Math.hypot(waypoints[i].x-waypoints[i-1].x,waypoints[i].y-waypoints[i-1].y);
 const gaps=transects.slice(1).map((t,i)=>({start:transects[i].end,end:t.start}));
 // Straight connectors are NOT claimed to stay inside concave boundaries.
 const hasOutsideConnector=gaps.some(t=>!segmentInside(t.start,t.end,poly));
 const warnings=[];if(!camera)warnings.push('Chưa có footprint camera; số ảnh và tuyến chưa xác định.');
 if(!flat)warnings.push(s.altitudeFrame==='terrain'?'Thiếu DEM; chưa tính cao độ theo địa hình.':'Chưa biết mặt đất/điểm cất cánh để suy ra AGL; chưa tính footprint.');
 const shortest=transects.length?Math.min(...transects.map(t=>t.length/(t.shots-1))):null;
 const interval=shortest!==null?shortest/s.speed:null;
 if(interval!==null&&interval+1e-9<camera.minInterval)warnings.push('Camera không theo kịp chu kỳ chụp; giảm tốc hoặc chồng ảnh.');
 if(hasOutsideConnector)warnings.push('Có đoạn nối ra ngoài polygon; cần lập tuyến chuyển tiếp trước khi bay.');
 return {settings:s,origin:frame.origin,polygonLocal:poly,bounds:{minX:Math.min(...poly.map(q=>q.x)),maxX:Math.max(...poly.map(q=>q.x)),minY:Math.min(...poly.map(q=>q.y)),maxY:Math.max(...poly.map(q=>q.y))},area:polygonArea(poly),effectiveAltitude:height,footprintWidth,footprintHeight,lineSpacing,nominalTriggerSpacing:trigger,triggerInterval:interval,lineCount:transects.length,photoCount,transects,waypoints,distance:transects.length?distance:null,nominalSeconds:transects.length?distance/s.speed:null,gsdCm:footprintWidth?footprintWidth/camera.imageWidth*100:null,feasible:warnings.length===0,warnings,hasOutsideConnector,operational:false,model:'wgs84-enu-polygon-flat-v2'};
}
export function surveyPackage(settings){const p=planPolygonSurvey(settings);return {format:'aeris-survey',version:2,operational:false,model:'wgs84-enu-polygon-flat-v2',coordinateSystem:'WGS84',settings:copy(p.settings)};}
export function importSurvey(text){
 if(typeof text!=='string'||text.length>256*1024)throw Error('Gói nhiệm vụ phải nhỏ hơn 256 KB.');let d;try{d=JSON.parse(text);}catch{throw Error('Không đọc được JSON nhiệm vụ.');}
 exact(d,['format','version','operational','model','coordinateSystem','settings'],'Gói nhiệm vụ');
 if(d.format!=='aeris-survey'||d.version!==2||d.operational!==false||d.model!=='wgs84-enu-polygon-flat-v2'||d.coordinateSystem!=='WGS84')throw Error('Cần gói khảo sát AERIS v2. QGC .plan và v1 cục bộ chưa chuyển tọa độ tự động.');
 const p=surveyPackage(d.settings);planPolygonSurvey(p.settings);return p;
}
