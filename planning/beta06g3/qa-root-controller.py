"""Persistent Root-only explicit-command controller. Import/--plan performs no runtime action.
Anchors are sampled here, never recovered from JSON, UTC or another process.
"""
from pathlib import Path
import importlib.util,json,os,re,subprocess,sys,threading,time,uuid,hashlib,shutil,math,socket
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation03'
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
g=module('beta_deadline','qa-deadline-guard.py')
def host_boot():
 v=subprocess.check_output(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],timeout=2,text=True).strip();assert re.fullmatch('[A-Fa-f0-9-]{36}',v),'ACTUAL_HOST_BOOT_ID_REQUIRED';return v
class Controller:
 def __init__(self,attempt,*,boot_reader=host_boot,clock=time.monotonic,ui=None,journal=None):
  assert attempt=='04';self.attempt=attempt;self.boot_reader=boot_reader;self.clock=clock;self.guard=g.DeadlineGuard(host_boot_id=boot_reader(),clock=clock);self.ui=ui;self.journal=journal;self.seen=set();self.dispatched=set();self.lock=threading.RLock();self.runtime=None;self.launch_error=None;self.closed=False;self.permit_thread=None;self.host_anchor=None;self.host_thread=None;self.persistence_only=False;self.ground_admission=None;self.host_boot_id=self.guard.snapshot()['hostBootId'];self.host_process=None;self.host_out=None;self.host_log=None;self.host_instances=0;self.host_restart_allowed=False;self.host_stop_proof=None;self.restart_authorization=None;self.launch_consumed=set();self.campaign_failed=False;self.connect_count=0;self.campaign_runs=[]
 def emit(self,event,**data):
  v={'event':event,'controllerPid':os.getpid(),'pythonMonoS':self.clock(),'attempt':self.attempt,**data}
  if self.journal:self.journal.write(json.dumps(v,separators=(',',':'))+'\n');self.journal.flush();os.fsync(self.journal.fileno())
  return v
 def snapshot(self):return {'anchors':self.guard.snapshot(),'launchError':self.launch_error,'controllerPid':os.getpid(),'hostBeforeLaunchPythonMonoS':self.host_anchor,'hostRemainingS':self.host_remaining()if self.host_anchor is not None else None,'persistenceOnly':self.persistence_only,'hostInstances':self.host_instances,'hostPid':self.host_process.pid if self.host_process else None,'hostRestartAllowed':self.host_restart_allowed,'noJsonAnchorRestore':True,'connectCount':self.connect_count,'campaignRuns':self.campaign_runs,'campaignFailed':self.campaign_failed,'launchConsumed':sorted(self.launch_consumed)}
 def approved(self,c):
  assert c.get('rootApproved')is True,'ROOT_EXPLICIT_APPROVAL_REQUIRED';ident=c.get('commandId');assert isinstance(ident,str)and re.fullmatch('[a-z0-9-]{1,64}',ident),'UNIQUE_COMMAND_ID_REQUIRED';assert ident not in self.seen,'COMMAND_REPLAY_NO_RETRY';self.seen.add(ident);self.emit('EXPLICIT_COMMAND',commandId=ident,operation=c['op']);return ident
 def reserve(self,run):
  assert not self.persistence_only,'PERSISTENCE_BOOT05_NO_ARM';assert self.host_process is not None and self.host_process.poll()is None,'CURRENT_OWNED_HOST_NOT_LIVE';remaining=self.host_remaining();assert remaining>=240,'HOST_REMAINING_BELOW240S_NO_ARM';proof=self.guard.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=self.boot_reader());return{**proof,'hostBeforeLaunchPythonMonoS':self.host_anchor,'hostRemainingConservativeS':remaining}
 def closure_reserve(self):
  a=self.guard.snapshot()['emulatorBeforeLaunchPythonMonoS'];assert a is not None,'EMULATOR_ANCHOR_MISSING';remaining=min(g.EMULATOR_BUDGET_S-(self.clock()-a),self.host_remaining());assert remaining>=90,'CLOSURE_RESERVE_BELOW90S';return remaining
 def host_remaining(self):
  assert self.host_anchor is not None,'PRELAUNCH_HOST_ANCHOR_MISSING';now=g.finite_time(self.clock());assert now>=self.host_anchor,'HOST_ANCHOR_FUTURE';return 1800-(now-self.host_anchor)
 def anchor_host(self):
  assert self.host_anchor is None and self.runtime is None,'HOST_ANCHOR_SINGLE_BEFORE_LAUNCH_NO_RESET';self.host_anchor=g.finite_time(self.clock());self.emit('HOST_ANCHORED_BEFORE_ROOT_LAUNCH',hostBeforeLaunchPythonMonoS=self.host_anchor,hardDurationS=1800)
  def watch():
   while not self.closed:
    if self.host_remaining()<=0:
     self.emit('HOST_ORIGINAL_DEADLINE_REACHED_STOP_OWN_EMULATOR');self.close();break
    time.sleep(.1)
  self.host_thread=threading.Thread(target=watch,daemon=True);self.host_thread.start();return self.snapshot()
 def start_host(self,c):
  assert self.host_instances<2 and(self.host_process is None or self.host_process.poll()is not None),'TWO_HOST_INSTANCES_ONE_WINDOW_MAX';assert self.host_instances==0 or self.host_restart_allowed,'NO_RESTART_AFTER_UNEXPECTED_EXIT_OR_FAILURE';assert c.get('sourceAndViewerStoppedAndInspected')is True,'ROOT_SOURCE_AND_VIEWER_GROUND_INSPECTION_REQUIRED'
  runtime=module('g2_host_admission','qa-runtime.py');samples=[];admission_path=E/('host-admission-'+c['commandId']+'.json');report={'status':'REFUSED_BEFORE_HOST_POPEN','samples':samples}
  try:
   for n in range(31):
    samples.append({'mono':self.clock(),'free':shutil.disk_usage(R).free});assert samples[-1]['free']>=29*2**30,'HOST_ADMISSION29GIB'
    if n<30:time.sleep(1)
   runtime.budget_decision(samples);report['status']='PASS_HOST_ADMISSION_BEFORE_POPEN'
  except BaseException as e:report['error']=str(e);raise
  finally:
   with admission_path.open('x')as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
  for port in [8872,8873]:
   with socket.socket()as sock:sock.bind(('127.0.0.1',port))
  if self.host_anchor is None:self.anchor_host()
  remaining=self.host_remaining();assert remaining>=240,'HOST_REMAINING_BELOW240_NO_POPEN';out=E/('host-app03'if self.host_instances==0 else'host-app03-restart');assert not out.exists(),'HOST_OUTPUT_ALREADY_EXISTS_NO_RETRY';workspace=(E/'workspace01').resolve();assert workspace.is_dir()and not workspace.is_symlink(),'ROOT_VERIFIED_GENERATION03_WORKSPACE_REQUIRED';self.host_log=(E/('host-console'+str(self.host_instances+1)+'.txt')).open('x');env={**os.environ,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid()),'BETA06_PARENT_HOST_REMAINING_MS':str(math.floor(remaining*1000))};self.emit('HOST_POPEN_INTENT_ANCHOR_ALREADY_CAPTURED',hostAnchorPythonMonoS=self.host_anchor,remainingMs=math.floor(remaining*1000),output=str(out),instanceOrdinal=self.host_instances+1);self.host_instances+=1;self.host_restart_allowed=False;self.restart_authorization=None;self.ground_admission=None;self.host_out=out;self.host_process=subprocess.Popen(['node',str(R/'pilot/beta06g3/app.mjs'),str(out),'--allow-sitl','--workspace='+str(workspace)],cwd=R,env=env,stdout=self.host_log,stderr=subprocess.STDOUT);self.emit('OWNED_HOST_PROCESS_STARTED',pid=self.host_process.pid,output=str(out),originalHostAnchorPythonMonoS=self.host_anchor);return self.snapshot()
 def stop_host(self,c):
  assert self.host_process is not None and self.host_process.poll()is None,'OWNED_HOST_ALREADY_EXITED_NO_MANAGED_RETRY';ui=self.ui or module('g2_stop_host_ui','qa-ui.py');state=ui.q.state();assert not state['flight'].get('run')and not state['flight'].get('authority')and not state['flight'].get('busy')and(state.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'CLOSE_RUN_AND_REVOKE_ALL_AUTHORITY_BEFORE_HOST_STOP';assert c.get('sourceAndViewerStoppedAndInspected')is True and(ui.observation()['observation'].get('mediaReadiness')or{}).get('active')is False,'EXPLICIT_SOURCE_VIEWER_STOP_REQUIRED';
  if self.restart_authorization is not None:
   try:
    refreshed=module('g2_restart_recheck','qa-restart-proof.py').authorize(self.restart_authorization['nominalReport'],self.restart_authorization['faultReport']);assert refreshed==self.restart_authorization,'RESTART_PROOF_CHANGED_BEFORE_STOP'
   except BaseException as e:self.restart_authorization=None;self.emit('RESTART_PROOF_REFUSED_CLEANUP_ONLY',error=str(e))
  pid=self.host_process.pid;self.emit('EXPLICIT_MANAGED_HOST_STOP_INTENT',pid=pid);self.host_process.terminate();code=self.host_process.wait(timeout=20);closure=self.host_out/'app-closure.json';assert code==0 and closure.is_file()and not closure.is_symlink(),'CLEAN_HOST_CLOSURE_REQUIRED_NO_RESTART';body=closure.read_bytes();value=json.loads(body);assert value.get('payloadEvidenceFailure')is None and value.get('reason')=='EXPLICIT_STOP','HOST_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';self.host_stop_proof={'pid':pid,'exit':code,'closure':str(closure),'sha256':hashlib.sha256(body).hexdigest(),'observedPythonMonoS':self.clock()};self.host_restart_allowed=self.host_instances==1 and self.restart_authorization is not None;self.ground_admission=None;self.emit('MANAGED_HOST_STOP_VERIFIED',**self.host_stop_proof);self.host_log.close();return self.host_stop_proof
 def persistence_boot(self,c):
  assert self.attempt=='04'and self.runtime is not None and self.runtime.poll()is not None and(E/'android-closure04.json').exists(),'BOOT04_MUST_BE_CLOSED_BEFORE05';assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_NO_PERSISTENCE_BOOT';assert not(E/'android-attempt05.json').exists(),'BOOT05_ALREADY_CONSUMED';self.emit('EXPLICIT_PERSISTENCE_BOOT05_NEW_EMULATOR_ANCHOR_OLD_HOST_DEADLINE',priorEmulatorAnchors=self.guard.snapshot());self.attempt='05';self.persistence_only=True;self.guard=g.DeadlineGuard(host_boot_id=self.host_boot_id,clock=self.clock);self.runtime=None;self.permit_thread=None;self.launch_error=None;return self.launch(c)
 def launch(self,c):
  assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_NO_EMULATOR_LAUNCH';assert self.attempt not in self.launch_consumed,'EMULATOR_LAUNCH_ATTEMPT_CONSUMED_NO_RETRY';self.launch_consumed.add(self.attempt);assert self.runtime is None and self.guard.snapshot()['emulatorBeforeLaunchPythonMonoS']is None,'ONE_EMULATOR_LAUNCH_PER_CONTROLLER';log=(E/f'root-runtime{self.attempt}.txt').open('x');argv=[sys.executable,str(Path(__file__).with_name('qa-runtime.py')),'--start',self.attempt,'--require-permit'];self.emit('EMULATOR_HELPER_POPEN_INTENT',argv=argv)
  try:self.runtime=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,cwd=R)
  except BaseException as e:
   self.launch_error=str(e);log.write('PARENT_POPEN_ERROR '+repr(e)+'\n');log.flush();os.fsync(log.fileno());log.close();self.emit('EMULATOR_HELPER_POPEN_FAILED_NO_RETRY',error=str(e),argv=argv);raise
  log.close()
  def permit():
   try:
    end=self.clock()+85;ready=E/f'android-ready-to-launch{self.attempt}.json'
    while not ready.exists():
     assert not self.closed,'ROOT_CLOSED_BEFORE_LAUNCH';assert self.runtime.poll()is None,'RUNTIME_REFUSED_BEFORE_LAUNCH';assert self.clock()<end,'PRELAUNCH_READY_TIMEOUT';time.sleep(.05)
    with self.lock:
     assert not self.closed,'ROOT_CLOSED_BEFORE_LAUNCH';assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_BEFORE_ACTUAL_BOOT';self.guard.anchor_emulator_before_launch('emulator-5582');proof=self.emit('EMULATOR_ANCHORED_BEFORE_PERMIT',anchors=self.guard.snapshot());p=E/f'android-launch-permit{self.attempt}.json'
     with p.open('x')as f:json.dump({'attempt':self.attempt,'clockBasis':g.CLOCK_BASIS,'rootControllerPid':os.getpid(),'anchorProof':proof,'parentHostRemainingS':self.host_remaining(),'hostBeforeLaunchPythonMonoS':self.host_anchor,'parentHostDeadlinePythonMonoS':self.host_anchor+1800},f);f.flush();os.fsync(f.fileno())
   except BaseException as e:self.launch_error=str(e);self.emit('LAUNCH_HANDSHAKE_FAILED',error=str(e))
  self.permit_thread=threading.Thread(target=permit,daemon=True);self.permit_thread.start();return {'status':'ADMISSION_PENDING_NO_UI_INPUT','pid':self.runtime.pid}
 def action(self,c):
  ui=self.ui or module('beta_ui','qa-ui.py');ident=c['target'];name=c['commandId'];
  if self.persistence_only:assert ident in ['field-tab-flight','field-tab-payload','field-tab-review','field-export-workspace','field-import-workspace','field-qa-bad-sha','video-stop','field-refresh']or re.fullmatch(r'field-(?:raw|delivery)-s[a-f0-9]{20}|field-capture-export-[a-zA-Z0-9-]{1,48}-[a-f0-9]{12}|field-delivery-file-s[a-f0-9]{20}-[a-zA-Z0-9-]{1,64}',ident),'PERSISTENCE_BOOT05_NO_FLIGHT_COMMANDS';
  timeout=c.get('timeout',100 if ident=='field-connect'else 12);assert ident!='field-connect'or timeout==100,'CONNECT_RECEIPT100S_REQUIRED';assert 0<timeout<=100
  reference=c['reference'];intent='connect-'+name;assert name not in self.dispatched,'INPUT_INTENT_REPLAY_NO_RETRY';self.dispatched.add(name)
  readiness=module('beta_readiness','qa-airborne.py').wait_target_ready(json.loads(Path(reference).read_text()),ident,reader=ui.observation);self.emit('TARGET_READY_NO_INPUT',target=ident,sequence=readiness['observation']['seq'])
  def before_input(target,observation,*unused):
   # qa-ui passes its exact fresh observation captured immediately before the one tap.
   o=observation.get('observation',observation)
   if c.get('nativePickerHandoffOnly')is True or c.get('nativeDiagnosticHandoffOnly')is True:
    actual=unused[0]if unused else ui.q.state();assert not actual['flight'].get('run')and not actual['flight'].get('authority')and(actual.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'NATIVE_PICKER_GROUND_IDLE_BEFORE_INPUT'
   if target=='field-connect':
    assert not self.campaign_failed,'FAILED_OR_UNCERTAIN_CAMPAIGN_NO_NEW_AP';assert self.connect_count<4,'FOUR_NEW_CONNECTS_MAX_BEFORE_INPUT';assert self.host_instances==(1 if self.connect_count<2 else 2),'N1_F1_BEFORE_MANAGED_RESTART_N2_F2_AFTER';assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_NO_AP';assert self.ground_admission is not None,'GROUND75S_ADMISSION_REQUIRED';admitted=self.ground_admission['binding'];ground=module('g2_ground_current','qa-ground-soak.py');actual=unused[0]if unused else ui.q.state();ground.sample_decision(observation,actual,admitted,{'counts':self.ground_admission['baselineCounts'],'clockSessionId':self.ground_admission['clockSessionId']});assert all(o.get(k)==admitted.get(k)for k in ['documentId','clientId','clientEpoch','clientInstance','configId','modelSha256','planSha256']),'GROUND_ADMISSION_CONTEXT_CHANGED';assert c.get('groundStagedAndInspected')is True,'GROUND_SOURCE_VIEWER_CONFIG_REFERENCE_STAGING_REQUIRED';assert o.get('configId'),'VIEWER_CONFIG_BEFORE_AP_REQUIRED';self.guard.anchor_before_connect(intent);self.connect_count+=1;self.ground_admission=None;self.emit('CONNECT_ANCHORED_BEFORE_INPUT',intent=intent,anchors=self.guard.snapshot())
   elif target=='field-arm':self.emit('PRE_ARM_ENGINEERING_RESERVE',proof=self.reserve(o.get('run')))
  def after_input(target,*unused):
   if target=='field-connect':self.guard.note_connect_input_once(intent);self.emit('CONNECT_ONE_INPUT_RETURNED',intent=intent,anchors=self.guard.snapshot())
  try:
   result=ui.dispatch(self.attempt,reference,ident,name,timeout=timeout,before_input=before_input,after_input=after_input,handoff_only=c.get('nativePickerHandoffOnly')is True,diagnostic_only=c.get('nativeDiagnosticHandoffOnly')is True)
   if ident=='field-connect':
    run=ui.q.state()['flight'].get('run');self.guard.bind_observed_run(intent,run);self.campaign_runs.append(run);self.emit('ACTUAL_RUN_BOUND_AFTER_ACK',anchors=self.guard.snapshot(),scenario=['N1','F1','N2','F2'][self.connect_count-1])
  except BaseException as e:
   if ident=='field-connect' or self.connect_count:self.campaign_failed=True;self.emit('CAMPAIGN_FAILED_OR_UNCERTAIN_NO_NEW_AP',target=ident,error=str(e))
   raise
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
  try:return self._command(c)
  except BaseException as e:
   if isinstance(c,dict)and c.get('op')in ['action','airborne','sequence','complete-nominal']and(self.connect_count or c.get('target')=='field-connect'):self.campaign_failed=True;self.emit('SCENARIO_FAILED_NO_NEW_AP',operation=c.get('op'),error=str(e))
   raise
 def scenario(self,scenario):
  assert not self.persistence_only,'PERSISTENCE_BOOT05_NO_AIRBORNE';assert self.connect_count>0,'CONNECT_BEFORE_AIRBORNE';expected=['nominal','cut','nominal','reboot'][self.connect_count-1];assert scenario==expected,'FINITE_SCENARIO_ORDER_N1_F1_N2_F2';assert not self.campaign_failed,'FAILED_OR_UNCERTAIN_CAMPAIGN_NO_AIRBORNE';return scenario
 def _command(self,c):
  assert isinstance(c,dict);op=c.get('op')
  if op=='status':return self.snapshot()
  self.approved(c)
  if op=='authorize-managed-restart':
   assert c.get('rootInspectedActualReplay')is True and self.host_instances==1,'EXPLICIT_ACTUAL_REPLAY_INSPECTION_REQUIRED';proof=module('g2_restart_proof','qa-restart-proof.py').authorize(c['nominalReplay'],c['faultReplay']);self.restart_authorization=proof;self.emit('ACTUAL_NOMINAL_AND_FAULT_RESTART_PROVENANCE',proof=proof);return proof
  if op=='start-host':return self.start_host(c)
  if op=='stop-host':return self.stop_host(c)
  if op=='anchor-host-before-launch':return self.anchor_host()
  if op=='launch-emulator':return self.launch(c)
  if op=='launch-persistence-emulator':return self.persistence_boot(c)
  if op=='ground-soak':
   assert not self.persistence_only,'PERSISTENCE_BOOT05_NO_AP_ADMISSION';a=module('g2_ground','qa-ground-soak.py');self.ground_admission=None;result=a.collect(c['commandId'],c['clockJournal'],clock=self.clock);self.ground_admission=result;return result
  if op=='action':return self.action(c)
  if op=='sequence':
   steps=c.get('steps');assert isinstance(steps,list)and 1<=len(steps)<=12,'BOUNDED_EXPLICIT_SEQUENCE_REQUIRED';results=[]
   for i,step in enumerate(steps):
    assert isinstance(step,dict);name=c['commandId']+'-'+str(i)
    if step.get('kind')=='airborne':
     assert i==len(steps)-1,'AIRBORNE_ONLY_EXPLICIT_LAST_STEP';assert not self.persistence_only,'PERSISTENCE_BOOT05_NO_AIRBORNE';a=module('beta_airborne','qa-airborne.py');results.append(a.run(self.attempt,step['flightReference'],step['payloadReference'],name,scenario=self.scenario(step.get('scenario','nominal')),dispatch=lambda target,ref,action,timeout:self.action({'target':target,'reference':ref,'commandId':action,'timeout':timeout}),reserve=self.reserve))
    else:results.append(self.action({**step,'commandId':name}))
   return results
  if op=='airborne':
   assert not self.persistence_only,'PERSISTENCE_BOOT05_NO_AIRBORNE';a=module('beta_airborne','qa-airborne.py');return a.run(self.attempt,c['flightReference'],c['payloadReference'],c['commandId'],scenario=self.scenario(c.get('scenario','nominal')),dispatch=lambda target,ref,name,timeout:self.action({'op':'action','target':target,'reference':ref,'commandId':name,'timeout':timeout}),reserve=self.reserve)
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
   p=E/f'android-stop-request{self.attempt}.json';
   with p.open('x')as f:json.dump({'explicitRootCommand':c['commandId'],'noRestart':True},f);f.flush();os.fsync(f.fileno())
   return {'stopRequested':True}
  raise AssertionError('EXPLICIT_COMMAND_ALLOWLIST')
 def close(self):
  self.closed=True
  if self.host_process is not None and self.host_process.poll()is None:
   self.emit('STOP_OWNED_HOST_ON_PARENT_CLOSE',pid=self.host_process.pid);self.host_process.terminate()
   try:self.host_process.wait(timeout=20)
   except subprocess.TimeoutExpired:self.emit('OWNED_HOST_CLOSE_UNKNOWN_FORCED_KILL',pid=self.host_process.pid);self.host_process.kill();self.host_process.wait(timeout=5)
  if self.host_log is not None and not self.host_log.closed:self.host_log.close()
  if self.permit_thread is not None and hasattr(self.permit_thread,'join'):self.permit_thread.join(timeout=1)
  if self.runtime is not None:
   p=E/f'android-stop-request{self.attempt}.json'
   if not p.exists():
    with p.open('x')as f:json.dump({'reason':'PERSISTENT_ROOT_CONTROLLER_CLOSED_NO_RESTART','rootControllerPid':os.getpid()},f);f.flush();os.fsync(f.fileno())
   self.emit('OWN_RUNTIME_STOP_REQUEST_ON_CONTROLLER_CLOSE',runtimePid=self.runtime.pid)
   try:self.runtime.wait(timeout=35)
   except subprocess.TimeoutExpired:
    self.emit('OWNED_RUNTIME_CLOSURE_TIMEOUT_UNKNOWN',runtimePid=self.runtime.pid);self.runtime.terminate()
    try:self.runtime.wait(timeout=20)
    except subprocess.TimeoutExpired:self.emit('OWNED_RUNTIME_CLOSURE_STILL_UNKNOWN',runtimePid=self.runtime.pid)
def plan():return {'persistentProcessRequired':True,'commands':['status','authorize-managed-restart','start-host','stop-host','anchor-host-before-launch','launch-emulator','launch-persistence-emulator','setup','start','store-before','store-after','prepare','ground-soak','action','sequence','airborne','complete-nominal','native-negative','native-picker','stop-emulator'],'attempts':['04','05'],'emulatorSeconds':1800,'newConnectIntentsBoot04':4,'connectIntentsBoot05':0,'hostBudgetSecondsAcrossBothBoots':1800,'apBudgetSeconds':540,'preArmApReserveSeconds':225,'preArmEmulatorReserveSeconds':240,'storeAfterReserveSeconds':90,'anchorSource':'THIS_PYTHON_PROCESS_BEFORE_LAUNCH_PERMIT_AND_BEFORE_CONNECT_TAP','restoreAnchorsFromJson':False,'automaticUiInput':False,'dispatchRetry':False}
if __name__=='__main__':
 if sys.argv[1:]==['--plan']:print(json.dumps(plan(),indent=2))
 else:
  assert len(sys.argv)==3 and sys.argv[1]=='--serve'and sys.argv[2]=='04';E.mkdir(parents=True,exist_ok=True)
  with(E/f'root-controller{sys.argv[2]}.jsonl').open('x')as j:
   ctl=Controller(sys.argv[2],journal=j);ctl.emit('NEW_PROCESS_NO_RESTORED_ANCHORS',plan=plan())
   try:
    while True:
     line=sys.stdin.buffer.readline(8193)
     if not line:break
     try:
      assert len(line)<=8192 and line.endswith(b'\n'),'COMMAND_LINE_BOUND8192_NO_PARTIAL_PARSE';v=ctl.command(json.loads(line));print(json.dumps({'ok':True,'result':v},default=str),flush=True)
     except BaseException as e:
      ctl.emit('COMMAND_REFUSED_NO_AUTOMATIC_RETRY',error=str(e));print(json.dumps({'ok':False,'error':str(e)}),flush=True)
      if len(line)>8192 or not line.endswith(b'\n'):break
   finally:ctl.close()
