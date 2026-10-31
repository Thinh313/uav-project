/** Explicit checked projection of the frozen publisher; unchanged codec/cadence. */
function replaceOnce(source,from,to){if(source.split(from).length!==2)throw Error('PBR_PUBLISHER_PROJECTION_ANCHOR');return source.replace(from,to);}
export function projectPbrPublisher(original){
 let s=original;
 s=replaceOnce(s,"const $ = id => document.getElementById(id), canvas=$('source'), draw=canvas.getContext('2d',{alpha:false});","const $ = id => document.getElementById(id), canvas=$('source'); let sourceSimulation=null;");
 const start=s.indexOf('function scene(t,id,feed){'),end=s.indexOf('\nfunction stop(',start);if(start<0||end<start||s.split('function scene(t,id,feed){').length!==2||s.split('\nfunction stop(').length!==2)throw Error('PBR_PUBLISHER_SCENE_ANCHOR');
 s=s.slice(0,start)+"function scene(t,id,feed){sourceSimulation=renderPayloadSource(feed,{videoFrameId:id});}"+s.slice(end);
 s=replaceOnce(s,"async function start(){if(active||starting)return;if(draining)throw Error('PREVIOUS_PUBLISH_INFLIGHT');starting=true;const local=++epoch,selected=","async function start(){if(active||starting)return;if(draining)throw Error('PREVIOUS_PUBLISH_INFLIGHT');starting=true;const local=++epoch;try{await preparePayloadSource(canvas);}catch(e){if(epoch===local)stop(e.message);throw e;}if(epoch!==local||!starting)return;const selected=");
 const drainStart=s.indexOf('async function drain(local){'),drainEnd=s.indexOf('\nfunction output(',drainStart);
 if(drainStart<0||drainEnd<drainStart||s.split('async function drain(local){').length!==2||s.split('\nfunction output(').length!==2)throw Error('PBR_PUBLISHER_DRAIN_ANCHOR');
 s=s.slice(0,drainStart)+`async function drain(local){if(draining)return;draining=true;try{while(active&&epoch===local&&queue.length){
 const until=performance.now()+40;while(active&&epoch===local&&queue.length<2&&performance.now()<until)await new Promise(resolve=>setTimeout(resolve,4));if(!active||epoch!==local)break;
 // Keep the waiting records in the original queue. The original3-credit gate
 // therefore counts conservatively during proof batching; no hidden in-flight slot.
 const items=queue.slice(0,2);await client.json('frame-proofs',{configId:session.configId,frames:items.map(item=>({frameId:item.frameId,timestampUs:item.timestampUs,metadata:item.sourceSimulation}))});
 if(!active||epoch!==local)break;for(const item of items){if(!active||epoch!==local)break;if(queue[0]!==item)throw Error('SOURCE_BATCH_QUEUE_IDENTITY');queue.shift();const result=await transport.publish(item);if(!result.accepted){if(result.localDrop)counts.outputDrops++;else counts.rejected++;key=true;}else counts.published++;if(result.needKeyframe)key=true;const exposure=takeSourceExposure(item.frameId);if(exposure){const outcome=await exposure;if(!outcome.ok)throw outcome.error;if(!active||epoch!==local)break;await client.json('source-exposure',{configId:session.configId,...outcome.value});}}
 }}catch(error){counts.apiFailures++;if(active&&epoch===local)stop(error.message);}finally{draining=false;}}`+s.slice(drainEnd);
 s=replaceOnce(s,"queue.push({frameId:id,timestampUs:chunk.timestamp,type:chunk.type,bytes,","queue.push({frameId:id,timestampUs:chunk.timestamp,type:chunk.type,bytes,sourceSimulation:source.sourceSimulation,");
 s=replaceOnce(s,"scene(t,id,session.feed);","try{scene(t,id,session.feed);}catch(e){stop(e.message);return;}");
 s=replaceOnce(s,"pending.set(stamp,{id,sourceBrowserMs:t,sourceStages});","pending.set(stamp,{id,sourceBrowserMs:t,sourceStages,sourceSimulation});");
 s=replaceOnce(s,"clock=initialClock;const prior=", "clock=initialClock;promoteSceneToEvents(()=>life.current());const prior=");
 s=replaceOnce(s,"function stop(reason='Publisher đã dừng'){","function stop(reason='Publisher đã dừng'){cancelSourceExposures();");
 s=s.replaceAll('HTTP/TCP 8873 · backend UNKNOWN','HTTP/TCP 8895 · PBR camera giả lập');
 s+="\nif(new URL(location.href).searchParams.get('auto-source')==='1'){try{if(!client)throw Error('SOURCE_MEDIA_BOOTSTRAP_REQUIRED');await waitForPayloadSource(canvas,{feed:$('feed').value});await start();}catch(e){status('Nguồn tự động đã dừng, không thử lại: '+e.message);}}\n";
 return "import {preparePayloadSource,renderPayloadSource,waitForPayloadSource,takeSourceExposure,cancelSourceExposures,promoteSceneToEvents} from '/scene/publisher-scene.mjs';\n"+s;
}
