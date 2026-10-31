// Engineering mathematics for offline comparison, independent of the frozen app.
const fail = message => { throw new Error(message); };
const num = x => typeof x === 'number' && Number.isFinite(x);
const need = (ok, message) => { if (!ok) fail(message); };
const radians = x => x * Math.PI / 180;
const hash = x => typeof x === 'string' && /^[0-9a-f]{64}$/.test(x);
export function coordinate(point) {
  need(Array.isArray(point) && point.length === 2 && point.every(num), 'COORD_TYPE');
  need(Math.abs(point[0]) <= 90 && Math.abs(point[1]) <= 180, 'COORD_RANGE_OR_AXIS');
  return point;
}
export function inverseWgs84(a, b) {
  coordinate(a); coordinate(b);
  const major=6378137, flattening=1/298.257223563, minor=major*(1-flattening);
  const U1=Math.atan((1-flattening)*Math.tan(radians(a[0]))), U2=Math.atan((1-flattening)*Math.tan(radians(b[0])));
  const sinU1=Math.sin(U1),cosU1=Math.cos(U1),sinU2=Math.sin(U2),cosU2=Math.cos(U2);
  const L=radians(((b[1]-a[1]+540)%360)-180);
  if (a[0]===b[0] && L===0) return {distanceM:0, method:'Vincenty-WGS84',iterations:0};
  let lambda=L,sigma,sinSigma,cosSigma,cosSqAlpha,cos2SigmaM,iteration=0;
  for (; iteration<200; iteration++) {
    const sinLambda=Math.sin(lambda),cosLambda=Math.cos(lambda);
    sinSigma=Math.hypot(cosU2*sinLambda,cosU1*sinU2-sinU1*cosU2*cosLambda);
    need(sinSigma>1e-16,'GEODESIC_DEGENERATE_OR_ANTIPODAL');
    cosSigma=sinU1*sinU2+cosU1*cosU2*cosLambda;sigma=Math.atan2(sinSigma,cosSigma);
    const sinAlpha=cosU1*cosU2*sinLambda/sinSigma;cosSqAlpha=Math.max(0,1-sinAlpha*sinAlpha);
    cos2SigmaM=cosSqAlpha<1e-15?0:cosSigma-2*sinU1*sinU2/cosSqAlpha;
    const C=flattening/16*cosSqAlpha*(4+flattening*(4-3*cosSqAlpha));
    const next=L+(1-C)*flattening*sinAlpha*(sigma+C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)));
    if (Math.abs(next-lambda)<1e-13) { lambda=next; break; }
    lambda=next;
  }
  need(iteration<200,'GEODESIC_NONCONVERGENT_NO_SPHERE_FALLBACK');
  const uSq=cosSqAlpha*(major*major-minor*minor)/(minor*minor);
  const A=1+uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)));
  const B=uSq/1024*(256+uSq*(-128+uSq*(74-47*uSq)));
  const correction=B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)));
  return {distanceM:minor*A*(sigma-correction),method:'Vincenty-WGS84',iterations:iteration+1,
    limitation:'Near-antipodal nonconvergence rejects; not a globally complete Karney implementation'};
}
function cross(a,b,c) { return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]); }
function on(a,b,p) { return Math.abs(cross(a,b,p))<1e-9 && p[0]>=Math.min(a[0],b[0])-1e-9 && p[0]<=Math.max(a[0],b[0])+1e-9 && p[1]>=Math.min(a[1],b[1])-1e-9 && p[1]<=Math.max(a[1],b[1])+1e-9; }
function intersects(a,b,c,d) { return cross(a,b,c)*cross(a,b,d)<0 && cross(c,d,a)*cross(c,d,b)<0 || on(a,b,c)||on(a,b,d)||on(c,d,a)||on(c,d,b); }
export function planarArea(points, frame) {
  need(frame==='LOCAL_PLANAR_METERS','AREA_METRIC_NOT_DECLARED');
  need(Array.isArray(points)&&points.length>=3&&points.length<=256,'POLYGON_SIZE');
  points=points.map(p=>{need(Array.isArray(p)&&p.length===2&&p.every(num),'POLYGON_TYPE');return [...p];});
  if (points[0].every((v,k)=>v===points.at(-1)[k])) points.pop();
  need(points.length>=3,'POLYGON_DEGENERATE');
  for(let i=0;i<points.length;i++) {
    const j=(i+1)%points.length;
    need(points[i].some((v,k)=>v!==points[j][k]),'POLYGON_DUPLICATE_EDGE');
    for(let k=i+1;k<points.length;k++) {
      const l=(k+1)%points.length;
      if (j===k || l===i) continue;
      need(!intersects(points[i],points[j],points[k],points[l]),'POLYGON_SELF_INTERSECTION');
    }
  }
  const origin=points[0];let twice=0;
  for(let i=0;i<points.length;i++)twice+=cross(origin,points[i],points[(i+1)%points.length]);
  need(Math.abs(twice)>1e-9,'POLYGON_ZERO_AREA');
  return {areaM2:Math.abs(twice)/2,hectares:Math.abs(twice)/20000,metric:frame};
}
export function legTime(legs) {
  need(Array.isArray(legs)&&legs.length>0&&legs.length<=10000,'LEG_LIMIT');let seconds=0;
  for(const leg of legs) {need(num(leg.distanceM)&&leg.distanceM>=0&&num(leg.speedMps)&&leg.speedMps>0&&num(leg.delayS)&&leg.delayS>=0,'LEG_INVALID');seconds+=leg.distanceM/leg.speedMps+leg.delayS;}
  return {seconds,model:'constant speed per leg + explicit delay; no wind/acceleration/turn model'};
}
export function cameraModel(input) {
  const {heightM,sensorWidthMm,focalLengthMm,imageWidthPx,footprintAlongM,frontOverlap,velocityMps,minPeriodS}=input;
  for(const x of [heightM,sensorWidthMm,focalLengthMm,imageWidthPx,footprintAlongM,velocityMps])need(num(x)&&x>0,'CAMERA_POSITIVE');
  need(Number.isInteger(imageWidthPx)&&num(frontOverlap)&&frontOverlap>=0&&frontOverlap<1,'CAMERA_OVERLAP_PIXELS');
  need(minPeriodS===null||num(minPeriodS)&&minPeriodS>0,'CAMERA_PERIOD');
  const spacingM=footprintAlongM*(1-frontOverlap),periodS=spacingM/velocityMps;
  return {spacingM,periodS,gsdM:heightM*(sensorWidthMm/focalLengthMm)/imageWidthPx,
    cadence:minPeriodS===null?'NOT_CHECKED':periodS+1e-12>=minPeriodS?'MODEL_FEASIBLE':'MODEL_TOO_FAST',
    scope:'synthetic flat nadir optics; not observed image quality'};
}
export function photoCount(lengths,spacingM,policy) {
  need(Array.isArray(lengths)&&lengths.length>0&&lengths.length<=10000,'TRANSECT_LIMIT');
  need(num(spacingM)&&spacingM>0 && policy?.name==='EXPLICIT_ENDPOINT_GRID_V1'&&typeof policy.includeEntry==='boolean'&&typeof policy.includeExit==='boolean','PHOTO_POLICY_REQUIRED');
  const counts=lengths.map(length=>{
    need(num(length)&&length>0&&length/spacingM<1e7,'TRANSECT_LENGTH');
    const ratio=length/spacingM,rounded=Math.round(ratio),exact=Math.abs(ratio-rounded)<1e-10;
    let n=Math.floor(ratio);if(exact)n=rounded;
    if(exact&&!policy.includeExit)n--;
    if(!exact&&policy.includeExit)n++;
    if(policy.includeEntry)n++;
    return n;
  });
  return {counts,total:counts.reduce((a,b)=>a+b,0),policy,scope:'Declared synthetic endpoint policy; QGC shot algorithm equivalence NOT_CHECKED'};
}
function samePoint(source,point) {coordinate([source.lat,source.lon]);coordinate(point);need(Math.abs(source.lat-point[0])<=1e-7&&Math.abs(source.lon-point[1])<=1e-7,'SOURCE_COORDINATE_MISMATCH');}
function sourceGuard(source,ctx,point) {
  need(source&&source.session===ctx.session&&source.boot===ctx.boot,'SOURCE_SESSION_BOOT');
  need(num(ctx.maxAgeMs)&&ctx.maxAgeMs>0&&num(source.ageMs)&&source.ageMs>=0&&source.ageMs<=ctx.maxAgeMs,'SOURCE_STALE');
  need(typeof ctx.datum==='string'&&ctx.datum!=='UNKNOWN'&&source.datum===ctx.datum,'DATUM_UNKNOWN_OR_MISMATCH');
  if(point)samePoint(source,point);
}
export function resolveAltitude(input,ctx) {
  need(input&&num(input.valueM)&&typeof ctx.session==='string'&&Number.isInteger(ctx.boot),'ALTITUDE_CONTEXT');
  coordinate(input.coordinate);let amslM,frame,z,sourceHashes=[];
  switch(input.mode) {
    case 'relative':sourceGuard(ctx.home,ctx);need(num(ctx.home.amslM),'HOME_AMSL');amslM=ctx.home.amslM+input.valueM;frame=3;z=input.valueM;break;
    case 'amsl':need(typeof ctx.datum==='string'&&ctx.datum!=='UNKNOWN'&&input.datum===ctx.datum,'ABSOLUTE_DATUM');amslM=input.valueM;frame=0;z=amslM;break;
    case 'terrain_calc':case 'terrain_native':
      sourceGuard(ctx.terrain,ctx,input.coordinate);need(num(ctx.terrain.amslM)&&hash(ctx.terrain.sha256)&&ctx.terrain.noData===false,'TERRAIN_MISSING_HASH_OR_NODATA');
      amslM=ctx.terrain.amslM+input.valueM;frame=input.mode==='terrain_native'?10:0;z=frame===10?input.valueM:amslM;sourceHashes.push(ctx.terrain.sha256);break;
    case 'ellipsoid':
      sourceGuard(ctx.geoid,ctx,input.coordinate);need(num(ctx.geoid.separationM)&&hash(ctx.geoid.sha256)&&typeof ctx.geoid.model==='string','GEOID_SOURCE');
      amslM=input.valueM-ctx.geoid.separationM;frame=0;z=amslM;sourceHashes.push(ctx.geoid.sha256);break;
    default:fail('ALTITUDE_MODE_UNSUPPORTED');
  }
  return {amslM,frame,z,datum:ctx.datum,sourceHashes,flightReady:false,scope:'synthetic explicit-context arithmetic, not surveyed launch/datum acceptance'};
}
export function ridgeClearance(groundSamples,plannedM) {
  need(Array.isArray(groundSamples)&&groundSamples.length>=2&&groundSamples.length<=10000&&num(plannedM),'TERRAIN_SAMPLES');
  need(groundSamples.every(num),'TERRAIN_NO_DATA');
  const clearanceM=groundSamples.map(g=>plannedM-g);
  return {clearanceM,minimumM:Math.min(...clearanceM),modelConflict:clearanceM.some(x=>x<0),
    scope:'Only provided samples; no full-cell obstacle or trajectory guarantee'};
}
export function evaluate(op,args) {
  switch(op){case 'area':return planarArea(args.points,args.frame);case 'inverse':return inverseWgs84(args.a,args.b);
    case 'time':return legTime(args.legs);case 'camera':return cameraModel(args);case 'photos':return photoCount(args.lengths,args.spacingM,args.policy);
    case 'altitude':return resolveAltitude(args.input,args.context);case 'ridge':return ridgeClearance(args.ground,args.plannedM);default:fail('UNKNOWN_OPERATION');}
}
