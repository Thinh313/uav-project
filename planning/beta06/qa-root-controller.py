"""Persistent Root-only explicit-command controller. Import/--plan performs no runtime action.
Anchors are sampled here, never recovered from JSON, UTC or another process.
"""
from pathlib import Path
import importlib.util,json,os,re,subprocess,sys,threading,time,uuid
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06'
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
g=module('beta_deadline','qa-deadline-guard.py')
def host_boot():
 v=subprocess.check_output(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],timeout=2,text=True).strip();assert re.fullmatch('[A-Fa-f0-9-]{36}',v),'ACTUAL_HOST_BOOT_ID_REQUIRED';return v
class Controller:
 def __init__(self,attempt,*,boot_reader=host_boot,clock=time.monotonic,ui=None,journal=None):
  assert attempt in ['01','02'];self.attempt=attempt;self.boot_reader=boot_reader;self.clock=clock;self.guard=g.DeadlineGuard(host_boot_id=boot_reader(),clock=clock);self.ui=ui;self.journal=journal;self.seen=set();self.dispatched=set();self.lock=threading.RLock();self.runtime=None;self.launch_error=None;self.closed=False;self.permit_thread=None
 def emit(self,event,**data):
  v={'event':event,'controllerPid':os.getpid(),'pythonMonoS':self.clock(),'attempt':self.attempt,**data}
  if self.journal:self.journal.write(json.dumps(v,separators=(',',':'))+'\n');self.journal.flush();os.fsync(self.journal.fileno())
  return v
 def snapshot(self):return {'anchors':self.guard.snapshot(),'launchError':self.launch_error,'controllerPid':os.getpid(),'noJsonAnchorRestore':True}
 def approved(self,c):
  assert c.get('rootApproved')is True,'ROOT_EXPLICIT_APPROVAL_REQUIRED';ident=c.get('commandId');assert isinstance(ident,str)and re.fullmatch('[a-z0-9-]{1,64}',ident),'UNIQUE_COMMAND_ID_REQUIRED';assert ident not in self.seen,'COMMAND_REPLAY_NO_RETRY';self.seen.add(ident);self.emit('EXPLICIT_COMMAND',commandId=ident,operation=c['op']);return ident
 def reserve(self,run):return self.guard.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=self.boot_reader())
 def closure_reserve(self):
  a=self.guard.snapshot()['emulatorBeforeLaunchPythonMonoS'];assert a is not None,'EMULATOR_ANCHOR_MISSING';remaining=g.EMULATOR_BUDGET_S-(self.clock()-a);assert remaining>=90,'CLOSURE_RESERVE_BELOW90S';return remaining
 def launch(self,c):
  assert self.runtime is None and self.guard.snapshot()['emulatorBeforeLaunchPythonMonoS']is None,'ONE_EMULATOR_LAUNCH_PER_CONTROLLER';log=(E/f'root-runtime{self.attempt}.txt').open('x');self.runtime=subprocess.Popen([sys.executable,str(Path(__file__).with_name('qa-runtime.py')),'--start',self.attempt,'--require-permit'],stdout=log,stderr=subprocess.STDOUT,cwd=R)
  def permit():
   try:
    end=self.clock()+85;ready=E/f'android-ready-to-launch{self.attempt}.json'
    while not ready.exists():
     assert not self.closed,'ROOT_CLOSED_BEFORE_LAUNCH';assert self.runtime.poll()is None,'RUNTIME_REFUSED_BEFORE_LAUNCH';assert self.clock()<end,'PRELAUNCH_READY_TIMEOUT';time.sleep(.05)
    with self.lock:
     assert not self.closed,'ROOT_CLOSED_BEFORE_LAUNCH';self.guard.anchor_emulator_before_launch('emulator-5582');proof=self.emit('EMULATOR_ANCHORED_BEFORE_PERMIT',anchors=self.guard.snapshot());p=E/f'android-launch-permit{self.attempt}.json'
     with p.open('x')as f:json.dump({'attempt':self.attempt,'clockBasis':g.CLOCK_BASIS,'rootControllerPid':os.getpid(),'anchorProof':proof},f);f.flush();os.fsync(f.fileno())
   except BaseException as e:self.launch_error=str(e);self.emit('LAUNCH_HANDSHAKE_FAILED',error=str(e))
  self.permit_thread=threading.Thread(target=permit,daemon=True);self.permit_thread.start();return {'status':'ADMISSION_PENDING_NO_UI_INPUT','pid':self.runtime.pid}
 def action(self,c):
  ui=self.ui or module('beta_ui','qa-ui.py');ident=c['target'];name=c['commandId'];timeout=c.get('timeout',12);assert 0<timeout<=100
  reference=c['reference'];intent='connect-'+name;assert name not in self.dispatched,'INPUT_INTENT_REPLAY_NO_RETRY';self.dispatched.add(name)
  readiness=module('beta_readiness','qa-airborne.py').wait_target_ready(json.loads(Path(reference).read_text()),ident,reader=ui.observation);self.emit('TARGET_READY_NO_INPUT',target=ident,sequence=readiness['observation']['seq'])
  def before_input(target,observation,*unused):
   # qa-ui passes its exact fresh observation captured immediately before the one tap.
   o=observation.get('observation',observation)
   if c.get('nativePickerHandoffOnly')is True or c.get('nativeDiagnosticHandoffOnly')is True:
    actual=unused[0]if unused else ui.q.state();assert not actual['flight'].get('run')and not actual['flight'].get('authority')and(actual.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'NATIVE_PICKER_GROUND_IDLE_BEFORE_INPUT'
   if target=='field-connect':
    assert c.get('groundStagedAndInspected')is True,'GROUND_SOURCE_VIEWER_CONFIG_REFERENCE_STAGING_REQUIRED';assert o.get('configId'),'VIEWER_CONFIG_BEFORE_AP_REQUIRED';self.guard.anchor_before_connect(intent);self.emit('CONNECT_ANCHORED_BEFORE_INPUT',intent=intent,anchors=self.guard.snapshot())
   elif target=='field-arm':self.emit('PRE_ARM_ENGINEERING_RESERVE',proof=self.reserve(o.get('run')))
  def after_input(target,*unused):
   if target=='field-connect':self.guard.note_connect_input_once(intent);self.emit('CONNECT_ONE_INPUT_RETURNED',intent=intent,anchors=self.guard.snapshot())
  result=ui.dispatch(self.attempt,reference,ident,name,timeout=timeout,before_input=before_input,after_input=after_input,handoff_only=c.get('nativePickerHandoffOnly')is True,diagnostic_only=c.get('nativeDiagnosticHandoffOnly')is True)
  if ident=='field-connect':
   run=ui.q.state()['flight'].get('run');self.guard.bind_observed_run(intent,run);self.emit('ACTUAL_RUN_BOUND_AFTER_ACK',anchors=self.guard.snapshot())
  return result
 def native_negative(self,c):
  ui=self.ui or module('beta_ui','qa-ui.py');state=ui.q.state();assert not state['flight'].get('run')and not state['flight'].get('authority')and(state.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'NATIVE_NEGATIVE_GROUND_IDLE_ONLY';before=ui.observation()['observation'];old=(before.get('nativeResult')or{}).get('seq',0);ack=self.action({**c,'target':'field-qa-bad-sha','nativeDiagnosticHandoffOnly':True});deadline=self.clock()+5
  while self.clock()<deadline:
   value=ui.receipt_observation(deadline);o=value['observation'];assert all(o.get(k)==before.get(k)for k in ['documentId','clientId','clientEpoch','clientInstance','run','boot','modelSha256','planSha256','configId']),'NATIVE_CALLBACK_CONTEXT_CHANGED';n=o.get('nativeResult')or{}
   if n.get('seq',0)>old:
    assert n.get('ok')is False and n.get('code')=='OPERATION_NOT_CONFIRMED'and'SHA256_MISMATCH'in n.get('message',''),'ACTUAL_NATIVE_SHA_REJECTION_REQUIRED';return {'uiDispatchIntentNotNativeResult':ack,'nativeCallback':n,'providerProof':False,'nativeJournalBeforeAfterStillRequired':True}
   time.sleep(.08)
  raise AssertionError('NATIVE_CALLBACK_MISSING_NO_RETRY')
 def complete_nominal(self,c):
  ui=self.ui or module('beta_ui','qa-ui.py');run=c['run'];assert re.fullmatch('s[a-f0-9]{20}',run);end=self.clock()+min(float(c.get('waitSeconds',120)),180)
  while self.clock()<end:
   self.closure_reserve();f=ui.q.state()['flight'];assert f.get('run')==run and not f.get('error')and not(f.get('live')or{}).get('failure'),'NOMINAL_CONTEXT_LOST'
   l=f.get('live')or{};o=ui.receipt_observation(end)['observation']
   if l.get('armed')is False and o.get('phase')=='DISARMED':
    # dispatch phase_policy independently requires completed navigation/near-home/disarm.
    return self.action({'op':'action','target':'field-close','reference':c['reference'],'commandId':c['commandId']+'-close','timeout':20})
   time.sleep(.25)
  raise AssertionError('NOMINAL_COMPLETION_TIMEOUT_NO_CLOSE_NO_RETRY')
 def command(self,c):
  assert isinstance(c,dict);op=c.get('op')
  if op=='status':return self.snapshot()
  self.approved(c)
  if op=='launch-emulator':return self.launch(c)
  if op=='action':return self.action(c)
  if op=='sequence':
   steps=c.get('steps');assert isinstance(steps,list)and 1<=len(steps)<=12,'BOUNDED_EXPLICIT_SEQUENCE_REQUIRED';results=[]
   for i,step in enumerate(steps):
    assert isinstance(step,dict);name=c['commandId']+'-'+str(i)
    if step.get('kind')=='airborne':
     assert i==len(steps)-1,'AIRBORNE_ONLY_EXPLICIT_LAST_STEP';a=module('beta_airborne','qa-airborne.py');results.append(a.run(self.attempt,step['flightReference'],step['payloadReference'],name,scenario=step.get('scenario','nominal'),dispatch=lambda target,ref,action,timeout:self.action({'target':target,'reference':ref,'commandId':action,'timeout':timeout}),reserve=self.reserve))
    else:results.append(self.action({**step,'commandId':name}))
   return results
  if op=='airborne':
   a=module('beta_airborne','qa-airborne.py');return a.run(self.attempt,c['flightReference'],c['payloadReference'],c['commandId'],scenario=c.get('scenario','nominal'),dispatch=lambda target,ref,name,timeout:self.action({'op':'action','target':target,'reference':ref,'commandId':name,'timeout':timeout}),reserve=self.reserve)
  if op in ['setup','start','store-before','store-after']:
   if op=='store-after':self.emit('BEFORE_STORE_AFTER_RESERVE',remainingS=self.closure_reserve())
   d=module('beta_device','qa-device-actions.py');return d.run(self.attempt,op,c.get('variant',''),before_receipt=c.get('beforeReceipt'))
  if op=='native-picker':
   ui=self.ui or module('beta_ui','qa-ui.py');s=ui.q.state();assert not s['flight'].get('run')and not s['flight'].get('authority')and(s.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'NATIVE_PICKER_GROUND_IDLE_ONLY';return self.action({**c,'nativePickerHandoffOnly':True})
  if op=='native-negative':return self.native_negative(c)
  if op=='complete-nominal':return self.complete_nominal(c)
  if op=='prepare':
   ui=self.ui or module('beta_ui','qa-ui.py');return ui.prepare(self.attempt,c['name'],c['nativeFrame'])
  if op=='stop-emulator':
   p=E/f'android-stop-request{self.attempt}.json';p.open('x').write(json.dumps({'explicitRootCommand':c['commandId'],'noRestart':True}));return {'stopRequested':True}
  raise AssertionError('EXPLICIT_COMMAND_ALLOWLIST')
 def close(self):
  self.closed=True
  if self.permit_thread is not None and hasattr(self.permit_thread,'join'):self.permit_thread.join(timeout=1)
  if self.runtime is not None:
   p=E/f'android-stop-request{self.attempt}.json'
   if not p.exists():
    with p.open('x')as f:json.dump({'reason':'PERSISTENT_ROOT_CONTROLLER_CLOSED_NO_RESTART','rootControllerPid':os.getpid()},f);f.flush();os.fsync(f.fileno())
   self.emit('OWN_RUNTIME_STOP_REQUEST_ON_CONTROLLER_CLOSE',runtimePid=self.runtime.pid)
def plan():return {'persistentProcessRequired':True,'commands':['status','launch-emulator','setup','start','store-before','store-after','prepare','action','sequence','airborne','complete-nominal','native-negative','native-picker','stop-emulator'],'attempts':['01','02'],'emulatorSeconds':1800,'connectIntentsPerBoot':2,'apBudgetSeconds':540,'preArmApReserveSeconds':225,'preArmEmulatorReserveSeconds':240,'storeAfterReserveSeconds':90,'anchorSource':'THIS_PYTHON_PROCESS_BEFORE_LAUNCH_PERMIT_AND_BEFORE_CONNECT_TAP','restoreAnchorsFromJson':False,'automaticUiInput':False,'dispatchRetry':False}
if __name__=='__main__':
 if sys.argv[1:]==['--plan']:print(json.dumps(plan(),indent=2))
 else:
  assert len(sys.argv)==3 and sys.argv[1]=='--serve'and sys.argv[2]in['01','02'];E.mkdir(parents=True,exist_ok=True)
  with(E/f'root-controller{sys.argv[2]}.jsonl').open('x')as j:
   ctl=Controller(sys.argv[2],journal=j);ctl.emit('NEW_PROCESS_NO_RESTORED_ANCHORS',plan=plan())
   try:
    for line in sys.stdin:
     try:
      assert len(line)<=8192;v=ctl.command(json.loads(line));print(json.dumps({'ok':True,'result':v},default=str),flush=True)
     except BaseException as e:ctl.emit('COMMAND_REFUSED_NO_AUTOMATIC_RETRY',error=str(e));print(json.dumps({'ok':False,'error':str(e)}),flush=True)
   finally:ctl.close()
