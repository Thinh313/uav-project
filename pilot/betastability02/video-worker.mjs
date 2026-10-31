/** Dedicated-worker video path. No hidden main-thread decoder/canvas fallback. */
export function createVideoWorkerRuntime({scope=globalThis,loadEngine=base=>import(new URL('/viewer-engine.mjs',base).href)}={}){
 let engine=null,generation=0,initialized=false,closing=false,heartbeat=null,visibility=null,lastVisibilityMs=-Infinity,sourceDiagnostics=null,capabilities=null,lastReport=null;
 let collection={total:0,completed:0,remaining:0,active:false,failure:null};
 const now=()=>scope.performance.now(),post=(kind,data={},g=generation)=>scope.postMessage({kind,generation:g,...data});
 const visible=()=>!!visibility&&now()-lastVisibilityMs<=500&&visibility.visible===true&&visibility.foreground===true&&visibility.rectFullyVisible===true&&Number.isFinite(visibility.width)&&visibility.width>0&&Number.isFinite(visibility.height)&&visibility.height>0;
 const stateWithScope=q=>({...q,scope:'WORKER_CANVAS_CALL_NOT_PHOTON',collection:{...collection},workerVisibility:{fresh:now()-lastVisibilityMs<=500,ageMs:now()-lastVisibilityMs,visible:visible()},workerCapabilities:capabilities});
 function stopCollection(reason){collection.active=false;collection.remaining=0;if(reason)collection.failure=reason;}
 function invalidate(reason){stopCollection(reason);engine?.invalidateVisualCoverage(reason);engine?.stop(reason,true);}
 function onState(q){
  if(q.report){
   const key=q.report.configId+':'+q.report.measurementStartBrowserMs+':'+q.report.measurementEndBrowserMs;
   if(lastReport===key)return;lastReport=key;
   if(collection.active){collection.completed++;collection.remaining=Math.max(0,collection.total-collection.completed);const valid=!q.report.stopReason&&q.report.engineeringGate?.coverage===true&&visible();if(!valid){const reason=q.report.stopReason??'WORKER_WINDOW_INVALID';stopCollection(reason);queueMicrotask(()=>engine?.stop(reason,true));}else if(collection.remaining>0){try{engine.measure({durationMs:30000});}catch(e){stopCollection('WORKER_NEXT_WINDOW:'+e.message);}}else collection.active=false;}
  }
  post('state',{state:stateWithScope(q)});
 }
 function updateVisibility(next,diagnostics){
  const priorHidden=scope.document?.hidden??true;visibility=next&&typeof next==='object'?{...next}:null;lastVisibilityMs=now();sourceDiagnostics=diagnostics??sourceDiagnostics;
  if(visibility){scope.innerWidth=visibility.width;scope.innerHeight=visibility.height;scope.devicePixelRatio=visibility.dpr??1;}
  const hidden=!visible();if(priorHidden!==hidden&&scope.document?.dispatchEvent)scope.document.dispatchEvent(new Event('visibilitychange'));
  if(initialized&&!visible()&&(engine.state().active||collection.active))invalidate('WORKER_VISIBILITY_LOST');
 }
 function installCanvasEnvironment(canvas){
  let initial=canvas;const events=new EventTarget();
  function adapt(c){c.style={cssText:''};c.setAttribute=()=>{};c.toBlob=(callback,type='image/jpeg',quality=.9)=>{c.convertToBlob({type,quality}).then(callback,()=>callback(null));};return c;}
  scope.document={get hidden(){return!visible();},createElement(name){if(name!=='canvas')throw Error('WORKER_CANVAS_ONLY');if(initial){const c=initial;initial=null;return adapt(c);}return adapt(new scope.OffscreenCanvas(1280,720));},addEventListener:events.addEventListener.bind(events),dispatchEvent:events.dispatchEvent.bind(events)};
  // Engine pagehide subscription is explicitly forwarded by the main proxy.
  scope.window=scope;scope.innerWidth=visibility?.width??0;scope.innerHeight=visibility?.height??0;scope.devicePixelRatio=visibility?.dpr??1;
 }
 async function init(q){
  if(initialized||engine)throw Error('WORKER_ALREADY_INITIALIZED');generation=q.generation;
  capabilities={videoDecoder:typeof scope.VideoDecoder==='function',offscreenCanvas:typeof scope.OffscreenCanvas==='function',transferredCanvas:typeof scope.OffscreenCanvas==='function'&&q.canvas instanceof scope.OffscreenCanvas,moduleWorker:true};
  if(!capabilities.videoDecoder||!capabilities.offscreenCanvas||!capabilities.transferredCanvas)throw Error('WORKER_CAPABILITY_UNSUPPORTED');capabilities.canvas2D=!!q.canvas.getContext('2d',{alpha:false});capabilities.blobExport=typeof q.canvas.convertToBlob==='function';if(!capabilities.canvas2D||!capabilities.blobExport)throw Error('WORKER_CANVAS_2D_OR_BLOB_UNSUPPORTED');
  updateVisibility(q.visibility,q.sourceDiagnostics);installCanvasEnvironment(q.canvas);
  const mod=await loadEngine(q.baseUrl);if(closing||generation!==q.generation)throw Error('WORKER_INIT_CANCELLED');
  engine=mod.createViewer({container:{append(){}},baseUrl:q.baseUrl,onState,isVisuallyVisible:visible,getSourceDiagnostics:()=>sourceDiagnostics});initialized=true;
  heartbeat=scope.setInterval(()=>{if(!closing&&engine&&(engine.state().active||collection.active)&&!visible())invalidate('WORKER_VISIBILITY_HEARTBEAT_EXPIRED_500MS');},100);
  return{capabilities,scope:'WORKER_CANVAS_CALL_NOT_PHOTON',state:stateWithScope(engine.state())};
 }
 async function receive(q){
  if(!q||typeof q!=='object')return;
  if(!Number.isSafeInteger(q.generation)||q.generation<0){post('fatal',{error:'WORKER_GENERATION_REQUIRED'});return;}
  if(q.kind==='visibility'){if(q.generation===generation&&!closing)updateVisibility(q.visibility,q.sourceDiagnostics);return;}
  if(q.kind==='invalidate'){if(q.generation===generation&&!closing&&typeof q.reason==='string'&&q.reason.length<=160)invalidate(q.reason);return;}
  if(q.kind==='pagehide'){if(q.generation===generation){invalidate('PAGEHIDE');scope.dispatchEvent?.(new Event('pagehide'));}return;}
  if(!Number.isSafeInteger(q.id)||q.id<1)return;
  const callGeneration=q.generation;
  try{
   let result;
   if(q.kind==='init')result=await init(q);
   else if(q.kind==='call'){
    if(closing)throw Error('WORKER_CLOSING');if(!initialized||!engine)throw Error('WORKER_NOT_INITIALIZED');
    const lifecycle=['start','stop','shutdown'].includes(q.method);
    if(q.generation<generation||!lifecycle&&q.generation!==generation)throw Error('WORKER_STALE_GENERATION');if(lifecycle)generation=q.generation;
    const args=Array.isArray(q.args)?q.args:[];
    if(q.method==='start'){if(!visible())throw Error('WORKER_VISIBLE_FOREGROUND_REQUIRED');stopCollection(null);collection={total:0,completed:0,remaining:0,active:false,failure:null};result=await engine.start();}
    else if(q.method==='stop'){stopCollection(args[0]??'EXPLICIT_STOP');result=engine.stop(...args);result=stateWithScope(engine.state());}
    else if(q.method==='shutdown'){closing=true;stopCollection(args[0]??'WORKER_SHUTDOWN');scope.clearInterval(heartbeat);const drained=await engine.shutdown(args[0]??'WORKER_SHUTDOWN');result={status:drained.drain.prefix?'COMPLETE':'NO_CONFIGURED_STREAM',prefix:drained.drain.prefix,clock:drained.drain.clock,workerClock:'WORKER_PERFORMANCE',generation:callGeneration,scope:'WORKER_CANVAS_CALL_NOT_PHOTON'};if(JSON.stringify(result).length>4096)throw Error('WORKER_CLOSURE_RECEIPT_BOUND');post('result',{id:q.id,result},callGeneration);post('closed',{receipt:result},callGeneration);scope.close?.();return;}
    else if(q.method==='measure'){const spec=args[0]??{};if(spec.durationMs!==30000||spec.windows!==6)throw Error('WORKER_FIXED_6X30S_REQUIRED');if(collection.active)throw Error('WORKER_COLLECTION_ACTIVE');if(!visible())throw Error('WORKER_VISIBLE_FOREGROUND_REQUIRED');collection={total:6,completed:0,remaining:6,active:true,failure:null};try{result=engine.measure({durationMs:30000});}catch(e){stopCollection(e.message);throw e;}}
    else if(q.method==='state')result=stateWithScope(engine.state());
    else if(['snapshot','pause','saveReport','setFeed'].includes(q.method))result=await engine[q.method](...args);
    else throw Error('WORKER_METHOD_FORBIDDEN');
   }else throw Error('WORKER_MESSAGE_KIND');
   post('result',{id:q.id,result},callGeneration);
  }catch(e){const error=String(e.message).slice(0,240);post('result',{id:q.id,error,capabilities},callGeneration);if(closing){post('fatal',{error,drain:'FAILED'},callGeneration);scope.close?.();}}
 }
 return{receive,visible,snapshot:()=>({initialized,generation,closing,capabilities,collection:{...collection},visible:visible()})};
}
if(typeof WorkerGlobalScope!=='undefined'&&globalThis instanceof WorkerGlobalScope){const runtime=createVideoWorkerRuntime();globalThis.addEventListener('message',event=>{void runtime.receive(event.data);});}
