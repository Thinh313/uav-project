import fs from'node:fs';import {execFileSync}from'node:child_process';import {createHash}from'node:crypto';import assert from'node:assert/strict';import{validateCapsule44}from'./assets/workflow/capsule.mjs';
const E='evidence/native86',sha=b=>createHash('sha256').update(b).digest('hex');
const data=JSON.parse(execFileSync('python3',['-c',`import tarfile,json,base64,zipfile
from pathlib import Path
files={};archives=[]
for p in Path('evidence/native86').glob('android86-*.tar'):
 with tarfile.open(p)as t:
  for m in t.getmembers():
   if m.isfile()and m.name.endswith('.bin'):
    b=t.extractfile(m).read();files[Path(m.name).name]=base64.b64encode(b).decode()
for p in Path('evidence/native86').glob('android86-workspace-export*.zip'):
 with zipfile.ZipFile(p)as z:archives.append({'path':str(p),'files':{n:base64.b64encode(z.read(n)).decode()for n in z.namelist()}})
print(json.dumps({'files':files,'archives':archives}))`],{maxBuffer:16*1024*1024}).toString());
let count=0,negative=0;const phases=new Set(),rows=[];
for(const[name,encoded]of Object.entries(data.files)){
 const b=Buffer.from(encoded,'base64');let i=0,at=0;const headers=[];for(;i<6;i++){const end=b.indexOf(10,at);assert(end>=0);headers.push(b.subarray(at,end).toString());at=end+1;}const body=b.subarray(at);assert.equal(headers[0],'AERISWORKSPACE33');assert.equal(Number(headers[4]),body.length);assert.equal(headers[5],'1');assert.equal(headers[3],sha(body));assert(name.endsWith(sha(b)+'.bin'));const cap=await validateCapsule44(body.toString());assert.equal(cap.operational,false);assert.equal(cap.authorityRestorable,false);if(cap.journey.current)phases.add(cap.journey.current.phase);count++;rows.push({name,revision:Number(headers[1]),previous:headers[2],sha256:sha(b),phase:cap.journey.current?.phase??'DRAFT'});
 if(count===1){for(const key of['operational','authorityRestorable']){const bad=structuredClone(cap);bad[key]=true;await assert.rejects(()=>validateCapsule44(JSON.stringify(bad)));negative++;}}
}
function checkArchive(files){const manifest=files.MANIFEST.toString().trimEnd().split('\n');assert.equal(manifest[0],'AERISARCHIVE83');assert.equal(manifest[2],'authority=false');assert.equal(files.HEAD.toString().trim(),manifest[1]);assert.equal(manifest.length,Object.keys(files).length+2);for(const line of manifest.slice(3)){const[n,size,h]=line.split(' ');assert.equal(files[n].length,Number(size));assert.equal(sha(files[n]),h);}}
for(const a of data.archives){const files=Object.fromEntries(Object.entries(a.files).map(([n,b])=>[n,Buffer.from(b,'base64')]));checkArchive(files);const bad=Buffer.from(files.HEAD);bad[0]^=1;assert.throws(()=>checkArchive({...files,HEAD:bad}));negative++;}
for(const row of rows){if(row.previous==='ROOT'){assert.equal(row.revision,1);continue;}const prev=rows.find(r=>r.sha256===row.previous);assert(prev);assert.equal(prev.revision,row.revision-1);}
assert(phases.has('COMPLETED_MOCK')&&phases.has('RUNNING_MOCK')&&phases.has('INTERRUPTED_RESTART'));
const draft=JSON.parse(fs.readFileSync(E+'/android86-draft-before.json'));const c=JSON.parse(Object.values(draft.journals)[0].latest.body);assert.equal(c.journey.draft.form.name,'Khao_sat_NATIVE86');assert.equal(c.journey.draft.form.altitude,'31');assert.equal(c.journey.draft.form.speed,'1.1');
const result={status:'PASS_CAPTURED_ANDROID_SHA_AND_SEMANTIC_REPLAY',uniqueRecords:count,archives:data.archives.map(a=>a.path),negativeControls:negative,phases:[...phases],records:rows,scope:'Captured Android mock journal only. No flight execution or physical media evidence.'};fs.writeFileSync(E+'/captured-replay02.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:result.status,uniqueRecords:count,archives:data.archives.length,negativeControls:negative,phases:[...phases]}));
