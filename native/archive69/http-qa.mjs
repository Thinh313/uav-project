import {request} from 'node:http';import {mkdir} from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {service} from './server.mjs';import {unpack,pinned68} from './package.mjs';import {bytes,write} from './io.mjs';
const run=process.env.A69_HTTP_RUN??'r01';if(!/^[a-z0-9-]{1,20}$/.test(run))throw Error('RUN_NAME');const root=path.resolve('evidence/archive69/http-'+run);await mkdir(root);const dir=path.join(root,'workspace'),url='http://127.0.0.1:8824',rows=[];let s=await service({dir,initialize:true}),token;
async function listen(){await new Promise(r=>s.server.listen(8824,'127.0.0.1',r));}await listen();
async function state(){const d=await (await fetch(url+'/api/state')).json();token=d.token;return d.state;}
async function post(route,input={},extra={}){const r=await fetch(url+'/api/'+route,{method:'POST',headers:{Origin:url,'Content-Type':'application/json',Authorization:'Bearer '+token,...extra},body:JSON.stringify(input)});return {status:r.status,body:await r.json()};}
const pass=(name)=>rows.push({name,pass:true});
try{
 let v=await state();assert.equal(v.generations.length,0);assert.equal(v.authorityRestored,false);pass('cold workspace no data or authority');
 assert.equal((await post('seed',{}, {Origin:'http://evil.test'})).status,409);pass('wrong origin refused');
 assert.equal((await post('seed',{}, {Authorization:'Bearer stale'})).status,409);pass('wrong local session refused');
 assert.equal((await post('seed',{source:'.local/journal68'})).status,409);pass('arbitrary original source path not accepted');
 const seed=await post('seed');assert.equal(seed.status,200);const g=seed.body.result.generation;assert.equal(seed.body.state.generations[0].inspection.runs.length,3);pass('pinned snapshot adopted as small managed replica');
 assert.equal((await post('confirm',{planSha256:'0'.repeat(64),confirmation:'yes'})).status,409);pass('no cleanup without verified package and fresh plan');
 const exp=await post('export',{generation:g});assert.equal(exp.status,200);const e=exp.body.result.exportId;
 const response=await fetch(url+'/api/download/'+e),raw=Buffer.from(await response.arrayBuffer()),checked=await unpack(raw,await pinned68());assert.equal(checked.packageSha256,exp.body.result.packageSha256);await write(path.join(root,'download.aeris69'),raw);pass('HTTP download independently decodes SHA and semantics');
 assert.equal((await fetch(url+'/api/download/e-'+('0'.repeat(32)))).status,409);pass('unknown download refused');
 await new Promise((resolve,reject)=>{const req=request(url+'/api/import',{method:'POST',headers:{Origin:url,'Content-Type':'application/json',Authorization:'Bearer '+token}},res=>{res.destroy();resolve();});req.on('error',e=>e.code==='ECONNRESET'?resolve():reject(e));req.end(JSON.stringify({exportId:e}));});v=await state();assert.equal(v.imports.length,1);assert.equal(v.imports[0].currentIntegrity,'PASS');const i=v.imports[0].importId;pass('discarded import response still committed, no automatic retry');
 let p=(await post('plan',{generation:g,exportId:e,importId:i})).body.result;assert(p.plan.reclaimHotBytes>0);assert.equal((await post('confirm',{planSha256:p.planSha256,confirmation:'yes'})).status,409);assert((await state()).generations[0].remainingBytes>0);pass('wrong typed confirmation leaves all files');
 p=(await post('plan',{generation:g,exportId:e,importId:i})).body.result;const oldToken=token,oldBoot=(await state()).boot;await s.stop();s=await service({dir});await listen();v=await state();assert.notEqual(v.boot,oldBoot);assert.equal(v.imports[0].currentIntegrity,'PASS');assert.equal(v.authorityRestored,false);pass('actual service restart replays committed history, no authority');
 assert.equal((await post('confirm',{planSha256:p.planSha256,confirmation:p.phrase},{Authorization:'Bearer '+oldToken})).status,409);pass('old server session refused after restart');
 assert.equal((await post('confirm',{planSha256:p.planSha256,confirmation:p.phrase})).status,409);pass('old plan does not survive restart');
 p=(await post('plan',{generation:g,exportId:e,importId:i})).body.result;const cleanup=await post('confirm',{planSha256:p.planSha256,confirmation:p.phrase});assert.equal(cleanup.status,200);assert.equal(cleanup.body.state.generations[0].remainingBytes,0);assert.equal(cleanup.body.state.imports[0].currentIntegrity,'PASS');pass('explicit fixture confirmation removes only hot bytes');
 assert.equal((await post('confirm',{planSha256:p.planSha256,confirmation:p.phrase})).status,409);pass('confirmation single use');
 assert.equal((await fetch(url+'/api/download/'+e)).status,200);pass('package remains downloadable after hot cleanup');
 await s.stop();s=await service({dir});await listen();v=await state();assert.equal(v.generations[0].status,'CLEANED_HOT_REPLICA_ONLY');assert.equal(v.imports[0].currentIntegrity,'PASS');assert.equal(v.pending.length,0);pass('restart preserves explicit cleanup receipt and receiver');
 await write(path.join(root,'results.json'),bytes({status:'PASS_HTTP_ARCHIVE_QUOTA',rows,finalState:v,scope:'Local mock HTTP fixture cleanup only; original JOURNAL68 and demo never deleted'}));console.log(JSON.stringify({passed:rows.length,total:rows.length}));
}finally{await s.stop();}
