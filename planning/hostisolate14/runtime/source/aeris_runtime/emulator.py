"""Stable owned cached emulator guardian; never AP, input, bootstrap, or aircraft control."""
from pathlib import Path
import argparse,hashlib,json,os,signal,socket,subprocess,time
from collections import deque
from .admission import DiskGuard
from .candidate import put,sha
from .campaign import Campaign
from .paths import repository
from .policy import case_budget,campaign_budget
from .monitor import host_power
from pilot.betaintegrated01.runtime.ap_stage import canonical
STOP=False
FAILED_DISPOSAL=False
def fail_dispose(*args):
 global STOP,FAILED_DISPOSAL
 STOP=True;FAILED_DISPOSAL=True
def stop(*args):
 global STOP
 STOP=True

class PhaseTiming:
 """Bounded non-authority timing; no IO, guard samples, or cadence service."""
 def __init__(self,*,now=time.monotonic_ns,cpu=time.thread_time_ns):
  self.now=now;self.cpu=cpu;self.rows=deque(maxlen=128);self.total=0;self.iteration=0;self.active=None;self.last_active=None;self.first_failure=None
 def call(self,phase,fn,*args,**kwargs):
  start=self.now();cpu=self.cpu();self.active={'phase':phase,'iteration':self.iteration,'enteredHostNs':start};error=None
  try:return fn(*args,**kwargs)
  except BaseException as exc:
   error={'type':type(exc).__name__,'reason':str(exc)[:512]}
   if self.first_failure is None:self.first_failure={**self.active,**error}
   raise
  finally:
   end=self.now();row={**self.active,'exitedHostNs':end,'durationNs':end-start,'threadCPUDeltaNs':self.cpu()-cpu,'exception':error};self.rows.append(row);self.total+=1;self.last_active=row;self.active=None
 def snapshot(self):
  return {'format':'aeris-guardian-phase-timing','version':1,'scope':'NON_AUTHORITY_ORIGINAL_CALL_DURATIONS_NOT_GUARD_SAMPLES_OR_CAUSAL_ATTRIBUTION','maximumRows':128,'totalCompletedPhases':self.total,'olderTimingRowsOverwritten':max(0,self.total-len(self.rows)),'rows':list(self.rows),'latestActivePhase':self.active,'lastCompletedPhase':self.last_active,'firstPhaseFailure':self.first_failure,'cadenceOrGuardHistoryChanged':False}

def _query(argv,budget,root,*,maximum=256):
 with budget.operation({'guardian':maximum+128+12288}):return _query_reserved(argv,budget,root,maximum=maximum)
def _query_reserved(argv,budget,root,*,maximum=256):
 from .metadata_budget import capture_command
 value=capture_command(budget,'guardian',argv,deadline_ns=time.monotonic_ns()+2_000_000_000,stdout_limit=maximum,stderr_limit=128);out=value['stdout'];err=value['stderr'];path=Path(root)/'query-output.raw';offset=path.stat().st_size if path.exists()else 0
 budget.write('guardian',path,out+err,append=True,closing=value['failure']is not None)
 budget.append_json('guardian',Path(root)/'queries.jsonl',[time.monotonic_ns(),offset,len(out),len(err),hashlib.sha256(out+err).hexdigest()],maximum=256,closing=value['failure']is not None)
 if value['failure']is not None:raise value['failure']
 if err:raise RuntimeError('GUARDIAN_QUERY_STDERR')
 return out.decode()

ADB_EXECUTABLE_SHA256='1811e253b21b12cbfda7201ebaf86c10e7ddcb5c606a7a81f7c82b4c429c2d3b'
ADB_STARTUP_STDERR=b'* daemon not running; starting now at tcp:5037\n* daemon started successfully\n'
def prepare_adb_server(adb,budget,root,campaign):
 """One exact source-admitted daemon preparation; ordinary queries stay strict."""
 from .metadata_budget import MetadataBudget,capture_command
 if type(budget)is not MetadataBudget:raise ValueError('ADB_SETUP_EXACT_METADATA_BUDGET')
 budget.require_real_actor();campaign.check()
 if type(adb)is not str or not Path(adb).is_absolute()or sha(adb)!=ADB_EXECUTABLE_SHA256:raise ValueError('ADB_SETUP_PINNED_EXECUTABLE_REQUIRED')
 root=Path(root);target=root/'adb-server-setup.json'
 if target.exists():raise ValueError('ADB_SETUP_ONE_DISPATCH_NO_RETRY')
 # Raw+query journal+stage receipt+new parent fit this source-fixed claim.
 with budget.operation({'guardian':32768}):
  campaign.check();started=time.monotonic_ns();deadline=min(campaign.deadline_ns,started+2_000_000_000);argv=[adb,'start-server'];out=err=b'';code=None;complete=False;primary=None
  try:
   if deadline<=started:raise TimeoutError('ADB_SETUP_ORIGINAL_CAMPAIGN_DEADLINE')
   value=capture_command(budget,'guardian',argv,deadline_ns=deadline,stdout_limit=64,stderr_limit=128);out=value['stdout'];err=value['stderr'];code=value['exit'];complete=value['captureComplete'];primary=value['failure']
   if primary is None:
    if not complete or type(code)is not int or code!=0:raise RuntimeError('ADB_SETUP_INCOMPLETE_OR_EXIT')
    if time.monotonic_ns()>=deadline:raise TimeoutError('ADB_SETUP_ORIGINAL2S_FINAL_DEADLINE')
    if out:raise RuntimeError('ADB_SETUP_UNEXPECTED_STDOUT')
    if err not in(b'',ADB_STARTUP_STDERR):raise RuntimeError('ADB_SETUP_UNEXPECTED_STDERR')
  except BaseException as error:primary=primary or error
  ended=time.monotonic_ns();path=root/'query-output.raw';raw=out+err;refs=None
  try:
   offset=path.stat().st_size if path.exists()else 0;budget.write('guardian',path,raw,append=True,closing=primary is not None)
   refs={name+'Ref':{'path':str(path),'offset':offset+extra,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}for name,data,extra in[('stdout',out,0),('stderr',err,len(out))]}
   budget.append_json('guardian',root/'queries.jsonl',[ended,offset,len(out),len(err),hashlib.sha256(raw).hexdigest()],maximum=256,closing=primary is not None)
   receipt={'format':'aeris-adb-server-preparation','version':1,'argv':argv,'ADBExecutableSHA256':ADB_EXECUTABLE_SHA256,'startedHostNs':started,'finishedHostNs':ended,'deadlineHostNs':deadline,'exit':code,'captureComplete':complete,'failure':None if primary is None else type(primary).__name__+':'+str(primary)[:256],'serverPreparationComplete':primary is None,'warmObserved':primary is None and err==b'','deadlineScope':'COMMAND_POPEN_EOF_WAIT_CLEANUP','devicesQueryStillRequired':True,'acceptedStartupBanner':err==ADB_STARTUP_STDERR,'APStarted':False,'emulatorStarted':False,**refs};body=canonical(receipt)+b'\n'
   if len(body)>2048:raise ValueError('ADB_SETUP_RECEIPT2KiB')
   budget.write('guardian',target,body,closing=primary is not None)
  except BaseException as storage:
   if primary is None:primary=storage
   else:primary.add_note('ADB_SETUP_STORAGE_SECONDARY:'+type(storage).__name__+':'+str(storage)[:192])
   fallback=None
   try:
    failed=root/'adb-server-setup.failed-prefix.raw';budget.write('guardian',failed,raw,closing=True);fallback={'path':str(failed),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
   except BaseException as secondary:primary.add_note('ADB_SETUP_RAW_PREFIX_UNDURABLE:'+type(secondary).__name__+':'+str(secondary)[:128])
   try:budget.failure(primary,detail={'stage':'adb-server-preparation','captureComplete':False,'ready':False,'failedPrefixRef':fallback,'storageSecondary':type(storage).__name__+':'+str(storage)[:192]})
   except BaseException as secondary:primary.add_note('ADB_SETUP_DIAGNOSTIC_UNDURABLE:'+type(secondary).__name__+':'+str(secondary)[:128])
   raise primary
  if primary is not None:raise primary
  return {'path':str(target),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'devicesQueryStillRequired':True}

_HEALTH_CLIENTS={}
def observe_guardian(root,source_sha,*,now=time.monotonic_ns,budget=None):
 from .host_health import GuardianClient
 if budget is None:raise ValueError('GUARDIAN_OBSERVATION_EXPLICIT_BUDGET')
 key=(str(Path(root).resolve()),source_sha)
 if key not in _HEALTH_CLIENTS:
  if len(_HEALTH_CLIENTS)>=2:raise ValueError('GUARDIAN_CLIENT_INSTANCE_BOUND')
  _HEALTH_CLIENTS[key]=GuardianClient(root,source_sha,budget=budget)
 return _HEALTH_CLIENTS[key]()

def run(spec,root,campaign_clock,inventory,*,budget=None):
 global STOP,FAILED_DISPOSAL
 from .metadata_budget import MetadataBudget
 from .owned_output import OwnedOutput
 budget=budget or MetadataBudget.attach(os.environ['AERIS_METADATA_BUDGET'])
 if type(budget)is not MetadataBudget:raise ValueError('EXACT_GUARDIAN_METADATA_BUDGET')
 budget.require_real_actor()
 root=Path(root)
 if root.exists():raise ValueError('GUARDIAN_FRESH_ROOT')
 campaign=Campaign(campaign_clock,budget=budget);repo=repository();guard=None;health=None;server=None;child=None;output=None;failure=None;primary=None;started=time.monotonic_ns();timing=PhaseTiming();owner_pid=os.getppid()
 try:
  timing.call('startup_campaign_check',campaign.check);b=case_budget(__import__('shutil').disk_usage(repo).free,180)
  if b['admitted']is not True:raise ValueError('EMULATOR_ORIGINAL_SHORT_BUDGET')
  argv=spec['argv'];avd=Path(spec['AVD']);sdk=Path(spec['SDK']);adb=spec['ADB']
  if argv[:5]!=[str(sdk/'emulator/emulator'),'-avd','aeris-beta-m1','-port','5582'] or '-wipe-data'in argv:raise ValueError('CACHED_OWNED_EMULATOR_ARGV')
  for name,fact in spec['prerequisites'].items():
   if sha(fact['path'])!=fact['sha256']:raise ValueError('CACHED_PREREQUISITE:'+name)
  if sha(avd/'config.ini')!=spec['AVDConfigSHA256']:raise ValueError('AVD_CONFIGURATION_SHA')
  adb_preparation=timing.call('adb_server_prepare',prepare_adb_server,adb,budget,root,campaign)
  if 'emulator-5582' in timing.call('adb_devices_query',_query,[adb,'devices'],budget,root,maximum=4096):raise RuntimeError('EMULATOR_ALREADY_PRESENT')
  for port in (5582,5583):
   with socket.socket() as s:s.bind(('127.0.0.1',port))
  from .host_health import HostHealth,HealthServer,source_sha,budget_binding
  import secrets
  health=HostHealth(root,budget,'guardian',inventory=inventory,check_inventory=_caps);ready=timing.call('real_health_prime',health.start);guard=health.disk;prime=ready['actualPrime'];p=ready['power'];timing.call('primed_campaign_check',campaign.check);barrier=health.barrier();timing.call('admission_write',budget.write,'guardian',root/'admission.json',canonical({'ADBServerPreparation':adb_preparation,'capacity':b,'power':p,'actualPrime':prime,'healthBarrier':barrier,'sourceSHA256':sha(__file__),'absoluteCampaignDeadlineNs':campaign.deadline_ns,'APStarted':False})+b'\n')
  console_lease=budget.reserve_lease({'guardian':500*1024+16384});env={**os.environ,'ANDROID_AVD_HOME':str(avd.parent),'ANDROID_USER_HOME':spec['ANDROID_USER_HOME'],'ANDROID_HOME':str(sdk),'ANDROID_SDK_ROOT':str(sdk)};health.check();health.barrier();child=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);budget.bind_lease_child(console_lease,child.pid);output=OwnedOutput(budget,'guardian',child,{'stdout':root/'console.txt'},maximum_each=500*1024,lease=console_lease)
  process_start=_query(['ps','-p',str(os.getpid()),'-o','lstart='],budget,root,maximum=128).strip()
  binding={**budget_binding(budget),'version':1,'instance':secrets.token_hex(16),'pid':os.getpid(),'processStart':process_start,'guardianSourceSHA256':sha(__file__),'healthSourceSHA256':source_sha()}
  budget.write('guardian',root/'launch.json',canonical({'pid':child.pid,'processStart':_query(['ps','-p',str(child.pid),'-o','lstart='],budget,root,maximum=128).strip(),'guardianPID':os.getpid(),'guardianProcessStart':process_start,'guardianSourceSHA256':sha(__file__),'healthBinding':binding,'argv':argv,'ADBExecutableSHA256':ADB_EXECUTABLE_SHA256,'startedHostNs':started,'originalCampaignDeadlineNs':campaign.deadline_ns})+b'\n')
  health.check();health.barrier();server=HealthServer(root,health,binding);server.start()
  tick=0
  while not STOP:
   if os.getppid()!=owner_pid:
    FAILED_DISPOSAL=True;raise RuntimeError('RUNTIME_OWNER_DIED_SIMULATOR_DISPOSAL')
   timing.iteration=tick+1;timing.call('health_read',health.check);timing.call('campaign_check',campaign.check);output.check()
   if server.failure or not server.thread.is_alive():raise RuntimeError('HOST_HEALTH_ENDPOINT_DEAD')
   if timing.call('child_poll',child.poll)is not None:raise RuntimeError('OWNED_EMULATOR_EXIT')
   tick+=1
   timing.call('sleep',time.sleep,.5)
 except BaseException as e:
  primary=e;failure=type(e).__name__+':'+str(e)
  try:budget.write('guardian',root/'failure.json',canonical({'failure':failure[:2048],'hostNs':time.monotonic_ns(),'APStarted':False})+b'\n',closing=True)
  except BaseException as storage:e.add_note('GUARDIAN_FAILURE_DIAGNOSTIC_UNDURABLE:'+str(storage))
 finally:
  from .cleanup import cleanup
  def stop_emulator():
   if health is not None and(not health.managed_closing or len(health.threads)==3 and health.threads[2].is_alive())and not FAILED_DISPOSAL:raise RuntimeError('OWNED_EMULATOR_RETAINED_INVENTORY_NOT_QUIESCED')
   observed=[]
   def wait_owned(seconds):
    end=time.monotonic()+seconds
    while child.poll()is None:
     if health is not None:
      try:health.closing_check()
      except BaseException as error:
       health.latch(error)
       if not observed:observed.append(error)
     remaining=end-time.monotonic()
     if remaining<=0:raise subprocess.TimeoutExpired(child.args,seconds)
     try:child.wait(timeout=min(.1,remaining))
     except subprocess.TimeoutExpired:pass
   if child is not None and child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:wait_owned(25)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);wait_owned(10)
   if observed:raise observed[0]
  if FAILED_DISPOSAL and primary is None:primary=RuntimeError('SIMULATOR_FAILED_PHYSICAL_DISPOSAL_NOT_ACCEPTANCE')
  receipts={}
  def capture_close(label,operation):
   receipts[label]=operation()
  ops=[]
  if server is not None:ops.append(('health-endpoint-drain-before-managed-closing',server.close))
  if health is not None:ops.append(('inventory-quiesce-before-owned-stop',lambda:capture_close('managedBefore',health.begin_managed_close)))
  ops.append(('owned-emulator-stop',stop_emulator))
  if output is not None:ops.append(('owned-emulator-output-close',lambda:capture_close('output',output.close)))
  if health is not None:
   ops.append(('stable-final-owned-avd-census',lambda:capture_close('managedAfter',health.final_managed_census)))
   ops.append(('host-health-close',lambda:capture_close('health',health.close)))
  primary=cleanup(primary,ops)
  if primary is not None:failure=type(primary).__name__+':'+str(primary)
  if server is not None:
   try:receipts['ipcTrace']=server.flush_trace(budget)
   except BaseException as diagnostic_error:
    print(json.dumps({'secondaryDiagnosticFailure':type(diagnostic_error).__name__+':'+str(diagnostic_error)[:512],'originalFailure':failure,'ipcCapture':'INCOMPLETE','flightAcceptance':False}),flush=True)
    if primary is None:primary=diagnostic_error;failure=type(primary).__name__+':'+str(primary)
    else:primary.add_note('IPC10_SERVER_TRACE_SECONDARY:'+str(diagnostic_error)[:256])
  output_receipt=receipts.get('output');health_receipt=receipts.get('health')
  budget.write('guardian',root/'closure.json',canonical({'failure':failure,'exit':None if child is None else child.poll(),'hostNs':time.monotonic_ns(),'APStarted':False,'flightCommands':0,'ipcTraceRef':receipts.get('ipcTrace'),'cleanupNotes':[]if primary is None else[str(x)[:256]for x in getattr(primary,'__notes__',())[-8:]],'outputCapture':output_receipt,'health':health_receipt,'managedBefore':receipts.get('managedBefore'),'managedAfter':receipts.get('managedAfter'),'exceptionalPhysicalDisposal':FAILED_DISPOSAL,'APGroundProven':False,'flightAcceptance':False,'durablyDrained':not FAILED_DISPOSAL and health_receipt is not None and health_receipt.get('durablyDrained')is True})+b'\n',closing=True)
  try:
   diagnostic={**timing.snapshot(),'hostHealthTraces':None if health is None else{'acquisition':health.power_trace.snapshot(),'writer':health.audit.trace.snapshot(),'inventoryFault':getattr(health,'inventory_fault',None)},'guardianSourceSHA256':sha(__file__),'originalFailure':failure,'originalGuardDiagnostic':None if guard is None else guard.diagnostic(),'closedHostNs':time.monotonic_ns(),'APStarted':False};body=canonical(diagnostic)+b'\n'
   if len(body)>131072:raise ValueError('GUARDIAN_PHASE_DIAGNOSTIC128KiB')
   budget.write('guardian',root/'phase-timing.json',body,closing=True)
  except BaseException as diagnostic_error:print(json.dumps({'secondaryDiagnosticFailure':type(diagnostic_error).__name__+':'+str(diagnostic_error)[:512],'originalFailure':failure,'flightAcceptance':False}),flush=True)
 return 1 if failure else 0

def _caps(v):
 if any(type(v.get(k))is not int or not 0<=v[k]<=limit for k,limit in {'metadataBytes':64*2**20,'exportBytes':192*2**20,'AVDPositiveGrowthBytes':512*2**20,'artifactBytes':9*2**20,'taskAllocatedBytes':campaign_budget()['taskHardPeakBytes']}.items()):raise RuntimeError('SHARED_ORIGINAL_CAP')

def main():
 from .inventory import Inventory
 from .entry import module_origin_receipt
 from .candidate import load
 candidate=os.environ['AERIS_CANDIDATE_DIR'];load(candidate,os.environ['AERIS_CANDIDATE_SHA256']);module_origin_receipt(candidate)
 p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--root',required=True);p.add_argument('--campaign',required=True);p.add_argument('--evidence',required=True);p.add_argument('--planning',required=True);p.add_argument('--avd-baseline',required=True);p.add_argument('--artifact-root');a=p.parse_args();spec=json.loads(Path(a.spec).read_bytes());signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGUSR1,fail_dispose);raise SystemExit(run(spec,a.root,a.campaign,Inventory(a.evidence,a.planning,spec['AVD'],a.avd_baseline,artifact_root=a.artifact_root)))
if __name__=='__main__':main()
