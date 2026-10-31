"""Independent effective clock/default/permit checks. Clock-only Python child, no product runtime."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys,types
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];P=Path(__file__).parent;E=R/'evidence/beta06/generation11'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
r=load('qa_g11_runtime',P/'qa-runtime.py');k=r.b.host_clock
if sys.argv[1:]==['--clock-child']:
 line=sys.stdin.buffer.readline(8193);assert len(line)<=8192 and line.endswith(b'\n');permit=json.loads(line);bootstrap=r.validate_bootstrap();binding=r.validate_parent_permit(permit,'22');ui=load('qa_g11_child_ui',P/'qa-ui.py');assert ui.receipt_observation.__defaults__[1]is k.now_s;calls=[]
 try:ui.receipt_observation(permit['hostBeforeLaunchPythonMonoS']-1,reader=lambda:calls.append(1))
 except AssertionError as e:assert 'DEADLINE' in str(e)
 else:raise AssertionError('EXPIRED_PARENT_DEADLINE_ACCEPTED')
 assert calls==[];assert ui.receipt_observation(permit['parentHostDeadlinePythonMonoS'],reader=lambda:{'mock':'read-only'})=={'mock':'read-only'};print(json.dumps({'bootstrap':bootstrap,'binding':binding,'expiredReceiptReaderCalls':0,'defaultReceiptClockCanonical':True,'pid':os.getpid(),'ppid':os.getppid()}));sys.exit(0)
assert not sys.argv[1:];assert tuple(sys.version_info[:3])==(3,9,6)
c=load('qa_g11_controller',P/'qa-root-controller.py');ui=load('qa_g11_ui',P/'qa-ui.py');a=load('qa_g11_airborne',P/'qa-airborne.py');ground=load('qa_g11_ground',P/'qa-ground-soak.py');pg=load('qa_g11_port',P/'qa-port-guard.py');g=c.g;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[];boot=k.boot_id();assert k is c.b.host_clock is ui.b.host_clock is g.host_clock is pg.host_clock
for fn in [c.Controller.__init__,g.DeadlineGuard.__init__,r.validate_parent_permit]:assert fn.__kwdefaults__['clock']is k.now_s
for fn in [ui.receipt_observation,a.wait_target_ready]:assert fn.__defaults__[1]is k.now_s
assert ground.collect.__kwdefaults__['clock']is pg.probe_host_ports.__kwdefaults__['clock']is k.now_s;checks.append('EFFECTIVE_DEFAULTS_SAME_PINNED_PROVIDER_BEFORE_CALLS')
ctl=c.Controller('22');ctl.host_anchor=k.now_s()-1;ctl.guard.anchor_emulator_before_launch('emulator-5582');anchor=ctl.emit('QA_MOCK_ANCHOR_ONLY',anchors=ctl.guard.snapshot());permit={'attempt':'22','clockBasis':k.BASIS,'hostBootId':boot,'rootControllerPid':os.getpid(),'anchorProof':anchor,'parentHostRemainingS':ctl.host_remaining(),'hostBeforeLaunchPythonMonoS':ctl.host_anchor,'parentHostDeadlinePythonMonoS':ctl.host_anchor+2700}
before=k.now_s();child=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--clock-child'],input=json.dumps(permit)+'\n',capture_output=True,text=True,timeout=3,env={**os.environ,'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_HOST_BOOT_UUID':boot,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid())});after=k.now_s();assert child.returncode==0 and not child.stderr and len(child.stdout)<8192,child.stderr;observed=json.loads(child.stdout);assert observed['ppid']==os.getpid()and before<=observed['binding']['receivedPythonMonoS']<=after;assert observed['binding']['parentHostDeadlinePythonMonoS']==permit['parentHostDeadlinePythonMonoS'];checks.append('ACTUAL_APPLE_CHILD_BOOTSTRAP_PERMIT_AND_CROSS_MODULE_UI_DEADLINE_DEFAULT')
for key,value in [('clockBasis','PYTHON_TIME_MONOTONIC_SAME_HOST_BOOT'),('hostBootId','11111111-1111-4111-8111-111111111111')]:
 bad=copy.deepcopy(permit);bad[key]=value;calls=[]
 try:r.validate_parent_permit(bad,'22',clock=lambda:calls.append(1),current_boot=boot,parent_pid=os.getpid(),pid_check=lambda *a:None)
 except k.ClockContractError:pass
 else:raise AssertionError('MIXED_CONTRACT_ACCEPTED')
 assert calls==[]
checks.append('MIXED_BASIS_AND_BOOT_REFUSE_BEFORE_CLOCK_ARITHMETIC')
bad=copy.deepcopy(permit);bad['anchorProof']['anchors']['clockBasis']='CLOCK_MONOTONIC'
try:r.validate_parent_permit(bad,'22',clock=lambda:(_ for _ in()).throw(RuntimeError('ARITHMETIC_REACHED')),current_boot=boot,parent_pid=os.getpid(),pid_check=lambda *a:None)
except AssertionError:pass
else:raise AssertionError('MIXED_ANCHOR_ACCEPTED')
try:r.validate_parent_permit(permit,'22',clock=lambda:permit['anchorProof']['anchors']['emulatorBeforeLaunchPythonMonoS']-1,current_boot=boot,parent_pid=os.getpid(),pid_check=lambda *a:None)
except AssertionError:pass
else:raise AssertionError('BACKWARD_CHILD_CLOCK_ACCEPTED')
checks.append('MIXED_ANCHOR_AND_BACKWARD_CHILD_CLOCK_REFUSED')
with patch.dict(os.environ,{'BETA06_CLOCK_BASIS':'BAD','BETA06_HOST_BOOT_UUID':boot,'BETA06_ROOT_CONTROLLER_PID':str(os.getppid())}),patch.object(r,'plan',side_effect=AssertionError('PLAN_EFFECT_REACHED'))as plan:
 try:r.run('22')
 except k.ClockContractError:pass
 else:raise AssertionError('BOOTSTRAP_MUST_REFUSE')
 plan.assert_not_called()
with patch.object(k,'now_ns',side_effect=k.ClockContractError('UNSUPPORTED_NO_FALLBACK')):
 try:r.validate_bootstrap({'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_HOST_BOOT_UUID':boot,'BETA06_ROOT_CONTROLLER_PID':str(os.getppid())})
 except k.ClockContractError:pass
 else:raise AssertionError('UNSUPPORTED_ACCEPTED')
checks.append('BAD_BOOTSTRAP_AND_UNSUPPORTED_PROVIDER_REFUSE_BEFORE_PLAN_OR_WRITER')
ns=[0];clock=lambda:k.now_s(reader=lambda _:ns[0]);run='s'+'b'*20
for label,start,end,key,minimum in [('AP',0,315,'apRemainingConservativeS',225),('EMU',2400,2460,'emulatorRemainingConservativeS',240)]:
 ns[0]=0;guard=g.DeadlineGuard(host_boot_id=boot,clock=clock);guard.anchor_emulator_before_launch('QA_EMU');ns[0]=start*10**9;guard.anchor_before_connect(label);guard.note_connect_input_once(label);guard.bind_observed_run(label,run);ns[0]=end*10**9;assert guard.before_arm(run=run,emulator_id='QA_EMU',current_host_boot_id=boot)[key]==minimum;ns[0]+=10**6
 try:guard.before_arm(run=run,emulator_id='QA_EMU',current_host_boot_id=boot)
 except g.DeadlineGuardError:pass
 else:raise AssertionError('SHORT_RESERVE_ACCEPTED')
ns[0]=0;mock=c.Controller('22',boot_reader=lambda:boot,clock=clock);mock.host_anchor=0;mock.guard.anchor_emulator_before_launch('QA_EMU');ns[0]=2610*10**9;assert mock.closure_reserve()==90;ns[0]+=10**6
try:mock.closure_reserve()
except AssertionError as e:assert 'CLOSURE_RESERVE' in str(e)
else:raise AssertionError('CLOSURE_SHORT_ACCEPTED')
checks.append('ORIGINAL_225_240_90_EXACT_AND_ONE_MS_SHORT_NO_AUTHORITY')
proof=json.loads((E/'builder-clock-integration01.json').read_bytes());inventory=proof['checks']['staticClockSiteInventory']['rows'];source={}
for row in inventory:
 p=R/row['path'];assert sha(p)==row['sha256'];tree=ast.parse(p.read_text());bad=[n for n in ast.walk(tree)if isinstance(n,ast.Attribute)and n.attr in ['monotonic','monotonic_ns','perf_counter','perf_counter_ns']];assert not bad,row['path'];source[row['path']]=sha(p)
source['pilot/beta06g11/clock_basis.py']=sha(R/'pilot/beta06g11/clock_basis.py');assert source['pilot/beta06g11/clock_basis.py']=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17';checks.append('INDEPENDENT_AST19_CLOCK_SITES_NO_RELATIVE_DEFAULT_OR_DYNAMIC_MONOTONIC')
tree=ast.parse((P/'qa-root-live22.py').read_text());main=tree.body[-1];runtimeAssert=main.body[2];assert isinstance(runtimeAssert,ast.Assert)
try:exec(compile(ast.fix_missing_locations(ast.Module(body=[runtimeAssert],type_ignores=[])),'wrong_interpreter_predicate_only','exec'),{'sys':types.SimpleNamespace(version_info=(3,14,6),executable=sys.executable),'Path':Path})
except AssertionError:pass
else:raise AssertionError('WRONG_INTERPRETER_ACCEPTED')
checks.append('WRONG_INTERPRETER_PREDICATE_REFUSES_BEFORE_IMPORT_WRITER')
report={'status':'PASS_INDEPENDENT_G11_EFFECTIVE_CLOCK_SOURCE_MOCK_ONLY','checks':checks,'groups':len(checks),'sourceSHA256':source,'actualCrossProcessProof':{'parentBeforeS':before,'parentAfterS':after,'child':observed},'basis':k.BASIS,'runtime':sys.version,'APRequests':0,'AndroidLaunches':0,'productHostLaunches':0,'preparedWorkspaceAccess':False,'scope':'Actual default-bound modules and real clock-only Python child; no Controller launch/commands/threads/ports/SDK/runtime or stdlib time patch. Parent pure guard anchor manually populated for this mock permit only. Native separate proof exercises complete Controller.launch callback path.','durationOnlyExceptions':'sleep/select/threadwait/subprocess timeout internals remain local duration-only; no parent absolute anchors passed','runtimeWiringCertifiedOnlyForFrozenFutureGate':False};b=json.dumps(report,separators=(',',':')).encode()+b'\n';assert len(b)<128*1024;out=E/'qa-clock-integration-independent01.json'
with out.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'groups':len(checks)}))
