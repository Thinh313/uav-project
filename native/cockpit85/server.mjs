import {createServer} from 'node:http';
import {readFile,statfs} from 'node:fs/promises';
import {validateCapsule44} from './assets/workflow/capsule.mjs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {journal82} from '../cockpit82/server.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)), store=path.resolve(root,'../../.local/cockpit85/journal');
const assets=new Set(JSON.parse(await readFile(path.join(root,'asset-list.json'),'utf8')));assets.add('/layout85.css');assets.add('/layout85.mjs');assets.add('/bite-alignment.css');assets.add('/bite-overflow.css');
const history=JSON.parse(await readFile(path.resolve(root,'../../evidence/cockpit85/history-fixture.json'),'utf8'));
let writing=false;
const server=createServer(async(req,res)=>{
 const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self';connect-src 'self';style-src 'self' 'unsafe-inline';object-src 'none';frame-src 'none';base-uri 'none'"};
 const json=(code,d)=>res.writeHead(code,{...headers,'Content-Type':'application/json'}).end(JSON.stringify(d));
 try{
  if(req.headers.host!=='127.0.0.1:8848')return json(403,{error:'HOST'});
  if(req.method==='GET'&&req.url==='/health')return json(200,{scope:'COCKPIT85_BROWSER_UI_ONLY_NO_FLIGHT',pid:process.pid});
  if(req.method==='GET'&&req.url.startsWith('/qa85/history?')){
   const q=new URL(req.url,'http://127.0.0.1:8848').searchParams;if(q.get('head')&&q.get('head')!==history.head)return json(409,{ok:false,error:'ARCHIVE_HEAD_MISMATCH'});
   if(q.get('action')==='review-list')return json(200,history.list);
   if(q.get('action')==='review-get'&&history.records[q.get('token')])return json(200,history.records[q.get('token')]);return json(404,{ok:false,error:'ARCHIVE_RECORD_UNKNOWN'});
  }
  if(req.method==='GET'&&req.url==='/workspace/load')return json(200,await journal82('load',store));
  if(req.method==='POST'&&req.url==='/workspace/save'){
   if(writing||req.headers.origin!=='http://127.0.0.1:8848'||req.headers['content-type']!=='application/json')return json(409,{ok:false,error:'REFUSED'});
   writing=true;try{let bytes=0,parts=[];for await(const p of req){bytes+=p.length;if(bytes>524544)throw Error('BODY_BOUND');parts.push(p);}const d=JSON.parse(Buffer.concat(parts));if(typeof d.body!=='string'||typeof d.token!=='string'||!/^(ROOT|[a-f0-9]{64})$/.test(d.token))throw Error('SCHEMA');const free=await statfs(root,{bigint:true});if(free.bavail*free.bsize<20n*1024n**3n+32n*1024n**2n)throw Error('HOST_20GIB_FLOOR');await validateCapsule44(d.body);return json(200,await journal82('save',store,d.token,d.body));}finally{writing=false;}
  }
  if(req.method!=='GET')return json(405,{ok:false,error:'NO_FLIGHT_TRANSPORT'});
  let u=new URL(req.url,'http://127.0.0.1:8848'),name=u.pathname;const before=name.startsWith('/before/');if(before)name=name.slice(7);
  const mock=name==='/mock.html';if(mock||name==='/')name='/index.html';if(!assets.has(name))return json(404,{error:'WHITELIST'});
  let b=await readFile(path.join(before?path.resolve(root,'../native84/assets'):path.join(root,'assets'),name.slice(1)));
  if(name==='/index.html'){
   let s=b.toString();
   if(u.searchParams.get('bite')==='alignment')s=s.replace('</head>','<link rel="stylesheet" href="/bite-alignment.css"></head>');
   if(u.searchParams.get('bite')==='overflow')s=s.replace('</head>','<link rel="stylesheet" href="/bite-overflow.css"></head>');
   if(mock)s=s.replace('<script type="module" src="fly84.mjs"></script>','');

   s=s.replace('<body data-theme="night"','<body data-qa85="browser" data-theme="night"');
   b=Buffer.from(s);
  }
  const type=name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':name.endsWith('.ttf')?'font/ttf':name.endsWith('.png')?'image/png':'text/javascript';res.writeHead(200,{...headers,'Content-Type':type,'Content-Length':b.length});res.end(b);
 }catch(e){json(409,{ok:false,error:e.message});}
});
server.requestTimeout=server.headersTimeout=15000;server.maxConnections=16;server.listen(8848,'127.0.0.1',()=>console.log(JSON.stringify({url:'http://127.0.0.1:8848/mock.html',pid:process.pid})));
for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>server.close(()=>process.exit(0)));
