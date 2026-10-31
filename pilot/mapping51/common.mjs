import {createHash} from 'node:crypto';
export const stable=x=>JSON.stringify(sort(x));
function sort(x){if(Array.isArray(x))return x.map(sort);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])]));if(typeof x==='number'&&!Number.isFinite(x))throw Error('NONFINITE');return x;}
export const sha=x=>createHash('sha256').update(typeof x==='string'?x:stable(x)).digest('hex');
export const clone=x=>structuredClone(x);
export function exact(x,keys,name){if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).sort().join(',')!==keys.split(',').sort().join(','))throw Error(name+'_SCHEMA');return x;}
export function num(x,lo,hi,n){if(typeof x!=='number'||!Number.isFinite(x)||x<lo||x>hi)throw Error(n+'_RANGE');return x;}
export function text(x,n,max=100){if(typeof x!=='string'||!x.trim()||x.length>max)throw Error(n+'_TEXT');return x;}
export const seal=x=>({...x,sha256:sha(x)});
export function unseal(x){const {sha256,...body}=x;if(sha(body)!==sha256)throw Error('DIGEST_MISMATCH');return body;}
export const POLICY=Object.freeze({id:'mapping51-engineering-mock',version:1,maxAgeMs:10000,maxCorrectionAgeMs:2000,maxGsdCm:3,maxTranslationBlurPx:.7,maxReadoutDisplacementPx:2,minFrontOverlap:80,minSideOverlap:70,maxTiltDeg:3,maxAngularRateDegS:2,minimumReserveBytes:10485760});
export const CAMERA=Object.freeze({profileVersion:1,iso:200,apertureF:5.6,id:'mock-rgb-01',lensId:'mock-prime35',calibrationId:'SYNTHETIC-CAL-01',sensorWidthMm:36,sensorHeightMm:24,imageWidthPx:6000,imageHeightPx:4000,focalLengthMm:35,minIntervalS:.6,shutterKind:'GLOBAL',readoutS:0,exposureS:.001,focusMode:'LOCKED_FOR_STRIP',provenance:'SYNTHETIC_FIXTURE'});
export const OPTIONS=Object.freeze({altitudeAglM:60,speedMS:4,frontOverlapPct:80,sideOverlapPct:75,headingDeg:0,corridorWidthM:100,positioning:'RTK',baseId:'mock-base-01',reference:'MOCK-WGS84-ELLIPSOID',terrain:'SYNTHETIC_FLAT',datumAcknowledged:false});
