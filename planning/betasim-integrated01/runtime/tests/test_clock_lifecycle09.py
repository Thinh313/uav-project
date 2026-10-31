"""Selected ClockOwner._run lifecycle on real threads with fake local UDP."""
from pathlib import Path
from unittest.mock import patch
import hashlib,json,struct,sys,time,threading,shutil
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(P.parent),str(T/'source'),str(R)]
import test_clock_pipeline09 as helpers
from aeris_runtime.foundation.owner import ClockOwner,Publication
from aeris_runtime.foundation.clock_socket import ClockSocket
from aeris_runtime.foundation.clock_pipeline09 import TentativeCorrelator
from aeris_runtime.metadata_budget import encoded
LAB=R/'evidence/betasim-integrated01/runtime/.clocklife09';C=helpers.CTX
class AutoUDP(helpers.UDP):
 def sendto(self,raw,peer):
  n=super().sendto(raw,peer);self.responses.append(helpers.response(int.from_bytes(raw,'little'),time.monotonic_ns()));return n
def make(name,hook=None):
 out=LAB/name;out.mkdir();u=AutoUDP();o=None
 def socket_factory(*a,**kw):return ClockSocket(*a,**kw,on_matched_response=o.stage_publication,socket_factory=lambda *a:u,correlator_factory=TentativeCorrelator)
 o=ClockOwner(out,*C,180,'a'*64,socket_factory=socket_factory,journal_factory=lambda root,*a:helpers.Journal(root,o.diagnostic_io));o.diagnostic_io.hook=hook or(lambda *a:None);return o,u
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);owners=[];groups=[]
 try:
  o,u=make('normal');owners.append(o);o.start();assert o.ready.wait(1);until=time.monotonic()+1;value=None
  while time.monotonic()<until:
   value=o.calibration()
   if value is not None:break
   time.sleep(.002)
  assert value is not None and value['clockPublicationSequence']>value['clockResponseSequence'];result=o.close(timeout=2);assert result['status']=='CLOCK_OWNER_CLOSED_NOT_FLIGHT_ACCEPTANCE'and not o.thread.is_alive()and not o.socket_thread.is_alive()and u.closed and o.pipeline.snapshot()['queued']==0 and o.pipeline.snapshot()['inflightSequence']is None;groups.append('actual-selected-run-two-thread-start-postfsync-publication-positive-close-queue-drained-socketclosed-no-orphan')
  io=json.loads((o.out/'clock-delivery-diagnostic.json').read_bytes())['clockOriginalIO'];assert io['totalObservedOperations']>0 and {r['operation']for r in io['lastOperations']}=={'write','fsync'};groups.append('normal-close-persists-real-clock-oswrite-fsync-subspans-in-existing32768-diagnostic')
  seen=[0]
  def fault(kind,*args):
   if kind=='fsync':
    seen[0]+=1
    if seen[0]==4:raise OSError('SOURCE_FSYNC_EIO_RESPONSE')
  o,u=make('EIO-response',fault);owners.append(o);o.start();assert o.done.wait(2);helpers.deny(lambda:o.close(timeout=2),'CLOCK_OWNER_FAILED');assert o.publication is None and o.result['commitAnchor']is None and o.pipeline.snapshot()['inflightOrQueuedUnknown']and not o.socket_thread.is_alive()and u.closed;groups.append('actual-run-response-fsyncEIO-zero-authority-unknown-prefix-sourcefailed-and-boththreadsclosed')
  # A fault already known to the queue must block the tiny owner-latch window.
  o,u=make('queue-latch-race');owners.append(o);o.thread=type('Alive',(),{'is_alive':lambda s:True})();t=time.monotonic_ns();o.publication=Publication(*C,1,t,0,0,0,1,'a'*64,2,'b'*64,t);o.history.append(o.publication);ref=o.calibration();o.pipeline.fail(OSError('KNOWN_QUEUE_EIO'));called=[];helpers.deny(lambda:o.calibration(),'KNOWN_QUEUE_EIO');helpers.deny(lambda:o.dispatch(ref,lambda at:called.append(at)),'QUEUE_FAILURE');assert not called;groups.append('known-queue-failure-before-owner-latch-blocks-lastgood-calibration-and-inherited-dispatch')
  # A foreign/tampered publication cannot join an unrelated durable response.
  o,u=make('wrong-marker');owners.append(o);o.journal=helpers.Journal(o.out/'clock-journal',o.diagnostic_io);o.last_response=({'id':1,'hostReceiveNs':t,'offsetLowNs':0,'offsetHighNs':0,'uncertaintyNs':0},{'sequence':1,'sha256':'a'*64,'durableHostNs':t});o.stage_publication({'tentativeNotDurable':True,'id':1,'hostReceiveNs':t+1,'offsetLowNs':0,'offsetHighNs':0,'uncertaintyNs':0});helpers.deny(lambda:o._commit(o.pipeline.take()),'DURABLE_MATCHED_RESPONSE');assert o.publication is None;groups.append('publication-original-receive-offset-uncertainty-all-exactjoin-before-authority')
  report={'format':'aeris-clockpipe09-selected-owner-lifecycle-mock','status':'PASS_REAL_THREADS_FILE_FSYNC_FAKE_LOCAL_UDP_NO_SIMULATOR_ACTORS','groups':groups,'sourceSHA256':hashlib.sha256((T/'source/aeris_runtime/foundation/owner.py').read_bytes()).hexdigest(),'actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))}
 finally:
  for o in owners:
   o.stop_event.set()
   if o.socket_thread is not None and o.socket_thread.is_alive():o.socket_thread.join(2)
   if o.journal is not None:o.journal.close()
  shutil.rmtree(LAB)
 out=R/'evidence/betasim-integrated01/runtime/clockpipe09-lifecycle-mock02.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
