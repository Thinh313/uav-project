/** Consume only copies already accepted by the unchanged UI observation validator. */
import fs from 'node:fs/promises';import path from 'node:path';import{createHash}from'node:crypto';
import{createUiTimingRecorder}from'../stability16/ui-timing.mjs';
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
export function createUiTimingHook(){
 const recorder=createUiTimingRecorder();let failure=null,closed=false,consumed=0,unmatchedServerEntries=0,missingLifecycleCopies=0,lastObservation=null;
 const healthy=()=>{if(closed)throw Error('UI_TIMING_HOOK_CLOSED');if(failure)throw Error('UI_TIMING_DIAGNOSTIC_FAILED:'+failure);};
 return{
  consume(view,server){healthy();try{const q=view?.observation;if(!q||!Number.isFinite(view.ageMs)||view.ageMs<0||!Array.isArray(server?.entries)||server.entries.length>32)throw Error('VALIDATED_UI_COPY_REQUIRED');
   lastObservation={uiDocumentId:q.documentId,ageAtConsumeMs:view.ageMs,statusAtConsume:view.ageMs<=1200?'WITHIN_EXISTING_AGE_BOUND_ONLY':'STALE_EXISTING_BOUND',clockDomain:'NODE_CHALLENGE_AGE_MS_AT_CONSUME_NOT_CURRENT_FRESHNESS',diagnosticOnly:true};const entries=server.entries.filter(r=>r?.clockDomain==='NODE_HRTIME_MS'&&r.correlation?.status==='MATCHED_DIAGNOSTIC_ONLY'&&UUID.test(r.correlation.documentId)&&Number.isSafeInteger(r.correlation.requestId)&&r.correlation.requestId>=1&&r.correlation.requestId<=20000&&['activate','heartbeat','background','stop'].includes(r.action));unmatchedServerEntries=server.entries.length-entries.length;
   if(q.lifecycleDiagnostics===null){missingLifecycleCopies++;consumed++;return{diagnosticOnly:true,status:'NO_LIFECYCLE_COPY',unmatchedServerEntries};}
   const result=recorder.ingest({uiDocumentId:q.documentId,life:q.lifecycleDiagnostics,observationAgeMs:view.ageMs,serverEntries:entries});consumed++;return{diagnosticOnly:true,status:'COPIED_VALIDATED_OBSERVATION',unmatchedServerEntries,requests:result.requests.length};
  }catch(error){failure=String(error.message).slice(0,160);throw Error('UI_TIMING_DIAGNOSTIC_FAILED:'+failure);}},
  assertHealthy:healthy,
  view(){return{diagnosticOnly:true,authorityEvidence:false,consumed,missingLifecycleCopies,lastObservation:lastObservation?{...lastObservation}:null,unmatchedServerEntries,unknownServerCorrelation:unmatchedServerEntries>0,failed:failure!==null,error:failure,closed};},
  async persist(out){if(closed)throw Error('UI_TIMING_CLOSURE_ALREADY_WRITTEN');closed=true;recorder.close();const snapshot=recorder.snapshot(),bytes=Buffer.from(JSON.stringify(snapshot)+'\n');if(bytes.length>32768)throw Error('UI_TIMING_CLOSURE32KIB');const name='ui-timing-closure.json',fd=await fs.open(path.join(out,name),'wx',0o600);try{await fd.writeFile(bytes);await fd.sync();}finally{await fd.close();}const dir=await fs.open(out,'r');try{await dir.sync();}finally{await dir.close();}return{...this.view(),path:name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),status:failure?'DIAGNOSTIC_FAILED':'DIAGNOSTIC_SNAPSHOT_ONLY_NO_AUTHORITY'};}
 };
}
