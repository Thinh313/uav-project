import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {RESOURCE_POLICY,policySha256,assessResources,observeResources,isolationPlan} from './resource-policy.mjs';
import {immutableJSON} from './data-schema.mjs';
import {randomUUID} from 'node:crypto';
import path from 'node:path';
import {digest} from './trust-metadata.mjs';
const exec=promisify(execFile);
export async function managedChild(plan,writer,{env={},inspect=null,timeoutMs=15000,isolation=null,auditDirectory=null}={}){
 const protectedRun=!!isolation;
 let configured=null,initial=null;
 if(protectedRun){initial=assessResources(await observeResources(plan.env.AERIS_DATA_ROOT));if(initial.status!=='OBSERVED_FIT')throw Error('Parent resource admission blocked: '+initial.reasons);configured=await isolationPlan({...isolation,slot:plan.slot,dataRoot:plan.env.AERIS_DATA_ROOT,command:plan.command,port:Number(plan.env.AERIS_PORT)});}
 const childEnv={...(protectedRun?{PATH:'/usr/bin:/bin:/usr/sbin:/sbin',LANG:'en_US.UTF-8',TZ:'UTC'}:process.env),...plan.env,...env,AERIS_BOOTSTRAP_IPC:'1',NODE_OPTIONS:'',NODE_PATH:'',DYLD_INSERT_LIBRARIES:'',DYLD_LIBRARY_PATH:'',DYLD_FRAMEWORK_PATH:'',LD_PRELOAD:'',LD_LIBRARY_PATH:''};
 if(protectedRun){childEnv.AERIS_RESOURCE_POLICY_SHA=policySha256;childEnv.AERIS_ISOLATION_SHA=configured.profileSha256;}else{delete childEnv.AERIS_RESOURCE_POLICY_SHA;delete childEnv.AERIS_ISOLATION_SHA;}
 const args=protectedRun?[...configured.prefix.slice(0,-1),configured.prefix.at(-1),'--max-old-space-size='+RESOURCE_POLICY.heapMiB,...plan.args]:plan.args;
 const id=randomUUID(),begin={format:'aeris-runtime-session',version:1,id,time:new Date().toISOString(),manifestSha256:plan.env.AERIS_EXPECTED_SOFTWARE??null,layoutSha256:env.AERIS_DATA_SCHEMA_SHA??plan.env.AERIS_DATA_SCHEMA_SHA??null,policySha256:protectedRun?policySha256:null,isolationSha256:configured?.profileSha256??null,initial,autoRestart:false};
 // An incomplete begin without end is evidence of interrupted supervision, never success.
 if(auditDirectory)await immutableJSON(path.join(auditDirectory,id+'.begin.json'),begin);
 const child=spawn(configured?.command??plan.command,args,{cwd:plan.slot,env:childEnv,stdio:['ignore','pipe','pipe','ipc']});
 let output='',ended=false,peakRssBytes=0,lastHeartbeat=Date.now(),cause=null,monitor=null,busy=false,shutdownTimer=null;
 child.stdout.on('data',b=>output=(output+b).slice(-8192));child.stderr.on('data',b=>output=(output+b).slice(-8192));
 const exit=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',(code,signal)=>{ended=true;resolve({code,signal});});});
 const stop=(why)=>{if(ended)return;if(!cause)cause=why;child.kill('SIGTERM');if(!shutdownTimer)shutdownTimer=setTimeout(()=>{if(!ended)child.kill('SIGKILL');},RESOURCE_POLICY.shutdownMs).unref();};
 const onSignal=()=>stop('OPERATOR_STOP');process.on('SIGTERM',onSignal);process.on('SIGINT',onSignal);
 let result=null;
 try{
  const ready=new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Managed child readiness timeout '+output)),timeoutMs);child.once('message',m=>{clearTimeout(timer);m?.type==='AERIS_SECURE_READY'?resolve():reject(Error('Invalid readiness'));});child.once('error',e=>{clearTimeout(timer);reject(e);});child.once('exit',()=>{clearTimeout(timer);reject(Error('Child exited before readiness '+output));});});
  await writer.registerChild(child.pid);await ready;
  child.on('message',m=>{if(m?.type==='AERIS_RESOURCE_HEARTBEAT'&&m.policySha256===policySha256)lastHeartbeat=Date.now();});
  if(protectedRun){monitor=setInterval(async()=>{if(ended||busy)return;busy=true;try{const r=await exec('/bin/ps',['-o','rss=','-p',String(child.pid)],{timeout:2000,maxBuffer:1024}),rss=Number(r.stdout.trim())*1024;if(!Number.isSafeInteger(rss)||rss<=0)throw Error('RSS observation invalid');peakRssBytes=Math.max(peakRssBytes,rss);const observation=await observeResources(plan.env.AERIS_DATA_ROOT);if(rss>RESOURCE_POLICY.rssBytes)stop('RSS_BUDGET');else if(observation.freeBytes<RESOURCE_POLICY.minFreeBytes+RESOURCE_POLICY.metadataReserveBytes)stop('DISK_RESERVE');else if(Date.now()-lastHeartbeat>RESOURCE_POLICY.heartbeatTimeoutMs)stop('HEARTBEAT_TIMEOUT');}catch{if(!ended)stop('RESOURCE_OBSERVATION_FAILED');}finally{busy=false;}},RESOURCE_POLICY.sampleMs);}
  child.send({type:'AERIS_SECURE_START'});
  if(inspect){const observation=await inspect(child,()=>output);stop('CANARY_COMPLETE');const end=await exit;if(end.code!==0)throw Error('Canary process failed '+output);if(cause!=='CANARY_COMPLETE')throw Error('Canary resource supervision failed '+cause);result=observation;}
  else{result=await exit;if(cause&&!['OPERATOR_STOP'].includes(cause)||result.code!==0&&result.signal!=='SIGTERM')throw Error('Active child failed '+(cause??result.signal??result.code)+' '+output);}
  return result;
 }finally{
  clearInterval(monitor);process.off('SIGTERM',onSignal);process.off('SIGINT',onSignal);
  if(!ended){stop(cause??'SUPERVISOR_ERROR');await exit.catch(()=>{});}clearTimeout(shutdownTimer);
  if(auditDirectory)await immutableJSON(path.join(auditDirectory,id+'.end.json'),{format:'aeris-runtime-session-end',version:1,id,beginSha256:digest(begin),time:new Date().toISOString(),pid:child.pid??null,manifestSha256:begin.manifestSha256,policySha256:begin.policySha256,isolationSha256:begin.isolationSha256,cause:cause??(child.exitCode===0?'PROCESS_EXIT':'PROCESS_FAILURE'),code:child.exitCode,signal:child.signalCode,peakRssBytes,completedSupervision:true,autoRestart:false});
 }
}
