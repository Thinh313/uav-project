/** Isolated diagnostic consumer. No timers, I/O, UI writes, authority or recovery. */
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const ACTIONS=new Set(['bootstrap','activate','heartbeat','background','stop']);
const finite=(v,name)=>{if(typeof v!=='number'||!Number.isFinite(v)||v<0)throw Error('UI_TIMING_FINITE_'+name);return v;};
const integer=(v,name)=>{if(!Number.isSafeInteger(v)||v<1)throw Error('UI_TIMING_INTEGER_'+name);return v;};
const requireValue=(v,name)=>{if(!v)throw Error('UI_TIMING_'+name);};
const bounded=(v,n,name)=>{requireValue(new TextEncoder().encode(JSON.stringify(v)).byteLength<=n,name);};
const span=(a,b)=>{if(a===null||b===null)return null;requireValue(b>=a,'LOCAL_TIME_ORDER');return b-a;};
const present=(v,name)=>v===undefined?null:finite(v,name);
export const UI_TIMING_LIMITS=Object.freeze({inputBytes:65536,outputBytes:32768,events:32,serverEntries:32,retainedRequests:32,observationMs:1200,requestMs:1000,heartbeatMs:750,hostTtlMs:3000});
export function analyzeUiTiming({uiDocumentId,life,observationAgeMs,serverEntries=[]}){
 requireValue(UUID.test(uiDocumentId),'UI_DOCUMENT_UUID');bounded({life,serverEntries},UI_TIMING_LIMITS.inputBytes,'INPUT_BYTES');
 requireValue(life?.format==='aeris-beta06g2-lifecycle-diagnostic/1'&&Array.isArray(life.events)&&life.events.length<=32,'BOUNDED_EXISTING_LIFECYCLE');
 requireValue(Array.isArray(serverEntries)&&serverEntries.length<=32,'SERVER_ENTRIES');finite(observationAgeMs,'OBSERVATION_AGE');
 const rows=[],map=new Map(),stages=new Map();let previousSeq=0,previousAt=0,lastQueue=null,lastTick=null,documentId=null,unattributedRequestEvents=0;
 for(const event of life.events){
  integer(event.seq,'EVENT_SEQ');finite(event.atBrowserMs,'BROWSER_AT');requireValue(event.seq>previousSeq&&event.atBrowserMs>=previousAt,'EVENT_ORDER');previousSeq=event.seq;previousAt=event.atBrowserMs;
  if(event.kind==='HEARTBEAT_TICK')lastTick={at:event.atBrowserMs,lag:finite(event.lagMs,'TIMER_LAG')};
  if(event.kind==='QUEUE_BEGIN')lastQueue={action:event.action,seq:event.seq,wait:finite(event.waitMs,'QUEUE_WAIT')};
  if(event.kind==='REQUEST_BEGIN'){
   integer(event.requestId,'REQUEST_ID');requireValue(ACTIONS.has(event.action),'ACTION');requireValue(event.deadlineMs===1000,'UNCHANGED_DEADLINE');requireValue(!map.has(event.requestId),'DUPLICATE_REQUEST_BEGIN');
   const match=/^CORRELATION_DOCUMENT:(.+)$/.exec(event.reason??'');const doc=match?.[1];requireValue(UUID.test(doc??''),'LIFECYCLE_DOCUMENT_UUID');requireValue(documentId===null||documentId===doc,'MIXED_LIFECYCLE_DOCUMENTS');documentId=doc;
   const row={uiDocumentId,lifecycleDocumentId:doc,requestId:event.requestId,action:event.action,browser:{clockDomain:'BROWSER_PERFORMANCE_NOW_MS',startedMs:event.atBrowserMs,queueWaitMs:lastQueue?.action===event.action&&lastQueue.seq===event.seq-1?lastQueue.wait:null,precedingTimerLagMs:lastTick?.at<=event.atBrowserMs?lastTick.lag:null,sendElapsedMs:null,headersElapsedMs:null,bodyElapsedMs:null,totalElapsedMs:null,sendToHeadersMs:null,headersToBodyMs:null,terminal:'PENDING',failure:null,afterTerminalStages:[]},server:null,correlation:'NO_MATCHED_SERVER_PHASES',authorityEvidence:false};rows.push(row);map.set(event.requestId,row);stages.set(event.requestId,{lastElapsed:0,seen:new Set()});
  }
  const row=map.get(event.requestId);if(event.kind==='REQUEST_BEGIN')continue;if(!row){if(event.requestId!==undefined)unattributedRequestEvents++;continue;}
  requireValue(event.action===row.action,'REQUEST_ACTION_MATCH');const elapsed=present(event.elapsedMs,'ELAPSED');
  if(['HTTP_SEND','HTTP_HEADERS','HTTP_BODY_COMPLETE'].includes(event.kind)){
   const stage=stages.get(event.requestId);requireValue(elapsed!==null&&!stage.seen.has(event.kind)&&elapsed>=stage.lastElapsed,'HTTP_STAGE_ORDER_OR_DUPLICATE');
   if(event.kind==='HTTP_HEADERS')requireValue(stage.seen.has('HTTP_SEND'),'HEADERS_REQUIRE_SEND');
   if(event.kind==='HTTP_BODY_COMPLETE')requireValue(stage.seen.has('HTTP_HEADERS'),'BODY_REQUIRES_HEADERS');
   requireValue(row.browser.terminal!=='ACK','HTTP_AFTER_ACK');stage.seen.add(event.kind);stage.lastElapsed=elapsed;
   if(row.browser.terminal==='FAILED'){requireValue(elapsed>=row.browser.totalElapsedMs,'LATE_STAGE_TIME');row.browser.afterTerminalStages.push({stage:event.kind,elapsedMs:elapsed});}
   else if(event.kind==='HTTP_SEND')row.browser.sendElapsedMs=elapsed;
   else if(event.kind==='HTTP_HEADERS')row.browser.headersElapsedMs=elapsed;
   else row.browser.bodyElapsedMs=elapsed;
  }
  if(event.kind==='REQUEST_ACK'||event.kind==='REQUEST_FAILED'){
   requireValue(row.browser.terminal==='PENDING','DUPLICATE_TERMINAL');requireValue(elapsed!==null,'TERMINAL_ELAPSED');
   requireValue(elapsed>=stages.get(event.requestId).lastElapsed,'TERMINAL_BEFORE_HTTP_STAGE');
   if(event.kind==='REQUEST_ACK'){requireValue(elapsed<1000,'LATE_ACK_NOT_VALID_DIAGNOSTIC');requireValue(row.action==='bootstrap'||row.browser.bodyElapsedMs!==null,'ACK_REQUIRES_BODY');}
   row.browser.totalElapsedMs=elapsed;row.browser.terminal=event.kind==='REQUEST_ACK'?'ACK':'FAILED';
   if(event.kind==='REQUEST_FAILED')row.browser.failure=/^[A-Z][A-Z0-9_:.-]{0,95}$/.test(event.reason??'')?event.reason:'UNCLASSIFIED_FAILURE';
  }
 }
 const seen=new Set();
 for(const server of serverEntries){
  requireValue(server?.clockDomain==='NODE_HRTIME_MS','SERVER_CLOCK_DOMAIN');const c=server.correlation;
  requireValue(c?.status==='MATCHED_DIAGNOSTIC_ONLY'&&UUID.test(c.documentId)&&ACTIONS.has(server.action),'SERVER_CORRELATION_SHAPE');integer(c.requestId,'SERVER_REQUEST');
  const key=c.documentId+':'+c.requestId+':'+server.action;requireValue(!seen.has(key),'DUPLICATE_SERVER_IDENTITY');seen.add(key);
  const times=server.times;requireValue(times&&typeof times==='object','SERVER_TIMES');const names=['ingress','body','action','payload','journalBegin','journalSynced','responseEndReturned'];let last=0;const t={};
  for(const name of names){t[name]=present(times[name],name);if(t[name]!==null){requireValue(t[name]>=last,'SERVER_TIME_ORDER');last=t[name];}}
  const row=rows.find(r=>r.lifecycleDocumentId===c.documentId&&r.requestId===c.requestId&&r.action===server.action);if(!row)continue;
  row.correlation='MATCHED_DOCUMENT_REQUEST_ACTION_DIAGNOSTIC_ONLY';row.server={clockDomain:'NODE_HRTIME_MS',ingressToBodyMs:span(t.ingress,t.body),bodyToActionMs:span(t.body,t.action),actionToPayloadMs:span(t.action,t.payload),journalAwaitMs:span(t.journalBegin,t.journalSynced),journalToResponseEndMs:span(t.journalSynced,t.responseEndReturned),ingressToResponseEndMs:span(t.ingress,t.responseEndReturned),clientDeliveryProven:false};
 }
 for(const row of rows){row.browser.sendToHeadersMs=span(row.browser.sendElapsedMs,row.browser.headersElapsedMs);row.browser.headersToBodyMs=span(row.browser.headersElapsedMs,row.browser.bodyElapsedMs);}
 const result={format:'aeris-stability16-ui-timing/1',diagnosticOnly:true,authorityEvidence:false,uiDocumentId,observation:{ageMs:observationAgeMs,thresholdMs:1200,status:observationAgeMs<=1200?'WITHIN_EXISTING_AGE_BOUND_ONLY':'STALE_EXISTING_BOUND'},requests:rows,unattributedRequestEvents,unattributedReason:unattributedRequestEvents?'MISSING_REQUEST_BEGIN_IN_BOUNDED_RING':null,crossClockLatency:null,crossClockReason:'UNMAPPED_DOMAINS_NO_ABSOLUTE_SUBTRACTION_OR_UNATTRIBUTED_NETWORK_ESTIMATE'};bounded(result,32768,'OUTPUT_BYTES');return result;
}
export function createUiTimingRecorder(){
 const retained=new Map();let closed=false;
 return Object.freeze({
  ingest(input){requireValue(!closed,'RECORDER_CLOSED');const result=analyzeUiTiming(input);
   for(const row of result.requests){const key=row.lifecycleDocumentId+':'+row.requestId+':'+row.action;const prior=retained.get(key);
    if(prior)requireValue(prior.browser.startedMs===row.browser.startedMs&&prior.uiDocumentId===row.uiDocumentId,'CROSS_SNAPSHOT_IDENTITY_CONFLICT');
    if(prior?.browser.terminal==='FAILED')requireValue(row.browser.terminal!=='ACK','LATE_ACK_CANNOT_REPLACE_FAILURE');
    if(prior?.browser.terminal==='FAILED'&&row.browser.terminal==='PENDING')continue;
    retained.delete(key);retained.set(key,structuredClone(row));while(retained.size>32)retained.delete(retained.keys().next().value);
   }
   return result;
  },
  snapshot(){const result={format:'aeris-stability16-ui-retained/1',closed,maximumRequests:32,retention:'BOUNDED_LAST32_REQUESTS_INCLUDING_TERMINALS_NOT_AUDIT_LOG',requests:[...retained.values()].map(row=>structuredClone(row)),diagnosticOnly:true,authorityEvidence:false};bounded(result,32768,'RETAINED_BYTES');return result;},
  close(){closed=true;return {closed:true,authorityEvidence:false};}
 });
}
