import fs from'node:fs';import os from'node:os';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';import{checkWorkspaceLineage}from'../../pilot/beta06g5/workspace-lineage.mjs';
const root=fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()),'codex-tmp-g5-lineage-20261022-')),owned=root+'/evidence/beta06/generation05',workspace=owned+'/workspace01',sha=b=>createHash('sha256').update(b).digest('hex'),checks=[];fs.mkdirSync(workspace,{recursive:true});
try{
 const files=[];for(let i=0;i<20;i++){const name=i===0?'journal.jsonl':'blob-'+i,b=Buffer.alloc(i===0?870221-19:1,120),copy='evidence/beta06/generation05/workspace01/'+name;fs.writeFileSync(root+'/'+copy,b);files.push({copy,bytes:b.length,sha256:sha(b)});}fs.writeFileSync(owned+'/workspace-copy01.json',JSON.stringify({mode:'EXACT_CLOSED_DATA_FORK_NOT_PROJECT_COPY',fileCount:20,bytes:870221,files}));
 checkWorkspaceLineage(root,workspace);assert.equal(JSON.parse(fs.readFileSync(owned+'/workspace-first-writer01.json')).firstWriterVerifiedBeforeStoreLock,true);checks.push('exact20file870221B_firstwriter_claim_beforeStorelock');
 fs.appendFileSync(workspace+'/journal.jsonl','new authorized WAL suffix');checkWorkspaceLineage(root,workspace);checks.push('managed_restart_allows_only_original_journal_prefix_with_exact_original_blobs');
 fs.writeFileSync(workspace+'/writer.lock','owned');assert.throws(()=>checkWorkspaceLineage(root,workspace),/PREEXISTING_WORKSPACE_WRITER/);fs.unlinkSync(workspace+'/writer.lock');checks.push('no_existing_lock_deleted_or_reset');
 fs.writeFileSync(workspace+'/blob-1','y');assert.throws(()=>checkWorkspaceLineage(root,workspace),/PREFIX_DRIFT/);checks.push('original_blob_drift_refuses_restart');
 console.log(JSON.stringify({status:'PASS_SOURCE_MOCK_FILES_ONLY',checks,temporaryRemoved:root}));
}finally{fs.rmSync(root,{recursive:true,force:true});}
