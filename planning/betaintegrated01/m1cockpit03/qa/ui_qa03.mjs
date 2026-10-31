// Deterministic DOM/bridge doubles. No browser, Android, server or flight runtime.
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import crypto from 'node:crypto';
const root=process.cwd(), assets=path.join(root,'native/betaintegrated01/cockpit03/assets');
const html=fs.readFileSync(path.join(assets,'index.html'),'utf8');
function harness(){
 let writes=0, clock=0, timer=0;const timers=new Map(), intervals=[], requests=[],nodes=new Map();
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
 const context={document:doc,performance:{now:()=>clock},console,setTimeout:f=>{timers.set(++timer,f);return timer;},clearTimeout:id=>timers.delete(id),setInterval:f=>{intervals.push(f);return intervals.length;}};
 context.window=context;context.AerisWorkspace={post:json=>requests.push(JSON.parse(json))};vm.createContext(context);
 vm.runInContext(fs.readFileSync(path.join(assets,'model.js'),'utf8'),context);
 vm.runInContext(fs.readFileSync(path.join(assets,'app.js'),'utf8'),context);
 return{context,nodes,requests,body,receive:x=>context.AerisCockpit.receive(x),tick:()=>{clock+=200;for(const f of intervals)f();},writes:()=>writes,clock:()=>clock,setClock:x=>clock=x};
}

const tests=[];function check(id,pass){tests.push({id,pass});}const h=harness(),M=h.context.AerisUIModel;
const workspace={draft:null,draftSHA256:null,reviews:[],authorityRestorable:false};
function d(native=null,now=10000000000){return{chosenView:'survey',viewEpoch:7,workspace:structuredClone(workspace),native,nowElapsedNs:now,nativeObservedElapsedNs:now,noMedia:true,trajectory:[]};}
const r=(id,type,data,ok=true)=>({version:1,id,viewEpoch:7,type,ok,data,error:'fail'});
h.receive(r('BOOT','LOAD',d()));h.nodes.get('nav-preflight').click();let req=h.requests.at(-1);h.receive(r(req.id,'STATE',{...d(),chosenView:'preflight'}));check('wrong_response_type_no_navigation',h.body.dataset.view==='survey');h.receive(r(req.id,'NAVIGATE',{...d(),chosenView:'preflight'}));check('accepted_matching_response_navigates',h.body.dataset.view==='preflight');
const f={firmwareObserved:true,positionMs:9900,heartbeatMs:9900,lat:0,lon:0,home:{latE7:0,lonE7:0,altMSLmm:0},relativeAltitudeM:0,horizontalSpeedMps:0,GPSFix:6,satellites:10,batteryWireMillivolts:24000,mode:5};
check('real_zero_coordinates_preserved',M.telemetry(d({closed:false,flight:f}),0).position?.[0]===0);
check('future_position_clock_unknown',!M.telemetry(d({closed:false,flight:{...f,positionMs:11000}}),0).fresh);
check('future_native_clock_unknown',!M.telemetry({...d({closed:false,flight:f}),nativeObservedElapsedNs:11000000000},0).fresh);
check('future_heartbeat_clock_unknown',!M.telemetry(d({closed:false,flight:{...f,heartbeatMs:11000}}),0).fresh);
check('closed_no_marker',M.telemetry(d({closed:true,flight:f}),0).position===null);
check('no_bridge_flight_types',!M.TYPES.some(t=>/ARM|LAND|CONTROL|COMMAND|CONSENT/.test(t)));
const hh=harness();const summary={id:'run',run:'run',nativeTerminalSHA256:'a'.repeat(64),status:'NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION',authorityRestorable:false,completionClaim:false,coverageClaim:false,actualImages:0,surveyRevision:1,surveySHA256:'b'.repeat(64)};const dd={...d(),chosenView:'review',workspace:{...workspace,reviews:[summary]}};hh.receive(r('BOOT','LOAD',dd));let rr=hh.requests.at(-1);check('review_summary_requests_bounded_detail',rr?.type==='REVIEWS'&&rr.payload.id==='run');const details={...summary,trajectory:[{nativeRecordNs:1,armedWindow:true,positionQualified:true,lat:10.854,lon:106.807,relativeAltitudeM:3},{nativeRecordNs:2,armedWindow:true,positionQualified:true,lat:10.85401,lon:106.807,relativeAltitudeM:3}]};hh.receive(r(rr.id,'REVIEWS',{...dd,selectedReview:details,nowElapsedNs:10000000001}));check('selected_detail_renders_trajectory',!!hh.nodes.get('actual-track').getAttribute('d'));hh.receive(r('PUSH','STATE',{...dd,nowElapsedNs:10000000002}));check('detail_cache_survives_summary_push',!!hh.nodes.get('actual-track').getAttribute('d'));const aa=harness();aa.receive(r('BOOT','LOAD',{...d({run:'r',epoch:'e',closed:false,input:{consent:false},flight:{armed:false}}),ownerActive:true}));check('all_active_owner_blocks_draft',aa.nodes.get('draft-save').disabled);
const fsources=['index.html','cockpit.css','model.js','app.js'];const sourceSHA256=Object.fromEntries(fsources.map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(assets,n))).digest('hex')]));const out=path.join(root,'evidence/betaintegrated01-m1cockpit03/qa/ui03');fs.mkdirSync(out);fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({status:tests.every(x=>x.pass)?'PASS':'FAIL',tests,sourceSHA256,scope:'Actual JavaScript in Builder DOM double, independent adversarial cases; not browser/Android visual QA',servicesStarted:0},null,2));console.log(JSON.stringify(tests));
