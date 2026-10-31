import http from'node:http';import fs from'node:fs';import{fileURLToPath}from'node:url';import{createHash}from'node:crypto';
import{pinned,projectUI,projectHTML}from'./project-ui.mjs';import{parseKml}from'../workbench01/kml.mjs';import{createPlan,DEFAULTS,HOME,ENERGY,preflight,replay,analyze,reflyProposal,makeBundle,receive}from'../workbench01/core.mjs';import{CAMERA}from'../mapping51/common.mjs';import{SAMPLES}from'../mapping51/fixtures.mjs';import{prepareSITL,sitlFixture}from'./sitl-contract.mjs';
const R=fileURLToPath(new URL('../../',import.meta.url)),PORT=8892,ORIGIN=`http://127.0.0.1:${PORT}`,ui=projectUI();
const assets={'/ui.css':['pilot/workbench01/ui.css','text/css'],'/workflow.mjs':['pilot/workbench01/workflow.mjs','text/javascript'],'/font-medium.ttf':['native/crew02/assets/fonts/Barlow-Medium.ttf','font/ttf'],'/font-semibold.ttf':['native/crew02/assets/fonts/Barlow-SemiBold.ttf','font/ttf'],'/font-bold.ttf':['native/crew02/assets/fonts/Barlow-Bold.ttf','font/ttf']};
const own={'/native-bridge.mjs':'native-bridge.mjs','/mock-native.mjs':'mock-native.mjs','/mock-provider.mjs':'mock-provider.mjs'},fontPins=JSON.parse(fs.readFileSync(R+'evidence/workbench01/handoff-manifest.json')).fontPins;let active=0;
const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self';script-src 'self';style-src 'self';font-src 'self';img-src 'self' blob: data:;connect-src 'self';object-src 'none';base-uri 'none';frame-ancestors 'none'"};
const server=http.createServer(async(req,res)=>{const send=(s,x)=>{res.writeHead(s,{...headers,'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(x));};try{if(req.headers.host!==`127.0.0.1:${PORT}`)return send(403,{error:'HOST_REFUSED'});
 if(req.method==='GET'){
  if(req.url==='/api/defaults')return send(200,{options:DEFAULTS,camera:CAMERA,home:HOME,energy:ENERGY,samples:SAMPLES,operational:false});
  if(req.url==='/api/health')return send(200,{platform:'NATIVE02_HOST_COMPANION_MOCK_ONLY',flightDispatch:false,projection:{...ui,source:undefined},freeBytes:fs.statfsSync(R).bavail*fs.statfsSync(R).bsize});
  if(req.url==='/'||req.url==='/mock'){res.writeHead(200,{...headers,'Content-Type':'text/html; charset=utf-8'});return res.end(projectHTML(req.url==='/mock'));}
  if(req.url==='/ui.mjs'){res.writeHead(200,{...headers,'Content-Type':'text/javascript; charset=utf-8'});return res.end(ui.source);}
  if(own[req.url]){res.writeHead(200,{...headers,'Content-Type':'text/javascript; charset=utf-8'});return res.end(fs.readFileSync(new URL(own[req.url],import.meta.url)));}
  const row=assets[req.url];if(!row)return send(404,{error:'NOT_FOUND'});const b=row[0].startsWith('pilot/workbench01')?pinned(row[0]):fs.readFileSync(R+row[0]);if(fontPins[row[0]]&&createHash('sha256').update(b).digest('hex')!==fontPins[row[0]])throw Error('FONT_DRIFT');res.writeHead(200,{...headers,'Content-Type':row[1]});return res.end(b);
 }
 if(req.method!=='POST')return send(405,{error:'METHOD'});if(req.headers.origin!==ORIGIN||!/^application\/json(?:;|$)/.test(req.headers['content-type']??''))return send(403,{error:'ORIGIN_OR_TYPE'});const st=fs.statfsSync(R);if(st.bavail*st.bsize<20*2**30)return send(507,{error:'PHYSICAL_FLOOR_20_GIB'});if(active>=2)return send(429,{error:'BUSY_NO_QUEUE'});active++;
 try{let size=0,parts=[];for await(const b of req){size+=b.length;if(size>3145728)throw Error('REQUEST_BOUND');parts.push(b);}const d=JSON.parse(Buffer.concat(parts));let out;
 if(req.url==='/api/parse')out={document:await parseKml(d.kml)};
 else if(req.url==='/api/native/sitl-fixture')out={input:sitlFixture(d.kind??'polygon')};
 else if(req.url==='/api/native/validate'){if(typeof d.body!=='string'||Buffer.byteLength(d.body)>2097152)throw Error('NATIVE_BODY_BOUND');const b=JSON.parse(d.body),doc=await parseKml(b.input?.kml);receive(b,doc);out={bodySha256:createHash('sha256').update(d.body).digest('hex'),workspaceSha256:b.sha256,authorityRestorable:false};}
 else if(req.url==='/api/receive'){const doc=await parseKml(d.bundle?.input?.kml);out=receive(d.bundle,doc);}
 else{if(!['/api/compile','/api/replay','/api/analyze','/api/export','/api/native/sitl-prepare'].includes(req.url))return send(404,{error:'NO_FLIGHT_DISPATCH_ROUTE'});const doc=await parseKml(d.input?.kml),plan=createPlan(doc,d.input),ready=preflight(plan);
 if(req.url==='/api/compile')out={plan,ready,analysis:analyze(plan,[],d.stepM??5)};
 if(req.url==='/api/native/sitl-prepare')out={preparation:await prepareSITL(plan,{confirmSyntheticHomeAmsl10:d.confirmSyntheticHomeAmsl10})};
 if(req.url==='/api/replay'){if(d.consent!==true||d.planSha256!==plan.sha256||!ready.readyForMock)throw Error('MOCK_REPLAY_NOT_APPROVED');const records=replay(plan,d.scenario);out={records,analysis:analyze(plan,records,d.stepM??5)};}
 if(req.url==='/api/analyze'){const analysis=analyze(plan,d.records,d.stepM??5);out={analysis,proposal:reflyProposal(plan,analysis)};}
 if(req.url==='/api/export')out={bundle:makeBundle(plan,d.records,d.stepM??5)};
 }return send(200,{ok:true,...out});}finally{active--;}
 }catch(e){if(!res.headersSent)send(400,{ok:false,error:String(e.message).slice(0,240)});else res.destroy();}});server.requestTimeout=10000;server.headersTimeout=5000;
server.listen(PORT,'127.0.0.1',()=>console.log(JSON.stringify({url:ORIGIN,mockPreview:ORIGIN+'/mock',pid:process.pid,flightDispatch:false})));
for(const s of['SIGTERM','SIGINT'])process.once(s,()=>server.close(()=>process.exit(0)));
