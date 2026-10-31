import {createHash} from 'node:crypto';
export const clone=x=>structuredClone(x);
export function tagUnavailable(x){if(typeof x==='number'&&!Number.isFinite(x))return {$number:Number.isNaN(x)?'NaN':x>0?'Infinity':'-Infinity'};if(Array.isArray(x))return x.map(tagUnavailable);if(x&&typeof x==='object')return Object.fromEntries(Object.entries(x).map(([k,v])=>[k,tagUnavailable(v)]));return x;}
export function canonical(x){
 if(x===null||typeof x==='boolean'||typeof x==='string')return JSON.stringify(x);
 if(typeof x==='number'&&Number.isFinite(x))return JSON.stringify(x);
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 if(x&&Object.getPrototypeOf(x)===Object.prototype)return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
 throw Error('NON_CANONICAL_VALUE');
}
export const sha=x=>createHash('sha256').update(typeof x==='string'?x:canonical(x)).digest('hex');
export const exact=(x,keys)=>{if(!x||Object.getPrototypeOf(x)!==Object.prototype||Object.keys(x).sort().join('|')!==[...keys].sort().join('|'))throw Error('EXACT_SHAPE_REQUIRED');};
export function deepFreeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(deepFreeze);Object.freeze(x);}return x;}
export const OPERATIONS=deepFreeze({
 capture:{unit:'single-exposure-request',mapped:'capture'},zoomPercent:{unit:'percent_0_100',mapped:'zoom'},
 focusPercent:{unit:'percent_0_100',mapped:'focus'},gimbalAngle:{unit:'degrees_pitch_yaw',mapped:'gimbal'},
 exposureSeconds:{unit:'seconds',mapped:null},iso:{unit:'ISO',mapped:null},apertureFNumber:{unit:'f-number',mapped:null},
 exposureCompensationEV:{unit:'EV',mapped:null},recordVideo:{unit:'boolean',mapped:null},downloadOriginal:{unit:'file-id',mapped:null},lidarStart:{unit:'boolean',mapped:null}
});
export function phaseOneUnknown(){return {format:'aeris-camera-contract65',version:1,kind:'PHASE_ONE_CLIENT_CONFIGURATION',origin:'USER_INTAKE_UNKNOWN',brand:'Phase One',model:null,firmware:null,lens:null,api:null,calibration:null,controls:null,physicalSupport:'NOT_CHECKED'};}
export function mockCamera(kind='PHASE_ONE_SEAM_FIXTURE'){
 return {...phaseOneUnknown(),kind,brand:kind==='PHASE_ONE_SEAM_FIXTURE'?'Phase One':'UNSPECIFIED_FIXTURE_VENDOR',origin:'SYNTHETIC_GENERIC_PROTOCOL_FIXTURE',controls:['capture','zoomPercent','focusPercent','gimbalAngle']};
}
export function validateDescriptor(d){
 exact(d,['format','version','kind','origin','brand','model','firmware','lens','api','calibration','controls','physicalSupport']);
 if(d.format!=='aeris-camera-contract65'||d.version!==1||d.physicalSupport!=='NOT_CHECKED')throw Error('NO_PHYSICAL_SUPPORT_CLAIM');
 if(!['PHASE_ONE_CLIENT_CONFIGURATION','PHASE_ONE_SEAM_FIXTURE','THERMAL_SEAM_FIXTURE','CORONA_SEAM_FIXTURE','LIDAR_UNMAPPED_FIXTURE'].includes(d.kind))throw Error('UNKNOWN_DESCRIPTOR_KIND');
 // These identifiers cannot be supplied as invented observations in this mock-only increment.
 if([d.model,d.firmware,d.lens,d.api,d.calibration].some(x=>x!==null))throw Error('CLIENT_MODEL_API_NOT_OBSERVED');
 if(d.kind==='PHASE_ONE_CLIENT_CONFIGURATION'){
  if(d.origin!=='USER_INTAKE_UNKNOWN'||d.brand!=='Phase One'||d.controls!==null)throw Error('UNKNOWN_PROFILE_CANNOT_GAIN_CAPABILITY');
 }else if(d.origin!=='SYNTHETIC_GENERIC_PROTOCOL_FIXTURE'||!Array.isArray(d.controls)||d.controls.length>4||new Set(d.controls).size!==d.controls.length||d.controls.some(x=>!['capture','zoomPercent','focusPercent','gimbalAngle'].includes(x)))throw Error('BOUNDED_SYNTHETIC_CONTROLS');
 return clone(d);
}
export function validateOperation(d,operation,value){
 validateDescriptor(d);if(!Object.hasOwn(OPERATIONS,operation))throw Error('UNKNOWN_OPERATION');
 if(!d.controls?.includes(operation))throw Error('UNKNOWN_OR_UNSUPPORTED_CAPABILITY');
 if(!OPERATIONS[operation].mapped)throw Error('MAPPING_NOT_IMPLEMENTED');
 if(operation==='capture'&&value!==null)throw Error('SINGLE_CAPTURE_NULL_VALUE');
 if(['zoomPercent','focusPercent'].includes(operation)&&(!Number.isFinite(value)||value<0||value>100))throw Error('PERCENT_RANGE');
 if(operation==='gimbalAngle'){
  exact(value,['pitchDeg','yawDeg']);if(!Number.isFinite(value.pitchDeg)||!Number.isFinite(value.yawDeg)||value.pitchDeg< -90||value.pitchDeg>30||Math.abs(value.yawDeg)>180)throw Error('DEGREE_RANGE');
 }
 return {operation:OPERATIONS[operation].mapped,value:clone(value),unit:OPERATIONS[operation].unit};
}
export function createPhaseOneHardwareAdapter(){throw Error('PHASE_ONE_SDK_API_NOT_IMPLEMENTED');}
export const SCOPE_NOTE='Mock/replay only; exact model/API unknown; no aircraft, camera, exposure, original image, dual radio or cryptographic remote authentication proven.';
