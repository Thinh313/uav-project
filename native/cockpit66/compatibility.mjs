/** Comparison only; never changes control computations, bytes, times, grants or stored hashes. */
import {sha} from './portable/cyber65/contracts.mjs';
export function validateReferences(refs,corpus){const ids=corpus.body.cases.map(s=>s.id);if(refs.corpusSha256!==corpus.sha256||ids.some(id=>!/^[a-f0-9]{64}$/.test(refs.references?.[id]))||Object.keys(refs.references??{}).some(id=>!ids.includes(id))||Object.entries(refs.diagnosticBodies??{}).some(([id,body])=>!ids.includes(id)||sha(body)!==refs.references[id]))throw Error('REFERENCE_CORPUS_OR_BODY_SHA');return true;}
export const INTERPRETED_ANGLE_ROUNDOFF_RAD=1e-12;
export function differences(expected,actual,path=''){
 if(Object.is(expected,actual))return[];
 if(expected&&actual&&typeof expected==='object'&&typeof actual==='object'&&Array.isArray(expected)===Array.isArray(actual)){
  const result=[];for(const key of new Set([...Object.keys(expected),...Object.keys(actual)]))result.push(...differences(expected[key],actual[key],path?path+'.'+key:key));return result;
 }
 return[{path,expected:expected??null,actual:actual??null,...typeof expected==='number'&&typeof actual==='number'?{absoluteDifference:Math.abs(expected-actual)}:{}}];
}
export function compareReview(expected,actual){
 const diff=differences(expected,actual),allowed=diff.length>0&&diff.every(d=>/^transport\.protocol\.gimbals\.\d+\.attitude\.(pitchRad|yawRad)$/.test(d.path)&&typeof d.expected==='number'&&typeof d.actual==='number'&&Number.isFinite(d.expected)&&Number.isFinite(d.actual)&&d.absoluteDifference<=INTERPRETED_ANGLE_ROUNDOFF_RAD);
 return{status:diff.length===0?'EXACT':allowed?'COMPATIBLE_INTERPRETED_ANGLE_ROUNDOFF':'MISMATCH',accepted:diff.length===0||allowed,differences:diff,scope:'Only interpreted attitude comparison; no hash rewrite or physical accuracy qualification'};
}
