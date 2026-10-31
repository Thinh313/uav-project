"""G17 targeted current source/default interfaces; no product effects."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;E=R/'evidence/beta06/generation17';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
b=load('g17_native_writer',P/'qa-native-budget.py');k=b.host_clock;r=load('g17_test_runtime',P/'qa-runtime.py');ui=load('g17_test_ui',P/'qa-ui.py')
if sys.argv[1:]==['--clock-child']:
 raw=sys.stdin.buffer.read(4097);assert len(raw)<=4096;permit=json.loads(raw);boot=r.validate_bootstrap();bound=r.validate_parent_permit(permit,'32');calls=[]
 try:ui.receipt_observation(permit['hostBeforeLaunchPythonMonoS']-1,reader=lambda:calls.append(True));raise AssertionError('EXPIRED_DEFAULT_ACCEPTED')
 except AssertionError as exc:assert str(exc)=='STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT'
 assert not calls;print(json.dumps({'bootstrap':boot,'binding':bound,'expiredReaderCalls':0}));sys.exit(0)
assert not sys.argv[1:]and tuple(sys.version_info[:3])==(3,9,6)
cfg=json.loads((P/'builder-namespace-map.json').read_bytes());prior=json.loads((R/'evidence/beta06/generation15/native-helper-freeze01.json').read_bytes());rows=[]
def namespace(t):
 for a,b in cfg['map']:t=t.replace(a,b)
 return t
for name in cfg['operationalFiles']:
 old=R/'planning/beta06g15'/name;new=P/('qa-root-live32.py'if name=='qa-root-live30.py'else name);assert H(old)==prior['files'][str(old.relative_to(R))];source=old
 got=new.read_text()
 if name=='qa-root-controller.py':
  guard="assert 'resourceEvidenceFailure'in value and value['resourceEvidenceFailure']is None,'HOST_RESOURCE_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';";assert got.count(guard)==1;got=got.replace(guard,'',1)
 assert got==namespace(source.read_text()),('SOURCE_DELTA',name)
 if new.suffix=='.py':
  compile(new.read_text(),str(new),'exec');nums=lambda t:[n.value for n in ast.walk(ast.parse(t))if isinstance(n,ast.Constant)and type(n.value)in(int,float)];assert nums(new.read_text())==nums(source.read_text())
 else:
  result=subprocess.run(['node','--check',str(new)],capture_output=True,timeout=5);assert result.returncode==0,result.stderr
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'priorPath':str(old.relative_to(R)),'priorSha256':H(old),'delta':'namespace only'})
checks={'wholeSourceAndNumericEquivalence':{'rows':rows,'namespaceMap':cfg['map'],'status':'PASS20'}}
provider=R/'pilot/beta06g17/clock_basis.py';assert H(provider)==H(R/'pilot/beta06g15/clock_basis.py')=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
c=load('g17_test_controller',P/'qa-root-controller.py');a=load('g17_test_airborne',P/'qa-airborne.py');ground=load('g17_test_ground',P/'qa-ground-soak.py');pg=load('g17_test_ports',P/'qa-port-guard.py');device=load('g17_test_device',P/'qa-device-actions.py')
assert c.b is r.b is ui.b is a.b is ground.b is device.b is b and c.g.host_clock is pg.host_clock is k
assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is r.validate_parent_permit.__kwdefaults__['clock']is ui.receipt_observation.__defaults__[1]is a.wait_target_ready.__defaults__[1]is ground.collect.__kwdefaults__['clock']is pg.probe_host_ports.__kwdefaults__['clock']is k.now_s
boot=k.boot_id();ctl=c.Controller('32',boot_reader=lambda:boot);ctl.host_anchor=k.now_s()-1;ctl.guard.anchor_emulator_before_launch('emulator-5582');proof=ctl.emit('MOCK_CLOCK_ONLY_ANCHOR',anchors=ctl.guard.snapshot());permit={'attempt':'32','clockBasis':k.BASIS,'hostBootId':boot,'rootControllerPid':os.getpid(),'anchorProof':proof,'parentHostRemainingS':ctl.host_remaining(),'hostBeforeLaunchPythonMonoS':ctl.host_anchor,'parentHostDeadlinePythonMonoS':ctl.host_anchor+2700};before=k.now_s()
child=subprocess.run(['/usr/bin/python3','-B',str(Path(__file__).resolve()),'--clock-child'],input=json.dumps(permit).encode(),capture_output=True,timeout=5,env={**os.environ,'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_HOST_BOOT_UUID':boot,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid())});after=k.now_s();assert child.returncode==0,(child.returncode,child.stderr[:2048]);value=json.loads(child.stdout);assert before<=value['binding']['receivedPythonMonoS']<=after and value['binding']['parentHostDeadlinePythonMonoS']==ctl.host_anchor+2700
checks['currentAppleChildDefaults']={'status':'PASS_CURRENT_CHILD_VALIDATOR_EXPIRED_READER0','child':value,'parentBeforeS':before,'parentAfterS':after,'providerSha256':H(provider),'noControllerLaunchThread':True}
for key,value in [('clockBasis','WRONG'),('hostBootId','aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')]:
 bad=copy.deepcopy(permit);bad[key]=value;calls=[]
 try:r.validate_parent_permit(bad,'32',clock=lambda:calls.append(True),parent_pid=os.getpid());raise AssertionError('BAD_PERMIT_ACCEPTED')
 except (AssertionError,k.ClockContractError)as exc:assert str(exc)!='BAD_PERMIT_ACCEPTED'
 assert not calls
checks['contextBeforeArithmetic']='PASS_BASIS_BOOT_BEFORE_CLOCK'
ad=load('g17_test_admission',P/'qa-ap-admission.py');pins=json.loads((R/'evidence/beta06/generation15/flight-pins01.json').read_bytes());assert len(ad.historical_runs(pins))==22
for mode in ['missing','sha','mock']:
 bad=copy.deepcopy(pins)
 if mode=='missing':bad.pop('priorGeneration13SITLRequests')
 elif mode=='sha':bad['priorGeneration13SITLRequests'][0]['requestSha256']='0'*64
 else:bad['priorGeneration13SITLRequests'][0]['run']='md02d1193c3e34e88be79'
 try:ad.historical_runs(bad);raise AssertionError('BAD_HISTORY_ACCEPTED')
 except AssertionError as exc:assert str(exc)!='BAD_HISTORY_ACCEPTED'
checks['effectiveHistorical22']='PASS_ORIGINAL_G13_BYTES_AND_THREE_NEGATIVES'
head=b'Active Internet connections (including servers)\nProto Recv-Q Send-Q Local Address Foreign Address (state)\n';ports=(8872,8873)
full=pg.parse_kernel_table(head+b'tcp6 0 0 2001:db8:1234:5678:abcd:ef01:2345:6789.12345 2001:db8::2.443 ESTABLISHED\n',b'',0,ports);pg.checked_kernel_snapshot(full,ports);assert full['command']==['/usr/sbin/netstat','-anl','-p','tcp']and full['listeners']==[]
try:pg.parse_kernel_table(head+b'tcp6 0 0 2001:db8:1234:56.12345 *.* ESTABLISHED\n',b'',0,ports);raise AssertionError('TRUNCATED_ACCEPTED')
except pg.KernelObservationError as exc:assert str(exc)=='KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED'
checks['currentPortCommandAndGrammar']='PASS_FULL_SYNTHETIC_IPV6_TRUNCATION_REFUSES_NO_PROBE_OR_KERNEL_CAPTURE'
inventory=[]
for row in rows:
 p=R/row['path']
 if p.suffix=='.py':assert not[n for n in ast.walk(ast.parse(p.read_text()))if isinstance(n,ast.Attribute)and n.attr in ['monotonic','monotonic_ns','perf_counter','perf_counter_ns']];inventory.append({'path':row['path'],'sha256':row['sha256']})
checks['staticClockInventory']={'status':'PASS_NO_RELATIVE_CLOCK','rows':inventory}
plan=subprocess.run(['/usr/bin/python3','-B',str(P/'qa-root-controller.py'),'--plan'],capture_output=True,timeout=5);assert plan.returncode==0,plan.stderr;value=json.loads(plan.stdout);assert value['attempts']==['32','33']and value['newConnectIntentsBoot32']==4 and value['connectIntentsBoot33']==0 and value['hostBudgetSecondsAcrossBothBoots']==2700
checks['currentPlanNoEffects']={'status':'PASS','plan':value}
actual=[p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller32','root-controller33','root-runtime32','root-runtime33','host-app17','host-console','quota-native-ledger','workspace-first-writer'))];assert not actual;checks['actualNamespacePristine']='PASS_NO_MOCK_ARTIFACTS'
report={'status':'PASS_G17_NATIVE_FOCUSED_SOURCE_MOCK_ONLY','groups':len(checks),'checks':checks,'testSha256':H(Path(__file__)),'reusedEvidence':[{'path':n,'sha256':H(R/n)}for n in ['evidence/beta06/generation14/builder-native-tests01.json','evidence/beta06/generation14/qa-native-cooperation01.json','evidence/beta06-port14fix/native-candidate-proof01.json','evidence/beta06-port14fix/qa-independent01.json']],'reuseDisposition':'Snapshot/numericpoll/deadline/ground/authority/choreography and strict parser guards reused only after exact whole source namespace/approved2literal equivalence. Not new actual tests. Historical G14 exact rejected row UNKNOWN.','runtimePerformed':False,'scope':'Current imports/syntax/plan/synthetic parse/read-only history plus one clock-only Apple child; no product host/Android/AP/ADB/browser/listener/portprobe/kernel capture/build/install/sign or preparedworkspace/ledger.','scratchCreated':False}
out=E/'nativebuilder-tests02.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'groups':len(checks)}))
