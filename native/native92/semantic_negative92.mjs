import fs from 'node:fs';import assert from 'node:assert/strict';import {spawnSync} from 'node:child_process';import{sha92,make92,stable92}from'./assets/mission92.mjs';
const E='evidence/native92',j=JSON.parse(fs.readFileSync(E+'/android92-journal-closed07.json')),base=JSON.parse(j.journals['workspaces/initial'].latest.body),results=[];
function replay(w){const p=spawnSync('node',['native/native92/receiver_workflow91.mjs'],{input:JSON.stringify([{kind:'workspace',body:JSON.stringify(w)}]),encoding:'utf8',timeout:30000});return p;}
assert.equal(replay(base).status,0);
async function test(name,edit){const w=structuredClone(base);await edit(w);const p=replay(w);assert.notEqual(p.status,0,name);results.push({name,rejected:true,reason:p.stderr.slice(-600)});}
async function rehashPlan(w){let{sha256,...b}=w.compiled.plan;w.compiled.plan.sha256=await sha92(b)}
async function rehashModel(w){const{sha256,...body}=w.mission;const m={...body,sha256:await sha92(body)};w.mission=m;w.compiled.modelSha256=m.sha256;w.compiled.modelRevision=m.revision;}
await test('stale model revision',w=>{w.compiled.modelRevision++});
await test('rehashed mission placeholder replaces camera',async w=>{w.compiled.plan.compiled.items.find(x=>x.command===206).command=0;w.compiled.plan.missionSha256=await sha92(w.compiled.plan.compiled.items);await rehashPlan(w)});
await test('rehashed wrong Home',async w=>{w.mission.draft.home.lat+=.001;await rehashModel(w)});
await test('rehashed altered camera',async w=>{w.mission.draft.camera.id="ALTERED";await rehashModel(w)});
await test('rehashed wrong speed with matching acquisition metadata',async w=>{w.mission.draft.options.speedMS=1.5;await rehashModel(w);w.compiled.plan.acquisition.plan.options.speedMS=1.5;await rehashPlan(w)});
await test('rehashed dropped navigation frame',async w=>{w.compiled.plan.compiled.items.splice(3,1);w.compiled.plan.missionSha256=await sha92(w.compiled.plan.compiled.items);await rehashPlan(w)});
await test('false authority restoration',w=>{w.authorityRestorable=true});
fs.writeFileSync(E+'/semantic-negative92.json',JSON.stringify({status:'PASS',checks:results.length,cases:results,scope:'REHASHED_COMPILED_MODEL_REQUIRES_UNCHANGED_COMPILER_REPLAY_NOT_SHA_ALONE'},null,2),{flag:'wx'});console.log(JSON.stringify({status:'PASS',checks:results.length}));
