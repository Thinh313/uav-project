/** G5 bounded sealed file reader, R2 index integration, and verified history projection. */
import fs from'node:fs';import path from'node:path';import{createHash}from'node:crypto';
import{indexCompletedFlightClose,sealedReviewIndex,LIMITS}from'../beta06g4r2/sealed-flight-close.mjs';
import{stable}from'../auto63/compiler.mjs';import{jsonBytes}from'../field02/evidence/schema.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'),validRun=r=>/^s[a-f0-9]{20}$/.test(r??'');
function boundedFile(p,max){
 let current=path.parse(path.resolve(p)).root;for(const part of path.resolve(p).slice(current.length).split('/').filter(Boolean).slice(0,-1)){current=path.join(current,part);const s=fs.lstatSync(current);if(!s.isDirectory()||s.isSymbolicLink())throw Error('SEALED_PARENT_NOT_REGULAR_DIRECTORY');}
 const fd=fs.openSync(p,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);if(!s.isFile()||s.size<2||s.size>max)throw Error('SEALED_FILE_BOUND');const b=fs.readFileSync(fd);if(b.length!==s.size||fs.fstatSync(fd).size!==s.size)throw Error('SEALED_FILE_CHANGED');return b;}finally{fs.closeSync(fd);}
}
function sealedInput(root,run,currentRun){if(!validRun(run)||!path.isAbsolute(root))throw Error('EXACT_OWNED_SEALED_RUN_REQUIRED');const reviewBytes=boundedFile(path.join(root,'runs',run,'review.json'),LIMITS.reviewBytes),closureBytes=boundedFile(path.join(root,'runs',run,'closure.json'),LIMITS.closureBytes);return{expectedRun:run,currentRun,reviewBytes,closureBytes,expectedReviewSha256:sha(reviewBytes),expectedClosureSha256:sha(closureBytes)};}
const unverified=(run,error)=>({format:'aeris-flight-close-index-outcome',version:1,run:validRun(run)?run:null,status:'CLOSE_RETURNED_REVIEW_UNVERIFIED',effectStatus:'CLOSE_ALREADY_RETURNED',reviewIndexStatus:'NOT_ATTEMPTED',error:String(error).slice(0,160),reviewRef:null,automaticRetry:false,campaignContinuationAllowed:false,authorityRestorable:false});
export async function archiveCompletedClose({root,run,currentRun,result,append}){
 let input,outcome;
 try{input=sealedInput(root,run,currentRun);if(stable(result)+'\n'!==input.reviewBytes.toString())throw Error('RETURNED_REVIEW_EXACT_SEALED_BYTES_REQUIRED');outcome=await indexCompletedFlightClose({...input,append});}catch(e){outcome=unverified(run,e.message);}
 return outcome.reviewRef?{...result,closeIndex:outcome}:{format:'aeris-flight-close-unverified-result',run:outcome.run,authorityRestorable:false,actualImages:0,closeIndex:outcome};
}
export function reviewHistory(records,root){return records.filter(r=>['FLIGHT_REVIEW','FLIGHT_REVIEW_SEALED_REF'].includes(r.kind)).map(row=>{
 if(row.kind==='FLIGHT_REVIEW')return{...row.data.review,indexProvenance:'INHERITED_FULL_REVIEW_NOT_G5_EXECUTION'};
 const ref=row.data.reviewRef;if(row.data.authorityRestored!==false||!ref)throw Error('SEALED_INDEX_RECORD_SCHEMA');const input=sealedInput(root,ref.run,null),expected=sealedReviewIndex(input);if(!jsonBytes(expected).equals(jsonBytes(row.data)))throw Error('SEALED_INDEX_REFERENCE_DRIFT');
 return{...ref,format:'aeris-field02-flight-review',mode:'sitl',reviewStorage:'VERIFIED_SEALED_REFERENCE',indexProvenance:{seq:row.seq,hash:row.hash},authorityRestorable:false,rawAcceptanceRecomputed:false};
});}
export function persistCloseOutcome(out,result){const p=path.join(out,'close-index-'+result.closeIndex.run+'.json'),fd=fs.openSync(p,'wx',0o600);try{fs.writeFileSync(fd,jsonBytes(result.closeIndex));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}const d=fs.openSync(out,'r');try{fs.fsyncSync(d);}finally{fs.closeSync(d);}}
