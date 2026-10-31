/** Independent remaining-recipe boundaries. All usage/capacity inputs are synthetic. */
import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';
import{ROOT,E,POLICY,decide,futureProjection}from'../../pilot/beta06g7/quota.mjs';
const name=process.argv[2];assert.match(name??'',/^qa-future-independent-[a-z0-9-]+\.json$/);const out=path.join(ROOT,E,name);assert(!fs.existsSync(out));
const sha=b=>createHash('sha256').update(b).digest('hex');const sources=['pilot/beta06g7/quota.mjs','pilot/beta06g7/quota-policy.json'];const sourceHashes=Object.fromEntries(sources.map(p=>[p,sha(fs.readFileSync(path.join(ROOT,p)))]));const groups=[];
const expected=(A,H)=>({ap:{entries:1536*A,bytes:90*A*2**20},sourceQA:{entries:6*A+16,bytes:(12*A+2)*2**20},native:{entries:128*A+48*H+32,bytes:(12*A+12*H+8)*2**20},screenshots:{entries:40*A+8*H+8,bytes:5*(40*A+8*H+8)*2**20},store:{entries:32*A+32,bytes:(16*A+16)*2**20},media:{entries:8*A+4*H+4,bytes:(8*A+8*H+8)*2**20},hostJournals:{entries:5*H+2,bytes:(4*A+H)*2**20},clock:{entries:H+1,bytes:(A+H)*2**20},hostOther:{entries:8*A+32*H+16,bytes:(8*A+8*H+16)*2**20}});
function usage(A,H){return{counts:Object.fromEntries(Object.keys(POLICY.categories).map(k=>[k,{entries:0,bytes:0}])),apRuns:{},newEntries:0,newBytes:0,capacity:{sitlRequests:4-A,hostProcesses:2-H}};}
function totals(u){u.newEntries=Object.values(u.counts).reduce((n,x)=>n+x.entries,0);u.newBytes=Object.values(u.counts).reduce((n,x)=>n+x.bytes,0);return u;}
function decision(u,A,H,phase){return decide(totals(u),{remaining_ap:A,remaining_hosts:H,phase,freeBytes:32*2**30});}
function test(name,fn){try{fn();groups.push({name,status:'PASS'});}catch(e){groups.push({name,status:'FAIL',error:e.message});}}
const stages=[{A:4,H:2,phase:'before-host'},{A:4,H:1,phase:'before-connect'},{A:3,H:1,phase:'before-connect'},{A:2,H:1,phase:'before-host'},{A:2,H:0,phase:'before-connect'},{A:1,H:0,phase:'before-connect'}];
test('exact_independently_calculated_nine_category_projection_all_six_stages',()=>{for(const s of stages)assert.deepEqual(futureProjection(s.A,s.H),expected(s.A,s.H));});
test('all_nine_categories_exact_future_headroom_and_one_entry_one_byte_short',()=>{
 let pairs=0;for(const s of stages){const projection=expected(s.A,s.H);for(const[k,f]of Object.entries(projection))for(const field of ['entries','bytes']){
  const c=POLICY.categories[k],cap=k==='ap'?(field==='entries'?c.slots*c.entriesPerSlot:c.slots*c.bytesPerSlot):c[field]-(c[field==='entries'?'closureEntries':'closureBytes']??0);
  const u=usage(s.A,s.H);u.counts[k][field]=cap-f[field];assert(u.counts[k][field]>=0);
  assert.equal(decision(u,s.A,s.H,s.phase).status,'ADMITTED',`${k}/${field}/${s.A}/${s.H} exact`);
  u.counts[k][field]++;assert.throws(()=>decision(u,s.A,s.H,s.phase),new RegExp('FUTURE_RECIPE_HEADROOM:'+k),`${k}/${field}/${s.A}/${s.H} one short`);pairs++;
 }}assert.equal(pairs,108);
});
test('original_sourceQA480_counterexample_now_refused_before_all_effects',()=>{const u=usage(4,2);u.counts.sourceQA.entries=480;assert.throws(()=>decision(u,4,2,'before-connect'),/FUTURE_RECIPE_HEADROOM:sourceQA/);});
test('missing_invalid_and_mismatched_capacity_refused',()=>{
 for(const capacity of [undefined,{sitlRequests:-1,hostProcesses:0},{sitlRequests:0,hostProcesses:3},{sitlRequests:0.5,hostProcesses:0}]){const u=usage(4,2);u.capacity=capacity;assert.throws(()=>decision(u,4,2,'before-host'),/CAPACITY_ONLY_OCCUPANCY_REQUIRED/);}
 assert.throws(()=>decision(usage(3,1),4,2,'before-connect'),/ORIGINAL_COUNTER_CAPACITY_MISMATCH/);
});
test('node_capacity_derived_late_stage_counters_not_default_four_two',()=>{
 const d=decide(usage(1,0),{phase:'before-connect',freeBytes:32*2**30});assert.equal(d.remainingReservations.remainingAP,1);assert.equal(d.remainingReservations.remainingHosts,0);assert.deepEqual(d.futureRecipe,expected(1,0));
});
test('guard_and_mock_phases_do_not_reserve_actual_fourAP_recipe',()=>{const u=usage(4,2);delete u.capacity;u.counts.sourceQA.entries=480;totals(u);for(const phase of ['guard','mock','runtime'])assert.equal(decide(u,{phase,freeBytes:32*2**30}).status,'ADMITTED');});
test('known_closed_fixture_first_host_and_later_recipe_capacity_fit',()=>{
 // These are explicit operational fixtures, not current filesystem acceptance.
 for(const s of stages){const u=usage(s.A,s.H);u.counts.store={entries:28,bytes:870221};u.counts.sourceQA={entries:410+(4-s.A)*6,bytes:(8+(4-s.A)*3)*2**20};u.counts.native={entries:10+(4-s.A)*20,bytes:(2+(4-s.A)*2)*2**20};u.counts.screenshots={entries:(4-s.A)*20,bytes:(4-s.A)*20*2**20};assert.equal(decision(u,s.A,s.H,s.phase).status,'ADMITTED');}
});
for(const[p,h]of Object.entries(sourceHashes))assert.equal(sha(fs.readFileSync(path.join(ROOT,p))),h,'source changed during synthetic tests');
const report={status:groups.every(g=>g.status==='PASS')?'PASS_SYNTHETIC_FUTURE_HEADROOM_ONLY':'FAIL_SYNTHETIC_FUTURE_HEADROOM_ONLY',sourceHashes,groups,independentGroups:groups.length,boundaryPairs:108,actualRuntimeActions:0,filesystemPreservationAcceptance:false,preservationIncidentRemainsSeparate:true};fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({path:out,status:report.status,groups:groups.length,failed:groups.filter(g=>g.status!=='PASS')}));
