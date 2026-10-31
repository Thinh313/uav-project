// Actual production module, controlled DOM: diagnostic work only, not an Android timing claim.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const root=new URL('../../../',import.meta.url);
const oldPath=new URL('evidence/operator01/build04-source-history/layout86.mjs',root);
const newPath=new URL('native/operator01/assets/layout86.mjs',root);
const old=fs.readFileSync(oldPath,'utf8'),current=fs.readFileSync(newPath,'utf8');
assert.equal(old.replace("document.addEventListener('paint84',()=>schedule());",''),current);
async function exercise(source){
 const listeners={document:new Map(),window:new Map()},raf=[],reports=[],calls={style:0,rect:0,hit:0,rpc:0};let now=1000;
 const rect={x:12,y:12,left:12,top:12,width:80,height:48,right:92,bottom:60};
 const body={dataset:{theme:'dark',view:'fly',scenario:'mock'},prepend(){}};
 const nodes=new Map();
 const node=key=>{if(!nodes.has(key))nodes.set(key,{id:key,textContent:key,hidden:false,disabled:false,type:'button',parentElement:null,scrollHeight:48,clientHeight:48,
  getBoundingClientRect(){calls.rect++;return rect;},closest(){return null;},contains(other){return this===other;},getAttribute(){return '#sun';},prepend(){}});return nodes.get(key);};
 const control=node('control');
 const add=(where)=>(name,fn)=>{const m=listeners[where];m.set(name,[...(m.get(name)??[]),fn]);};
 const document={body,hidden:false,activeElement:null,fonts:{ready:Promise.resolve()},createElement:()=>({}),
  querySelector:node,querySelectorAll:()=>[control],elementFromPoint(){calls.hit++;return control;},addEventListener:add('document')};
 const bridge={environment86:()=>JSON.stringify({sdk:33,webview:'mock',source:'mock',hasHostToken:false}),reportUI86:s=>reports.push(JSON.parse(s))};
 const window={Native82Bridge:bridge,addEventListener:add('window')};
 const context={document,window,CSS:{supports:()=>true},MutationObserver:class{observe(){}},performance:{now:()=>now},
  getComputedStyle:()=>{calls.style++;return{display:'block',visibility:'visible',overflow:'visible',overflowX:'visible',overflowY:'visible'};},
  requestAnimationFrame:fn=>raf.push(fn),setTimeout:fn=>fn(),innerWidth:1280,innerHeight:800,devicePixelRatio:1};
 vm.runInNewContext(source,context,{filename:'actual-layout86.mjs'});
 const drain=()=>{while(raf.length)raf.shift()();};
 await Promise.resolve();drain();
 const initial=reports.length;
 const before={...calls},beforeReports=reports.length;
 for(let i=0;i<100;i++){now+=300;for(const f of listeners.document.get('paint84')??[])f({});drain();}
 const idle={style:calls.style-before.style,rect:calls.rect-before.rect,hit:calls.hit-before.hit,reports:reports.length-beforeReports};
 const explicit=[];
 for(const [where,event] of [['document','click'],['document','change'],['document','scroll'],['window','resize'],['document','visibilitychange']]){
  now+=300;const n=reports.length;for(const f of listeners[where].get(event)??[])f({});drain();explicit.push({event,reports:reports.length-n});
 }
 // Insets use unchanged dedup semantics, but must still run a scan; no forced report for unchanged data.
 now+=300;const r=calls.rect;window.native86Insets(0,false);drain();
 return{initial,idle,explicit,insetsScanned:calls.rect>r,totalReports:reports.length,controlRpc:calls.rpc};
}
const before=await exercise(old),after=await exercise(current);
assert.equal(before.initial,1);assert.equal(after.initial,1);
assert(before.idle.rect>0);assert.equal(after.idle.rect,0);assert.equal(after.idle.style,0);assert.equal(after.idle.hit,0);
assert.deepEqual(before.explicit,after.explicit);assert(after.explicit.every(x=>x.reports===1));
assert(before.insetsScanned&&after.insetsScanned);assert.equal(after.controlRpc,0);
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
console.log(JSON.stringify({format:'operator01-ui-diagnostic-causal-cut',version:1,provenance:'ACTUAL_MODULE_CONTROLLED_DOM_NOT_ANDROID_TIMING',
 scope:'Only paint84 diagnostic capture listener removed; same explicit events, geometry schema, dedup, caps and bridge.',
 sources:{before:{path:oldPath.pathname,sha256:sha(old)},after:{path:newPath.pathname,sha256:sha(current)}},
 before,after,verdict:'PASS',limits:['Does not prove UI diagnostics sole cause of runtime stale heartbeat.','Does not measure Android filesystem or Java/WebView scheduling.','Raw frames, native WAL/fsync and flight guards not changed.']},null,2));
