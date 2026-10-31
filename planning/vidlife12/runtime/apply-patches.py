from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def patch(name,a,b):
 p=ROOT/name;s=p.read_text();assert s.count(a)==1,(name,a[:100],s.count(a));p.write_text(s.replace(a,b))
p='runtime/root-wire-media09c.mjs'
patch(p,"fail(reason){this.failure??=reason;this.heartbeatStopped=true;clearInterval(this.heartbeatTimer);clearInterval(this.watch);this.failPending(this.failure);this.socket?.destroy();}","""fail(reason){if(!this.firstFailure12){this.firstFailure12=Object.freeze({reason:String(reason).slice(0,180),nodeHostNs:String(process.hrtime.bigint()),hostClockDomain:'NODE_HRTIME_NS',rxOffset:this.rxOffset,rxValidatedOffset:this.rxValidatedOffset,rxQueued:this.rxQueued,lastRxProof:this.lastRxProof??null,heartbeatAtMs:this.samples[0]?.at??null,observedNowMs:this.now(),authorityRestorable:false});this.failure??=reason;}this.heartbeatStopped=true;clearInterval(this.heartbeatTimer);clearInterval(this.watch);try{this.failPending(this.failure);}finally{this.socket?.destroy();}if(!this.failureTraceAttempted12){this.failureTraceAttempted12=true;try{this.capture.append('ROOT_WIRE_FIRST_FAILURE12',this.firstFailure12);Promise.resolve(this.capture.beforeWire()).catch(e=>{this.failureTraceError12=String(e.message).slice(0,180);});}catch(e){this.failureTraceError12=String(e.message).slice(0,180);}}}""")
patch(p,"receive(m,at){need(","receive(m,at){if(this.heartbeatCadence12&&m.system===42&&m.component===1){const c=this.heartbeatCadence12,f=m.fields;if(m.id===77&&f.command===511&&(!f.target_system||f.target_system===255)&&(!f.target_component||f.target_component===190)&&c.ack===null){c.ack={result:f.result,at};}if(m.id===0&&c.ack?.result===0&&at>=c.ack.at&&c.samples.length<3){const prior=c.samples.at(-1);if(prior!==undefined&&at-prior>1500)c.sampleFailure='ROOT_HEARTBEAT_CADENCE_ORIGINAL_GAP1500';c.samples.push(at);}}need(")
patch(p,"for(const id of[1,24,30,33,42,193,242,245])", "await this.requestHeartbeatCadence12();for(const id of[1,24,30,33,42,193,242,245])")
patch(p," startReadOnlyDiscovery(){", """ async requestHeartbeatCadence12(){need(!this.heartbeatCadence12,'ROOT_HEARTBEAT_CADENCE_ONE_REQUEST');const c=this.heartbeatCadence12={messageId:0,intervalUs:200000,targetSystem:42,targetComponent:1,ack:null,samples:[],sampleFailure:null,ready:false,ackAloneNotExecution:true};await this.send(76,this.target({command:511,param1:0,param2:200000}));await this.until(()=>this.parameterClosing||c.ack!==null,3000);need(!this.parameterClosing,'ROOT_READONLY_SOURCE_CLOSE');need(c.ack.result===0,'ROOT_HEARTBEAT_INTERVAL_REJECTED:'+c.ack.result);await this.until(()=>this.parameterClosing||c.sampleFailure||c.samples.length>=2,3000);need(!this.parameterClosing&&!c.sampleFailure&&c.samples.length>=2,'ROOT_HEARTBEAT_CADENCE_NOT_OBSERVED:'+c.sampleFailure);c.ready=true;this.record('ROOT_HEARTBEAT_CADENCE_OBSERVED12',c);return structuredClone(c);}
 startReadOnlyDiscovery(){""")
patch(p,"heartbeatAgeMs:h?this.now()-h.at:null,", "heartbeatAgeMs:h?this.now()-h.at:null,heartbeatCadence12:this.heartbeatCadence12??null,firstFailure12:this.firstFailure12??null,failureTraceError12:this.failureTraceError12??null,")
p='product/main-session-codec09c.mjs'
patch(p," async function lifecycle(q){need(!closed,'PRODUCT_CLOSED');record('OPERATOR_LIFECYCLE_INTENT',q);const result=operators.lifecycle(q);await journal.flush();await payload.settled();return result;}",""" let lifecycleSequence12=0,lifecycleTraceRows12=0;const lifecycleTrace12=(stage,detail)=>{if(lifecycleTraceRows12>=64)return;record('OPERATOR_LIFECYCLE_STAGE12',{stage,...detail,nodeHostNs:String(process.hrtime.bigint()),hostClockDomain:'NODE_HRTIME_NS'});lifecycleTraceRows12++;};
 async function lifecycle(q){need(!closed,'PRODUCT_CLOSED');const sequence=++lifecycleSequence12,intent=record('OPERATOR_LIFECYCLE_INTENT',q),sample=q.action!=='heartbeat'||(sequence&(sequence-1))===0;return awaitLifecycle12({q,intent,operators,journal,payload,trace:(stage,detail)=>{if(sample)lifecycleTrace12(stage,{sequence,action:q.action,instance:q.instance,...detail});}});}""")
pth=ROOT/p;s=pth.read_text();s+='''\n/** Heartbeat has no payload mutation; its own original intent must be durable. */
export async function awaitLifecycle12({q,intent,operators,journal,payload,trace=()=>{}}){
 trace('REQUEST',{intentSequence:intent.n});
 if(payload.fatal)throw Error(payload.fatal);
 const result=operators.lifecycle(q);trace('ACTION_RETURN',{active:result.active,epoch:result.epoch});
 const receipt=await journal.flush();need(receipt?.durable===true&&receipt.throughSequence>=intent.n,'LIFECYCLE_OWN_INTENT_DURABILITY12');trace('OWN_INTENT_DURABLE',{throughSequence:receipt.throughSequence});
 if(q.action!=='heartbeat'){await payload.settled();trace('PAYLOAD_SETTLED',{});}else{if(payload.fatal)throw Error(payload.fatal);operators.assert({...q,clientInstance:q.instance});trace('HEARTBEAT_UNRELATED_PAYLOAD_NOT_AWAITED',{});}
 trace('REPLY_READY',{active:result.active,epoch:result.epoch});return result;
}
''';pth.write_text(s)
p='runtime/scene-feed.mjs'
patch(p,"verifyFrameClaim(claim){", "verifyFrameClaim(claim,{stage='UNSPECIFIED'}={}){")
patch(p,"need(age>=0&&age<=250,'SCENE_CLAIM_ORIGINAL_AGE250');", "if(!(age>=0&&age<=250)){const error=Error('SCENE_CLAIM_ORIGINAL_AGE250');error.ageDetail12={stage:String(stage).slice(0,64),frame:claim.frame,context:structuredClone(row.frame.context),rootOriginalAgeMs:Number(BigInt(row.frame.rootNowNs)-BigInt(row.frame.sampleHostNs))/1e6,rootRPCRoundtripMs:row.fullRoundtripMs,nodeRegistryResidenceMs:now-row.receivedAt,totalAgeUpperMs:age,rootClockDomain:'PYTHON_ROOT_MONOTONIC_NS',relayClockDomain:'NODE_HRTIME_NS',crossClockArithmetic:'DURATIONS_ONLY_NO_RAW_DOMAIN_COMPARISON',maximumMs:250};throw error;}")
p='runtime/product-companion-codec09.mjs'
patch(p,"frameProofValidator:claim=>({...scene.verifyFrameClaim(claim),camera:host.session.verifyCameraClaim(claim)})", "frameProofValidator:(claim,stage)=>({...scene.verifyFrameClaim(claim,{stage}),camera:host.session.verifyCameraClaim(claim)})")
p='product/media-server-codec09.mjs'
patch(p,"function verifyFrame(metadata){", "function verifyFrame(metadata,stage='UNSPECIFIED'){")
patch(p,"return frameProofValidator({...metadata,positionNedM:metadata.aircraftPositionNedM,quaternionWxyz:metadata.aircraftQuaternionWxyz});", "try{return frameProofValidator({...metadata,positionNedM:metadata.aircraftPositionNedM,quaternionWxyz:metadata.aircraftQuaternionWxyz},stage);}catch(e){if(e.ageDetail12&&!firstMediaFailure12){firstMediaFailure12={reason:e.message,detail:e.ageDetail12,nodeHostNs:String(process.hrtime.bigint()),clockDomain:'NODE_HRTIME_NS',authorityRestorable:false};clockJournal.append('ORIGINAL_MEDIA_FIRST_FAILURE12',firstMediaFailure12);}throw e;}")
patch(p,"let publisherCounters=null", "let firstMediaFailure12=null;let publisherCounters=null")
patch(p,"videoReadiness:requiredVideoReadiness(),", "videoReadiness:requiredVideoReadiness(),firstMediaFailure12,")
patch(p,"verifyFrame(frameProof.metadata);", "verifyFrame(frameProof.metadata,'CHUNK_ARRIVAL');")
patch(p,"const proof=verifyFrame(metadata);", "const proof=verifyFrame(metadata,'PROOF_PRE_DURABLE');")
patch(p,"for(const r of staged)r.proof=verifyFrame(r.metadata);", "for(const r of staged)r.proof=verifyFrame(r.metadata,'PROOF_POST_DURABLE');")
p='product/beta-client-codec09.mjs'
patch(p,"function invalidateLocal(reason){fence.invalidate();", "let firstInvalidation12=null;function invalidateLocal(reason,origin='LOCAL_POLICY'){firstInvalidation12??=Object.freeze({reason:String(reason).slice(0,180),origin,browserMs:performance.now(),clockDomain:'BROWSER_PERFORMANCE_MS'});fence.invalidate();")
patch(p,"window.field02Lifecycle?.('background');", "window.field02Lifecycle?.('background',{origin,reason:String(reason).slice(0,180)});")
patch(p,"invalidateLocal(reason);if(old?.active)", "invalidateLocal(reason,reason);if(old?.active)")
patch(p,"video:media?.state()?.collection??null,", "video:media?.state()?.collection??null,videoLifecycle12:media?.state()?.lifecycle12??null,firstInvalidation12,")
p='product/media-panel.mjs'
patch(p,"collection=null;", "collection=null,firstStop12=null,startAttempt12=0,startPhase12='NOT_STARTED';")
patch(p,"function stop(reason){foreground=false;", "function stop(reason){firstStop12??=Object.freeze({reason:String(reason).slice(0,180),browserMs:performance.now(),clockDomain:'BROWSER_PERFORMANCE_MS'});startPhase12='TERMINAL_STOPPED';foreground=false;")
patch(p,"const lifecycle=event=>{if(event==='background'||event==='stop')stop('MEDIA_NATIVE_'+event.toUpperCase());", "const lifecycle=(event,detail)=>{if(event==='background'||event==='stop')stop(detail?.reason?'MEDIA_INVALIDATED:'+detail.origin+':'+detail.reason:'MEDIA_NATIVE_'+event.toUpperCase());")
patch(p,"return oldLife?.(event);", "return oldLife?.(event,detail);")
patch(p,"const local=lifeEpoch;await viewer.start();", "const local=lifeEpoch;startAttempt12++;startPhase12='STARTING';try{await viewer.start();}catch(e){startPhase12='TERMINAL_START_FAILED';firstStop12??=Object.freeze({reason:String(e.message).slice(0,180),browserMs:performance.now(),clockDomain:'BROWSER_PERFORMANCE_MS'});throw e;}")
patch(p,"viewerState=viewer.state();notice('Đang nhận nguồn host.", "viewerState=viewer.state();startPhase12='STARTED_WAIT_QUALIFIED_PREVIEW';notice('Đang nhận nguồn host.")
# Projection exposes actual viewer/readiness separately from collection. It does not enable anything.
patch(p,"return{viewer:viewer.state(),", "return{lifecycle12:{startAttempt:startAttempt12,startPhase:startPhase12,firstStop:firstStop12,viewer:viewer.state(),previewReady:!!(foreground&&viewer.getPreview()),terminal:!!firstStop12},viewer:viewer.state(),")
print('patched explicit static files; no actors')
