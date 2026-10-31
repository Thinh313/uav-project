import assert from'node:assert/strict';import{readFile,writeFile}from'node:fs/promises';import{createHash}from'node:crypto';import{parse43}from'./replay.mjs';import{FullFramer,encodeFull,unhex,hex}from'../apstream40/wire.mjs';import{digest}from'./profile.mjs';
const text=await readFile('evidence/preflight43/run01/session01-raw.jsonl','utf8'),rows=text.trimEnd().split('\n').map(JSON.parse),results=[];
const hash=x=>createHash('sha256').update(x).digest('hex');
function chain(rows){let prev='0'.repeat(64);return rows.map((r,k)=>{const{sha256,n,prev:old,...p}=r,obj={n:k+1,prev,...p},sha=hash(JSON.stringify(obj));prev=sha;return JSON.stringify({...obj,sha256:sha})+'\n';}).join('');}
function bite(name,fn){assert.throws(fn,undefined,name);results.push({name,rejected:true,origin:'OFFLINE_NO_NETWORK'});}
function fresh(){return structuredClone(rows);}
function mutatePV(r,name,change){let changed=false;for(const row of r){if(row.kind!=='RX')continue;const bytes=unhex(row.rawHex);for(let k=0;k<bytes.length-12;k++){if(![253,254].includes(bytes[k]))continue;const v2=bytes[k]===253,h=v2?10:6,len=bytes[k+1],n=h+len+2;if(k+n>bytes.length)continue;const id=v2?bytes[k+7]+bytes[k+8]*256+bytes[k+9]*65536:bytes[k+5];if(id!==22)continue;const packet=bytes.slice(k,k+n);let f;try{f=new FullFramer().push(packet,0)[0];}catch{continue;}if(f?.fields.param_id!==name)continue;const fields=structuredClone(f.fields);change(fields);const b=encodeFull(22,fields,{system:f.system,component:f.component,seq:f.seq,version:f.version});assert.equal(b.length,n);bytes.set(b,k);row.rawHex=hex(bytes);changed=true;break;}if(changed)break;}assert.ok(changed,'targetPVfound');return r;}
bite('corrupt byte without hashchain update',()=>{const r=fresh();r.find(x=>x.kind==='RX').rawHex='00';parse43(r.map(x=>JSON.stringify(x)+'\n').join(''));});
bite('truncatedjournal nofinal newline',()=>parse43(text.slice(0,-1)));
bite('missingwriterreturn despite allraw data',()=>{const r=fresh(),i=r.findIndex(x=>x.kind==='TX_WRITE_RETURN');r.splice(i,1);parse43(chain(r));});
bite('missingclosedwriter cannotPASS',()=>parse43(chain(rows.slice(0,-1))));
bite('forged READY at staleassessment rejected with rehashedchain',()=>{const r=fresh(),a=r.find(x=>x.kind==='ASSESSMENT'&&x.assessment.state==='UNKNOWN');a.assessment.state='READY_SCOPED_READONLY';a.assessment.reasons=[];parse43(chain(r));});
bite('complete-lookingcohort with missing final response rejected',()=>{const r=fresh(),i=r.findIndex(x=>x.kind==='RX'&&x.rawHex.includes(Buffer.from('GPS_HDOP_GOOD').toString('hex')));assert.ok(i>0);r.splice(i,1);parse43(chain(r));});
bite('actualparameter changedtype REAL32 cannotPASS',()=>parse43(chain(mutatePV(fresh(),'MAV_SYSID',p=>p.param_type=9))));
bite('cohort count discrepancy cannotPASS',()=>parse43(chain(mutatePV(fresh(),'MAV_GCS_SYSID',p=>p.param_count++))));
bite('wrong parameter index cannotPASS',()=>parse43(chain(mutatePV(fresh(),'MAV_SYSID',p=>p.param_index=p.param_count))));
bite('unsafeARMING_SKIPCHK altered to skip checks cannotPASS',()=>parse43(chain(mutatePV(fresh(),'ARMING_SKIPCHK',p=>p.param_value=1))));
bite('newdeclaredpolicy without matching assessment rejected',()=>{const r=fresh();r[0].profile.expected.FENCE_RADIUS=31;r[0].profile.revision='forgedprofile31';parse43(chain(r));});
bite('changed session cannot keep oldintent binding',()=>{const r=fresh();r[0].context.session='other-session';parse43(chain(r));});
await writeFile('evidence/preflight43/bites1.json',JSON.stringify({status:'PASS',total:results.length,passed:results.length,results,baseRawSha256:hash(text),scope:'Rechained semantic mutations plus raw integrity tests; not remoteauthentication/physicalattestation'},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',bites:results.length}));
