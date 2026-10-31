/** Proposal/helper only: never imported by pinned runtime04.
 * Required prefix is fixed before flush; live producer may continue afterwards. */
export const SCOPE='DURABLE_REQUIRED_PREFIX_ONLY_LIVE_PRODUCER_CONTINUES';
const natural=x=>Number.isSafeInteger(x)&&x>=0;
const require=(q,m)=>{if(!q)throw Error(m)};
export async function prefixBarrier({traceId,configId,serverBoot,snapshot,flush,persist}){
 const entry=snapshot(),requiredThrough=entry.accepted;
 require(natural(requiredThrough)&&natural(entry.acknowledged)&&entry.acknowledged<=requiredThrough&&!entry.fatal,'TRACE_PREFIX_ENTRY');
 let previous=entry.acknowledged,attempts=0;
 while(snapshot().acknowledged<requiredThrough){
  require(++attempts<=9,'TRACE_PREFIX_FLUSH_BOUND');await flush();
  const live=snapshot();require(!live.fatal&&natural(live.acknowledged)&&live.acknowledged>previous,'TRACE_PREFIX_FLUSH_NO_PROGRESS');previous=live.acknowledged;
 }
 const reply=await persist({traceId,configId,serverBoot,requiredThrough});
 const live=snapshot();require(!live.fatal,'TRACE_PREFIX_FATAL');
 require(reply.traceId===traceId&&reply.configId===configId&&reply.serverBoot===serverBoot&&reply.requiredThrough===requiredThrough&&natural(reply.ackThrough)&&reply.ackThrough>=requiredThrough,'TRACE_PREFIX_ACK');
 const d=reply.durable;
 require(d&&d.complete===true&&d.fatal===null&&natural(d.hostThrough)&&/^[a-f0-9]{64}$/.test(d.hostHead)&&/^[a-f0-9]{64}$/.test(d.receiptSha256),'TRACE_PREFIX_DURABILITY');
 return{format:'aeris-betastability02-trace-prefix',version:1,traceId,configId,serverBoot,requiredThrough,ackThrough:reply.ackThrough,durable:{...d},currentLiveAccepted:live.accepted,currentLiveAcknowledged:live.acknowledged,currentLivePending:live.pending,fatal:live.fatal,scope:SCOPE};
}
export function verifyPrefix(fence,{configId,serverBoot,rows,selectedViewerRows}){
 require(fence?.format==='aeris-betastability02-trace-prefix'&&fence.version===1&&fence.scope===SCOPE,'REPORT_TRACE_PREFIX_REQUIRED');
 require(fence.configId===configId&&fence.serverBoot===serverBoot&&typeof fence.traceId==='string'&&natural(fence.requiredThrough)&&fence.requiredThrough>0&&natural(fence.ackThrough)&&fence.ackThrough>=fence.requiredThrough&&fence.fatal===null,'REPORT_TRACE_PREFIX_FENCE');
 require(natural(fence.currentLivePending)&&natural(fence.currentLiveAccepted)&&natural(fence.currentLiveAcknowledged)&&fence.currentLiveAccepted>=fence.currentLiveAcknowledged&&fence.currentLivePending===fence.currentLiveAccepted-fence.currentLiveAcknowledged,'REPORT_TRACE_LIVE_COUNTERS');
 const producer=rows.filter(r=>r.data?.externalTraceId===fence.traceId);require(producer.length>0,'REPORT_TRACE_PRODUCER_MISSING');
 let prior=null;for(const row of producer){require(natural(row.data.externalSeq)&&row.data.externalSeq>0&&(prior===null||row.data.externalSeq===prior+1),'REPORT_TRACE_PRODUCER_SEQUENCE_GAP');prior=row.data.externalSeq;}
 require(producer.some(r=>r.data.externalSeq===fence.requiredThrough),'REPORT_TRACE_REQUIRED_SEQUENCE_MISSING');
 const d=fence.durable;require(d?.complete===true&&d.fatal===null&&natural(d.hostThrough)&&/^[a-f0-9]{64}$/.test(d.hostHead)&&/^[a-f0-9]{64}$/.test(d.receiptSha256),'REPORT_TRACE_PREFIX_DURABILITY');
 const anchor=rows.find(r=>r.seq===d.hostThrough);require(anchor&&anchor.sha256===d.hostHead,'REPORT_TRACE_DURABLE_PREFIX_NOT_IN_RANGE');
 for(const row of selectedViewerRows){require(row.kind==='VIEWER_FRAME'&&row.data.externalTraceId===fence.traceId&&natural(row.data.externalSeq)&&row.data.externalSeq>0&&row.data.externalSeq<=fence.requiredThrough,'REPORT_SAMPLE_OUTSIDE_TRACE_PREFIX');require(row.seq<=d.hostThrough,'REPORT_SAMPLE_AFTER_DURABLE_PREFIX');}
 return{requiredThrough:fence.requiredThrough,ackThrough:fence.ackThrough,livePending:fence.currentLivePending,status:'PASS',scope:SCOPE};
}
