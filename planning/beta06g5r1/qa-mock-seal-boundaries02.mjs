/** Rehashed mutation challenges from our real, retained MockSocket replay. */
import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';
import{mockReviewIndex}from'../../pilot/beta06g5r1/mock-review.mjs';import{stable}from'../../pilot/auto63/compiler.mjs';
const E='evidence/beta06/generation05-mockcompat01/',receipt=JSON.parse(fs.readFileSync(E+'qa-real-mock-journey01.json')),run=receipt.run;
const src=path.resolve(E+'flight/runs/'+run),scratch=path.resolve(E+'qa-mock-seal-negative-scratch02'),root=path.join(scratch,'flight'),dir=path.join(root,'runs',run),hash=b=>createHash('sha256').update(b).digest('hex');
const originals=Object.fromEntries(fs.readdirSync(src).map(n=>[n,fs.readFileSync(path.join(src,n))]));assert(Object.values(originals).reduce((n,b)=>n+b.length,0)<8*2**20);
fs.mkdirSync(dir,{recursive:true});const rows=[];let r;
function reset(){for(const n of fs.readdirSync(dir))fs.rmSync(path.join(dir,n),{recursive:true,force:true});for(const[n,b]of Object.entries(originals))fs.writeFileSync(path.join(dir,n),b);r=JSON.parse(originals['review.json']);}
function reseal(){fs.writeFileSync(path.join(dir,'review.json'),stable(r)+'\n');}
function artifact(n,value){const b=Buffer.isBuffer(value)?value:Buffer.from(stable(value)+'\n');fs.writeFileSync(path.join(dir,n),b);r.filesSha256[n]=hash(b);reseal();}
const cases=[
 ['wrong-review-mode',()=>{r.mode='sitl';reseal();}],
 ['wrong-review-source',()=>{r.source='OBSERVED_ARDUPILOT_INTERNAL_QUAD_HOST_NODE_GCS';reseal();}],
 ['foreign-request-instance-rehashed',()=>{const q=JSON.parse(originals['request.json']);q.instance='11111111-1111-4111-8111-111111111111';artifact('request.json',q);}],
 ['foreign-request-source-rehashed',()=>{const q=JSON.parse(originals['request.json']);q.source='OBSERVED_OWNED_SITL';artifact('request.json',q);}],
 ['foreign-session-rehashed',()=>{const q=JSON.parse(originals['session.json']);q.session='22222222-2222-4222-8222-222222222222';artifact('session.json',q);}],
 ['foreign-model-rehashed',()=>{const q=JSON.parse(originals['document92.json']);q.mission.sha256='0'.repeat(64);artifact('document92.json',q);}],
 ['raw-chain-rehashed-file',()=>{const lines=originals['raw.jsonl'].toString().trimEnd().split('\n');const q=JSON.parse(lines[2]);q.n++;lines[2]=stable(q);artifact('raw.jsonl',Buffer.from(lines.join('\n')+'\n'));}],
 ['torn-raw-rehashed-file',()=>artifact('raw.jsonl',originals['raw.jsonl'].subarray(0,originals['raw.jsonl'].length-1))],
 ['missing-document',()=>fs.unlinkSync(path.join(dir,'document92.json'))],
 ['symlink-document',()=>{const n=path.join(dir,'document92.json');fs.unlinkSync(n);fs.symlinkSync(path.join(src,'document92.json'),n);}],
 ['map-parent-traversal',()=>{r.filesSha256['../request.json']='0'.repeat(64);reseal();}],
 ['nonfinite-json-number',()=>{const b=stable(r).replace('"actualImages":0','"actualImages":1e999');fs.writeFileSync(path.join(dir,'review.json'),b+'\n');}],
 ['oversized-review',()=>{r.padding='a'.repeat(300*1024);reseal();}],
 ['strict-64-key-serializer',()=>{r.execution.extra=Object.fromEntries(Array.from({length:65},(_,i)=>['k'+i,i]));reseal();}],
 ['execution-contradicts-raw-closing',()=>{r.execution={...r.execution,complete:false,nearHome:false};r.accepted=false;reseal();}],
 ['failure-contradicts-raw-closing',()=>{r.failure='INVENTED_FAILURE';r.accepted=false;reseal();}],
 ['accepted-false-contradiction',()=>{r.accepted=false;reseal();}],
 ['accepted-aborted-contradiction',()=>{r.aborted=true;reseal();}],
 ['terminal-route-rehashed-contradiction',()=>{const rs=originals['raw.jsonl'].toString().trimEnd().split('\n').map(JSON.parse);rs.findLast(x=>x.kind==='FIELD01_INTENT').data.route='abort';let previous='';for(const row of rs){const{sha256,...body}=row;body.previous=previous;Object.assign(row,body,{sha256:hash(stable(body))});previous=row.sha256;}r.rawHead=previous;artifact('raw.jsonl',Buffer.from(rs.map(stable).join('\n')+'\n'));}],
 ['invented-owned-closure',()=>fs.writeFileSync(path.join(dir,'closure.json'),'{}\n')],
];
try{
 reset();assert.equal(mockReviewIndex({root,run,currentRun:null}).mockReviewRef.run,run);
 for(const[name,change]of cases){reset();change();let error=null;try{mockReviewIndex({root,run,currentRun:null});}catch(e){error=e.message;}rows.push({name,error});assert(error,'UNEXPECTED_MUTATION_ACCEPTED:'+name);}
 reset();for(const [name,input]of [['s-prefix',{run:'s'+run.slice(1)}],['still-current',{currentRun:run}],['foreign-returned-review',{result:{...r,accepted:false}}]]){let error=null;try{mockReviewIndex({root,run,currentRun:null,...input});}catch(e){error=e.message;}rows.push({name,error});assert(error,'UNEXPECTED_BINDING_ACCEPTED:'+name);}
 fs.writeFileSync(E+'qa-mock-seal-boundaries02.json',JSON.stringify({status:'PASS_INDEPENDENT_REHASHED_MOCK_SEAL_MUTATIONS',scope:'SOURCE_PROTOCOL_REPLAY_NOT_AP',sourceReplayRun:run,groups:rows.length,rows,removed:[scratch]},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',groups:rows.length,rows}));
}catch(e){fs.writeFileSync(E+'qa-mock-seal-boundaries-failure-'+Date.now()+'.json',JSON.stringify({status:'FAIL',error:e.stack,rows},null,2)+'\n',{flag:'wx'});throw e;}
finally{fs.rmSync(scratch,{recursive:true,force:true});}
