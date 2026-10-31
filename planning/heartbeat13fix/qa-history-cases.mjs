/** Independent worker/history falsification; callable only by the bounded QA runner. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {canonicalize,jsonBytes,sha256} from '../../pilot/field02/evidence/schema.mjs';

const digest=b=>createHash('sha256').update(b).digest('hex');
export function sealedFixture() {
  const parent=path.resolve('planning/heartbeat13fix/qa-scratch');fs.mkdirSync(parent,{recursive:true});
  const scratch=fs.mkdtempSync(path.join(parent,'codex-tmp-qa-history-20261023-'));
  try {
  const root=path.join(scratch,'flight'),workspaceRoot=path.join(scratch,'workspace');
  fs.mkdirSync(root);fs.mkdirSync(workspaceRoot);
  const source='evidence/beta06/generation12',walPath=source+'/workspace01/journal.jsonl';
  const wal=fs.readFileSync(walPath);assert.equal(wal.at(-1),10);
  const records=[];let head='0'.repeat(64);
  for(const line of wal.toString().trimEnd().split('\n')) {
    const row=JSON.parse(line),{hash,...body}=row;
    assert.equal(canonicalize(row),line);assert.equal(row.seq,records.length+1);
    assert.equal(row.previousHash,head);assert.equal(sha256(jsonBytes(body)),hash);
    head=hash;records.push(row);
  }
  assert(!records.some(row=>row.kind==='FLIGHT_REVIEW_MOCK_REF'),'FIXTURE_MOCK_BINDINGS_NOT_IN_THIS_SCOPE');
  const copies=[];
  for(const row of records.filter(row=>row.kind==='FLIGHT_REVIEW_SEALED_REF')) {
    const run=row.data.reviewRef.run;assert(/^s[a-f0-9]{20}$/.test(run));
    const dir=path.join(root,'runs',run);fs.mkdirSync(dir,{recursive:true});
    for(const name of ['review.json','closure.json']) {
      const input=source+'/flight/runs/'+run+'/'+name,s=fs.lstatSync(input);
      assert(s.isFile()&&!s.isSymbolicLink()&&s.size<=256*1024);
      const bytes=fs.readFileSync(input),output=path.join(dir,name),fd=fs.openSync(output,'wx',0o600);
      try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
      copies.push({input,bytes:bytes.length,sha256:digest(bytes),output});
    }
  }
  assert.equal(copies.length,4,'TWO_CLOSED_G12_SEALED_RUNS_ONLY');
  const q={root,workspaceRoot,currentRun:null,head,records};
  return {q,copies,wal:{path:walPath,sha256:digest(wal),records:records.length,head},scratch,
    cleanup(){fs.rmSync(scratch,{recursive:true});assert(!fs.existsSync(scratch));if(!fs.readdirSync(parent).length)fs.rmdirSync(parent);}};
  } catch(error) {
    fs.rmSync(scratch,{recursive:true});
    if(!fs.readdirSync(parent).length)fs.rmdirSync(parent);
    throw error;
  }
}

export async function historyCases(createHistoryReader,fixture) {
  const q=fixture.q,checks=[];
  async function using(options,fn){const reader=createHistoryReader(options);try{return await fn(reader);}finally{await reader.close();}}
  const main=await using({worker:false},reader=>reader.verify(q,{isCurrent:()=>true}));
  const isolated=await using({worker:true},reader=>reader.verify(q,{isCurrent:()=>true}));
  assert.deepEqual(isolated,main);
  checks.push({case:'EXACT_MAIN_AND_WORKER_HISTORY_EQUAL',rows:isolated.length});

  await using({worker:true},async reader=>{
    let current=true;const promise=reader.verify(q,{isCurrent:()=>current});
    current=false;await assert.rejects(promise,/CONTEXT_SUPERSEDED/);
    assert.equal(reader.diagnostics().pending,0);
  });
  checks.push({case:'CALLER_CONTEXT_CHANGED_BEFORE_RESULT_REFUSES'});

  const review=fixture.copies.find(row=>row.input.endsWith('/review.json'));
  const bytes=fs.readFileSync(review.output),tampered=Buffer.from(bytes);
  const at=bytes.indexOf(Buffer.from('"actualImages":0'));assert(at>=0);
  tampered[at+15]='1'.charCodeAt(0);assert.notEqual(digest(tampered),digest(bytes));
  fs.writeFileSync(review.output,tampered);
  try {
    await using({worker:true},reader=>assert.rejects(reader.verify(q,{isCurrent:()=>true})));
  }finally{fs.writeFileSync(review.output,bytes);assert.equal(digest(fs.readFileSync(review.output)),review.sha256);}
  checks.push({case:'TAMPERED_SEALED_BYTES_REFUSE_NO_CACHE',originalSHA256:digest(bytes),tamperedSHA256:digest(tampered)});

  await using({worker:true,fault:{error:'QA_SEALED_READ_EIO',targetPath:review.output}},reader=>
    assert.rejects(reader.verify(q,{isCurrent:()=>true}),/QA_SEALED_READ_EIO/));
  checks.push({case:'WORKER_SEALED_READ_ERROR_REFUSES'});

  await using({worker:true},async reader=>{
    const promise=reader.verify(q,{isCurrent:()=>true});
    const rejection=assert.rejects(promise,/WORKER_FAILED/);
    await reader.terminateForTest();await rejection;
    await assert.rejects(reader.verify(q,{isCurrent:()=>true}),/CLOSED_OR_FAILED/);
  });
  checks.push({case:'WORKER_DEATH_REJECTS_PENDING_AND_FUTURE'});

  const reader=createHistoryReader({worker:true});
  const tiny={...q,records:[],head:'0'.repeat(64)};
  const pending=Array.from({length:16},()=>reader.verify(tiny,{isCurrent:()=>true}));
  const completion=Promise.allSettled(pending);
  await assert.rejects(reader.verify(tiny,{isCurrent:()=>true}),/QUEUE_QUOTA/);
  await reader.close();const stopped=await completion;
  assert(stopped.every(value=>value.status==='rejected'));
  assert.equal(reader.diagnostics().pending,0);assert.equal(reader.diagnostics().queuedBytes,0);
  checks.push({case:'DEFAULT16_QUEUE_LIMIT_AND_CLOSE_CANCELS_ALL_NO_STRANDED_WORK',rejected:stopped.length});

  const size=Buffer.byteLength(JSON.stringify(q));
  await using({worker:true,maxQueuedBytes:size},reader=>reader.verify(q,{isCurrent:()=>true}));
  await using({worker:true,maxQueuedBytes:size-1},reader=>
    assert.rejects(reader.verify(q,{isCurrent:()=>true}),/QUEUE_QUOTA/));
  checks.push({case:'EXACT_SERIALIZED_QUEUE_BYTES_AND_ONE_BYTE_SHORT',bytes:size});
  return {checks,fixtureWal:fixture.wal,
    copiedArtifacts:fixture.copies.map(({output,...row})=>row),
    dependencies:'Actual immutable r1 reviewHistory/assertWorkspaceOutcomes and R2 sealed verifier; strict input WAL chain independently replayed. No alternate acceptance algorithm or metadata-only trust.',
    limits:'Only retained closed G12 sealed evidence reused as synthetic read-only history fixture. No current AP, HTTP/TCP, Android or actual G12 initiating-cause claim.'};
}
