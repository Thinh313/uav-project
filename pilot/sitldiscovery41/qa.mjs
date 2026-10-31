import assert from 'node:assert/strict';
import {readFile,writeFile,statfs,mkdir} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {connect41} from './client.mjs';
import {NAMES,liveWitness} from './observer.mjs';
import {APStream40} from '../apstream40/adapter.mjs';
import {FullFramer,hex,unhex,encodeFull} from '../apstream40/wire.mjs';
import {contract} from '../firmware38/contract.mjs';
const ROOT='evidence/sitldiscovery41/run03',E=ROOT+'/attempt02',exec=promisify(execFile),results=[];let clients=[];await mkdir(E,{recursive:true});
const put=async(n,o)=>{let path=E+'/'+n,k=2;const {existsSync}=await import('node:fs');while(existsSync(path))path=E+'/'+n.replace(/\.json$/,`-attempt${k++}.json`);return writeFile(path,JSON.stringify(o,null,2)+'\n',{flag:'wx'});};
const check=(name,fn)=>{fn();results.push({name,pass:true});};
const manifest=async (suffix)=>{const p=suffix==='before-reboot'?'inspect-before-reboot-attempt02.json':'inspect-after-reboot-attempt02.json';const info=JSON.parse(await readFile(ROOT+'/'+p,'utf8'));return {scope:'OWNED_DISARMED_REAL_SITL_ONLY',binarySha256:'011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482',flightVersion:67568127,customCommit:'dbe79216',containerId:info.Id,guestVMInitPid:info.State.Pid,startedAt:info.State.StartedAt,system:42,component:1,session:suffix,boot:info.State.StartedAt,clockEpoch:suffix};};
async function collect(m,label){const c=await connect41(m,E+'/'+label+'-raw.jsonl');clients.push(c);await c.send(c.observer.heartbeat());await c.wait(s=>s.disarmedObserved,15000);await c.send(c.observer.discovery(c.now()));await c.wait(s=>!!s.version,1800);for(const name of NAMES){await c.send(c.observer.read(name,c.now()));await c.wait(s=>Object.hasOwn(s.parameters,name),1800);}await c.flush();const snapshot=c.observer.snapshot(c.now());await put(label+'-snapshot.json',snapshot);return c;}
try{
 const fs=await statfs('.');assert.ok(fs.bavail*fs.bsize>21.5*2**30);
 await exec('python3',['-B','pilot/sitldiscovery41/lifecycle.py','inspect','run03','before-reboot-attempt02'],{timeout:15000});
 const m=await manifest('before-reboot'),a=await collect(m,'session01'),p=a.observer.witness(a.now());
 check('actual version4.7.1 builddbe +owned process',()=>{const s=a.observer.snapshot(a.now());assert.equal(s.version.fields.flight_sw_version,67568127);assert.equal(String.fromCharCode(...s.version.fields.flight_custom_version),'dbe79216');assert.equal(s.version.fields.uid,'0');assert.equal(Object.keys(s.parameters).length,8);assert.equal(s.disarmedObserved,true);assert.equal(liveWitness(p,a.now()),true);});
 // Preserve AP40 incompatibility with exact actual version bytes, no live reuse of mock buffers.
 const s=a.observer.snapshot(a.now()),target={vehicle:'Owned-SITL41-not-Hera',system:42,component:1,session:'projection41',boot:m.boot,link:'projection-only'},cc=contract(target,'projection41');cc.expected={flight_sw_version:s.version.fields.flight_sw_version,flight_custom_version:s.version.fields.flight_custom_version,vendor_id:s.version.fields.vendor_id,product_id:s.version.fields.product_id,board_version:s.version.fields.board_version,uid:s.version.fields.uid};
 const projection=new APStream40(cc);const firstHB=s.events.find(x=>x.id===0&&x.label==='ACCEPTED');await projection.receive(unhex(firstHB.rawHex),{origin:'MOCK_REPLAY',target,epoch:'projection41',receivedAtMs:0},0);await projection.startDiscovery(1);
 const vf=unhex(s.version.rawHex); // retain original AP sequence; all earlier AP packets must be projected first to avoid sequence ambiguities.
 const before=s.events.slice(0,s.events.findIndex(x=>x.rawHex===s.version.rawHex));for(const e of before.slice(1))try{await projection.receive(unhex(e.rawHex),{origin:'MOCK_REPLAY',target,epoch:'projection41',receivedAtMs:2},2);}catch{}
 let projectionError=null;try{await projection.receive(vf,{origin:'MOCK_REPLAY',target,epoch:'projection41',receivedAtMs:3},3);}catch(e){projectionError=e.message;}
 const ps=projection.snapshot(3);await put('ap40-actual-byte-projection.json',{scope:'OFFLINE_PROJECTION_OF_OBSERVED_REAL_BYTES_NO_NETWORK_SEND',actualRawVersionHex:s.version.rawHex,expectedReviewedIdentity:cc.expected,error:projectionError,snapshot:ps});
 check('legacy AP40 actually refuses zeroUID',()=>{assert.equal(ps.phase,'INVALIDATED');assert.match(ps.reason,/unknown UID/);});
 await a.close();check('actual TCP close revokes prior witness',()=>{assert.equal(liveWitness(p,a.now()),false);assert.throws(()=>a.observer.discovery(a.now()));});
 const b=await collect({...m,session:'manual-reconnect',clockEpoch:'manual-reconnect'},'session02'),q=b.observer.witness(b.now());
 check('manual new connection rediscovers and rereads',()=>{assert.equal(Object.keys(b.observer.snapshot(b.now()).parameters).length,8);assert.equal(liveWitness(q,b.now()),true);assert.equal(liveWitness(p,a.now()),false);});
 // Capture deliberate wrong-sender version separately, never send this injection to AP.
 const snap=b.observer.snapshot(b.now()),decoded=new FullFramer().push(unhex(snap.version.rawHex),0,0)[0],foreign=encodeFull(148,decoded.fields,{system:43,component:1,seq:decoded.seq});
 const beforeV=canonicalVersion(snap);b.observer.frames(foreign,{origin:'OBSERVED_OWNED_SITL',context:{...m,session:'manual-reconnect',clockEpoch:'manual-reconnect'},receivedAtMs:b.now()},b.now());
 await put('wrong-target-injection.json',{origin:'FAULT_INJECTION_AT_PARSER_SEAM_NOT_AP_NETWORK',rawHex:hex(foreign),beforeVersion:beforeV,afterVersion:canonicalVersion(b.observer.snapshot(b.now())),witnessStillValid:liveWitness(q,b.now())});
 check('wrong sender cannot replace observed firmware',()=>assert.equal(canonicalVersion(b.observer.snapshot(b.now())),beforeV));
 await exec('python3',['-B','pilot/sitldiscovery41/lifecycle.py','restart','run03'],{timeout:20000});await b.wait(()=>b.isClosed(),5000).catch(e=>{if(!b.isClosed())throw e;});
 check('actual AP restart closes old link and revokes witness',()=>{assert.equal(b.isClosed(),true);assert.equal(liveWitness(q,b.now()),false);});await b.close();
 await exec('python3',['-B','pilot/sitldiscovery41/lifecycle.py','inspect','run03','after-reboot-attempt02'],{timeout:15000});const next=await manifest('after-reboot'),c=await collect(next,'session03');
 check('fresh process PID/start with same binary',()=>{assert.notEqual(next.guestVMInitPid,m.guestVMInitPid);assert.notEqual(next.startedAt,m.startedAt);assert.equal(next.containerId,m.containerId);assert.equal(next.binarySha256,m.binarySha256);assert.equal(Object.keys(c.observer.snapshot(c.now()).parameters).length,8);});await c.close();
 await put('qa.json',{status:'PASS_SCOPED_REAL_SITL',results,actualNetworkSessions:3,parameterReads:24,sourceBinaryAssociation:'LOCAL_OWNED_BINARY_VERSION_AND_CAPTURED_METADATA',sourceBuildReproduced:false,noFlightCommands:true,SDK_Hera:'NOT_CHECKED'});console.log(JSON.stringify({status:'PASS_SCOPED_REAL_SITL',checks:results.length}));
}catch(e){await put('qa-failure.json',{status:'FAIL',error:e.stack,passed:results});console.error(e.stack);process.exitCode=1;}
finally{for(const c of clients)try{await c.close();}catch{} }
function canonicalVersion(s){return JSON.stringify(s.version?.fields??null);}
