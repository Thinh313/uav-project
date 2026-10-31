import assert from 'node:assert/strict';
import {mkdir,cp,rm,writeFile,readdir} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {Store} from './store.mjs';
import {OPTIONS,CAMERA} from './common.mjs';
import {SAMPLES} from './fixtures.mjs';
import {context} from './workspace.mjs';
import {fixture} from './readiness.mjs';
const id=process.env.MAPPING51_CRASH??'crash1',E='evidence/mapping51/'+id,results=[],processes=[],roots=[];await mkdir(E);
const check=(n,v)=>{assert.ok(v,n);results.push({name:n,pass:true})};let child;
try{for(const point of ['AFTER_CREATE','AFTER_WRITE','AFTER_SYNC']){
 const root='.local/mapping51-'+id+'-'+point.toLowerCase();roots.push(root);await mkdir(root);const s=new Store(root);await s.load();const ctx=context(),events=[['IMPORT_KML',{text:SAMPLES.polygon}],['CONFIGURE',{featureId:'f-0001',options:{...OPTIONS,datumAcknowledged:true},camera:CAMERA}],['CONNECT_MOCK',{context:ctx}]];let t=1000000;
 for(const[type,data]of events)await s.append({type,atMs:t++,data});const p=s.w.machine.plan;await s.append({type:'OBSERVE',atMs:t,data:{observation:fixture(p,ctx,t)}});t++;await s.append({type:'REVIEW',atMs:t++,data:{planSha256:p.sha256,typedCode:'MOCK-'+p.sha256.slice(0,8),acknowledge:'SYNTHETIC_FLAT_TRANSIT_UNCHECKED_NO_FLIGHT'}});await s.append({type:'START',atMs:t++,data:{}});
 child=spawn(process.execPath,['pilot/mapping51/crash-worker.mjs',root,point],{stdio:['ignore','pipe','pipe']});let out='',err='';child.stdout.on('data',b=>out+=b);child.stderr.on('data',b=>err+=b);const ended=new Promise(r=>child.once('exit',(code,signal)=>r({code,signal})));
 for(let i=0;i<200&&!out.includes('HOOK '+point);i++){if(child.exitCode!==null)throw Error('WORKER_EXIT:'+err);await new Promise(r=>setTimeout(r,25))}assert.ok(out.includes('HOOK '+point),'hook reached');const pid=child.pid;child.kill('SIGKILL');const exit=await ended;child=null;processes.push({pid,point,exit,stdout:out,stderr:err});check('actual owned SIGKILL '+point,exit.signal==='SIGKILL');check('old six records plus pending/committed seventh retained '+point,(await readdir(root)).length===7);
 if(point==='AFTER_CREATE'){await assert.rejects(()=>new Store(root).load(),/JSON|Unexpected|end/);check('torn create refuses cold replay, no deletion',true)}else{const cold=new Store(root);await cold.load();check('complete raw bytes replay exactly once '+point,cold.w.machine.counts.simulatedAcks===1&&cold.records.length===7);await cold.w.apply({type:'RESET',atMs:1000100,data:{}});check('cold live reset revokes authority '+point,!cold.w.machine.ctx&&!cold.w.machine.observation&&!cold.w.machine.approval&&cold.w.machine.status==='INTERRUPTED');check('historical ACK remains not image '+point,cold.w.machine.counts.actualFiles===0&&cold.w.machine.counts.simulatedExposures===0)}
 await cp(root,E+'/'+point.toLowerCase(),{recursive:true,errorOnExist:true,force:false});await rm(root,{recursive:true});
 }
 await writeFile(E+'/receipt.json',JSON.stringify({status:'PASS',checks:results.length,results,processes,scope:'Owned Node process termination only, not physical powerloss'},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',checks:results.length}));
}catch(e){await writeFile(E+'/failure.json',JSON.stringify({status:'FAIL',error:e.stack,results,processes},null,2)+'\n',{flag:'wx'});throw e}finally{if(child){child.kill('SIGKILL');await new Promise(r=>child.once('exit',r))}for(const root of roots){try{await cp(root,E+'/failed-'+root.split('/').at(-1),{recursive:true,errorOnExist:true,force:false});await rm(root,{recursive:true})}catch(e){if(e.code!=='ENOENT')throw e}}await writeFile(E+'/cleanup.json',JSON.stringify({removed:roots})+'\n',{flag:'wx'})}
