import fs from'node:fs';import path from'node:path';import{createHash}from'node:crypto';import {Flight01}from'./flight01.mjs';import{Takeoff01,TAKEOFF_RULE}from'./takeoff01.mjs';
const digest=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
export class Flight02 extends Flight01 {
 pins(){const base=super.pins(),extra=JSON.parse(fs.readFileSync(this.evidenceRoot+'/source-pins-flight02.json'));for(const[n,h]of Object.entries(extra.files))if(digest(path.join(this.root,n))!==h)throw Error('FIELD02_SOURCE_PIN:'+n);return{...base,files:{...base.files,...extra.files},successor:extra.format};}
 observe(link,run){super.observe(link,run);const t=new Takeoff01(link.plan),record=link.record.bind(link),process=link.process63.bind(link),completion=link.completion.bind(link);let rxMeta=null,recorded=false;
  link.record=(kind,data)=>{const row=record(kind,data),meta={record:row.n,hostMonoMs:Number(BigInt(row.hostNs))/1e6};if(kind==='RX_RAW')rxMeta=meta;if(kind==='TX_RAW'&&data.id===76&&data.fields?.command===176&&data.fields.param2===3)t.begin(meta,link.boundHome);return row;};
  link.process63=m=>{const value=process(m);if(rxMeta)t.feed(m,rxMeta);if(t.view().valid&&!recorded){recorded=true;link.record('FIELD02_TAKEOFF_DERIVED_PROOF',t.view().proof);}return value;};
  link.completion=()=>{const base=completion(),v=t.view(),missing=base.missingNavigation.filter(n=>!(n===1&&v.valid));return{...base,completionRule:TAKEOFF_RULE,takeoffEvidence:v,takeoffAlternativeUsed:base.missingNavigation.includes(1)&&v.valid,missingNavigation:missing,originalMissingNavigation:base.missingNavigation,complete:base.complete||!!(v.valid&&!link.failure&&missing.length===0&&base.autoObserved&&base.expectedTerminalRTL&&base.groundDisarmed&&base.nearHome&&link.freshness(0,1500)&&link.freshness(33,1500)&&link.freshness(245,1500))};};
 }
}
