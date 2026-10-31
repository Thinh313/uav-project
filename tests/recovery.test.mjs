import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';import {once} from 'node:events';import {sealRecovery,validateRecoveryRun} from '../app/core/recovery.mjs';import {createAppServer} from '../tools/server.mjs';
// Actual receipt becomes golden only after the simulator campaign has independently sealed it.
let golden;try{golden=JSON.parse(await readFile('evidence/recovery07/run.json','utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
test('Recovery cannot accept an empty or invented 12-trial result',async()=>{await assert.rejects(validateRecoveryRun('{}'));await assert.rejects(validateRecoveryRun(await sealRecovery({format:'aeris-recovery-run',version:1,simulation:true,suite:{},freeze:{},trials:[]})));});
test('Recovery latest API is read-only and rejects missing receipt with runtime disabled',async()=>{const s=createAppServer({recoveryFile:'evidence/recovery07/nonexistent.json'});s.listen(0,'127.0.0.1');await once(s,'listening');try{const url='http://127.0.0.1:'+s.address().port;assert.equal((await fetch(url+'/api/recovery/latest')).status,404);assert.equal((await fetch(url+'/api/recovery/latest',{method:'POST'})).status,405);assert.equal((await fetch(url+'/recovery-ui.mjs')).status,200);}finally{s.close();await once(s,'close');}});
test('Actual twelve-trial receipt validates with historic source and per-attempt records',{skip:!golden},async()=>{assert.equal((await validateRecoveryRun(golden)).trials.length,12);});
for(const [name,mutate]of [
 ['passive CRC corrupt',r=>{const p=r.trials.find(t=>t.kind==='duplex').passive.find(p=>p.id===0);p.hex=p.hex.slice(0,-2)+(p.hex.endsWith('00')?'01':'00');}],
 ['passive fields fabricated',r=>r.trials.find(t=>t.kind==='duplex').passive.find(p=>p.id===253).fields.text='GCS Failsafe fabricated'],
 ['flight command on restore',r=>{const t=r.trials[0],cmd=t.wire.find(w=>w.id===76&&w.phase==='flight');t.wire.push({...cmd,phase:'restore'});}],
 ['digest tamper',r=>r.trials[0].stages.airborne.modeId=0],
 ['duplicate case',r=>r.trials[1]=structuredClone(r.trials[0])],
 ['automatic resume',r=>r.trials[0].stages.reviewed.modeId=3],
 ['fresh heartbeat restores verification',r=>r.trials[0].stages.restored.mission.readbackMatches=true],
 ['missing passive failsafe',r=>r.trials.find(t=>t.kind==='duplex').passive=[]],
 ['mismatched source binding',r=>r.trials[0].caseId='rotated'],
 ['armed reboot',r=>r.trials.find(t=>t.kind==='reboot').stages.beforeReboot.armed=true],
 ['wiped mission accepted',r=>r.trials.find(t=>t.kind==='reboot').stages.mismatch.mission.state='verified'],
 ['recovery emits flight command',r=>{const t=r.trials[0],cmd=t.wire.find(w=>w.id===76&&w.phase==='flight');t.wire.push({...cmd,phase:'recover'});}],
 ['record reused',r=>r.trials[1].records=r.trials[0].records],
 ['wire ID falsified',r=>r.trials[0].wire[0].id=23],
 ['loss still shows live position',r=>r.trials[0].stages.lost.position={relativeAltitude:15}],
 ['recovery record removed',r=>r.trials[0].records=r.trials[0].records.filter(v=>v.summary.origin==='upload')]
])test('Rehashed adversary rejected: '+name,{skip:!golden},async()=>{const r=structuredClone(golden);mutate(r);await assert.rejects(validateRecoveryRun(await sealRecovery(r)));});

import {recoveryPacket} from '../app/core/recovery.mjs';import {encode} from '../services/mavlink.mjs';
test('Browser packet verifier checks actual CRC, IDs and GCS/vehicle bytes',()=>{const bytes=encode(76,{command:176,param2:6},{system:255,component:190}),w={id:76,hex:bytes.toString('hex')};assert.equal(recoveryPacket(w).command,176);assert.equal(recoveryPacket(w).param2,6);assert.equal(recoveryPacket(w).system,255);bytes[10]^=1;assert.throws(()=>recoveryPacket({id:76,hex:bytes.toString('hex')}),/CRC/);assert.throws(()=>recoveryPacket({...w,id:23}),/ID/);const hb=encode(0,{custom_mode:6,base_mode:129,mavlink_version:3},{system:1,component:1});assert.deepEqual(recoveryPacket({id:0,hex:hb.toString('hex')}).heartbeat,{custom_mode:6,base_mode:129});});
