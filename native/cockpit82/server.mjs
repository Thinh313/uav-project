import {createServer} from 'node:http';
import {readFile,statfs} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateCapsule44} from './assets/workflow/capsule.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const allowed=new Set(JSON.parse(await readFile(path.join(root,'asset-list.json'),'utf8')));
export function journal82(action,dir,token='ROOT',body=''){
 if(!['save','load'].includes(action))throw Error('STORAGE_ACTION_ONLY');
 return new Promise((resolve,reject)=>{
  const child=spawn('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/java',['-cp',path.join(root,'dist/journal-host82.jar'),'vn.rtr.aeris.cockpit82.JournalMain',action,dir,...(action==='save'?[token]:[])],{stdio:['pipe','pipe','pipe']});
  let output='',error='',done=false;const timer=setTimeout(()=>{child.kill('SIGKILL');finish(Error('COMMIT_UNKNOWN_NO_RETRY'));},12000);
  const finish=(err,value)=>{if(done)return;done=true;clearTimeout(timer);err?reject(err):resolve(value);};
  child.stdout.on('data',b=>{output+=b;if(output.length>400000){child.kill('SIGKILL');finish(Error('JOURNAL_REPLY_BOUND'));}});child.stderr.on('data',b=>{error=(error+b).slice(0,2000);});child.stdin.on('error',()=>{});child.on('error',finish);child.on('close',code=>{if(done)return;if(code!==0)return finish(Error(error.slice(0,500)));try{finish(null,JSON.parse(output));}catch(e){finish(e);}});child.stdin.end(body);
 });
}
export function preview82({store=path.resolve('.local/cockpit82/preview')}={}){
 let writing=false;
 const server=createServer(async(req,res)=>{
  const headers={'Cache-Control':'no-store','Content-Security-Policy':"default-src 'self';connect-src 'self';style-src 'self' 'unsafe-inline';object-src 'none';frame-src 'none';base-uri 'none'",'X-Content-Type-Options':'nosniff'};
  const send=(code,value)=>res.writeHead(code,{...headers,'Content-Type':'application/json'}).end(JSON.stringify(value));
  try{
   if(!/^127\.0\.0\.1:\d+$/.test(req.headers.host??''))return send(403,{ok:false,error:'HOST_REFUSED'});
   const origin='http://'+req.headers.host;if(req.headers.origin&&req.headers.origin!==origin)return send(403,{ok:false,error:'ORIGIN_REFUSED'});
   if(req.method==='GET'&&req.url==='/workspace/load')return send(200,await journal82('load',store));
   if(req.method==='GET'&&req.url==='/health')return send(200,{scope:'HOST_UI_JAVA_JOURNAL_NOT_ANDROID',pid:process.pid,signing:false,flight:false});
   if(req.method==='POST'&&req.url==='/workspace/save'){
    if(writing||req.headers.origin!==origin||req.headers['content-type']!=='application/json')return send(409,{ok:false,error:'WRITER_ORIGIN_TYPE'});
    writing=true;try{
     let bytes=0,parts=[];for await(const part of req){bytes+=part.length;if(bytes>524544)throw Error('REQUEST_BOUND');parts.push(part);}
     const d=JSON.parse(Buffer.concat(parts).toString('utf8'));
     if(Object.keys(d).sort().join()!=='body,token'||typeof d.body!=='string'||typeof d.token!=='string'||!/^(ROOT|[a-f0-9]{64})$/.test(d.token))throw Error('SAVE_SCHEMA');
     const f=await statfs(root,{bigint:true});if(f.bavail*f.bsize<20n*1024n**3n+16n*1024n**2n+2n*BigInt(Buffer.byteLength(d.body)))throw Error('HOST_20GIB_FLOOR');
     await validateCapsule44(d.body);return send(200,await journal82('save',store,d.token,d.body));
    }finally{writing=false;}
   }
   if(req.method!=='GET')return send(405,{ok:false,error:'NO_FLIGHT_TRANSPORT'});
   const name=req.url==='/'?'/index.html':req.url;if(!allowed.has(name))return send(404,{ok:false,error:'ASSET_WHITELIST'});
   const bytes=await readFile(path.join(root,'assets',name.slice(1))),type=name.endsWith('.ttf')?'font/ttf':name.endsWith('.css')?'text/css':name.endsWith('.html')?'text/html':name.endsWith('.png')?'image/png':'text/javascript';res.writeHead(200,{...headers,'Content-Type':type,'Content-Length':bytes.length});res.end(bytes);
  }catch(e){send(409,{ok:false,error:e.message});}
 });
 server.requestTimeout=server.headersTimeout=15000;server.keepAliveTimeout=1000;server.maxConnections=8;return server;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const server=preview82();server.listen(8844,'127.0.0.1',()=>console.log(JSON.stringify({url:'http://127.0.0.1:8844/',pid:process.pid,scope:'Host native82 assets + actual Java journal; no Android or flight'})));for(const s of ['SIGINT','SIGTERM'])process.on(s,()=>server.close(()=>process.exit(0)));}
