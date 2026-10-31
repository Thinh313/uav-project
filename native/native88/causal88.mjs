// Additional offline causal check. Never opens a socket or changes run bytes.
import fs from'node:fs';import assert from'node:assert/strict';import{FullFramer}from'../../pilot/apstream40/wire.mjs';import{sha}from'../../pilot/auto63/compiler.mjs';
const E='evidence/native88',out=[];
for(const run of process.argv.slice(2)){
 assert(/^s[a-f0-9]{20}$/.test(run));const root=E+'/runs/'+run;
 function rows(name){let n=0,previous='';return fs.readFileSync(root+'/'+name,'utf8').trimEnd().split('\n').map(x=>{const r=JSON.parse(x),{sha256,...body}=r;assert(r.n===++n&&r.previous===previous&&sha(body)===sha256);previous=sha256;return r;});}
 const rr=rows('raw.jsonl'),or=rows('observer/raw.jsonl'),cut=or.find(x=>x.kind==='CHANNEL_CUT');assert(cut);
 const fr=new FullFramer(),frames=[];let started=false,prefix='';for(const r of or.filter(x=>x.kind==='UPSTREAM_RAW')){let b=Buffer.from(r.data.rawHex,'hex');if(!started){const i=b.findIndex(x=>x===253||x===254);prefix+=b.subarray(0,i<0?b.length:i).toString();assert(prefix.length<1024);if(i<0)continue;started=true;b=b.subarray(i);}for(const f of fr.push(b,r.n,r.n))if(f.system===42&&f.component===1)frames.push({...f,ns:BigInt(r.hostNs),n:r.n});}
 const before=frames.filter(f=>f.n<cut.n&&f.id===0).at(-1);assert(before?.fields.custom_mode===3&&(before.fields.base_mode&128));
 const failsafe=frames.find(f=>f.n>cut.n&&f.id===253&&/gcs.*failsafe|failsafe.*gcs/i.test(f.fields.text));const rtl=frames.find(f=>f.n>cut.n&&f.id===0&&f.fields.custom_mode===6);assert(failsafe&&rtl);
 const terminal=frames.find(f=>f.id===253&&/Mission: 15 RTL/.test(f.fields.text));
 const causal=failsafe.ns<=rtl.ns&&(!terminal||terminal.ns>failsafe.ns);
 const df=new FullFramer(),parameters=new Map();let rxStarted=false,rxPrefix='';for(const r of rr.filter(x=>x.kind==='RX_RAW')){let b=Buffer.from(r.data.rawHex,'hex');if(!rxStarted){const at=b.findIndex(x=>x===253||x===254);rxPrefix+=b.subarray(0,at<0?b.length:at).toString();assert(rxPrefix.length<1024);if(at<0)continue;rxStarted=true;b=b.subarray(at);}for(const f of df.push(b,r.n,r.n))if(f.id===22&&f.system===42&&f.component===1)parameters.set(f.fields.param_id,f.fields);}
 for(const[id,type,value]of[['FS_GCS_ENABLE',2,1],['FS_GCS_TIMEOUT',9,5],['FS_OPTIONS',6,16],['MAV_GCS_SYSID',4,255]]){const p=parameters.get(id);assert(p&&p.param_type===type&&p.param_value===value,id);}
 out.push({run,status:'PASS',lastHeartbeatBeforeCutMode:3,armedBeforeCut:true,failsafeToFirstRTLSeconds:Number(rtl.ns-failsafe.ns)/1e9,terminalMissionRTLBeforeFailsafe:!!terminal&&terminal.ns<failsafe.ns,causalFailsafeRTL:causal,typedFailsafeParameters:'MATCH',timestampResolution:'HOST_RECEIVE_CHUNK_NOT_AP_EVENT_TIMESTAMP',scope:causal?'GCS_FAILSAFE_AND_RTL_SAME_OR_LATER_CHUNK_WITHOUT_TERMINAL_RTL_ITEM':'COINCIDENT_RTL_NOT_CAUSALLY_QUALIFIED'});
}
assert(out.filter(x=>x.causalFailsafeRTL).length>=2,'EARLY_DUPLEX_AND_BACKGROUND_CAUSAL_REQUIRED');fs.writeFileSync(E+'/causal-verification02.json',JSON.stringify({status:'PASS',runs:out},null,2),{flag:'wx'});console.log(JSON.stringify(out));
