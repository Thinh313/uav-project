import {compileSurvey,SITL_WORLD} from './compiler.mjs';
import {compileQgc,prepareQgcForSitl} from './qgc.mjs';
import {PROFILE_REF,assertMissionProfile} from './vehicle-profile.mjs';
import {digest,validateExecutionRecord} from './execution-record.mjs';
import {requestIdentity,sha256} from './geodata.mjs';
const clone=x=>structuredClone(x),same=(a,b)=>requestIdentity(a)===requestIdentity(b),hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x),time=x=>typeof x==='string'&&Number.isFinite(Date.parse(x));
const fail=m=>{throw Error(m);},exact=(v,keys)=>{if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).some(k=>!keys.includes(k)))fail('Benchmark schema/extension chưa hỗ trợ.');};
export const BENCH_TRIALS=Object.freeze([{caseId:'narrow',kind:'completed'},{caseId:'rotated',kind:'completed'},{caseId:'qgc-relative',kind:'completed'},{caseId:'rotated',kind:'interrupted'}].map(Object.freeze));
export const EXPECTED_SITL_ARGV=Object.freeze(['/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/aeris/aeris.parm','--speedup','5']);
export const MAX_BENCH_BYTES=8*1024*1024;
function compile(request){const c=request?.format==='aeris-qgc-run'?compileQgc(request):compileSurvey(request,SITL_WORLD);assertMissionProfile(c);return c;}
export async function caseExpectation(request){
 const sourceSha256=await digest(request);
 try{const c=compile(request);return {accepted:true,sourceSha256,compiledSha256:await digest(c.items),items:c.items.length,transects:c.transects??null,error:null};}
 catch(e){return {accepted:false,sourceSha256,compiledSha256:null,items:null,transects:null,error:e.message};}
}
async function parse(input,limit){let raw;try{raw=typeof input==='string'?input:JSON.stringify(input);}catch{fail('Benchmark không phải JSON.');}if(typeof raw!=='string'||new TextEncoder().encode(raw).length>limit)fail('Benchmark vượt giới hạn dung lượng.');let v;try{v=JSON.parse(raw);}catch{fail('Benchmark không phải JSON.');}return v;}
async function sealed(v){if(!hex(v.sha256))fail('Benchmark thiếu SHA-256.');const {sha256:h,...body}=v;if(await digest(body)!==h)fail('Benchmark sai SHA-256.');}
export async function sealBenchmark(value){const {sha256:previous,...body}=value;return {...clone(body),sha256:await digest(body)};}
export async function validateBenchmarkSuite(input){
 const s=await parse(input,256*1024);exact(s,['format','version','id','simulation','world','profile','cases','sha256']);await sealed(s);
 if(s.format!=='aeris-benchmark-suite'||s.version!==1||s.id!=='survey-matrix06'||s.simulation!==true||!same(s.world,SITL_WORLD)||!same(s.profile,PROFILE_REF)||!Array.isArray(s.cases)||s.cases.length!==7)fail('Suite/world/profile chưa hỗ trợ.');
 const ids=new Set();
 for(const c of s.cases){exact(c,['id','title','provenance','request','expected']);if(typeof c.id!=='string'||!/^[a-z0-9-]{1,40}$/.test(c.id)||ids.has(c.id)||typeof c.title!=='string'||!c.title.trim()||c.title.length>100)fail('Case ID/title không hợp lệ.');ids.add(c.id);exact(c.provenance,['kind','source','originalSha256','derivation']);const p=c.provenance;if(typeof p.source!=='string'||p.source.length>300)fail('Thiếu nguồn case.');if(p.kind==='synthetic'){if(p.originalSha256!==null||p.derivation!==null)fail('Synthetic case không được nhận provenance QGC.');}
  else if(p.kind==='qgc-derived'){if(!hex(p.originalSha256)||!p.derivation)fail('Thiếu nguồn QGC.');const d=await prepareQgcForSitl(p.derivation.sourceRaw,p.derivation.options);if(await sha256(p.derivation.sourceRaw)!==p.originalSha256||c.request.rawPlan!==d.raw||!same(d.receipt,p.derivation))fail('QGC case/source/lineage khác nhau.');}else fail('Case provenance chưa hỗ trợ.');
  if(!same(c.expected,await caseExpectation(c.request)))fail('Kỳ vọng compiler khác source case.');
 }
 if(!BENCH_TRIALS.every(t=>s.cases.some(c=>c.id===t.caseId&&c.expected.accepted))||s.cases.filter(c=>!c.expected.accepted).length!==4)fail('Thiếu mission matrix.');
 return clone(s);
}
export async function validateBenchmarkFreeze(input,suite){
 const f=await parse(input,256*1024);exact(f,['format','version','id','createdAt','suiteSha256','build','runtime','sha256']);await sealed(f);
 if(f.format!=='aeris-benchmark-freeze'||f.version!==1||typeof f.id!=='string'||f.id.length>80||!time(f.createdAt)||f.suiteSha256!==suite.sha256)fail('Freeze không thuộc suite.');
 exact(f.build,['version','label','files','sha256']);if(!({'1.2.0':'1.2.0-BENCH06','1.2.1':'1.2.1-RECOVERY07','1.3.0':'1.3.0-JOURNAL08','1.3.1':'1.3.1-JOURNAL08','1.4.0':'1.4.0-HANDOFF09','1.5.0':'1.5.0-STREAM10','1.6.0':'1.6.0-RESUME11','1.7.0':'1.7.0-LIFECYCLE12','1.8.0':'1.8.0-ACCEPT13','1.12.0':'1.12.0-UPDATE17','1.13.0':'1.13.0-RESOURCE18','1.13.1':'1.13.1-RESOURCE18','1.15.0':'1.15.0-ENDURE20','1.14.0':'1.14.0-LOAD19','1.11.0':'1.11.0-TRUST16','1.10.0':'1.10.0-PACK15','1.9.0':'1.9.0-GEO14'}[f.build.version]===f.build.label)||!f.build.files||Array.isArray(f.build.files)||Object.keys(f.build.files).length<10||!Object.entries(f.build.files).every(([p,h])=>/^(app\/|services\/|tools\/|package\.json$)/.test(p)&&!p.includes('..')&&hex(h))||await digest(f.build.files)!==f.build.sha256)fail('Freeze build/source không hợp lệ.');
 exact(f.runtime,['kind','firmware','binarySha256','defaults','imageId','argv','model','speedup','world','profile','resetPolicy']);const r=f.runtime;
 if(r.kind!=='dedicated-loopback-sitl'||r.firmware!=='4.7.1'||!hex(r.binarySha256)||!/^sha256:[a-f0-9]{64}$/.test(r.imageId)||!same(r.world,SITL_WORLD)||!same(r.profile,PROFILE_REF)||r.model!=='quad'||r.speedup!==5||r.resetPolicy!=='observed-disarmed-restart-before-each-trial'||!same(r.argv,EXPECTED_SITL_ARGV))fail('Runtime freeze không hợp lệ.');
 exact(r.defaults,['copter.parm','aeris.parm']);if(!Object.values(r.defaults).every(hex)||Object.keys(r.defaults).length!==2)fail('Runtime defaults thiếu hash.');return clone(f);
}
export async function validateBenchmarkRun(input,{suiteSha256=null}={}){
 const r=await parse(input,MAX_BENCH_BYTES);exact(r,['format','version','simulation','suite','freeze','trials','negativeChecks','comparator','sha256']);await sealed(r);
 if(r.format!=='aeris-benchmark-run'||r.version!==1||r.simulation!==true||!Array.isArray(r.trials)||r.trials.length>4||!Array.isArray(r.negativeChecks)||r.negativeChecks.length>4)fail('Run schema chưa hỗ trợ.');
 const suite=await validateBenchmarkSuite(r.suite);if(suiteSha256&&suite.sha256!==suiteSha256)fail('Gói thuộc suite khác.');const freeze=await validateBenchmarkFreeze(r.freeze,suite);
 if(!same(r.comparator,{arm:'B',application:'RAGAS',status:'NOT_CHECKED',build:null,runtime:null,observations:[]}))fail('BENCH06 chưa có collector/bằng chứng B; không nhận kết quả RAGAS.');
 const keys=new Set(),ids=new Set(),sessions=new Set();
 for(const t of r.trials){exact(t,['caseId','kind','method','reset','record']);const key=t.caseId+'/'+t.kind;if(keys.has(key)||!BENCH_TRIALS.some(p=>p.caseId===t.caseId&&p.kind===t.kind)||t.method!=='automated-sitl')fail('Trial trùng/khác protocol.');keys.add(key);const c=suite.cases.find(c=>c.id===t.caseId),record=await validateExecutionRecord(t.record),h=record.rows[0].event.header;
  if(ids.has(record.id)||sessions.has(record.summary.sessionId))fail('Record/phiên bị dùng lại giữa các trial.');ids.add(record.id);sessions.add(record.summary.sessionId);
  if(record.version<2||h.build!==freeze.build.label||h.sourceSha256!==c.expected.sourceSha256||await digest(h.compiledItems)!==c.expected.compiledSha256||!same(h.profileSnapshot.profile,suite.profile)||!h.profileSnapshot.comparison.pass||!same(h.derivation,c.provenance.derivation)||Date.parse(h.startedAt)<Date.parse(freeze.createdAt))fail('Record không khớp case/build/profile/freeze.');
  exact(t.reset,['container','action','before','after']);const reset=t.reset;exact(reset.before,['checkedAt','sessionId','armed']);exact(reset.after,['checkedAt','sessionId','armed']);if(reset.container!=='aeris-sitl'||reset.action!=='restart'||reset.before.armed!==false||reset.after.armed!==false||reset.before.sessionId===reset.after.sessionId||reset.after.sessionId!==h.sessionId||!time(reset.before.checkedAt)||!time(reset.after.checkedAt)||Date.parse(reset.before.checkedAt)<Date.parse(freeze.createdAt)||Date.parse(reset.after.checkedAt)<Date.parse(reset.before.checkedAt)||Date.parse(h.startedAt)<Date.parse(reset.after.checkedAt))fail('Thiếu ranh giới reset disarmed/phiên/time.');
 }
 const negatives=new Set();for(const n of r.negativeChecks){exact(n,['caseId','sourceSha256','status','error','frames']);const c=suite.cases.find(c=>c.id===n.caseId);if(!c||c.expected.accepted||negatives.has(n.caseId)||n.sourceSha256!==c.expected.sourceSha256||n.status!==409||n.error!==c.expected.error||!Array.isArray(n.frames)||n.frames.length>1000||n.frames.some(f=>f.direction==='out'&&f.id!==0))fail('Negative case/proof khác rejection protocol.');negatives.add(n.caseId);}
 return clone(r);
}
function trialProcedure(t){
 if(!t)return false;const events=t.record.rows.map(r=>r.event),steps=t.kind==='interrupted'?[['guided',4,false],['arm',4,true],['auto',3,true],['hold',5,true],['rtl',6,true]]:[['guided',4,false],['arm',4,true],['auto',3,true]];let previous=-Infinity;
 return steps.every(([name,mode,armed])=>{const e=events.find(e=>e.type==='command-observed'&&e.detail.name===name&&Date.parse(e.time)>=previous),h=e?.proof?.heartbeat;if(!e||!h||!Number.isFinite(h.ageMs)||h.ageMs>3000||h.ageMs<0||h.fields.custom_mode!==mode||!!(h.fields.base_mode&128)!==armed)return false;previous=Date.parse(e.time);return true;});
}
export function benchmarkReport(run){
 const rows=BENCH_TRIALS.map(p=>{const t=run?.trials.find(t=>t.caseId===p.caseId&&t.kind===p.kind),s=t?.record.summary,expected=p.kind==='completed'?'COMPLETED':'STOPPED';return {...p,status:!s?'NOT_CHECKED':s.outcome===expected&&trialProcedure(t)?'PASS':'FAIL',outcome:s?.outcome??null,recordId:t?.record.id??null,readbackVerified:s?.readbackVerified??null,relativeHeightM:s?.heightRangeRelativeM??null,sourceSha256:s?.sourceSha256??null,observationSpanSeconds:s?Math.max(0,(Date.parse(s.closedAt)-Date.parse(s.startedAt))/1000):null,scope:'Automated SITL observation span at speedup5; not operator/native performance.'};});
 const negatives=run?.suite.cases.filter(c=>!c.expected.accepted).map(c=>({caseId:c.id,status:run.negativeChecks.some(n=>n.caseId===c.id)?'PASS':'NOT_CHECKED'}))??[];
 return {armA:{status:run&&rows.every(r=>r.status==='PASS')&&negatives.every(n=>n.status==='PASS')?'ENGINEERING_PASS':run?'PARTIAL':'NOT_CHECKED',method:'automated-sitl',rows,negatives},armB:{status:'NOT_CHECKED',application:'RAGAS'},comparison:{status:'NOT_COMPARABLE',winner:null,operatorTaskSeconds:null,operatorTouches:null,nativePerformance:null,reason:'Chưa đo RAGAS hoặc workflow người điều khiển trên cấu hình tương đương.'}};
}
