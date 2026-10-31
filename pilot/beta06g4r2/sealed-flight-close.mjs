/** Isolated, unwired post-effect close indexing. No flight, filesystem or network access. */
import{createHash}from'node:crypto';
import{jsonBytes}from'../field02/evidence/schema.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'),runID=v=>typeof v==='string'&&/^s[a-f0-9]{20}$/.test(v),validSHA=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export const LIMITS=Object.freeze({reviewBytes:256*1024,closureBytes:64*1024,indexBytes:8192,reviewFiles:4096});
function parse(bytes,max){if(!Buffer.isBuffer(bytes)||bytes.length<2||bytes.length>max)throw Error('SEALED_FILE_BYTE_BOUND');const x=JSON.parse(bytes.toString('utf8'));if(!x||typeof x!=='object'||Array.isArray(x))throw Error('SEALED_JSON_OBJECT_REQUIRED');return x;}
function inspectSeal({expectedRun,currentRun,reviewBytes,closureBytes,expectedReviewSha256,expectedClosureSha256}){
 if(!runID(expectedRun)||currentRun!==null)throw Error('EXACT_CLOSED_RUN_REQUIRED');
 const review=parse(reviewBytes,LIMITS.reviewBytes),closure=parse(closureBytes,LIMITS.closureBytes);
 if(!validSHA(expectedReviewSha256)||!validSHA(expectedClosureSha256)||sha(reviewBytes)!==expectedReviewSha256||sha(closureBytes)!==expectedClosureSha256)throw Error('EXACT_SEALED_FILE_SHA_REQUIRED');
 // Validate all complete semantic fields with the unchanged strict JSON contract. The only
 // excluded field is explicitly the large path-to-SHA map, retained by the full-review digest.
 const{filesSha256,...semanticReview}=review;jsonBytes(semanticReview);
 if(!review.execution||typeof review.execution!=='object'||Array.isArray(review.execution)||typeof review.execution.complete!=='boolean'||![review.failure,review.writerError].every(v=>v===null||typeof v==='string'&&v.length<=512))throw Error('COMPLETE_JSON_SAFE_EXECUTION_RESULT_REQUIRED');
 if(review.format!=='aeris-field02-flight-review'||review.version!==1||review.mode!=='sitl'||review.run!==expectedRun||review.authorityRestorable!==false||review.actualImages!==0||typeof review.accepted!=='boolean'||typeof review.aborted!=='boolean'||typeof review.closedAt!=='string'||!Number.isFinite(Date.parse(review.closedAt))||!validSHA(review.rawHead)||!Number.isSafeInteger(review.rawRecords)||review.rawRecords<1||!['modelSha256','planSha256','documentSha256','missionSha256'].every(k=>validSHA(review[k])))throw Error('EXACT_SEALED_REVIEW_BINDING_REQUIRED');
 if(!closure||closure.stopped!==true||closure.error!==null||closure.stateRetained!==true||closure.containerRetained!==true||closure.ownedIdentityValidated!==true||!validSHA(closure.containerId))throw Error('EXACT_STOPPED_OWNED_CLOSURE_REQUIRED');
 const fileMap=review.filesSha256;
 if(!fileMap||typeof fileMap!=='object'||Array.isArray(fileMap)||Object.keys(fileMap).length<1||Object.keys(fileMap).length>LIMITS.reviewFiles||fileMap['closure.json']!==sha(closureBytes)||!Object.entries(fileMap).every(([p,h])=>p.length<=512&&!p.startsWith('/')&&!p.split('/').some(s=>!s||s==='.'||s==='..')&&validSHA(h)))throw Error('SEALED_REVIEW_FILE_HASH_BINDING_REQUIRED');
 if(review.accepted&&(review.aborted||review.failure!==null||review.writerError!==null||review.execution?.complete!==true))throw Error('ACCEPTED_REVIEW_CONTRADICTION');
 // Reference the immutable full review; preserve its complete bytes without canonicalizing its large map.
 const reference={format:'aeris-sealed-flight-review-reference',version:1,run:expectedRun,accepted:review.accepted,aborted:review.aborted,closedAt:review.closedAt,modelSha256:review.modelSha256,planSha256:review.planSha256,documentSha256:review.documentSha256,missionSha256:review.missionSha256,rawHead:review.rawHead,rawRecords:review.rawRecords,execution:review.execution,failure:review.failure,writerError:review.writerError,review:{path:'flight/runs/'+expectedRun+'/review.json',bytes:reviewBytes.length,sha256:sha(reviewBytes)},closure:{path:'flight/runs/'+expectedRun+'/closure.json',bytes:closureBytes.length,sha256:sha(closureBytes),containerId:closure.containerId,stopped:true},authorityRestorable:false,actualImages:0,acceptanceBasis:'EXISTING_SEALED_REVIEW_CLAIM_NOT_NEW_CANONICAL_RAW_VERIFICATION'};
 const index={reviewRef:reference,authorityRestored:false};if(jsonBytes(index).length>LIMITS.indexBytes)throw Error('COMPACT_REVIEW_INDEX_BOUND');return index;
}
export function sealedReviewIndex(input){return inspectSeal(input);}
const errorCode=e=>String(e?.message??e).slice(0,160);
/** Call only after flight.close sealed the effect. A later store failure cannot mean effect rejection.
 * append performs exactly one index write; it must never actuate or retry. This module does not
 * certify raw flight acceptance, repair historical WAL or permit another campaign request.
 */
export async function indexCompletedFlightClose({append,...input}={}){
 const base={format:'aeris-flight-close-index-outcome',version:1,run:runID(input.expectedRun)?input.expectedRun:null,effectStatus:'CLOSE_ALREADY_RETURNED',authorityRestorable:false,automaticRetry:false,campaignContinuationAllowed:false};
 let index;
 try{index=inspectSeal(input);}catch(e){return{...base,status:'CLOSE_RETURNED_REVIEW_UNVERIFIED',reviewIndexStatus:'NOT_ATTEMPTED',error:errorCode(e),reviewRef:null};}
 const completed={...base,effectStatus:'SEALED_OWNED_CLOSED',reviewRef:index.reviewRef};
 try{
  if(typeof append!=='function')throw Error('REVIEW_INDEX_WRITER_REQUIRED');
  const receipt=await append('FLIGHT_REVIEW_SEALED_REF',index);
  if(!Number.isSafeInteger(receipt?.seq)||receipt.seq<1||!validSHA(receipt?.hash))throw Error('REVIEW_INDEX_DURABLE_RECEIPT_UNKNOWN');
  return{...completed,status:'CLOSED_REVIEW_INDEXED',reviewIndexStatus:'INDEXED',receipt:{seq:receipt.seq,hash:receipt.hash},error:null};
 }catch(e){return{...completed,status:'CLOSED_REVIEW_INDEX_PENDING',reviewIndexStatus:'FAILED_OR_UNKNOWN',receipt:null,error:errorCode(e)};}
}
