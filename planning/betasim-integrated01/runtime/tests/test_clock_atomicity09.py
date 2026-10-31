"""Authority/fault linearization causal tests, real threads, no simulator actors."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys,threading,time,shutil
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(P.parent),str(T/'source'),str(R)]
import test_clock_pipeline09 as h
from aeris_runtime.foundation.owner import ClockOwner,Publication
from aeris_runtime.metadata_budget import encoded
LAB=R/'evidence/betasim-integrated01/runtime/.clockatomic09'
def owner(name):
 p=LAB/name;p.mkdir();o=ClockOwner(p,*h.CTX,180,'a'*64);o.thread=SimpleNamespace(is_alive=lambda:True);now=time.monotonic_ns();o.publication=Publication(*h.CTX,1,now,0,0,0,1,'a'*64,2,'b'*64,now);o.history.append(o.publication);return o
def run():
 assert not LAB.exists();LAB.mkdir();groups=[];pins={str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(T/'source/aeris_runtime/foundation/owner.py',T/'source/aeris_runtime/foundation/clock_pipeline09.py')}
 try:
  o=owner('reentrant');ref=o.calibration();original=o._validated;calls=[]
  def validate(value,now):original(value,now);o.pipeline.fail(OSError('AFTER_VALIDATION_BEFORE_CALLBACK'))
  o._validated=validate;h.deny(lambda:o.dispatch(ref,lambda _:calls.append('SENSOR')),'QUEUE_FAILURE');assert not calls and o.pipeline.failure and o.failed;groups.append('reentrant-fault-after-validation-before-callback-zero-sensor')
  o=owner('concurrent');ref=o.calibration();entered=threading.Event();release=threading.Event();fault_done=threading.Event();errors=[];sent=[]
  def callback(at):entered.set();assert release.wait(1);sent.append(at)
  def dispatch():
   try:o.dispatch(ref,callback)
   except BaseException as e:errors.append(str(e))
  def fault():o.pipeline.fail(OSError('CONCURRENT_EIO'));fault_done.set()
  a=threading.Thread(target=dispatch);a.start();assert entered.wait(1);b=threading.Thread(target=fault);b.start();until=time.monotonic()+1
  while not o.pipeline.requested_failure and time.monotonic()<until:time.sleep(.001)
  assert o.pipeline.requested_failure and o.pipeline.failure is None and not fault_done.is_set();release.set();a.join(1);b.join(1);assert not a.is_alive()and not b.is_alive()and not errors and len(sent)==1 and o.pipeline.failure;h.deny(lambda:o.dispatch(ref,lambda _:sent.append(0)),'QUEUE_FAILURE');assert len(sent)==1;groups.append('permit-linearizes-before-concurrent-fault-effective-latch-no-queuecondition-over-callback-next-permit-denied')
  o=owner('publication');o.publication=None;o.history.clear();o.journal=h.Journal(o.out/'clock-journal',o.diagnostic_io);now=time.monotonic_ns();o.last_response=({'id':2,'hostReceiveNs':now,'offsetLowNs':0,'offsetHighNs':0,'uncertaintyNs':0},{'sequence':1,'sha256':'a'*64,'durableHostNs':now});o.stage_publication({'tentativeNotDurable':True,**o.last_response[0]});append=o._append
  def append_then_fault(kind,data):
   result=append(kind,data)
   if kind=='CLOCK_PUBLICATION':o.pipeline.fail(OSError('AFTER_FSYNC_BEFORE_EXPOSE'))
   return result
  o._append=append_then_fault;h.deny(lambda:o._commit(o.pipeline.take()),'FAILURE_LATCHED');assert o.publication is None and not o.history and o.pipeline.snapshot()['inflightOrQueuedUnknown'];o.journal.close();groups.append('publication-fsync-completes-but-effective-fault-before-exposure-zero-authority-unknown-retained')
  o=owner('fatal-ingress');caught=[]
  def fatal_ingress():
   try:o.sink({'kind':'TICK','tooLarge':'x'*3000})
   except BaseException as e:caught.append(str(e))
  with o.lock:
   worker=threading.Thread(target=fatal_ingress);worker.start();until=time.monotonic()+1
   while not o.pipeline.requested_failure and time.monotonic()<until:time.sleep(.001)
   assert o.pipeline.requested_failure and o.failed is None and o.pipeline.failure is None;h.deny(lambda:o.calibration(),'QUEUE_FAILURE')
  worker.join(1);assert not worker.is_alive()and caught and o.failed and o.pipeline.failure;groups.append('actual-owner-ingress-catch-records-requested-fault-before-blocking-owner-latch')
  assert pins=={k:hashlib.sha256((T/k).read_bytes()).hexdigest()for k in pins}
  report={'format':'aeris-clockpipe09-authority-fault-linearization','version':1,'status':'PASS_REAL_THREADS_FAKE_TIME_PEERS_NO_SIMULATOR_ACTORS','groups':groups,'sourceSHA256':pins,'actorsStarted':False,'sourceChangedDuringTest':False,'scope':'PERMIT_START_VS_EFFECTIVE_FAULT_LINEARIZATION_NOT_PREEMPTION_OF_AN_ALREADY_STARTED_SEND','scratchRemoved':str(LAB.relative_to(R))}
 finally:shutil.rmtree(LAB)
 out=R/'evidence/betasim-integrated01/runtime/clockpipe09-atomicity-mock02.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':run()
