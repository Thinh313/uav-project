import{CONTRACT,EXERCISES,PROFILES}from'../../pilot/coach02/contract.mjs';import{createState,apply,effectiveView}from'../../pilot/coach02/engine.mjs';import{packageRows,verifyPackage,hash}from'../../pilot/coach02/journal.mjs';import{canonical}from'../../pilot/coach01/replay.mjs';
export function service(initialNow){let now=initialNow,hostLast=5000,offset=5000,serial=0,active=null;const runs=new Map(),received=new Map(),calls=[];let hold=false,release;
 const response=(x,status=200)=>new Response(JSON.stringify(x),{status,headers:{'Content-Type':'application/json'}});
 const append=(run,kind,data)=>{const row={n:run.rows.length+1,previous:run.head,kind,data};row.sha256=hash(canonical(row));run.head=row.sha256;run.rows.push(row);};
 const packed=run=>packageRows(run.rows,run.state.finished?{format:'manual02-durable-closure',sessionId:run.state.context.sessionId,head:run.head,rows:run.rows.length,authorityRestorable:false}:null);
 const server={calls,setNow(fn){now=fn;},get active(){return active;},get rows(){return active?.rows??[];},holdTick(){hold=true;},release(){release?.();},async fetcher(url,options={}){
  const route=url.replace('/api/training/','');calls.push({route,method:options.method??'GET'});const host=Math.max(hostLast+1,now()+offset);hostLast=host;
  if(route==='state')return response({csrf:'vm-csrf',hostBoot:'vm-server-clock',contract:CONTRACT,exercises:EXERCISES,profiles:PROFILES,active:active?effectiveView(active.state,host):null});
  if(route==='history')return response({runs:[...runs.values()].map(r=>({sessionId:r.state.context.sessionId,exerciseId:r.state.context.exerciseId,verdict:packed(r).review.verdict})),received:[...received].map(([id,p])=>({archiveId:id,sessionId:p.review.sessionId,verdict:p.review.verdict})),issues:[]});
  if(route.startsWith('package/'))return response(packed(runs.get(route.slice(8))));
  if(route.startsWith('received/'))return response(received.get(route.slice(9)));
  if(options.headers['X-Coach-CSRF']!=='vm-csrf')return response({error:'CSRF'},400);
  const d=JSON.parse(options.body);
  if(route==='start'){if(active&&!active.state.finished)return response({error:'CLOSE_ACTIVE_TRAINING'},400);offset=host-now();const context={...d,sessionId:'m'+(++serial).toString(16).padStart(32,'0'),hostBoot:'vm-server-clock'},challenge={nonce:'vm-q'+serial,t1:host,t2:host};active={state:createState(context,challenge,host),head:'0'.repeat(64),rows:[]};append(active,'START',{context,challenge,hostMs:host,contract:CONTRACT,profile:PROFILES[d.profileId],exercise:EXERCISES[d.exerciseId]});runs.set(context.sessionId,active);return response({context,challenge,state:effectiveView(active.state,host)});}
  if(route==='action'||route==='abandon'){if(hold&&d.kind==='tick'){hold=false;await new Promise(r=>release=r);}const action=route==='abandon'?{kind:'hostAbort',hostBoot:'vm-server-clock',reason:'OBSERVER_RESTART',observerClockId:d.sourceClockId}:d;if(action.kind==='challenge'){action.serverNonce='vm-next-q';action.t1=host;action.t2=host;}const r=apply(active.state,action,host);append(active,'ACTION',{hostMs:host,action,outcome:r.outcome,state:r.state});active.state=r.state;return response({...r.outcome,state:effectiveView(active.state,host),durableRecord:active.rows.length});}
  if(route==='import'){const checked=verifyPackage(Buffer.from(JSON.stringify(d)));received.set(d.sha256,d);return response({...checked,archiveId:d.sha256,activeRestored:false});}
  throw Error('VM_UNEXPECTED_ROUTE '+route);
 }};return server;
}
