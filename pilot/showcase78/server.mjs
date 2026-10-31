import {createServer} from 'node:http';
import {readFile,statfs,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createWorkspace} from '../aeris57/server.mjs';
import {CATALOG,EXTRA_REPORTS} from './catalog.mjs';
const ROOT=fileURLToPath(new URL('../..',import.meta.url)),HOME=path.join(ROOT,'pilot/showcase78');
export const PREVIEW_MIN=20.25*2**30,LIVE_MIN=28*2**30;
export const admitted=(free,live=false)=>Number.isFinite(free)&&free>=(live?LIVE_MIN:PREVIEW_MIN);
export async function startShowcase(port=8828){
 const free=async()=>{const d=await statfs(ROOT,{bigint:true});return Number(d.bavail*d.bsize)};
 if(!admitted(await free()))throw Error('PREVIEW_DISK_ADMISSION');
 await mkdir(path.join(ROOT,'evidence/showcase78'),{recursive:true});
 const core=await createWorkspace({port,storeRoot:path.join(ROOT,'evidence/showcase78/workspace')});
 const host='127.0.0.1:'+port;
 const server=createServer(async(req,res)=>{
  const json=(code,d)=>{res.writeHead(code,{'content-type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(d))};
  if(req.headers.host!==host||req.headers.origin&&req.headers.origin!=='http://'+host)return json(403,{error:'ORIGIN'});
  try{
   if(req.method==='GET'&&req.url==='/assets/replay-index.json'){const previous=JSON.parse(await readFile(path.join(ROOT,'pilot/visual56/assets/replay-index.json'),'utf8')),current=JSON.parse(await readFile(path.join(ROOT,'evidence/showcase78/replay-descriptor.json'),'utf8'));return json(200,[current,...previous])}
   if(req.method==='GET'&&req.url==='/assets/showcase78-flight.json'){res.writeHead(200,{'content-type':'application/json','Cache-Control':'no-store'});res.end(await readFile(path.join(ROOT,'evidence/showcase78/flight-replay.json')));return}
   if(req.method==='GET'&&req.url==='/api/catalog'){const result=[];for(const c of CATALOG){const sources=[];for(const p of c.reports){try{const b=await readFile(path.join(ROOT,p));sources.push({path:p,sha256:createHash('sha256').update(b).digest('hex'),bytes:b.length,available:true})}catch{sources.push({path:p,available:false})}}result.push({...c,sources})}return json(200,result)}
   if(req.method==='GET'&&req.url.startsWith('/api/report?')){const p=new URL(req.url,'http://'+host).searchParams.get('id');if(EXTRA_REPORTS.has(p)){const b=await readFile(path.join(ROOT,p));return json(200,{path:p,sha256:createHash('sha256').update(b).digest('hex'),text:b.toString('utf8'),provenance:'RETAINED_LOCAL_REPORT_NOT_NEW_ACCEPTANCE'})}}
   if(req.url==='/api/presentation'&&req.method==='GET'){const bytes=await free();return json(200,{freeBytes:bytes,previewAllowed:admitted(bytes),liveAllowed:admitted(bytes,true),liveMinimumGiB:28,scope:'RECORDED_REFERENCE_SITL_DEFAULT',actualImages:0,calibratedHera:false})}
   if(req.url==='/api/flight/start'&&!admitted(await free(),true))return json(409,{error:'SHOWCASE_LIVE_PEAK_28GIB',noAutomaticRetry:true});
   const own={'/':'index.html','/showcase.mjs':'ui.mjs','/showcase.css':'style.css','/sound.mjs':'sound.mjs','/live-controls.mjs':'controls.mjs','/live-controls.css':'controls.css'};
   if(own[req.url]){
    if(req.method!=='GET')return json(405,{error:'METHOD'});
    if(!admitted(await free()))return json(503,{error:'DISK_FLOOR_HEADROOM'});
    const b=await readFile(path.join(HOME,own[req.url]));res.writeHead(200,{'content-type':req.url.endsWith('.mjs')?'text/javascript':req.url.endsWith('.css')?'text/css':'text/html; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self';script-src 'self';style-src 'self';connect-src 'self' blob:;img-src 'self' blob: data:;object-src 'none';frame-ancestors 'none'"});res.end(b);return;
   }
   if(req.url==='/live'&&req.method==='GET'){
    if(!admitted(await free()))return json(503,{error:'DISK_FLOOR_HEADROOM'});
    let html=await readFile(path.join(ROOT,'pilot/aeris57/index.html'),'utf8');
    html=html.replace('<title>AERIS · Simulator Workspace</title>','<title>AERIS · Điều khiển SITL trực tiếp</title>').replace('Simulator</small>','SITL trực tiếp</small>').replace('href="/" aria-label','href="/" aria-label');
    html=html.replace('</head>','<link rel="stylesheet" href="/live-controls.css"></head>').replace('</body>','<script type="module" src="/live-controls.mjs"></script></body>');
    res.writeHead(200,{'content-type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self';script-src 'self';style-src 'self' 'unsafe-inline';img-src 'self' data: blob:;connect-src 'self' blob:;object-src 'none';frame-ancestors 'none'"});res.end(html);return;
   }
   // Existing core retains its exact token/origin/action/session/boot/lease guards.
   core.server.emit('request',req,res);
  }catch(e){if(!res.headersSent)json(500,{error:e.message});else res.end()}
 });
 server.requestTimeout=65000;server.headersTimeout=10000;server.maxConnections=24;
 await new Promise((ok,no)=>{server.once('error',no);server.listen(port,'127.0.0.1',ok)});
 return server;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const server=await startShowcase();console.log('SHOWCASE78 http://127.0.0.1:8828/ pid '+process.pid);
 for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>server.close(()=>process.exit(0)));
}
