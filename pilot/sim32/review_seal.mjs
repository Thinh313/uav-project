// Vehicle terminal observation and complete evidence are distinct facts.
export function sealReview(record,summary,closureError=null){
 const complete=!!summary&&!summary.error&&summary.journal?.sealed===true&&summary.journal.rows===summary.frames&&summary.frames>0&&summary.journal.queueRemaining===0&&/^[a-f0-9]{64}$/.test(summary.rawSha256)&&!closureError;
 return {...record,version:2,recordComplete:record.recordComplete&&complete,receiptSeal:complete?'SEALED_CAPTURE':'INCOMPLETE_CAPTURE',physicsEvidence:summary?{frames:summary.frames,rawSha256:summary.rawSha256,journal:summary.journal,status:summary.status,error:summary.error}:null,closureError,physicalMediaVerified:false,flightExecutionProven:false};
}
