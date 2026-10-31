import {createServer} from 'node:http';
import {readFile,statfs} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {Workspace46} from './workspace.mjs';
const root=fileURLToPath(new URL('.',import.meta.url)),project=path.resolve(root,'../..');
export function preview46(){const sessions=new Map();const server=createServer(async(req,res)=>{
 const host=req.headers.host??'',origin='http://'+host,h={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"};
 const send=(status,obj)=>res.writeHead(status,{...h,'Content-Type':'application/json'}).end(JSON.stringify(obj));
 try{
  if(!/^127\.0\.0\.1:\d+$/.test(host)||req.headers.origin&&req.headers.origin!==origin)return send(403,{error:'ORIGIN_REFUSED'});
  if(req.method==='GET'&&['/','/shell.mjs','/shell.css','/font.ttf'].includes(req.url)){const name=req.url==='/'?'index.html':req.url.slice(1),p=name==='font.ttf'?path.join(project,'native/preflight44/assets/IBMPlexSans.ttf'):path.join(root,name),bytes=await readFile(p);res.writeHead(200,{...h,'Content-Type':name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':name.endsWith('.ttf')?'font/ttf':'text/javascript','Content-Length':bytes.length});return res.end(bytes);}
  if(req.method==='POST'&&['/api/create','/api/action'].includes(req.url)){
   if(req.headers.origin!==origin||req.headers['content-type']!=='application/json')return send(403,{error:'POST_ORIGIN_JSON_REQUIRED'});
   const s=await statfs(root,{bigint:true});if(s.bavail*s.bsize<20n*1024n**3n+16777216n)return send(409,{error:'HOST_20GIB_FLOOR'});
   const pieces=[];let n=0;for await(const b of req){n+=b.length;if(n>300000)throw Error('REQUEST_BOUND');pieces.push(b);}const d=JSON.parse(Buffer.concat(pieces).toString('utf8'));
   if(req.url==='/api/create'){if(Object.keys(d).length)throw Error('CREATE_SCHEMA');if(sessions.size>=2)throw Error('TWO_WORKSPACE_LIMIT_RESTART_PREVIEW_AFTER_EXPORT');const token=randomUUID(),workspace=new Workspace46();sessions.set(token,workspace);return send(200,{token,view:workspace.view()});}
   const w=sessions.get(req.headers['x-workspace']);if(!w)return send(403,{error:'WORKSPACE_NOT_FOUND_RELOAD_NEW_SESSION'});if(Object.keys(d).sort().join()!=='data,kind,revision')throw Error('ACTION_SCHEMA');try{return send(200,{view:w.dispatch(d.kind,d.data,d.revision)});}catch(e){return send(409,{error:e.message,view:w.view()});}
  }
  if(req.method==='GET'&&req.url==='/api/view'){const w=sessions.get(req.headers['x-workspace']);return w?send(200,{view:w.view()}):send(403,{error:'WORKSPACE_NOT_FOUND_RELOAD_NEW_SESSION'});}
  if(req.method==='GET'&&/^\/api\/export\?index=[0-3]$/.test(req.url)){const w=sessions.get(req.headers['x-workspace']),index=Number(req.url.at(-1));return w&&w.records[index]?send(200,{record:w.records[index]}):send(404,{error:'ARCHIVE_NOT_FOUND'});}
  send(404,{error:'ROUTE_NOT_ALLOWED_NO_PHYSICAL_TRANSPORT'});
 }catch(e){send(409,{error:e.message});}
 });server.requestTimeout=10000;server.headersTimeout=10000;server.keepAliveTimeout=1000;server.maxConnections=8;return server;}
if(process.argv[1]===fileURLToPath(import.meta.url)){const server=preview46();server.requestTimeout=10000;server.headersTimeout=10000;server.maxConnections=8;server.listen(8800,'127.0.0.1',()=>console.log('HERAUI46 MOCK http://127.0.0.1:8800 pid '+process.pid));for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>server.close(()=>process.exit(0)));}
