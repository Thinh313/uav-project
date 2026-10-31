"""Independent CLOCKPIPE09 authority/receipt negatives, RAM IO and fake time."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,os,struct,sys,threading,time
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.foundation.owner import ClockOwner
from aeris_runtime.foundation.clock_pipeline09 import OrderedClockQueue,TentativeCorrelator
from aeris_runtime.foundation.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.clock.correlation import Context
from aeris_runtime.metadata_budget import encoded
CTX=('qa-clock09','e'*32,'b'*32);checks=[]
class MemoryJournal:
 def __init__(self):self.rows=[];self.head='0'*64
 def append_event(self,kind,data):
  row={'kind':kind,'data':json.loads(json.dumps(data)),'n':len(self.rows)+1};self.rows.append(row);self.head=hashlib.sha256(encoded(row)).hexdigest();return row['n']
def owner():
 o=ClockOwner(R/'planning/betasim-integrated01/qa/NOT_CREATED',*CTX,180,'a'*64,origin_ns=0);o.thread=SimpleNamespace(is_alive=lambda:True);o.journal=MemoryJournal();return o
def drain(o):
 while True:
  x=o.pipeline.take()
  if x is None:return
  o._commit(x)
def parser(o):return TentativeCorrelator(Context(*CTX),('127.0.0.1',9014),o.sink,max_pending=8,recent_limit=64)
def response(c,rid,sent,recv):return c.receive(struct.pack('<7Q',rid,sent+100,recv-100,0,1,0,0),('127.0.0.1',9014),recv,Context(*CTX))
def publication(o,c,rid,sent,recv):
 c.tick(sent,Context(*CTX));c.register(rid,sent,Context(*CTX));response(c,rid,sent,recv);o.stage_publication(c.calibration(recv,Context(*CTX)))
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def test(name,fn):fn();checks.append(name)
def queue_bounds():
 q=OrderedClockQueue();v={'nested':{'original':1}};q.stage('CLOCK',v);v['nested']['original']=2;x=q.take();assert json.loads(x[2])['nested']['original']==1;deny(q.take);q.finish(x)
 q=OrderedClockQueue()
 for i in range(63):q.stage('CLOCK',{'i':i})
 q.stage('PUBLICATION',{'id':1});q.take();deny(lambda:q.stage('CLOCK',{}));s=q.snapshot();assert s['highWaterEvents']==64 and s['inflightSequence']==1 and s['inflightOrQueuedUnknown'] and s['failure'];q.close_ingress();deny(lambda:q.stage('CLOCK',{}))
def tentative_not_authority():
 now=[2000];o=owner();c=parser(o)
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',side_effect=lambda:now[0]):
  publication(o,c,1,1000,2000);assert o.calibration()is None and o.publication is None;assert c.calibration(2000,Context(*CTX))['tentativeNotDurable'];drain(o);v=o.calibration();assert v['id']==1 and o.journal.rows[-1]['kind']=='CLOCK_PUBLICATION';assert v['hostReceiveNs']==2000
  invalid=owner();deny(lambda:invalid.stage_publication({'id':1}));deny(invalid.calibration)
 return o
def queue_failure_interval():
 now=[2000];o=owner();c=parser(o)
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',side_effect=lambda:now[0]):
  publication(o,c,1,1000,2000);drain(o);v=o.calibration();o.pipeline.fail(OSError('QA_EIO_EFFECTIVE_AUTHORITY_LATCH'));assert o.failed is not None;deny(o.calibration);sent=[];deny(lambda:o.dispatch(v,lambda *a:sent.append(a)));assert not sent
def stale_commit_not_retimed():
 now=[300_002_000];o=owner();c=parser(o)
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',side_effect=lambda:now[0]):
  publication(o,c,1,1000,2000);drain(o);assert o.publication is None and o.calibration()is None;pub=o.journal.rows[-1];assert pub['kind']=='CLOCK_PUBLICATION'and pub['data']['hostReceiveNs']==2000
def adapter(o):
 a=FrameAdapter.__new__(FrameAdapter);a.clock_owner=o;a.failed=a.closed=False;a.frames=a.stage_rows=0;a.max_frames=10;a.peer=None;a.origin_ns=0;a.first_rx=a.last_rx=None;a.last_sensor_send_ns=0;a.scene=None;a.current=None;a.model=SimpleNamespace(t=0,n=0);a.sent=[];a.stages=[];a.capture_failure=lambda *a:None
 def reject(*args,**kwargs):a.failed=True
 a.reject=reject
 def step(pwm,dt):a.model.n+=1;a.model.t+=dt;return{'t':a.model.t}
 a.model.step=step
 def record(frame,raw,compute,dispatch):dispatch(compute(raw))
 a.journal=SimpleNamespace(record_frame=record,append_stage=lambda f,row:a.stages.append(row.copy()))
 return a
def wait_new_and_original_receipt():
 now=[2000];o=owner();c=parser(o)
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',side_effect=lambda:now[0]):
  publication(o,c,1,1000,2000);drain(o);now[0]=300_000_000;c.tick(now[0],Context(*CTX));c.register(2,now[0],Context(*CTX));a=adapter(o)
  def wait(_):
   assert a.model.n==0 and not a.current['journalAdmissionAttempted'];now[0]=350_000_000;response(c,2,300_000_000,now[0]);o.stage_publication(c.calibration(now[0],Context(*CTX)));drain(o)
  with patch.object(o.pipeline.condition,'wait',side_effect=wait):a.receive(SERVO.pack(18458,1200,0,*([1000]*16)),('127.0.0.1',9000),lambda b:a.sent.append(b)or len(b),clock_read=o.calibration,admission_deadline_ns=490_000_000,original_receive_ns=299_000_000)
  assert a.model.n==a.frames==a.stage_rows==len(a.sent)==1;v=a.stages[0];assert v['receiveSinceOriginNs']==v['originalReceiveSinceOriginNs']==299_000_000 and v['clockAdmissionSinceOriginNs']==350_000_000 and v['clockWaitPriorID']==1 and v['unadmittedClockWaitNs']==50_000_000 and v['clockIDAtAdmission']==2 and v['clockAtOriginalReceiptStatus']==0 and v['originalReceiveKind']==1 and 'clockIDAtReceive'not in v
def expired_original_bound():
 now=[2000];o=owner();c=parser(o)
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',side_effect=lambda:now[0]):
  publication(o,c,1,1000,2000);drain(o);now[0]=300_000_000;c.tick(now[0],Context(*CTX));a=adapter(o)
  with patch.object(o.pipeline.condition,'wait',side_effect=lambda t:now.__setitem__(0,now[0]+10_000_000)):
   deny(lambda:a.receive(SERVO.pack(18458,1200,0,*([1000]*16)),('127.0.0.1',9000),lambda b:a.sent.append(b),clock_read=o.calibration,admission_deadline_ns=325_000_000,original_receive_ns=299_000_000))
  assert a.model.n==0 and not a.sent and a.frames==0 and a.failed and now[0]<400_000_000
def reentrant_after_validation():
 o=owner();c=parser(o)
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',return_value=2000):
  publication(o,c,1,1000,2000);drain(o);ref=o.calibration();before=o._validated;sent=[]
  def changed(*args):value=before(*args);o.pipeline.fail(OSError('QA_AFTER_VALIDATE'));return value
  o._validated=changed;deny(lambda:o.dispatch(ref,lambda n:sent.append(n)));assert not sent
def concurrent_started_permit():
 o=owner();c=parser(o);began=threading.Event();go=threading.Event();fault_done=threading.Event();errors=[];sent=[]
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',return_value=2000):
  publication(o,c,1,1000,2000);drain(o);ref=o.calibration()
  def callback(n):began.set();assert go.wait(2);sent.append(n)
  def dispatch():
   try:o.dispatch(ref,callback)
   except BaseException as e:errors.append(str(e))
  def fault():o.pipeline.fail(OSError('QA_CONCURRENT'));fault_done.set()
  a=threading.Thread(target=dispatch);a.start();assert began.wait(2);b=threading.Thread(target=fault);b.start();until=time.monotonic()+1
  while o.pipeline.requested_failure is None and time.monotonic()<until:time.sleep(.001)
  assert o.pipeline.requested_failure is not None and o.pipeline.failure is None and not fault_done.is_set();assert o.pipeline.snapshot()['failure']is None
  go.set();a.join(2);b.join(2);assert not a.is_alive()and not b.is_alive()and not errors and len(sent)==1 and o.pipeline.failure;deny(lambda:o.dispatch(ref,lambda n:sent.append(n)));assert len(sent)==1
def caught_socket_fault_before_owner_lock():
 o=owner();c=parser(o);o.journal.guard=SimpleNamespace(check=lambda *a:None)
 class Socket:
  def poll(self):raise OSError('QA_SOCKET_CAUGHT_EIO')
  def close(self):return{}
 o.clock=Socket()
 with patch('aeris_runtime.foundation.owner.time.monotonic_ns',return_value=2000):
  publication(o,c,1,1000,2000);drain(o)
  with o.lock:
   worker=threading.Thread(target=o._socket_run);worker.start();until=time.monotonic()+1
   while o.pipeline.requested_failure is None and time.monotonic()<until:time.sleep(.001)
   requested=o.pipeline.requested_failure
   if requested is not None:deny(o.calibration)
  worker.join(2);assert not worker.is_alive();assert requested is not None,'caught fault waited owner lock before recording request';assert o.failed and o.pipeline.failure
test('immutable_bytes_queue_publication_counts64_including_inflight_close_refusal',queue_bounds)
test('tentative_correlator_never_authority_until_ordered_publication_commit',tentative_not_authority)
test('known_queue_fault_before_owner_latch_denies_lastgood_calibration_and_dispatch',queue_failure_interval)
test('stale_durable_publication_retained_but_not_retimed_or_exposed',stale_commit_not_retimed)
test('one_unadmitted_wait_new_ID_and_original_receipt_fields_no_model_before_commit',wait_new_and_original_receipt)
test('original_case_deadline_refuses_without_model_intent_or_sensor',expired_original_bound)
test('reentrant_fault_after_validation_zero_callback',reentrant_after_validation)
test('concurrent_started_permit_before_effective_fault_then_no_new_permits',concurrent_started_permit)
test('caught_socket_fault_records_request_before_waiting_authority_lock',caught_socket_fault_before_owner_lock)
pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[T/'source/aeris_runtime/foundation'/n for n in('owner.py','clock_socket.py','clock_pipeline09.py','frame_adapter.py')]}
out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/clockpipe09-01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-clockpipe09-source-qa','status':'PASS_RAM_IO_FAKE_CLOCK_NOT_ACTUAL_TIMING_OR_FSYNC','checks':checks,'sourcePins':pins,'actorsStarted':False,'durabilityInjected':True,'actualUDP':False,'actualAndroidSITL':False}));print(json.dumps({'status':'PASS','checks':len(checks),'path':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
