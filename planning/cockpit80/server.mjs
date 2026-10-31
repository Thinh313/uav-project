import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath}from'node:url';
const root=path.dirname(fileURLToPath(import.meta.url)),fonts=path.resolve(root,'../../native/cockpit66/assets');
const publicFiles=new Map([['/','index.html'],['/index.html','index.html'],['/cockpit.css','cockpit.css'],['/glass.css','glass.css'],['/cockpit.mjs','cockpit.mjs'],['/mock-model.mjs','mock-model.mjs'],['/assets/camera-concept.png','assets/camera-concept.png']]);
const server=http.createServer(async(req,res)=>{try{
 res.setHeader('Content-Security-Policy',"default-src 'self'; connect-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'none'");res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control','no-store');
 if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);return res.end('Read-only mock; no command API');}
 const u=new URL(req.url,'http://127.0.0.1');let p;if(u.pathname==='/favicon.ico'){res.writeHead(204);return res.end();}if(publicFiles.has(u.pathname))p=path.join(root,publicFiles.get(u.pathname));else if(/^\/fonts\/Barlow-(Medium|SemiBold|Bold)\.ttf$/.test(u.pathname))p=path.join(fonts,path.basename(u.pathname));else{res.writeHead(404);return res.end('No operational route');}
 const b=await fs.readFile(p),types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.png':'image/png','.ttf':'font/ttf'};res.writeHead(200,{'Content-Type':types[path.extname(p)],'Content-Length':b.length});res.end(req.method==='HEAD'?undefined:b);
 }catch(e){res.writeHead(500);res.end('Mock asset unavailable');}});
server.listen(Number(process.env.COCKPIT80_PORT??8840),'127.0.0.1',()=>console.log(JSON.stringify({port:server.address().port,pid:process.pid,scope:'Read-only COCKPIT80 design mock; no flight API'})));
for(const s of ['SIGINT','SIGTERM'])process.on(s,()=>server.close(()=>process.exit(0)));
