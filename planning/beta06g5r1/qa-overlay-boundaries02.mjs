/** Independent fail-before-writer overlay checks; no listener or flight action. */
import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import{execFileSync}from'node:child_process';
const E='evidence/beta06/generation05-mockcompat01/',manifestPath=path.resolve(process.argv[2]??E+'overlay-pins01.json');
const m=JSON.parse(fs.readFileSync(manifestPath)),scratch=path.resolve(E+'qa-overlay-negative-scratch02');fs.mkdirSync(scratch);const rows=[];
const cases=[
 ['omit-new-module',x=>{delete x.files[Object.keys(x.files)[0]];}],
 ['override-original-pin',x=>{x.files['app/core/compiler.mjs']='0'.repeat(64);}],
 ['unsafe-parent-path',x=>{x.files['pilot/beta06g5r1/../beta06g5/app.mjs']='0'.repeat(64);}],
 ['omit-compiled',x=>{delete x.compiled[Object.keys(x.compiled)[0]];}],
 ['extra-compiled',x=>{x.compiled['pilot/beta06g5/close-index.mjs']={originalSha256:'0'.repeat(64),compiledSha256:'0'.repeat(64)};}],
 ['compiled-sha',x=>{x.compiled[Object.keys(x.compiled)[0]].compiledSha256='0'.repeat(64);}],
 ['source-sha',x=>{x.files[Object.keys(x.files)[0]]='0'.repeat(64);}],
 ['recipe-count',x=>{x.recipe[Object.keys(x.recipe)[0]][0].count++;}],
];
try{
 for(const [name,change]of cases){const bad=structuredClone(m);change(bad);const p=path.join(scratch,name+'.json');fs.writeFileSync(p,JSON.stringify(bad));await test(name,p);}
 const link=path.join(scratch,'linked.json');fs.symlinkSync(manifestPath,link);await test('symlink-manifest',link);
 const huge=path.join(scratch,'huge.json');fs.writeFileSync(huge,JSON.stringify(m)+' '.repeat(1024*1024));await test('oversized-manifest',huge);
 await test('preloaded-original-cache',manifestPath,true);
 fs.writeFileSync(E+'qa-overlay-boundaries02.json',JSON.stringify({status:'PASS_OVERLAY_REJECTS_BEFORE_ANY_APP_WRITER',scope:'SOURCE_MOCK_ONLY_NO_LISTENER_NO_AP',groups:rows.length,rows,removed:[scratch]},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',groups:rows.length,rows}));
}finally{fs.rmSync(scratch,{recursive:true,force:true});}
async function test(name,p,preload=false){
 const out=path.join(scratch,'out-'+name);
 const code=`import fs from 'node:fs';${preload?"await import('./pilot/beta06g5/app.mjs');":''}const {createMockCompatibleG5}=await import('./pilot/beta06g5r1/entry.mjs');let error=null;try{await createMockCompatibleG5({manifestPath:${JSON.stringify(p)},out:${JSON.stringify(out)}});}catch(e){error=e.message;}if(!error||fs.existsSync(${JSON.stringify(out)}))throw Error('FAILED_TO_REFUSE_BEFORE_WRITER:'+String(error));console.log(JSON.stringify({error,outputCreated:false}));`;
 const s=execFileSync(process.execPath,['--input-type=module','-e',code],{cwd:process.cwd(),encoding:'utf8',timeout:15000,maxBuffer:65536});const result=JSON.parse(s.trim());assert(result.error);assert.equal(result.outputCreated,false);rows.push({name,...result});
}
