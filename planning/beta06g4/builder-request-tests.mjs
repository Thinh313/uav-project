import fs from'node:fs';import os from'node:os';import path from'node:path';import assert from'node:assert/strict';
import{priorRequests,FlightBeta06G4}from'../../pilot/beta06g4/flight/adapter.mjs';
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'codex-tmp-g4-cap-20261022-')),runs=path.join(dir,'runs');fs.mkdirSync(runs);
const journal=fs.readFileSync('evidence/beta06/generation04/workspace02/journal.jsonl','utf8').trim().split('\n').map(JSON.parse),document=journal.findLast(x=>x.kind==='WORKSPACE_SAVED').data.document,checks=[];
try{
 for(let i=0;i<4;i++){const rid='s'+String(i).repeat(20),p=path.join(runs,rid);fs.mkdirSync(p);fs.writeFileSync(p+'/request.json',JSON.stringify({run:rid,mode:'sitl'}));}
 assert.equal(priorRequests(runs).length,4);checks.push('own_four_valid_requests_counted');
 const subject={current:null,pins(){return{}},document,evidenceRoot:dir},before=fs.readdirSync(runs);await assert.rejects(()=>FlightBeta06G4.prototype.connect.call(subject,{mode:'sitl',confirmSimulation:true}),/MAX_FOUR/);assert.deepEqual(fs.readdirSync(runs),before);checks.push('fifth_refused_before_allocation_or_write');
 const last=path.join(runs,'s'+'3'.repeat(20));fs.rmSync(last,{recursive:true});await assert.rejects(()=>FlightBeta06G4.prototype.connect.call(subject,{mode:'sitl',confirmSimulation:true}),/PRIOR_REQUEST_UNCLOSED/);checks.push('failed_preparation_without_review_blocks_next');
 const first=path.join(runs,'s'+'0'.repeat(20));fs.writeFileSync(first+'/request.json','broken');assert.throws(()=>priorRequests(runs),/UNKNOWN_REQUEST/);checks.push('malformed_request_fail_closed');
 console.log(JSON.stringify({status:'PASS',checks,scope:'MOCK_FILES_NO_SUBPROCESS_OR_RUNTIME',temporaryRemoved:dir}));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
