/** Host/mock workbench. No vehicle sockets, flight commands, real camera or DEM. */
import {compile} from '../mapping51/planner.mjs';
import {CAMERA,OPTIONS,sha,stable,seal,unseal,exact,num} from '../mapping51/common.mjs';
import {fixture,readiness} from '../mapping51/readiness.mjs';
import {localFrame,pointInPolygon} from '../../app/core/survey.mjs';
import {planarArea} from '../mission55/geo.mjs';
export const VERSION='workbench01-v1';
export const HOME={lat:10.854,lon:106.807};
export const ENERGY={batteryWh:180,powerW:600,payloadKg:0,extraPowerWPerKg:60,windMps:0,reservePct:30,climbLandingS:45};
export const DEFAULTS={...OPTIONS,altitudeAglM:60,speedMS:4,datumAcknowledged:false};
export const SCENARIOS=['nominal','missing','blur','clipped','ack-only','clock-skew','wrong-camera','tilted','link-loss'];
const need=(x,m)=>{if(!x)throw Error(m);};
const finite=p=>p&&Number.isFinite(p.x)&&Number.isFinite(p.y);
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
export function energyBudget(legs,home,options,profile){
 exact(profile,Object.keys(ENERGY).join(','),'ENERGY');
 for(const[k,a,b]of[['batteryWh',1,10000],['powerW',1,20000],['payloadKg',0,30],['extraPowerWPerKg',0,1000],['windMps',0,30],['reservePct',20,80],['climbLandingS',0,600]])num(profile[k],a,b,k);
 need(finite(home),'HOME');
 const groundSpeed=options.speedMS-profile.windMps;
 if(groundSpeed<=.2)return {status:'BLOCKED',reason:'WIND_EXCEEDS_MODEL_GROUND_SPEED',sorties:[],model:'CONSTANT_POWER_SYNTHETIC_NOT_HERA_CALIBRATED'};
 const usableWh=profile.batteryWh*(1-profile.reservePct/100),powerW=profile.powerW+profile.payloadKg*profile.extraPowerWPerKg;
 const sorties=[];let current=[];
 function cost(xs){let distance=dist(home,xs[0].start)+dist(xs.at(-1).end,home);for(let i=0;i<xs.length;i++){distance+=dist(xs[i].start,xs[i].end);if(i)distance+=dist(xs[i-1].end,xs[i].start);}const seconds=distance/groundSpeed+profile.climbLandingS;return {distanceM:distance,seconds,requiredWh:seconds/3600*powerW};}
 function finish(){if(current.length){sorties.push({index:sorties.length+1,legIds:current.map(x=>x.id),...cost(current)});current=[];}}
 for(const leg of legs){if(cost([leg]).requiredWh>usableWh)return {status:'BLOCKED',reason:'SINGLE_LEG_EXCEEDS_USABLE_ENERGY',failedLeg:leg.id,sorties:[],usableWh,powerW,model:'CONSTANT_POWER_SYNTHETIC_NOT_HERA_CALIBRATED'};if(current.length&&cost([...current,leg]).requiredWh>usableWh)finish();current.push(leg);}finish();
 return {status:'MODEL_FEASIBLE',sorties,usableWh,powerW,groundSpeedMps:groundSpeed,reservePct:profile.reservePct,model:'CONSTANT_POWER_SYNTHETIC_NOT_HERA_CALIBRATED',limitations:['Same worst-case headwind in every direction','No battery voltage/temperature/aging model','Turns/climb simplified; transit/terrain/airspace NOT_CHECKED']};
}
export function createPlan(document,input){
 exact(input,'kml,featureId,options,camera,home,energy','INPUT');
 need(typeof input.kml==='string'&&Buffer.byteLength(input.kml)<=262144,'KML_BOUND');
 need(document.sourceSha256===sha(input.kml),'KML_SOURCE_BINDING');
 exact(input.home,'lat,lon','HOME');num(input.home.lat,-70,70,'HOME_LAT');num(input.home.lon,-180,180,'HOME_LON');
 const acquisition=compile(document,input.featureId,input.options,input.camera);
 const coords=acquisition.feature.coordinates;
 const origin={lat:coords.reduce((s,p)=>s+p[1],0)/coords.length,lon:coords.reduce((s,p)=>s+p[0],0)/coords.length};const frame=localFrame(origin);
 const home=frame.forward(input.home);need(Math.hypot(home.x,home.y)<2500,'HOME_OUTSIDE_LOCAL_DOMAIN');
 const regions=acquisition.regions.map(r=>r.map(p=>frame.forward(p)));
 for(const r of regions)planarArea(r.map(p=>[p.x,p.y]),'LOCAL_PLANAR_METERS');
 const legs=acquisition.legs.map((l,i)=>({id:`L${i+1}`,start:frame.forward(l.start),end:frame.forward(l.end),shots:l.shots}));
 need(acquisition.metrics.photoCommands<=1500,'WORKBENCH_PHOTO_BOUND_1500');
 const shots=[];
 for(const l of legs){const n=Math.hypot(l.end.x-l.start.x,l.end.y-l.start.y),ux=(l.end.x-l.start.x)/n,uy=(l.end.y-l.start.y)/n;for(let j=0;j<l.shots;j++){const t=l.shots===1?.5:j/(l.shots-1);shots.push({id:`P${String(shots.length+1).padStart(4,'0')}`,legId:l.id,x:l.start.x+(l.end.x-l.start.x)*t,y:l.start.y+(l.end.y-l.start.y)*t,ux,uy,alongM:acquisition.metrics.footprintAlongM,acrossM:acquisition.metrics.footprintAcrossM});}}
 return seal({format:VERSION,operational:false,authorityRestorable:false,provenance:'SYNTHETIC_FLAT_NADIR',input,acquisition,origin,home,regions,legs,shots,energy:energyBudget(legs,home,input.options,input.energy),plannedAt:'DETERMINISTIC_NO_WALL_CLOCK'});
}
export function preflight(plan){
 unseal(plan);const ctx={sessionId:'wb01-session',bootId:'wb01-boot',aircraftId:'synthetic-aircraft',clockId:'MOCK_MONOTONIC'};
 const base=readiness(plan.acquisition,fixture(plan.acquisition,ctx,1000),ctx,1000);
 base.checks.push({id:'ENERGY',pass:plan.energy.status==='MODEL_FEASIBLE',detail:plan.energy.reason??'Dự toán điện năng tổng hợp, chưa hiệu chuẩn Hera'});
 base.readyForMock=base.checks.every(x=>x.pass);base.status=base.readyForMock?'READY_FOR_MOCK':'BLOCKED';return base;
}
export function pixelStats(pixels){
 need(Array.isArray(pixels)&&pixels.length===256&&pixels.every(v=>Number.isInteger(v)&&v>=0&&v<=255),'PIXEL_BOUND');
 let sum=0,sq=0,n=0;for(let y=1;y<15;y++)for(let x=1;x<15;x++){const i=y*16+x,v=pixels[i-16]+pixels[i+16]+pixels[i-1]+pixels[i+1]-4*pixels[i];sum+=v;sq+=v*v;n++;}
 const mean=pixels.reduce((a,b)=>a+b,0)/256,clippedFraction=pixels.filter(v=>v<=2||v>=253).length/256;
 return {laplacianVariance:sq/n-(sum/n)**2,mean,clippedFraction,thresholdScope:'16x16 synthetic fixtures only; no real-camera calibration'};
}
export function syntheticPixels(kind='sharp'){return Array.from({length:256},(_,i)=>kind==='clipped'?255:kind==='blur'?Math.round(120+(i%16)/2):((Math.floor(i/16)+i%16)%2?205:45));}
export function makeRecord(plan,shot,index,kind='nominal'){
 const pixels=['missing','ack-only'].includes(kind)?null:syntheticPixels(kind);
 const t=Math.round(index*1000+1000);
 return {id:shot.id,planSha256:plan.sha256,cameraId:kind==='wrong-camera'?'other-camera':plan.input.camera.id,provenance:'SYNTHETIC_PIXELS',clockId:'MOCK_MONOTONIC',cameraAtMs:t,navAtMs:t+(kind==='clock-skew'?500:0),x:shot.x,y:shot.y,tiltDeg:kind==='tilted'?12:0,exposure:!['missing','ack-only'].includes(kind),ack:kind!=='missing',pixels,pixelSha256:pixels?sha(pixels):null};
}
export function replay(plan,scenario='nominal'){
 need(SCENARIOS.includes(scenario),'SCENARIO');
 return plan.shots.filter((_,i)=>scenario!=='link-loss'||i<Math.floor(plan.shots.length/2)).map((s,i)=>makeRecord(plan,s,i,(scenario==='missing'?(i>=plan.shots.length*.3&&i<plan.shots.length*.7):i%5===0)?scenario:'nominal'));
}
export function qualify(plan,records){
 need(Array.isArray(records)&&records.length<=1500,'RECORD_BOUND');const ids=new Set(),shotMap=new Map(plan.shots.map(s=>[s.id,s]));
 return records.map(r=>{
  exact(r,'id,planSha256,cameraId,provenance,clockId,cameraAtMs,navAtMs,x,y,tiltDeg,exposure,ack,pixels,pixelSha256','RECORD');
  need(typeof r.id==='string'&&!ids.has(r.id),'DUPLICATE_RECORD');ids.add(r.id);
  need(typeof r.exposure==='boolean'&&typeof r.ack==='boolean','RECORD_BOOLEAN');
  const s=shotMap.get(r.id),reasons=[];let stats=null;
  if(!s)reasons.push('UNKNOWN_SHOT');
  if(r.planSha256!==plan.sha256)reasons.push('WRONG_PLAN');
  if(r.cameraId!==plan.input.camera.id)reasons.push('WRONG_CAMERA');
  if(r.provenance!=='SYNTHETIC_PIXELS')reasons.push('UNSUPPORTED_MEDIA_PROVENANCE');
  if(r.clockId!=='MOCK_MONOTONIC'||!Number.isSafeInteger(r.cameraAtMs)||!Number.isSafeInteger(r.navAtMs)||r.cameraAtMs<0||r.navAtMs<0||Math.abs(r.cameraAtMs-r.navAtMs)>50)reasons.push('CLOCK_UNQUALIFIED');
  if(!finite(r)||Math.hypot(r.x,r.y)>5000||!Number.isFinite(r.tiltDeg)||Math.abs(r.tiltDeg)>3)reasons.push('POSE_UNQUALIFIED');
  if(!r.exposure)reasons.push('NO_EXPOSURE');
  if(r.pixels===null){reasons.push('NO_PIXEL_FILE');need(r.pixelSha256===null,'PIXEL_HASH_WITHOUT_PIXELS');}
  else{stats=pixelStats(r.pixels);need(sha(r.pixels)===r.pixelSha256,'PIXEL_DIGEST_MISMATCH');}
  const acquired=reasons.length===0;
  if(stats&&stats.laplacianVariance<100)reasons.push('BLUR_SYNTHETIC');
  if(stats&&stats.clippedFraction>.1)reasons.push('CLIPPING_SYNTHETIC');
  return {id:r.id,acquired,quality:acquired&&reasons.length===0,reasons,stats,footprint:s?{...s,x:r.x,y:r.y}:null};
 });
}
export function coverage(plan,qualified=[],stepM=5){
 num(stepM,1,25,'GRID_STEP');const ps=plan.regions.flat(),minX=Math.floor(Math.min(...ps.map(p=>p.x))/stepM)*stepM,minY=Math.floor(Math.min(...ps.map(p=>p.y))/stepM)*stepM;
 const nx=Math.ceil((Math.max(...ps.map(p=>p.x))-minX)/stepM),ny=Math.ceil((Math.max(...ps.map(p=>p.y))-minY)/stepM);need(nx*ny<=32000,'COVERAGE_GRID_BOUND');
 const cells=[],index=new Map();for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const p={x:minX+(i+.5)*stepM,y:minY+(j+.5)*stepM};if(plan.regions.some(poly=>pointInPolygon(p,poly))){const c={...p,i,j,planned:0,acquired:0,quality:0};cells.push(c);index.set(j*nx+i,c);}}
 need(cells.length>0,'AOI_SMALLER_THAN_GRID_SELECT_FINER_RESOLUTION');
 let work=0;
 function add(f,key){const a=f.alongM/2,b=f.acrossM/2,rx=Math.abs(f.ux)*a+Math.abs(f.uy)*b,ry=Math.abs(f.uy)*a+Math.abs(f.ux)*b;
  const i0=Math.max(0,Math.floor((f.x-rx-minX)/stepM)),i1=Math.min(nx-1,Math.floor((f.x+rx-minX)/stepM)),j0=Math.max(0,Math.floor((f.y-ry-minY)/stepM)),j1=Math.min(ny-1,Math.floor((f.y+ry-minY)/stepM));
  for(let j=j0;j<=j1;j++)for(let i=i0;i<=i1;i++){need(++work<=8000000,'COVERAGE_WORK_BOUND');const c=index.get(j*nx+i);if(!c)continue;const dx=c.x-f.x,dy=c.y-f.y;if(Math.abs(dx*f.ux+dy*f.uy)<=a+1e-8&&Math.abs(-dx*f.uy+dy*f.ux)<=b+1e-8)c[key]++;}}
 for(const f of plan.shots)add(f,'planned');for(const q of qualified){if(q.acquired)add(q.footprint,'acquired');if(q.quality)add(q.footprint,'quality');}
 const fraction=k=>100*cells.filter(c=>c[k]>0).length/cells.length;
 return {method:'UNION_OF_NADIR_RECTANGLES_AT_GRID_CELL_CENTERS',stepM,sampledAreaM2:cells.length*stepM**2,boundaryUncertainty:'No exact area or geodetic accuracy claim; cells sample AOI center, refine grid to compare',plannedPct:fraction('planned'),acquiredPct:fraction('acquired'),qualityPct:fraction('quality'),uncoveredCells:cells.filter(c=>c.quality===0).length,cells,work};
}
export function analyze(plan,records,stepM=5){unseal(plan);const photos=qualify(plan,records),grid=coverage(plan,photos,stepM);return {format:'workbench01-analysis',planSha256:plan.sha256,provenance:'SYNTHETIC_ONLY',actualFiles:0,recordCount:records.length,acceptedSynthetic:photos.filter(p=>p.quality).length,rejectedSynthetic:photos.filter(p=>!p.quality).length,missingRecords:plan.shots.length-records.filter(r=>plan.shots.some(s=>s.id===r.id)).length,photos,grid,fieldQuality:'NOT_CHECKED',photogrammetry:'NOT_IMPLEMENTED'};}
export function reflyProposal(plan,analysis){need(analysis.planSha256===plan.sha256,'REFLY_BINDING');const cells=analysis.grid.cells.filter(c=>!c.quality);const step=analysis.grid.stepM,groups=[];for(const c of cells){let g=groups.at(-1);if(!g||g.j!==c.j||c.i!==g.lastI+1){g={j:c.j,lastI:c.i,start:{x:c.x,y:c.y},end:{x:c.x,y:c.y},cells:0};groups.push(g);}g.lastI=c.i;g.end={x:c.x,y:c.y};g.cells++;}return seal({format:'workbench01-refly-proposal',planSha256:plan.sha256,analysisSha256:sha(analysis),stepM:step,missingAreaSampleM2:cells.length*step**2,segments:groups,operational:false,requiresSeparateMissionPlanning:true,safetyClearance:'NOT_CHECKED'});}
export function makeBundle(plan,records,stepM=5){const analysis=analyze(plan,records,stepM);const bundle=seal({format:'aeris-workbench01-workspace',version:1,operational:false,authorityRestorable:false,input:plan.input,documentSource:plan.acquisition.sourceSha256,planSha256:plan.sha256,records,stepM,analysisSha256:sha(analysis),proposal:reflyProposal(plan,analysis)});need(Buffer.byteLength(stable(bundle))<=2097152,'WORKSPACE_BOUND');return bundle;}
export function receive(bundle,document){
 exact(bundle,'format,version,operational,authorityRestorable,input,documentSource,planSha256,records,stepM,analysisSha256,proposal,sha256','BUNDLE');
 need(Buffer.byteLength(stable(bundle))<=2097152,'WORKSPACE_BOUND');unseal(bundle);
 need(bundle.format==='aeris-workbench01-workspace'&&bundle.version===1&&bundle.operational===false&&bundle.authorityRestorable===false,'WORKSPACE_SCOPE');
 const plan=createPlan(document,bundle.input);need(plan.sha256===bundle.planSha256&&document.sourceSha256===bundle.documentSource,'WORKSPACE_PLAN_BINDING');
 const analysis=analyze(plan,bundle.records,bundle.stepM);need(sha(analysis)===bundle.analysisSha256,'WORKSPACE_ANALYSIS_MISMATCH');need(stable(reflyProposal(plan,analysis))===stable(bundle.proposal),'WORKSPACE_PROPOSAL_MISMATCH');
 return {plan,analysis,records:bundle.records,proposal:bundle.proposal,authority:null,status:'VERIFIED_SYNTHETIC_WORKSPACE'};
}
