/** CLOCKVIDEO05 test admission only. All command/authority/physics methods inherited frozen. */
import{Flight02}from'../../field02/flight/flight02.mjs';
import fs from'node:fs';import path from'node:path';import{randomUUID,createHash}from'node:crypto';import{spawn}from'node:child_process';
const{MissionLink,wait}=await import('../../auto63/link-v5.mjs');
const{connectMock}=await import('../../auto63/mock-v5.mjs');
const{Capture,save}=await import('../../auto63/journal-v3.mjs');
const{verifyPlan}=await import('../../auto63/compiler.mjs');
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex'),mono=()=>Number(process.hrtime.bigint())/1e6;
export class Flight04 extends Flight02{
 pins(){const file=path.join(this.root,'evidence/field02/clockvideo05/flight-pins03.json'),p=JSON.parse(fs.readFileSync(file));if(p.format!=='aeris-clockvideo05-flight-pins'||p.budget.maxCumulativeSITLRequests!==12||p.priorSITLRequests.length!==10||new Set(p.priorSITLRequests.map(r=>r.run)).size!==10)throw Error('CLOCKVIDEO05_PIN_SCHEMA');for(const[n,h]of Object.entries(p.files))if(hash(path.join(this.root,n))!==h)throw Error('SOURCE_PIN:'+n);for(const r of p.priorSITLRequests){const name='evidence/field02/flight/runs/'+r.run+'/request.json';if(!/^s[a-f0-9]{20}$/.test(r.run)||hash(path.join(this.root,name))!==r.requestSha256||JSON.parse(fs.readFileSync(path.join(this.root,name))).mode!=='sitl')throw Error('CLOCKVIDEO05_PRIOR_REQUEST:'+r.run);}return p;}
 async connect(d){
  if(this.current)throw Error('SESSION_ALREADY_EXISTS');if(d.confirmSimulation!==true||!['mock','sitl'].includes(d.mode))throw Error('EXPLICIT_SIMULATION_MODE');const sourcePins=this.pins();verifyPlan(this.document.compiled.plan);
  if(d.mode==='sitl'&&fs.readdirSync(this.evidenceRoot+'/runs').filter(n=>{try{return JSON.parse(fs.readFileSync(this.evidenceRoot+'/runs/'+n+'/request.json')).mode==='sitl'}catch{return false}}).length>=12)throw Error('MAX_TWELVE_SITL_ATTEMPTS');
  const run=(d.mode==='sitl'?'s':'m')+randomUUID().replaceAll('-','').slice(0,20),out=this.evidenceRoot+'/runs/'+run;fs.mkdirSync(out);save(out+'/source-pins.json',sourcePins);save(out+'/plan.json',this.document.compiled.plan);save(out+'/document92.json',this.document);save(out+'/request.json',{run,mode:d.mode,instance:this.instance,binding:this.binding,source:'HOST_NODE_GCS_SIM_ONLY',at:new Date().toISOString()});
  const capture=new Capture(out);let link,proc;
  try{
   if(d.mode==='sitl'){
    const start=mono(),samples=[];for(let i=0;i<31;i++){const f=fs.statfsSync(this.root);const freeBytes=f.bavail*f.bsize;samples.push({hostMonoMs:mono(),freeBytes});if(freeBytes<29*2**30)throw Error('ADMISSION_BELOW_29GIB');if(i<30)await wait(1000);}save(out+'/admission.json',{samples,durationMs:mono()-start,minimumBytes:29*2**30});
    const fd=fs.openSync(out+'/runtime-console.txt','wx');proc=spawn('python3',['-B','pilot/clockvideo05/flight/runtime04.py',run],{cwd:this.root,stdio:['ignore',fd,fd]});fs.closeSync(fd);const end=mono()+35000;while(!fs.existsSync(out+'/launch.json')){if(proc.exitCode!==null||proc.signalCode!==null)throw Error('OWNED_RUNTIME_LAUNCH_FAILED');if(mono()>end)throw Error('OWNED_RUNTIME_LAUNCH_DEADLINE_NO_RETRY');await wait(100);}
    const launch=JSON.parse(fs.readFileSync(out+'/launch.json'));link=new MissionLink(capture,this.document.compiled.plan);link.port=5972;link.simSource='OBSERVED_ARDUPILOT_INTERNAL_QUAD_HOST_NODE_GCS';this.observe(link,run);await link.connect();link.attach({scope:'READONLY_PREFLIGHT43',origin:'OBSERVED_OWNED_SITL',binarySha256:launch.binarySha256,system:42,component:1,session:link.sessionId,boot:randomUUID(),epoch:run,containerId:launch.containerId,pid:launch.pid,startedAt:launch.startedAt});await link.until(()=>link.freshness(0),5000);
   }else{link=await connectMock(capture,this.document.compiled.plan);this.observe(link,run);}
   this.current={run,out,capture,link,proc,mode:d.mode};this.authority=null;this.attest();link.record('FIELD01_BINDING',{...this.binding,run,hostArchitecture:'HOST_NODE_GCS_SIM_ONLY',authorityRestored:false});save(out+'/session.json',{run,session:link.sessionId,boot:link.boot,mode:d.mode});return this.state();
  }catch(e){try{link?.close63();if(!capture.closed)capture.close()}catch{}if(proc){if(!fs.existsSync(out+'/stop-request.json'))save(out+'/stop-request.json',{reason:'LAUNCH_FAILURE',error:e.message});await this.waitProcess(proc);}this.current=null;save(out+'/launch-failure.json',{error:e.message,accepted:false});throw e;}
 }
}
