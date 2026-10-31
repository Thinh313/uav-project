import {validateBenchmarkSuite,validateBenchmarkFreeze,sealBenchmark,MAX_BENCH_BYTES} from './benchmark.mjs';
import {validateExecutionRecord,digest,stable} from './execution-record.mjs';
export const RECOVERY_KINDS=Object.freeze(['inbound','tcp','duplex','reboot']);
export const sealRecovery=sealBenchmark;
const fail=m=>{throw Error('Recovery: '+m);},same=(a,b)=>stable(a)===stable(b),time=t=>typeof t==='string'&&Number.isFinite(Date.parse(t));
const fresh=s=>s?.connected===true&&Number.isFinite(s.heartbeatAgeMs)&&s.heartbeatAgeMs>=0&&s.heartbeatAgeMs<=3000;
export function recoveryPacket(w){
 if(typeof w.hex!=='string'||!/^(?:[a-f0-9]{2})+$/.test(w.hex))fail('packet hex');const b=Uint8Array.from(w.hex.match(/../g),h=>parseInt(h,16)),v=b[0],header=v===253?10:v===254?6:0;if(!header||b.length!==header+b[1]+2||v===253&&b[2]!==0)fail('packet framing');const d=new DataView(b.buffer),id=v===253?b[7]+b[8]*256+b[9]*65536:b[5],extra={0:50,20:214,43:132,44:221,47:153,51:196,73:38,76:152,245:130,253:83}[id];if(id!==w.id||extra===undefined)fail('packet ID');let crc=65535;for(const byte of [...b.slice(1,-2),extra]){let t=byte^(crc&255);t^=(t<<4)&255;crc=((crc>>8)^(t<<8)^(t<<3)^(t>>4))&65535;}if(crc!==d.getUint16(b.length-2,true))fail('packet CRC');
 const payload=new Uint8Array(255);payload.set(b.slice(header,-2));const f=new DataView(payload.buffer),system=b[v===253?5:3],component=b[v===253?6:4],fields={id,system,component};
 if(id===76){fields.command=f.getUint16(28,true);fields.param2=f.getFloat32(4,true);}if(id===0)fields.heartbeat={custom_mode:f.getUint32(0,true),base_mode:payload[6]};if(id===253)fields.text=new TextDecoder().decode(payload.slice(1,51)).split('\0')[0];if(id===245)fields.landed=payload[1];return fields;
}
export async function validateRecoveryRun(input){
 const raw=typeof input==='string'?input:JSON.stringify(input);if(new TextEncoder().encode(raw).length>MAX_BENCH_BYTES)fail('gói >8 MiB');const r=JSON.parse(raw),{sha256,...body}=r;if(await digest(body)!==sha256)fail('SHA');if(r.format!=='aeris-recovery-run'||r.version!==1||r.simulation!==true)fail('schema');
 const suite=await validateBenchmarkSuite(r.suite),freeze=await validateBenchmarkFreeze(r.freeze,suite);if(!['1.2.1-RECOVERY07','1.3.0-JOURNAL08','1.3.1-JOURNAL08','1.4.0-HANDOFF09','1.5.0-STREAM10','1.6.0-RESUME11','1.7.0-LIFECYCLE12','1.8.0-ACCEPT13','1.9.0-GEO14','1.10.0-PACK15','1.11.0-TRUST16','1.12.0-UPDATE17','1.13.0-RESOURCE18','1.13.1-RESOURCE18','1.14.0-LOAD19'].includes(freeze.build.label))fail('build');
 if(!Array.isArray(r.trials)||r.trials.length!==12)fail('cần đủ 12 trial');const keys=new Set(),ids=new Set(),sessions=new Set();
 for(const t of r.trials){const c=suite.cases.find(c=>c.id===t.caseId&&c.expected.accepted),key=t.caseId+'/'+t.kind,s=t.stages;if(!c||!RECOVERY_KINDS.includes(t.kind)||keys.has(key)||!s)fail('case/kind trùng');keys.add(key);
  const reset=t.reset;if(reset?.container!=='aeris-sitl'||reset.before?.armed!==false||!fresh(reset.before)||!fresh(reset.after)||reset.after.armed!==false||reset.before.sessionId===reset.after.sessionId||sessions.has(reset.after.sessionId)||!time(reset.before.time)||!time(reset.after.time)||Date.parse(reset.before.time)<Date.parse(freeze.createdAt)||Date.parse(reset.after.time)<Date.parse(reset.before.time))fail('reset/session');sessions.add(reset.after.sessionId);
  if(!fresh(s.ready)||s.ready.sessionId!==reset.after.sessionId||s.ready.armed!==false||!s.ready.configuration.pass||!s.ready.mission.readbackMatches||!fresh(s.ground)||s.ground.armed!==false||s.ground.landed!==1)fail('ready/ground');
  if(!Array.isArray(t.wire)||!t.wire.length||t.wire.length>4000||!Array.isArray(t.passive))fail('wire');
  const wire=t.wire.map(w=>{if(!time(w.time)||typeof w.forwarded!=='boolean'||typeof w.phase!=='string')fail('wire metadata');const p=recoveryPacket(w);if(p.id===23)fail('PARAM_SET');if(p.system!==255||p.component!==190)fail('GCS wire identity');if(p.id===76&&[176,400].includes(p.command)&&!(w.phase==='flight'||w.phase==='landing'&&p.command===176&&p.param2===6))fail('implicit flight command');return {...w,...p};});
  for(const p of t.passive){const decoded=recoveryPacket(p);if(decoded.system!==1||decoded.component!==1||decoded.heartbeat&&(decoded.heartbeat.custom_mode!==p.fields.custom_mode||decoded.heartbeat.base_mode!==p.fields.base_mode)||decoded.text!==undefined&&decoded.text!==p.fields.text||decoded.landed!==undefined&&decoded.landed!==p.fields.landed_state)fail('passive decoded fields differ from raw packet');}
  for(const phase of ['recover','mismatch','blocked','review'])if(wire.some(w=>w.phase===phase&&![0,43,51,47].includes(w.id)))fail('recovery phát lệnh');
  if(!wire.some(w=>w.phase==='recover'&&w.id===43&&w.forwarded))fail('thiếu mission download');
  if(t.kind==='reboot'){
   if(!fresh(s.beforeReboot)||s.beforeReboot.armed!==false||!fresh(s.rebooted)||s.rebooted.armed!==false||s.beforeReboot.sessionId===s.rebooted.sessionId||s.rebooted.configuration.pass||s.rebooted.mission.readbackMatches||s.mismatch.mission.state!=='failed'||!fresh(s.reloaded)||s.reloaded.armed!==false||!s.reloaded.configuration.pass||!s.reloaded.mission.readbackMatches||!wire.some(w=>w.phase==='reload'&&w.id===44))fail('reboot lost/reload');
  }else{
   if(!fresh(s.airborne)||s.airborne.armed!==true||s.airborne.position?.relativeAltitude<=8||s.airborne.modeId!==(t.kind==='duplex'?3:5)||s.lost.connected!==false||s.lost.position!==null||s.lost.armed!==null||s.lost.configuration.pass||s.lost.mission.readbackMatches||!fresh(s.restored)||s.restored.mission.readbackMatches||s.restored.configuration.pass||!fresh(s.recovered)||!s.recovered.mission.readbackMatches||!s.recovered.configuration.pass)fail('loss/readback/profile');
   if(t.kind!=='tcp'&&!(s.lost.heartbeatAgeMs>3000))fail('missing heartbeat expiry');
   if(t.kind==='tcp'&&s.airborne.sessionId===s.restored.sessionId)fail('TCP session reused');
   if(t.kind!=='tcp'&&(Date.parse(s.restored.time)-Date.parse(s.lost.time)<0||!wire.some(w=>w.phase==='fault'&&w.id===0&&w.forwarded===(t.kind==='inbound'))))fail('heartbeat delivery');
   if(t.kind==='duplex'){const fs=t.passive.some(p=>p.phase==='fault'&&p.id===253&&/GCS Failsafe/i.test(p.fields.text)),rtl=t.passive.some(p=>p.phase==='fault'&&p.id===0&&p.fields.custom_mode===6&&(p.fields.base_mode&128));if(!fs||!rtl||wire.some(w=>w.phase==='fault'&&w.id===0&&w.forwarded))fail('autopilot failsafe RTL proof');}
   else if(!s.recovered.armed||!s.recovered.mission.resumeRequired||s.mismatch.mission.state!=='failed'||s.reviewed.mission.resumeRequired||!s.reviewed.armed||s.reviewed.modeId!==5)fail('source review');
  }
  if(!Array.isArray(t.records)||t.records.length<2)fail('durable records');let recovery=false,upload=false;
  for(const value of t.records){const record=await validateExecutionRecord(value),h=record.rows[0].event.header;if(ids.has(record.id)||h.build!==freeze.build.label||Date.parse(h.startedAt)<Date.parse(freeze.createdAt)||record.summary.outcome==='COMPLETED')fail('record reused/build/completion');ids.add(record.id);
   if(h.sourceSha256===c.expected.sourceSha256){if(await digest(h.compiledItems)!==c.expected.compiledSha256||!same(h.derivation,c.provenance.derivation))fail('source/lineage');if(h.origin==='upload')upload=true;if(h.origin==='recovery'&&record.summary.readbackVerified)recovery=true;}
  }
  if(t.records.some(r=>r.summary.origin==='recovery'&&r.rows.some(row=>row.event.type==='command-sent'&&row.event.detail.name==='auto')))fail('recovery sends AUTO');
  if(!upload||(t.kind!=='reboot'&&!recovery))fail('missing upload/recovery proof');
 }
 if(!suite.cases.filter(c=>c.expected.accepted).every(c=>RECOVERY_KINDS.every(k=>keys.has(c.id+'/'+k))))fail('matrix');return structuredClone(r);
}
export function recoveryReport(run){return {status:run?'ENGINEERING_PASS':'NOT_CHECKED',rows:run?.trials.map(t=>({caseId:t.caseId,kind:t.kind,outcome:t.kind==='reboot'?'RESET_LOST_RELOADED':'RECOVERED_REVIEW_ONLY',records:t.records.map(r=>({id:r.id,outcome:r.summary.outcome,origin:r.summary.origin}))}))??[],scope:'Loopback fault evidence only; no SDK/device, retaining-flash reboot or automatic resume.'};}
