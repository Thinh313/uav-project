import {createServer} from 'node:http';
import {readFile,statfs} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {validateCapsule} from './capsule.mjs';
const root=fileURLToPath(new URL('.',import.meta.url));
const files=new Set(['index.html','shell.css','shell.mjs','journey.mjs','editor.mjs','pins.mjs','vendor/survey.mjs','vendor/compiler.mjs','capsule.mjs','route.mjs','assets/IBMPlexSans.ttf',...['common','geometry','airspace','flightops','fence'].map(n=>'core/'+n+'.mjs')]);
export function journal(mode,dir,token='ROOT',body='') {
  return new Promise((resolve,reject)=>{
    const p=spawn('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/java',['-cp',path.join(root,'dist/journal-host.jar'),'vn.rtr.aeris.flightops35.JournalMain',mode,dir,...(mode==='save'?[token]:[])],{stdio:['pipe','pipe','pipe']});
    let out='',err='';const timer=setTimeout(()=>{p.kill('SIGKILL');reject(Error('Journal timeout; commit unknown'))},10000);
    p.stdout.on('data',b=>{out+=b;if(out.length>400000)p.kill('SIGKILL')});p.stderr.on('data',b=>err+=b.toString().slice(0,4096));p.stdin.on('error',()=>{});
    p.on('error',e=>{clearTimeout(timer);reject(e)});p.on('close',code=>{clearTimeout(timer);if(code!==0){reject(Error(err.slice(0,500)));return;}try{resolve(JSON.parse(out))}catch(e){reject(e)}});p.stdin.end(body);
  });
}
export function preview({store=path.join(root,'.preview-store')}={}) {
  let writing=false;
  const server=createServer(async(req,res)=>{
    const origin='http://'+req.headers.host,headers={'Cache-Control':'no-store','Content-Security-Policy':"default-src 'self';object-src 'none';frame-src 'none';base-uri 'none'",'X-Content-Type-Options':'nosniff'};
    const send=(code,d)=>res.writeHead(code,{...headers,'Content-Type':'application/json'}).end(JSON.stringify(d));
    try{
      if(!/^127\.0\.0\.1:\d+$/.test(req.headers.host??'')||req.headers.origin&&req.headers.origin!==origin){send(403,{ok:false,error:'Origin refused'});return;}
      if(req.method==='GET'&&req.url==='/workspace/load'){send(200,await journal('load',store));return;}
      if(req.method==='POST'&&req.url==='/workspace/save'){
        if(req.headers.origin!==origin||req.headers['content-type']!=='application/json'||writing){send(409,{ok:false,error:'Writer/origin/type refused'});return;}
        writing=true;
        try{let size=0;const pieces=[];for await(const b of req){size+=b.length;if(size>524544)throw Error('Request bound');pieces.push(b);}const d=JSON.parse(Buffer.concat(pieces).toString());if(Object.keys(d).sort().join()!=='body,token'||typeof d.body!=='string'||! /^(ROOT|[a-f0-9]{64})$/.test(d.token))throw Error('Save schema');const space=await statfs(root,{bigint:true});if(space.bavail*space.bsize<20n*1024n**3n+8388608n+2n*BigInt(Buffer.byteLength(d.body)))throw Error('Host storage floor20GiB; preserve evidence');await validateCapsule(d.body);send(200,await journal('save',store,d.token,d.body));}finally{writing=false;}return;
      }
      if(req.method!=='GET'){send(405,{ok:false,error:'Offline mock only; no flight endpoint'});return;}
      const name=req.url==='/'?'index.html':req.url.slice(1);if(!files.has(name)){send(404,{ok:false,error:'Offline asset only'});return;}
      const bytes=await readFile(path.join(root,name));res.writeHead(200,{...headers,'Content-Type':name.endsWith('.ttf')?'font/ttf':name.endsWith('.css')?'text/css':name.endsWith('.html')?'text/html':'text/javascript','Content-Length':bytes.length}).end(bytes);
    }catch(e){send(409,{ok:false,error:e.message})}
  });
  server.requestTimeout=server.headersTimeout=10000;server.keepAliveTimeout=1000;server.maxConnections=8;return server;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  const s=preview();s.listen(8798,'127.0.0.1',()=>console.log('NATIVE35 HOST PREVIEW http://127.0.0.1:8798 PID '+process.pid));
  for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>s.close(()=>process.exit(0)));
}
