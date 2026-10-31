import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {inspect,plan,sealBundle,sha,quota,LIMITS} from './recovery.mjs';
import {clone,stable} from '../heramcu45/schema.mjs';
const b=JSON.parse(await readFile('evidence/herarecover48/pending-source-bundle3.json','utf8')),results=[];
const check=(name,v)=>{assert.ok(v,name);results.push({name,pass:true});};const bad=(name,x)=>{let fail=false;try{fail=inspect(x).errors.length>0;}catch{fail=true;}check(name,fail);};
for(const f of b.files.filter(f=>f.name.endsWith('.bin'))){for(const offset of [0,17,80,Math.floor(f.bytes/2),f.bytes-1]){const x=clone(b),v=x.files.find(v=>v.name===f.name),raw=Buffer.from(v.base64,'base64');raw[offset]^=128;v.base64=raw.toString('base64');v.sha256=sha(raw);bad('raw corruption even with recomputed file and bundle hashes '+f.name.slice(0,12)+' offset '+offset,sealBundle(x.files));}}
for(const count of [0,1,2,3,4,5]){const q=quota({freeBytes:LIMITS.floorBytes+LIMITS.totalBytes,allocatedBytes:count*4096,generationCount:count,requestedBytes:4096});check('generation count '+count+' budget decision',q.allowed===(count<4));}
for(const name of ['HEAD','HEAD.pending']){const x=clone(b),f=x.files.find(f=>f.name===name),raw=Buffer.from('f'.repeat(64)+'\n');f.base64=raw.toString('base64');f.sha256=sha(raw);bad(name+' references missing record',sealBundle(x.files));}
const orphan=clone(b);orphan.files=orphan.files.filter(f=>f.name!=='HEAD'&&f.name!=='HEAD.pending');const o=sealBundle(orphan.files),i=inspect(o);check('no HEAD is explicit orphan not empty journal',i.head===null&&i.recordCount===2&&i.candidates.length===1&&i.candidates[0].classification==='UNACKNOWLEDGED_RECORD');check('orphan selected only with explicit token/digest',plan(o,i.candidates[0].token,o.sha256).classification==='UNACKNOWLEDGED_RECORD');
const repeated=clone(b);repeated.files.push({...clone(b.files[0]),name:'.'});bad('dot entry refused',sealBundle(repeated.files));
const x=clone(b);x.files.find(f=>f.name==='HEAD.pending').base64=x.files.find(f=>f.name==='HEAD').base64;x.files.find(f=>f.name==='HEAD.pending').sha256=x.files.find(f=>f.name==='HEAD').sha256;bad('pending pointer cannot alias head',sealBundle(x.files));
check('host high free does not override aggregate quota',!quota({freeBytes:LIMITS.floorBytes+LIMITS.totalBytes*100,allocatedBytes:LIMITS.totalBytes,generationCount:0,requestedBytes:1}).allowed);
check('host floor exact cannot spend reserve',!quota({freeBytes:LIMITS.floorBytes,allocatedBytes:0,generationCount:0,requestedBytes:0}).allowed);
await writeFile('evidence/herarecover48/corpus1.json',JSON.stringify({status:'PASS',checks:results.length,results,scope:'Pure parser/quota mock/replay; no runtime/SDK or disk fill'},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',checks:results.length}));
