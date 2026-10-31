import {createServer} from 'node:http';
import {readFile,mkdir,statfs,lstat} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {randomBytes,randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {WorkspaceStore} from '../aeris57/store.mjs';
import {FixedBackend,ACTIONS} from './backend.mjs';
import {planMission,inspectKml,comparePlans,SAMPLES,CAMERA,OPTIONS} from '../aeris57/domain.mjs';
import {CAPABILITIES} from '../aeris57/catalog.mjs';
const ROOT=fileURLToPath(new URL('../..',import.meta.url)),HOME=path.join(ROOT,'pilot/alloc60'),VISUAL=path.join(ROOT,'pilot/visual56'),E=path.join(ROOT,'evidence/alloc60');
const sha=b=>createHash('sha256').update(b).digest('hex');
export async function createWorkspace({port=8814,backend=new FixedBackend(),storeRoot=path.join(E,'workspace')}={}){
 await mkdir(E,{recursive:true});const free=await statfs(ROOT,{bigint:true});if(free.bavail*free.bsize<20n*1024n**3n)throw Error('DISK_FLOOR');
 const store=new WorkspaceStore(storeRoot),token=randomBytes(24).toString('hex'),instance=randomUUID(),HOST='127.0.0.1:'+port;let owner=null,pendingStart=false,busy=false,auditError=null;
 const audit=(kind,data)=>{try{return store.append(kind,data)}catch(e){auditError=e.message;throw e}};
 const own=s=>!!owner&&s.run===owner.run&&s.session===owner.session&&s.boot===owner.boot;
 async function state(){let s;try{s=await backend.get('state')}catch(e){return{available:false,error:e.message,owned:false,instance,workspace:store.view(),mock:backend.mock,auditError}}const owned=own(s);if(!owned)s={...s,challenge:null,session:null,boot:null,input:s.input?{...s.input,lease:null}:null};return{...s,available:true,owned,instance,pendingStart,workspace:store.view(),mock:backend.mock,auditError,noAutomaticFlight:true,planningUploadsEnabled:false}}
 async function perform(route,d){if(!ACTIONS.has(route))throw Error('ACTION_ALLOWLIST');if(route==='start'){
   if(pendingStart||busy)throw Error('START_PENDING_NO_RETRY');if(store.error)throw Error('JOURNAL_BLOCKED');if(store.view().pending.length||store.view().uncertain.length)throw Error('WORKSPACE_RECONCILIATION_REQUIRED');const s=await backend.get('state');if(s.controllerActive||s.verifying)throw Error('BACKEND_ALREADY_ACTIVE_OR_VERIFYING');const disk=await statfs(ROOT,{bigint:true});if(disk.bavail*disk.bsize<24n*1024n**3n)throw Error('LIVE_PEAK_ADMISSION_24GIB');if(!['empty','central','offset'].includes(d.load)||!['calm','gust'].includes(d.wind))throw Error('PROFILE_ALLOWLIST');
   const intent=audit('INTENT',{route,load:d.load,wind:d.wind,mode:d.mode,requestId:d.requestId});busy=true;pendingStart=true;try{const response=await backend.post('start',{load:d.load,wind:d.wind,mode:d.mode,requestId:d.requestId});if(response.simulation!==true||!response.controllerActive||!response.run||!response.session||!response.boot)throw Error('START_IDENTITY_UNKNOWN');owner={run:response.run,session:response.session,boot:response.boot,mode:d.mode};pendingStart=false;audit('OUTCOME',{intent:intent.sha256,route,owner,scope:'SIMULATOR_ONLY',status:'OBSERVED_OWNED_START'});return response}catch(e){try{audit('OUTCOME',{intent:intent.sha256,route,error:e.message,status:'START_OUTCOME_REQUIRES_REVIEW'})}catch{}throw e}finally{busy=false}
  }
  if(!owner||d.session!==owner.session||d.boot!==owner.boot)throw Error('OWNED_SESSION_BOOT_REQUIRED');
  // Typed input is validated again by the canonical AP adapter (including current
  // session/boot, transport, physical epoch/age, heartbeat, lease/seq/challenge).
  // Avoid a redundant full-state GET+serialization per input in optimized mode.
  if(!(route==='input'&&owner.mode==='optimized')){const s=await backend.get('state');if(!own(s)||!s.controllerActive)throw Error('CURRENT_OWNED_BACKEND_REQUIRED');
   if(route==='claim'&&(!s.physics||s.physics.ground||s.vehicle?.mode!=='LOITER'||s.vehicle?.armed!==true))throw Error('AIRBORNE_ARMED_LOITER_REQUIRED');}
  let intent;if(route!=='input'){try{intent=audit('INTENT',{route,owner})}catch(e){if(!['land','release','end'].includes(route))throw e}}
  try{const response=await backend.post(route,d);if(intent)try{audit('OUTCOME',{intent:intent.sha256,route,status:'BACKEND_RESPONSE',run:owner.run})}catch{}return response}catch(e){if(intent)try{audit('OUTCOME',{intent:intent.sha256,route,error:e.message,status:e.message.includes('WRITE_OUTCOME_UNKNOWN')?'WRITE_OUTCOME_UNKNOWN_NO_RETRY':'BACKEND_REJECTED'})}catch{}throw e}
 }
 const reports=new Map();for(const c of CAPABILITIES)for(const p of c.reports)reports.set(p,p);
 const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.ttf':'font/ttf','.jpg':'image/jpeg','.glb':'model/gltf-binary','.hdr':'application/octet-stream'};
 async function file(res,p){const s=await lstat(p);if(!s.isFile()||s.isSymbolicLink()||!mime[path.extname(p)])throw Error('STATIC_FILE');res.writeHead(200,{'content-type':mime[path.extname(p)]});res.end(await readFile(p))}
 const server=createServer(async(req,res)=>{
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Content-Security-Policy',"default-src 'self';script-src 'self';style-src 'self' 'unsafe-inline';img-src 'self' data: blob:;connect-src 'self' blob:;object-src 'none';frame-ancestors 'none'");const json=(code,d)=>{res.writeHead(code,{'content-type':'application/json; charset=utf-8'});res.end(JSON.stringify(d))};
  try{if(req.headers.host!==HOST||req.headers.origin&&req.headers.origin!=='http://'+HOST)return json(403,{error:'ORIGIN'});const url=new URL(req.url,'http://'+HOST),route=url.pathname;
   if(req.method==='GET'){
    if(route==='/api/bootstrap')return json(200,{token,instance,mock:backend.mock,scope:'ISOLATED_ENGINEERING_SIMULATOR',samples:SAMPLES,camera:CAMERA,options:OPTIONS});
    if(route==='/api/state')return json(200,await state());
    if(route==='/api/history')return json(200,await backend.get('history'));
    const history=route.match(/^\/api\/history\/([a-zA-Z0-9]{1,24})$/);if(history){const item=await backend.get('history/'+history[1]);const bytes=await readFile(path.join(ROOT,'evidence/alloc60/runs',history[1],'readback.json'));const r=JSON.parse(bytes);return json(200,{...item,timing:{readbackSha256:sha(bytes),status:r.status,activeReceiveRTF:r.activeReceiveRTF,fiveSecondWindows:r.fiveSecondWindows,hostReceiveGapsMs:r.hostReceiveGapsMs,hostComputeMs:r.hostComputeMs,manualNonNeutralRCFrames:r.manualNonNeutralRCFrames,fullG1Accepted:false}})}
    if(route==='/api/catalog'){const result=[];for(const c of CAPABILITIES){const sources=[];for(const p of c.reports){try{const b=await readFile(path.join(ROOT,p));sources.push({path:p,sha256:sha(b),bytes:b.length,available:true})}catch{sources.push({path:p,available:false})}}result.push({...c,sources})}return json(200,result)}
    if(route==='/api/report'){const p=url.searchParams.get('id');if(!reports.has(p))throw Error('REPORT_ALLOWLIST');const b=await readFile(path.join(ROOT,p));return json(200,{path:p,sha256:sha(b),text:b.toString('utf8'),provenance:'RETAINED_LOCAL_REPORT_NOT_NEW_ACCEPTANCE'})}
    if(route==='/api/qgc-example'){const b=await readFile(path.join(ROOT,'pilot/mission55/fixtures/run5/camera-mixed-altitude.plan'),'utf8'),a=await readFile(path.join(ROOT,'pilot/mission55/fixtures/run5/placeholder.plan'),'utf8');return json(200,{before:b,after:a,provenance:'SYNTHETIC_MISSION55_CAMERA_PLACEHOLDER_NEGATIVE'})}
    if(route==='/api/journal')return json(200,{format:'aeris57-workspace-export',version:1,records:store.rows,head:store.head,authorityRestored:false});
    if(route==='/')return await file(res,path.join(ROOT,'pilot/aeris57/index.html'));
    const ownFiles={'/ui.mjs':'ui.mjs','/ui-timing.mjs':'ui-timing.mjs','/style.css':'../aeris57/style.css','/scene.mjs':'../visual56/scene.mjs','/blend.mjs':'../simtrain53/pose.mjs','/audio.mjs':'../sim32/viewer/audio.mjs','/credits.html':'../visual56/credits.html','/font.ttf':'../../native/preflight44/assets/IBMPlexSans.ttf'};if(ownFiles[route])return await file(res,path.resolve(HOME,ownFiles[route]));
    if(['/vendor/three.module.js','/vendor/three.core.js'].includes(route))return await file(res,path.join(ROOT,'pilot/sim32/viewer',route));
    if(route.startsWith('/assets/')||route.startsWith('/vendor/addons/')){const p=path.resolve(VISUAL,'.'+decodeURIComponent(route));if(!p.startsWith(VISUAL+path.sep))throw Error('STATIC_PATH');return await file(res,p)}
    return json(404,{error:'NO_ROUTE'});
   }
   if(req.method!=='POST')return json(405,{error:'METHOD'});if(req.headers.origin!=='http://'+HOST||req.headers['x-aeris-token']!==token||req.headers['content-type']!=='application/json')return json(403,{error:'EXPLICIT_LOCAL_TOKEN_ORIGIN_TYPE'});
   let d;try{const chunks=[];let size=0;for await(const c of req){size+=c.length;if(size>768*1024)throw Error('BODY_BOUND');chunks.push(c)}d=JSON.parse(Buffer.concat(chunks).toString('utf8'))}catch(e){if(route==='/api/flight/input'&&owner)await backend.post('release',{session:owner.session,boot:owner.boot}).catch(()=>{});throw e}
   if(route==='/api/mission/inspect')return json(200,await inspectKml(d.kml));
   if(route==='/api/mission/compile'){if(busy||pendingStart)throw Error('WORKSPACE_BUSY');const s=await backend.get('state').catch(()=>({controllerActive:false}));if(s.controllerActive)throw Error('EDIT_PLAN_AFTER_FLIGHT_CLOSED');if(d.expectedHead!==store.head)throw Error('STALE_HEAD');const plan=await planMission(d);store.append('PLAN',plan,d.expectedHead);return json(200,store.view())}
   if(route==='/api/semantic')return json(200,await comparePlans(d));
   const action=route.match(/^\/api\/flight\/([a-z-]+)$/);if(action)return json(200,await perform(action[1],d));
   return json(404,{error:'NO_ARBITRARY_COMMAND_OR_UPLOAD_ROUTE'});
  }catch(e){json(409,{error:e.message,noAutomaticRetry:true})}
 });
 server.requestTimeout=65000;server.headersTimeout=10000;server.maxConnections=24;
 return{server,store,state,perform,instance};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const {server}=await createWorkspace();server.listen(8814,'127.0.0.1',()=>console.log('AERIS57 http://127.0.0.1:8814 pid'+process.pid));for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)))}
