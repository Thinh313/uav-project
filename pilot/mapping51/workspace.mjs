import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {clone,sha,seal,unseal,exact,OPTIONS,CAMERA} from './common.mjs';
import {compile} from './planner.mjs';
import {Machine,fixture} from './readiness.mjs';
export function parseKml(text){return new Promise((resolve,reject)=>{const c=spawn('python3',['-B',fileURLToPath(new URL('./kml.py',import.meta.url))],{stdio:['pipe','pipe','pipe']}),chunks=[];let bytes=0,err='';const timer=setTimeout(()=>{c.kill('SIGKILL');reject(Error('KML_PARSE_TIMEOUT'))},5000);c.on('error',e=>{clearTimeout(timer);reject(e)});c.stdout.on('data',b=>{bytes+=b.length;if(bytes>1048576)c.kill('SIGKILL');else chunks.push(b)});c.stderr.on('data',b=>err+=b.toString().slice(0,1000));c.on('exit',code=>{clearTimeout(timer);try{const r=JSON.parse(Buffer.concat(chunks).toString());if(code!==0||!r.ok)throw Error(r.error??err);resolve(r.document)}catch(e){reject(e)}});c.stdin.on('error',()=>{});c.stdin.end(JSON.stringify({text}));});}
export const context=()=>({sessionId:randomUUID(),bootId:randomUUID(),aircraftId:'mock-aircraft-01',clockId:randomUUID()});
export class Workspace{
 constructor(){this.source=null;this.document=null;this.featureId=null;this.options=clone(OPTIONS);this.camera=clone(CAMERA);this.machine=new Machine();}
 snapshot(){return clone({source:this.source,document:this.document,featureId:this.featureId,options:this.options,camera:this.camera,plan:this.machine.plan,machine:this.machine.snapshot()});}
 async apply(e){
  exact(e,'type,atMs,data','EVENT');if(!Number.isFinite(e.atMs)||e.atMs<0||e.atMs>1e12)throw Error('EVENT_CLOCK');
  const d=e.data,m=this.machine,t=e.atMs;
  if(e.type==='IMPORT_KML'){
   exact(d,'text','IMPORT');const doc=await parseKml(d.text);m.setPlan(null,t);this.source=d.text;this.document=doc;this.featureId=null;return;
  }
  if(e.type==='CONFIGURE'){
   exact(d,'featureId,options,camera','CONFIGURE');if(!this.document)throw Error('KML_REQUIRED');const p=compile(this.document,d.featureId,d.options,d.camera);m.setPlan(p,t);this.featureId=d.featureId;this.options=clone(d.options);this.camera=clone(d.camera);return;
  }
  if(e.type==='RESET') {exact(d,'','RESET');m.revoke('PROCESS_RESTART',t);m.ctx=null;m.observation=null;m.lastNow=null;return;}
  if(e.type==='CONNECT_MOCK'){exact(d,'context','CONNECT');if(!m.plan)throw Error('PLAN_REQUIRED');m.connect(d.context,t);return;}
  if(e.type==='OBSERVE'){exact(d,'observation','OBSERVE');m.observe(d.observation,t);return;}
  if(e.type==='REVIEW'){m.review(t,d);return;}
  if(e.type==='START'){exact(d,'','START');m.start(t);return;}
  if(e.type==='STEP'){exact(d,'kind','STEP');m.step(t,d.kind);return;}
  if(e.type==='CLOSE'){exact(d,'','CLOSE');m.close(t);return;}
  if(e.type==='TICK'){exact(d,'','TICK');m.tick(t);return;}
  throw Error('EVENT_UNKNOWN');
 }
}
export async function replay(records){
 if(!Array.isArray(records)||records.length>64)throw Error('JOURNAL_BOUND');const w=new Workspace();let prev='';
 for(let n=0;n<records.length;n++){
  const r=records[n];exact(r,'format,version,sequence,previous,event,stateSha256,sha256','RECORD');const body=unseal(r);
  if(r.format!=='aeris-mapping51-journal'||r.version!==1||r.sequence!==n+1||r.previous!==prev)throw Error('JOURNAL_CHAIN');await w.apply(r.event);if(sha(w.snapshot())!==r.stateSha256)throw Error('SEMANTIC_REPLAY_CHANGED');prev=r.sha256;
 }return w;
}
export function record(previous,event,w){return seal({format:'aeris-mapping51-journal',version:1,sequence:previous.length+1,previous:previous.at(-1)?.sha256??'',event:clone(event),stateSha256:sha(w.snapshot())});}
export function observedScenario(w,now,name){if(!w.machine.ctx||!w.machine.plan)throw Error('CONNECT_REQUIRED');return fixture(w.machine.plan,w.machine.ctx,now,name,(w.machine.observation?.sequence??0)+1);}
