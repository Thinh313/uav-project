/** Independent synthetic quota challenges. No runtime, listener or real command execution. */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {ROOT,E,POLICY,policySha256,history,scan,decide} from '../../pilot/beta06g7/quota.mjs';

const output=process.argv[2];
assert.match(output??'',/^qa-quota-independent-[a-z0-9-]+\.json$/);
const target=path.join(ROOT,E,output);assert(!fs.existsSync(target));
const h=history(), rows=[], sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['pilot/beta06g7/quota.mjs','pilot/beta06g7/quota-policy.json'];
const sourceHashes=Object.fromEntries(sources.map(p=>[p,sha(fs.readFileSync(path.join(ROOT,p)))]));
const record=async(name,fn)=>{try{await fn();rows.push({name,status:'PASS'});}catch(e){rows.push({name,status:'FAIL',error:String(e.message).slice(0,500)});}};
const usage=()=>({counts:Object.fromEntries(Object.keys(POLICY.categories).map(k=>[k,{bytes:0,entries:0}])),apRuns:{},capacity:{sitlRequests:0,hostProcesses:0},newEntries:0,newBytes:0,finishedAt:Date.now(),policySha256,historySha256:POLICY.history.sha256});
const admission=u=>decide(u,{phase:'guard',remaining_ap:4,remaining_hosts:2,closed_runs:[],freeBytes:32*2**30});
await record('exact_integer_envelope_and_entry_geometry',()=>{
 const bytes=Object.entries(POLICY.categories).reduce((n,[k,v])=>n+(k==='ap'?v.slots*v.bytesPerSlot:v.bytes),0);
 const entries=Object.entries(POLICY.categories).reduce((n,[k,v])=>n+(k==='ap'?v.slots*v.entriesPerSlot:v.entries),0);
 assert.equal(bytes,2228*2**20);assert.equal(bytes+POLICY.active.closureBytes,2484*2**20);
 assert.equal(POLICY.categories.native.bytes,112*2**20);assert.equal(POLICY.categories.native.closureBytes,16*2**20);
 assert.equal(POLICY.categories.hostOther.bytes,80*2**20);assert.equal(entries,8192);
 assert.equal(POLICY.active.closureEntries,412);assert.equal(8192-POLICY.active.closureEntries,7780);
 assert.equal(4*1536+2048,8192);assert.equal(427*3+64+128+63,1536);
 assert.equal(POLICY.optionalExports.bytes,0);assert.equal(POLICY.optionalExports.entries,0);
});
await record('all_remaining_slots_reserved_even_with_reported_closed_runs',()=>{
 const u=usage();const a=admission(u);const b=decide(u,{remaining_ap:0,remaining_hosts:0,closed_runs:['s'+'1'.repeat(20)],freeBytes:32*2**30});
 assert.equal(a.remainingReservations.bytes,b.remainingReservations.bytes);assert.equal(a.remainingReservations.entries,b.remainingReservations.entries);
 assert.equal(a.remainingReservations.entries,8192);
});
await record('each_category_one_byte_and_one_entry_over_refused',()=>{
 for(const[k,c]of Object.entries(POLICY.categories))for(const key of ['bytes','entries']){
  const u=usage(),cap=k==='ap'?c.slots*(key==='bytes'?c.bytesPerSlot:c.entriesPerSlot):c[key];u.counts[k][key]=cap+1;
  assert.throws(()=>admission(u),/QUOTA|RESERVATION/);
 }
});
await record('normal_empty_entries_cannot_consume_final_proof_or_host_closure_reserve',()=>{
 for(const k of ['sourceQA','hostOther']){
  const c=POLICY.categories[k],u=usage();u.counts[k].entries=c.entries-c.closureEntries;
  u.newEntries=u.counts[k].entries;assert.equal(admission(u).status,'ADMITTED');
  u.counts[k].entries++;u.newEntries++;assert.throws(()=>admission(u),/CATEGORY_QUOTA/);
  assert.throws(()=>decide(u,{phase:'before-connect',closure:true,freeBytes:32*2**30}),/CATEGORY_QUOTA/);
  assert.equal(decide(u,{phase:'closure',closure:true,freeBytes:32*2**30}).status,'ADMITTED');
 }
});
await record('ap_capture_state_slot_and_fifth_run_refused',()=>{
 for(const[key,max]of [['bytes',90*2**20],['entries',1536],['normalEntries',1473],['stateEntries',128],['captureResults',427]]){
  const u=usage();u.apRuns['s'+'1'.repeat(20)]={bytes:0,entries:0,stateEntries:0,captureResults:0,[key]:max+1};assert.throws(()=>admission(u),/AP_SLOT_QUOTA/);
 }
 const u=usage();for(let i=0;i<5;i++)u.apRuns['s'+String(i).repeat(20)]={bytes:0,entries:0,stateEntries:0,captureResults:0};assert.throws(()=>admission(u),/ACTIVE_ENTRY_QUOTA/);
});
await record('physical_runtime_floor_one_byte_short_refused',()=>{
 assert.throws(()=>decide(usage(),{freeBytes:POLICY.physical.runtimeBytes-1}),/PHYSICAL_FLOOR_RESERVATION/);
 assert.equal(decide(usage(),{freeBytes:POLICY.physical.runtimeBytes}).status,'ADMITTED');
});

// Model only the filesystem APIs used by scan; immutable inventory bytes remain real.
const original={opendir:fsp.opendir,lstat:fsp.lstat,readFile:fsp.readFile};
async function virtual(change=()=>{},options={}){
 const entries=new Map(Object.entries(h.entries).map(([p,r])=>[p,{...r}]));
 entries.set(E.slice(0,-1),{kind:'DIRECTORY',mode:'0o755',bytes:0,mtimeNs:'0',sha256:null});
 const overrideBodies=new Map();change(entries,overrideBodies);
 const children=new Map();for(const[p]of entries){const parent=path.posix.dirname(p);if(!children.has(parent))children.set(parent,[]);children.get(parent).push(path.posix.basename(p));}
 const root='/virtual-g7-independent';
 fsp.opendir=async p=>{
  const rel=path.relative(root,p);assert(children.has(rel)||entries.get(rel)?.kind==='DIRECTORY','virtual directory missing '+rel);
  return{async *[Symbol.asyncIterator](){for(const name of children.get(rel)??[])yield{name};},async close(){}};
 };
 fsp.lstat=async p=>{const r=entries.get(path.relative(root,p));assert(r);return{isSymbolicLink:()=>r.kind==='SYMLINK',isFile:()=>r.kind==='REGULAR_FILE',isDirectory:()=>r.kind==='DIRECTORY',size:BigInt(r.bytes),mode:BigInt(parseInt(r.mode.slice(2),8)),mtimeNs:BigInt(r.mtimeNs)};};
 fsp.readFile=async p=>{const rel=path.relative(root,p);if(overrideBodies.has(rel))return overrideBodies.get(rel);return original.readFile(path.join(ROOT,rel));};
 try{return await scan({root,...options});}finally{Object.assign(fsp,original);}
}
await record('retained_history_above_old4096_and_empty_new_entries_counted',async()=>{
 const u=await virtual(m=>{for(let i=0;i<10;i++)m.set(E+'empty-'+i,{kind:'REGULAR_FILE',mode:'0o600',bytes:0,sha256:sha(''),mtimeNs:'0'});m.set(E+'empty-dir',{kind:'DIRECTORY',mode:'0o700',bytes:0,sha256:null,mtimeNs:'0'});});
 assert.equal(u.historicalEntries,4133);assert.equal(u.historicalBytes,135756685);assert.equal(u.newEntries,11);assert.equal(u.newBytes,0);assert(u.slices>0);assert.equal(admission(u).status,'ADMITTED');
});
await record('only_exact_cleanup_paths_receive_ap_closure_entry_credit',async()=>{
 const run='s'+'9'.repeat(20),base=E+'flight/runs/'+run;
 const u=await virtual((m,bodies)=>{
  for(const p of [E+'flight',E+'flight/runs',base,base+'/diagnostics',base+'/ap-state'])m.set(p,{kind:'DIRECTORY',mode:'0o700',bytes:0,sha256:null,mtimeNs:'0'});
  for(const p of ['closure.json','diagnostics/closure-before-stdout.bin','diagnostics/closure-before-result.json','diagnostics/closure-before-FAKE','ap-state/closureXjson','diagnostics/recovered-label-FAKE'])m.set(base+'/'+p,{kind:'REGULAR_FILE',mode:'0o600',bytes:0,sha256:sha(''),mtimeNs:'0'});
  const request=Buffer.from(JSON.stringify({run,mode:'sitl',source:'HOST_NODE_GCS_SIM_ONLY'}));m.set(base+'/request.json',{kind:'REGULAR_FILE',mode:'0o600',bytes:request.length,sha256:sha(request),mtimeNs:'0'});bodies.set(base+'/request.json',request);
 });
 assert.equal(u.apRuns[run].entries,10);assert.equal(u.apRuns[run].normalEntries,7);
});
await record('old_unknown_addition_deletion_metadata_corruption_refused',async()=>{
 const file=Object.keys(h.entries).find(p=>h.entries[p].kind==='REGULAR_FILE');
 await assert.rejects(()=>virtual(m=>m.set('evidence/beta06/unknown-new',{...h.entries[file]})),/OUT_OF_SCOPE_HISTORY_ADDITION/);
 await assert.rejects(()=>virtual(m=>m.delete(file)),/HISTORY_DELETION_OR_UNSEEN_ENTRY/);
 for(const update of [{bytes:h.entries[file].bytes+1},{mode:'0o777'},{mtimeNs:String(BigInt(h.entries[file].mtimeNs)+1n)}])await assert.rejects(()=>virtual(m=>m.set(file,{...m.get(file),...update})),/HISTORY_METADATA_DRIFT/);
});
await record('same_size_preserved_metadata_sha_corruption_refused',async()=>{
 const file=Object.keys(h.entries).find(p=>h.entries[p].kind==='REGULAR_FILE'&&h.entries[p].bytes>0);
 await assert.rejects(()=>virtual((m,b)=>b.set(file,Buffer.alloc(m.get(file).bytes,0x7e)),{verifyHashes:true}),/HISTORY_SHA_DRIFT/);
});
await record('new_symlink_special_entry_and_depth_refused',async()=>{
 for(const kind of ['SYMLINK','SPECIAL'])await assert.rejects(()=>virtual(m=>m.set(E+'bad',{kind,mode:'0o600',bytes:0,sha256:null,mtimeNs:'0'})),/QUOTA_REGULAR_FILES_ONLY/);
 await assert.rejects(()=>virtual(m=>{let p=E.slice(0,-1);for(let i=0;i<22;i++){p+='/deep';m.set(p,{kind:'DIRECTORY',mode:'0o700',bytes:0,mtimeNs:'0',sha256:null});}}),/BOUNDED_SCAN_DEPTH/);
});
await record('8193_empty_new_entries_refused_without_disk_fill',async()=>{
 await assert.rejects(()=>virtual(m=>{for(let i=0;i<8193;i++)m.set(E+'empty-'+i,{kind:'REGULAR_FILE',mode:'0o600',bytes:0,mtimeNs:'0',sha256:sha('')});}),/BOUNDED_SCAN_ENTRY_OVERFLOW/);
});
await record('runtime_scan_stale_deadline_refused',async()=>{
 const old=POLICY.scanner.cycleMs;try{POLICY.scanner.cycleMs=-1;await assert.rejects(()=>virtual(),/QUOTA_SCAN_STALE_DEADLINE/);}finally{POLICY.scanner.cycleMs=old;}
});
for(const[p,h]of Object.entries(sourceHashes))assert.equal(sha(fs.readFileSync(path.join(ROOT,p))),h,'source changed during independent test');
const report={at:new Date().toISOString(),status:rows.every(r=>r.status==='PASS')?'PASS_SOURCE_MOCK_ONLY':'FAIL_SOURCE_MOCK_ONLY',sourceHashes,policySha256,groups:rows,independentGroups:rows.length,virtualFilesystemOnly:true,historyRetained:true,actualRuntimeActions:0,noAPPhysicsOrAndroidAcceptance:true};
fs.writeFileSync(target,JSON.stringify(report,null,2)+'\n',{flag:'wx',mode:0o600});console.log(JSON.stringify({path:target,status:report.status,groups:rows.length,failed:rows.filter(r=>r.status!=='PASS')}));
