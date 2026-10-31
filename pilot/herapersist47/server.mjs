import {createServer} from 'node:http';
import {readFile,statfs} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {Durable47} from './workspace.mjs';
import {storage47} from './storage.mjs';
import {replayCapsule} from './capsule.mjs';
import {digest} from '../heramcu45/schema.mjs';
const root=fileURLToPath(new URL('.',import.meta.url)),project=path.resolve(root,'../..');
export function preview47({store=path.join(project,'.local/herapersist47/operator')}={}){const engine=new Durable47(storage47(store));let token=null;
 const server=createServer(async(req,res)=>{const host=req.headers.host??'',origin='http://'+host,h={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'none'; frame-ancestors 'none'"};const send=(s,d)=>res.writeHead(s,{...h,'Content-Type':'application/json'}).end(JSON.stringify(d));
 try{
  if(!/^127\.0\.0\.1:\d+$/.test(host)||req.headers.origin&&req.headers.origin!==origin)return send(403,{error:'ORIGIN_REFUSED'});
  if(req.method==='GET'&&['/','/shell.mjs','/shell.css','/persist.css','/font.ttf'].includes(req.url)){const name=req.url==='/'?'index.html':req.url.slice(1),p=name==='font.ttf'?path.join(project,'native/preflight44/assets/IBMPlexSans.ttf'):name==='shell.css'?path.join(project,'pilot/heraui46/shell.css'):path.join(root,name),bytes=await readFile(p);res.writeHead(200,{...h,'Content-Type':name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':name.endsWith('.ttf')?'font/ttf':'text/javascript'});return res.end(bytes);}
  if(req.method==='POST'&&['/api/create','/api/action','/api/recover','/api/check-workspace'].includes(req.url)){
   if(req.headers.origin!==origin||req.headers['content-type']!=='application/json')return send(403,{error:'POST_ORIGIN_JSON_REQUIRED'});const f=await statfs(root,{bigint:true});if(f.bavail*f.bsize<20n*1024n**3n+16777216n)return send(409,{error:'HOST_20GIB_FLOOR'});const pieces=[];let n=0;for await(const b of req){n+=b.length;if(n>300000)throw Error('REQUEST_BOUND');pieces.push(b);}const d=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(pieces)));
   if(req.url==='/api/create'){if(Object.keys(d).length)throw Error('CREATE_SCHEMA');const view=await engine.load();token=randomUUID();return send(200,{token,view});}
   if(!token||req.headers['x-workspace']!==token)return send(403,{error:'WORKSPACE_TOKEN_REVOKED_RELOAD_REQUIRED'});
   if(req.url==='/api/check-workspace'){const r=replayCapsule(d.record,d.expectedSha||null);return send(200,{workspaceReplay:{status:r.status,epochs:d.record.epochs.length,operations:d.record.seal.operationCount,storedMockSha256:digest(r.stored),expectedShaMatched:!!d.expectedSha,authorityRestorable:false}});}
   if(req.url==='/api/recover'){if(Object.keys(d).length)throw Error('RECOVER_SCHEMA');return send(200,{view:await engine.load()});}
   if(Object.keys(d).sort().join()!=='data,kind,revision')throw Error('ACTION_SCHEMA');try{return send(200,{view:await engine.dispatch(d.kind,d.data,d.revision)});}catch(e){return send(409,{error:e.message,view:engine.view()});}
  }
  if(!token||req.headers['x-workspace']!==token)return send(403,{error:'WORKSPACE_TOKEN_REVOKED_RELOAD_REQUIRED'});
  if(req.method==='GET'&&req.url==='/api/view')return send(200,{view:engine.view()});
  if(req.method==='GET'&&req.url==='/api/checkpoint')return send(200,{record:engine.exportCapsule()});
  if(req.method==='GET'&&/^\/api\/export\?index=\d{1,2}$/.test(req.url))return send(200,{record:engine.archive(Number(req.url.split('=').at(-1)))});
  send(404,{error:'NO_PHYSICAL_TRANSPORT_ROUTE'});
 }catch(e){send(409,{error:e.message});}});server.requestTimeout=10000;server.headersTimeout=10000;server.keepAliveTimeout=1000;server.maxConnections=8;return server;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const server=preview47({store:process.env.HERA47_STORE??undefined});server.listen(Number(process.env.HERA47_PORT??8801),'127.0.0.1',()=>console.log('HERAPERSIST47 MOCK port '+server.address().port+' pid '+process.pid));for(const sig of ['SIGTERM','SIGINT'])process.on(sig,()=>server.close(()=>process.exit(0)));}
