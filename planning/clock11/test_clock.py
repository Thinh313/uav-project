"""Read-only two-Apple-process proof and pure frozen-guard mocks; no campaign."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys,time
P=Path(__file__).resolve().parent;R=P.parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
k=load('clock11_candidate',P/'clock_basis.py')
if sys.argv[1:]==['--child']:
 raw=sys.stdin.buffer.readline(2049);assert len(raw)<=2048 and raw.endswith(b'\n');p=json.loads(raw);boot=k.boot_id();k.same_contract(p['boot'],boot,p['basis']);now=k.now_ns();assert p['hostAnchorNs']<=now<p['hostDeadlineNs']<=now+2700*10**9;assert p['emulatorAnchorNs']<=now<p['emulatorDeadlineNs']<=now+2700*10**9
 print(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'boot':boot,'basis':k.BASIS,'nowNs':now,'oldAppleMonotonicNs':time.monotonic_ns(),'hostRemainingNs':p['hostDeadlineNs']-now,'emulatorRemainingNs':p['emulatorDeadlineNs']-now,'version':sys.version,'executable':sys.executable}));sys.exit(0)
assert not sys.argv[1:] and tuple(sys.version_info[:3])==(3,9,6),'DIRECT_APPLE_PARENT_ONLY'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks={};boot=k.boot_id()
for value in [None,True,-1,1.2,float('nan'),float('inf')]:
 try:k.now_ns(reader=lambda _id,value=value:value);raise AssertionError('INVALID_CLOCK_ACCEPTED')
 except k.ClockContractError:pass
for kwargs in [{'platform':'linux'},{'clock_id':time.CLOCK_MONOTONIC},{'clock_id':True},{'reader':lambda _:(_ for _ in()).throw(OSError('UNSUPPORTED'))}]:
 try:k.now_ns(**kwargs);raise AssertionError('UNSUPPORTED_CLOCK_ACCEPTED')
 except k.ClockContractError:pass
for observed,basis in [('0'*36,k.BASIS),(boot,'CLOCK_MONOTONIC')]:
 try:k.same_contract(boot,observed,basis);raise AssertionError('MIXED_CONTRACT_ACCEPTED')
 except k.ClockContractError:pass
for invalid_boot in ['-'*36,'0'*36]:
 try:k.same_contract(invalid_boot,invalid_boot,k.BASIS);raise AssertionError('NONCANONICAL_BOOT_UUID_ACCEPTED')
 except k.ClockContractError:pass
checks['invalidUnsupportedAndMixedBootBasis']='PASS_14_NEGATIVE_CASES'
g=load('clock11_frozen_deadline',R/'planning/beta06g10/qa-deadline-guard.py');c=load('clock11_frozen_controller',R/'planning/beta06g10/qa-root-controller.py');ns=[0];read=lambda:k.now_s(reader=lambda _:ns[0]);run='s'+'1'*20
for label,connect_s,exact_s,expected in [('AP225',0,315,'apRemainingConservativeS'),('emulator240',2400,2460,'emulatorRemainingConservativeS')]:
 ns[0]=0;guard=g.DeadlineGuard(host_boot_id=boot,clock=read);guard.anchor_emulator_before_launch('emulator-5582');ns[0]=connect_s*10**9;guard.anchor_before_connect(label);guard.note_connect_input_once(label);guard.bind_observed_run(label,run);ns[0]=exact_s*10**9;proof=guard.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=boot);assert proof[expected]==(225 if label=='AP225'else 240)
 ns[0]+=1000000
 try:guard.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=boot);raise AssertionError('ONE_MS_SHORT_ACCEPTED')
 except g.DeadlineGuardError:pass
 checks[label]={'exact':'PASS','oneMsShort':'REFUSED','authorityGranted':proof['authorityGranted']}
ns[0]=0;ctl=c.Controller('20',boot_reader=lambda:boot,clock=read);ctl.host_anchor=0;ctl.guard.anchor_emulator_before_launch('emulator-5582');ns[0]=2610*10**9;assert ctl.closure_reserve()==90;ns[0]+=1000000
try:ctl.closure_reserve();raise AssertionError('CLOSURE_SHORT_ACCEPTED')
except AssertionError as exc:assert 'CLOSURE_RESERVE' in str(exc)
checks['closure90']={'exact':'PASS','oneMsShort':'REFUSED','noControllerCommandOrThread':True}
# One finite delay distinguishes the two old process-relative origins, never a product wait/retry.
time.sleep(.25);old_parent=time.monotonic_ns();anchor=k.now_ns();payload={'boot':boot,'basis':k.BASIS,'hostAnchorNs':anchor,'hostDeadlineNs':anchor+2700*10**9,'emulatorAnchorNs':anchor,'emulatorDeadlineNs':anchor+2700*10**9};before=k.now_ns();child=subprocess.run(['/usr/bin/python3','-B',str(Path(__file__).resolve()),'--child'],input=json.dumps(payload)+'\n',capture_output=True,text=True,timeout=5);after=k.now_ns();assert child.returncode==0 and not child.stderr and len(child.stdout.encode())<=2048,child.stderr;v=json.loads(child.stdout);assert v['ppid']==os.getpid() and before<=v['nowNs']<=after and v['boot']==boot;assert old_parent>v['oldAppleMonotonicNs'],'OLD_APPLE_ORIGIN_FALSIFICATION_NOT_OBSERVED';assert v['hostRemainingNs']==payload['hostDeadlineNs']-v['nowNs'] and 0<v['hostRemainingNs']<2700*10**9
checks['twoAppleProcesses']={'parentPid':os.getpid(),'boot':boot,'parentOldMonotonicAnchorNs':old_parent,'parentRawBeforeNs':before,'parentRawAfterNs':after,'permit':payload,'child':v,'oldRelativeOriginWouldMakeParentAnchorFuture':True,'newSharedRawOrderAndOriginalDeadline':'PASS'}
# Separate single Brew observation brackets its own monotonic sample on the exact uptime basis.
brew=shutil.which('python3');code="import json,time,sys; a=time.clock_gettime_ns(time.CLOCK_UPTIME_RAW); m=time.monotonic_ns(); b=time.clock_gettime_ns(time.CLOCK_UPTIME_RAW); print(json.dumps({'beforeRawNs':a,'monotonicNs':m,'afterRawNs':b,'clockId':time.CLOCK_UPTIME_RAW,'version':sys.version,'executable':sys.executable}))";before=k.now_ns();r=subprocess.run([brew,'-B','-c',code],capture_output=True,text=True,timeout=5);after=k.now_ns();assert r.returncode==0 and not r.stderr and len(r.stdout.encode())<=2048;r=json.loads(r.stdout);assert before<=r['beforeRawNs']<=r['monotonicNs']<=r['afterRawNs']<=after
checks['BrewExactBasisObservation']={'outerAppleBeforeNs':before,'outerAppleAfterNs':after,**r,'scope':'Read-only sequential observation on CLOCK_UPTIME_RAW; no wall-clock alignment, RTC or alternate sleep basis.'}
report={'status':'PASS_MOCK_ONLY_CLOCK11_NOT_INTEGRATED','checks':checks,'source':{'clockModuleSha256':sha(P/'clock_basis.py'),'testSha256':sha(Path(__file__)),'frozenDeadlineSha256':sha(R/'planning/beta06g10/qa-deadline-guard.py'),'frozenControllerSha256':sha(R/'planning/beta06g10/qa-root-controller.py')},'scope':'Only clock/sysctl reads, two-Apple-process proof plus separate Brew observation, frozen guard objects with injected pure mock ns; no command/controller campaign/thread/ports/AP/Android or stdlib monkeypatch. All G10 source and evidence unchanged.','futureIntegration':'NOT_IMPLEMENTED_NOT_AUTHORIZED_FOR_ACTUAL'}
p=P/'proof02.json'
with p.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(checks),'receipt':str(p),'sha256':sha(p)}))
