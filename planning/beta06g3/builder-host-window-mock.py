"""Actual Controller host methods under fake process/filesystem/clock. Never Popen or UI."""
from pathlib import Path
import importlib.util,sys,json,datetime,hashlib,types,io
p=Path('planning/beta06g3/qa-root-controller.py');spec=importlib.util.spec_from_file_location('independent_g3_host_ctl',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class Clock:
 def __init__(self):self.t=0
 def __call__(self):return self.t
class Memory(io.StringIO):
 def fileno(self):return 0
class FakePath:
 def __init__(self,s='/G3'):self.s=s
 def __truediv__(self,s):return FakePath(self.s+'/'+str(s))
 def __str__(self):return self.s
 def resolve(self):return self
 def exists(self):return False
 def is_dir(self):return True
 def is_symlink(self):return False
 def is_file(self):return self.s.endswith('/app-closure.json')
 def open(self,*a,**k):return Memory()
 def read_bytes(self):return json.dumps({'reason':'EXPLICIT_STOP','payloadEvidenceFailure':None}).encode()
class Proc:
 def __init__(self,pid):self.pid=pid;self.code=None
 def poll(self):return self.code
 def terminate(self):self.code=0
 def wait(self,timeout):return self.code
class Thread:
 def __init__(self,target,daemon):self.target=target
 def start(self):pass
class Socket:
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def bind(self,*args):pass
clock=Clock();calls=[]
def popen(*a,**k):
 calls.append({'args':a,'kwargs':k,'clock':clock()});return Proc(2000+len(calls))
m.E=FakePath();m.shutil.disk_usage=lambda p:types.SimpleNamespace(free=40*2**30);m.os.fsync=lambda fd:None;m.time.sleep=lambda s:setattr(clock,'t',clock.t+s);m.subprocess.Popen=popen;m.threading.Thread=Thread;m.socket.socket=Socket
PROOF={'nominalReport':'FAKE_NOMINAL','faultReport':'FAKE_FAULT','nominalRun':'s'+'1'*20,'faultRun':'s'+'2'*20};proof_bad=False
def proof(*args):
 if proof_bad:raise AssertionError('MOCK_PROOF_NOW_STALE')
 return dict(PROOF)
orig=m.module
def module(name,file):
 if file=='qa-runtime.py':return types.SimpleNamespace(budget_decision=lambda samples:None)
 if file=='qa-restart-proof.py':return types.SimpleNamespace(authorize=proof)
 return orig(name,file)
m.module=module
def make():
 global proof_bad
 clock.t=0;calls.clear();proof_bad=False;ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:{'flight':{'run':None,'authority':None,'busy':False},'payloadLeaseObservation':{'leaseCount':0}}),observation=lambda:{'observation':{'mediaReadiness':{'active':False}}});return m.Controller('04',boot_reader=lambda:'BOOT',clock=clock,ui=ui)
def rejects(fn,part):
 try:fn()
 except AssertionError as e:assert part in str(e),(part,str(e));return
 raise AssertionError('MISSING_REJECTION '+part)
rows=[]
def test(n,fn):
 try:fn();rows.append({'name':n,'status':'PASS'})
 except Exception as e:rows.append({'name':n,'status':'FAIL','error':str(e)})
command={'commandId':'first-host','sourceAndViewerStoppedAndInspected':True}
def first():
 t=make();t.start_host(command);assert len(calls)==1 and t.host_anchor==30;assert calls[0]['clock']==30;assert calls[0]['kwargs']['env']['BETA06_PARENT_HOST_REMAINING_MS']=='1800000';assert t.host_instances==1
test('first_host_anchor_before_actual_fake_Popen_not_after_launch',first)
def restart():
 t=make();t.start_host(command);old=t.host_anchor;clock.t+=200;t.restart_authorization=dict(PROOF);t.stop_host(command);assert t.host_restart_allowed;assert not t.ground_admission;t.start_host({**command,'commandId':'second-host'});assert t.host_anchor==old and t.host_instances==2;assert int(calls[1]['kwargs']['env']['BETA06_PARENT_HOST_REMAINING_MS'])==1570000;assert t.host_remaining()==1570;assert t.ground_admission is None and not t.host_restart_allowed and t.restart_authorization is None
test('one_explicit_managed_restart_preserves_original_host_anchor_and_remaining',restart)
def no_unexpected():
 t=make();t.start_host(command);t.host_process.code=1;rejects(lambda:t.start_host(command),'NO_RESTART_AFTER_UNEXPECTED');assert len(calls)==1
test('unexpected_child_exit_cannot_be_retried',no_unexpected)
def third():
 t=make();t.start_host(command);t.restart_authorization=dict(PROOF);t.stop_host(command);t.start_host({**command,'commandId':'second'});t.host_process.code=0;rejects(lambda:t.start_host(command),'TWO_HOST_INSTANCES');assert len(calls)==2
test('third_generation03_process_refused_before_admission_or_process',third)
def active():
 for state in [{'flight':{'run':'s'+'1'*20}},{'flight':{'authority':{}},'payloadLeaseObservation':{'leaseCount':1}},{'flight':{'busy':True}}]:
  t=make();t.start_host(command);t.ui.q.state=lambda:state;rejects(lambda:t.stop_host(command),'CLOSE_RUN_AND_REVOKE');assert t.host_process.poll()is None and not t.host_restart_allowed
test('managed_stop_requires_no_run_authority_busy_or_payload_lease',active)
def expired():
 t=make();t.start_host(command);t.restart_authorization=dict(PROOF);t.stop_host(command);clock.t=t.host_anchor+1561;rejects(lambda:t.start_host({**command,'commandId':'late'}),'HOST_REMAINING_BELOW240');assert len(calls)==1;assert t.host_remaining()==209
test('restart_admission_time_spends_same_host_window_and_cannot_borrow_old_time',expired)
def persistence():
 t=make();t.persistence_only=True;rejects(lambda:t.reserve('s'+'1'*20),'PERSISTENCE_BOOT05_NO_ARM');rejects(lambda:t.action({'target':'field-connect','commandId':'forbidden','reference':'DO_NOT_READ'}),'PERSISTENCE_BOOT05_NO_FLIGHT_COMMANDS');assert not calls
test('persistence_only_boot_refuses_connect_and_ARM_before_any_UI_file_or_input',persistence)
def close():
 t=make();t.start_host(command);t.close();assert t.host_process.poll()==0 and t.closed
test('actual_parent_close_terminates_only_owned_host_without_restoring_authority',close)
def cleanup_only():
 t=make();t.start_host(command);t.stop_host(command);assert t.host_process.poll()==0 and not t.host_restart_allowed;rejects(lambda:t.start_host(command),'NO_RESTART_AFTER_UNEXPECTED')
test('clean_cleanup_without_actual_replay_proof_doesnot_authorize_restart',cleanup_only)
def stale_proof():
 global proof_bad
 t=make();t.start_host(command);t.restart_authorization=dict(PROOF);proof_bad=True;t.stop_host(command);assert t.host_process.poll()==0 and not t.host_restart_allowed and t.restart_authorization is None
test('changed_proof_revalidated_before_stop_cleanup_allowed_restart_refused',stale_proof)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_BUILDER_G3_HOST_WINDOW_CONTROLLER_MOCK_ONLY'if all(r['status']=='PASS'for r in rows)else'FAIL','sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()},'rows':rows,'scope':'Actual Controller methods with fake Popen/process/fs/clock/socket and disabled fake Thread; actual replay proof checker isolated as fake contract and tested separately. No launch, network, UI, AP, emulator, actual sysctl or external writes. Host admission disk policy is separate; here admission wait advances fake30s to test original deadline spending.'}
out=Path(sys.argv[1]if len(sys.argv)>1 else'evidence/beta06/generation03/builder-host-window01.json');assert str(out).startswith('evidence/beta06/generation03/builder-')and not out.exists();out.open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'groups':len(rows),'failures':[r for r in rows if r['status']=='FAIL']}));assert result['status'].startswith('PASS')
