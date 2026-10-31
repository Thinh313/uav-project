"""G12 targeted normalized-source, clock-only child and effective ground regressions."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,types,subprocess
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];F=R/'planning/beta06g11'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
freeze=json.loads((R/'evidence/beta06/generation11/native-helper-freeze01.json').read_bytes())
original=F/'qa-ground-soak.py';proposal=P/'qa-ground-soak.py';writer=P/'qa-native-budget.py'
changes=[('beta06g11','beta06g12'),('generation11','generation12'),('GENERATION11','GENERATION12'),('host-app11','host-app12'),('g11_','g12_'),('aeris_g11_clock','aeris_g12_clock'),('G11','G12'),("'22'","'24'"),("'23'","'25'"),('22|23','24|25'),('ROOT_LIVE22','ROOT_LIVE24'),('root-controller22','root-controller24'),('EMULATOR22','EMULATOR24'),('BOOT22','BOOT24'),('BOOT23','BOOT25'),('BEFORE23','BEFORE25'),('closure22','closure24'),('attempt23','attempt25'),('Boot22','Boot24'),('Boot23','Boot25'),('g12_frozen_root_controller_live22','g12_frozen_root_controller_live24')]
def transform(text):
 for old,new in changes:text=text.replace(old,new)
 return text
ops=['qa-root-controller.py','qa-runtime.py','qa-deadline-guard.py','qa-device-actions.py','qa-ui.py','qa-android.py','qa-airborne.py','qa-ground-soak.py','qa-restart-proof.py','qa-ap-admission.py','qa-native-replay.py','qa-media-replay.py','qa-native-budget.py','qa-proof-writer.py','qa-raw-flight.mjs','qa-cut-replay.mjs','qa-reboot-replay.mjs','qa-overlap-replay.mjs','qa-root-live22.py','qa-port-guard.py'];normalized=[]
for name in ops:
 old=F/name;new=P/('qa-root-live24.py'if name=='qa-root-live22.py'else name);assert sha(old)==freeze['files'][str(old.relative_to(R))];expected=transform(old.read_text())
 if name=='qa-ground-soak.py':expected=expected.replace('import hashlib,json,math,time,importlib.util,sys,re\n','import os,hashlib,json,math,time,importlib.util,sys,re\n',1)
 assert new.read_text()==expected,('UNAUTHORIZED_OPERATIONAL_DELTA',name)
 if name.endswith('.py'):
  numbers=lambda text:[n.value for n in ast.walk(ast.parse(text))if isinstance(n,ast.Constant)and type(n.value)in(int,float)]
  assert numbers(old.read_text())==numbers(new.read_text()),('NUMERIC_DELTA',name)
 normalized.append({'oldPath':str(old.relative_to(R)),'oldSha256':sha(old),'path':str(new.relative_to(R)),'sha256':sha(new),'soleExtraDelta':'import os'if name=='qa-ground-soak.py'else None})
assert 'g12_native_writer'not in sys.modules
b=load('g12_native_writer',writer);m=load('g12_effective_ground',proposal);k=b.host_clock
assert m.b is b and sha(R/'pilot/beta06g12/clock_basis.py')=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
r=load('g12_effective_runtime',P/'qa-runtime.py');ui=load('g12_effective_ui',P/'qa-ui.py')
if sys.argv[1:]==['--clock-child']:
 packet=sys.stdin.buffer.read(4097);assert len(packet)<=4096;permit=json.loads(packet);bootstrap=r.validate_bootstrap();binding=r.validate_parent_permit(permit,'24');calls=[]
 try:ui.receipt_observation(permit['hostBeforeLaunchPythonMonoS']-1,reader=lambda:calls.append(True));raise AssertionError('EXPIRED_DEFAULT_ACCEPTED')
 except AssertionError as exc:assert str(exc)=='STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT'
 assert not calls;print(json.dumps({'bootstrap':bootstrap,'binding':binding,'expiredReaderCalls':0,'defaultCanonical':ui.receipt_observation.__defaults__[1]is k.now_s}));sys.exit(0)
assert not sys.argv[1:]and tuple(sys.version_info[:3])==(3,9,6)
# The original frozen module remains a separate loaded instance with its exact writer.
oldb=load('g11_native_writer',F/'qa-native-budget.py');o=load('g12_old_ground_witness',original);assert o.b is oldb
boot='11111111-2222-3333-4444-555555555555';basis=b.host_clock.BASIS;clock=[1000.0];calls=[];writes=[]
def tick():return clock[0]
def write(path,value,*,maximum,kind):
 assert Path(path).parent==P and kind=='ground'and maximum==256*2**10
 raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();assert len(raw)<=maximum
 with Path(path).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 writes.append({'path':str(Path(path).relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
def rejected_journal(path):calls.append('journal');raise AssertionError('MOCK_JOURNAL_REFUSAL_NO_NETWORK')
fake=types.SimpleNamespace(observation=lambda:(_ for _ in()).throw(AssertionError('UNEXPECTED_UI_READ')),q=types.SimpleNamespace(state=lambda:(_ for _ in()).throw(AssertionError('UNEXPECTED_STATE_READ'))))
checks={'normalizedSourceAndNumbers':{'files':normalized,'map':changes,'status':'PASS_20_BYTE_NORMALIZED_SIBLINGS_AND_ALL_PYTHON_NUMERIC_CONSTANTS'}}
with patch.dict(os.environ,{'BETA06_HOST_BOOT_UUID':boot}),patch.object(oldb,'write_json',side_effect=write),patch.object(o,'E',P),patch.object(o,'journal_rows',side_effect=rejected_journal):
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
assert sha(original)==freeze['files'][str(original.relative_to(R))]
checks['soleImportDeltaAndFrozenDependencies']='PASS_20_NORMALIZED_SOURCE_FILES_PLUS_SOLE_GROUND_IMPORT'

# Current effective parent/child validator and UI default, with no actual namespace writes.
c=load('g12_effective_controller',P/'qa-root-controller.py');a=load('g12_effective_airborne',P/'qa-airborne.py');pg=load('g12_effective_ports',P/'qa-port-guard.py')
assert c.b is r.b is ui.b is a.b is b and c.g.host_clock is pg.host_clock is k
assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is r.validate_parent_permit.__kwdefaults__['clock']is ui.receipt_observation.__defaults__[1]is a.wait_target_ready.__defaults__[1]is m.collect.__kwdefaults__['clock']is pg.probe_host_ports.__kwdefaults__['clock']is k.now_s
actualboot=k.boot_id();ctl=c.Controller('24',boot_reader=lambda:actualboot);ctl.host_anchor=k.now_s()-1;ctl.guard.anchor_emulator_before_launch('emulator-5582');anchor=ctl.emit('MOCK_CLOCK_ONLY_ANCHOR',anchors=ctl.guard.snapshot());permit={'attempt':'24','clockBasis':k.BASIS,'hostBootId':actualboot,'rootControllerPid':os.getpid(),'anchorProof':anchor,'parentHostRemainingS':ctl.host_remaining(),'hostBeforeLaunchPythonMonoS':ctl.host_anchor,'parentHostDeadlinePythonMonoS':ctl.host_anchor+2700};before=k.now_s()
child=subprocess.run(['/usr/bin/python3','-B',str(Path(__file__).resolve()),'--clock-child'],input=json.dumps(permit).encode(),capture_output=True,timeout=5,env={**os.environ,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid()),'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_HOST_BOOT_UUID':actualboot});after=k.now_s();assert child.returncode==0,(child.returncode,child.stderr[:2048].decode());assert len(child.stdout)<=4096;answer=json.loads(child.stdout);assert before<=answer['binding']['receivedPythonMonoS']<=after and answer['binding']['parentHostDeadlinePythonMonoS']==ctl.host_anchor+2700 and answer['defaultCanonical']and answer['expiredReaderCalls']==0
for field in ['clockBasis','hostBootId']:
 bad=copy.deepcopy(permit);bad[field]='INVALID';called=[]
 try:r.validate_parent_permit(bad,'24',clock=lambda:called.append(True),current_boot=actualboot,parent_pid=os.getpid(),pid_check=lambda *x:None);raise AssertionError('BAD_PERMIT_ACCEPTED')
 except k.ClockContractError:pass
 assert not called
checks['currentClockIdentityAndChildDefault']={'status':'PASS_EFFECTIVE_G12_DEFAULTS_AND_CLOCK_ONLY_CHILD_VALIDATOR','parentBeforeS':before,'parentAfterS':after,'child':answer,'noControllerLaunchThread':True,'noProductRuntime':True}
inventory=[]
for path in [P/name for name in ops if name.endswith('.py')and name!='qa-root-live22.py']+[P/'qa-root-live24.py',R/'pilot/beta06g12/clock_basis.py']:
 tree=ast.parse(path.read_text());assert not[n for n in ast.walk(tree)if isinstance(n,ast.Attribute)and n.attr in ['monotonic','monotonic_ns','perf_counter','perf_counter_ns']];inventory.append({'path':str(path.relative_to(R)),'sha256':sha(path)})
checks['currentStaticClockSites']={'status':'PASS_NO_RELATIVE_CLOCK_ATTRIBUTE_IN_NATIVE_EFFECTIVE_FILES','rows':inventory,'inheritedClockProof':'G11 effective6/independent8 are historical and reused only with whole-source namespace equality. Current child/default seam tested above; Node/duration-only stdlib internals unchanged.'}
actual=R/'evidence/beta06/generation12';assert not[p.name for p in actual.iterdir()if p.name.startswith(('android-','root-controller24','root-controller25','root-runtime24','root-runtime25','host-app12','host-console','quota-native-ledger','workspace-first-writer'))]
checks['actualNamespacePristine']='PASS_NO_MOCK_LEAKS_INTO_ACTUAL_LAUNCH_NAMES'
report={'status':'PASS_G12_EFFECTIVE_GROUND_AND_CLOCK_SOURCE_MOCK_ONLY','checks':checks,'groups':len(checks),'originalSha256':sha(original),'proposalSha256':sha(proposal),'currentWriterSha256':sha(writer),'testSha256':sha(Path(__file__)),'loading':'Current G12 collector preloads/reuses exact effective g12_native_writer. Frozen G11 witness separately reuses exact old g11_native_writer. UI/clock/pause explicitly injected; only test module E and writer sink patched. No default UI/dependency action.','mockJournal':{'path':str(journal.relative_to(R)),'initialBytes':initialBytes,'initialSha256':initialSha,'finalBytes':journal.stat().st_size,'finalSha256':sha(journal),'rows':seq},'outputs':writes,'wallTimeSleep':False,'actualRuntimeOrNetwork':False,'G11WiringChanged':False,'G12RuntimeExecuted':False,'authorityGranted':False,'limitations':'Controlled synthetic observations/journal and fake clock only; no actual75s admission, UI latency, Android/SITL/reboot/persistence or product readiness claim. Refusal was injected at journal read before UI; other error branches not newly exercised.'}
out=R/'evidence/beta06/generation12/builder-native-tests01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(checks),'receipt':str(out),'sha256':sha(out)}))
