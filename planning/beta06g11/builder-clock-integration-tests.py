"""Effective G11 clock wiring proof. Mock Python helper only; no Android/app/AP."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,io,json,os,subprocess,sys,tempfile,time,types
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation11'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
r=load('g11_effective_clock_runtime',P/'qa-runtime.py');k=r.b.host_clock
if sys.argv[1:2]==['--child-protocol']:
 out=Path(sys.argv[2]);boot=r.validate_bootstrap();assert boot['rootControllerPid']==os.getppid();ready={'attempt':'22','controllerPid':os.getpid(),'permission':'MOCK_CLOCK_READER_ONLY','clockBasis':boot['clockBasis'],'hostBootId':boot['hostBootId']}
 with (out/'android-ready-to-launch22.json').open('x')as f:json.dump(ready,f)
 end=k.now_s()+5
 while not(out/'android-launch-permit22.json').exists():assert k.now_s()<end;time.sleep(.01)
 permit=json.loads((out/'android-launch-permit22.json').read_bytes());binding=r.validate_parent_permit(permit,'22');ui=load('g11_effective_child_ui',P/'qa-ui.py');calls=[]
 try:ui.receipt_observation(permit['hostBeforeLaunchPythonMonoS']-1,reader=lambda:calls.append('SHOULD_NOT_READ'));raise AssertionError('EXPIRED_GLOBAL_DEADLINE_ACCEPTED')
 except AssertionError as exc:assert str(exc)=='STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT'
 assert calls==[];assert ui.receipt_observation(k.now_s()+1,reader=lambda:{'mockReceipt':True})=={'mockReceipt':True};assert ui.receipt_observation.__defaults__[1]is k.now_s
 print(json.dumps({'bootstrap':boot,'binding':binding,'pid':os.getpid(),'ppid':os.getppid(),'expiredReceiptReaderCalls':len(calls),'positiveDefaultReceipt':True,'uiDefaultIsCanonical':True,'stdlibMonotonicStillProcessRelative':time.monotonic(),'canonicalNowS':k.now_s()}));sys.exit(0)
assert not sys.argv[1:] and tuple(sys.version_info[:3])==(3,9,6)
c=load('g11_effective_clock_controller',P/'qa-root-controller.py');ui=load('g11_effective_clock_ui',P/'qa-ui.py');a=load('g11_effective_clock_airborne',P/'qa-airborne.py');gnd=load('g11_effective_clock_ground',P/'qa-ground-soak.py');pg=load('g11_effective_clock_port',P/'qa-port-guard.py');g=c.g;boot=k.boot_id();checks={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class FakeQuota:
 def reserve_write(self,**kw):return kw
 def load_policy(self):return {'scanner':{'staleMs':15000},'categories':{'screenshots':{'perFileBytes':5*2**20}}}
c.b._quota=FakeQuota()
assert c.b.host_clock is r.b.host_clock is ui.b.host_clock is g.host_clock is pg.host_clock is k
assert c.Controller.__init__.__kwdefaults__['clock']is g.DeadlineGuard.__init__.__kwdefaults__['clock']is r.validate_parent_permit.__kwdefaults__['clock']is k.now_s
assert ui.receipt_observation.__defaults__[1]is a.wait_target_ready.__defaults__[1]is gnd.collect.__kwdefaults__['clock']is pg.probe_host_ports.__kwdefaults__['clock']is k.now_s
checks['effectiveDefaultsAndIdentity']='PASS_ONE_CANONICAL_PROVIDER'
# The actual unchanged launch method produces the actual permit for a real clock-only child.
real_popen=subprocess.Popen
with tempfile.TemporaryDirectory(prefix='builder-g11-clock-child-',dir=E)as directory:
 out=Path(directory);ctl=c.Controller('22',boot_reader=lambda:boot);ctl.host_anchor=k.now_s()-1
 def mock_runtime(argv,**kwargs):
  assert argv[:2]==[sys.executable,'-B']and argv[-2:]==['22','--require-permit'];return real_popen(['/usr/bin/python3','-B',str(Path(__file__).resolve()),'--child-protocol',str(out)],**kwargs)
 before=k.now_s()
 with patch.object(c,'E',out),patch.object(c.subprocess,'Popen',side_effect=mock_runtime):
  result=ctl.launch({'commandId':'g11-effective-clock-only'})
  ctl.permit_thread.join(timeout=5);assert not ctl.permit_thread.is_alive()and ctl.launch_error is None,ctl.launch_error
 assert ctl.runtime.wait(timeout=5)==0;ctl.runtime_capture.finish();after=k.now_s();text=(out/'root-runtime22.txt').read_text();assert len(text.encode())<=8192;child=json.loads(text);permit=json.loads((out/'android-launch-permit22.json').read_bytes())
 assert child['ppid']==os.getpid()and child['bootstrap']['hostBootId']==boot and before<=child['binding']['receivedPythonMonoS']<=after;assert child['binding']['parentHostDeadlinePythonMonoS']==ctl.host_anchor+2700;assert child['binding']['emulatorDeadlinePythonMonoS']==ctl.guard.snapshot()['emulatorBeforeLaunchPythonMonoS']+2700
 assert child['expiredReceiptReaderCalls']==0 and child['uiDefaultIsCanonical']and child['positiveDefaultReceipt'];assert child['stdlibMonotonicStillProcessRelative']<child['canonicalNowS']
 checks['actualParentLaunchAndChildValidator']={'parentBeforeS':before,'parentAfterS':after,'launchResult':result,'permit':permit,'child':child,'scope':'Controller.launch with only its Popen replaced by a clock-only Apple child; actual parent readiness/permit code and child bootstrap/permit/UI default code. No runtime.run/SDK/Android/app/AP.'}
 with patch.object(c,'E',out):ctl.close()
# Mixed contracts must reject before clock arithmetic; bootstrap must reject before plan/mkdir/writers.
negative=[]
for case in ['basis','boot','anchorBasis','anchorBoot','pid','past','future','nan']:
 value=copy.deepcopy(permit)
 if case=='basis':value['clockBasis']='PYTHON_TIME_MONOTONIC_SAME_HOST_BOOT'
 elif case=='boot':value['hostBootId']='-'*36
 elif case=='anchorBasis':value['anchorProof']['anchors']['clockBasis']='OTHER'
 elif case=='anchorBoot':value['anchorProof']['anchors']['hostBootId']='0'*36
 elif case=='pid':value['rootControllerPid']+=1
 elif case=='past':value['parentHostDeadlinePythonMonoS']=k.now_s()-1
 elif case=='future':value['parentHostDeadlinePythonMonoS']=k.now_s()+2701
 elif case=='nan':value['parentHostDeadlinePythonMonoS']=float('nan')
 called=[]
 def clock():called.append(True);return k.now_s()
 try:r.validate_parent_permit(value,'22',clock=clock,current_boot=boot,parent_pid=os.getpid(),pid_check=lambda *a:None);raise AssertionError('BAD_PERMIT_ACCEPTED:'+case)
 except (AssertionError,k.ClockContractError)as exc:assert not str(exc).startswith('BAD_PERMIT_ACCEPTED')
 if case in ['basis','boot','anchorBasis','anchorBoot','pid']:assert called==[]
 negative.append(case)
for case in ['basis','boot','pid','unsupported']:
 env={'BETA06_HOST_BOOT_UUID':boot,'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_ROOT_CONTROLLER_PID':str(os.getppid())}
 if case=='basis':env['BETA06_CLOCK_BASIS']='OTHER'
 elif case=='boot':env['BETA06_HOST_BOOT_UUID']='-'*36
 elif case=='pid':env['BETA06_ROOT_CONTROLLER_PID']='0'
 with patch.dict(os.environ,env),patch.object(r,'plan')as plan,patch.object(r.E.__class__,'mkdir')as mkdir,patch.object(r.b,'write_json')as write:
  if case=='unsupported':
   with patch.object(k,'now_ns',side_effect=k.ClockContractError('UNSUPPORTED')):
    try:r.run('22');raise AssertionError('BAD_BOOTSTRAP_ACCEPTED')
    except k.ClockContractError:pass
  else:
   try:r.run('22');raise AssertionError('BAD_BOOTSTRAP_ACCEPTED')
   except (AssertionError,k.ClockContractError)as exc:assert str(exc)!='BAD_BOOTSTRAP_ACCEPTED'
  plan.assert_not_called();mkdir.assert_not_called();write.assert_not_called()
checks['contractBeforeArithmeticAndWriter']={'permitNegatives':negative,'bootstrapBeforePlanMkdirWriter':['basis','boot','pid','unsupported']}
# Wrong child ready packet: actual parent thread refuses before anchor/permit writer, no child launch.
for case in ['basis','boot','pid']:
 with tempfile.TemporaryDirectory(prefix='builder-g11-clock-ready-',dir=E)as directory:
  out=Path(directory);fake=types.SimpleNamespace(pid=12345,poll=lambda:None,stdout=io.BytesIO(b''),wait=lambda timeout:0);value={'controllerPid':fake.pid,'clockBasis':k.BASIS,'hostBootId':boot}
  if case=='basis':value['clockBasis']='OTHER'
  elif case=='boot':value['hostBootId']='-'*36
  else:value['controllerPid']+=1
  (out/'android-ready-to-launch22.json').write_text(json.dumps(value));ctl=c.Controller('22',boot_reader=lambda:boot);ctl.host_anchor=k.now_s()
  with patch.object(c,'E',out),patch.object(c.subprocess,'Popen',return_value=fake):
   ctl.launch({'commandId':'g11-bad-ready-'+case});ctl.permit_thread.join(timeout=2)
   assert ctl.launch_error and ctl.guard.snapshot()['emulatorBeforeLaunchPythonMonoS']is None and not(out/'android-launch-permit22.json').exists()
  with patch.object(c,'E',out):ctl.close()
checks['parentReadyBeforeAnchorPermitWriter']='PASS_BASIS_BOOT_PID_NEGATIVES'
# Exact existing numerical guards with mock ns, not new guard arithmetic.
ns=[0];clock=lambda:k.now_s(reader=lambda _:ns[0]);run='s'+'1'*20
for label,start,at,key,expected in [('ap225',0,315,'apRemainingConservativeS',225),('emu240',2400,2460,'emulatorRemainingConservativeS',240)]:
 ns[0]=0;d=g.DeadlineGuard(host_boot_id=boot,clock=clock);d.anchor_emulator_before_launch('emulator-5582');ns[0]=start*10**9;d.anchor_before_connect(label);d.note_connect_input_once(label);d.bind_observed_run(label,run);ns[0]=at*10**9;assert d.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=boot)[key]==expected;ns[0]+=1000000
 try:d.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=boot);raise AssertionError('ONE_MS_SHORT_ACCEPTED')
 except g.DeadlineGuardError:pass
ns[0]=0;ctl=c.Controller('22',boot_reader=lambda:boot,clock=clock);ctl.host_anchor=0;ctl.guard.anchor_emulator_before_launch('emulator-5582');ns[0]=2610*10**9;assert ctl.closure_reserve()==90;ns[0]+=1000000
try:ctl.closure_reserve();raise AssertionError('CLOSURE_SHORT_ACCEPTED')
except AssertionError as exc:assert 'CLOSURE_RESERVE'in str(exc)
checks['unchanged22524090']='PASS_EXACT_AND_ONE_MS_SHORT'
# Full current Python clock-site inventory. Duration-only stdlib internals are not patched.
ops=['qa-root-controller.py','qa-runtime.py','qa-deadline-guard.py','qa-device-actions.py','qa-ui.py','qa-android.py','qa-airborne.py','qa-ground-soak.py','qa-restart-proof.py','qa-ap-admission.py','qa-native-replay.py','qa-media-replay.py','qa-native-budget.py','qa-proof-writer.py','qa-root-live22.py','qa-port-guard.py']
paths=[P/name for name in ops]+[R/'pilot/beta06g11'/name for name in ['clock_basis.py','quota.py','flight/runtime.py']];inventory=[]
for path in paths:
 tree=ast.parse(path.read_text());leaks=[];sites=[];utc=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Attribute)and node.attr in ['monotonic','monotonic_ns','perf_counter','perf_counter_ns']:leaks.append(node.lineno)
  if isinstance(node,ast.Attribute)and node.attr in ['now_s','now_ns','clock_gettime_ns']:sites.append({'line':node.lineno,'providerCall':node.attr})
  if isinstance(node,ast.Attribute)and isinstance(node.value,ast.Name)and node.value.id=='time'and node.attr in ['time','time_ns']:utc.append({'line':node.lineno,'purpose':'UTC metadata or exclusive filename only, never anchor'})
 assert not leaks,(str(path),leaks);inventory.append({'path':str(path.relative_to(R)),'sha256':sha(path),'explicitClockSites':sites,'utcMetadataOnly':utc,'forbiddenRelativeDefaults':leaks})
checks['staticClockSiteInventory']={'files':len(inventory),'rows':inventory,'stdlibExceptions':['sleep/select/join/wait/communicate timeout durations are local intervals; no parent anchors passed into them.','Immutable R2 wait policy receives explicit Controller clock at effective call; its frozen default is never used in this route.'],'noStdlibMonkeypatch':True}
report={'classification':'G11_EFFECTIVE_CLOCK_SOURCE_MOCK_NO_PRODUCT_RUNTIME','status':'PASS_EFFECTIVE_CLOCK_BINDING','groups':len(checks),'checks':checks,'providerSha256':sha(R/'pilot/beta06g11/clock_basis.py'),'testSha256':sha(Path(__file__)),'runtime':{'executable':sys.executable,'version':sys.version},'scope':'No host app/emulator/ADB/browser/SITL/listener/build/install/sign, no preparedworkspace access; temporary clock-only helper bodies cleaned, current G10 unchanged. Parent methods are injected mock objects, not an operational campaign.'}
out=E/'builder-clock-integration01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(checks),'inventoryFiles':len(inventory),'receipt':str(out),'sha256':sha(out)}))
