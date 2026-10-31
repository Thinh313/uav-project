import fs from'node:fs';import{createHash}from'node:crypto';
import{analyzePackage,POLICY}from'../coach01/core.mjs';import{verifyPackage as manualVerify}from'../coach02/journal.mjs';import{CONTRACT}from'../coach02/contract.mjs';
export const hash=b=>createHash('sha256').update(b).digest('hex');
export const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
export const FORMAT='AERIS_BETAOPS01_V1';
export function entryFingerprint(){return hash(['../coach01/core.mjs','../betaworkbench05/package.mjs','../betaworkbench05/auto-video.mjs','../coach02/contract.mjs','../coach02/engine.mjs','../coach02/journal.mjs','./verify.mjs'].map(n=>n+':'+hash(fs.readFileSync(new URL(n,import.meta.url)))).join('\n'));}
export async function verify(bytes){
 bytes=Buffer.from(bytes);if(bytes.length>32*2**20)throw Error('PACKAGE32MIB');const b=JSON.parse(bytes);let result;
 if(b?.format==='aeris-beta05-diagnostic-package'){
  const r=await analyzePackage(bytes);if(typeof r.sourceAccepted!=='boolean')throw Error('SOURCE_REVIEW_BOOLEAN');result={kind:'AUTO_REPLAY',run:r.run,name:r.plan.name,source:r.source,integrity:'RAW_MODEL_RECOMPUTED',outcome:r.sourceAccepted?'SOURCE_REVIEW_ACCEPTED':'SOURCE_REVIEW_INCOMPLETE',reason:r.sourceReason,policy:POLICY.id,rawRecords:r.rawRecords,actualImages:0,syntheticImages:r.inspection.syntheticImages,video:r.verification.video?.status??'NOT_PRESENT',warnings:r.telemetry.warnings,reportSha256:r.sha256};
 }else if(b?.format==='aeris-manual02-package'){
  const r=manualVerify(bytes),v=r.review;result={kind:'MANUAL_REFERENCE',run:r.sessionId,name:v.exercise.name,source:v.context.sourceKind,integrity:'RAW_MODEL_RECOMPUTED',outcome:v.verdict,reason:v.clockFailures.join(', ')||null,policy:CONTRACT.id,rawRecords:b.rows.length,actualImages:0,syntheticImages:0,video:'NOT_APPLICABLE',warnings:v.limits,reportSha256:hash(canonical(v))};
 }else throw Error('UNSUPPORTED_PACKAGE_FORMAT');
 return{format:FORMAT,...result,sourceSha256:hash(bytes),sourceBytes:bytes.length,entrypointsFingerprint:entryFingerprint(),fingerprintScope:'SEVEN_VERIFIER_ENTRYPOINTS_NOT_COMPLETE_SUPPLY_CHAIN',sourceAuthenticated:false,authorityRestorable:false,operational:false,visualAcceptance:'NOT_CHECKED'};
}
