// Deterministic DOM/bridge doubles. No browser, Android, server or flight runtime.
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm'; import crypto from 'node:crypto';
const root=process.cwd(), assets=path.join(root,'native/betaintegrated01/cockpit03/assets');
const html=fs.readFileSync(path.join(assets,'index.html'),'utf8');
function harness(){
 let writes=0, clock=0, timer=0;const raf=[], timers=new Map(), intervals=[], requests=[],nodes=new Map();
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
 const context={requestAnimationFrame:f=>raf.push(f),document:doc,performance:{now:()=>clock},console,setTimeout:f=>{timers.set(++timer,f);return timer;},clearTimeout:id=>timers.delete(id),setInterval:f=>{intervals.push(f);return intervals.length;}};
 context.window=context;context.AerisWorkspace={post:json=>requests.push(JSON.parse(json))};vm.createContext(context);
 vm.runInContext(fs.readFileSync(path.join(assets,'model.js'),'utf8'),context);
 vm.runInContext(fs.readFileSync(path.join(assets,'app.js'),'utf8'),context);
 return{frame:()=>{const q=raf.splice(0);q.forEach(f=>f());},context,nodes,requests,body,receive:x=>context.AerisCockpit.receive(x),tick:()=>{clock+=200;for(const f of intervals)f();},writes:()=>writes,clock:()=>clock,setClock:x=>clock=x};
}

const tests=[];function check(id,pass){tests.push({id,pass});}const h=harness();const workspace={draft:null,draftSHA256:null,reviews:[],authorityRestorable:false};const d=(v,t)=>({chosenView:v,viewEpoch:7,workspace:structuredClone(workspace),native:null,nowElapsedNs:t,nativeObservedElapsedNs:t,noMedia:true,trajectory:[]});const r=(id,type,view,t)=>({version:1,id,viewEpoch:7,type,ok:true,data:d(view,t),error:null});h.receive(r('BOOT','LOAD','survey',10000000000));check('beforeRAF_no_ack',h.requests.length===0);h.frame();check('firstRAF_no_ack',h.requests.length===0);h.frame();check('secondRAF_readonlySTATE',h.requests.length===1&&h.requests[0].type==='STATE'&&h.requests[0].payload.renderedView==='survey');let a=h.requests.at(-1);h.receive(r(a.id,'STATE','survey',10000000001));h.nodes.get('nav-preflight').click();let nav=h.requests.at(-1);h.receive(r(nav.id,'NAVIGATE','preflight',10000000002));h.receive(r('PUSH','STATE','fly',10000000003));let n=h.requests.length;h.frame();h.frame();check('late_oldviewRAF_canceled',h.requests.length===n+1&&h.requests.at(-1).payload.renderedView==='fly');a=h.requests.at(-1);h.receive(r(a.id,'STATE','fly',10000000004));n=h.requests.length;h.receive(r('PUSH','STATE','fly',10000000005));h.frame();h.frame();check('ordinary_sameFlyPUSH_noAckOrReset',h.requests.length===n);h.receive({...r('PUSH','STATE','review',10000000006),viewEpoch:8});h.frame();h.frame();check('foreignEpoch_noAck',h.requests.length===n&&h.body.dataset.view==='fly');check('noFlightAPI_fromACK',h.requests.every(x=>['STATE','NAVIGATE'].includes(x.type)));const pins=Object.fromEntries(['app.js','model.js','cockpit.css','index.html'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(assets,n))).digest('hex')]));const out=path.join(root,'evidence/betaintegrated01-m1cockpit03/qa/presentation-ui01.json');fs.writeFileSync(out,JSON.stringify({status:tests.every(x=>x.pass)?'PASS_DOM_DOUBLE_NOT_RENDERED':'FAIL',tests,pins,servicesStarted:0,scope:'Actual JavaScript, explicit RAF queue in DOMdouble. Does not claim compositor visual atomicity or actual Android.'},null,2));console.log(JSON.stringify(tests));
