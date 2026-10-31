import http from 'node:http';import fs from 'node:fs';import {readFile}from'node:fs/promises';import {fileURLToPath}from'node:url';import {performance}from'node:perf_hooks';
import {parseKml}from'./kml.mjs';import{createPlan,DEFAULTS,ENERGY,HOME,preflight,replay,analyze,makeBundle,receive,reflyProposal}from'./core.mjs';import{CAMERA}from'../mapping51/common.mjs';import{SAMPLES}from'../mapping51/fixtures.mjs';
const ROOT=fileURLToPath(new URL('../../',import.meta.url)),PORT=Number(process.env.WORKBENCH_PORT??8890);if(!Number.isInteger(PORT)||PORT<1024||PORT>65535)throw Error('PORT');
const assets=new Map([['/','pilot/workbench01/index.html'],['/ui.css','pilot/workbench01/ui.css'],['/ui.mjs','pilot/workbench01/ui.mjs'],['/workflow.mjs','pilot/workbench01/workflow.mjs'],['/font-medium.ttf','native/crew02/assets/fonts/Barlow-Medium.ttf'],['/font-semibold.ttf','native/crew02/assets/fonts/Barlow-SemiBold.ttf'],['/font-bold.ttf','native/crew02/assets/fonts/Barlow-Bold.ttf']]);
const mime={html:'text/html; charset=utf-8',css:'text/css; charset=utf-8',mjs:'text/javascript; charset=utf-8',ttf:'font/ttf'};let active=0;
const security={'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' blob: data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",'X-Content-Type-Options':'nosniff','Cache-Control':'no-store','Referrer-Policy':'no-referrer'};
const server=http.createServer(async(req,res)=>{const started=performance.now();const send=(code,body)=>{res.writeHead(code,{...security,'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(body));};
 try{const authority=`127.0.0.1:${PORT}`;if(req.headers.host!==authority){send(403,{error:'HOST_REFUSED'});return;}
 if(req.method==='GET'){
  if(req.url==='/api/defaults'){send(200,{options:DEFAULTS,camera:CAMERA,home:HOME,energy:ENERGY,samples:SAMPLES,operational:false});return;}
  if(req.url==='/api/health'){const s=fs.statfsSync(ROOT);send(200,{status:'HOST_MOCK_ONLY',freeBytes:s.bavail*s.bsize,operational:false,active});return;}
  const asset=assets.get(req.url);if(!asset){send(404,{error:'NOT_FOUND'});return;}const b=await readFile(ROOT+asset);res.writeHead(200,{...security,'Content-Type':mime[asset.split('.').at(-1)]});res.end(b);return;
 }
 if(req.method!=='POST'){send(405,{error:'METHOD'});return;}
 if(req.headers.origin!==`http://${authority}`||!/^application\/json(?:;|$)/.test(req.headers['content-type']??'')){send(403,{error:'ORIGIN_OR_TYPE'});return;}
 const st=fs.statfsSync(ROOT);if(st.bavail*st.bsize<20*2**30){send(507,{error:'PHYSICAL_FLOOR_20_GIB'});return;}
 if(active>=2){send(429,{error:'BUSY_NO_QUEUE'});return;}active++;
 try{let bytes=0,chunks=[];for await(const c of req){bytes+=c.length;if(bytes>2097152){send(413,{error:'REQUEST_BOUND'});req.destroy();return;}chunks.push(c);}const body=JSON.parse(Buffer.concat(chunks).toString());let out;
  if(req.url==='/api/parse'){out={document:await parseKml(body.kml)};}
  else if(req.url==='/api/receive'){const d=await parseKml(body.bundle?.input?.kml);out=receive(body.bundle,d);}
  else{
   if(!['/api/compile','/api/replay','/api/analyze','/api/export'].includes(req.url)){send(404,{error:'NOT_FOUND'});return;}
   const d=await parseKml(body.input?.kml),plan=createPlan(d,body.input),ready=preflight(plan);
   if(req.url==='/api/compile')out={plan,ready,analysis:analyze(plan,[],body.stepM??5)};
   if(req.url==='/api/replay'){if(body.consent!==true||body.planSha256!==plan.sha256||!ready.readyForMock)throw Error('MOCK_REPLAY_NOT_APPROVED');const records=replay(plan,body.scenario);out={records,analysis:analyze(plan,records,body.stepM??5)};}
   if(req.url==='/api/analyze'){const analysis=analyze(plan,body.records,body.stepM??5);out={analysis,proposal:reflyProposal(plan,analysis)};}
   if(req.url==='/api/export')out={bundle:makeBundle(plan,body.records,body.stepM??5)};
  }
  send(200,{ok:true,...out,computeMs:performance.now()-started});
 }finally{active--;}
 }catch(e){if(!res.headersSent)send(400,{ok:false,error:String(e.message).slice(0,240)});else res.destroy();}
});server.requestTimeout=10000;server.headersTimeout=5000;server.listen(PORT,'127.0.0.1',()=>console.log(JSON.stringify({url:`http://127.0.0.1:${PORT}/`,pid:process.pid,scope:'WORKBENCH01_HOST_MOCK_ONLY'})));
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));process.on('SIGINT',()=>server.close(()=>process.exit(0)));
