import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {Observer41,NAMES,liveWitness} from './observer.mjs';
import {FullFramer,unhex,hex,encodeFull} from '../apstream40/wire.mjs';
const E='evidence/sitldiscovery41',BASE=E+'/run03/attempt02';
export async function replayFile(path){const rows=(await readFile(path,'utf8')).trim().split('\n').map(x=>JSON.parse(x));assert.deepEqual(rows.map(x=>x.n),rows.map((_,k)=>k+1));const manifest=rows.find(x=>x.kind==='CONNECT').context,o=new Observer41(manifest);let typed=null,tx=[],frames=0,ids=new Set();
 for(const r of rows){if(r.kind==='RX'){const fs=o.frames(unhex(r.rawHex),{origin:'OBSERVED_OWNED_SITL',context:manifest,receivedAtMs:r.hostMs},r.hostMs);frames+=fs.length;fs.forEach(f=>ids.add(f.id));if(Object.keys(o.snapshot(r.hostMs).parameters).length===8)typed=o.snapshot(r.hostMs);}
  else if(r.kind==='TX_INTENT'){const f=new FullFramer().push(unhex(r.rawHex),0,0)[0];tx.push(f);if(f.id===0)assert.equal(hex(o.heartbeat()),r.rawHex);else if(f.id===76)assert.equal(hex(o.discovery(r.hostMs)),r.rawHex);else if(f.id===20)assert.equal(hex(o.read(f.fields.param_id,r.hostMs)),r.rawHex);else throw Error('outbound not readonly');}
  else if(r.kind==='SOCKET_CLOSE')o.loss('SOCKET_CLOSED');
 }
 const snap=JSON.parse(await readFile(path.replace('-raw.jsonl','-snapshot.json'),'utf8'));assert.ok(typed);assert.deepEqual(typed.version.fields,snap.version.fields);assert.deepEqual(typed.parameters,snap.parameters);assert.equal(o.snapshot(rows.at(-1).hostMs).phase,'INVALIDATED');assert.ok(tx.length===10);assert.equal(tx.filter(x=>x.id===20).length,8);
 return {path,rawSha256:createHash('sha256').update(await readFile(path)).digest('hex'),rows:rows.length,decodedFrames:frames,messageIds:[...ids].sort((a,b)=>a-b),version:snap.version.fields.flight_sw_version,build:String.fromCharCode(...snap.version.fields.flight_custom_version),parameters:typed.parameters,txCount:tx.length,context:manifest,status:'ACTUAL_BYTES_REPLAY_MATCHED',flightAuthority:false,authenticated:false};
}
export async function replayAll(){const out=[];for(const name of ['session01','session02','session03'])out.push(await replayFile(BASE+'/'+name+'-raw.jsonl'));return out;}
if(process.argv[1]?.endsWith('/replay.mjs')){const results=await replayAll();await writeFile(E+'/raw-replay1.json',JSON.stringify({status:'PASS',results},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',sessions:results.length,rows:results.reduce((n,x)=>n+x.rows,0),frames:results.reduce((n,x)=>n+x.decodedFrames,0)}));}
