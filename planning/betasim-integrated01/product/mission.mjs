/** One simulation mission identity, with explicitly disjoint reference envelopes.
 * Existing survey/compiler code remains the semantic source, never a UI copy.
 */
import {createHash} from 'node:crypto';
import {parseKml94} from '../../../native/native94/assets/offline94/kml.mjs';
import {createPlan} from '../../../pilot/workbench01/core.mjs';
import {prepareSITL} from '../../../pilot/workbench02/sitl-contract.mjs';

export const PROFILES=Object.freeze({
 'M1-COCKPIT04-NOMINAL':Object.freeze({provider:'NATIVE_MANUAL',altitudeM:[1,5],radiusM:10,modes:['manual','assisted'],source:'EXACT_EXISTING_CONTROLFLIGHT_ENVELOPE'}),
 'WB02_SYNTHETIC_NATIVE92_PREPARATION':Object.freeze({provider:'HOST_AUTO',altitudeM:[10,30],speedMS:[.5,2],modes:['auto'],source:'EXACT_EXISTING_WORKBENCH02_ENVELOPE'}),
 'WORKBENCH_SIM_V1':Object.freeze({provider:'HOST_WORKBENCH',altitudeM:[10,30],speedMS:[.5,2],modes:['manual','assisted','auto'],source:'VERSIONED_WORKBENCH_ENVELOPE_ROOT_TYPED_GCS_LAND5_FS_OPTIONS0'})
});
export const canonical=value=>value===null||typeof value!=='object'?JSON.stringify(value):Array.isArray(value)?'['+value.map(canonical).join(',')+']':'{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
export const sha=value=>createHash('sha256').update(typeof value==='string'||Buffer.isBuffer(value)?value:canonical(value)).digest('hex');
export const need=(value,reason)=>{if(!value)throw Error(reason);};
const exact=(o,keys)=>need(o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).sort().join(',')===keys.split(',').sort().join(','),'PRODUCT_SCHEMA');
const finite=(x,a,b)=>typeof x==='number'&&Number.isFinite(x)&&x>=a&&x<=b;
export function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
function seal(body){return freeze({...body,sha256:sha(body)});}
function common(profileId,name,geometry,home,altitudeM){
 need(PROFILES[profileId],'PRODUCT_PROFILE_UNKNOWN');need(typeof name==='string'&&name.trim()&&name.length<=80&&!/[\x00-\x1f]/.test(name),'PRODUCT_NAME');
 need(Array.isArray(geometry)&&geometry.length>=2&&geometry.length<=64,'PRODUCT_GEOMETRY_BOUND');
 for(const p of geometry)need(Array.isArray(p)&&p.length===2&&finite(p[0],-90,90)&&finite(p[1],-180,180),'PRODUCT_WGS84_LAT_LON');
 need(home&&finite(home.lat,-70,70)&&finite(home.lon,-180,180),'PRODUCT_HOME');
 const profile=PROFILES[profileId];need(finite(altitudeM,...profile.altitudeM),'PRODUCT_PROFILE_ALTITUDE_NO_CLAMP');
 return {format:'aeris-unified-simulation-mission',version:1,profileId,provider:profile.provider,name:name.trim(),geometryWgs84LatLon:geometry,home,altitude:{valueM:altitudeM,datum:'RELATIVE_HOME_ON_EXPLICIT_SYNTHETIC_FLAT'},simulationOnly:true,authorityRestorable:false};
}
export async function autoMission(input,{confirmSyntheticHomeAmsl10=false,profileId='WORKBENCH_SIM_V1'}={}){
 need(['WB02_SYNTHETIC_NATIVE92_PREPARATION','WORKBENCH_SIM_V1'].includes(profileId),'PRODUCT_AUTO_PROFILE');
 const plan=createPlan(parseKml94(input.kml),input),prepared=await prepareSITL(plan,{confirmSyntheticHomeAmsl10});
 const feature=plan.acquisition.feature;
 const body=common(profileId,feature.name,feature.coordinates.map(([lon,lat])=>[lat,lon]),input.home,input.options.altitudeAglM);
 const model=seal({...body,kind:feature.kind==='Polygon'?'polygon':'corridor',input:structuredClone(input),binding:prepared.binding});
 return {model,plan,prepared};
}
export function manualMission(draft,home){
 exact(draft,'revision,kind,name,datum,altitudeDatum,units,geometry,altitudeM,corridorWidthM');
 need(Number.isInteger(draft.revision)&&draft.revision>=0&&draft.revision<=999998,'PRODUCT_DRAFT_REVISION');
 need(['polygon','corridor'].includes(draft.kind)&&draft.datum==='WGS84'&&draft.altitudeDatum==='RELATIVE_HOME'&&draft.units==='m','PRODUCT_MANUAL_DRAFT');
 need(draft.kind!=='polygon'||draft.geometry.length>=3,'PRODUCT_POLYGON_MINIMUM');
 need(finite(draft.corridorWidthM,1,100),'PRODUCT_CORRIDOR_WIDTH');
 const body=common('M1-COCKPIT04-NOMINAL',draft.name,draft.geometry,home,draft.altitudeM);
 // This is the original flight radius, not the much larger draft editing bound.
 for(const [lat,lon]of draft.geometry){const y=(lat-home.lat)*111319,x=(lon-home.lon)*111319*Math.cos(lat*Math.PI/180);need(Math.hypot(x,y)<=10,'PRODUCT_MANUAL_RADIUS_NO_CLAMP');}
 const input=structuredClone(draft);
 return seal({...body,kind:draft.kind,input,binding:{draftSha256:sha(input),profileId:'M1-COCKPIT04-NOMINAL'}});
}
export function verifyMission(model){
 need(model&&typeof model==='object'&&!Array.isArray(model),'PRODUCT_MISSION');
 const{sha256,...body}=model;need(typeof sha256==='string'&&/^[a-f0-9]{64}$/.test(sha256)&&sha(body)===sha256,'PRODUCT_MISSION_SHA');
 need(body.format==='aeris-unified-simulation-mission'&&body.version===1&&body.simulationOnly===true&&body.authorityRestorable===false,'PRODUCT_SIMULATION_SCOPE');
 const profile=PROFILES[body.profileId];need(profile&&body.provider===profile.provider,'PRODUCT_PROFILE_PROVIDER');
 common(body.profileId,body.name,body.geometryWgs84LatLon,body.home,body.altitude.valueM);
 need(body.altitude.datum==='RELATIVE_HOME_ON_EXPLICIT_SYNTHETIC_FLAT','PRODUCT_ALTITUDE_DATUM');
 return profile;
}
export function supports(model,mode){const profile=verifyMission(model);return profile.modes.includes(mode);}
export function requireMode(model,mode){need(supports(model,mode),'PRODUCT_MODE_UNSUPPORTED_FOR_SELECTED_PROFILE');return model;}
export function nativeProjection(model){requireMode(model,'manual');need(model.provider==='NATIVE_MANUAL','PRODUCT_M1_NATIVE_PROJECTION_ONLY');const checked=manualMission(model.input,model.home);need(checked.sha256===model.sha256,'PRODUCT_MANUAL_PROJECTION_MISMATCH');return {missionSHA256:model.sha256,profileId:model.profileId,draft:structuredClone(model.input),authorityRestorable:false};}
export async function verifySemanticMission(model){
 verifyMission(model);const rebuilt=model.provider!=='NATIVE_MANUAL'?(await autoMission(model.input,{confirmSyntheticHomeAmsl10:true,profileId:model.profileId})).model:manualMission(model.input,model.home);
 need(canonical(rebuilt)===canonical(model),'PRODUCT_SEMANTIC_PROJECTION_MISMATCH');return rebuilt;
}
