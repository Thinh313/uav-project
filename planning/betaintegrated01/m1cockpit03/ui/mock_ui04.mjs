// Deterministic DOM/bridge doubles. No browser, Android, server or flight runtime.
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import crypto from 'node:crypto';
const root=process.cwd(), assets=path.join(root,'native/betaintegrated01/cockpit03/assets');
const html=fs.readFileSync(path.join(assets,'index.html'),'utf8');
function harness(){
 let writes=0, clock=0, timer=0;const timers=new Map(), intervals=[], frames=[], requests=[],nodes=new Map();
 class Element{
  constructor(tag='div'){this.tagName=tag;this.attrs={};this.dataset={};this.children=[];this.events={};this._text='';this._hidden=false;this._disabled=false;this.value='';this.classes=new Set();this.classList={toggle:(key,force)=>{const next=force??!this.classes.has(key);if(next!==this.classes.has(key)){writes++;next?this.classes.add(key):this.classes.delete(key);}},contains:key=>this.classes.has(key)};}
  set textContent(v){writes++;this._text=String(v);this.children=[];}get textContent(){return this.children.length?this.children.map(c=>c.textContent).join(''):this._text;}
  set hidden(v){if(this._hidden!==!!v)writes++;this._hidden=!!v;}get hidden(){return this._hidden;}
  set disabled(v){if(this._disabled!==!!v)writes++;this._disabled=!!v;}get disabled(){return this._disabled;}
  set innerHTML(v){throw new Error('Unsafe HTML interpolation');}
  setAttribute(k,v){if(this.attrs[k]!==String(v))writes++;this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]??null;}hasAttribute(k){return k in this.attrs;}removeAttribute(k){if(k in this.attrs)writes++;delete this.attrs[k];}
  replaceChildren(...c){writes++;this.children=c;this._text='';}append(...c){writes++;this.children.push(...c);}
  addEventListener(k,f){(this.events[k]??=[]).push(f);}click(extra={}){if(!this.disabled)for(const f of this.events.click??[])f({clientX:700,clientY:300,...extra});}
  emit(k){for(const f of this.events[k]??[])f({});}getBoundingClientRect(){return{left:0,top:0,width:1280,height:800};}
 }
 for(const match of html.matchAll(/<([a-z][a-z0-9-]*)\b[^>]*\bid="([^"]+)"[^>]*>/g)){
  const node=new Element(match[1]);node.id=match[2];nodes.set(node.id,node);
  const nav=/data-nav="([^"]+)"/.exec(match[0]);if(nav)node.dataset.nav=nav[1];
  const value=/\bvalue="([^"]*)"/.exec(match[0]);if(value)node.value=value[1];
  if(/\bhidden(?:\s|>)/.test(match[0])){node.hidden=true;node.setAttribute('hidden','');}
 }
 nodes.get('draft-type').value='polygon';
 const body=new Element('body');body.dataset={theme:'night',view:'survey'};
 const doc={body,getElementById:id=>{if(!nodes.has(id))throw new Error('MissingDOM:'+id);return nodes.get(id);},querySelectorAll:q=>q==='[data-nav]'?[...nodes.values()].filter(n=>n.dataset.nav):[],createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),createTextNode:v=>({textContent:String(v)})};
 const context={document:doc,performance:{now:()=>clock},console,setTimeout:f=>{timers.set(++timer,f);return timer;},clearTimeout:id=>timers.delete(id),requestAnimationFrame:f=>{frames.push(f);return frames.length;},setInterval:f=>{intervals.push(f);return intervals.length;}};
 context.window=context;context.AerisWorkspace={post:json=>requests.push(JSON.parse(json))};vm.createContext(context);
 vm.runInContext(fs.readFileSync(path.join(assets,'model.js'),'utf8'),context);
 vm.runInContext(fs.readFileSync(path.join(assets,'app.js'),'utf8'),context);
 return{context,nodes,requests,body,receive:x=>context.AerisCockpit.receive(x),tick:()=>{clock+=200;for(const f of intervals)f();},frame:()=>{clock+=16;const ready=frames.splice(0);for(const f of ready)f(clock);},writes:()=>writes,clock:()=>clock,setClock:x=>clock=x};
}
const tests=[];function check(name,truth){if(!truth)throw new Error(name);tests.push({case:name,status:'PASS'});}
const h=harness(), M=h.context.AerisUIModel;
const draft={version:1,id:'survey-unit',revision:1,kind:'polygon',name:'Khảo sát <b>không phải HTML</b>',datum:'WGS84',altitudeDatum:'RELATIVE_HOME',units:'m',geometry:[[10.854,106.807],[10.8541,106.807],[10.854,106.8071]],altitudeM:3,corridorWidthM:10,trainingOnly:true};
const workspace={draft:null,draftSHA256:null,reviews:[],authorityRestorable:false};
function data(view='survey',native={format:'NO_SESSION'},ws=workspace,now=10000000000){return{chosenView:view,viewEpoch:7,workspace:structuredClone(ws),native,nowElapsedNs:now,nativeObservedElapsedNs:now,noMedia:true,trajectory:[]};}
function response(id,type,d,ok=true,error=null){return{version:1,id,viewEpoch:7,type,ok,data:d,error};}
h.receive(response('BOOT','LOAD',data()));check('BOOT_loads_native_epoch_only',h.body.dataset.view==='survey');
for(const [button,next]of[['nav-preflight','preflight'],['nav-fly','fly'],['nav-review','review']]){
 h.nodes.get(button).click();const req=h.requests.at(-1);check('nav_'+next+'_not_optimistic',h.body.dataset.view!==next);
 h.receive(response(req.id,'NAVIGATE',data(next,undefined,workspace,10000000001+h.requests.length)));check('nav_'+next+'_accepted_only',h.body.dataset.view===next);
}
check('no_session_Fly_allows_exit',h.nodes.get('nav-review').disabled===false);
check('only_narrow_native_bridge_types',h.requests.every(r=>M.TYPES.includes(r.type)&&!('command'in r.payload)));
const before=h.writes();for(let i=0;i<5;i++)h.tick();check('NO_SESSION_local_tick_zero_DOM_churn',h.writes()===before);
h.receive(response('PUSH','STATE',data('survey',undefined,workspace,11000000000)));
const beforePush=h.writes();h.receive(response('PUSH','STATE',data('survey',undefined,workspace,11000000001)));check('unchanged_NO_SESSION_push_zero_DOM_churn',h.writes()===beforePush);
h.nodes.get('draft-name').value='Khảo sát thử';h.nodes.get('draft-name').emit('input');h.nodes.get('draft-example').click();h.nodes.get('draft-save').click();const save=h.requests.at(-1);check('save_validated_revision0_geometry',save.type==='SAVE_DRAFT'&&save.payload.revision===0&&save.payload.geometry.length===4);
const saved={...draft,name:'Khảo sát thử',geometry:save.payload.geometry};const savedWS={...workspace,draft:saved,draftSHA256:'a'.repeat(64)};
h.receive(response(save.id,'SAVE_DRAFT',data('survey',undefined,savedWS,12000000000)));check('native_save_ack_displays_SHA',h.nodes.get('preflight-draft-sha').textContent==='a'.repeat(64));
h.nodes.get('nav-preflight').click();let nav=h.requests.at(-1);h.receive(response(nav.id,'NAVIGATE',data('preflight',undefined,savedWS,12000000001)));check('saved_revision_persists_across_view',h.nodes.get('preflight-draft-revision').textContent.includes('Revision 1'));
h.nodes.get('nav-fly').click();nav=h.requests.at(-1);const active={run:'r',epoch:'e',closed:false,input:{consent:true},flight:{armed:true}};h.receive(response(nav.id,'NAVIGATE',data('fly',active,savedWS,12000000002)));check('active_owner_Fly_locked_until_close',h.nodes.get('nav-review').disabled===true);
h.receive(response('foreign','STATE',data('review',null,workspace,13000000000)));check('unsolicited_callback_rejected',h.body.dataset.view==='fly');h.receive({...response('PUSH','STATE',data('review',null,workspace,13000000000)),viewEpoch:6});check('old_epoch_callback_rejected',h.body.dataset.view==='fly');h.receive(response('PUSH','STATE',data('review',null,workspace,1)));check('stale_push_doesnot_navigate',h.body.dataset.view==='fly');
h.nodes.get('theme').click();check('theme_sun_changes_to_moon',h.nodes.get('theme-icon').getAttribute('href')==='#i-moon'&&h.nodes.get('theme').getAttribute('aria-label').includes('tối'));
h.nodes.get('theme').click();check('theme_moon_changes_to_sun',h.nodes.get('theme-icon').getAttribute('href')==='#i-sun');
const f={firmwareObserved:true,positionMs:9900,heartbeatMs:9900,lat:0,lon:0,home:{latE7:0,lonE7:0,altMSLmm:0},relativeAltitudeM:0,horizontalSpeedMps:0,GPSFix:6,satellites:10,GPSHDOP100:121,batteryWireMillivolts:24000,mode:5};
const good=data('fly',{closed:false,flight:f});check('qualified_numeric_zero_is_valid',M.telemetry(good,0).fresh&&M.telemetry(good,0).altitude===0&&M.telemetry(good,0).distance===0);
check('startup00_withoutGPS_is_unknown',M.telemetry(data('fly',{flight:{...f,GPSFix:0,satellites:0}}),0).position===null);
check('stale_position_is_unknown',M.telemetry(good,1600).position===null);check('closed_native_not_active_telemetry',M.telemetry(data('fly',{closed:true,flight:f}),0).position===null);
check('unknown_remains_unknown',M.telemetry(null,0).mode===null);
for(const [name,input]of[['foreignDatum',{...draft,datum:'AGL'}],['nonfinite',{...draft,geometry:[[NaN,0],[1,1],[2,2]]}],['tooHigh',{...draft,altitudeM:6}],['tooMany',{...draft,geometry:Array(65).fill([1,1])}],['degenerate',{...draft,geometry:[[1,1],[1,1],[1,1]]}]]){
 let rejected=false;try{M.validateDraft(input);}catch{rejected=true;}check('draft_'+name+'_rejected',rejected);
}
check('valid_corridor_supported',M.validateDraft({...draft,kind:'corridor',geometry:[[0,0],[0,.0001]]}).kind==='corridor');
check('review_never_promotes_ground_to_complete',M.reviewStatus({status:'NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION',completionClaim:false,coverageClaim:false,authorityRestorable:false,actualImages:0}).includes('chờ đối chiếu'));
check('pending_review_never_says_closed',M.reviewStatus({status:'PENDING_NATIVE_TERMINAL_OR_VERIFICATION',completionClaim:false,authorityRestorable:false,actualImages:0})==='Chờ đóng / kiểm hồ sơ');
const sample=(t,extra={})=>({nativeRecordNs:t,lat:10.854,lon:106.807,armedWindow:true,positionQualified:true,...extra});
const track=M.trajectoryPath([sample(1,{lat:0,lon:0,armedWindow:false}),sample(100),sample(200),sample(300,{positionQualified:false}),sample(400),sample(3000000000)],M.referenceHome,.08,[720,370]);
check('startup_trajectory_not_drawn_and_gaps_break',track.shown===4&&track.excluded===2&&(track.path.match(/M/g)||[]).length===3);
const injection=harness();injection.receive(response('BOOT','LOAD',data('survey',null,{...workspace,draft,draftSHA256:'b'.repeat(64)})));check('imported_name_is_text_only',injection.nodes.get('preflight-draft-name').textContent===draft.name);
const newActivity=harness();newActivity.receive({...response('PUSH','STATE',good),viewEpoch:7});check('restart_ignores_old_push_beforeBOOT',newActivity.body.dataset.view==='survey');
for(const [name,mut]of[['future_position',x=>x.native.flight.positionMs=11000],['future_heartbeat',x=>x.native.flight.heartbeatMs=11000],['future_snapshot',x=>x.nativeObservedElapsedNs=11000000000]]){const x=structuredClone(good);mut(x);check(name+'_is_unknown',M.telemetry(x,0).fresh===false);}
const locked=harness();const lockedData=data('preflight',{run:'bound-r',epoch:'bound-e',closed:false,flight:{armed:false},input:{consent:false}},workspace);lockedData.ownerActive=true;locked.receive(response('BOOT','LOAD',lockedData));check('active_owner_edit_lock_before_arm',locked.nodes.get('draft-name').disabled===true&&locked.nodes.get('nav-survey').disabled===true&&locked.nodes.get('nav-fly').disabled===false);
const history=harness();const summary={id:'review-r',run:'review-r',epoch:'e',boot:'b',surveyRevision:1,surveySHA256:'a'.repeat(64),status:'NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION',nativeTerminalSHA256:'c'.repeat(64),groundDistinctFreshGroups:2,actualImages:0,completionClaim:false,coverageClaim:false,authorityRestorable:false};const historyWS={...savedWS,reviews:[summary]};history.receive(response('BOOT','LOAD',data('review',null,historyWS)));const detailReq=history.requests.at(-1);check('review_queries_bounded_selected_detail',detailReq.type==='REVIEWS'&&detailReq.payload.id==='review-r');const detailed=data('review',null,historyWS,12000000000);detailed.selectedReview={...summary,trajectory:[sample(1000),sample(2000)]};history.receive(response(detailReq.id,'REVIEWS',detailed));check('selected_detail_trajectory_rendered',history.nodes.get('actual-track').getAttribute('d').startsWith('M'));history.receive(response('PUSH','STATE',data('review',null,historyWS,13000000000)));check('thinPUSH_doesnot_clear_detail_cache',history.nodes.get('actual-track').getAttribute('d').startsWith('M'));
const homePreview=harness();homePreview.receive(response('BOOT','LOAD',data('fly',{format:'NO_SESSION'},workspace)));check('FlyNO_SESSION_has_no_blank_Home_underlay',homePreview.nodes.get('native-home-underlay').hidden===true);
const observed={run:'home-r',epoch:'home-e',closed:false,flight:{...f,homeHash:'d'.repeat(64)}};homePreview.receive(response('PUSH','STATE',data('fly',observed,workspace,14000000000)));check('observed_Home_hash_shows_underlay',homePreview.nodes.get('native-home-underlay').hidden===false);homePreview.receive(response('PUSH','STATE',data('preflight',observed,workspace,15000000000)));check('Home_underlay_remains_Flyonly',homePreview.nodes.get('native-home-underlay').hidden===true);
check('unknown_Home_hash_never_reveals_blank_box',M.observedHome(data('fly',{flight:{...f,homeHash:'unknown'}}))===false);
check('transparent_WebView_tap_highlight',fs.readFileSync(path.join(assets,'cockpit.css'),'utf8').includes('-webkit-tap-highlight-color:transparent'));
check('gold_focus_visible_retained',fs.readFileSync(path.join(assets,'cockpit.css'),'utf8').includes('outline:3px solid var(--gold)'));
const atomic=harness();atomic.receive(response('BOOT','LOAD',data('survey')));check('presentation_ACK_not_immediate',atomic.requests.length===0);atomic.frame();check('presentation_ACK_waits_two_RAF_double',atomic.requests.length===0);atomic.frame();check('BOOT_ACK_once_after_two_RAF',atomic.requests.length===1&&atomic.requests[0].type==='STATE'&&atomic.requests[0].payload.renderedView==='survey');const firstAck=atomic.requests[0];atomic.receive(response(firstAck.id,'STATE',data('survey',undefined,workspace,11000000000)));atomic.receive(response('PUSH','STATE',data('survey',undefined,workspace,12000000000)));atomic.frame();atomic.frame();check('same_view_PUSH_doesnot_ACK_loop',atomic.requests.length===1);
const race=harness();race.receive(response('BOOT','LOAD',data('survey')));race.nodes.get('nav-preflight').click();const raceNAV=race.requests[0];race.receive(response(raceNAV.id,'NAVIGATE',data('preflight',undefined,workspace,11000000000)));race.frame();race.frame();const raceAcks=race.requests.filter(r=>r.type==='STATE');check('stale_RAF_viewgeneration_cancelled',raceAcks.length===1&&raceAcks[0].payload.renderedView==='preflight');race.frame();race.frame();check('no_automatic_presentation_ACK_retry',race.requests.filter(r=>r.type==='STATE').length===1);
const out=path.join(root,'evidence/betaintegrated01-m1cockpit03/ui/mock04');fs.mkdirSync(out);
const sourceSHA256=Object.fromEntries(['index.html','cockpit.css','model.js','app.js'].map(n=>['native/betaintegrated01/cockpit03/assets/'+n,crypto.createHash('sha256').update(fs.readFileSync(path.join(assets,n))).digest('hex')]));
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({status:'PASS_DOM_DOUBLE_NOT_VISUAL',groups:tests.length,cases:tests,sourceSHA256,servicesStarted:0,AndroidStarts:0,scope:'DeterministicDOM/nativebridge doubles +modelpolicy; no browser/WebViewrender/GPU/visualQA claimed'},null,2)+'\n');console.log(JSON.stringify({status:'PASS',groups:tests.length}));
