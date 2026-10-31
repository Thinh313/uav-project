/** Original quality thresholds, grouped full-interval original windows. */
const need=(v,m)=>{if(!v)throw Error(m);};const percentile=xs=>[...xs].sort((a,b)=>a-b)[Math.max(0,Math.ceil(xs.length*.95)-1)];
export function qualifySamples({reports,startHostMs,endHostMs}){
 need(Number.isFinite(startHostMs)&&Number.isFinite(endHostMs)&&endHostMs>startHostMs,'AUTO_INTERVAL');
 need(reports.length>=3&&reports.length<=24,'ORIGINAL_WINDOWS3_TO24');
 need(reports.reduce((n,r)=>n+(r.samples?.length??0),0)<=32768,'ORIGINAL_REPORT_AGGREGATE32768');
 const keys=['serverBoot','run','boot','configId','feed','profileId'];
 const all=[];let previousEnd=-Infinity;
 for(const r of reports){
  need(keys.every(k=>typeof r[k]==='string'&&r[k]===reports[0][k]),'MEDIA_IDENTITY');
  need(r.sourceKind==='SYNTHETIC'&&r.actualImages===0&&r.foregroundOnly===true&&r.visualForeground===true&&r.overflow===0&&!r.stopReason,'MEDIA_COVERAGE');
  need(r.durationMs>=30000&&r.durationMs<=60050&&r.sampleCount===r.samples?.length&&r.sampleCount>0,'WINDOW_BOUND');
  need(r.measurementStartBrowserMs>=previousEnd&&r.measurementStartBrowserMs-previousEnd<=250||previousEnd===-Infinity,'WINDOW_GAP_OR_OVERLAP');previousEnd=r.measurementEndBrowserMs;
  for(const s of r.samples){
   need([s.latencyLowerMs,s.latencyUpperMs,s.sourceHostBounds?.lowerMs,s.sourceHostBounds?.upperMs,s.displayBrowserMs,s.frameId].every(Number.isFinite),'UNKNOWN_CLOCK');
   const lower=s.latencyLowerMs+s.sourceHostBounds.upperMs,upper=s.latencyUpperMs+s.sourceHostBounds.lowerMs;
   need(s.displayBrowserMs>=r.measurementStartBrowserMs&&s.displayBrowserMs<=r.measurementEndBrowserMs,'SAMPLE_WINDOW');
   need(lower<=upper&&upper-lower<=20&&s.latencyLowerMs>=0&&s.latencyUpperMs>=s.latencyLowerMs,'CLOCK_BOUNDS');
   need(!all.length||s.frameId>all.at(-1).frameId&&lower>all.at(-1).lower,'FRAME_SEQUENCE');
   all.push({...s,lower,upper});
  }
  for(const k of ['apiFailures','decoderErrors','consumerDrops','timestampMisses','unexpectedFreeze']){
   need(Number.isSafeInteger(r.counters?.[k])&&Number.isSafeInteger(r.counterBaseline?.[k])&&r.counters[k]===r.counterBaseline[k],'COUNTER_DELTA_'+k);
  }
 }
 need(all[0].upper<=startHostMs&&all.at(-1).lower>=endHostMs,'WHOLE_AUTO_NOT_COVERED');
 const enclosing=all.filter(s=>s.upper>=startHostMs-250&&s.lower<=endHostMs+250);
 const inside=all.filter(s=>s.lower>=startHostMs&&s.upper<=endHostMs);
 need(inside.length>0,'NO_AUTO_FRAMES');
 const gaps=enclosing.slice(1).map((s,i)=>s.upper-enclosing[i].lower),maximumConservativeGapMs=Math.max(...gaps);
 const durationMs=endHostMs-startHostMs,fps=inside.length/(durationMs/1000),p95=percentile(inside.map(s=>s.latencyUpperMs));
 const bins=[];for(let t=startHostMs;t+5000<=endHostMs;t+=5000){const count=inside.filter(s=>s.lower>=t&&s.upper<t+5000).length;bins.push({startHostMs:t,seconds:5,frames:count,fps:count/5});}
 const gates={fullInterval:true,fps:fps>=24,everyFull5sBin:bins.length>0&&bins.every(b=>b.fps>=24),latencyP95Upper:p95<=300,maximumGap:maximumConservativeGapMs<=250};
 return{status:Object.values(gates).every(Boolean)?'PASS':'FAIL',gates,startHostMs,endHostMs,durationMs,frames:inside.length,displayedFps:fps,latencyP95UpperMs:p95,maximumConservativeGapMs,bins,terminalPartialBinMs:durationMs%5000,sourceKind:'SYNTHETIC',actualImages:0,physicalLatency:'NOT_MEASURED',method:'RAW_MAVLINK_TO_CALIBRATED_SOURCE_CANVAS_INTERVAL_JOIN'};
}

