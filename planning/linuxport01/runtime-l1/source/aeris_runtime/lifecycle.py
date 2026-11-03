"""Product-owned session lifecycle. It never creates or renews native input authority."""
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,os,re,time,threading
from .foundation.journal_base import SegmentedJournal,Policy,FileIO
from pilot.betaintegrated01.runtime.ap_stage import canonical
PHASES={'CREATED','ADMITTING','STARTING','RESOURCES_READY','BOOTSTRAPPING','READY','CONNECTED','ARMED','ACTIVE','LANDING','GROUNDED','REVOKED','NATIVE_SEALED','DRAINING','EVIDENCE_DURABLE','REVIEW_READY','CLOSED','FAILED'}
NEXT={'CREATED':{'ADMITTING'},'ADMITTING':{'STARTING'},'STARTING':{'RESOURCES_READY'},'RESOURCES_READY':{'BOOTSTRAPPING'},'BOOTSTRAPPING':{'READY'},'READY':{'CONNECTED'},'CONNECTED':{'ARMED','GROUNDED','REVOKED'},'ARMED':{'ACTIVE','LANDING','GROUNDED'},'ACTIVE':{'LANDING','GROUNDED'},'LANDING':{'GROUNDED'},'GROUNDED':{'REVOKED'},'REVOKED':{'NATIVE_SEALED'},'NATIVE_SEALED':{'DRAINING'},'DRAINING':{'EVIDENCE_DURABLE'},'EVIDENCE_DURABLE':{'REVIEW_READY'},'REVIEW_READY':{'CLOSED'}}
@dataclass(frozen=True)
class Context:
 run:str;epoch:str;boot:str;operator:str;generation:str;profileId:str
 def __post_init__(self):
  for k in('run','epoch','boot','generation'):
   v=getattr(self,k)
   if type(v)is not str or re.fullmatch('[A-Za-z0-9_-]{1,64}',v)is None:raise ValueError('SESSION_CONTEXT_IDENTIFIER')
  for k in('operator','profileId'):
   v=getattr(self,k)
   if type(v)is not str or not 1<=len(v)<=128 or any(ord(c)<32 for c in v):raise ValueError('SESSION_CONTEXT_LABEL')
 def value(self):return asdict(self)
class MetadataGuardObserver:
 """Real observations of the existing guard; never resets/reprimes its history."""
 def __init__(self,journal,gate):
  self.journal=journal;self.gate=gate;self.stop_event=threading.Event();self.thread=None;self.lock=threading.Lock();self.observations=0;self.contentions=0;self.first_ns=None;self.last_ns=None;self.maximum_gap_ns=0;self.failure=None;self.closed=False;self.last_guard_diagnostic=None
 def _sample(self):
  if not self.gate.acquire(timeout=.2):
   with self.lock:self.contentions+=1
   return
  acquired=False
  try:
   acquired=self.journal.lock.acquire(timeout=.2)
   if not acquired:
    with self.lock:self.contentions+=1
    return
   self.journal.guard.check();d=self.journal.guard.diagnostic();n=d.get('currentObservationNs')
   if type(n)is not int or n<0:raise RuntimeError('ACTUAL_METADATA_GUARD_OBSERVATION_REQUIRED')
   with self.lock:
    if self.last_ns is not None:self.maximum_gap_ns=max(self.maximum_gap_ns,n-self.last_ns)
    self.first_ns=n if self.first_ns is None else self.first_ns;self.last_ns=n;self.observations+=1;self.last_guard_diagnostic=d
  finally:
   if acquired:self.journal.lock.release()
   self.gate.release()
 def start(self):
  if self.thread is not None:raise RuntimeError('METADATA_GUARD_OBSERVER_ONE_START')
  self._sample();self.thread=threading.Thread(target=self._run,name='aeris-lifecycle-real-guard-observer');self.thread.start()
 def _run(self):
  try:
   while not self.stop_event.wait(.1):
    self._sample()
    with self.lock:last=self.last_ns
    if last is None or time.monotonic_ns()-last>2_000_000_000:raise RuntimeError('METADATA_GUARD_OBSERVER_NO_REAL_SAMPLE2S')
  except BaseException as e:
   with self.lock:self.failure=type(e).__name__+':'+str(e)
 def check(self):
  with self.lock:failure=self.failure;last=self.last_ns
  if failure is not None:raise RuntimeError('METADATA_GUARD_OBSERVER_FAILED:'+failure)
  if self.thread is not None and not self.thread.is_alive() and not self.stop_event.is_set():raise RuntimeError('METADATA_GUARD_OBSERVER_DEAD')
  if not self.stop_event.is_set() and (last is None or time.monotonic_ns()-last>2_000_000_000):raise RuntimeError('METADATA_GUARD_OBSERVER_STALE2S')
 def snapshot(self):
  with self.lock:return {'scope':'REAL_EXISTING_JOURNAL_GUARD_STATVFS_OBSERVATIONS_NOT_HEARTBEAT','observations':self.observations,'firstActualObservationNs':self.first_ns,'lastActualObservationNs':self.last_ns,'maximumObserverGapNs':self.maximum_gap_ns,'lockContentions':self.contentions,'failure':self.failure,'stopped':self.closed,'threadAlive':self.thread is not None and self.thread.is_alive(),'reprimeOrHistoryReset':False,'lastActualObserverGuardDiagnostic':json.loads(json.dumps(self.last_guard_diagnostic))}
 def close(self):
  self.stop_event.set()
  if self.thread is not None:self.thread.join(timeout=2)
  if self.thread is not None and self.thread.is_alive():raise RuntimeError('METADATA_GUARD_OBSERVER_DID_NOT_JOIN')
  self.closed=True;return self.snapshot()

class Lifecycle:
 def __init__(self,root,context,source_sha,*,journal=None,now=time.monotonic_ns,budget=None):
  if type(context)is not Context or re.fullmatch('[a-f0-9]{64}',source_sha)is None:raise ValueError('LIFECYCLE_BINDING')
  self.budget=budget
  self.root=Path(root);self.context=context;self.source=source_sha;self.now=now;self.lock=threading.RLock();self.observation_gate=threading.RLock();self.phase='CREATED';self.sequence=0;self.last=-1;self.failure=None;self.failureType=None;self.failureEventCommitRef=None;self.failureAppendError=None;self.secondaryFailures=[];self.unpublishedDurableEvents=[];self.proofs={};self.incidents=[];self.closed=False;self.guard_observer=None;self.proof_root=self.root/'lifecycle-proofs'
  if budget is not None:budget.prepare_directory('lifecycle',self.proof_root)
  from .budget_fileio import BudgetFileIO
  io=BudgetFileIO(budget)if budget is not None else None
  self.journal=journal or SegmentedJournal(self.root/'lifecycle',context.run,context.epoch,Policy(segment_bytes=1024*1024,quota_bytes=8*1024*1024,max_record_bytes=16384,max_segments=12,termination_reserve_bytes=32768),io=io)
  try:
   if hasattr(self.journal,'guard') and hasattr(self.journal,'lock'):
    self.guard_observer=MetadataGuardObserver(self.journal,self.observation_gate);self.guard_observer.start()
   elif journal is None:raise RuntimeError('REAL_LIFECYCLE_JOURNAL_GUARD_REQUIRED')
   self._record('SESSION_CREATED',{})
  except BaseException:
   try:self.stop_guard_observer()
   except BaseException:pass
   if isinstance(self.journal,SegmentedJournal):
    try:self.journal.abort('LIFECYCLE_CONSTRUCTOR_FAILED')
    except BaseException:pass
   raise
 def check_guard_observer(self):
  if self.guard_observer is not None:self.guard_observer.check()
 def stop_guard_observer(self):
  return self.guard_observer.close() if self.guard_observer is not None else {'scope':'UNIT_SUPPLIED_JOURNAL_NO_RUNTIME_GUARD','threadAlive':False}
 def _proof_capacity(self,new_bytes):
  from .audit.lifecycle import allocated
  used=allocated(self.root/'lifecycle')+allocated(self.proof_root);reserve=32768+16384+8192;required=((new_bytes+4095)//4096)*4096+reserve
  if used+required>8*2**20:raise RuntimeError('COMBINED_LIFECYCLE_PROOF_JOURNAL8MiB')
  if self.root.parent.name=='sessions':
   from .inventory import Inventory
   from .budget_fileio import BudgetFileIO
   inventory=None if self.budget is None else self.budget.inventory
   if type(inventory)is not Inventory or inventory.evidence!=self.root.parent.parent.resolve():raise ValueError('EXACT_CURRENT_CAMPAIGN_INVENTORY_REQUIRED_FOR_PROOF')
   closing=type(self.journal.io)is BudgetFileIO and self.journal.io.closing is True
   v=self.budget.snapshot_inventory(inventory,closing=closing)
   from .metadata_budget import CAP as METADATA_CAP
   if v['metadataBytes']+required>METADATA_CAP:raise RuntimeError('GLOBAL_HOST_METADATA68MiB_PROOF_ADMISSION')
  if hasattr(self.journal,'guard'):
   with self.journal.lock:self.journal.guard.check(required)
 def _store_proof(self,row):
  from .audit.lifecycle import read_blob
  raw=canonical(row);self._proof_capacity(len(raw));h=hashlib.sha256(raw).hexdigest();ref={'format':'aeris-lifecycle-proof-ref','version':1,'path':'lifecycle-proofs/'+h+'.json','sha256':h,'bytes':len(raw)};io=getattr(self.journal,'io',None)or FileIO()
  if not self.proof_root.exists():self.proof_root.mkdir();io.dirsync(self.root)
  if self.proof_root.is_symlink()or not self.proof_root.is_dir():raise RuntimeError('PROOF_BLOB_DIRECTORY_TYPE')
  target=self.proof_root/(h+'.json');pending=self.proof_root/(h+'.json.pending')
  if target.exists()or pending.exists():raise RuntimeError('PROOF_BLOB_ALREADY_EXISTS_NO_OVERWRITE')
  fd=io.open_exclusive(pending)
  try:
   view=memoryview(raw)
   while view:
    count=io.write(fd,view)
    if type(count)is not int or not 0<count<=len(view):raise RuntimeError('PROOF_BLOB_SHORT_WRITE')
    view=view[count:]
   io.fsync(fd)
  finally:io.close(fd)
  if self.budget is not None:self.budget.publish_lifecycle_proof(pending,target,io)
  else:os.replace(pending,target);io.dirsync(self.proof_root)
  read_blob(self.root,ref,{k:v for k,v in row.items()if k!='data'});return ref
 def _record(self,kind,data):
  with self.observation_gate:
   self.check_guard_observer();n=self.now()
   if type(n)is not int or n<0 or n<self.last:raise RuntimeError('SUPERVISOR_CLOCK_REGRESSION')
   original={'version':1,'context':self.context.value(),'sourceSHA256':self.source,'phase':self.phase,'lifecycleSequence':self.sequence+1,'hostNs':n,'kind':kind,'data':data,'authorityMintedOrRenewed':False};blob=self._store_proof(original);row={**original,'data':{'proofBlob':blob}};self.check_guard_observer();seq=self.journal.append_event('MISSION_LIFECYCLE',row);self.last=n;self.sequence+=1
   ref={'journalSequence':seq,'journalSHA256':self.journal.head,'hostNs':n,'lifecycleSequence':self.sequence,'proofBlob':blob}
   try:
    from .audit.lifecycle import read_blob
    read_blob(self.root,blob,{k:v for k,v in row.items()if k!='data'});self.check_guard_observer()
   except BaseException:
    if len(self.unpublishedDurableEvents)<16:self.unpublishedDurableEvents.append({'kind':kind,'originalCommitRef':ref,'operationalPhasePublished':False})
    raise
   return ref
 def verify_proofs(self):
  from .audit.lifecycle import verify_prefix
  with self.observation_gate:
   result=verify_prefix(self.root,self.context.value(),self.source,self.journal.seq-1,self.journal.head)
   if result['finalPhase']!=self.phase:raise RuntimeError('COMMITTED_LIFECYCLE_PHASE_NOT_PUBLISHED_IN_PRODUCER')
   return result
 def transition(self,phase,proof):
  with self.lock:
   if self.closed or self.phase in('FAILED','CLOSED')or phase not in PHASES or phase not in NEXT.get(self.phase,set()):raise RuntimeError('ILLEGAL_PRODUCT_LIFECYCLE:'+self.phase+'->'+str(phase))
   if type(proof)is not dict or not proof:raise ValueError('DURABLE_PHASE_PROOF_REQUIRED')
   ref=self._record('PHASE_COMMIT',{'from':self.phase,'to':phase,'proof':proof});self.phase=phase;self.proofs[phase]=ref;return ref
 def incident(self,record):
  with self.lock:
   if len(self.incidents)>=128:raise RuntimeError('INCIDENT128_BOUND_NO_SUPPRESSION')
   if type(record)is not dict or record.get('APEventHostNs')is not None:raise ValueError('UNPROVEN_AP_EVENT_TIME')
   ref=self._record('INCIDENT',record);self.incidents.append({**record,'phase':self.phase,'durablePhaseRef':ref});return ref
 def fail(self,reason):
  with self.lock:
   if self.closed:return
   if self.failure is None:
    if self.budget is not None and hasattr(self.journal.io,'closing'):self.journal.io.closing=True
    self.failure=str(reason);self.failureType=type(reason).__name__
    try:self.failureEventCommitRef=self._record('SESSION_FAILED',{'reason':str(reason)[:1024],'groundInferredFromProcessExit':False})
    except BaseException as append_error:self.failureAppendError=type(append_error).__name__+':'+str(append_error)
    self.phase='FAILED'
 def note_failure_detail(self,kind,detail):
  try:return self._record(kind,detail)
  except BaseException as e:
   if len(self.secondaryFailures)<16:self.secondaryFailures.append({'kind':kind,'error':type(e).__name__+':'+str(e),'commitClaimed':False})
   return None
 def snapshot(self):
  with self.lock:return {'format':'aeris-mission-supervision','version':1,'context':self.context.value(),'sourceSHA256':self.source,'phase':self.phase,'sequence':self.sequence,'failure':self.failure,'failureType':self.failureType,'failureEventCommitRef':self.failureEventCommitRef,'failureAppendError':self.failureAppendError,'secondaryFailures':list(self.secondaryFailures),'unpublishedDurableEvents':list(self.unpublishedDurableEvents),'proofs':dict(self.proofs),'incidents':list(self.incidents),'authorityRestorable':False,'nativeOwnsAllInputAuthority':True,'metadataGuardObserver':None if self.guard_observer is None else self.guard_observer.snapshot()}
 def finish(self):
  with self.lock:
   if self.closed:raise RuntimeError('LIFECYCLE_ALREADY_CLOSED')
   if self.phase not in('CLOSED','FAILED'):raise RuntimeError('LIFECYCLE_NOT_FINAL')
   if self.budget is not None and hasattr(self.journal.io,'closing'):self.journal.io.closing=True
   self.check_guard_observer();observation=self.stop_guard_observer()
   with self.observation_gate:result=self.journal.close()
   proof_audit=self.verify_proofs();self.closed=True;return {**result,'metadataGuardObservation':observation,'lifecycleProofAudit':proof_audit}
