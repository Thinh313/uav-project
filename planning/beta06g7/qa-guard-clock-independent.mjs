/** Execute the actual guard body with virtual clock/fs/quota dependencies. */
import fs from 'node:fs';import path from 'node:path';import vm from 'node:vm';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import {ROOT,E,POLICY} from '../../pilot/beta06g7/quota.mjs';
import {decideResource} from '../../pilot/beta06/resource.mjs';
const name=process.argv[2];assert.match(name??'',/^qa-guard-clock-independent-[a-z0-9-]+\.json$/);
const file=path.join(ROOT,E,name);assert(!fs.existsSync(file));
const source=fs.readFileSync(path.join(ROOT,'pilot/beta06g7/resource.mjs'),'utf8');
const body=source.split('\n').filter(l=>!l.startsWith('import')).join('\n').replace('export function createResourceGuard','function createResourceGuard')+'\nglobalThis.guardFactory=createResourceGuard;';
const sha=s=>createHash('sha256').update(s).digest('hex'),groups=[];
function setup({finishedMonoMs=100,missing=false,scanReject=false}={}){
 let mono=100,wall=100000,scanCalls=0;const stopped=[],writes=[],timers=[];
 const proof={newBytes:1,newEntries:1,aggregateBytes:135756686,historySha256:POLICY.history.sha256,finishedAt:wall,...missing?{}:{finishedMonoMs}};
 const context={Buffer,Symbol,Number,Math,JSON,Error,Promise,performance:{now:()=>mono},Date:{now:()=>wall},process:{hrtime:{bigint:()=>BigInt(Math.round(mono*1e6))}},path,decideResource,POLICY,
  fs:{openSync:()=>1,statfsSync:()=>({bavail:32*2**30,bsize:1}),writeSync:(fd,b,offset=0,length=b.length)=>{writes.push(Buffer.from(b.subarray(offset,offset+length)));return length;},fsyncSync(){},closeSync(){}},
  scan:()=>{scanCalls++;return scanReject?Promise.reject(Error('SYNTHETIC_HISTORY_DRIFT')):new Promise(()=>{});},
  decide:()=>({status:'ADMITTED'}),setInterval:fn=>{timers.push(fn);return{unref(){}};},clearInterval(){}};
 context[Symbol.for('aeris.g7.quota.last')]=proof;vm.createContext(context);vm.runInContext(body,context,{filename:'ACTUAL_G7_RESOURCE_BODY_WITH_VIRTUAL_DEPENDENCIES'});
 const guard=context.guardFactory({root:'virtual',out:'virtual',onStop:reason=>stopped.push(reason),onObservation(){}});
 return{guard,stopped,writes,setMono:v=>mono=v,setWall:v=>wall=v,scanCalls:()=>scanCalls};
}
async function test(name,fn){try{await fn();groups.push({name,status:'PASS'});}catch(e){groups.push({name,status:'FAIL',error:e.message});}}
await test('wall_clock_backstep_cannot_hide_monotonic_stale_audit',()=>{const t=setup();t.guard.tick();assert.equal(t.stopped.length,0);t.setWall(-1e12);t.setMono(100+POLICY.scanner.staleMs+1);t.guard.tick();assert.match(t.stopped.at(-1),/STALE_FAIL_CLOSED/);t.guard.close();});
await test('missing_and_future_process_monotonic_origin_refused',()=>{for(const opts of [{missing:true},{finishedMonoMs:101}]){const t=setup(opts);t.guard.tick();assert.match(t.stopped.at(-1),/STALE_FAIL_CLOSED/);t.guard.close();}});
await test('heartbeat_ticks_do_not_walk_history_and_trace_retains_complete_rows',()=>{const t=setup();for(let i=0;i<8;i++){t.setMono(100+i*250);t.guard.tick();}assert.equal(t.scanCalls(),1);assert.equal(t.stopped.length,0);assert.equal(t.writes.length,8);for(const row of t.writes){assert.equal(row.at(-1),10);assert(Number.isFinite(JSON.parse(row).quotaAuditAgeMs));}t.guard.close();});
await test('async_historical_audit_error_fails_closed_on_next_tick',async()=>{const t=setup({scanReject:true});await Promise.resolve();await Promise.resolve();await Promise.resolve();t.guard.tick();assert.match(t.stopped.at(-1),/SYNTHETIC_HISTORY_DRIFT/);t.guard.close();});
assert.equal(sha(fs.readFileSync(path.join(ROOT,'pilot/beta06g7/resource.mjs'))),sha(source));
const report={status:groups.every(g=>g.status==='PASS')?'PASS_SOURCE_MOCK_ONLY':'FAIL_SOURCE_MOCK_ONLY',source:{path:'pilot/beta06g7/resource.mjs',sha256:sha(source)},bodyExtraction:'Only import declarations and export keyword replaced; actual guard function body executed in VM',groups,independentGroups:groups.length,allClockFsQuotaDependenciesVirtual:true,actualRuntimeActions:0};
fs.writeFileSync(file,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({path:file,status:report.status,groups:groups.length,failed:groups.filter(g=>g.status!=='PASS')}));
