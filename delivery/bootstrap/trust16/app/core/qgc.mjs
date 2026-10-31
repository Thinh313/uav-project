import {SITL_WORLD} from './compiler.mjs';
import {localFrame} from './survey.mjs';
export const QGC_PIN=Object.freeze({release:'v5.1.5',commit:'3a67d31f0c36bf3fe38ec52970d250a89d0aaf67'});
const fail=m=>{throw Error(m)}, obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x), finite=x=>typeof x==='number'&&Number.isFinite(x), int=x=>Number.isInteger(x), copy=x=>structuredClone(x);
const bounded=(x,min,max)=>finite(x)&&x>=min&&x<=max;
function coord(p,n=3){if(!Array.isArray(p)||p.length!==n||!bounded(p[0],-90,90)||!bounded(p[1],-180,180)||(n===3&&!finite(p[2])))fail('Tọa độ WGS84/cao độ không hợp lệ.');}
function parameters(i){const p=i.params;if(!Array.isArray(p))fail('Thiếu params.');if(p.length===4&&Array.isArray(i.coordinate)){coord(i.coordinate);return [...p,...i.coordinate];}if(p.length!==7||i.coordinate!==undefined)fail('Params cần 7 giá trị hoặc dạng legacy coordinate + 4 params.');return p;}
function simple(i){if(!obj(i)||i.type!=='SimpleItem'||!int(i.command)||i.command<0||i.command>65535||!int(i.frame)||i.frame<0||i.frame>255||typeof i.autoContinue!=='boolean')fail('SimpleItem không hợp lệ.');const p=parameters(i);if(!p.every(v=>v===null||finite(v)))fail('Params chỉ nhận số hữu hạn hoặc null.');if(i.doJumpId!==undefined&&(!int(i.doJumpId)||i.doJumpId<1))fail('doJumpId không hợp lệ.');return {source:i,params:p};}
function cached(i){const t=i.TransectStyleComplexItem;if(!obj(t)||![1,2].includes(t.version)||!Array.isArray(t.Items)||t.Items.length<1)fail('Survey cần TransectStyle v1/v2 và Items đã lưu.');return t;}
/** Retains exact UTF-8 text for original-file export; validity is not flight readiness. */
export function importQgc(raw){
 if(typeof raw!=='string'||new TextEncoder().encode(raw).length>65536)fail('Plan cần ≤64 KiB.');let plan;try{plan=JSON.parse(raw.startsWith("\uFEFF")?raw.slice(1):raw);}catch{fail('Plan không phải JSON hợp lệ.');}
 if(!obj(plan)||plan.fileType!=='Plan'||plan.version!==1||!obj(plan.mission)||plan.mission.version!==2)fail('Chỉ nhận Plan v1 / mission v2.');
 const m=plan.mission;coord(m.plannedHomePosition);if(!int(m.firmwareType)||!int(m.vehicleType)||!bounded(m.cruiseSpeed,0,100)||!bounded(m.hoverSpeed,0,100)||!Array.isArray(m.items)||m.items.length<1||m.items.length>511)fail('Mission header/items không hợp lệ.');
 const commands=[],complex=[];let count=0;
 for(const i of m.items){if(i?.type==='SimpleItem')commands.push(simple(i));else if(i?.type==='ComplexItem'&&i.complexItemType==='survey'&&[4,5].includes(i.version)){if(!Array.isArray(i.polygon)||i.polygon.length<3||i.polygon.length>128)fail('Polygon survey không hợp lệ.');i.polygon.forEach(p=>coord(p,2));const t=cached(i);complex.push(i);commands.push(...t.Items.map(simple));}else fail('Loại ComplexItem/version chưa hỗ trợ; không chuyển đổi ngầm.');count=commands.length;if(count>511)fail('Mission snapshot vượt 511 lệnh.');}
 for(const key of ['geoFence','rallyPoints']){const g=plan[key];if(g!==undefined&&(!obj(g)||![1,2].includes(g.version)))fail(key+' version không hợp lệ.');}
 if(plan.geoFence){const f=plan.geoFence;if(f.version===1){if(!Array.isArray(f.polygon))fail('GeoFence legacy thiếu polygon.');}else if(!Array.isArray(f.circles)||!Array.isArray(f.polygons))fail('GeoFence thiếu circles/polygons.');}
 if(plan.rallyPoints&&!Array.isArray(plan.rallyPoints.points))fail('Rally thiếu points.');
 return {raw,plan,commands,complex,summary:{items:commands.length,visualItems:m.items.length,complex:complex.length,home:copy(m.plannedHomePosition),firmwareType:m.firmwareType,vehicleType:m.vehicleType,cameraCommands:commands.filter(c=>c.source.command===206).length}};
}
const extra=(o,keys)=>Object.keys(o).filter(k=>!keys.includes(k));
const zeros=a=>a.every(x=>x===0);
export function makeQgcRequest(raw){importQgc(raw);return {format:'aeris-qgc-run',version:1,simulation:true,worldId:SITL_WORLD.id,profile:'copter-4.7.1-stored-snapshot-v1',rawPlan:raw};}
export function compileQgc(request,world=SITL_WORLD){
 if(!obj(request)||extra(request,['format','version','simulation','worldId','profile','rawPlan']).length||request.format!=='aeris-qgc-run'||request.version!==1||request.simulation!==true||request.worldId!==SITL_WORLD.id||request.profile!=='copter-4.7.1-stored-snapshot-v1'||JSON.stringify(world)!==JSON.stringify(SITL_WORLD))fail('Cần envelope/profile SITL rõ ràng.');
 if(new TextEncoder().encode(JSON.stringify(request)).length>65000)fail('Envelope vượt giới hạn API 64 KiB sau escaping.');
 const intake=importQgc(request.rawPlan),p=intake.plan,m=p.mission,normalizations=[];
 if(extra(p,['fileType','version','groundStation','mission','geoFence','rallyPoints']).length||extra(m,['version','firmwareType','vehicleType','cruiseSpeed','hoverSpeed','items','plannedHomePosition','globalPlanAltitudeMode']).length)fail('Extension Plan/mission chưa có ngữ nghĩa; chỉ review.');
 if(m.firmwareType!==3||m.vehicleType!==2)fail('SITL chỉ nhận ArduPilot / quadrotor.');
 if(m.globalPlanAltitudeMode!==undefined&&![0,1].includes(m.globalPlanAltitudeMode))fail('Global altitude mode chưa hỗ trợ.');
 const h=m.plannedHomePosition;if(Math.abs(h[0]-world.home.lat)>1e-7||Math.abs(h[1]-world.home.lon)>1e-7||Math.abs(h[2]-world.home.amsl)>.001)fail('Home khác world SITL; không tự dời nhiệm vụ.');
 if(p.geoFence&&extra(p.geoFence,p.geoFence.version===1?['version','polygon','breachReturn']:['version','circles','polygons']).length)fail('Geofence extension chưa hỗ trợ.');
 if(p.geoFence&&(p.geoFence.polygon?.length||p.geoFence.polygons?.length||p.geoFence.circles?.length||p.geoFence.breachReturn?.length))fail('Geofence không rỗng: adapter mission-only chưa hỗ trợ.');
 if(p.rallyPoints&&(extra(p.rallyPoints,['version','points']).length||p.rallyPoints.points.length))fail('Rally point chưa hỗ trợ; không bỏ qua.');
 const frame=localFrame({lat:world.home.lat,lon:world.home.lon}),radius=(lat,lon)=>{const q=frame.forward({lat,lon});if(Math.hypot(q.x,q.y)>world.maxRadiusM)fail('Tuyến/polygon vượt vùng SITL 500 m.');};
 for(const c of intake.complex){const t=cached(c),calc=t.CameraCalc;if(!obj(calc)||t.FollowTerrain===true||(calc.DistanceMode!==undefined?calc.DistanceMode!==1:calc.DistanceToSurfaceRelative!==true))fail('Survey chưa xác định relative-home; không suy từ DEM.');if(t.HoverAndCapture!==false||t.Refly90Degrees!==false)fail('Survey capture/refly pattern chưa hỗ trợ.');c.polygon.forEach(v=>radius(...v));}
 const home={seq:0,command:16,frame:6,param1:0,param2:0,param3:0,param4:0,x:Math.round(h[0]*1e7),y:Math.round(h[1]*1e7),z:0,current:0,autocontinue:1,mission_type:0};
 const ids=new Set();const items=[home,...intake.commands.map(({source:i,params:p},n)=>{
  const seq=n+1,c=i.command,a=copy(p),nav=[16,22].includes(c);
  if(extra(i,['type','frame','command','autoContinue','doJumpId','params','coordinate','Altitude','AltitudeMode','AMSLAltAboveTerrain']).length)fail('Item extension chưa hỗ trợ.');
  if(i.doJumpId!==undefined){if(ids.has(i.doJumpId))fail('doJumpId trùng.');ids.add(i.doJumpId);}
  if(!i.autoContinue)fail('autoContinue=false chưa hỗ trợ trên Copter profile.');
  if(nav){if(![3,6].includes(i.frame))fail('Chỉ hỗ trợ độ cao relative-home; AMSL/terrain bị chặn.');coord(a.slice(4));if(!bounded(a[6],5,120))fail('Cao độ cần 5–120 m.');radius(a[4],a[5]);
   if(i.AltitudeMode!==undefined&&(i.AltitudeMode!==1||!finite(i.Altitude)||Math.abs(i.Altitude-a[6])>1e-6||i.AMSLAltAboveTerrain!==null))fail('Metadata cao độ khác params/frame.');
   if(i.AltitudeMode===undefined&&(i.Altitude!==undefined||i.AMSLAltAboveTerrain!==undefined))fail('Metadata cao độ thiếu mode.');
   if(a[3]===null){normalizations.push({seq,field:'param4',from:null,to:0,reason:'Copter-4.7.1 AP_Mission ignores NAV yaw; original null retained'});a[3]=0;}
   if(!int(a[0])||!bounded(a[0],0,60)||!zeros(a.slice(1,4)))fail('NAV tham số ngoài profile đã kiểm.');
   if(c===22&&(n!==0||Math.abs(a[4]-h[0])>1e-7||Math.abs(a[5]-h[1])>1e-7||a[0]!==0))fail('Takeoff cần đứng đầu và tại Home.');
  }else{if(c===2001){if(a[0]!==0||!a.slice(1).every(v=>v===0||v===null))fail('Stop capture chỉ nhận camera 0 và reserved 0/null.');for(let k=1;k<7;k++)if(a[k]===null){normalizations.push({seq,field:'param'+(k+1),from:null,to:0,reason:'Copter-4.7.1 IMAGE_STOP_CAPTURE stores only camera ID; reserved null retained in original'});a[k]=0;}}
   if(i.frame!==2||!a.every(finite))fail('DO/RTL cần frame MISSION và số hữu hạn.');
   if(c===178){if(a[0]!==1||!bounded(a[1],.5,20)||a[2]!==-1||!zeros(a.slice(3)))fail('Speed command ngoài profile.');}
   else if(c===206){if(!bounded(a[0],0,1000)||a[1]!==0||![0,1].includes(a[2])||!zeros(a.slice(3)))fail('Camera distance ngoài profile.');}
   else if(c===2001){const previous=intake.commands[n-1];if(!zeros(a)||previous?.source.command!==206||!zeros(previous.params))fail('Stop capture cần ngay sau 206 tắt trigger, không chụp ngay.');}
   else if(c===20){if(n!==intake.commands.length-1||!zeros(a))fail('RTL cần ở cuối với params=0.');}
   else fail('Command '+c+' chưa hỗ trợ; không loại bỏ.');
  }
  return {seq,command:c,frame:nav?6:2,param1:Math.fround(a[0]),param2:Math.fround(a[1]),param3:Math.fround(a[2]),param4:Math.fround(a[3]),x:nav?Math.round(a[4]*1e7):0,y:nav?Math.round(a[5]*1e7):0,z:Math.fround(a[6]),current:0,autocontinue:1,mission_type:0};
 })];
 if(items[1]?.command!==22||items.at(-1)?.command!==20||!items.some(i=>i.seq>0&&i.command===16))fail('Cần takeoff → waypoint → RTL trong profile.');
 const lastTrigger=items.filter(i=>i.command===206).at(-1);if(lastTrigger&&lastTrigger.param1!==0)fail('Cần tắt trigger camera trước RTL.');
 return {version:1,simulation:true,worldId:world.id,sourceRequest:copy(request),items,normalizations,sourceKind:intake.complex.length?'QGC stored complex snapshot':'QGC SimpleItems',altitudeMapping:'Explicit relative-home / simulated flat world only',cameraProvenance:'QGC command snapshot; physical capture NOT_CHECKED',qgcPin:QGC_PIN};
}
export function reviewQgc(raw){const intake=importQgc(raw);let compiled=null,error=null;try{compiled=compileQgc(makeQgcRequest(raw));}catch(e){error=e.message;}return {...intake,compiled,error};}
export function exportQgc(compiled,{cameraSection=false}={}){
 if(!compiled?.simulation||compiled.worldId!==SITL_WORLD.id||!Array.isArray(compiled.items)||compiled.items.length<2)fail('Chỉ xuất mission đã compile cho SITL.');
 const insertions=[],items=[];const source=compiled.items.slice(1);for(let n=0;n<source.length;n++){const i=source[n];if(cameraSection&&i.command===206&&(i.param1===0?i.param3!==0:i.param3!==1))fail('Camera-section cần start chụp ngay và stop không chụp ngay; không sửa ý định ngầm.');items.push(i);if(cameraSection&&i.command===206&&i.param1===0&&source[n+1]?.command!==2001){items.push({command:2001,frame:2,param1:0,param2:0,param3:0,param4:0,x:0,y:0,z:0,autocontinue:1});insertions.push({afterSourceSeq:i.seq,command:2001,reason:'Explicit QGC stop-photo section: stop distance trigger and image sequence'});}}
 const plan={fileType:'Plan',version:1,groundStation:'AERIS',geoFence:{version:2,circles:[],polygons:[]},rallyPoints:{version:2,points:[]},mission:{version:2,firmwareType:3,vehicleType:2,cruiseSpeed:15,hoverSpeed:5,globalPlanAltitudeMode:1,plannedHomePosition:[SITL_WORLD.home.lat,SITL_WORLD.home.lon,SITL_WORLD.home.amsl],items:items.map((i,n)=>({type:'SimpleItem',frame:[16,22].includes(i.command)?3:2,command:i.command,autoContinue:!!i.autocontinue,doJumpId:n+1,params:cameraSection&&i.command===2001?[0,null,null,null,null,null,null]:[i.param1,i.param2,i.param3,i.param4,i.x/1e7,i.y/1e7,i.z],...([16,22].includes(i.command)?{AltitudeMode:1,Altitude:i.z,AMSLAltAboveTerrain:null}:{})}))}};
 const raw=JSON.stringify(plan,null,2)+'\n';compileQgc(makeQgcRequest(raw));return {raw,receipt:{format:'aeris-qgc-lineage',version:2,simulation:true,world:SITL_WORLD,qgcPin:QGC_PIN,sourceRequest:compiled.sourceRequest??compiled.sourcePackage??null,altitudeMapping:compiled.altitudeMapping,cameraSection,insertions,scope:'SITL ONLY; disclosed camera-stop command additions; standard Plan cannot enforce simulation-only use in external GCS; no QGC polygon-regeneration claim'}};
}
export async function qgcSha256(raw){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),x=>x.toString(16).padStart(2,'0')).join('');}
/** Builds a disclosed derivative, never edits the source or sends a vehicle command. */
export async function prepareQgcForSitl(raw,options){
 if(!obj(options)||extra(options,['confirmHome','confirmSnapshot','altitudePolicy','cameraPolicy']).length||options.confirmHome!==true||!['preserve-relative','preserve-implied-amsl'].includes(options.altitudePolicy)||!['preserve','stop-without-photo'].includes(options.cameraPolicy))fail('Cần xác nhận Home và chọn ý định độ cao/camera rõ ràng.');
 const intake=importQgc(raw),p=copy(intake.plan),m=p.mission,h=copy(m.plannedHomePosition),target=[SITL_WORLD.home.lat,SITL_WORLD.home.lon,SITL_WORLD.home.amsl];
 if(Math.abs(h[0]-target[0])>1e-7||Math.abs(h[1]-target[1])>1e-7)fail('Home ngang khác world SITL; không dịch Home hoặc tuyến.');
 if(intake.complex.length&&options.confirmSnapshot!==true)fail('Cần xác nhận bỏ thiết kế Survey trong bản dẫn xuất, chỉ giữ Items đã lưu.');
 m.plannedHomePosition=target;
 // Validate the untouched command/design semantics with only the disclosed Home reference changed.
 const validation=importQgc(JSON.stringify(p));validation.commands.forEach(({source},n)=>{source.doJumpId=n+1;});compileQgc(makeQgcRequest(JSON.stringify(validation.plan)));
 const heightChanges=[],cameraChanges=[],sequenceLabelChanges=[];m.items=intake.commands.map(({source,params},n)=>{const i=copy(source);delete i.coordinate;i.params=copy(params);if(i.doJumpId!==n+1)sequenceLabelChanges.push({sourceSeq:n+1,from:i.doJumpId??null,to:n+1});i.doJumpId=n+1;
  if([16,22].includes(i.command)){const old=i.params[6],next=options.altitudePolicy==='preserve-relative'?old:old+h[2]-target[2];i.params[6]=next;if(i.AltitudeMode!==undefined)i.Altitude=next;heightChanges.push({sourceSeq:n+1,relativeBefore:old,relativeAfter:next,impliedAmslBefore:h[2]+old,impliedAmslAfter:target[2]+next});}
  if(i.command===206&&i.params[0]===0&&i.params[2]===1&&options.cameraPolicy==='stop-without-photo'){i.params[2]=0;cameraChanges.push({sourceSeq:n+1,fromImmediate:1,toImmediate:0,meaning:'Remove the immediate stop-time photo explicitly; not mission equivalence'});}
  return i;
 });
 const compiled=compileQgc(makeQgcRequest(JSON.stringify(p))),out=exportQgc(compiled,{cameraSection:true}),result=JSON.parse(out.raw);
 const navSource=m.items.filter(i=>[16,22].includes(i.command));let navIndex=0;for(const i of result.mission.items)if([16,22].includes(i.command)){const original=navSource[navIndex++];i.params=copy(original.params);}
 for(const k of ['cruiseSpeed','hoverSpeed','globalPlanAltitudeMode'])if(m[k]!==undefined)result.mission[k]=m[k];
 const derived=JSON.stringify(result,null,2)+'\n',finalCompiled=compileQgc(makeQgcRequest(derived));
 return {raw:derived,receipt:{format:'aeris-qgc-derived-review',version:1,simulation:true,sourceSha256:await qgcSha256(raw),derivedSha256:await qgcSha256(derived),sourceRaw:raw,options:copy(options),homeBefore:h,homeAfter:target,heightChanges,cameraChanges,sequenceLabelChanges,insertions:out.receipt.insertions,flattenedComplex:intake.complex.length,normalizations:finalCompiled.normalizations,diff:compareQgc(raw,derived),scope:'Explicit SITL-only derivative; sequential label repair without DO_JUMP support; no lateral relocation, terrain/AGL assertion, polygon regeneration or physical camera claim. Review/adoption sends no command.'}};
}
/** Conservative semantic diff for an external GCS roundtrip. No altitude or camera changes are forgiven. */
export function compareQgc(beforeRaw,afterRaw){
 const a=importQgc(beforeRaw),b=importQgc(afterRaw),changes=[];const ordered=x=>Array.isArray(x)?x.map(ordered):obj(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,ordered(x[k])])):x;const same=(x,y)=>JSON.stringify(ordered(x))===JSON.stringify(ordered(y));const add=(path,before,after)=>{if(!same(before,after))changes.push({path,before:copy(before??null),after:copy(after??null)});};
 for(const k of ['version','plannedHomePosition','firmwareType','vehicleType','globalPlanAltitudeMode','cruiseSpeed','hoverSpeed'])add('mission.'+k,a.plan.mission[k],b.plan.mission[k]);for(const k of ['geoFence','rallyPoints'])add(k,a.plan[k],b.plan[k]);
 for(const k of new Set([...Object.keys(a.plan),...Object.keys(b.plan)]))if(!['groundStation','mission','geoFence','rallyPoints'].includes(k))add(k,a.plan[k],b.plan[k]);const missionExtra=x=>Object.fromEntries(Object.entries(x).filter(([k])=>!['version','plannedHomePosition','firmwareType','vehicleType','globalPlanAltitudeMode','cruiseSpeed','hoverSpeed','items'].includes(k)));add('mission.extensions',missionExtra(a.plan.mission),missionExtra(b.plan.mission));
 add('commandCount',a.commands.length,b.commands.length);for(let n=0;n<Math.max(a.commands.length,b.commands.length);n++){const x=a.commands[n],y=b.commands[n];if(!x||!y){add(`items[${n}]`,x?.source,y?.source);continue;}for(const k of ['command','frame','autoContinue','AltitudeMode','Altitude','AMSLAltAboveTerrain'])add(`items[${n}].${k}`,x.source[k],y.source[k]);for(let i=0;i<7;i++)add(`items[${n}].params[${i}]`,x.params[i],y.params[i]);const extensions=c=>Object.fromEntries(Object.entries(c.source).filter(([k])=>!['type','doJumpId','command','frame','autoContinue','AltitudeMode','Altitude','AMSLAltAboveTerrain','params','coordinate'].includes(k)));add(`items[${n}].extensions`,extensions(x),extensions(y));}
 add('complexCount',a.complex.length,b.complex.length);for(let n=0;n<Math.max(a.complex.length,b.complex.length);n++){const x=a.complex[n],y=b.complex[n];if(!x||!y){add(`complex[${n}]`,x,y);continue;}const settings=c=>{const out=copy(c);delete out.TransectStyleComplexItem.Items;delete out.TransectStyleComplexItem.VisualTransectPoints;delete out.TransectStyleComplexItem.CameraShots;delete out.doJumpId;return out;};add(`complex[${n}].settings`,settings(x),settings(y));}
 return {format:'aeris-qgc-semantic-diff',version:1,equal:changes.length===0,changes,before:a.summary,after:b.summary,scope:'Strict semantic comparison; formatting/key order/doJumpId/groundStation ignored. Null yaw, camera flags, Home and generated coordinates remain visible. Comparison sends no flight command.'};
}
