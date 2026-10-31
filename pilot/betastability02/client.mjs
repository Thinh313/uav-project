/** AbortController works on Android WebView101; deadline includes complete response body. */
export async function fetchBoundedMedia(url,init={},timeoutMs=2200){
 const startBrowserMs=performance.now(),controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
 try{const r=await fetch(url,{...init,signal:controller.signal}),headersBrowserMs=performance.now(),declared=Number(r.headers.get('Content-Length'));if(Number.isFinite(declared)&&declared>2*2**20)throw Error('MEDIA_RESPONSE_BOUND');const bytes=await r.arrayBuffer();if(bytes.byteLength>2*2**20)throw Error('MEDIA_RESPONSE_BOUND');const response=new Response([204,205,304].includes(r.status)?null:bytes,{status:r.status,statusText:r.statusText,headers:r.headers});Object.defineProperty(response,'field02Timing',{value:{startBrowserMs,headersBrowserMs,bodyBrowserMs:performance.now(),responseBytes:bytes.byteLength},enumerable:false});return response;}finally{clearTimeout(timer);}
}
/** Browser-only authenticated transport and bounded monotonic clock calibration. */
export async function connectMedia(role, baseUrl = 'http://127.0.0.1:8873') {
  const clockEvents=[];let clockSequence=0,clockSent=0,clockFlush=null,clockDropped=0;function recordClock(event){if(clockEvents.length-clockSent>=512){clockDropped++;traceFatal??='CLOCK_DIAGNOSTIC_PENDING_OVERFLOW';return;}clockEvents.push({seq:++clockSequence,atBrowserMs:performance.now(),...event});}
  const traceId=crypto.randomUUID();let traceContext=null,traceSequence=0,traceAck=0,traceQueue=[],traceFatal=null,traceTask=null;const traceTimer=setInterval(()=>{if(traceQueue.length&&!traceTask&&!traceFatal)void flushSpans().catch(()=>{});},250);
  function setTraceContext(context){traceContext={...context};}
  function recordSpan(kind,data){if(!traceContext)return;if(traceFatal)throw Error('FULL_TRACE_FAILED:'+traceFatal);if(traceQueue.length>=512){traceFatal='PENDING_BOUND';throw Error('FULL_TRACE_FAILED:'+traceFatal);}const frozenData=structuredClone({...data,context:{...traceContext}});traceQueue.push({seq:++traceSequence,kind,atMs:performance.now(),data:frozenData});}
  async function flushSpans(){if(traceFatal)throw Error('FULL_TRACE_FAILED:'+traceFatal);if(traceTask)return traceTask;if(!traceQueue.length)return;const task=(async()=>{const rows=traceQueue.slice(0,64),q=await json('full-trace',{version:1,traceId,serverBoot:bootstrap.serverBoot,configId:rows[0].data.context.configId,events:rows});if(q.acceptedThrough!==rows.at(-1).seq)throw Error('FULL_TRACE_ACK_SEQUENCE');traceQueue.splice(0,rows.length);traceAck=rows.at(-1).seq;})();traceTask=task;try{await task;}catch(e){traceFatal=e.message;throw e;}finally{traceTask=null;}}
  /** Fsync only the prefix required at entry; a live producer may append later rows. */
  async function traceBarrier(){
    if(traceFatal)throw Error('FULL_TRACE_FAILED:'+traceFatal);
    const requiredThrough=traceSequence,configId=traceContext?.configId??null;
    if(!configId)throw Error('TRACE_PREFIX_CONTEXT_REQUIRED');
    let attempts=0,previous=traceAck;
    while(traceAck<requiredThrough){if(++attempts>9)throw Error('TRACE_PREFIX_FLUSH_BOUND');await flushSpans();if(traceFatal||traceAck<=previous)throw Error('TRACE_PREFIX_FLUSH_NO_PROGRESS');previous=traceAck;}
    const q=await json('trace-barrier',{traceId,configId,serverBoot:bootstrap.serverBoot,requiredThrough});
    const live=traceState(),d=q?.durable;
    if(traceFatal)throw Error('FULL_TRACE_FAILED:'+traceFatal);
    if(q?.traceId!==traceId||q.configId!==configId||q.serverBoot!==bootstrap.serverBoot||q.requiredThrough!==requiredThrough||!Number.isSafeInteger(q.ackThrough)||q.ackThrough<requiredThrough)throw Error('TRACE_PREFIX_ACK');
    if(!d||d.complete!==true||d.fatal!==null||!Number.isSafeInteger(d.hostThrough)||d.hostThrough<0||!/^[a-f0-9]{64}$/.test(d.hostHead??'')||!/^[a-f0-9]{64}$/.test(d.receiptSha256??'')||!/^trace-barrier-[0-9]{5}\.json$/.test(d.receiptFile??''))throw Error('TRACE_PREFIX_DURABILITY');
    return{format:'aeris-betastability02-trace-prefix',version:1,traceId,configId,serverBoot:bootstrap.serverBoot,requiredThrough,ackThrough:q.ackThrough,durable:{...d},currentLiveAccepted:live.accepted,currentLiveAcknowledged:live.acknowledged,currentLivePending:live.pending,fatal:live.fatal,scope:'DURABLE_REQUIRED_PREFIX_ONLY_LIVE_PRODUCER_CONTINUES'};
  }
  function traceState(){return{accepted:traceSequence,acknowledged:traceAck,pending:traceQueue.length,fatal:traceFatal};}
  const transportSamples=[],transportTotals={};const bootstrap = await fetchBoundedMedia(baseUrl + '/api/bootstrap?role=' + role,{},2000).then(r => { if (!r.ok) throw Error('BOOTSTRAP_HTTP_'+r.status); return r.json(); });
  async function post(route, value, binary = false) {
    const response = await fetchBoundedMedia(baseUrl + '/api/' + route,{method:'POST',headers:{'Content-Type':binary?'application/octet-stream':'application/json',Authorization:'Bearer '+bootstrap.bearer,'X-Media-Nonce':bootstrap.nonce},body:binary?value:JSON.stringify(value)});
    const timing=response.field02Timing;if(!transportTotals[route]&&Object.keys(transportTotals).length<16)transportTotals[route]={count:0,totalMs:0,maximumMs:0};const total=transportTotals[route];if(total){const elapsed=timing.bodyBrowserMs-timing.startBrowserMs;total.count++;total.totalMs+=elapsed;total.maximumMs=Math.max(total.maximumMs,elapsed);}if(!['full-trace','trace-barrier'].includes(route))recordSpan(role==='viewer'?'VIEWER_HTTP':'SOURCE_HTTP',{route,...timing,status:response.status});transportSamples.push({route,...timing,status:response.status});if(transportSamples.length>128)transportSamples.shift();if (!response.ok) { let error; try { error = (await response.json()).error; } catch {} throw Error(error || 'MEDIA_HTTP_'+response.status); }
    return response;
  }
  const json = async (route,value) => (await post(route,value)).json();
  async function flushClock(){if(clockFlush)return clockFlush;if(clockSent>=clockEvents.length)return;const task=(async()=>{let batches=0;while(clockSent<clockEvents.length&&batches++<16){const rows=clockEvents.slice(clockSent,clockSent+32);await json('clock-diagnostics',{role,events:rows,dropped:clockDropped});clockSent+=rows.length;}})();clockFlush=task;try{await task;}finally{if(clockSent>256){clockEvents.splice(0,clockSent);clockSent=0;}if(clockFlush===task)clockFlush=null;}}
  async function calibrate({isCurrent=()=>true,reason='UNSPECIFIED'}={}) {
    const samples=[];recordClock({kind:'PROBE_BATCH_BEGIN',reason});
    try{for(let i=0;i<5;i++){if(!isCurrent())throw Error('CLOCK_CONTEXT_ENDED');const start=performance.now();let q,end;try{q=await json('clock',{browserSendMs:start});end=performance.now();}catch(e){recordClock({kind:'PROBE_TRANSPORT_FAILURE',reason,index:i,startBrowserMs:start,endBrowserMs:performance.now(),error:String(e.message).slice(0,160)});throw e;}if(!isCurrent())throw Error('CLOCK_CONTEXT_ENDED');const low=q.serverSentMs-end,high=q.serverReceivedMs-start,accepted=q.serverBoot===bootstrap.serverBoot&&end-start<=20&&high>=low&&high-low<=20;recordClock({kind:'PROBE_RESULT',reason,index:i,startBrowserMs:start,endBrowserMs:end,serverBoot:q.serverBoot,serverReceivedMs:q.serverReceivedMs,serverSentMs:q.serverSentMs,lowerMs:low,upperMs:high,roundtripMs:end-start,accepted});if(accepted)samples.push({lowerMs:low,upperMs:high,...clockValidityWindow(end),roundtripMs:end-start});}if(!samples.length)throw Error('CLOCK_CALIBRATION_UNKNOWN');if(!isCurrent())throw Error('CLOCK_CONTEXT_ENDED');return samples.sort((a,b)=>(a.upperMs-a.lowerMs)-(b.upperMs-b.lowerMs))[0];}
    finally{recordClock({kind:'PROBE_BATCH_END',reason,validSamples:samples.length});void flushClock().catch(()=>{});}
  }
  return {bootstrap,post,json,calibrate,recordClock,flushClock,setTraceContext,recordSpan,flushSpans,traceBarrier,traceState,clockEvents:()=>clockEvents.map(e=>({...e})),transportSamples:()=>transportSamples.map(x=>({...x})),transportTotals:()=>structuredClone(transportTotals)};
}
export function clockBounds(browserMs, clock) { return clock && browserMs >= clock.sampledBrowserMs-1000 && browserMs < clock.validUntilBrowserMs ? {lowerMs:browserMs+clock.lowerMs,upperMs:browserMs+clock.upperMs} : null; }
export function percentile(values,p=.95) { const sorted = values.filter(Number.isFinite).sort((a,b)=>a-b); return sorted.length ? sorted[Math.max(0,Math.ceil(p*sorted.length)-1)] : null; }

/** A stale encoded item is discarded, never retried. Seq advances only after an
 * acknowledged relay response (including explicit relay suppression). A fresh
 * keyframe fences dependencies after a local drop. Clock repairs are bounded. */
export class PublisherTransport {
  constructor({session,postChunk,json,calibrate,packet,now=()=>performance.now(),maxClockRecoveries=2,onRecovery=()=>{},onTiming=()=>{},isCurrent=()=>true}) {
    this.session={...session};this.postChunk=postChunk;this.json=json;this.calibrate=calibrate;this.packet=packet;this.now=now;this.maxClockRecoveries=maxClockRecoveries;this.onRecovery=onRecovery;this.onTiming=onTiming;
    this.isCurrent=isCurrent;this.sequence=0;this.clockRecoveries=0;this.staleDrops=0;this.waitKey=true;
  }
  async publish(item) {
    if(!this.isCurrent())throw Error('CLOCK_CONTEXT_ENDED');
    const age=this.now()-item.timestampUs/1000;
    if(!Number.isFinite(age)||age<0||age>750){this.staleDrops++;this.waitKey=true;return{accepted:false,needKeyframe:true,localDrop:true,reason:'STALE_ENCODED_ITEM_DROPPED',ageMs:age};}
    if(this.waitKey&&item.type!=='key')return{accepted:false,needKeyframe:true,localDrop:true,reason:'WAIT_FRESH_SOURCE_KEYFRAME'};
    const s=this.session,meta={run:s.run,boot:s.boot,feed:s.feed,configId:s.configId,profileId:s.profileId,chunkSeq:this.sequence+1,frameId:item.frameId,timestampUs:item.timestampUs,type:item.type};
    let result;
    const publishStartMs=this.now();try{result=await this.postChunk(this.packet(meta,item.bytes));this.onTiming({configId:s.configId,frameId:item.frameId,sourceTimestampUs:item.timestampUs,encodedBrowserMs:item.encodedBrowserMs??null,sourceStages:item.sourceStages?{...item.sourceStages}:null,publishStartMs,publishEndMs:this.now(),accepted:result?.accepted===true});}
    catch(error){
      if(!this.isCurrent())throw Error('CLOCK_CONTEXT_ENDED');
      if(error.message!=='SOURCE_CLOCK_STALE_OR_FUTURE')throw error;
      this.waitKey=true;
      if(this.clockRecoveries>=this.maxClockRecoveries)throw Error('SOURCE_CLOCK_RECOVERY_BOUND');
      await this.calibrate();if(!this.isCurrent())throw Error('CLOCK_CONTEXT_ENDED');this.clockRecoveries++;
      this.onRecovery({kind:'SOURCE_CLOCK_RECALIBRATED_ITEM_DROPPED',clockRecoveries:this.clockRecoveries,maxClockRecoveries:this.maxClockRecoveries,frameId:item.frameId,ageMs:age});
      return{accepted:false,needKeyframe:true,localDrop:true,reason:'SOURCE_CLOCK_RECALIBRATED_ITEM_DROPPED'};
    }
    if(!this.isCurrent())throw Error('CLOCK_CONTEXT_ENDED');
    if(typeof result?.accepted!=='boolean'||typeof result?.needKeyframe!=='boolean')throw Error('PUBLISH_ACK_SCHEMA_UNCERTAIN_NO_RETRY');
    this.sequence++;
    this.waitKey=!result.accepted||result.needKeyframe;
    return result;
  }
}

/** Binary-grid marker prevents validUntil - sampled from drifting from exact 60000.
 * Offset bounds retain the original full precision request/reply timestamps. */
export function clockValidityWindow(browserNowMs) {
  if(!Number.isFinite(browserNowMs)||browserNowMs<0||browserNowMs>2**31)throw Error('CLOCK_MARKER_BOUND');
  const sampledBrowserMs=Math.floor(browserNowMs*1024)/1024;
  return{sampledBrowserMs,validUntilBrowserMs:sampledBrowserMs+60000};
}

/** No in-flight/pre-resume frame may certify recovery from a relay blackout. */
export function pauseRecoveryEligible(fault,frame,displayBrowserMs) {
  return !!fault && fault.status==='ARMED' && Number.isFinite(fault.responseBrowserMs) && Number.isSafeInteger(fault.expectedRecoveryId) && Number.isFinite(fault.serverResumeNotBeforeMs)
    && Number.isFinite(displayBrowserMs) && displayBrowserMs-fault.at>=fault.durationMs
    && frame.configId===fault.configId && Number.isSafeInteger(frame.recoveryId) && frame.recoveryId>=fault.expectedRecoveryId
    && Number.isFinite(frame.sourceHostBounds?.lowerMs) && frame.sourceHostBounds.lowerMs>=fault.serverResumeNotBeforeMs;
}

/** Keep decoder queue cap2/pending cap8. Allow bounded asynchronous output before resync. */
export async function waitDecoderCapacity({queueSize,pendingSize,isCurrent=()=>true,now=()=>performance.now(),sleep=ms=>new Promise(r=>setTimeout(r,ms)),budgetMs=150,startupGrace=false}={}){
 if(budgetMs!==150||typeof startupGrace!=='boolean')throw Error('FIXED_DECODER_WAIT_150MS');const budget=startupGrace?1500:150,start=now();let checks=0;
 while(isCurrent()){const q=queueSize(),p=pendingSize();if(!Number.isSafeInteger(q)||q<0||!Number.isSafeInteger(p)||p<0)throw Error('DECODER_CAPACITY_STATE');checks++;if(q<2&&p<8)return{ready:true,waitMs:now()-start,checks};const remaining=budget-(now()-start);if(remaining<=0)return{ready:false,reason:'DECODER_CAPACITY_TIMEOUT',waitMs:now()-start,checks};await sleep(Math.min(5,remaining));}
 return{ready:false,reason:'DECODER_SESSION_ENDED',waitMs:now()-start,checks};
}

let codecProbeUsed=false;
/** One explicitly requested local encode/key/decode/flush probe; never network acceptance. */
export async function probeCodecOnce(){
 if(codecProbeUsed)throw Error('ONE_CODEC_PROBE_PER_PAGE');codecProbeUsed=true;const start=performance.now(),r={kind:'FIELD02_LOCAL_VP8_SINGLE_KEY_PROBE',networkUsed:false,videoAcceptance:false,width:1280,height:720,deadlineMs:2000,outputs:0};let encoder,decoder,timer,current=true;
 const work=async()=>{if(!globalThis.VideoEncoder||!globalThis.VideoDecoder)throw Error('WEBCODECS_UNAVAILABLE');const ec={codec:'vp8',width:1280,height:720,framerate:30,bitrate:4000000,latencyMode:'realtime',hardwareAcceleration:'prefer-software'};r.encoderSupported=(await VideoEncoder.isConfigSupported(ec)).supported;if(!current)throw Error('PROBE_STOPPED');if(!r.encoderSupported)throw Error('ENCODER_UNSUPPORTED');const canvas=document.createElement('canvas');canvas.width=1280;canvas.height=720;const d=canvas.getContext('2d');d.fillStyle='#46755e';d.fillRect(0,0,1280,720);d.fillStyle='#fff';d.fillRect(100,100,800,400);let encoded=null,codecError=null;encoder=new VideoEncoder({output:(chunk,meta)=>{if(!current)return;const bytes=new Uint8Array(chunk.byteLength);chunk.copyTo(bytes);encoded={bytes,type:chunk.type,timestamp:chunk.timestamp,descriptionBytes:meta?.decoderConfig?.description?.byteLength??0};},error:e=>codecError=String(e.message)});encoder.configure(ec);const frame=new VideoFrame(canvas,{timestamp:1000000,duration:33333});try{encoder.encode(frame,{keyFrame:true});}finally{frame.close();}const es=performance.now();await encoder.flush();if(!current)throw Error('PROBE_STOPPED');r.encodeFlushMs=performance.now()-es;if(codecError)throw Error(codecError);if(!encoded)throw Error('NO_ENCODED_KEY');r.chunk={type:encoded.type,timestamp:encoded.timestamp,bytes:encoded.bytes.length,descriptionBytes:encoded.descriptionBytes,first16Hex:[...encoded.bytes.slice(0,16)].map(x=>x.toString(16).padStart(2,'0')).join('')};const dc={codec:'vp8',codedWidth:1280,codedHeight:720,optimizeForLatency:true,hardwareAcceleration:'prefer-software'};r.decoderSupported=(await VideoDecoder.isConfigSupported(dc)).supported;if(!current)throw Error('PROBE_STOPPED');if(!r.decoderSupported)throw Error('DECODER_UNSUPPORTED');decoder=new VideoDecoder({output:f=>{try{if(current){r.outputs++;r.output={timestamp:f.timestamp,width:f.codedWidth,height:f.codedHeight,atMs:performance.now()-start};}}finally{f.close();}},error:e=>codecError=String(e.message)});decoder.configure(dc);decoder.decode(new EncodedVideoChunk({type:encoded.type,timestamp:encoded.timestamp,data:encoded.bytes}));const ds=performance.now();await decoder.flush();if(!current)throw Error('PROBE_STOPPED');r.decodeFlushMs=performance.now()-ds;if(codecError)throw Error(codecError);r.status=r.outputs>0?'LOCAL_SINGLE_KEY_DECODED':'NO_DECODER_OUTPUT';return r;};
 try{return await Promise.race([work(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('CODEC_PROBE_2000MS_DEADLINE')),2000);})]);}catch(e){r.status='FAILED_OR_TIMEOUT';r.error=String(e.message);return r;}finally{current=false;clearTimeout(timer);try{encoder?.close();}catch{}try{decoder?.close();}catch{}r.elapsedMs=performance.now()-start;}
}

/** Cached state is discovery only; every binary packet retains the complete session fence. */
export function assertMediaPacket(meta,session,{lastFrameId=-1,lastTimestampUs=-1}={}){
 if(!session)throw Error('VIEWER_SESSION_REQUIRED');for(const k of['run','boot','configId','feed','profileId'])if(meta[k]!==session[k])throw Error('VIEWER_FRAME_TARGET:'+k);
 if(!Number.isSafeInteger(meta.frameId)||meta.frameId<=lastFrameId||!Number.isSafeInteger(meta.timestampUs)||meta.timestampUs<=lastTimestampUs||typeof meta.frameRef!=='string'||!meta.frameRef||!Number.isFinite(meta.sourceHostBounds?.lowerMs)||!Number.isFinite(meta.sourceHostBounds?.upperMs)||meta.sourceHostBounds.upperMs<meta.sourceHostBounds.lowerMs||!/^\d{1,24}$/.test(meta.relayReceivedMonoNs??''))throw Error('VIEWER_FRAME_SEQUENCE_OR_CLOCK');return true;
}
export const statePollDue=(lastAt,now)=>!Number.isFinite(lastAt)||now-lastAt>=1000;

/** Admit raw frames before encode; three total pipeline credits preserve encoded dependencies. */
export function sourceCreditAdmission({pending,queued,publishing,encodeQueueSize,active=true,hidden=false}={}){
 if(![pending,queued,encodeQueueSize].every(x=>Number.isSafeInteger(x)&&x>=0)||typeof publishing!=='boolean')throw Error('SOURCE_CREDIT_STATE');const credits=pending+queued+(publishing?1:0);
 if(!active)return{allowed:false,reason:'INACTIVE',credits};if(hidden)return{allowed:false,reason:'HIDDEN',credits};if(encodeQueueSize>=2)return{allowed:false,reason:'ENCODER_QUEUE_2',credits};if(pending>=8)return{allowed:false,reason:'PENDING_8',credits};if(credits>=3)return{allowed:false,reason:'PIPELINE_CREDITS_3',credits};return{allowed:true,credits};
}
