import assert from'node:assert/strict';import fs from'node:fs';import{createWorkspace}from'./server.mjs';import{MockBackend}from'../aeris57/mock.mjs';
class CheckedMock extends MockBackend{reads=0;canonicalReject=false;async get(route){this.reads++;return super.get(route)}async post(route,d){if(route==='input'&&this.canonicalReject){this.calls.push({route,body:d});throw Error('CANONICAL_FRESHNESS_REJECTION')}return super.post(route,d)}}
const b=new CheckedMock(),w=await createWorkspace({backend:b,storeRoot:'evidence/pace58/qa-fastpath-store'});const s=await w.perform('start',{mode:'optimized',load:'empty',wind:'calm'});b.reads=0;
await w.perform('input',{session:s.session,boot:s.boot,packet:{axes:[0,0,0,0]}});assert.equal(b.reads,0);assert.equal(b.calls.filter(c=>c.route==='input').length,1);
const n=b.calls.length;await assert.rejects(()=>w.perform('input',{session:'foreign',boot:s.boot}),/OWNED_SESSION/);assert.equal(b.calls.length,n);
b.canonicalReject=true;await assert.rejects(()=>w.perform('input',{session:s.session,boot:s.boot,packet:{axes:[0,0,0,0]}}),/CANONICAL_FRESHNESS_REJECTION/);assert.equal(b.calls.length,n+1);assert.equal(b.reads,0);
b.canonicalReject=false;b.failure='input';const before=b.calls.length;await assert.rejects(()=>w.perform('input',{session:s.session,boot:s.boot,packet:{axes:[0,0,0,0]}}),/WRITE_OUTCOME_UNKNOWN_NO_RETRY/);assert.equal(b.calls.length,before+1);
await assert.rejects(()=>w.perform('auto',{session:s.session,boot:s.boot}),/ALLOWLIST/);
fs.writeFileSync('evidence/pace58/qa-fastpath.json',JSON.stringify({status:'PASS_SCOPED_CHECKED_MOCK',checks:5,canonicalSafetyAdapterStillInvoked:true,skippedRedundantStateGET:true,unknownPostRetries:0,liveAP:false},null,2)+'\n',{flag:'wx'});console.log('Fastpath5 checks PASS');
