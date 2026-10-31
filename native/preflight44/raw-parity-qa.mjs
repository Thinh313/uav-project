import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {parse43} from '../../pilot/preflight43/replay.mjs';
import {Preflight43} from './preflight/adapter.mjs';
import {stable} from './preflight/profile.mjs';
import {unhex} from './preflight/wire.mjs';
const sessions=[];
for(const name of ['session01','session02','session03']){
 const text=await readFile('evidence/preflight43/run02/'+name+'-raw.jsonl','utf8');
 const original=parse43(text),rows=text.trimEnd().split('\n').map(JSON.parse),first=rows[0];
 const adapter=new Preflight43(first.profile,first.context),intents=new Map(),actions=[];let frames=0;
 for(const row of rows){if(row.kind==='TX_INTENT')actions.push({kind:'INTENT',at:row.intent.at,row});else if(['TX_WRITE_RETURN','RX','BEGIN_COHORT','ASSESSMENT','SOCKET_CLOSE'].includes(row.kind))actions.push({kind:row.kind,at:row.hostMs,row});}
 actions.sort((a,b)=>a.at-b.at);
 for(const {kind,row:r} of actions){
  if(kind==='INTENT'){const i=r.intent;let out;if(i.reason==='GCS_HEARTBEAT')out=adapter.heartbeat(i.at);else if(i.reason==='DISCOVERY_148')out=adapter.discover(i.at);else if(i.reason.startsWith('STREAM_'))out=adapter.stream(Number(i.reason.slice(7)),i.at);else if(i.reason.startsWith('READ_'))out=adapter.readNext(i.at);else throw Error('UNSUPPORTED_INTENT');assert.equal(stable(out),stable(i));intents.set(i.id,out);}
  if(kind==='TX_WRITE_RETURN')adapter.written(intents.get(r.intentId),r.hostMs);
  if(kind==='RX')frames+=adapter.receive(unhex(r.rawHex),{origin:first.context.origin,context:first.context,receivedAtMs:r.hostMs},r.hostMs).length;
  if(kind==='BEGIN_COHORT')assert.equal(adapter.beginCycle(r.hostMs),r.generation);
  if(kind==='ASSESSMENT')assert.equal(stable(adapter.assess(r.hostMs)),stable(r.assessment));
  if(kind==='SOCKET_CLOSE')adapter.invalidate('SOCKET_CLOSED');
 }
 assert.equal(frames,original.frames);assert.equal(adapter.assess(rows.at(-1).hostMs).state,original.lastState);
 sessions.push({name,rawSha256:original.rawSha256,rows:original.rows,frames,tx:original.txCount,assessments:original.assessments.length,pass:true});
}
await writeFile('evidence/native44/raw-parity1.json',JSON.stringify({status:'PASS',sessions,scope:'Portable44 and original43 exact intents/assessments on existing ownedSITL raw; cold replay only, no new transport/flight'},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:'PASS',sessions:sessions.length,rows:sessions.reduce((n,s)=>n+s.rows,0),frames:sessions.reduce((n,s)=>n+s.frames,0)}));
