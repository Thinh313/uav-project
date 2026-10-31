/** Independent real legacy protocol replay. No Flight action/state stubs or listener. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Readable} from 'node:stream';
import {EventEmitter} from 'node:events';
import {randomUUID,createHash} from 'node:crypto';
import {createMockCompatibleG5} from '../../pilot/beta06g5r1/entry.mjs';
const E='evidence/beta06/generation05-mockcompat01/';
const manifestPath=path.resolve(process.argv[2]??E+'overlay-pins03.json');
const report=E+'qa-real-mock-journey02.json';
const out=E+'qa-real-mock-app02',reloadOut=E+'qa-real-mock-reload02';
const sha=b=>createHash('sha256').update(b).digest('hex');
const document=fs.readFileSync('evidence/beta06/generation04/workspace02/journal.jsonl','utf8').trim().split('\n').map(JSON.parse).findLast(r=>r.kind==='WORKSPACE_SAVED').data.document;
const steps=[];let app,reloaded,renew,run=null;
async function req(server,url,body,headers={}){
 return new Promise((yes,no)=>{const b=body===undefined?Buffer.alloc(0):Buffer.from(JSON.stringify(body)),q=Readable.from(b.length?[b]:[]);Object.assign(q,{url,method:body===undefined?'GET':'POST',headers:{host:'127.0.0.1:8872',origin:'http://127.0.0.1:8872','content-type':'application/json',...headers}});const res=new EventEmitter();Object.assign(res,{writableEnded:false,destroyed:false,writeHead(status,h){this.status=status;this.headers=h;},setHeader(){},end(bytes){this.writableEnded=true;try{yes({status:this.status,value:JSON.parse(Buffer.from(bytes).toString())});}catch(e){no(e);}}});server.emit('request',q,res);});
}
try{
 app=await createMockCompatibleG5({manifestPath,out});
 assert.throws(()=>app.listen(),/NO_LISTENER/);assert.throws(()=>app.server.listen(),/NO_LISTENER/);
 const b=(await req(app.server,'/api/bootstrap')).value,h={'x-field-csrf':b.csrf};
 const activated=await req(app.server,'/api/client-session',{action:'activate',instance:'QA-real-legacy-mock-journey01'},h);assert.equal(activated.status,200);const c=activated.value.result;
 const context={clientId:c.id,clientEpoch:c.epoch,clientInstance:c.instance};
 let heartbeatFailure=null;renew=setInterval(()=>req(app.server,'/api/client-session',{action:'heartbeat',instance:c.instance,...context},h).then(r=>{if(r.status!==200)heartbeatFailure=r;}).catch(e=>{heartbeatFailure=String(e);}),750);
 const ws=(await req(app.server,'/api/state')).value.workspace;
 const saved=await req(app.server,'/api/native82',{action:'save',expected:ws.token,body:JSON.stringify(document)},h);assert.equal(saved.status,200,JSON.stringify(saved));
 async function flight(action,extra={}){
  assert.equal(heartbeatFailure,null);const state=(await req(app.server,'/api/state')).value;
  const r=await req(app.server,'/api/flight',{action,confirmSimulation:true,...state.flight.request,...context,...extra,uiActionId:randomUUID()},h);
  steps.push({action,status:r.status,uiActionId:r.value.uiActionId??null,closeIndexStatus:r.value.result?.closeIndex?.status??null});assert.equal(r.status,200,JSON.stringify(r.value));assert.equal(r.value.ok,true);return r.value.result;
 }
 const connected=await flight('connect',{mode:'mock',modelSha256:document.mission.sha256,planSha256:document.compiled.plan.sha256});
 run=connected.run;assert.match(run,/^m[a-f0-9]{20}$/);assert.equal(app.flight.current.link.socket.constructor.name,'MockSocket');assert.equal(app.flight.current.mode,'mock');assert.equal(app.flight.current.proc,undefined);
 const requestPath=app.flight.current.out,session=JSON.parse(fs.readFileSync(requestPath+'/session.json'));
 assert.equal(session.run,run);assert.equal(session.mode,'mock');
 await flight('preflight');await flight('grant',{authorityConfirmed:true});await flight('upload');
 const armed=await flight('arm');assert.equal(typeof armed.sha256,'string');
 await flight('auto',{postArmHomeConfirmed:true,homeReviewSha256:armed.sha256});
 const start=performance.now();let complete;
 do{assert.equal(heartbeatFailure,null);const s=(await req(app.server,'/api/state')).value;complete=s.flight.live?.completion;if(complete?.complete)break;assert(performance.now()-start<15000,'REAL_MOCK_COMPLETION_DEADLINE');await new Promise(r=>setTimeout(r,100));}while(true);
 assert.equal(complete.autoObserved,true);assert.equal(complete.groundDisarmed,true);assert.equal(complete.nearHome,true);
 const closed=await flight('close');assert.equal(closed.mode,'mock');assert.equal(closed.source,'MOCK_PROTOCOL_REPLAY_NOT_AP');assert.equal(closed.run,run);assert.equal(closed.accepted,true);assert.equal(closed.execution.complete,true);assert.equal(closed.actualImages,0);assert.equal(closed.authorityRestorable,false);assert.equal(closed.closeIndex.status,'CLOSED_REVIEW_INDEXED');assert.equal(app.flight.state().run,null);
 assert.equal(fs.existsSync(requestPath+'/closure.json'),false,'NO_SYNTHESIZED_OWNED_CLOSURE');
 const state=(await req(app.server,'/api/state')).value;assert.equal(state.closeIndexFailure,null);const history=state.flightReviews.find(r=>r.run===run);assert(history);assert.equal(history.mode,'mock');assert.equal(history.source,'MOCK_PROTOCOL_REPLAY_NOT_AP');assert.equal(history.execution.complete,true);assert.equal(history.accepted,true);assert.equal(history.authorityRestorable,false);
 const rows=app.store.records().filter(r=>r.kind.includes('FLIGHT_REVIEW'));assert.equal(rows.length,1);assert.notEqual(rows[0].kind,'FLIGHT_REVIEW_SEALED_REF');
 clearInterval(renew);renew=null;await app.close();
 reloaded=await createMockCompatibleG5({manifestPath,out:reloadOut,workspaceRoot:path.resolve(out,'workspace')});
 const restored=(await req(reloaded.server,'/api/state'));assert.equal(restored.status,200,JSON.stringify(restored.value));const again=restored.value.flightReviews.find(r=>r.run===run);assert.deepEqual(again,history);assert.equal(restored.value.flight.run,null);assert.equal(restored.value.flight.authority,null);assert.equal(restored.value.authorityRestored,false);await reloaded.close();
 const {replay}=await import('../../pilot/auto63/journal-v3.mjs'),raw=replay(requestPath+'/raw.jsonl'),review=JSON.parse(fs.readFileSync(requestPath+'/review.json'));
 assert.equal(review.rawHead,raw.head);assert.equal(review.rawRecords,raw.rows.length);assert.equal(review.mode,'mock');assert.equal(review.source,'MOCK_PROTOCOL_REPLAY_NOT_AP');assert.equal(raw.rows.find(r=>r.kind==='FIELD01_CLOSING').data.aborted,false);
 const files={};for(const root of [requestPath,out,reloadOut]){for(const p of fs.readdirSync(root,{recursive:true}).map(n=>path.join(root,n))){if(fs.statSync(p).isFile()){const b=fs.readFileSync(p);files[path.relative(process.cwd(),p)]={bytes:b.length,sha256:sha(b)};}}}
 const result={status:'PASS_REAL_LEGACY_MOCKSOCKET_ACTUAL_REVISION_HANDLER_STRICT_STORE_HISTORY_RELOAD',scope:'SOURCE_MOCK_PROTOCOL_REPLAY_ONLY_NOT_AP_NOT_PHYSICS_NO_BROWSER',run,source:review.source,mode:review.mode,steps,complete,historyKind:rows[0].kind,history,request:JSON.parse(fs.readFileSync(requestPath+'/request.json')),session,raw:{records:raw.rows.length,head:raw.head,kindCounts:Object.fromEntries([...new Set(raw.rows.map(r=>r.kind))].sort().map(k=>[k,raw.rows.filter(r=>r.kind===k).length]))},noOwnedClosure:true,flightActionOrStateStubs:false,APRequests:0,listenersOpened:0,retainedReplayEvidence:files,retainedPurpose:'Bounded positive replay evidence, not disposable scratch. Original G5 workspace untouched.',manifest:{path:manifestPath,sha256:sha(fs.readFileSync(manifestPath))}};
 fs.writeFileSync(report,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:result.status,run,raw:result.raw,steps,files:Object.keys(files).length}));
}catch(e){const failure=E+'qa-real-mock-journey-failure-'+Date.now()+'.json';fs.writeFileSync(failure,JSON.stringify({status:'FAIL',error:e.stack,steps,run,scope:'SOURCE_MOCK_ONLY'},null,2)+'\n',{flag:'wx'});throw e;}
finally{if(renew)clearInterval(renew);for(const a of [reloaded,app])if(a)try{await a.close();}catch{}}
