"""Mock-only regression: actual collector entrypoints, no live dependencies/effects."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,types
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];F=R/'planning/beta06g11'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
freeze=json.loads((R/'evidence/beta06/generation11/native-helper-freeze01.json').read_bytes())
original=F/'qa-ground-soak.py';proposal=P/'qa-ground-soak.py';writer=F/'qa-native-budget.py'
assert sha(original)==freeze['files'][str(original.relative_to(R))]
assert sha(writer)==freeze['files'][str(writer.relative_to(R))]
old=original.read_bytes();new=proposal.read_bytes();assert new==old.replace(b'import hashlib,json,math,time,importlib.util,sys,re\n',b'import os,hashlib,json,math,time,importlib.util,sys,re\n',1)
tree=ast.parse(proposal.read_text());imports=[n for n in tree.body if isinstance(n,ast.Import)and any(a.name=='os'for a in n.names)];assert len(imports)==1
imports[0].names=[a for a in imports[0].names if a.name!='os'];assert ast.dump(tree,include_attributes=False)==ast.dump(ast.parse(original.read_text()),include_attributes=False)
# Preload exactly the frozen writer. Proposal header must reuse it, not a sibling.
assert 'g11_native_writer'not in sys.modules
b=load('g11_native_writer',writer);o=load('ground11fix_original',original);m=load('ground11fix_candidate',proposal);assert o.b is m.b is b
boot='11111111-2222-3333-4444-555555555555';basis=b.host_clock.BASIS;clock=[1000.0];calls=[];writes=[]
def tick():return clock[0]
def write(path,value,*,maximum,kind):
 assert Path(path).parent==P and kind=='ground'and maximum==256*2**10
 raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();assert len(raw)<=maximum
 with Path(path).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 writes.append({'path':str(Path(path).relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
def rejected_journal(path):calls.append('journal');raise AssertionError('MOCK_JOURNAL_REFUSAL_NO_NETWORK')
fake=types.SimpleNamespace(observation=lambda:(_ for _ in()).throw(AssertionError('UNEXPECTED_UI_READ')),q=types.SimpleNamespace(state=lambda:(_ for _ in()).throw(AssertionError('UNEXPECTED_STATE_READ'))))
checks={}
with patch.dict(os.environ,{'BETA06_HOST_BOOT_UUID':boot}),patch.object(b,'write_json',side_effect=write),patch.object(o,'E',P),patch.object(o,'journal_rows',side_effect=rejected_journal):
 try:o.collect('mock-original01',P/'mock-clock01.jsonl',clock=tick,pause=lambda _:None,ui=fake);raise AssertionError('ORIGINAL_BUG_NOT_REPRODUCED')
 except NameError as exc:assert str(exc)=="name 'os' is not defined"
 assert not calls and not writes and not(P/'mock-original01-ground-soak.json').exists()
checks['originalEffectiveEntrypoint']='PASS_NAMEERROR_BEFORE_JOURNAL_OR_WRITER'
with patch.dict(os.environ,{'BETA06_HOST_BOOT_UUID':boot}),patch.object(b,'write_json',side_effect=write),patch.object(m,'E',P),patch.object(m,'journal_rows',side_effect=rejected_journal):
 try:m.collect('mock-refusal01',P/'mock-clock01.jsonl',clock=tick,pause=lambda _:None,ui=fake);raise AssertionError('MOCK_REFUSAL_LOST')
 except AssertionError as exc:assert str(exc)=='MOCK_JOURNAL_REFUSAL_NO_NETWORK'
refusal=json.loads((P/'mock-refusal01-ground-soak.json').read_bytes());assert refusal['status']=='REFUSED_GROUND_ADMISSION_NO_AP'and refusal['clockBasis']==basis and refusal['hostBootId']==boot and refusal['endedPythonMonoS']==1000 and calls==['journal']
checks['correctedFinallyRefusal']='PASS_EFFECTIVE_ENTRYPOINT_REPORT_WRITTEN_AND_SERIALIZABLE'
# Real journal parser/hash-chain and renewal predicates, with synthetic rows only.
journal=P/'mock-clock01.jsonl';head='0'*64;seq=0;server='mock-server-boot';viewer='viewer-mock-clock';config='mock-config';source={'run':'publisher-mock','boot':server,'configId':config,'feed':'IAB_SYNTHETIC','profileId':'VP8-720P30-V1'}
def append(kind,data):
 global head,seq
 seq+=1;row={'seq':seq,'previousSha256':head,'hostMonoMs':(clock[0]-1000)*1000,'kind':kind,'data':{'serverBoot':server,**data}};body=json.dumps(row,separators=(',',':')).encode();head=hashlib.sha256(body).hexdigest();raw=body[:-1]+b',"sha256":"'+head.encode()+b'"}\n'
 with journal.open('ab')as f:f.write(raw)
def mapping(at):return {'lowerMs':0,'upperMs':1,'roundtripMs':1,'sampledBrowserMs':at,'validUntilBrowserMs':at+60000}
assert not journal.exists();journal.touch(exist_ok=False)
append('INITIAL',{});append('SOURCE_CONFIGURED',{'session':source});append('BROWSER_CLOCK_EVENT',{'role':'publisher','event':{'session':source,'kind':'CALIBRATION_APPLIED','reason':'INITIAL','mapping':mapping(0)}})
initialSha=sha(journal);initialBytes=journal.stat().st_size;emitted=set();observations=[0]
def pause(seconds):
 assert seconds==.5;clock[0]+=seconds;elapsed=int((clock[0]-1000)*1000)
 for at in (30000,60000):
  if elapsed>=at and at not in emitted:
   emitted.add(at);v=mapping(at);append('SOURCE_MAPPING_APPLIED',{'configId':config,'sourceClock':v});append('BROWSER_CLOCK_EVENT',{'role':'publisher','event':{'session':source,'kind':'CALIBRATION_APPLIED','reason':'PERIODIC_30S','mapping':v}});append('BROWSER_CLOCK_EVENT',{'role':'viewer','event':{'session':{'run':viewer,'boot':server},'kind':'CALIBRATION_APPLIED','reason':'PERIODIC_30S','mapping':v}})
def observation():
 observations[0]+=1;at=(clock[0]-1000)*1000+10;sample=int(at//30000)*30000
 return {'ok':True,'ageMs':100,'observation':{'seq':observations[0],'foreground':True,'run':None,'documentId':'mock-doc','clientId':'mock-client','clientEpoch':1,'clientInstance':'mock-instance','configId':config,'modelSha256':'a'*64,'planSha256':'b'*64,'observedAtClientMonoMs':at,'lifecycleDiagnostics':{'format':'aeris-beta06g2-lifecycle-diagnostic/1','desiredForeground':True,'documentHidden':False,'nativeForeground':True,'localSessionActive':True,'clientEpoch':1,'counts':{'started':0,'acknowledged':0,'failed':0,'deadline':0}},'mediaReadiness':{'active':True,'clockStatus':'CALIBRATED_BOUNDS','clockDegraded':False,'previewReady':True,'frameAgeMs':10,'clockSessionId':viewer,'clockMappingSampledBrowserMs':sample,'clockMappingValidUntilBrowserMs':sample+60000}}}
def state():return {'flight':{'run':None,'authority':None},'payloadLeaseObservation':{'leaseCount':0},'client':{'active':True,'id':'mock-client','epoch':1,'instance':'mock-instance','ageMs':100}}
fake=types.SimpleNamespace(observation=observation,q=types.SimpleNamespace(state=state))
with patch.dict(os.environ,{'BETA06_HOST_BOOT_UUID':boot}),patch.object(b,'write_json',side_effect=write),patch.object(m,'E',P):result=m.collect('mock-success01',journal,clock=tick,pause=pause,ui=fake)
saved=json.loads((P/'mock-success01-ground-soak.json').read_bytes());assert saved==result and result['status']=='PASS_GROUND_INTERVAL_NOT_AP_AUTHORITY'and result['observedPythonSpanS']==75 and len(result['samples'])==151 and result['clockBasis']==basis and result['hostBootId']==boot and result['apStarts']==0
assert len(result['renewalEvidence']['viewer'])==len(result['renewalEvidence']['publisher'])==2 and result['lifecycleFailuresDuringInterval']==0 and emitted=={30000,60000}
checks['correctedSuccessful75s']='PASS_151_REAL_SAMPLE_DECISIONS_AND_REAL_CHAIN_RENEWAL_PREDICATES_CONTROLLED_CLOCK'
assert sha(original)==freeze['files'][str(original.relative_to(R))]and sha(writer)==freeze['files'][str(writer.relative_to(R))]
checks['soleImportDeltaAndFrozenDependencies']='PASS_BYTE_EXACT_ONE_IMPORT_AND_FUNCTION_AST_IDENTICAL'
report={'status':'PASS_ADDITIVE_MISSING_IMPORT_REPAIR_SOURCE_MOCK_ONLY','checks':checks,'groups':len(checks),'originalSha256':sha(original),'proposalSha256':sha(proposal),'frozenWriterSha256':sha(writer),'testSha256':sha(Path(__file__)),'loading':'Preloaded exact frozen g11_native_writer into sys.modules before either collector; both reused identical object. UI/clock/pause explicitly injected; only test module E and writer sink patched. No default UI/dependency action.','mockJournal':{'path':str(journal.relative_to(R)),'initialBytes':initialBytes,'initialSha256':initialSha,'finalBytes':journal.stat().st_size,'finalSha256':sha(journal),'rows':seq},'outputs':writes,'wallTimeSleep':False,'actualRuntimeOrNetwork':False,'G11WiringChanged':False,'authorityGranted':False,'limitations':'Controlled synthetic observations/journal and fake clock only; no actual75s admission, UI latency, Android/SITL/reboot/persistence or product readiness claim. Refusal was injected at journal read before UI; other error branches not newly exercised.'}
out=P/'builder-effective01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(checks),'receipt':str(out),'sha256':sha(out)}))
