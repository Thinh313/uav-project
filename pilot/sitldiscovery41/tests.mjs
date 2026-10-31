import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {Observer41,liveWitness} from './observer.mjs';
import {FullFramer,encodeFull,unhex} from '../apstream40/wire.mjs';
const B='evidence/sitldiscovery41/run03/attempt02',s=JSON.parse(await readFile(B+'/session01-snapshot.json','utf8')),manifest=s.context,results=[];
async function check(name,fn){try{await fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false,error:e.stack});}}
const meta=t=>({origin:'OBSERVED_OWNED_SITL',context:manifest,receivedAtMs:t});
const hb=seq=>encodeFull(0,{type:2,autopilot:3,base_mode:1},{system:42,component:1,seq});
function ready(){const o=new Observer41(manifest);o.frames(hb(0),meta(0),0);o.discovery(1);o.frames(encodeFull(148,s.version.fields,{system:42,component:1,seq:1}),meta(2),2);return o;}
for(const [name,mutate]of [['scope',m=>m.scope='PHYSICAL_HERA'],['binary',m=>m.binarySha256='0'.repeat(64)],['PID',m=>m.guestVMInitPid=0],['version',m=>m.flightVersion=0],['commit',m=>m.customCommit='unknown'],['target',m=>m.system=1]])await check('zeroUID exception cannot escape '+name,()=>{const m=structuredClone(manifest);mutate(m);assert.throws(()=>new Observer41(m));});
await check('split reviewed banner before MAVLink retained',()=>{const o=new Observer41(manifest),b=new TextEncoder().encode('\nInit ArduCopter V4.7.1 (dbe79216)\n');o.frames(b.slice(0,15),meta(0),0);o.frames(b.slice(15),meta(1),1);o.frames(hb(0),meta(2),2);assert.equal(o.snapshot(2).disarmedObserved,true);assert.equal(o.snapshot(2).preambleHex,Buffer.from(b).toString('hex'));});
await check('preamble size limit',()=>{const o=new Observer41(manifest);assert.throws(()=>o.frames(new Uint8Array(1025).fill(65),meta(0),0),/UNREVIEWED/);});
await check('wrong banner cannot become firmware evidence',()=>{const o=new Observer41(manifest);o.frames(new TextEncoder().encode('Other vehicle\n'),meta(0),0);assert.throws(()=>o.frames(hb(0),meta(1),1),/WRONG_BOOT_BANNER/);});
await check('zeroUID actually observed stays unauthenticated',()=>{const o=ready(),p=o.witness(2);assert.equal(p.version.fields.uid,'0');assert.equal(p.hardwareIdentityProven,false);assert.equal(p.authenticated,false);assert.equal(p.flightAuthority,false);});
await check('clone/tamper witness cannot restore',()=>{const o=ready(),p=o.witness(2);assert.equal(liveWitness(structuredClone(p),2),false);p.version.fields.flight_sw_version=0;assert.equal(liveWitness(p,2),false);});
await check('loss prevents heartbeat/discovery/read output',()=>{const o=ready(),p=o.witness(2);o.loss();assert.equal(liveWitness(p,2),false);assert.throws(()=>o.heartbeat());assert.throws(()=>o.discovery(2));assert.throws(()=>o.read('MAV_SYSID',2));});
await check('old process context rejected by fresh observer',()=>{const m={...manifest,guestVMInitPid:manifest.guestVMInitPid+1,boot:'new-boot'},o=new Observer41(m);assert.throws(()=>o.frames(hb(0),meta(0),0),/CONTEXT/);assert.equal(o.snapshot(0).liveWitnessAvailable,false);});
await check('armed heartbeat fails closed',()=>{const o=new Observer41(manifest);assert.throws(()=>o.frames(encodeFull(0,{type:2,autopilot:3,base_mode:129},{system:42,component:1}),meta(0),0),/NOT_DISARMED/);});
await check('wrong target cannot satisfy discovery',()=>{const o=new Observer41(manifest);o.frames(hb(0),meta(0),0);o.discovery(1);o.frames(encodeFull(148,s.version.fields,{system:43,component:1}),meta(2),2);assert.equal(o.snapshot(2).version,null);});
await check('wrong build rejects source association',()=>{const o=new Observer41(manifest);o.frames(hb(0),meta(0),0);o.discovery(1);assert.throws(()=>o.frames(encodeFull(148,{...s.version.fields,flight_custom_version:Array(8).fill(0)},{system:42,component:1,seq:1}),meta(2),2),/MISMATCH/);});
await check('guest boot regression revokes local witness',()=>{const o=ready(),p=o.witness(2);o.frames(encodeFull(33,{time_boot_ms:10000},{system:42,component:1,seq:2}),meta(3),3);assert.throws(()=>o.frames(encodeFull(33,{time_boot_ms:100},{system:42,component:1,seq:3}),meta(4),4),/REGRESSION/);assert.equal(liveWitness(p,4),false);});
await check('heartbeat stale prevents witness',()=>{const o=ready(),p=o.witness(2);assert.equal(liveWitness(p,3001),false);});
await check('no automatic second discovery',()=>{const o=ready();assert.throws(()=>o.discovery(3));});
const report={status:results.every(x=>x.pass)?'PASS':'FAIL',checks:results.length,passed:results.filter(x=>x.pass).length,results,scope:'UNIT_FAULTS_WITH_OBSERVED_VERSION_FIXTURE_NO_NETWORK'};await writeFile('evidence/sitldiscovery41/unit1.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:report.status,checks:report.checks,failures:results.filter(x=>!x.pass)}));if(report.status==='FAIL')process.exitCode=1;
