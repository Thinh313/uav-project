import {createServer} from 'node:http';
import {readFile,mkdir,statfs} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {randomBytes} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {Store} from './store.mjs';
import {Workspace,replay,context,observedScenario} from './workspace.mjs';
import {stable,sha,seal,unseal,exact,clone} from './common.mjs';
import {SCENARIOS} from './readiness.mjs';
import {SAMPLES} from './fixtures.mjs';
const H=path.dirname(fileURLToPath(import.meta.url)),R=path.resolve(H,'../..'),now=()=>1000000+performance.now();
export async function preview(root=path.join(R,'.local/mapping51/operator')){
 const s=await statfs(R,{bigint:true});if(Number(s.bavail*s.bsize)<20*2**30+32*2**20)throw Error('HOST_FLOOR_20GIB');
 await mkdir(path.dirname(root),{recursive:true});const store=new Store(root),token=randomBytes(32).toString('hex');let busy=false,loadError=null,cold=false;
 try{await store.load();cold=store.records.length>0;await store.w.apply({type:'RESET',atMs:now(),data:{}})}catch(e){loadError=e.message;store.error=e.message}
 async function append(type,data,at=now()){
  if(loadError||store.error)throw Error('STORE_BLOCKED_'+(loadError??store.error));
  if(cold){await store.append({type:'RESET',atMs:now(),data:{}});cold=false;}
  await store.append({type,atMs:at,data});
 }
 function view(){const w=store.w,m=w.machine,t=now(),r=m.report(t),stale=(m.status==='RUNNING'||m.status==='REVIEWED')&&!r.readyForMock;return {format:'mapping51-view',scope:'HOST_MOCK_ONLY',operational:false,head:store.records.at(-1)?.sha256??'',revision:store.records.length,document:w.document,source:w.source,featureId:w.featureId,options:w.options,camera:w.camera,plan:m.plan,machine:m.snapshot(),effectiveStatus:(loadError||store.error)?'BLOCKED_STORAGE':stale?'INTERRUPTED_REQUIRES_REVIEW':m.status,readiness:r,store:{error:loadError??store.error,bytes:store.bytes,capBytes:16*2**20,records:store.records.length,maxRecords:64,coldDisconnected:cold},reviewCode:m.plan?'MOCK-'+m.plan.sha256.slice(0,8):null,actualFiles:0,fieldAccepted:false};}
 const server=createServer(async(req,res)=>{
  const host=req.headers.host??'',origin='http://'+host,h={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self';object-src 'none';frame-src 'none';base-uri 'none';form-action 'none'"},send=(code,x)=>res.writeHead(code,{...h,'Content-Type':'application/json'}).end(JSON.stringify(x));let held=false;
  try{
   if(!/^127\.0\.0\.1:\d+$/.test(host)||req.headers.origin&&req.headers.origin!==origin)return send(403,{ok:false,error:'ORIGIN_REFUSED'});
   const assets={'/':'index.html','/shell.mjs':'shell.mjs','/shell.css':'shell.css','/font.ttf':'../../native/preflight44/assets/IBMPlexSans.ttf'};
   if(req.method==='GET'&&assets[req.url]){const f=assets[req.url];res.writeHead(200,{...h,'Content-Type':f.endsWith('.html')?'text/html':f.endsWith('.css')?'text/css':f.endsWith('.ttf')?'font/ttf':'text/javascript'}).end(await readFile(path.join(H,f)));return;}
   if(req.method==='GET'&&req.url==='/api/bootstrap')return send(200,{ok:true,token,scenarios:SCENARIOS,samples:SAMPLES});
   if(req.headers['x-workspace-token']!==token)return send(403,{ok:false,error:'TOKEN_REFUSED'});
   if(busy)return send(409,{ok:false,error:'BUSY_NO_RETRY'});busy=held=true;
   if(req.method==='GET'&&req.url==='/api/view')return send(200,{ok:true,view:view()});
   if(req.method==='GET'&&req.url==='/api/export'){if(loadError||store.error)throw Error('STORE_BLOCKED_EXPORT');const bundle=seal({format:'aeris-mapping51-review',version:1,scope:'HOST_MOCK_ONLY',operational:false,records:clone(store.records)});res.writeHead(200,{...h,'Content-Type':'application/json','Content-Disposition':'attachment; filename="mapping51-review.json"'}).end(JSON.stringify(bundle));return;}
   if(req.method!=='POST'||!['/api/import-kml','/api/configure','/api/observe','/api/review','/api/start','/api/step','/api/close','/api/inspect'].includes(req.url))return send(404,{ok:false,error:'NO_FLIGHT_OR_ARBITRARY_FILE_ROUTE'});
   if(req.headers.origin!==origin||req.headers['content-type']!=='application/json')return send(403,{ok:false,error:'POST_ORIGIN_TYPE'});
   const chunks=[];let len=0;for await(const b of req){len+=b.length;if(len>(req.url==='/api/inspect'?17:1)*2**20)throw Error('REQUEST_SIZE');chunks.push(b)}const a=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));exact(a,'expectedHead,data','REQUEST');
   if(a.expectedHead!==(store.records.at(-1)?.sha256??''))throw Error('STALE_HEAD_RELOAD_NO_RETRY');const d=a.data;
   if(req.url==='/api/inspect'){
    exact(d,'bundle','INSPECT');const b=d.bundle;exact(b,'format,version,scope,operational,records,sha256','BUNDLE');unseal(b);if(b.format!=='aeris-mapping51-review'||b.version!==1||b.scope!=='HOST_MOCK_ONLY'||b.operational!==false)throw Error('BUNDLE_VERSION');const w=await replay(b.records);return send(200,{ok:true,inspection:{integrity:'VERIFIED_CHAIN_AND_SEMANTIC_REPLAY',records:b.records.length,historicalStatus:w.machine.status,syntheticCounts:w.machine.counts,actualFiles:0,authorityRestored:false,operational:false},view:view()});
   }
   if(req.url==='/api/import-kml')await append('IMPORT_KML',d);
   if(req.url==='/api/configure')await append('CONFIGURE',d);
   if(req.url==='/api/observe'){
    exact(d,'scenario','SCENARIO');if(!store.w.machine.ctx||store.w.machine.status==='CLOSED')await append('CONNECT_MOCK',{context:context()});const t=now(),o=observedScenario(store.w,t,d.scenario);await append('OBSERVE',{observation:o},t);
   }
   if(req.url==='/api/review')await append('REVIEW',d);
   if(req.url==='/api/start'){exact(d,'planSha256','START');if(d.planSha256!==store.w.machine.plan?.sha256)throw Error('PLAN_CHANGED');await append('START',{});}
   if(req.url==='/api/step')await append('STEP',d);
   if(req.url==='/api/close'){exact(d,'','CLOSE');await append('CLOSE',{});}
   send(200,{ok:true,view:view()});
  }catch(e){send(409,{ok:false,error:e.message})}finally{if(held)busy=false}
 });server.requestTimeout=15000;server.headersTimeout=10000;server.maxConnections=8;return server;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const s=await preview(process.env.MAPPING51_STORE?path.resolve(process.env.MAPPING51_STORE):undefined);s.listen(Number(process.env.MAPPING51_PORT??8805),'127.0.0.1',()=>console.log('MAPPING51 port '+s.address().port+' pid '+process.pid));for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>s.close(()=>process.exit(0)))}
