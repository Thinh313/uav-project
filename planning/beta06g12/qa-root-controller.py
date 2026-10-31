"""Persistent Root-only explicit-command controller. Import/--plan performs no runtime action.
Anchors are sampled here, never recovered from JSON, UTC or another process.
"""
from pathlib import Path
import importlib.util,sys
if 'g12_native_writer'not in sys.modules:
 _w=importlib.util.spec_from_file_location('g12_native_writer',Path(__file__).with_name('qa-native-budget.py'));b=importlib.util.module_from_spec(_w);sys.modules[_w.name]=b;_w.loader.exec_module(b)
else:b=sys.modules['g12_native_writer']
import importlib.util,json,os,re,subprocess,sys,threading,time,uuid,hashlib,shutil,math,socket
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation12'
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
g=module('beta_deadline','qa-deadline-guard.py')
def host_boot():
 v=subprocess.check_output(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],timeout=2,text=True).strip();assert re.fullmatch('[A-Fa-f0-9-]{36}',v),'ACTUAL_HOST_BOOT_ID_REQUIRED';return v
class CompletionPollDiagnostics:
 """Bounded concurrent-read decision evidence, no control/authority operation."""
 MAX_BYTES=4*2**20;MAX_POLL_BYTES=32*2**10;MAX_POLLS=721;MAX_SNAPSHOT_BYTES=128*2**10
 def __init__(self,prefix,clock,host_boot_id=None):
  self.prefix=prefix;self.clock=clock;self.host_boot_id=host_boot_id;self.count=0;self.bytes=0;self.head='0'*64;self.last=None;self.saved=False;self.file=b.BoundedFile(E/(prefix+'-completion-polls.jsonl'),self.MAX_BYTES,kind='completion-journal');self.closed=False
 def append(self,kind,data):
  body={'seq':self.count+1,'previousSha256':self.head,'pythonMonoS':self.clock(),'clockBasis':b.host_clock.BASIS,'hostBootId':self.host_boot_id,'kind':kind,'data':data};encoded=json.dumps(body,separators=(',',':'),allow_nan=False).encode();head=hashlib.sha256(encoded).hexdigest();raw=encoded[:-1]+b',"sha256":"'+head.encode()+b'"}\n';assert len(raw)<=self.MAX_POLL_BYTES,'COMPLETION_DIAGNOSTIC_POLL32KIB_BOUND';assert self.bytes+len(raw)<=self.MAX_BYTES,'COMPLETION_DIAGNOSTIC4MIB_BOUND';assert self.count<self.MAX_POLLS+4,'COMPLETION_DIAGNOSTIC_RECORD_BOUND';self.file.write(raw.decode());self.file.flush();os.fsync(self.file.fileno());self.count+=1;self.bytes+=len(raw);self.head=head
 def capture(self,state,view,timing):
  flight=state.get('flight')or{};live=flight.get('live')or{};request=flight.get('request')or{};client=state.get('client')or{}
  projected={'ok':state.get('ok'),'client':{k:client.get(k)for k in ['id','epoch','instance','active','ageMs']},'flight':{k:flight.get(k)for k in ['run','mode','error','writerError','positionAgeMs']}}
  projected['flight']['request']={k:request.get(k)for k in ['run','boot','modelSha256','planSha256']};projected['flight']['live']={k:live.get(k)for k in ['armed','boot','simulation','failure','mode','stage','heartbeatAgeMs','completion']}
  o=view.get('observation')or{};compact_view={k:view.get(k)for k in ['ok','ageMs','issuedAtHostMonoMs','receivedAtHostMonoMs','ageBasis']};compact_view['observation']={k:o.get(k)for k in ['documentId','clientId','clientEpoch','clientInstance','run','boot','configId','modelSha256','planSha256','foreground','phase','seq','observedAtClientMonoMs']}
  exact_state=json.dumps(state,separators=(',',':'),allow_nan=False).encode();exact_view=json.dumps(view,separators=(',',':'),allow_nan=False).encode();assert len(exact_state)<=2*2**20 and len(exact_view)<=128*2**10,'COMPLETION_INPUT_BOUND'
  self.last={'clockBasis':b.host_clock.BASIS,'hostBootId':self.host_boot_id,'classification':'SAME_POLL_SEQUENTIAL_READS_EXACT_DECISION_PROJECTION_NOT_ATOMIC_FULL_STATE','state':projected,'view':view,'timing':timing,'fullStateAtReadSha256':hashlib.sha256(exact_state).hexdigest(),'fullViewAtReadSha256':hashlib.sha256(exact_view).hexdigest(),'omittedStateFields':'Nondecision workspace/media/history fields omitted; digest binds exact state returned in this poll.'}
  self.append('COMPLETION_POLL',{'state':projected,'view':compact_view,'timing':timing,'fullStateAtReadSha256':self.last['fullStateAtReadSha256'],'fullViewAtReadSha256':self.last['fullViewAtReadSha256'],'notAtomic':True})
 def save_last(self):
  if self.saved or self.last is None:return
  raw=json.dumps(self.last,indent=2,allow_nan=False).encode();assert len(raw)<=self.MAX_SNAPSHOT_BYTES,'COMPLETION_LAST_INPUTS128KIB_BOUND'
  b.write_bytes(E/(self.prefix+'-completion-last-inputs.json'),raw,maximum=self.MAX_SNAPSHOT_BYTES,kind='completion-last')
  self.saved=True
 def close(self,status,error=None):
  if self.closed:return
  self.save_last();self.file.flush();os.fsync(self.file.fileno());self.file.close();self.closed=True
  summary={'classification':'ROOT_COMPLETION_READ_DIAGNOSTICS_NOT_FLIGHT_ACCEPTANCE','status':status,'errorClass':type(error).__name__ if error is not None else None,'error':str(error)[:256]if error is not None else None,'records':self.count,'bytes':self.bytes,'head':self.head,'pollJournal':self.prefix+'-completion-polls.jsonl','lastInputsSaved':self.saved,'maximumBytes':self.MAX_BYTES,'maximumSnapshotBytes':self.MAX_SNAPSHOT_BYTES,'noRetry':True,'noAuthorityRestore':True}
  b.write_json(E/(self.prefix+'-completion-summary.json'),summary,maximum=64*2**10,kind='completion-summary',closure=True)

class Controller:
 def __init__(self,attempt,*,boot_reader=host_boot,clock=b.host_clock.now_s,ui=None,journal=None):
  assert attempt=='24';self.attempt=attempt;self.boot_reader=boot_reader;self.clock=clock;self.guard=g.DeadlineGuard(host_boot_id=boot_reader(),clock=clock);self.ui=ui;self.journal=journal;self.seen=set();self.dispatched=set();self.lock=threading.RLock();self.runtime=None;self.launch_error=None;self.closed=False;self.permit_thread=None;self.host_anchor=None;self.host_thread=None;self.persistence_only=False;self.ground_admission=None;self.host_boot_id=self.guard.snapshot()['hostBootId'];self.host_process=None;self.host_out=None;self.host_log=None;self.host_instances=0;self.host_restart_allowed=False;self.host_stop_proof=None;self.restart_authorization=None;self.launch_consumed=set();self.campaign_failed=False;self.connect_count=0;self.campaign_runs=[];self.ground_failure=None;self.ground_recovery_authorized=False;self.ground_recovery_used=False;self.persistence_stop_proof=None;self.host_capture=None;self.runtime_capture=None;self.prepare_count=0;self.cleanup_journal=None
 def emit(self,event,**data):
  v={'event':event,'controllerPid':os.getpid(),'pythonMonoS':self.clock(),'clockBasis':g.CLOCK_BASIS,'hostBootId':self.host_boot_id,'attempt':self.attempt,**data}
  if self.journal:self.journal.write(json.dumps(v,separators=(',',':'),allow_nan=False)+'\n');self.journal.flush();os.fsync(self.journal.fileno())
  return v
 def snapshot(self):return {'anchors':self.guard.snapshot(),'launchError':self.launch_error,'controllerPid':os.getpid(),'hostBeforeLaunchPythonMonoS':self.host_anchor,'hostRemainingS':self.host_remaining()if self.host_anchor is not None else None,'persistenceOnly':self.persistence_only,'hostInstances':self.host_instances,'hostPid':self.host_process.pid if self.host_process else None,'hostRestartAllowed':self.host_restart_allowed,'noJsonAnchorRestore':True,'connectCount':self.connect_count,'campaignRuns':self.campaign_runs,'campaignFailed':self.campaign_failed,'launchConsumed':sorted(self.launch_consumed),'groundFailure':self.ground_failure,'groundRecoveryAuthorized':self.ground_recovery_authorized,'groundRecoveryUsed':self.ground_recovery_used}
 def approved(self,c):
  assert c.get('rootApproved')is True,'ROOT_EXPLICIT_APPROVAL_REQUIRED';ident=c.get('commandId');assert isinstance(ident,str)and re.fullmatch('[a-z0-9-]{1,64}',ident),'UNIQUE_COMMAND_ID_REQUIRED';assert ident not in self.seen,'COMMAND_REPLAY_NO_RETRY';self.seen.add(ident);self.emit('EXPLICIT_COMMAND',commandId=ident,operation=c['op']);return ident
 def reserve(self,run):
  assert not self.persistence_only,'PERSISTENCE_BOOT25_NO_ARM';assert self.host_process is not None and self.host_process.poll()is None,'CURRENT_OWNED_HOST_NOT_LIVE';remaining=self.host_remaining();assert remaining>=240,'HOST_REMAINING_BELOW240S_NO_ARM';proof=self.guard.before_arm(run=run,emulator_id='emulator-5582',current_host_boot_id=self.boot_reader());return{**proof,'hostBeforeLaunchPythonMonoS':self.host_anchor,'hostRemainingConservativeS':remaining}
 def closure_reserve(self):
  a=self.guard.snapshot()['emulatorBeforeLaunchPythonMonoS'];assert a is not None,'EMULATOR_ANCHOR_MISSING';remaining=min(g.EMULATOR_BUDGET_S-(self.clock()-a),self.host_remaining());assert remaining>=90,'CLOSURE_RESERVE_BELOW90S';return remaining
 def host_remaining(self):
  assert self.host_anchor is not None,'PRELAUNCH_HOST_ANCHOR_MISSING';now=g.finite_time(self.clock());assert now>=self.host_anchor,'HOST_ANCHOR_FUTURE';return 2700-(now-self.host_anchor)
 def anchor_host(self):
  assert self.host_anchor is None and self.runtime is None,'HOST_ANCHOR_SINGLE_BEFORE_LAUNCH_NO_RESET';self.host_anchor=g.finite_time(self.clock());self.emit('HOST_ANCHORED_BEFORE_ROOT_LAUNCH',hostBeforeLaunchPythonMonoS=self.host_anchor,hardDurationS=2700)
  def watch():
   while not self.closed:
    if self.host_remaining()<=0:
     try:self.emit('HOST_ORIGINAL_DEADLINE_REACHED_STOP_OWN_EMULATOR')
     finally:self.close()
     break
    time.sleep(.1)
  self.host_thread=threading.Thread(target=watch,daemon=True);self.host_thread.start();return self.snapshot()
 def workspace_before_first_writer(self):
  path=E/'workspace-copy01.json';assert path.is_file()and not path.is_symlink()and path.stat().st_size<=64*2**10,'G12_REGULAR_BOUNDED_COPY_MANIFEST_REQUIRED';raw=path.read_bytes();manifest=json.loads(raw);workspace=E/'workspace01';assert workspace.is_dir()and not workspace.is_symlink(),'G12_REGULAR_CLOSED_WORKSPACE_REQUIRED';assert manifest.get('mode')=='EXACT_CLOSED_DATA_FORK_NOT_PROJECT_COPY'and manifest.get('fileCount')==20 and manifest.get('bytes')==870221,'G12_CURRENT_CLOSED_WORKSPACE20FILES_REQUIRED';expected={}
  for row in manifest['files']:
   name=row['copy'];assert isinstance(name,str)and name.startswith('evidence/beta06/generation12/workspace01/')and not any(part in ['.','..']for part in Path(name).parts),'G12_WORKSPACE_MANIFEST_PATH';expected[name]={'sha256':row['sha256'],'bytes':row['bytes']}
  actual={}
  for p in sorted(workspace.rglob('*')):
   assert not p.is_symlink(),'G12_WORKSPACE_SYMLINK_REFUSED'
   if p.is_file():actual[str(p.relative_to(R))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
  assert len(expected)==20 and actual==expected,'G12_CLOSED_WORKSPACE_DRIFT_BEFORE_FIRST_WRITER';return self.emit('G12_WORKSPACE_EXACT_BEFORE_FIRST_WRITER',manifestSha256=hashlib.sha256(raw).hexdigest(),files=len(actual),bytes=sum(row['bytes']for row in actual.values()))
 def quota_admission(self,phase,claim):
  try:
   if phase=='before-connect'and self.host_process is not None and self.host_process.poll()is not None:
    self.emit('OWNED_HOST_EXIT_OBSERVED_BEFORE_CONNECT_NO_RETRY',pid=self.host_process.pid,exitCode=self.host_process.returncode,console=str(E/('host-console'+str(self.host_instances)+'.txt')));raise RuntimeError('OWNED_HOST_EXITED_NO_CONNECT_OR_RETRY')
   future=b.quota().check_native_future(remaining_ap=4-self.connect_count,remaining_hosts=2-self.host_instances);proof=b.admit(phase,remaining_ap=4-self.connect_count,remaining_hosts=2-self.host_instances,closed_runs=list(self.campaign_runs),claim_id=claim);self.emit('SCOPED_QUOTA_ADMITTED_BEFORE_FRESH_UI',proof=proof,pngFuture=future);return proof
  except BaseException as e:
   self.campaign_failed=True;self.emit('QUOTA_REFUSAL_LATCHED_NO_NEW_AP_OR_HOST',phase=phase,error=str(e));raise
 def start_host(self,c):
  assert not self.campaign_failed,'FAILED_CAMPAIGN_NO_NEW_HOST_OR_AP'
  assert self.host_instances<2 and(self.host_process is None or self.host_process.poll()is not None),'TWO_HOST_INSTANCES_ONE_WINDOW_MAX';assert self.host_instances==0 or self.host_restart_allowed,'NO_RESTART_AFTER_UNEXPECTED_EXIT_OR_FAILURE';assert c.get('sourceAndViewerStoppedAndInspected')is True,'ROOT_SOURCE_AND_VIEWER_GROUND_INSPECTION_REQUIRED'
  self.quota_admission('before-host',c['commandId']);runtime=module('g2_host_admission','qa-runtime.py');samples=[];admission_path=E/('host-admission-'+c['commandId']+'.json');report={'status':'REFUSED_BEFORE_HOST_POPEN','samples':samples}
  try:
   for n in range(31):
    samples.append({'mono':self.clock(),'free':shutil.disk_usage(R).free});assert samples[-1]['free']>=29*2**30,'HOST_ADMISSION29GIB'
    if n<30:time.sleep(1)
   runtime.budget_decision(samples);report['status']='PASS_HOST_ADMISSION_BEFORE_POPEN'
  except BaseException as e:report['error']=str(e);raise
  finally:
   b.write_json(admission_path,report,kind='host-admission')
  portguard=module('g12_host_port_guard','qa-port-guard.py');port_path=E/('host-admission-'+c['commandId']+'-ports.json')
  try:port_proof=portguard.probe_host_ports((8872,8873),clock=self.clock)
  except BaseException as e:
   self.campaign_failed=True;port_proof=getattr(e,'report',{'status':'REFUSED','errorClass':type(e).__name__,'error':str(e)[:256]})
   try:b.write_json(port_path,port_proof,kind='host-admission')
   finally:self.emit('HOST_PORT_PROBE_REFUSED_NO_POPEN_NO_RETRY',diagnostic=str(port_path),proof=port_proof)
   raise
  try:b.write_json(port_path,port_proof,kind='host-admission');self.emit('HOST_PORT_PROBE_PASSED_NO_TOCTOU_GUARANTEE',diagnostic=str(port_path),proof=port_proof)
  except BaseException:self.campaign_failed=True;raise
  if self.host_anchor is None:self.anchor_host()
  remaining=self.host_remaining();assert remaining>=240,'HOST_REMAINING_BELOW240_NO_POPEN';out=E/('host-app12'if self.host_instances==0 else'host-app12-restart');assert not out.exists(),'HOST_OUTPUT_ALREADY_EXISTS_NO_RETRY';workspace=(E/'workspace01').resolve();assert workspace.is_dir()and not workspace.is_symlink(),'ROOT_VERIFIED_GENERATION12_WORKSPACE_REQUIRED';
  if self.host_instances==0:self.workspace_before_first_writer()
  self.host_log=b.BoundedFile(E/('host-console'+str(self.host_instances+1)+'.txt'),4*2**20,binary=True,category='hostOther',kind='host-console');env={**os.environ,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid()),'BETA06_PARENT_HOST_REMAINING_MS':str(math.floor(remaining*1000))};self.emit('HOST_POPEN_INTENT_ANCHOR_ALREADY_CAPTURED',hostAnchorPythonMonoS=self.host_anchor,remainingMs=math.floor(remaining*1000),output=str(out),instanceOrdinal=self.host_instances+1);self.host_instances+=1;self.host_restart_allowed=False;self.restart_authorization=None;self.ground_admission=None;self.host_out=out;self.host_process=subprocess.Popen(['node',str(R/'pilot/beta06g12/entry.mjs'),str(out),'--allow-sitl','--workspace='+str(workspace)],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);self.host_capture=b.PipeCapture(self.host_process,self.host_log);self.emit('OWNED_HOST_PROCESS_STARTED',pid=self.host_process.pid,output=str(out),originalHostAnchorPythonMonoS=self.host_anchor);return self.snapshot()
 def stop_host(self,c):
  assert self.host_process is not None and self.host_process.poll()is None,'OWNED_HOST_ALREADY_EXITED_NO_MANAGED_RETRY';ui=self.ui or module('g2_stop_host_ui','qa-ui.py');state=ui.q.state();assert not state['flight'].get('run')and not state['flight'].get('authority')and not state['flight'].get('busy')and(state.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'CLOSE_RUN_AND_REVOKE_ALL_AUTHORITY_BEFORE_HOST_STOP';assert c.get('sourceAndViewerStoppedAndInspected')is True and(ui.observation()['observation'].get('mediaReadiness')or{}).get('active')is False,'EXPLICIT_SOURCE_VIEWER_STOP_REQUIRED';
  if self.restart_authorization is not None:
   try:
    refreshed=module('g2_restart_recheck','qa-restart-proof.py').authorize(self.restart_authorization['nominalReport'],self.restart_authorization['faultReport']);assert refreshed==self.restart_authorization,'RESTART_PROOF_CHANGED_BEFORE_STOP'
   except BaseException as e:self.restart_authorization=None;self.emit('RESTART_PROOF_REFUSED_CLEANUP_ONLY',error=str(e))
  pid=self.host_process.pid;self.emit('EXPLICIT_MANAGED_HOST_STOP_INTENT',pid=pid);self.host_process.terminate();code=self.host_process.wait(timeout=20);closure=self.host_out/'app-closure.json';assert code==0 and closure.is_file()and not closure.is_symlink(),'CLEAN_HOST_CLOSURE_REQUIRED_NO_RESTART';body=closure.read_bytes();value=json.loads(body);assert value.get('payloadEvidenceFailure')is None and value.get('reason')=='EXPLICIT_STOP'and 'closeIndexFailure'in value and value['closeIndexFailure']is None,'HOST_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';self.host_stop_proof={'pid':pid,'exit':code,'closure':str(closure),'sha256':hashlib.sha256(body).hexdigest(),'observedPythonMonoS':self.clock()};self.host_restart_allowed=self.host_instances==1 and self.restart_authorization is not None;self.ground_admission=None;self.emit('MANAGED_HOST_STOP_VERIFIED',**self.host_stop_proof);self.host_capture.finish()if self.host_capture is not None else None;self.host_log.close();return self.host_stop_proof
 def capture_persistence_stop_proof(self,c):
  assert self.attempt=='24'and self.host_instances==2 and self.host_process is not None and self.host_process.poll()is None,'PERSISTENCE_PRESTOP_REQUIRES_SAME_LIVE_HOST2'
  assert self.runtime is not None and self.runtime.poll()is None and not(E/'android-closure24.json').exists(),'PERSISTENCE_PROOF_MUST_PRECEDE_EMULATOR24_CLOSURE'
  assert self.persistence_stop_proof is None,'PERSISTENCE_PRESTOP_PROOF_SINGLE_USE_NO_RECAPTURE';ui=self.ui or module('g12_persistence_ui','qa-ui.py');state=ui.q.state();view=ui.observation();o=view.get('observation')or{};age=view.get('ageMs');assert view.get('ok')is True and isinstance(age,(int,float))and not isinstance(age,bool)and math.isfinite(age)and 0<=age<=1200 and o.get('foreground')is True,'PERSISTENCE_PRESTOP_FRESH_FOREGROUND_REQUIRED'
  assert state.get('ok')is True and not o.get('run')and not state['flight'].get('run')and not state['flight'].get('authority')and not state['flight'].get('busy')and(state.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0 and 'closeIndexFailure'in state and state['closeIndexFailure']is None,'PERSISTENCE_PRESTOP_GROUND_ZERO_AUTHORITY_INDEXED_REQUIRED'
  assert c.get('sourceAndViewerStoppedAndInspected')is True and(o.get('mediaReadiness')or{}).get('active')is False,'PERSISTENCE_PRESTOP_SOURCE_VIEWER_STOP_INSPECTION_REQUIRED'
  proof={'hostPid':self.host_process.pid,'hostInstances':self.host_instances,'hostAnchorPythonMonoS':self.host_anchor,'connectCount':self.connect_count,'commandId':c['commandId'],'pythonMonoS':self.clock(),'nativeObservationAgeMs':age,'stateSha256':hashlib.sha256(json.dumps(state,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'viewSha256':hashlib.sha256(json.dumps(view,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'consumed':False,'basis':'FRESH_NATIVE_UI_BEFORE_EXPLICIT_EMULATOR24_STOP_NOT_AFTER_STOP'}
  self.persistence_stop_proof=proof;self.emit('PERSISTENCE_PRESTOP_PROOF_SAME_PYTHON_CONTROLLER',proof=proof);return proof
 def persistence_boot(self,c):
  assert self.host_instances==2 and self.host_process is not None and self.host_process.poll()is None,'PERSISTENCE_BOOT25_REQUIRES_SAME_LIVE_HOST2_NO_THIRD_HOST'
  proof=self.persistence_stop_proof;assert proof is not None and proof['consumed']is False and proof['hostPid']==self.host_process.pid and proof['hostInstances']==self.host_instances and proof['hostAnchorPythonMonoS']==self.host_anchor and proof['connectCount']==self.connect_count,'PERSISTENCE_BOOT25_IN_MEMORY_PRESTOP_PROOF_REQUIRED'
  assert self.attempt=='24'and self.runtime is not None and self.runtime.poll()==0,'BOOT24_MUST_BE_CLOSED_BEFORE25';path=E/'android-closure24.json';assert path.is_file()and not path.is_symlink()and path.stat().st_size<=64*2**10,'BOOT24_REGULAR_BOUNDED_CLOSURE_REQUIRED';closed=json.loads(path.read_bytes());assert closed.get('exit')==0 and closed.get('error')is None and closed.get('explicitStop')is True,'BOOT24_CLEAN_EXPLICIT_CLOSURE_REQUIRED'
  ui=self.ui or module('g12_persistence_host_ui','qa-ui.py');state=ui.q.state();assert state.get('ok')is True and not state['flight'].get('run')and not state['flight'].get('authority')and not state['flight'].get('busy')and(state.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0 and 'closeIndexFailure'in state and state['closeIndexFailure']is None,'PERSISTENCE_BOOT25_CURRENT_HOST_GROUND_ZERO_AUTHORITY_REQUIRED'
  assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_NO_PERSISTENCE_BOOT';assert not(E/'android-attempt25.json').exists(),'BOOT25_ALREADY_CONSUMED';proof['consumed']=True;self.emit('EXPLICIT_PERSISTENCE_BOOT25_NEW_EMULATOR_ANCHOR_OLD_HOST_DEADLINE',priorEmulatorAnchors=self.guard.snapshot(),preStopProof=proof);self.attempt='25';self.persistence_only=True;self.guard=g.DeadlineGuard(host_boot_id=self.host_boot_id,clock=self.clock);self.runtime=None;self.permit_thread=None;self.launch_error=None;return self.launch(c)
 def launch(self,c):
  assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_NO_EMULATOR_LAUNCH';assert self.attempt not in self.launch_consumed,'EMULATOR_LAUNCH_ATTEMPT_CONSUMED_NO_RETRY';self.launch_consumed.add(self.attempt);assert self.runtime is None and self.guard.snapshot()['emulatorBeforeLaunchPythonMonoS']is None,'ONE_EMULATOR_LAUNCH_PER_CONTROLLER';log=b.BoundedFile(E/f'root-runtime{self.attempt}.txt',128*2**10,binary=True,kind='runtime-helper-console');argv=[sys.executable,'-B',str(Path(__file__).with_name('qa-runtime.py')),'--start',self.attempt,'--require-permit'];self.emit('EMULATOR_HELPER_POPEN_INTENT',argv=argv)
  try:self.runtime=subprocess.Popen(argv,env={**os.environ,'BETA06_CLOCK_BASIS':g.CLOCK_BASIS,'BETA06_HOST_BOOT_UUID':self.host_boot_id,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid())},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=R);self.runtime_capture=b.PipeCapture(self.runtime,log)
  except BaseException as e:
   self.launch_error=str(e);log.write(('PARENT_POPEN_ERROR '+repr(e)+'\n').encode());log.flush();os.fsync(log.fileno());log.close();self.emit('EMULATOR_HELPER_POPEN_FAILED_NO_RETRY',error=str(e),argv=argv);raise
  def permit():
   try:
    end=self.clock()+85;ready=E/f'android-ready-to-launch{self.attempt}.json'
    while not ready.exists():
     assert not self.closed,'ROOT_CLOSED_BEFORE_LAUNCH';assert self.runtime.poll()is None,'RUNTIME_REFUSED_BEFORE_LAUNCH';assert self.clock()<end,'PRELAUNCH_READY_TIMEOUT';time.sleep(.05)
    ready_value=json.loads(ready.read_bytes())if ready.stat().st_size<=16*2**10 else None;assert isinstance(ready_value,dict)and ready_value.get('controllerPid')==self.runtime.pid,'CURRENT_CHILD_READY_PID_REQUIRED';b.host_clock.same_contract(self.host_boot_id,ready_value.get('hostBootId'),ready_value.get('clockBasis'))
    with self.lock:
     assert not self.closed,'ROOT_CLOSED_BEFORE_LAUNCH';assert self.host_remaining()>=240,'HOST_RESERVE_BELOW240_BEFORE_ACTUAL_BOOT';self.guard.anchor_emulator_before_launch('emulator-5582');proof=self.emit('EMULATOR_ANCHORED_BEFORE_PERMIT',anchors=self.guard.snapshot());p=E/f'android-launch-permit{self.attempt}.json'
     b.write_json(p,{'attempt':self.attempt,'clockBasis':g.CLOCK_BASIS,'hostBootId':self.host_boot_id,'rootControllerPid':os.getpid(),'anchorProof':proof,'parentHostRemainingS':self.host_remaining(),'hostBeforeLaunchPythonMonoS':self.host_anchor,'parentHostDeadlinePythonMonoS':self.host_anchor+2700},kind='launch-permit')
   except BaseException as e:self.launch_error=str(e);self.emit('LAUNCH_HANDSHAKE_FAILED',error=str(e))
  self.permit_thread=threading.Thread(target=permit,daemon=True);self.permit_thread.start();return {'status':'ADMISSION_PENDING_NO_UI_INPUT','pid':self.runtime.pid}
 def action(self,c):
  ui=self.ui or module('beta_ui','qa-ui.py');ident=c['target'];name=c['commandId'];
  assert len(self.dispatched)<160,'FINITE160_VISIBLE_DISPATCHES';assert not re.fullmatch(r'field-(?:raw|delivery)-.*|field-capture-export-.*|field-delivery-file-.*',ident)and ident not in ['field-export-workspace','field-import-workspace'],'OPTIONAL_EXPORT_ALLOCATION_ZERO'
  if ident=='field-connect':
   assert not self.campaign_failed,'FAILED_OR_UNCERTAIN_CAMPAIGN_NO_NEW_AP';self.quota_admission('before-connect','connect-'+name)

  if self.persistence_only:assert ident in ['field-tab-flight','field-tab-payload','field-tab-review','field-export-workspace','field-import-workspace','field-qa-bad-sha','video-stop','field-refresh']or re.fullmatch(r'field-(?:raw|delivery)-s[a-f0-9]{20}|field-capture-export-[a-zA-Z0-9-]{1,48}-[a-f0-9]{12}|field-delivery-file-s[a-f0-9]{20}-[a-zA-Z0-9-]{1,64}',ident),'PERSISTENCE_BOOT25_NO_FLIGHT_COMMANDS';
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
   if ident in ['field-close','field-cut','field-reboot','field-abort']:
    post=ui.q.state();assert 'closeIndexFailure'in post and post['closeIndexFailure']is None and not post['flight'].get('run'),'POST_EFFECT_SEALED_INDEX_PENDING_OR_UNKNOWN_NO_ADVANCE';self.emit('TERMINAL_VISIBLE_ACK_AND_INDEX_STATE_NOT_FAILED',target=ident,priorRun=readiness['observation'].get('run'),notRawAcceptance=True)
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
  ui=self.ui or module('beta_ui','qa-ui.py');spec=importlib.util.spec_from_file_location('beta_g12_R2_completion',R/'planning/beta06g4r2/complete_nominal_policy.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
  path=Path(c['reference']);assert path.is_file()and not path.is_symlink()and path.stat().st_size<=128*2**10,'BOUNDED_INSPECTED_COMPLETION_REFERENCE_REQUIRED';reference=json.loads(path.read_text());diagnostics=CompletionPollDiagnostics(c['commandId'],self.clock,self.host_boot_id);pending={};status='FAILED_OR_PARTIAL_NO_RETRY';error=None
  def read_state():
   begin=self.clock();value=ui.q.state();pending.update(state=value,stateReadBeginPythonMonoS=begin,stateReadEndPythonMonoS=self.clock());return value
  def read_observation(end):
   begin=self.clock();value=ui.receipt_observation(end);timing={k:pending[k]for k in ['stateReadBeginPythonMonoS','stateReadEndPythonMonoS']};timing.update(observationReadBeginPythonMonoS=begin,observationReadEndPythonMonoS=self.clock());diagnostics.capture(pending['state'],value,timing);return value
  def dispatch(command):
   diagnostics.save_last();diagnostics.append('ONE_VISIBLE_CLOSE_DISPATCH_INTENT',{'run':c['run'],'target':'field-close','noRetry':True});return self.action(command)
  try:
   result=policy.wait_complete_nominal(c,reference=reference,state_reader=read_state,observation_reader=read_observation,closure_reserve=self.closure_reserve,phase_policy=ui.phase_policy,dispatch=dispatch,clock=self.clock);status='VISIBLE_CLOSE_ACKNOWLEDGED_NOT_RAW_ACCEPTANCE';return result
  except BaseException as e:error=e;raise
  finally:diagnostics.close(status,error)

 def command(self,c):
  try:return self._command(c)
  except BaseException as e:
   if isinstance(c,dict)and c.get('op')=='start-host':self.campaign_failed=True;self.emit('HOST_START_FAILED_NO_NEW_HOST_OR_AP',error=str(e)[:256])
   if isinstance(c,dict)and c.get('op')in ['action','airborne','sequence','complete-nominal']and(self.connect_count or c.get('target')=='field-connect'):self.campaign_failed=True;self.emit('SCENARIO_FAILED_NO_NEW_AP',operation=c.get('op'),error=str(e))
   raise
 def scenario(self,scenario):
  assert not self.persistence_only,'PERSISTENCE_BOOT25_NO_AIRBORNE';assert self.connect_count>0,'CONNECT_BEFORE_AIRBORNE';expected=['nominal','cut','nominal','reboot'][self.connect_count-1];assert scenario==expected,'FINITE_SCENARIO_ORDER_N1_F1_N2_F2';assert not self.campaign_failed,'FAILED_OR_UNCERTAIN_CAMPAIGN_NO_AIRBORNE';return scenario
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
  if op=='authorize-ground-recovery':
   assert self.connect_count==0 and self.ground_failure is not None and not self.ground_recovery_used and not self.ground_recovery_authorized,'ONE_GROUND_RECOVERY_BEFORE_ANY_AP_ONLY'
   assert c.get('rootInspectedRawGroundFailure')is True,'ROOT_RAW_GROUND_FAILURE_INSPECTION_REQUIRED'
   assert all(isinstance(c.get(k),str)and 1<=len(c[k].strip())<=1024 for k in ['diagnosis','explicitRecovery']),'CONCRETE_DIAGNOSIS_AND_EXPLICIT_RECOVERY_REQUIRED'
   self.ground_recovery_authorized=True;self.emit('ONE_READONLY_GROUND_RECOVERY_AUTHORIZED',priorFailure=self.ground_failure,diagnosis=c['diagnosis'],explicitRecovery=c['explicitRecovery']);return self.snapshot()
  if op=='ground-soak':
   assert not self.persistence_only,'PERSISTENCE_BOOT25_NO_AP_ADMISSION';assert not self.campaign_failed,'FAILED_CAMPAIGN_NO_MORE_GROUND_INTERVALS'
   if self.ground_failure is not None:
    assert self.connect_count==0 and self.ground_recovery_authorized and not self.ground_recovery_used,'GROUND_FAILURE_NO_AUTOMATIC_INTERVAL_RETRY'
    self.ground_recovery_authorized=False;self.ground_recovery_used=True
   a=module('g4_ground','qa-ground-soak.py');self.ground_admission=None
   try:
    result=a.collect(c['commandId'],c['clockJournal'],clock=self.clock);self.ground_admission=result;self.ground_failure=None;return result
   except BaseException as e:
    self.ground_failure={'commandId':c['commandId'],'receipt':str(E/(c['commandId']+'-ground-soak.json')),'error':str(e),'pythonMonoS':self.clock()}
    if self.connect_count or self.ground_recovery_used:self.campaign_failed=True
    self.emit('GROUND_INTERVAL_FAILED_NO_AUTOMATIC_RETRY',failure=self.ground_failure,recoveryUsed=self.ground_recovery_used,campaignFailed=self.campaign_failed);raise
  if op=='action':return self.action(c)
  if op=='sequence':
   steps=c.get('steps');assert isinstance(steps,list)and 1<=len(steps)<=12,'BOUNDED_EXPLICIT_SEQUENCE_REQUIRED';results=[]
   for i,step in enumerate(steps):
    assert isinstance(step,dict);name=c['commandId']+'-'+str(i)
    if step.get('kind')=='airborne':
     assert i==len(steps)-1,'AIRBORNE_ONLY_EXPLICIT_LAST_STEP';assert not self.persistence_only,'PERSISTENCE_BOOT25_NO_AIRBORNE';a=module('beta_airborne','qa-airborne.py');results.append(a.run(self.attempt,step['flightReference'],step['payloadReference'],name,scenario=self.scenario(step.get('scenario','nominal')),dispatch=lambda target,ref,action,timeout:self.action({'target':target,'reference':ref,'commandId':action,'timeout':timeout}),reserve=self.reserve))
    else:results.append(self.action({**step,'commandId':name}))
   return results
  if op=='airborne':
   assert not self.persistence_only,'PERSISTENCE_BOOT25_NO_AIRBORNE';a=module('beta_airborne','qa-airborne.py');return a.run(self.attempt,c['flightReference'],c['payloadReference'],c['commandId'],scenario=self.scenario(c.get('scenario','nominal')),dispatch=lambda target,ref,name,timeout:self.action({'op':'action','target':target,'reference':ref,'commandId':name,'timeout':timeout}),reserve=self.reserve)
  if op in ['setup','start','store-before','store-after']:
   if op=='store-after':self.emit('BEFORE_STORE_AFTER_RESERVE',remainingS=self.closure_reserve())
   d=module('beta_device','qa-device-actions.py');return d.run(self.attempt,op,c.get('variant',''),before_receipt=c.get('beforeReceipt'))
  if op=='native-picker':
   ui=self.ui or module('beta_ui','qa-ui.py');s=ui.q.state();assert not s['flight'].get('run')and not s['flight'].get('authority')and(s.get('payloadLeaseObservation')or{}).get('leaseCount',0)==0,'NATIVE_PICKER_GROUND_IDLE_ONLY';return self.action({**c,'nativePickerHandoffOnly':True})
  if op=='native-negative':return self.native_negative(c)
  if op=='complete-nominal':return self.complete_nominal(c)
  if op=='prepare':
   assert self.prepare_count<48,'FINITE48_INSPECTED_PREPARES';self.prepare_count+=1;ui=self.ui or module('beta_ui','qa-ui.py');return ui.prepare(self.attempt,c['name'],c['nativeFrame'])
  if op=='stop-emulator':
   if self.attempt=='24'and self.host_instances==2 and c.get('sourceAndViewerStoppedAndInspected')is True:self.capture_persistence_stop_proof(c)
   p=E/f'android-stop-request{self.attempt}.json';
   b.write_json(p,{'explicitRootCommand':c['commandId'],'noRestart':True},kind='stop-request',closure=True)
   return {'stopRequested':True}
  raise AssertionError('EXPLICIT_COMMAND_ALLOWLIST')
 def cleanup_emit(self,event,**data):
  try:return self.emit(event,**data)
  except BaseException as error:
   if self.cleanup_journal is None:self.cleanup_journal=b.BoundedFile(E/('root-controller-closure'+self.attempt+'.jsonl'),512*2**10,kind='cleanup-journal',closure=True)
   self.cleanup_journal.write(json.dumps({'event':event,'controllerPid':os.getpid(),'pythonMonoS':self.clock(),'clockBasis':g.CLOCK_BASIS,'hostBootId':self.host_boot_id,'originalJournalFailure':str(error)[:256],**data},separators=(',',':'),allow_nan=False)+'\n');self.cleanup_journal.flush();os.fsync(self.cleanup_journal.fileno())
 def close(self):
  self.closed=True
  if self.host_process is not None and self.host_process.poll()is None:
   self.cleanup_emit('STOP_OWNED_HOST_ON_PARENT_CLOSE',pid=self.host_process.pid);self.host_process.terminate()
   try:self.host_process.wait(timeout=20)
   except subprocess.TimeoutExpired:self.cleanup_emit('OWNED_HOST_CLOSE_UNKNOWN_FORCED_KILL',pid=self.host_process.pid);self.host_process.kill();self.host_process.wait(timeout=5)
  if self.host_capture is not None:
   try:self.host_capture.finish()
   except BaseException as e:self.cleanup_emit('OWNED_HOST_CONSOLE_FAILED',error=str(e))
  if self.host_log is not None and not self.host_log.closed:self.host_log.close()
  if self.permit_thread is not None and hasattr(self.permit_thread,'join'):self.permit_thread.join(timeout=1)
  if self.runtime is not None:
   p=E/f'android-stop-request{self.attempt}.json'
   if not p.exists():
    b.write_json(p,{'reason':'PERSISTENT_ROOT_CONTROLLER_CLOSED_NO_RESTART','rootControllerPid':os.getpid()},kind='stop-request',closure=True)
   self.cleanup_emit('OWN_RUNTIME_STOP_REQUEST_ON_CONTROLLER_CLOSE',runtimePid=self.runtime.pid)
   try:self.runtime.wait(timeout=35)
   except subprocess.TimeoutExpired:
    self.cleanup_emit('OWNED_RUNTIME_CLOSURE_TIMEOUT_UNKNOWN',runtimePid=self.runtime.pid);self.runtime.terminate()
    try:self.runtime.wait(timeout=20)
    except subprocess.TimeoutExpired:self.cleanup_emit('OWNED_RUNTIME_CLOSURE_STILL_UNKNOWN',runtimePid=self.runtime.pid)
  if self.runtime_capture is not None:
   try:self.runtime_capture.finish()
   except BaseException as e:self.cleanup_emit('OWNED_RUNTIME_CONSOLE_FAILED',error=str(e))
  if self.cleanup_journal is not None:self.cleanup_journal.close()
def plan():return {'persistentProcessRequired':True,'commands':['status','authorize-managed-restart','start-host','stop-host','anchor-host-before-launch','launch-emulator','launch-persistence-emulator','setup','start','store-before','store-after','prepare','ground-soak','authorize-ground-recovery','action','sequence','airborne','complete-nominal','native-negative','native-picker','stop-emulator'],'attempts':['24','25'],'emulatorSeconds':2700,'newConnectIntentsBoot24':4,'connectIntentsBoot25':0,'hostBudgetSecondsAcrossBothBoots':2700,'apBudgetSeconds':540,'preArmApReserveSeconds':225,'preArmEmulatorReserveSeconds':240,'storeAfterReserveSeconds':90,'anchorSource':'THIS_PYTHON_PROCESS_BEFORE_LAUNCH_PERMIT_AND_BEFORE_CONNECT_TAP','clockBasis':g.CLOCK_BASIS,'clockProvider':'pilot/beta06g12/clock_basis.py','restoreAnchorsFromJson':False,'automaticUiInput':False,'dispatchRetry':False}
if __name__=='__main__':
 if sys.argv[1:]==['--plan']:print(json.dumps(plan(),indent=2))
 else:
  assert len(sys.argv)==3 and sys.argv[1]=='--serve'and sys.argv[2]=='24';E.mkdir(parents=True,exist_ok=True)
  with b.BoundedFile(E/f'root-controller{sys.argv[2]}.jsonl',2*2**20,kind='controller-journal')as j:
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
