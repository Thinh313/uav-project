import assert from'node:assert/strict';import fs from'node:fs';import{encodePacket}from'../../media/big02/relay-core.mjs';import{createViewer}from'./media/viewer.mjs';
const save={document:globalThis.document,window:globalThis.window,VideoDecoder:globalThis.VideoDecoder,EncodedVideoChunk:globalThis.EncodedVideoChunk,fetch:globalThis.fetch};const rows=[];
const session={run:'s00000000000000000000',boot:'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',configId:'bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb',feed:'rgb',profileId:'VP8-720P30-V1',viewerId:'cccccccc-cccc-4ccc-cccc-cccccccccccc'};
const waitFor=async(predicate,timeout=1000)=>{let end=performance.now()+timeout;while(!predicate()){assert(performance.now()<end,'TEST_WAIT_TIMEOUT');await new Promise(r=>setTimeout(r,5));}};
async function run(mode){let seq=0,recovery=1,resync=0,draws=0,frameCloses=0,decoderCloses=0,flushes=0,configures=0,resets=0,lastStamp=0,replyWrong=false,warmDeltaSkipped=false,seen=[];const decoders=[];let v;
 globalThis.document={hidden:false,createElement:()=>({style:{},setAttribute(){},getContext:()=>({drawImage(){draws++;}})}),addEventListener(){}};globalThis.window={addEventListener(){}};
 const frame=timestamp=>({timestamp,close(){frameCloses++;}});
 globalThis.VideoDecoder=class{constructor(c){this.c=c;this.state='unconfigured';this.decodeQueueSize=0;this.cold=true;this.keyRequired=true;decoders.push(this);}configure(){configures++;this.state='configured';this.keyRequired=true;}reset(){resets++;this.decodeQueueSize=0;this.state='unconfigured';this.keyRequired=true;}decode(c){if(this.keyRequired&&c.type!=='key')throw Error('DECODE_DELTA_AFTER_FLUSH');this.keyRequired=false;seen.push({type:c.type,timestamp:c.timestamp});this.decodeQueueSize++;this.pending=c;if(!this.cold){this.decodeQueueSize--;queueMicrotask(()=>this.c.output(frame(c.timestamp)));}}async flush(){flushes++;this.keyRequired=true;if(mode==='stall')return new Promise(()=>{});if(mode==='late-stop'){await new Promise(r=>setTimeout(r,70));}this.cold=false;this.decodeQueueSize=0;if(mode!=='no-output')this.c.output(frame(this.pending.timestamp));}close(){decoderCloses++;this.state='closed';}};
 globalThis.EncodedVideoChunk=class{constructor(q){Object.assign(this,q);}};
 globalThis.fetch=async(url,init={})=>{const route=new URL(url).pathname;let value;
 if(route==='/api/bootstrap')value={bearer:'test',nonce:'boot',serverBoot:'test-boot',viewerId:session.viewerId,profiles:{profiles:[{id:session.profileId,codec:'vp8'}]}};
 else if(route==='/api/clock'){const now=performance.now();value={serverBoot:'test-boot',serverReceivedMs:now,serverSentMs:now};}
 else if(route==='/api/state')value={serverBoot:'test-boot',relay:{session}};
 else if(route==='/api/resync'){resync++;recovery++;value={session:{...session,...mode==='wrong-reply'&&resync===2?{boot:'wrong'}:{}},recoveryId:recovery};}
 else if(route==='/api/next'){
  if(seq>=4){await new Promise(r=>setTimeout(r,5));return new Response(null,{status:204});}
  const n=++seq;lastStamp=Math.max(lastStamp+1000,Math.round(performance.now()*1000));let type=n===1||n===3?'key':'delta';if(n===2)warmDeltaSkipped=true;
  const meta={run:session.run,boot:session.boot,configId:session.configId,feed:session.feed,profileId:session.profileId,frameId:n,timestampUs:lastStamp,type,frameRef:'network-'+n,sourceHostBounds:{lowerMs:lastStamp/1000-.1,upperMs:lastStamp/1000+.1},relayReceivedMonoNs:String(Math.round(performance.now()*1e6)),recoveryId:mode==='wrong-recovery'&&n===2?recovery+1:recovery};
  if(mode==='wrong-first'&&n===1)meta.boot='wrong';
  return new Response(encodePacket(meta,new Uint8Array([1,2,3])),{status:200});
 }else throw Error('UNEXPECTED_ROUTE:'+route);return new Response(JSON.stringify(value),{status:200});};
 try {v=createViewer({container:{append(){}},isVisuallyVisible:()=>true});await v.start();
  if(mode==='success'){
   await waitFor(()=>v.state().networkBootstrap.ready);const s=v.state();assert.equal(flushes,1);assert.equal(resync,2);assert.equal(decoders.length,1);assert.equal(resets,2);assert.equal(configures,2);assert.equal(s.counters.networkBootstrapFlushed,1);assert.equal(s.counters.networkBootstrapWarmKeys,1);assert.equal(s.counters.consumerDrops,1);assert.deepEqual(seen.map(x=>x.type),['key','key','delta']);assert.equal(s.counters.displayed,3);assert.equal(draws,3);assert(v.getPreview());
   const before=structuredClone(s.counters),beforeDraws=draws;v.stop('EXPLICIT_STOP');const afterStop=v.state();decoders[0].c.output(frame(lastStamp));assert.equal(draws,beforeDraws);assert.deepEqual(v.state().counters,afterStop.counters);assert.equal(v.state().decoder.pending,0);rows.push('actual_viewer_first_network_key_flush_same_decoder_exact_warm_key_delta_skip_and_steady_delta');rows.push('late_closed_decoder_callback_changes_no_canvas_counter_or_pending');
  }else if(mode==='late-stop'){
   await waitFor(()=>flushes===1);v.stop('EXPLICIT_STOP_DURING_FLUSH');const before=structuredClone(v.state().counters);await new Promise(r=>setTimeout(r,100));assert.equal(draws,0);assert.equal(resync,1);assert.deepEqual(v.state().counters,before);assert.equal(frameCloses,1);rows.push('actual_stop_during_flush_late_output_closed_without_counter_or_resync');
  }else if(mode==='wrong-first'){await waitFor(()=>v.state().counters.identityRejects===1);assert.equal(flushes,0);assert.equal(draws,0);v.stop('WRONG_FRAME_REFUSED');rows.push('actual_wrong_initial_network_identity_zero_flush_or_display');
  }else{
   await waitFor(()=>!v.state().active,mode==='stall'?1900:1000);const s=v.state();assert.equal(s.networkBootstrap.ready,false);assert.equal(s.counters.networkBootstrapFailures,mode==='wrong-first'?0:1);assert(!v.getPreview());
   if(mode==='stall'){assert.equal(flushes,1);assert.equal(resync,1);assert.equal(seq,1);assert.match(s.failure,/1500MS_TIMEOUT/);}if(mode==='no-output'){assert.equal(flushes,1);assert.equal(resync,1);assert.match(s.failure,/OUTPUT_REQUIRED/);}if(mode==='wrong-reply'){assert.equal(flushes,1);assert.match(s.failure,/RESYNC_IDENTITY/);}if(mode==='wrong-recovery'){assert.equal(seen.length,1);assert.match(s.failure,/POST_FLUSH_KEY_IDENTITY/);}if(mode==='wrong-first'){assert.equal(flushes,0);assert.equal(draws,0);}
   rows.push('actual_viewer_'+mode+'_refused_without_automatic_bootstrap_retry');
  }
 }finally{v?.stop();await new Promise(r=>setTimeout(r,15));}
}
try{for(const mode of['success','late-stop','stall','no-output','wrong-reply','wrong-recovery','wrong-first'])await run(mode);const report={status:'PASS',at:new Date().toISOString(),rows,scope:'ACTUAL_PRODUCTION_VIEWER_FAKE_HTTP_AND_CODEC_NO_ANDROID_PERFORMANCE'};fs.writeFileSync('evidence/field02/host-network-viewer01.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));}finally{Object.assign(globalThis,save);}
