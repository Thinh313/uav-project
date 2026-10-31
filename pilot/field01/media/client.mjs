/** Browser-only authenticated transport and bounded monotonic clock calibration. */
export async function connectMedia(role, baseUrl = 'http://127.0.0.1:8871') {
  const bootstrap = await fetch(baseUrl + '/api/bootstrap?role=' + role,{signal:AbortSignal.timeout(2000)}).then(r => { if (!r.ok) throw Error('BOOTSTRAP_HTTP_'+r.status); return r.json(); });
  async function post(route, value, binary = false) {
    const response = await fetch(baseUrl + '/api/' + route,{method:'POST',headers:{'Content-Type':binary?'application/octet-stream':'application/json',Authorization:'Bearer '+bootstrap.bearer,'X-Media-Nonce':bootstrap.nonce},body:binary?value:JSON.stringify(value),signal:AbortSignal.timeout(2200)});
    if (!response.ok) { let error; try { error = (await response.json()).error; } catch {} throw Error(error || 'MEDIA_HTTP_'+response.status); }
    return response;
  }
  const json = async (route,value) => (await post(route,value)).json();
  async function calibrate() {
    const samples = [];
    for (let i=0;i<5;i++) { const start = performance.now(); const q = await json('clock',{browserSendMs:start}); const end = performance.now(); if (q.serverBoot !== bootstrap.serverBoot || end-start > 20) continue; const low = q.serverSentMs-end, high=q.serverReceivedMs-start; if (high >= low && high-low <=20) samples.push({lowerMs:low,upperMs:high,...clockValidityWindow(end),roundtripMs:end-start}); }
    if (!samples.length) throw Error('CLOCK_CALIBRATION_UNKNOWN');
    return samples.sort((a,b)=>(a.upperMs-a.lowerMs)-(b.upperMs-b.lowerMs))[0];
  }
  return {bootstrap,post,json,calibrate};
}
export function clockBounds(browserMs, clock) { return clock && browserMs >= clock.sampledBrowserMs-1000 && browserMs <= clock.validUntilBrowserMs ? {lowerMs:browserMs+clock.lowerMs,upperMs:browserMs+clock.upperMs} : null; }
export function percentile(values,p=.95) { const sorted = values.filter(Number.isFinite).sort((a,b)=>a-b); return sorted.length ? sorted[Math.max(0,Math.ceil(p*sorted.length)-1)] : null; }

/** A stale encoded item is discarded, never retried. Seq advances only after an
 * acknowledged relay response (including explicit relay suppression). A fresh
 * keyframe fences dependencies after a local drop. Clock repairs are bounded. */
export class PublisherTransport {
  constructor({session,postChunk,json,calibrate,packet,now=()=>performance.now(),maxClockRecoveries=2,onRecovery=()=>{}}) {
    this.session={...session};this.postChunk=postChunk;this.json=json;this.calibrate=calibrate;this.packet=packet;this.now=now;this.maxClockRecoveries=maxClockRecoveries;this.onRecovery=onRecovery;
    this.sequence=0;this.clockRecoveries=0;this.staleDrops=0;this.waitKey=true;
  }
  async publish(item) {
    const age=this.now()-item.timestampUs/1000;
    if(!Number.isFinite(age)||age<0||age>750){this.staleDrops++;this.waitKey=true;return{accepted:false,needKeyframe:true,localDrop:true,reason:'STALE_ENCODED_ITEM_DROPPED',ageMs:age};}
    if(this.waitKey&&item.type!=='key')return{accepted:false,needKeyframe:true,localDrop:true,reason:'WAIT_FRESH_SOURCE_KEYFRAME'};
    const s=this.session,meta={run:s.run,boot:s.boot,feed:s.feed,configId:s.configId,profileId:s.profileId,chunkSeq:this.sequence+1,frameId:item.frameId,timestampUs:item.timestampUs,type:item.type};
    let result;
    try{result=await this.postChunk(this.packet(meta,item.bytes));}
    catch(error){
      if(error.message!=='SOURCE_CLOCK_STALE_OR_FUTURE')throw error;
      this.waitKey=true;
      if(this.clockRecoveries>=this.maxClockRecoveries)throw Error('SOURCE_CLOCK_RECOVERY_BOUND');
      const clock=await this.calibrate();await this.json('source-clock',{configId:s.configId,clock});this.clockRecoveries++;
      this.onRecovery({kind:'SOURCE_CLOCK_RECALIBRATED_ITEM_DROPPED',clockRecoveries:this.clockRecoveries,maxClockRecoveries:this.maxClockRecoveries,frameId:item.frameId,ageMs:age});
      return{accepted:false,needKeyframe:true,localDrop:true,reason:'SOURCE_CLOCK_RECALIBRATED_ITEM_DROPPED'};
    }
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
