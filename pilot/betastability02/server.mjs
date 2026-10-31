import{createArchiveWorker}from'./archive-client.mjs';
import{setJournalSpanSink}from'./flight-journal.mjs';
import{traceRange}from'./trace-range.mjs';
import{startNativePublisher}from'./native-publisher.mjs';
import{History}from'./history.mjs';
import http from'node:http';import fs from'node:fs';import path from'node:path';import{fileURLToPath}from'node:url';import{randomBytes,createHash}from'node:crypto';
import{uiProjection,htmlProjection,mediaPanelProjection,pinned}from'./ui-projection.mjs';import{createSession,diskFloor}from'./session.mjs';import{createBetaMedia}from'./media-projection.mjs';
import{parseKml}from'../workbench01/kml.mjs';import{createPlan,ENERGY,preflight,replay,analyze,reflyProposal,makeBundle,receive}from'../workbench01/core.mjs';import{sitlFixture,prepareSITL}from'../workbench02/sitl-contract.mjs';import{FIXTURE92}from'../../native/native94/assets/mission-fixtures92.mjs';
const ROOT=fileURLToPath(new URL('../../',import.meta.url)),ORIGIN='http://127.0.0.1:8896',MEDIA='http://127.0.0.1:8895',sha=b=>createHash('sha256').update(b).digest('hex');
export async function createHost({out,workspaceRoot,allowSitl=false,mediaFactory=createBetaMedia}={}){
 diskFloor();out=path.resolve(out??'');if(!out.startsWith(path.join(ROOT,'evidence/betastability02/'))||fs.existsSync(out))throw Error('EXCLUSIVE_BETA05_ROOT');fs.mkdirSync(out);
 let media,session,publisher;const traceStarts=new Map();try{media=await mediaFactory({port:8895,out:path.join(out,'media'),allowedOrigin:ORIGIN});setJournalSpanSink(data=>media.fullTrace?.append('FLIGHT_STORAGE',data));session=await createSession({out:path.join(out,'session'),workspaceRoot,media,allowSitl});}catch(e){await media?.close();throw e;}
 const history=new History(path.join(ROOT,'evidence/betastability02/history01'));
 let archiveBusy=false,archiveTask=null;const archiveAttempted=new Set();
 const archive=createArchiveWorker({historyRoot:history.root,onSpan:span=>media.fullTrace?.append('ARCHIVE_WORK',span)});
 function archiveReview(r){
  if(archiveBusy)return Promise.reject(Error('ARCHIVE_BUSY_NO_QUEUE'));if(archiveAttempted.has(r.run))return Promise.reject(Error('ARCHIVE_ATTEMPT_ALREADY_MADE_NO_RETRY'));
  archiveBusy=true;archiveAttempted.add(r.run);
  const task=(async()=>{
   if(r.accepted&&r.source==='OBSERVED_OWNED_SITL')await archive.qualify({root:out,review:r});
   if(media.fullTrace&&traceStarts.has(r.run)){await publisher?.barrier();const barrier=await media.fullTrace.barrier('flight-'+r.run),range=await traceRange(path.join(out,'media/full-trace'),traceStarts.get(r.run),barrier.receipt.events,barrier.file);const traceFile=path.join(out,'trace-'+r.run+'.jsonl.gz');if(!fs.existsSync(traceFile)){diskFloor();fs.writeFileSync(traceFile,range.bytes,{flag:'wx'});}}
   const snapshotStartHostMs=Number(process.hrtime.bigint())/1e6,workspaceRoot=session.store.snapshot().root,journalPath=path.join(workspaceRoot,'journal.jsonl'),st=fs.lstatSync(journalPath);
   if(!st.isFile()||st.isSymbolicLink()||st.size>16*2**20)throw Error('PACKAGE_JOURNAL_SNAPSHOT_BOUND');
   const workspaceJournalBytes=fs.readFileSync(journalPath);if(workspaceJournalBytes.length>16*2**20)throw Error('PACKAGE_JOURNAL_SNAPSHOT_BOUND');media.fullTrace?.append('ARCHIVE_SNAPSHOT',{run:r.run,bytes:workspaceJournalBytes.length,startHostMs:snapshotStartHostMs,endHostMs:Number(process.hrtime.bigint())/1e6});
   return archive.archive({root:out,review:r,workspaceRoot,workspaceJournalBytes});
  })();archiveTask=task;
  return task.finally(()=>{archiveBusy=false;archiveTask=null;});
 }

 const videoShutdownSeen=new Map();const ui=uiProjection(),csrf=randomBytes(24).toString('hex');let requests=0,active=0,closed=false,guard,lastUI=null;const assets={'/ui.css':['pilot/workbench01/ui.css','text/css'],'/workflow.mjs':['pilot/workbench01/workflow.mjs','text/javascript'],'/font-medium.ttf':['native/crew02/assets/fonts/Barlow-Medium.ttf','font/ttf'],'/font-semibold.ttf':['native/crew02/assets/fonts/Barlow-SemiBold.ttf','font/ttf'],'/font-bold.ttf':['native/crew02/assets/fonts/Barlow-Bold.ttf','font/ttf']};
 const own={'/beta-client.mjs':'beta-client.mjs','/client-fence.mjs':'client-fence.mjs','/beta.css':'beta.css','/download-package.mjs':'download-package.mjs','/media-panel.mjs':'media-panel.mjs','/video-worker.mjs':'video-worker.mjs'};const wb={'/native-bridge.mjs':'native-bridge.mjs','/mock-native.mjs':'mock-native.mjs','/mock-provider.mjs':'mock-provider.mjs'};
 const fontPins=JSON.parse(fs.readFileSync(path.join(ROOT,'evidence/workbench01/handoff-manifest.json'))).fontPins;
 const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':`default-src 'self';script-src 'self' ${MEDIA};style-src 'self';font-src 'self';img-src 'self' blob: data:;connect-src 'self' ${MEDIA};frame-src 'none';worker-src 'self';object-src 'none';base-uri 'none';frame-ancestors 'none'`};
 const server=http.createServer(async(req,res)=>{const send=(code,v,type='application/json')=>{res.writeHead(code,{...headers,'Content-Type':type});res.end(Buffer.isBuffer(v)?v:type==='application/json'?JSON.stringify(v):v);};try{
  if(closed)throw Error('HOST_CLOSED');if(++requests>20000)throw Error('REQUEST_BUDGET');if(req.headers.host!=='127.0.0.1:8896')return send(403,{error:'HOST_REFUSED'});
  if(req.method==='GET'){
   if(req.url==='/api/ui-observation')return send(200,{ok:true,observation:lastUI,ageMs:lastUI?performance.now()-lastUI.receivedMs:null});
   if(req.url==='/api/bootstrap')return send(200,{ok:true,csrf,origin:ORIGIN,mediaOrigin:MEDIA,simulationOnly:true,allowSITL:allowSitl,source:'BETA05_HOST_COMPANION_SIMULATION'});
   if(req.url==='/api/history')return send(200,{ok:true,result:await archive.list()});
   if(req.url.startsWith('/api/beta-package?run=')){const run=req.url.slice('/api/beta-package?run='.length);return send(200,(await archive.read(run)).bytes,'application/json');}
   if(req.url.startsWith('/api/video-quality?run=')){const run=req.url.slice('/api/video-quality?run='.length);return send(200,{ok:true,...await archive.quality(run)});}
   if(req.url==='/api/video-quality'){const state=await session.state(),r=state.reviews.at(-1),p=r?path.join(out,'auto-video-qualification-'+r.run+'.json'):null;return send(200,{ok:true,result:p&&fs.existsSync(p)?JSON.parse(fs.readFileSync(p)):null});}
   if(req.url==='/api/state'){const result=await session.state(),old=history.catalog(),current=new Set(result.reviews.map(r=>r.run));result.reviews=[...old.reviews.filter(r=>!current.has(r.run)),...result.reviews];result.archiveIssues=old.issues;result.archivePending=archiveBusy;result.archiveCommittedRuns=old.reviews.map(r=>r.run);return send(200,{ok:true,result});}
   if(req.url==='/api/defaults'){const f=sitlFixture();return send(200,{options:f.options,camera:f.camera,home:f.home,energy:ENERGY,samples:FIXTURE92.samples,operational:false});}
   if(req.url==='/api/health')return send(200,{source:'BETA05_HOST_COMPANION_SIMULATION',projection:{...ui,source:undefined},freeBytes:diskFloor(),actualImages:0});
   if(req.url==='/'||req.url==='/mock')return send(200,htmlProjection(req.url==='/mock'),'text/html; charset=utf-8');
   if(req.url==='/ui.mjs')return send(200,ui.source,'text/javascript');
   if(own[req.url])return send(200,fs.readFileSync(new URL(own[req.url],import.meta.url)),req.url.endsWith('.css')?'text/css':'text/javascript');
   if(wb[req.url]){let bytes=fs.readFileSync(path.join(ROOT,'pilot/workbench02',wb[req.url]));if(req.url==='/mock-native.mjs')bytes=Buffer.from(bytes.toString().replace('aeris-workbench02-MOCK-native-store','aeris-betastability02-MOCK-native-store'));if(req.url==='/native-bridge.mjs')bytes=Buffer.from(bytes.toString().replace("['export','pick-json','pick-kml'].includes(p.request.action)","['export','export-diagnostics','pick-json','pick-kml'].includes(p.request.action)").replace("'pick-kml'].includes(action)","'pick-kml','export-diagnostics'].includes(action)"));return send(200,bytes,'text/javascript');}
   
   if(req.url==='/media-panel.css')return send(200,fs.readFileSync(path.join(ROOT,'pilot/clockvideo05/media-panel.css')),'text/css');
   if(req.url.startsWith('/capture/')){const id=req.url.slice(9);if(!/^capture-[a-f0-9-]{36}$/.test(id))throw Error('CAPTURE_ID');const c=await session.store.read(id);return send(200,c.originalBytes,'image/jpeg');}
   const a=assets[req.url];if(!a)return send(404,{error:'NOT_FOUND'});const b=a[0].startsWith('pilot/workbench01')?pinned(a[0]):fs.readFileSync(path.join(ROOT,a[0]));if(fontPins[a[0]]&&sha(b)!==fontPins[a[0]])throw Error('FONT_DRIFT');return send(200,b,a[1]);
  }
  if(req.method!=='POST'||req.headers.origin!==ORIGIN||!/^application\/json(?:;|$)/.test(req.headers['content-type']??''))return send(403,{error:'ORIGIN_TYPE_OR_METHOD'});
  diskFloor();if(active>=2)return send(429,{error:'HOST_BUSY_NO_QUEUE'});active++;const alarm=setTimeout(()=>req.destroy(),5000);try{
   let bytes=0,chunks=[];for await(const b of req){bytes+=b.length;if(bytes>3145728)throw Error('REQUEST_BOUND');chunks.push(b);}const d=JSON.parse(Buffer.concat(chunks));let result;if(archiveBusy&&((req.url==='/api/beta/bind')||(req.url==='/api/beta/flight'&&d.action!=='revoke')||(req.url.startsWith('/api/beta/payload/')&&req.url!=='/api/beta/payload/revoke')||req.url==='/api/media-sidecar'||req.url==='/api/qualify-video'))throw Error('ARCHIVE_BUSY_WORKSPACE_MUTATION_NO_QUEUE');
   if(req.url==='/api/ui-observation'){if(req.headers['x-field-csrf']!==csrf||bytes>65536||d.platform!=='ANDROID')throw Error('QA_OBSERVATION_SCOPE');if(d.videoShutdown!==undefined){if(!Array.isArray(d.videoShutdown)||d.videoShutdown.length>8||typeof d.videoShutdownOverflow!=='boolean')throw Error('VIDEO_SHUTDOWN_QA_BOUND');for(const r of d.videoShutdown){if(!r||typeof r.workerId!=='string'||!/^[a-f0-9-]{36}$/.test(r.workerId)||!['REQUESTED','COMPLETE','NOT_STARTED','FAILED'].includes(r.status)||!Number.isFinite(r.requestedAtEpochMs)||Buffer.byteLength(JSON.stringify(r))>5120)throw Error('VIDEO_SHUTDOWN_QA_SCHEMA');if(r.status==='REQUESTED')continue;if(!Number.isFinite(r.settledAtEpochMs)||r.settledAtEpochMs<r.requestedAtEpochMs||r.status==='FAILED'&&(typeof r.error!=='string'||r.error.length>240)||['COMPLETE','NOT_STARTED'].includes(r.status)&&(r.receipt?.status!==r.status||r.receipt?.workerId!==r.workerId))throw Error('VIDEO_SHUTDOWN_QA_RECEIPT');const key=d.instance+':'+r.workerId,digest=sha(JSON.stringify(r)),prior=videoShutdownSeen.get(key);if(prior&&prior!==digest)throw Error('VIDEO_SHUTDOWN_QA_CHANGED');if(!prior){if(videoShutdownSeen.size>=128)throw Error('VIDEO_SHUTDOWN_HOST_BOUND');media.fullTrace?.append('VIDEO_UI_SHUTDOWN',{instance:d.instance,record:r,scope:'UI_REPORTED_WORKER_CLOSURE_RECEIPT_REQUIRES_RAW_PREFIX_VERIFICATION'});videoShutdownSeen.set(key,digest);}}if(d.videoShutdownOverflow===true&&!videoShutdownSeen.has('overflow:'+d.instance)){media.fullTrace?.append('VIDEO_UI_SHUTDOWN_OVERFLOW',{instance:d.instance,overflow:true});videoShutdownSeen.set('overflow:'+d.instance,'true');}}lastUI={...d,receivedMs:performance.now()};return send(200,{ok:true});}
   if(req.url==='/api/qualify-video'){if(req.headers['x-field-csrf']!==csrf)throw Error('CSRF');const state=await session.state();if(state.flight.run)throw Error('CLOSED_REVIEW_REQUIRED');const r=state.reviews.filter(r=>r.accepted&&r.source==='OBSERVED_OWNED_SITL').at(-1);if(!r)throw Error('ACTUAL_ACCEPTED_REVIEW_REQUIRED');const checked=await archive.qualify({root:out,review:r});if(!checked.quality)throw Error(checked.error??'VIDEO_QUALIFICATION_NOT_CHECKED');const result=checked.quality;return send(200,{ok:true,result});}
   if(req.url==='/api/media-sidecar'){if(req.headers['x-field-csrf']!==csrf)throw Error('CSRF');return send(200,{ok:true,result:await session.saveReport(d,out)});}
   if(req.url.startsWith('/api/beta/')){
    if(req.headers['x-field-csrf']!==csrf)throw Error('CSRF');const route=req.url.slice('/api/beta/'.length);
    if(route==='lifecycle')result=await session.lifecycle(d);
    else if(route==='bind')result=await session.bind(d.input,d.confirmSyntheticHomeAmsl10);
    else if(route==='flight'){const traceStart=d.action==='connect'?(media.fullTrace?.snapshot().accepted??0)+1:null;result=await session.command(d.action,d);if(traceStart!==null){const f=await session.state();if(f.flight.run)traceStarts.set(f.flight.run,traceStart);}if(result?.rawHead)await archiveReview(result);}
    else if(route.startsWith('payload/'))result=await session.payloadAction(route.slice(8),d);
    else throw Error('BETA_ROUTE');return send(200,{ok:true,result});
   }
   if(req.url==='/api/parse')result={document:await parseKml(d.kml)};
   else if(req.url==='/api/native/sitl-fixture')result={input:sitlFixture(d.kind??'polygon')};
   else if(req.url==='/api/native/validate'||req.url==='/api/receive'){const b=req.url.endsWith('validate')?JSON.parse(d.body):d.bundle;if(req.url.endsWith('validate')&&(typeof d.body!=='string'||Buffer.byteLength(d.body)>2097152))throw Error('BODY_BOUND');const checked=receive(b,await parseKml(b.input?.kml));result=req.url.endsWith('validate')?{bodySha256:sha(d.body),workspaceSha256:b.sha256,authorityRestorable:false}:checked;}
   else{if(!['/api/compile','/api/replay','/api/analyze','/api/export','/api/native/sitl-prepare'].includes(req.url))return send(404,{error:'NO_REAL_FLIGHT_ROUTE'});const p=createPlan(await parseKml(d.input?.kml),d.input),ready=preflight(p);
    if(req.url==='/api/compile')result={plan:p,ready,analysis:analyze(p,[],5)};
    if(req.url==='/api/native/sitl-prepare')result={preparation:await prepareSITL(p,{confirmSyntheticHomeAmsl10:d.confirmSyntheticHomeAmsl10})};
    if(req.url==='/api/replay')throw Error('USE_BETA_PROTOCOL_FLY_NOT_POSITION_REPLAY');
    if(req.url==='/api/analyze'){const analysis=analyze(p,d.records,d.stepM??5);result={analysis,proposal:reflyProposal(p,analysis)};}
    if(req.url==='/api/export')result={bundle:makeBundle(p,d.records,d.stepM??5)};
   }return send(200,{ok:true,...result});
  }finally{clearTimeout(alarm);active--;}
 }catch(e){if(!res.headersSent)send(400,{ok:false,error:String(e.message).slice(0,240),automaticRetry:false});else res.destroy();}});
 server.requestTimeout=10000;server.headersTimeout=5000;
 async function close(){if(closed)return;closed=true;clearInterval(guard);server.close();server.closeAllConnections();let error;
  try{await session.close();if(archiveTask)await archiveTask;await archive.idle();const state=await session.state();for(const r of state.reviews){const own=path.join(out,r.source==='OBSERVED_OWNED_SITL'?'flight/runs':'session',r.run,'raw.jsonl');if(fs.existsSync(own)){try{await archive.read(r.run);}catch(e){if(archiveAttempted.has(r.run)||fs.existsSync(path.join(history.root,r.run+'.json'))||fs.existsSync(path.join(history.root,r.run+'.receipt.json')))throw e;await archiveReview(r);}}}}catch(e){error=e;}
  setJournalSpanSink(null);try{await archive.close();}catch(e){error??=e;}try{await publisher?.close();}catch(e){error??=e;}try{await media.close();}catch(e){error??=e;}if(error)throw error;
 }

 async function listen(){try{await media.listen();publisher=startNativePublisher({out:path.join(out,'producer'),baseUrl:MEDIA});await new Promise((yes,no)=>{server.once('error',no);server.listen(8896,'127.0.0.1',yes);});guard=setInterval(()=>{try{diskFloor();if(publisher?.snapshot().failed)throw Error('PUBLISHER_FAILED:'+publisher.snapshot().failed);}catch{close().catch(e=>console.error(e.message));}},250);return{origin:ORIGIN,mediaOrigin:MEDIA,source:'HOST_COMPANION_SIMULATION_MOCK_OR_OWNED_SITL',pid:process.pid};}catch(e){await close();throw e;}}
 return{listen,close,server,session,media,ui};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const host=await createHost({out:process.argv[2],allowSitl:process.argv.includes('--sitl'),workspaceRoot:process.argv.includes('--workspace')?process.argv[process.argv.indexOf('--workspace')+1]:undefined});console.log(JSON.stringify(await host.listen()));for(const signal of['SIGINT','SIGTERM'])process.once(signal,()=>host.close().catch(e=>{console.error(e.message);process.exitCode=1;}));}
