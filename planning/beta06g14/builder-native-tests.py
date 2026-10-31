"""G14 current namespace/interface checks; no product effects or actual launch names."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation14';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
b=load('g14_native_writer',P/'qa-native-budget.py');k=b.host_clock;r=load('g14_test_runtime',P/'qa-runtime.py');ui=load('g14_test_ui',P/'qa-ui.py')
if sys.argv[1:]==['--clock-child']:
 raw=sys.stdin.buffer.read(4097);assert len(raw)<=4096;permit=json.loads(raw);boot=r.validate_bootstrap();bound=r.validate_parent_permit(permit,'28');calls=[]
 try:ui.receipt_observation(permit['hostBeforeLaunchPythonMonoS']-1,reader=lambda:calls.append(True));raise AssertionError('EXPIRED_DEFAULT_ACCEPTED')
 except AssertionError as exc:assert str(exc)=='STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT'
 assert not calls;print(json.dumps({'bootstrap':boot,'binding':bound,'expiredReaderCalls':0}));sys.exit(0)
assert not sys.argv[1:]and tuple(sys.version_info[:3])==(3,9,6)
config=json.loads((P/'builder-namespace-map.json').read_bytes());mapping=config['map'];prior=json.loads((R/'evidence/beta06/generation13/native-helper-freeze01.json').read_bytes());rows=[]
def namespace(text):
 for old,new in mapping:text=text.replace(old,new)
 return text
for name in config['operationalFiles']:
 old=R/'planning/beta06g13'/name;new=P/('qa-root-live28.py'if name=='qa-root-live26.py'else name);assert H(old)==prior['files'][str(old.relative_to(R))];expected=namespace(old.read_text());got=new.read_text();delta='namespace only'
 if name=='qa-ap-admission.py':
  expected=expected.replace("'priorGeneration12SITLRequests'];expected=[11,1,1,1,1,2,2,2]","'priorGeneration12SITLRequests','priorGeneration13SITLRequests'];expected=[11,1,1,1,1,2,2,2,1]").replace('EXACT_TWENTYONE_HISTORICAL_REQUESTS_REQUIRED','EXACT_TWENTYTWO_HISTORICAL_REQUESTS_REQUIRED').replace('len(set(runs))==21','len(set(runs))==22')
  begin=got.index('    expected_g13=');end=got.index('    return runs\n',begin);assert "'sa79cb8c8ee88488b9c8b':'595a5047aafcf3bce8e9743a763ec1f3b58b46177b87d3998f366640281f78e0'"in got[begin:end];got=got[:begin]+got[end:];delta='namespace plus exact one G13 original request bytes/history22'
 assert got==expected,('UNDECLARED_DELTA',name)
 if new.suffix=='.py':
  compile(new.read_text(),str(new),'exec');nums=lambda t:[n.value for n in ast.walk(ast.parse(t))if isinstance(n,ast.Constant)and type(n.value)in(int,float)];assert nums(got)==nums(expected)
 else:
  result=subprocess.run(['node','--check',str(new)],capture_output=True,timeout=5);assert result.returncode==0,result.stderr
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'priorPath':str(old.relative_to(R)),'priorSha256':H(old),'delta':delta})
checks={'wholeSourceAndNumericEquivalence':{'status':'PASS_20_CURRENT_SIBLINGS','map':mapping,'rows':rows}}
provider=R/'pilot/beta06g14/clock_basis.py';assert H(provider)==H(R/'pilot/beta06g13/clock_basis.py')=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
c=load('g14_test_controller',P/'qa-root-controller.py');a=load('g14_test_airborne',P/'qa-airborne.py');ground=load('g14_test_ground',P/'qa-ground-soak.py');pg=load('g14_test_ports',P/'qa-port-guard.py');device=load('g14_test_device',P/'qa-device-actions.py')
assert c.b is r.b is ui.b is a.b is ground.b is device.b is b and c.g.host_clock is pg.host_clock is k
assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is r.validate_parent_permit.__kwdefaults__['clock']is ui.receipt_observation.__defaults__[1]is a.wait_target_ready.__defaults__[1]is ground.collect.__kwdefaults__['clock']is pg.probe_host_ports.__kwdefaults__['clock']is k.now_s
boot=k.boot_id();ctl=c.Controller('28',boot_reader=lambda:boot);ctl.host_anchor=k.now_s()-1;ctl.guard.anchor_emulator_before_launch('emulator-5582');proof=ctl.emit('MOCK_CLOCK_ONLY_ANCHOR',anchors=ctl.guard.snapshot());permit={'attempt':'28','clockBasis':k.BASIS,'hostBootId':boot,'rootControllerPid':os.getpid(),'anchorProof':proof,'parentHostRemainingS':ctl.host_remaining(),'hostBeforeLaunchPythonMonoS':ctl.host_anchor,'parentHostDeadlinePythonMonoS':ctl.host_anchor+2700};before=k.now_s()
child=subprocess.run(['/usr/bin/python3','-B',str(Path(__file__).resolve()),'--clock-child'],input=json.dumps(permit).encode(),capture_output=True,timeout=5,env={**os.environ,'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_HOST_BOOT_UUID':boot,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid())});after=k.now_s();assert child.returncode==0,(child.returncode,child.stderr[:2048]);answer=json.loads(child.stdout);assert before<=answer['binding']['receivedPythonMonoS']<=after and answer['binding']['parentHostDeadlinePythonMonoS']==ctl.host_anchor+2700
checks['currentAppleClockChildAndDefaults']={'status':'PASS_CURRENT_CHILD_VALIDATOR_EXPIRED_UI_READER0','child':answer,'parentBeforeS':before,'parentAfterS':after,'providerSha256':H(provider),'noControllerLaunchThread':True}
ad=load('g14_test_admission',P/'qa-ap-admission.py');pins=json.loads((R/'evidence/beta06/generation13/flight-pins01.json').read_bytes());pins['priorGeneration13SITLRequests']=[{'run':'sa79cb8c8ee88488b9c8b','requestSha256':'595a5047aafcf3bce8e9743a763ec1f3b58b46177b87d3998f366640281f78e0'}];assert len(ad.historical_runs(pins))==22
for mode in ['missing','bad-sha','duplicate','mock']:
 bad=copy.deepcopy(pins)
 if mode=='missing':bad.pop('priorGeneration13SITLRequests')
 elif mode=='bad-sha':bad['priorGeneration13SITLRequests'][0]['requestSha256']='0'*64
 elif mode=='duplicate':bad['priorGeneration13SITLRequests'][0]=bad['priorGeneration12SITLRequests'][0]
 else:bad['priorGeneration13SITLRequests'][0]['run']='md02d1193c3e34e88be79'
 try:ad.historical_runs(bad);raise AssertionError('BAD_HISTORY_ACCEPTED')
 except AssertionError as exc:assert str(exc)!='BAD_HISTORY_ACCEPTED'
checks['historical22']='PASS_EXACT_ORIGINAL_G13_REQUEST_AND_FOUR_NEGATIVES'
for badkey,badvalue in [('clockBasis','WRONG'),('hostBootId','aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')]:
 bad=copy.deepcopy(permit);bad[badkey]=badvalue;calls=[]
 try:r.validate_parent_permit(bad,'28',clock=lambda:calls.append(True),parent_pid=os.getpid());raise AssertionError('BAD_PERMIT_ACCEPTED')
 except (AssertionError,k.ClockContractError)as exc:assert str(exc)!='BAD_PERMIT_ACCEPTED'
 assert not calls
checks['currentPermitContextBeforeClock']='PASS_WRONG_BASIS_BOOT_BEFORE_ARITHMETIC'
inventory=[]
for row in rows:
 p=R/row['path']
 if p.suffix=='.py':assert not[n for n in ast.walk(ast.parse(p.read_text()))if isinstance(n,ast.Attribute)and n.attr in ['monotonic','monotonic_ns','perf_counter','perf_counter_ns']];inventory.append({'path':row['path'],'sha256':row['sha256']})
checks['staticClockInventory']={'status':'PASS_NO_RELATIVE_CLOCK_SITES','rows':inventory}
plan=subprocess.run(['/usr/bin/python3','-B',str(P/'qa-root-controller.py'),'--plan'],capture_output=True,timeout=5);assert plan.returncode==0,plan.stderr;value=json.loads(plan.stdout);assert value['attempts']==['28','29']and value['newConnectIntentsBoot28']==4 and value['connectIntentsBoot29']==0 and value['hostBudgetSecondsAcrossBothBoots']==2700
checks['currentPlanNoEffects']={'status':'PASS','plan':value}
actual=[p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller28','root-controller29','root-runtime28','root-runtime29','host-app14','host-console','quota-native-ledger','workspace-first-writer'))];assert not actual;checks['actualNamespacePristine']='PASS_NO_MOCK_ARTIFACTS'
report={'status':'PASS_G14_NATIVE_FOCUSED_SOURCE_MOCK_ONLY','groups':len(checks),'checks':checks,'testSha256':H(Path(__file__)),'inheritedEvidence':{'path':'evidence/beta06/generation13/builder-native-tests02.json','sha256':H(R/'evidence/beta06/generation13/builder-native-tests02.json'),'disposition':'Snapshot prevalidation/caller, numeric polls, deadline/ground/observer/authority/choreography reused ONLY after exact whole operational source normalization, not recounted as actual or newly executed cases.'},'runtimePerformed':False,'scope':'One bounded real clock-only Apple child plus current imports/plan/syntax and read-only exact historical files. No product host/Android/AP/ADB/browser/listener/build/install/sign; no preparedworkspace/operational ledger access.'}
out=E/'builder-native-tests01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(checks),'sha256':H(out),'path':str(out)}))
