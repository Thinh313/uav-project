// BETA06 generation02: bounded Android/host lifecycle, no automatic authority restoration.
let bootstrap,session=null,queue=Promise.resolve(),desiredForeground=!document.hidden,heartbeatPending=false;
const instance=new URL(location.href).searchParams.get('instance')??('browser-'+crypto.randomUUID());
const android=new URL(location.href).searchParams.get('android')==='field02';
const LIFE_DEADLINE_MS=1000,HEARTBEAT_CADENCE_MS=750,MAX_EVENTS=32,MAX_QUEUE=16;
let seq=0,requestSeq=0,queueDepth=0,lastTimerAt=performance.now(),lastTimerLagMs=0,maxTimerLagMs=0,lastError=null,lastEpoch=null,inflight=null;
const events=[],counts={started:0,acknowledged:0,failed:0,deadline:0};
const now=()=>performance.now();
function errorCode(e){if(e?.name==='SyntaxError')return'MALFORMED_JSON';if(e?.name==='AbortError')return'LIFECYCLE_REQUEST_ABORTED';if(e?.name==='TypeError')return'NETWORK_OR_TYPE_ERROR';const m=String(e?.message??'');return/^[A-Z][A-Z0-9_:.-]{0,95}$/.test(m)?m:'LIFECYCLE_UNKNOWN_ERROR';}
function record(kind,data={}){events.push({seq:++seq,atBrowserMs:now(),kind,...data});if(events.length>MAX_EVENTS)events.shift();}
function lose(reason){session=null;lastError=reason;record('LOCAL_SESSION_CLEARED',{reason});window.dispatchEvent(new Event('field02AuthorityLost'));}
window.field02LifecycleDiagnostics=()=>{const snapshot={format:'aeris-beta06g2-lifecycle-diagnostic/1',seq,desiredForeground,documentHidden:!!document.hidden,nativeForeground:window.FIELD02Environment?.foreground??null,localSessionActive:session?.active===true,clientEpoch:session?.epoch??lastEpoch,heartbeatPending,queueDepth,lastTimerLagMs,maxTimerLagMs,lastError,inflight:inflight?{...inflight,ageMs:Math.max(0,now()-inflight.startedAtBrowserMs)}:null,counts:{...counts},events:events.map(e=>({...e}))};while(JSON.stringify(snapshot).length>8192&&snapshot.events.length)snapshot.events.shift();return snapshot;};
async function bounded(action,operation){
 const requestId=++requestSeq,startedAtBrowserMs=now(),controller=new AbortController();let timer,finished=false,aborted=false;
 const abort=()=>{if(!aborted){aborted=true;controller.abort();}};
 const owner={requestId,action,startedAtBrowserMs,deadlineMs:LIFE_DEADLINE_MS};if(action!=='bootstrap')inflight=owner;counts.started++;record('REQUEST_BEGIN',{requestId,action,deadlineMs:LIFE_DEADLINE_MS});
 const timeout=new Promise((_,reject)=>{timer=setTimeout(()=>{if(finished)return;counts.deadline++;abort();reject(Error('LIFECYCLE_REQUEST_DEADLINE'));},LIFE_DEADLINE_MS);});
 // No session/cache mutation inside operation: ignored abort or late body resolution cannot commit.
 const work=Promise.resolve().then(()=>operation(controller.signal));
 try{const value=await Promise.race([work,timeout]);if(controller.signal.aborted||now()-startedAtBrowserMs>=LIFE_DEADLINE_MS){if(!aborted)counts.deadline++;abort();throw Error('LIFECYCLE_RESPONSE_AFTER_DEADLINE');}finished=true;counts.acknowledged++;record('REQUEST_ACK',{requestId,action,elapsedMs:Math.max(0,now()-startedAtBrowserMs)});return value;}
 catch(e){finished=true;counts.failed++;const reason=errorCode(e);lastError=reason;record('REQUEST_FAILED',{requestId,action,elapsedMs:Math.max(0,now()-startedAtBrowserMs),reason});throw Error(reason);}
 finally{finished=true;clearTimeout(timer);if(inflight?.requestId===requestId)inflight=null;}
}
const cfg=()=>bootstrap??=bounded('bootstrap',async signal=>{const r=await fetch('/api/bootstrap',{signal}),v=await r.json();if(!r.ok||!v?.ok||typeof v.csrf!=='string')throw Error('BOOTSTRAP_RESPONSE_REQUIRED');return v;}).catch(e=>{bootstrap=null;throw e;});
async function requestLife(action){
 const v=await bounded(action,async signal=>{const b=await cfg();if(signal.aborted)throw Error('LIFECYCLE_REQUEST_ABORTED');const q={action,instance,platform:android?'ANDROID_WEBVIEW':'HOST_BROWSER',...session&&{clientId:session.id,clientEpoch:session.epoch,clientInstance:instance}};const r=await fetch('/api/client-session',{method:'POST',headers:{'Content-Type':'application/json','X-Field-CSRF':b.csrf},body:JSON.stringify(q),signal}),value=await r.json();if(!r.ok||!value?.ok)throw Error(typeof value?.error==='string'?value.error:'LIFECYCLE_RESPONSE_REJECTED');const s=value.result;if(!s||typeof s.active!=='boolean'||!Number.isSafeInteger(s.epoch)||s.epoch<0)throw Error('LIFECYCLE_RESPONSE_SCHEMA');return s;});
 session=v;lastEpoch=v.epoch;return session;
}
function enqueue(fn,label){
 if(queueDepth>=MAX_QUEUE){desiredForeground=false;lose('LIFECYCLE_QUEUE_LIMIT');return Promise.reject(Error('LIFECYCLE_QUEUE_LIMIT'));}
 const queuedAt=now();queueDepth++;record('QUEUE_ENQUEUED',{action:label,queueDepth});const result=queue.then(async()=>{record('QUEUE_BEGIN',{action:label,waitMs:Math.max(0,now()-queuedAt)});try{return await fn();}finally{queueDepth--;record('QUEUE_END',{action:label,queueDepth});}});queue=result.catch(()=>{});return result;
}
window.field02Lifecycle=event=>{if(!['foreground','background','stop'].includes(event))return Promise.reject(Error('LIFECYCLE_EVENT_ALLOWLIST'));desiredForeground=event==='foreground';const wanted=event;record('LIFECYCLE_INTENT',{action:wanted,documentHidden:!!document.hidden,nativeForeground:window.FIELD02Environment?.foreground??null});return enqueue(async()=>{try{if(wanted==='foreground'){if(!desiredForeground)return;if(!session?.active)await requestLife('activate');if(!desiredForeground&&session?.active)await requestLife('background');}else if(session){await requestLife(wanted==='stop'?'stop':'background');}}catch(e){lose(errorCode(e));}},wanted);};
window.field02ClientContext=()=>{if(!desiredForeground||!session?.active)throw Error('Cần đưa ứng dụng về foreground và cấp quyền mới');return{clientId:session.id,clientEpoch:session.epoch,clientInstance:instance};};
window.fieldBootstrap01=async()=>{const b=await cfg();await window.field02Lifecycle(document.hidden?'background':'foreground');return b;};
window.Native82Bridge={environment86:()=>JSON.stringify({source:'mock',hardware:android?'FIELD02_ANDROID_WEBVIEW_HOST_COMPANION':'FIELD02_HOST_NOT_ANDROID',sdk:null,webview:android?'ANDROID_WEBVIEW':'HOST_BROWSER',hasHostToken:false}),reportUI86:()=>{},request:(id,action,expected,body)=>cfg().then(b=>fetch('/api/native82',{method:'POST',headers:{'Content-Type':'application/json','X-Field-CSRF':b.csrf},body:JSON.stringify({action,expected,body})})).then(r=>r.json()).then(r=>window.native82Result(id,JSON.stringify(r.result??r))).catch(e=>window.native82Result(id,JSON.stringify({ok:false,error:e.message})))};
setInterval(()=>{const tick=now();lastTimerLagMs=Math.max(0,tick-lastTimerAt-HEARTBEAT_CADENCE_MS);maxTimerLagMs=Math.max(maxTimerLagMs,lastTimerLagMs);lastTimerAt=tick;record('HEARTBEAT_TICK',{lagMs:lastTimerLagMs,skipped:heartbeatPending?'PENDING':!desiredForeground?'NOT_DESIRED':!session?.active?'NO_LOCAL_SESSION':document.hidden?'DOCUMENT_HIDDEN':null});if(heartbeatPending||!desiredForeground||!session?.active||document.hidden)return;heartbeatPending=true;enqueue(async()=>{if(!desiredForeground||!session?.active)return;try{await requestLife('heartbeat');if(!desiredForeground&&session?.active)await requestLife('background');}catch(e){lose(errorCode(e));}},'heartbeat').finally(()=>heartbeatPending=false).catch(()=>{});},HEARTBEAT_CADENCE_MS);
document.addEventListener('visibilitychange',()=>window.field02Lifecycle(document.hidden?'background':'foreground'));window.addEventListener('pagehide',()=>window.field02Lifecycle('stop'));
for(const name of ['error','unhandledrejection'])window.addEventListener(name,()=>{if(document.body?.dataset.fieldLoading==='true')document.body.dataset.fieldMessage='Không thể nạp workspace. Tải lại để kiểm tra nguồn dữ liệu.';});
