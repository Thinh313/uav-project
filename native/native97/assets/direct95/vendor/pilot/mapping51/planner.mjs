import {localFrame,planPolygonSurvey} from '../../app/core/survey.mjs';
import {CAMERA,POLICY,exact,num,sha,seal,clone} from './common.mjs';
export function cameraProfile(c){exact(c,Object.keys(CAMERA).join(','),'CAMERA');if(c.profileVersion!==1)throw Error('CAMERA_PROFILE_VERSION');for(const k of ['id','lensId','calibrationId'])if(typeof c[k]!=='string'||!c[k].trim()||c[k].length>100||['UNKNOWN','UNAVAILABLE','NOT_CHECKED'].includes(c[k].trim().toUpperCase()))throw Error('CAMERA_ID');
 for(const[k,lo,hi]of [['iso',100,6400],['apertureF',1.4,22],['sensorWidthMm',1,60],['sensorHeightMm',1,60],['imageWidthPx',100,20000],['imageHeightPx',100,20000],['focalLengthMm',5,200],['minIntervalS',.05,30],['readoutS',0,.2],['exposureS',.00001,.1]])num(c[k],lo,hi,k);
 if(!Number.isInteger(c.iso))throw Error('ISO_INTEGER');if(!Number.isInteger(c.imageWidthPx)||!Number.isInteger(c.imageHeightPx)||Math.abs(c.sensorWidthMm/c.sensorHeightMm-c.imageWidthPx/c.imageHeightPx)>.01)throw Error('CAMERA_ASPECT');
 if(c.provenance!=='SYNTHETIC_FIXTURE'||!['GLOBAL','ROLLING','FOCAL_PLANE'].includes(c.shutterKind)||c.shutterKind==='GLOBAL'&&c.readoutS!==0||c.shutterKind!=='GLOBAL'&&c.readoutS<=0||!['LOCKED_FOR_STRIP','CONTINUOUS','UNKNOWN'].includes(c.focusMode))throw Error('CAMERA_MODEL');return c;}
function cross(a,b,c){return(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)}
function hit(a,b,c,d){const on=(p,q,r)=>Math.abs(cross(p,q,r))<1e-6&&r.x>=Math.min(p.x,q.x)-1e-6&&r.x<=Math.max(p.x,q.x)+1e-6&&r.y>=Math.min(p.y,q.y)-1e-6&&r.y<=Math.max(p.y,q.y)+1e-6;return cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0||on(a,b,c)||on(a,b,d)||on(c,d,a)||on(c,d,b)}
export function compile(document,featureId,options,camera=CAMERA){
 exact(options,'altitudeAglM,speedMS,frontOverlapPct,sideOverlapPct,headingDeg,corridorWidthM,positioning,baseId,reference,terrain,datumAcknowledged','OPTIONS');cameraProfile(camera);
 num(options.altitudeAglM,10,120,'AGL');num(options.speedMS,.5,15,'SPEED');num(options.frontOverlapPct,50,90,'FRONT');num(options.sideOverlapPct,50,90,'SIDE');num(options.headingDeg,0,179.9,'HEADING');num(options.corridorWidthM,5,200,'WIDTH');
 if(!['RTK','PPK'].includes(options.positioning)||options.baseId!=='mock-base-01'||options.reference!=='MOCK-WGS84-ELLIPSOID')throw Error('POSITION_REFERENCE');
 if(options.terrain!=='SYNTHETIC_FLAT')throw Error('TERRAIN_UNKNOWN');if(options.datumAcknowledged!==true)throw Error('FLAT_AGL_REVIEW_REQUIRED');
 if(document.format!=='aeris-kml-aoi51'||document.version!==1||document.operational!==false)throw Error('DOCUMENT_VERSION');
 const feature=document.features.find(f=>f.id===featureId);if(!feature)throw Error('EXPLICIT_FEATURE_REQUIRED');if(feature.inspectionOnly||feature.holes.length||!feature.visible||feature.altitudeMode!=='clampToGround')throw Error('FEATURE_INSPECTION_ONLY');
 const points=feature.coordinates.map(p=>({lon:p[0],lat:p[1]}));const origin={lat:points.reduce((a,p)=>a+p.lat,0)/points.length,lon:points.reduce((a,p)=>a+p.lon,0)/points.length};
 if(Math.max(...points.map(p=>p.lon))-Math.min(...points.map(p=>p.lon))>1)throw Error('DATELINE_OR_EXTENT');const frame=localFrame(origin),local=points.map(p=>frame.forward(p));
 for(let i=0;i<local.length;i++)for(let j=i+1;j<local.length;j++)if(Math.hypot(local[i].x-local[j].x,local[i].y-local[j].y)>2500)throw Error('LOCAL_EXTENT');
 const c={name:camera.id,provenance:'demo',sensorWidth:camera.sensorWidthMm,sensorHeight:camera.sensorHeightMm,focalLength:camera.focalLengthMm,imageWidth:camera.imageWidthPx,minInterval:camera.minIntervalS};
 const settings=(polygon,heading)=>({name:feature.name.slice(0,80),polygon,altitude:options.altitudeAglM,altitudeFrame:'flat-reference',speed:options.speedMS,heading,sideOverlap:options.sideOverlapPct,frontOverlap:options.frontOverlapPct,targetGsdCm:null,camera:c});
 const legs=[],regions=[],warnings=['SYNTHETIC_FLAT_ONLY','TRANSIT_TERRAIN_OBSTACLES_AIRSPACE_NOT_CHECKED'];
 if(feature.coordinates.some(p=>p[2]!==null&&p[2]!==0))warnings.push('KML_Z_RETAINED_BUT_IGNORED_BY_CLAMP');
 if(feature.kind==='Polygon'){
  const poly=points.slice(0,-1),p=planPolygonSurvey(settings(poly,options.headingDeg));regions.push(poly);for(const t of p.transects)legs.push({region:0,start:t.startGeo,end:t.endGeo,shots:t.shots,lengthM:t.length});if(p.hasOutsideConnector)warnings.push('CONCAVE_CONNECTOR_OUTSIDE_AOI');
 }else if(feature.kind==='LineString'){
  for(let i=0;i<local.length-1;i++){
   const a=local[i],b=local[i+1],dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy);if(len<2)throw Error('LINE_DUPLICATE_OR_SHORT_SEGMENT');
   for(let j=i+2;j<local.length-1;j++)if(hit(a,b,local[j],local[j+1]))throw Error('LINE_SELF_INTERSECTION');
   if(i&&cross(local[i-1],a,b)===0&&((a.x-local[i-1].x)*dx+(a.y-local[i-1].y)*dy)<=0)throw Error('LINE_BACKTRACK');
   const ux=dx/len,uy=dy/len,h=options.corridorWidthM/2,rect=[{x:a.x-ux*h-uy*h,y:a.y-uy*h+ux*h},{x:a.x-ux*h+uy*h,y:a.y-uy*h-ux*h},{x:b.x+ux*h+uy*h,y:b.y+uy*h-ux*h},{x:b.x+ux*h-uy*h,y:b.y+uy*h+ux*h}].map(p=>frame.reverse(p));
   const footprint=options.altitudeAglM*camera.sensorWidthMm/camera.focalLengthMm,trigger=options.altitudeAglM*camera.sensorHeightMm/camera.focalLengthMm*(1-options.frontOverlapPct/100),usable=Math.max(0,options.corridorWidthM-footprint),spacing=footprint*(1-options.sideOverlapPct/100),count=usable===0?1:Math.ceil(usable/spacing-1e-9)+1;
   if(count>128)throw Error('CORRIDOR_LANE_BOUND');regions.push(rect);
   for(let lane=0;lane<count;lane++){
    const offset=count===1?0:-usable/2+lane*usable/(count-1),start=frame.reverse({x:a.x-ux*h-uy*offset,y:a.y-uy*h+ux*offset}),end=frame.reverse({x:b.x+ux*h-uy*offset,y:b.y+uy*h+ux*offset});
    legs.push({region:i,start:lane%2?end:start,end:lane%2?start:end,shots:Math.ceil((len+2*h)/trigger-1e-9)+1,lengthM:len+2*h});
   }
  }
  warnings.push('SEGMENT_RECTANGLES_OVERLAP_DUPLICATES_AND_OVERSCAN');
 }else throw Error('GEOMETRY_UNSUPPORTED');
 if(!legs.length||legs.length>512||legs.reduce((s,t)=>s+t.shots,0)>10000)throw Error('MISSION_SIZE');
 const footprintAcrossM=options.altitudeAglM*camera.sensorWidthMm/camera.focalLengthMm,footprintAlongM=options.altitudeAglM*camera.sensorHeightMm/camera.focalLengthMm,gsdM=footprintAcrossM/camera.imageWidthPx;
 let distanceM=0;for(let i=0;i<legs.length;i++){distanceM+=legs[i].lengthM;if(i){const a=frame.forward(legs[i-1].end),b=frame.forward(legs[i].start);distanceM+=Math.hypot(a.x-b.x,a.y-b.y)}}
 const minIntervalS=Math.min(...legs.map(l=>l.lengthM/(l.shots-1)/options.speedMS));
 return seal({format:'aeris-acquisition-plan51',version:1,scope:'HOST_MOCK_ONLY',operational:false,sourceSha256:document.sourceSha256,documentSha256:sha(document),featureId,feature:clone(feature),camera:clone(camera),options:clone(options),policy:clone(POLICY),regions,legs,metrics:{gsdCm:gsdM*100,footprintAcrossM,footprintAlongM,translationBlurPx:options.speedMS*camera.exposureS/gsdM,readoutDisplacementPx:options.speedMS*camera.readoutS/gsdM,minIntervalS,photoCommands:legs.reduce((s,t)=>s+t.shots,0),distanceM,nominalSeconds:distanceM/options.speedMS},warnings,actualCoverage:'NOT_CHECKED',safetyClearance:'NOT_CHECKED',model:feature.kind==='Polygon'?'frozen-survey-flat51':'square-capped-segment-cover51'});
}
