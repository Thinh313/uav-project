// Deterministic DOM/bridge doubles. No browser, Android, server or flight runtime.
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import crypto from 'node:crypto';
const root=process.cwd(), assets=path.join(root,'planning/betaintegrated01/cockpit05-ui/assets');
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
const tests=[];function check(name,ok){if(!ok)throw Error(name);tests.push({name,pass:true});}
const baseWS={draft:null,draftSHA256:null,reviews:[],authorityRestorable:false};
function payload(view='survey',ws=baseWS,n=10000000000){return{chosenView:view,viewEpoch:19,workspace:structuredClone(ws),native:{format:'NO_SESSION'},ownerActive:false,nowElapsedNs:n,nativeObservedElapsedNs:n,noMedia:true,trajectory:[]};}
function reply(id,type,data,ok=true,error=null,epoch=19){return{version:1,id,type,data,ok,error,viewEpoch:epoch};}
const h=harness();h.receive(reply('BOOT','LOAD',payload()));h.frame();h.frame();let ack=h.requests.at(-1);h.receive(reply(ack.id,'STATE',payload('survey',baseWS,10000000001)));
check('NO_SESSION_no_fake_ARM_or_owner',h.context.AerisUIModel.telemetry(payload(),0).fresh===false&&h.context.AerisUIModel.telemetry(payload(),0).position===null);
const sun=h.nodes.get('theme-icon').getAttribute('href');h.nodes.get('theme').click();check('day_has_moon_action_icon',sun==='#i-sun'&&h.body.dataset.theme==='day'&&h.nodes.get('theme-icon').getAttribute('href')==='#i-moon');h.nodes.get('theme').click();check('night_has_sun_action_icon',h.body.dataset.theme==='night'&&h.nodes.get('theme-icon').getAttribute('href')==='#i-sun');
const review=(id,status,hash)=>({id,run:id,epoch:'mock-e',boot:'mock-b',surveyRevision:1,surveySHA256:'a'.repeat(64),status,nativeTerminalSHA256:hash.repeat(64),groundDistinctFreshGroups:0,actualImages:0,completionClaim:false,coverageClaim:false,authorityRestorable:false});
const older=review('MOCK-FAILED','FAILED','b'),newer=review('MOCK-PENDING','PENDING_NATIVE_TERMINAL_OR_VERIFICATION','c');const ws={...baseWS,reviews:[older,newer]};
h.receive(reply('PUSH','STATE',payload('review',ws,11000000000)));let buttons=h.nodes.get('review-list').children;check('exact_one_current_row',buttons.filter(x=>x.getAttribute('aria-current')==='true').length===1);check('initial_latest_summary_selected',buttons[1].getAttribute('aria-current')==='true');check('checkmark_is_independent_noncolour_selection',buttons[1].children.at(-1).tagName==='svg'&&buttons[1].children.at(-1).getAttribute('aria-hidden')==='true');check('review_metadata_and_pending_notice_retained',h.nodes.get('review-detail').textContent.includes('Chờ đóng / kiểm hồ sơ')&&buttons[1].textContent.includes('Khảo sát r1'));
// Complete auto-request before explicit selection, then prove click cannot invent success.
let req=h.requests.at(-1);h.receive(reply(req.id,'REVIEWS',payload('review',ws,11000000001)));buttons=h.nodes.get('review-list').children;buttons[0].click();req=h.requests.at(-1);check('select_requires_native_REVIEWS_ack',req.type==='REVIEWS'&&req.payload.id==='MOCK-FAILED'&&buttons[1].getAttribute('aria-current')==='true');
const accepted=payload('review',ws,12000000000);accepted.selectedReview={...older,trajectory:[]};h.receive(reply(req.id,'REVIEWS',accepted));buttons=h.nodes.get('review-list').children;check('acked_old_failed_selected_with_accessible_current_name',buttons[0].getAttribute('aria-current')==='true'&&buttons[0].getAttribute('aria-label')==='Đang xem hồ sơ MOCK-FAILED'&&buttons[1].getAttribute('aria-current')==='false');check('failed_notice_not_suppressed_by_visual_cleanup',h.nodes.get('review-detail').textContent.includes('Đã đóng do lỗi · hồ sơ được giữ')&&h.nodes.get('review-detail').textContent.includes('không khẳng định đã bay AUTO'));
h.receive(reply('PUSH','STATE',null,false,'MOCK: workspace quota denied'));check('native_failure_message_visible_and_text_exact',h.nodes.get('ui-message').hidden===false&&h.nodes.get('ui-message').textContent==='MOCK: workspace quota denied');h.receive(reply('PUSH','STATE',null,false,'STALE: must not replace',18));check('stale_epoch_cannot_replace_current_notice',h.nodes.get('ui-message').textContent==='MOCK: workspace quota denied');check('error_does_not_clear_accepted_selection',h.nodes.get('review-list').children[0].getAttribute('aria-current')==='true');
const css=fs.readFileSync(path.join(assets,'cockpit.css'),'utf8');check('three_decorative_leading_patterns_absent',!css.includes('inset 2px 0 var(--gold)')&&!css.includes('border-left:2px solid var(--gold)')&&!css.includes('[aria-current=page]:before'));check('flat_row_icon_notice_short_center_nav_present',css.includes('border-radius:2px;background:transparent;box-shadow:none')&&css.includes('.notice-icon{width:20px;height:20px')&&css.includes('left:calc(50% - 10px);bottom:4px;width:20px;height:2px'));check('information_icon_does_not_replace_notice_text',html.includes('role="note"')&&html.includes('id="preflight-reason"')&&html.includes('href="#i-info"'));
check('strict_narrow_post_no_flight_api',h.requests.every(r=>['LOAD','SAVE_DRAFT','NAVIGATE','STATE','REVIEWS'].includes(r.type)&&!('command'in r.payload)&&!('authority'in r.payload)));
const output=path.join(root,'evidence/betaintegrated01-cockpit05-native/qa/ui05-mock01.json');fs.writeFileSync(output,JSON.stringify({status:'PASS_DOM_DOUBLE_ONLY_NATIVE_ANDROID_PENDING',tests,sourceSHA256:Object.fromEntries(['index.html','cockpit.css','model.js','app.js'].map(n=>[path.relative(root,path.join(assets,n)),crypto.createHash('sha256').update(fs.readFileSync(path.join(assets,n))).digest('hex')])),scope:'Independent scenarios over reused deterministic DOM mechanics; mock states explicitly labelled; no Android/browser/flight proof.',servicesStarted:0},null,2)+'\n');console.log(JSON.stringify({status:'PASS',groups:tests.length}));
