import {createServer} from 'node:http';
import {randomBytes} from 'node:crypto';
import {readFile,statfs} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {capture,stage,catalog,verifyGeneration} from './store.mjs';
import {inspect,plan,LIMITS} from './recovery.mjs';
const R=path.resolve(fileURLToPath(new URL('../..',import.meta.url))),H=path.join(R,'pilot/herarecover48');
export function preview(store=path.join(R,'.local/herarecover48/operator')){const token=randomBytes(32).toString('hex');let busy=false;const assets={'/':'index.html','/shell.mjs':'shell.mjs','/shell.css':'shell.css','/font.ttf':'../../native/preflight44/assets/IBMPlexSans.ttf'};const server=createServer(async(req,res)=>{const origin='http://'+req.headers.host,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self';object-src 'none';frame-src 'none';base-uri 'none';form-action 'none'"};const send=(code,data)=>res.writeHead(code,{...headers,'Content-Type':'application/json'}).end(JSON.stringify(data));let held=false;try{
 if(!/^127\.0\.0\.1:\d+$/.test(req.headers.host??'')||req.headers.origin&&req.headers.origin!==origin)return send(403,{ok:false,error:'ORIGIN_REFUSED'});
 if(req.method==='GET'&&assets[req.url]){const name=assets[req.url],raw=await readFile(path.join(H,name));res.writeHead(200,{...headers,'Content-Type':name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':name.endsWith('.ttf')?'font/ttf':'text/javascript'}).end(raw);return;}
 if(req.method==='GET'&&req.url==='/api/bootstrap')return send(200,{ok:true,token,limits:LIMITS});
 if(req.headers['x-workspace-token']!==token)return send(403,{ok:false,error:'TOKEN_REFUSED'});
 if(busy)return send(409,{ok:false,error:'BUSY_NO_RETRY'});busy=held=true;
 if(req.method==='GET'&&req.url==='/api/catalog')return send(200,{ok:true,...await catalog(store)});
 const fixture=/^\/api\/fixture\/(RECORD_PUBLISHED|HEAD_PENDING|HEAD_COMMITTED)$/.exec(req.url);if(req.method==='GET'&&fixture)return send(200,{ok:true,bundle:await capture(path.join(R,'evidence/herapersist47/fault-'+fixture[1]))});
 const gen=/^\/api\/generation\/(g-[a-f0-9-]{36})$/.exec(req.url);if(req.method==='GET'&&gen)return send(200,{ok:true,...await verifyGeneration(store,gen[1])});
 if(req.method!=='POST'||!['/api/inspect','/api/plan','/api/stage'].includes(req.url))return send(404,{ok:false,error:'ROUTE_REFUSED_NO_DELETE_OR_FLIGHT_API'});
 if(req.headers.origin!==origin||req.headers['content-type']!=='application/json')return send(403,{ok:false,error:'POST_ORIGIN_TYPE'});
 let chunks=[],length=0;for await(const b of req){if((length+=b.length)>LIMITS.bundleBytes+65536)throw Error('REQUEST_BOUND');chunks.push(b);}const body=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));const keys=Object.keys(body).sort().join(',');
 if(req.url==='/api/inspect'){if(keys!=='bundle,expectedSha')throw Error('REQUEST_SCHEMA');return send(200,{ok:true,inspection:inspect(body.bundle,body.expectedSha)});}
 if(req.url==='/api/plan'){if(keys!=='bundle,expectedSha,selectedToken')throw Error('REQUEST_SCHEMA');return send(200,{ok:true,plan:plan(body.bundle,body.selectedToken,body.expectedSha)});}
 if(keys!=='acknowledge,bundle,plan,planSha256')throw Error('REQUEST_SCHEMA');const fs=await statfs(R,{bigint:true});if(fs.bavail*fs.bsize<BigInt(LIMITS.floorBytes+LIMITS.reserveBytes))throw Error('HOST_20GIB_FLOOR_AND_RESERVE');return send(200,{ok:true,...await stage(store,body.bundle,body.plan,{planSha256:body.planSha256,acknowledge:body.acknowledge})});
 }catch(e){send(409,{ok:false,error:e.message});}finally{if(held)busy=false;}});server.requestTimeout=15000;server.headersTimeout=10000;server.keepAliveTimeout=1000;server.maxConnections=8;return server;}
if(process.argv[1]===fileURLToPath(import.meta.url)){const store=process.env.HERA48_STORE?path.resolve(process.env.HERA48_STORE):path.join(R,'.local/herarecover48/operator');const s=preview(store);s.listen(Number(process.env.HERA48_PORT??8802),'127.0.0.1',()=>console.log('HERARECOVER48 port '+s.address().port+' pid '+process.pid));for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>s.close(()=>process.exit(0)));}
