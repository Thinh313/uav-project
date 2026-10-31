import http from 'node:http';import fs from 'node:fs';import path from 'node:path';
import {fileURLToPath} from 'node:url';import {randomBytes} from 'node:crypto';
import {trainingAPI} from '../coach02/api.mjs';
import {ReportStore,diskGuard} from './store.mjs';import {POLICY} from './core.mjs';
const ROOT=fileURLToPath(new URL('../../',import.meta.url)),HERE=path.dirname(fileURLToPath(import.meta.url));
export async function start({port=8897,storeRoot=path.join(ROOT,'evidence/coach01/workspace02'),trainingRoot}={}){
 diskGuard(true);const store=new ReportStore(storeRoot),origin='http://127.0.0.1:'+port,csrf=randomBytes(24).toString('hex');let active=false,requests=0;
 const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self';script-src 'self';style-src 'self';img-src 'self' blob:;font-src 'self';connect-src 'self';object-src 'none';base-uri 'none';frame-ancestors 'none'"};
 const training=trainingAPI(trainingRoot?{root:trainingRoot}:{});
 const assets={'/':['index.html','text/html'],'/app.mjs':['app.mjs','text/javascript'],'/replay.mjs':['replay.mjs','text/javascript'],'/style.css':['style.css','text/css'],'/medium.ttf':['../../native/crew02/assets/fonts/Barlow-Medium.ttf','font/ttf'],'/semibold.ttf':['../../native/crew02/assets/fonts/Barlow-SemiBold.ttf','font/ttf'],'/bold.ttf':['../../native/crew02/assets/fonts/Barlow-Bold.ttf','font/ttf']};
 const server=http.createServer(async(req,res)=>{
  const send=(code,body,type='application/json',extra={})=>{res.writeHead(code,{...headers,'Content-Type':type,...extra});res.end(type==='application/json'?JSON.stringify(body):body);};
  try{
   if(++requests>10000)throw Error('REQUEST_BUDGET');if(req.headers.host!=='127.0.0.1:'+port)return send(403,{error:'HOST_REFUSED'});
   if(req.url.startsWith('/manual/')||req.url.startsWith('/api/training/'))return await training.handle(req,send,{origin,csrf});
   if(req.method==='GET'){
    if(assets[req.url]){const [f,type]=assets[req.url];return send(200,fs.readFileSync(path.resolve(HERE,f)),type);}
    if(req.url==='/api/state')return send(200,{...store.list(),csrf,policy:POLICY,scope:'OFFLINE_REPLAY_NO_FLIGHT_CONNECTION',model:'DETERMINISTIC_BASELINE',controlAuthority:false});
    const m=req.url.match(/^\/api\/report\/([a-f0-9]{64})(?:\/(export|image)?)?(?:\?file=([^&]+))?$/);
    if(m){if(active)return send(409,{error:'ANALYSIS_BUSY'});active=true;try{const r=await store.get(m[1]);if(m[2]==='image')return send(200,store.image(r,decodeURIComponent(m[3]??'')),'image/jpeg');if(m[2]==='export')return send(200,Buffer.from(JSON.stringify(r,null,2)),'application/json; charset=utf-8',{'Content-Disposition':'attachment; filename="AERIS-debrief-'+r.run+'.json"'});return send(200,r);}finally{active=false;}}
    return send(404,{error:'NOT_FOUND'});
   }
   if(req.method!=='POST')return send(405,{error:'METHOD_REFUSED'});
   if(req.headers.origin!==origin||req.headers['x-coach-csrf']!==csrf)return send(403,{error:'ORIGIN_OR_CSRF'});
   if(!['/api/import','/api/demo'].includes(req.url))return send(404,{error:'NO_CONTROL_ROUTE'});
   if(Number(req.headers['content-length']??0)>POLICY.maxSourceBytes)return send(413,{error:'SOURCE32MIB'});
   if(active)return send(409,{error:'ANALYSIS_BUSY'});active=true;
   try{
    const chunks=[];let size=0;const alarm=setTimeout(()=>req.destroy(Error('BODY_TIMEOUT')),10000);
    try{for await(const c of req){size+=c.length;if(size>POLICY.maxSourceBytes)throw Error('SOURCE32MIB');chunks.push(c);}}finally{clearTimeout(alarm);}
    const bytes=req.url==='/api/demo'?fs.readFileSync(path.join(ROOT,'evidence/betaworkbench05/android-saf-package01.json')):Buffer.concat(chunks);
    const start=performance.now(),report=await store.ingest(bytes);return send(200,{report,analysisMs:performance.now()-start});
   }finally{active=false;}
  }catch(e){if(!res.headersSent)send(400,{error:String(e.message).slice(0,160),automaticRetry:false});else res.destroy();}
 });
 server.requestTimeout=15000;server.headersTimeout=5000;
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
 const close=()=>new Promise(resolve=>{clearTimeout(timer);training.close();server.close(resolve);server.closeAllConnections();});
 const timer=setTimeout(()=>close(),30*60*1000);timer.unref();
 console.log(JSON.stringify({origin,pid:process.pid,mode:'OFFLINE_REPLAY_NO_FLIGHT',storeRoot,limitMinutes:30}));return{server,store,close,origin};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const h=await start();for(const sig of ['SIGINT','SIGTERM'])process.once(sig,()=>h.close());}
