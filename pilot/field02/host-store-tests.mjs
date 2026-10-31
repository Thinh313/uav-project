import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {Store01 as OldStore} from '../field01/evidence/store01.mjs';
import {Store01} from './evidence/store01.mjs';
import {createField02} from './app.mjs';
const out=process.argv[2];assert(/^evidence\/field02\/host-store[0-9]+$/.test(out));
await fs.mkdir(out,{recursive:false});const rows=[];const check=id=>rows.push({id,pass:true});
const seed=async store=>{for(let n=0;n<8;n++)await store.append('TEST_BOUNDED_RECORD',{n,text:'x'.repeat(20000)});};
let old,own,app;
try {
 old=await OldStore({root:out+'/old'});await seed(old);assert.throws(()=>old.records(),/JSON_SIZE/);check('old_aggregate_limit_defect_reproduced');await old.close();old=null;
 own=await Store01({root:out+'/own'});await seed(own);let r=own.records();assert.equal(r.length,8);assert(JSON.stringify(r).length>131072);check('valid_aggregate_above_128k_reads');
 const before=await fs.readFile(out+'/own/journal.jsonl');r[0].data.text='mutated';r.pop();assert.equal(own.records()[0].data.text.length,20000);assert.equal(own.records().length,8);check('each_record_remains_deep_copy');
 await assert.rejects(own.append('TEST_OVERSIZE',{text:'x'.repeat(131073)}),/JSON_SIZE/);assert.equal(own.records().length,8);assert((await fs.readFile(out+'/own/journal.jsonl')).equals(before));check('single_record_bound_and_original_bytes_preserved');
 await own.close();own=await Store01({root:out+'/own'});assert.equal(own.snapshot().poisoned,false);assert.equal(own.records().length,8);assert((await fs.readFile(out+'/own/journal.jsonl')).equals(before));check('restart_chain_verified_without_rewrite');await own.close();own=null;
 app=await createField02({out:out+'/http01',port:8892,mediaPort:8893});await app.listen();await seed(app.store);let response=await fetch('http://127.0.0.1:8892/api/state');assert.equal(response.status,200);const state=await response.json();assert.equal(state.ok,true);assert.equal(state.authorityRestored,false);assert.equal(state.store.recordCount,8);check('http_state_after_large_journal_is200_no_authority');await app.close('STORE_MOCK_TEST');app=null;
 app=await createField02({out:out+'/http02',workspaceRoot:out+'/http01/workspace',port:8892,mediaPort:8893});await app.listen();response=await fetch('http://127.0.0.1:8892/api/state');assert.equal(response.status,200);assert.equal((await response.json()).store.poisoned,false);check('host_restart_reads_large_journal_without_global_limit_relaxation');
 const source=await fs.readFile('pilot/field01/evidence/store.mjs','utf8');const fork=await fs.readFile('pilot/field02/evidence/store.mjs','utf8');assert.equal(fork.slice(fork.indexOf("import * as fs")),source.slice(source.indexOf("import * as fs")).replace('records:()=>copy(records)','records:()=>records.map(copy)'));check('production_fork_only_functional_change_records_projection');
} catch(e) {rows.push({id:'unexpected',pass:false,error:e.stack});} finally {
 await old?.close();await own?.close();await app?.close('STORE_MOCK_TEST');const report={status:rows.every(x=>x.pass)?'PASS':'FAIL',rows,scope:'LOCAL_HTTP_MOCK_NO_ANDROID_NO_SITL',at:new Date().toISOString(),sourceSha256:createHash('sha256').update(await fs.readFile('pilot/field02/evidence/store.mjs')).digest('hex')};await fs.writeFile(out+'/results.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));if(report.status==='FAIL')process.exitCode=1;
}
