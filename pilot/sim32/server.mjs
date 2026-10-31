import http from 'node:http';
import {readFile,writeFile,stat,readdir} from 'node:fs/promises';
import {createReadStream,existsSync} from 'node:fs';
import {createGunzip} from 'node:zlib';
import {createInterface} from 'node:readline';
import {randomBytes,createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {compileSurvey,SITL_WORLD}from'../../app/core/compiler.mjs';
import{localFrame,DEMO_ORIGIN}from'../../app/core/survey.mjs';
import {PayloadRange}from'./payload.mjs';
import {sealReview}from'./review_seal.mjs';
import {SimulationLink,request} from './link.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),web=path.join(root,'pilot/sim32/viewer'),execute=promisify(execFile),origin='http://127.0.0.1:8796',token=randomBytes(32).toString('hex');
process.chdir(root);
function compilePlan(p){const c=compileSurvey(p,SITL_WORLD),frame=localFrame(DEMO_ORIGIN);return {...c,scenePoints:c.items.filter(i=>[16,22].includes(i.command)&&i.z>0).map(i=>{const xy=frame.forward({lat:i.x/1e7,lon:i.y/1e7});return [xy.x,i.z,-xy.y];})};}
let compiledPlan=compilePlan(request());
let starting=false,payload=null,link=null,run=null,busy=false,grant=null,plan=request(),lastError=null,closing=false;
const enc=value=>JSON.stringify(value);
async function runtime(mode,id,load,wind){return execute('python3',['-B','pilot/sim32/runtime.py',mode,id,...(mode==='start'?[load,wind]:[])],{cwd:root,timeout:25000,maxBuffer:1024*1024});}
async function close(){
 if(!run||closing)return;closing=true;const id=run,l=link;grant=null;let record=null,closureError=null;
 try{
  if(l){record={...l.review(),physicsFinal:(()=>{try{return l.physics();}catch{return null;}})(),payload:payload?.snapshot()??null};await writeFile(`evidence/sim32/runs/${id}/review-capture-before-close.json`,enc(record)+'\n',{flag:'wx'});}
  payload?.close();payload=null;l?.disconnect();link=null;
  try{await runtime('stop',id);}catch(e){closureError=e.message;throw e;}
 }finally{
  try{if(record){let summary=null;try{summary=JSON.parse(await readFile(`evidence/sim32/runs/${id}/backend-summary.json`,'utf8'));}catch{}await writeFile(`evidence/sim32/runs/${id}/review-ui.json`,enc(sealReview(record,summary,closureError))+'\n',{flag:'wx'});}}
  finally{run=null;closing=false;}
 }
}
async function state(){let physics=null;try{if(link)physics=link.physics();}catch(e){if(!starting)lastError=e.message;}return {run,busy,starting,token,physics,payload:payload?.snapshot()??null,vehicle:link?.snapshot()??null,preflight:link?[...link.preflight(),{id:'payload',pass:!!payload&&!payload.closed&&!payload.error&&payload.cameras.size===3&&payload.gimbals.size===2,detail:'Synthetic fixture3cameras/2gimbals available through actual AP'}]:[],mission:link?.mission.state??'idle',execution:link?.execution.state??'idle',grant:grant?{expires:grant.expires}:null,error:lastError,compiledPlan,runtimeConfiguration:{engine:process.env.SIM32_ENGINE??'optimized',requestedSpeedup:Number(process.env.SIM32_SPEEDUP??1),rateHz:1200,lockstep:true},scope:'SIMULATION · reference quad, provisional physics; no physical media',plan};}
async function body(req){let s='';for await(const b of req){s+=b;if(Buffer.byteLength(s)>4096)throw Error('Request bound');}return JSON.parse(s||'{}');}
async function action(kind,b){
 if(busy)throw Error('Operation already in progress');busy=true;lastError=null;
 try{
  if(kind==='plan'){if(run)throw Error('Stop session before changing mission');const proposed=request(b),compiled=compilePlan(proposed);plan=proposed;compiledPlan=compiled;grant=null;}
  else if(kind==='start'){
   if(run)throw Error('Session already active');if(!['empty','central','offset'].includes(b.load)||!['calm','crosswind','gust'].includes(b.wind))throw Error('Reference profile allowlist');
   starting=true;const id='ui'+Date.now();await runtime('start',id,b.load,b.wind);run=id;link=new SimulationLink(id);
   try{await link.connect();payload=new PayloadRange(link);await payload.connect();starting=false;await writeFile(`evidence/sim32/runs/${id}/mission-request.json`,enc(plan)+'\n');}catch(e){await close();throw e;}
  }else if(kind==='stop'){await close();}
  else{
   if(!link||!run)throw Error('No owned simulator session');link.physics();
   if(kind==='preflight'){
    if(b.confirmHome!==true)throw Error('Confirm virtual Home / AMSL10m / relative altitude first');await link.readConfiguration();await link.readSimulatorConfiguration();
    if(!link.preflight().every(c=>c.pass)||payload.closed||payload.error)throw Error('Preflight not ready');grant={expires:Date.now()+60000,planSha:createHash('sha256').update(enc(plan)).digest('hex'),run};
   }else if(kind==='upload'){
    if(!grant||grant.expires<Date.now()||grant.run!==run||grant.planSha!==createHash('sha256').update(enc(plan)).digest('hex'))throw Error('Fresh preflight authorization required');await link.upload(plan);
   }else if(kind==='arm'){
    if(!grant||grant.expires<Date.now()||link.mission.state!=='verified')throw Error('Fresh preflight and complete readback required');await link.readConfiguration();await link.readSimulatorConfiguration();if(!link.preflight().every(c=>c.pass))throw Error('Preflight changed');await link.command('guided');await link.command('arm');grant=null;
   }else if(kind==='auto'){if(link.snapshot().mode==='AUTO'||link.execution.state==='running')throw Error('AUTO already observed; no repeat');if(!link.snapshot().armed||link.mission.state!=='verified')throw Error('Armed/readback state required');await link.command('auto');}
   else if(kind==='zoom'||kind==='gimbal'){if(kind==='gimbal'){const binding={100:1,102:2}[b.cameraComponent];if(!binding||binding!==b.device||b.component!==154)throw Error('Camera/gimbal binding mismatch');}const t=payload.dispatch({component:b.component,device:b.device??0,operation:kind,value:b.value});await payload.receivedByPeer(t);payload.feedback(t);}
   else if(kind==='rtl'){if(!link.snapshot().armed)throw Error('Aircraft not armed');await link.command('rtl');}
   else throw Error('Unsupported action');
  }
 }catch(e){lastError=e.message;throw e;}finally{busy=false;starting=false;}
 return state();
}
async function replay(id){
 if(!/^[a-zA-Z0-9]{1,32}$/.test(id))throw Error('Run ID');const base=`evidence/sim32/runs/${id}`,result=[],f=createReadStream(base+'/physics-raw.jsonl.gz').pipe(createGunzip());
 let n=0;for await(const line of createInterface({input:f,crlfDelay:Infinity})){if(line.length>8192)throw Error('Replay line bound');const row=JSON.parse(line);if(++n%20)continue;if(result.length>=18000)throw Error('Replay sample bound');const s=JSON.parse(row.sensorUtf8),aux=row.modelAux??row.model;result.push({...s,rpmEstimated:aux.rpmEstimated,ground:aux.ground,energyWhEstimated:aux.energyWhEstimated,frame:row.frame});}
 const launch=JSON.parse(await readFile(base+'/launch.json','utf8')),speedupIndex=launch.command.indexOf('--speedup'),runtimeConfiguration=launch.runtimeConfiguration??{requestedSpeedup:Number(launch.command[speedupIndex+1]),rateHz:1200,provenance:'DECLARED_LAUNCH_ARGUMENT'};
 return {runtimeConfiguration,run:id,source:'RECORDED_SITL_PROVISIONAL_PHYSICS',samples:result,profile:JSON.parse(await readFile(base+'/profile.json','utf8')),summary:JSON.parse(await readFile(base+'/backend-summary.json','utf8')),flightQa:existsSync(base+'/flight-qa.json')?JSON.parse(await readFile(base+'/flight-qa.json','utf8')):null,acceptance:existsSync(base+'/acceptance.json')?JSON.parse(await readFile(base+'/acceptance.json','utf8')):null,readOnly:true};
}
const server=http.createServer(async(req,res)=>{
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'");
 try{
  if(req.headers.host!=='127.0.0.1:8796')throw Error('Loopback host required');const url=new URL(req.url,origin);
  if(req.method==='POST'){
   if(req.headers.origin!==origin||req.headers['x-sim32-token']!==token)throw Error('Same-origin session token required');const b=await body(req);const value=await action(url.pathname.replace('/api/',''),b);res.setHeader('Content-Type','application/json');return res.end(enc(value));
  }
  if(req.method!=='GET')throw Error('Method not allowed');
  if(url.pathname==='/api/state'){res.setHeader('Content-Type','application/json');return res.end(enc(await state()));}
  if(url.pathname==='/api/runs'){const dirs=await readdir('evidence/sim32/runs',{withFileTypes:true}),items=[];for(const d of dirs)if(d.isDirectory()&&existsSync(`evidence/sim32/runs/${d.name}/backend-summary.json`))items.push({run:d.name,summary:JSON.parse(await readFile(`evidence/sim32/runs/${d.name}/backend-summary.json`,'utf8'))});res.setHeader('Content-Type','application/json');return res.end(enc(items));}
  if(url.pathname==='/api/replay'){if(run||busy)throw Error('Stop live session before replay');res.setHeader('Content-Type','application/json');return res.end(enc(await replay(url.searchParams.get('run'))));}
  if(url.pathname==='/api/review'){if(!/^[a-zA-Z0-9]{1,32}$/.test(url.searchParams.get('run')??''))throw Error('Run ID');const id=url.searchParams.get('run'),base=`evidence/sim32/runs/${id}`;const fname=existsSync(base+'/review.json')?'review.json':'review-ui.json';res.setHeader('Content-Type','application/json');return res.end(await readFile(base+'/'+fname));}
  const relative=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1),p=path.resolve(web,relative);if(!p.startsWith(web+path.sep))throw Error('Path rejected');const info=await stat(p);if(!info.isFile()||info.size>2*1024**2)throw Error('Asset bound');const types={'.html':'text/html','.css':'text/css','.mjs':'text/javascript','.js':'text/javascript','.txt':'text/plain'};res.setHeader('Content-Type',types[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));
 }catch(e){res.statusCode=400;res.setHeader('Content-Type','application/json');res.end(enc({error:e.message}));}
});
const watch=setInterval(async()=>{if(!run||busy||closing)return;try{link.physics();if(link.execution.state==='completed'&&!link.snapshot().armed){if(!link.physics().ground)lastError='Autopilot terminal while physics airborne';await close();}}catch(e){lastError=e.message;try{await close();}catch(x){lastError+='; closure: '+x.message;}}},1000);
async function shutdown(){clearInterval(watch);try{await close();}finally{server.close(()=>process.exit(0));}}
process.on('SIGTERM',shutdown);process.on('SIGINT',shutdown);
server.listen(8796,'127.0.0.1',()=>console.log('SIM32 viewer '+origin+' — isolated actual SITL / recorded inspection'));
