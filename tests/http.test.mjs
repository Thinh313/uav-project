import test from 'node:test';import assert from 'node:assert/strict';import {once} from 'node:events';
import http from 'node:http';
import {createAppServer} from '../tools/server.mjs';
test('HTTP localhost API: CSRF/session/allowlist/disabled runtime defenses',async()=>{
 const link={sessionId:null,snapshot(){return {sessionId:this.sessionId};},disconnect(){},journal(){return {simulation:true};},connect(){this.sessionId='new';return this.snapshot();},recover(request){return {readOnly:true,request};},reviewResume(request){return {reviewed:true,request};}};
 const s=createAppServer({enableSitl:true,link});s.listen(0,'127.0.0.1');await once(s,'listening');const url=`http://127.0.0.1:${s.address().port}`;
 try{const state=await(await fetch(url+'/api/sitl/status')).json();const headers={'Content-Type':'application/json','X-Aeris-Token':state.apiToken,Origin:url};
  assert.equal((await fetch(url+'/api/sitl/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status,403);
  assert.equal((await fetch(url+'/api/sitl/connect',{method:'POST',headers:{...headers,Origin:'http://attacker.test'},body:'{}'})).status,403);
  assert.equal((await fetch(url+'/api/sitl/connect',{method:'POST',headers,body:'{"sessionId":"old"}'})).status,409);
  assert.equal((await fetch(url+'/api/sitl/connect',{method:'POST',headers,body:'{"sessionId":null}'})).status,200);
  assert.equal((await fetch(url+'/api/sitl/command',{method:'POST',headers,body:'{"sessionId":null}'})).status,409);
  assert.equal((await fetch(url+'/sot/source_canonical/0.BOM26.xlsx')).status,404);
  assert.equal((await fetch(url+'/runtime/sitl/arducopter')).status,404);
  assert.equal((await fetch(url+'/sitl.html')).status,200);
  assert.equal((await fetch(url+'/')).status,200);assert.equal((await fetch(url+'/legacy.html')).status,200);
  assert.equal((await fetch(url+'/api/sitl/recover',{method:'POST',headers,body:'{"sessionId":"old"}'})).status,409);
  const recovery=await fetch(url+'/api/sitl/recover',{method:'POST',headers,body:JSON.stringify({sessionId:'new',request:{fixture:true}})});assert.equal(recovery.status,200);assert.deepEqual(await recovery.json(),{readOnly:true,request:{fixture:true}});
  assert.equal((await fetch(url+'/api/sitl/resume-review',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status,403);
  assert.equal((await fetch(url+'/api/sitl/resume-review',{method:'POST',headers,body:'{"sessionId":"old"}'})).status,409);
  const rr=await fetch(url+'/api/sitl/resume-review',{method:'POST',headers,body:JSON.stringify({sessionId:'new',request:{review:true}})});assert.equal(rr.status,200);assert.deepEqual(await rr.json(),{reviewed:true,request:{review:true}});
  assert.equal((await fetch(url+'/runtime/qgc/QGroundControl-v5.1.5.dmg')).status,404);
  assert.equal(await new Promise((resolve,reject)=>http.get(url+'/api/sitl/status',{headers:{Host:'attacker.test'}},r=>{r.resume();resolve(r.statusCode);}).on('error',reject)),403);
  assert.equal((await fetch(url+'/api/sitl/command',{method:'POST',headers:{...headers,'X-Aeris-Token':'é'.repeat(48)},body:'{}'})).status,403);
  assert.equal((await fetch(url+'/api/sitl/command',{method:'POST',headers,body:JSON.stringify({sessionId:'new',data:'x'.repeat(70000)})})).status,413);
 }finally{s.close();await once(s,'close');}
 const off=createAppServer();off.listen(0,'127.0.0.1');await once(off,'listening');try{assert.equal((await fetch(`http://127.0.0.1:${off.address().port}/api/sitl/status`)).status,503);}finally{off.close();await once(off,'close');}
});
