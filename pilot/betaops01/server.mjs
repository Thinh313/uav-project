import http from'node:http';import fs from'node:fs';import{randomBytes}from'node:crypto';import{fileURLToPath}from'node:url';import{Inbox,budget,regular}from'./store.mjs';import{verifier}from'./runner.mjs';import{launchCatalog}from'./catalog.mjs';
const HERE=new URL('./',import.meta.url),FIXTURE=new URL('../../evidence/betaworkbench05/android-saf-package01.json',import.meta.url);
export async function start({port=8900,root,launchRoot,limitMs=30*60000}={}){
 const inbox=new Inbox(root),verify=verifier(),origin='http://127.0.0.1:'+port,csrf=randomBytes(24).toString('hex');let requests=0,mutation=false,closed=false;
 const assets={'/':['index.html','text/html; charset=utf-8'],'/app.mjs':['app.mjs','text/javascript'],'/style.css':['style.css','text/css'],'/medium.ttf':['../../native/crew02/assets/fonts/Barlow-Medium.ttf','font/ttf'],'/semibold.ttf':['../../native/crew02/assets/fonts/Barlow-SemiBold.ttf','font/ttf']};
 const server=http.createServer(async(req,res)=>{const send=(status,data,type='application/json',extra={})=>{if(res.destroyed)return;res.writeHead(status,{'Content-Type':type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self';script-src 'self';style-src 'self';font-src 'self';connect-src 'self';object-src 'none';base-uri 'none';frame-ancestors 'none'",...extra});res.end(type==='application/json'?JSON.stringify(data):data);};try{
  if(++requests>2000)throw Error('REQUEST_BUDGET');if(req.headers.host!=='127.0.0.1:'+port)return send(403,{error:'HOST_REFUSED'});
  if(req.method==='GET'){
   if(assets[req.url]){const[f,t]=assets[req.url];return send(200,fs.readFileSync(new URL(f,HERE)),t);}
   if(req.url==='/api/state'){const s=fs.statfsSync(new URL('../../',import.meta.url));return send(200,{csrf,scope:'BETA_OPERATIONS_READ_REPLAY_ONLY',busy:mutation||verify.busy,freeBytes:s.bavail*s.bsize,admissionGiB:20,writeFloorGiB:10,authorityRestorable:false,browserVisual:'NOT_CHECKED'});}
   if(req.url==='/api/catalog'){if(mutation)return send(409,{error:'VERIFY_BUSY_NO_QUEUE'});return send(200,{inbox:inbox.list(),launches:launchCatalog(launchRoot)});}
   return send(404,{error:'NOT_FOUND'});
  }
  if(req.method!=='POST')return send(405,{error:'METHOD_REFUSED'});
  if(req.headers.origin!==origin||req.headers['x-beta-csrf']!==csrf)return send(403,{error:'ORIGIN_CSRF_REFUSED'});
  const m=req.url.match(/^\/api\/(verify|export)\/([a-f0-9]{64})$/);if(!m&&!['/api/import','/api/example'].includes(req.url))return send(404,{error:'NO_CONTROL_ROUTE'});
  if(mutation)return send(409,{error:'VERIFY_BUSY_NO_QUEUE'});mutation=true;
  try{const max=req.url==='/api/import'?32*2**20:64;if(Number(req.headers['content-length']??0)>max)return send(413,{error:'BODY_BOUND'});const parts=[];let count=0;const timer=setTimeout(()=>req.destroy(Error('BODY_TIMEOUT')),8000);try{for await(const b of req){count+=b.length;if(count>max)throw Error('BODY_BOUND');parts.push(b);}}finally{clearTimeout(timer);}
   if(m){const r=await inbox.verified(m[2],b=>verify.run(b));if(m[1]==='export')return send(200,r.bytes,'application/octet-stream',{'Content-Disposition':'attachment; filename="AERIS-'+m[2]+'.json"'});return send(200,{summary:r.summary,id:m[2],authorityRestorable:false});}
   const bytes=req.url==='/api/example'?regular(fileURLToPath(FIXTURE),32*2**20):Buffer.concat(parts);const r=await inbox.ingest(bytes,b=>verify.run(b));return send(200,{...r,authorityRestorable:false});
  }finally{mutation=false;}
 }catch(e){send(400,{error:String(e.message).slice(0,200),automaticRetry:false,authorityRestorable:false});}});
 server.requestTimeout=12000;server.headersTimeout=5000;await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});let timer=setTimeout(()=>close(),limitMs);timer.unref();
 async function close(){if(closed)return;closed=true;clearTimeout(timer);verify.close();await new Promise(r=>{server.close(r);server.closeAllConnections();});}
 console.log(JSON.stringify({origin,pid:process.pid,scope:'READ_REPLAY_NO_FLIGHT',limitMs}));return{server,close,origin,inbox};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const host=await start();for(const s of['SIGINT','SIGTERM'])process.once(s,()=>host.close());}
