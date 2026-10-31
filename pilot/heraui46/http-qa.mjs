import assert from 'node:assert/strict';
import {writeFile,statfs} from 'node:fs/promises';
import {preview46} from './server.mjs';
const server=preview46(),results=[];let url;
const check=(name,pass)=>{assert.ok(pass,name);results.push({name,pass:true});};
try{
 const f=await statfs('.',{bigint:true});assert.ok(f.bavail*f.bsize>20n*1024n**3n+16777216n);await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port;
 const post=(path,data,extra={})=>fetch(url+path,{method:'POST',headers:{Origin:url,'Content-Type':'application/json',...extra},body:JSON.stringify(data)});
 let r=await post('/api/create',{}, {Origin:'https://foreign.invalid'});check('foreignOriginPOST403',r.status===403);
 r=await fetch(url+'/api/create',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});check('missingOriginPOST403',r.status===403);
 r=await post('/api/create',{}, {'Content-Type':'text/plain'});check('wrongcontenttype403',r.status===403);
 r=await fetch(url+'/../contract.json');check('pathtraversal refused',r.status===404);
 r=await fetch(url+'/api/view');check('view token required',r.status===403);
 r=await fetch(url+'/api/create');check('GET cannot createworkspace',r.status===404);
 r=await post('/api/create',{});const first=await r.json();check('createsmock workspace',r.status===200&&first.view.summary.state==='DISCONNECTED');const headers={'X-Workspace':first.token};
 r=await post('/api/action',{kind:'connect',data:{},revision:0},headers);check('connect explicit revision0 advances1',(await r.json()).view.revision===1);
 r=await post('/api/action',{kind:'connect',data:{},revision:0},headers);const stale=await r.json();check('duplicate revision refuses and no duplicate modelaction',r.status===409&&stale.view.revision===1&&stale.view.record.events.length===1);
 r=await post('/api/action',{kind:'identity',data:{},revision:1}, {'X-Workspace':'foreign'});check('foreignworkspace denied',r.status===403);
 r=await post('/api/action',{kind:'identity',data:{},revision:1,operational:true},headers);check('extraAPI fields refused',r.status===409);
 r=await post('/api/action',{kind:'identity',data:{},revision:1},headers);check('rejectedforeign/extra requests neveradvanced originalrevision',(await r.json()).view.summary.state==='DISCOVERED');
 r=await post('/api/action',{kind:'USB_SEND',data:{},revision:2},headers);check('physicalroute action unknown refused',r.status===409&&(await r.json()).error==='UI_ACTION_NOT_ALLOWED');
 r=await post('/api/action',{kind:'import',data:{record:'x'.repeat(300001)},revision:3},headers);check('bodybound300000 rejects',r.status===409&&(await r.json()).error==='REQUEST_BOUND');
 r=await post('/api/create',{});const second=await r.json();check('second workspace isolated',second.token!==first.token&&second.view.summary.state==='DISCONNECTED');
 r=await post('/api/create',{});check('third workspace bounded refuses',r.status===409);
 r=await fetch(url+'/shell.mjs');check('CSP no framing no externalresource',(r.headers.get('content-security-policy')??'').includes("frame-ancestors 'none'")&&r.headers.get('cache-control')==='no-store');
 await writeFile('evidence/heraui46/http2.json',JSON.stringify({status:'PASS',checks:results.length,results,scope:'Loopbackmock endpoints only, not penetration/security certification'},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',checks:results.length}));
}catch(e){await writeFile('evidence/heraui46/http-failure2.json',JSON.stringify({status:'FAIL',error:e.stack,passed:results},null,2)+'\n',{flag:'wx'});throw e;}finally{if(server.listening)await new Promise(r=>server.close(r));}
