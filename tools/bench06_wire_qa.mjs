// Independent socket-write capture: journal ring truncation cannot hide a write.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {SitlLink} from '../services/sitl.mjs';
import {Decoder} from '../services/mavlink.mjs';
import {validateBenchmarkRun} from '../app/core/benchmark.mjs';
import {assertCurrentFreeze} from './bench06_freeze.mjs';
const directory=process.env.AERIS_EVIDENCE_DIR||'evidence/bench06',checks=[],wire=[],link=new SitlLink();
const check=(name,pass,detail={})=>{checks.push({name,pass,...detail});if(!pass)throw Error(name);};
const delay=ms=>new Promise(r=>setTimeout(r,ms));async function until(f){const end=Date.now()+60000;while(!f()){if(Date.now()>end)throw Error('Fresh simulator observation timeout');await delay(100);}}
try{
 const run=await validateBenchmarkRun(await readFile(directory+'/run.json','utf8'));await assertCurrentFreeze(run.freeze);
 const state=await(await fetch('http://127.0.0.1:8788/api/sitl/status')).json();check('preview has no active connection/attempt',state.transport==='disconnected'&&!state.archive?.activeId);
 await link.connect();const socket=link.socket,original=socket.write;socket.write=function(bytes,...args){wire.push(Buffer.from(bytes));return original.call(this,bytes,...args);};
 try{await until(()=>link.snapshot().armed===false&&link.preflight().filter(c=>c.id!=='configuration').every(c=>c.pass));const cfg=await link.readConfiguration();check('fresh matching simulator/profile, observed disarmed',cfg.pass&&link.snapshot().armed===false);
  for(const c of run.suite.cases.filter(c=>!c.expected.accepted)){const start=wire.length;let error=null;try{await link.upload(c.request);}catch(e){error=e.message;}const emitted=wire.slice(start),decoder=new Decoder(),frames=emitted.flatMap(b=>decoder.push(b));check(c.id+' direct socket rejection',error===c.expected.error,{error});check(c.id+' zero mission/parameter writes',frames.every(f=>f.id===0)&&emitted.length===frames.length,{outboundIds:frames.map(f=>f.id),chunks:emitted.length});}
  check('entire read-only probe has zero PARAM_SET',new Decoder().push(Buffer.concat(wire)).every(f=>f.id!==23));check('probe final observed disarmed',link.snapshot().armed===false);await assertCurrentFreeze(run.freeze);
 }finally{socket.write=original;}
}catch(e){checks.push({name:'wire-probe-error',pass:false,error:e.stack});process.exitCode=1;}
finally{link.disconnect();const bytes=Buffer.concat(wire);await writeFile(directory+'/negative-socket.hex',bytes.toString('hex')+'\n');await writeFile(directory+'/wire-qa.json',JSON.stringify({scope:'Supplemental actual direct socket-write interception on fresh dedicated loopback SitlLink. No journal-ring length inference; no flight commands. Existing HTTP rejection receipts retained.',wireSha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,checks},null,2)+'\n');}
console.log(JSON.stringify({pass:checks.filter(c=>c.pass).length,fail:checks.filter(c=>!c.pass).length}));
