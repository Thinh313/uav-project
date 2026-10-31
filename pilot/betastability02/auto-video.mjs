import {Decoder} from '../../services/mavlink.mjs';
import {replay} from '../auto63/journal-v3.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const need=(v,m)=>{if(!v)throw Error(m);};
const hash=b=>createHash('sha256').update(b).digest('hex');
const percentile=xs=>[...xs].sort((a,b)=>a-b)[Math.max(0,Math.ceil(xs.length*.95)-1)];

/** Conservative interval join, independent of UI completion and aggregate FPS labels. */
export function qualifySamples({reports,startHostMs,endHostMs}){
 need(Number.isFinite(startHostMs)&&Number.isFinite(endHostMs)&&endHostMs>startHostMs,'AUTO_INTERVAL');
 need(reports.length===6,'SIX_RAW_WINDOWS');
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

export function flightInterval(rawPath,review){
 return flightIntervalRows(replay(rawPath),review);
}

export function flightIntervalRows(raw,review){
 need(raw.head===review.rawHead&&raw.rows.length===review.rawRecords&&review.source==='OBSERVED_OWNED_SITL'&&review.accepted===true,'CLOSED_ACTUAL_REVIEW');
 let start=null,end=null,sawAirborne=false,sawAuto=false,landed=null,armed=null,autoCommand=null;const rx=new Decoder(),tx=new Decoder();
 for(const r of raw.rows){const t=Number(BigInt(r.hostNs))/1e6;
  if(r.kind==='TX_RAW')for(const m of tx.push(Buffer.from(r.data.rawHex,'hex')))if(m.id===76&&m.fields.command===176&&m.fields.param2===3){autoCommand??=t;start??=t;}
  if(r.kind!=='RX_RAW'||start===null)continue;
  for(const m of rx.push(Buffer.from(r.data.rawHex,'hex'))){if(m.system!==42||m.component!==1)continue;
   if(m.id===0){armed=!!(m.fields.base_mode&128);if(armed&&m.fields.custom_mode===3)sawAuto=true;}
   if(m.id===33&&m.fields.relative_alt>2000)sawAirborne=true;
   if(m.id===245)landed=m.fields.landed_state;
   if(sawAuto&&sawAirborne&&landed===1&&armed===false&&end===null)end=t;
  }
 }
 need(autoCommand!==null&&sawAuto&&sawAirborne&&end!==null,'OBSERVED_AUTO_AIRBORNE_LANDED_DISARM_REQUIRED');
 return{startHostMs:start,endHostMs:end,rawHead:raw.head,rawRecords:raw.rows.length,startRule:'FIRST_AUTO_COMMAND_WIRE_BEFORE_ARMED_AUTO_HEARTBEAT',endRule:'FIRST_OBSERVED_LANDED_AND_DISARMED_AFTER_AIRBORNE'};
}

export function qualifyRun(hostRoot,review){
 const inputFiles={},read=p=>{const b=fs.readFileSync(p);inputFiles[path.relative(hostRoot,p)]={bytes:b.length,sha256:hash(b)};return JSON.parse(b);};
 const rows=[];
 for(const n of fs.readdirSync(hostRoot).filter(n=>/^binding-report-(?:0[1-9]|[1-3][0-9]|4[0-8])\.json$/.test(n)).sort()){
  const sidecar=read(path.join(hostRoot,n));if(sidecar.flight.run!==review.run)continue;
  need(sidecar.flight.boot===review.boot&&sidecar.flight.modelSha256===review.modelSha256&&sidecar.flight.planSha256===review.planSha256,'FLIGHT_BINDING');
  const p=path.join(hostRoot,'media',sidecar.rawReport.file);need(hash(fs.readFileSync(p))===sidecar.rawReport.sha256,'REPORT_SHA');rows.push(read(p));
 }
 const rawPath=path.join(hostRoot,'flight/runs',review.run,'raw.jsonl');
 const interval=flightInterval(rawPath,review);inputFiles[path.relative(hostRoot,rawPath)]={sha256:hash(fs.readFileSync(rawPath))};
 return{format:'aeris-beta05-auto-video-qualification',version:1,flightRun:review.run,flightBoot:review.boot,modelSha256:review.modelSha256,planSha256:review.planSha256,...interval,...qualifySamples({reports:rows,...interval}),inputFiles,authorityRestorable:false,independentHumanQA:false};
}
