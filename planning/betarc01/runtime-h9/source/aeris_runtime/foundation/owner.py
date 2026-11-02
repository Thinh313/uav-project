"""CLOCKPIPE09: tentative socket ingress separated from durable authority."""
from importlib import import_module
from pathlib import Path
import hashlib,json,threading,time
from pilot.betaintegrated01.runtime.ap_stage import canonical,exclusive
from .clock_socket import ClockSocket
from .delivery import DeliveryProbe
from .clock_pipeline09 import OrderedClockQueue,TentativeCorrelator,SerializedGuard,ClockIO
BASE=import_module('aeris_runtime.foundation.owner_base')
Publication=BASE.Publication
class ClockOwner(BASE.ClockOwner):
 def __init__(self,*args,socket_factory=None,**kwargs):
  self.delivery=DeliveryProbe();self.delivery_written=False;self.delivery_publication_error=None;self.pipeline=OrderedClockQueue();self.socket_done=threading.Event();self.socket_thread=None;self.socket_result=None;self.socket_failure=None;self.waits=0
  def make_socket(*a,**kw):return ClockSocket(*a,**kw,on_matched_response=self.stage_publication,probe=self.delivery,correlator_factory=TentativeCorrelator)
  super().__init__(*args,socket_factory=socket_factory or make_socket,**kwargs)
  self.lock=threading.RLock();self.pipeline.bind_authority(self.lock,self.latch_failure);self.diagnostic_io=ClockIO()
 def _append(self,kind,data):return self.delivery.measure('DURABLE_APPEND',lambda:super(ClockOwner,self)._append(kind,data),eventKind=kind,clockKind=data.get('kind'),id=data.get('id'))
 def publish(self,bracket):
  return self.delivery.measure('PUBLICATION',lambda:super(ClockOwner,self).publish(bracket),id=None if bracket is None else bracket.get('id'),originalReceiveNs=None if bracket is None else bracket.get('hostReceiveNs'))
 def sink(self,row):
  try:
   if any(row.get(k)!=v for k,v in [('run',self.run),('epoch',self.epoch),('boot',self.boot)]):raise ValueError('CLOCK_OWNER_FOREIGN_EVENT')
   if self.pipeline.staged>=self.maximum_events-1:raise RuntimeError('CLOCK_OWNER_TOTAL_EVENTS_CAPACITY')
   return self.pipeline.stage('CLOCK',row)
  except BaseException as error:self.pipeline.fail(error);self.stop_event.set();raise
 def stage_publication(self,bracket):
  try:
   if type(bracket)is not dict or bracket.get('tentativeNotDurable')is not True:raise ValueError('CLOCKPIPE09_TENTATIVE_MARKER_REQUIRED')
   if self.pipeline.staged>=self.maximum_events-1:raise RuntimeError('CLOCK_OWNER_TOTAL_EVENTS_CAPACITY')
   return self.pipeline.stage('PUBLICATION',bracket)
  except BaseException as error:self.pipeline.fail(error);self.stop_event.set();raise
 def socket_diagnostic(self,data):
  # Source fault latch precedes optional diagnostic IO, never the reverse.
  error=RuntimeError('CLOCKPIPE09_SOCKET:'+str(data.get('reason','UNKNOWN')));self.pipeline.fail(error);self.stop_event.set();return self.diagnostic(data)
 def _commit(self,item):
  _,kind,raw=item;data=json.loads(raw)
  if kind=='CLOCK':
   ref=self._append('CLOCK',data)
   if data.get('kind')=='RESPONSE'and data.get('freshCalibration')is True:self.last_response=(dict(data),dict(ref))
  else:
   # Retain every publication row, even if it became stale during durable IO.
   # A stale committed row is evidence only and never becomes visible authority.
   if self.last_response is None or any(self.last_response[0].get(k)!=data.get(k)for k in('id','hostReceiveNs','offsetLowNs','offsetHighNs','uncertaintyNs')):raise ValueError('CLOCK_PUBLICATION_REQUIRES_DURABLE_MATCHED_RESPONSE')
   row,ref=self.last_response;record={'run':self.run,'epoch':self.epoch,'boot':self.boot,'id':row['id'],'responseSequence':ref['sequence'],'responseSHA256':ref['sha256'],'responseDurableHostNs':ref['durableHostNs'],'publicationBeginHostNs':time.monotonic_ns(),'hostReceiveNs':row['hostReceiveNs'],'offsetLowNs':row['offsetLowNs'],'offsetHighNs':row['offsetHighNs']};committed=self._append('CLOCK_PUBLICATION',record)
   value=Publication(self.run,self.epoch,self.boot,row['id'],row['hostReceiveNs'],row['offsetLowNs'],row['offsetHighNs'],row['uncertaintyNs'],ref['sequence'],ref['sha256'],committed['sequence'],committed['sha256'],committed['durableHostNs'])
   with self.lock:
    if self.failed is not None or self.pipeline.failure is not None or self.pipeline.requested_failure is not None:raise RuntimeError('CLOCK_OWNER_FAILURE_LATCHED')
    if self.publication is not None and(value.id<=self.publication.id or value.hostReceiveNs<self.publication.hostReceiveNs):raise ValueError('CLOCK_PUBLICATION_REGRESSION')
    if 0<=time.monotonic_ns()-value.hostReceiveNs<=250_000_000:self.publication=value;self.history.append(value);self.last_publication_id=value.id
  self.pipeline.finish(item)
 def calibration(self):
  # Pending durable work is not a fault waiver: expose NO stale authority.
  # The one-frame admission wait below may await a NEW publication, never clear
  # an existing latch. Outside pending work, the original failure latch remains.
  with self.lock:
   if self.failed is not None:raise RuntimeError('CLOCK_OWNER_FAILED:'+self.failed)
   if self.pipeline.failure is not None or self.pipeline.requested_failure is not None:raise RuntimeError('CLOCKPIPE09_QUEUE_FAILURE:'+str(self.pipeline.failure or self.pipeline.requested_failure))
   if self.publication is not None and time.monotonic_ns()-self.publication.hostReceiveNs>250_000_000 and self.pipeline.pending():return None
  return super().calibration()
 def _validated(self,value,now):
  # Applies to inherited dispatch as well: even the tiny queue-fault -> owner
  # latch interval cannot authorize a last-good reference.
  if self.pipeline.failure is not None or self.pipeline.requested_failure is not None:raise RuntimeError('CLOCKPIPE09_QUEUE_FAILURE:'+str(self.pipeline.failure or self.pipeline.requested_failure))
  return super()._validated(value,now)
 def pending_prior_id(self):
  # Diagnostic identity only; never a calibration/dispatch permission.
  with self.lock:return 0 if self.publication is None else self.publication.id
 def dispatch(self,reference,callback):
  # Queue failure publication shares this authority lock. Queue.condition is
  # NEVER held over callback/network or journal IO. Requested faults also
  # refuse the next permit; observation/effective times remain distinct.
  with self.lock:
   try:
    value=Publication(**reference);checked=time.monotonic_ns();self._validated(value,checked)
    if self.pipeline.failure is not None or self.pipeline.requested_failure is not None:raise RuntimeError('CLOCKPIPE09_QUEUE_FAILURE:'+str(self.pipeline.failure or self.pipeline.requested_failure))
   except Exception as error:
    if self.failed is None:self.failed=type(error).__name__+':'+str(error)[:512]
    raise
   return callback(checked)
 def wait_for_frame(self,deadline_ns,prior_id=-1):
  if type(deadline_ns)is not int or type(prior_id)is not int:raise ValueError('CLOCKPIPE09_TYPED_ADMISSION_BOUND')
  started=time.monotonic_ns();end=min(started+100_000_000,deadline_ns)
  self.waits+=1
  while True:
   if time.monotonic_ns()>=end:raise TimeoutError('CLOCKPIPE09_UNADMITTED_WAIT100MS_DEADLINE')
   value=self.calibration()
   if value is not None and value['id']>prior_id:return value
   if not self.pipeline.pending():raise RuntimeError('CLOCKPIPE09_NO_PENDING_DURABLE_CLOCK')
   with self.pipeline.condition:self.pipeline.condition.wait(min(.005,max(0,(end-time.monotonic_ns())/1e9)))
 def _socket_run(self):
  try:
   started=time.monotonic()
   while not self.stop_event.wait(.01):
    # Same original periodic guard, now source-owned socket thread. The writer
    # has its separate unchanged per-write guards; no MetadataBudget IO here.
    self.journal.guard.check()
    if time.monotonic()-started>self.maximum_seconds+30:raise RuntimeError('CLOCK_OWNER_LIFETIME')
    self.clock.poll()
   self.socket_result=self.clock.close()
  except BaseException as error:
   self.socket_failure=type(error).__name__+':'+str(error)[:512];self.pipeline.fail(error);self.stop_event.set()
  finally:
   try:self.clock.close()
   except Exception:pass
   self.pipeline.close_ingress();self.socket_done.set()
 def _run(self):
  try:
   from aeris_runtime.policy import clock_policy
   self.journal=self.journal_factory(self.out/'clock-journal',self.run,self.epoch,clock_policy(self.maximum_seconds))
   self.journal.guard=SerializedGuard(self.journal.guard)
   self._append('CLOCK_OWNER_BINDING',{'run':self.run,'epoch':self.epoch,'boot':self.boot,'sourceAmendmentSHA256':self.source_amendment,'originHostNs':self.origin_ns,'maximumEvents':self.maximum_events,'maximumRecordBytes':2048})
   self.clock=self.socket_factory(self.run,self.epoch,self.boot,self.sink,maximum_seconds=self.maximum_seconds,diagnostic=self.socket_diagnostic);self.socket_thread=threading.Thread(target=self._socket_run,name='clockpipe09-tentative-socket',daemon=False);self.socket_thread.start();self.ready.set()
   while True:
    if self.failed is not None:raise RuntimeError('CLOCK_OWNER_FAILED:'+self.failed)
    item=self.pipeline.take()
    if item is not None:self._commit(item);continue
    if self.socket_done.is_set():break
    with self.pipeline.condition:self.pipeline.condition.wait(.01)
   result=self.journal.close();self.result={'status':'CLOCK_OWNER_CLOSED_NOT_FLIGHT_ACCEPTANCE','run':self.run,'epoch':self.epoch,'boot':self.boot,'events':self.events,'commitAnchor':result['commitAnchor'],'pipeline':self.pipeline.snapshot(),'tentativeSocket':self.socket_result}
  except BaseException as error:
   self.pipeline.fail(error);self.stop_event.set()
   if self.journal is not None:
    try:self.journal.abort(self.failed)
    except Exception:pass
   self.result={'status':'CLOCK_OWNER_FAILED_RETAINED_PREFIX','run':self.run,'epoch':self.epoch,'boot':self.boot,'events':self.events,'error':self.failed,'errorChain':BASE.D.exception_chain(error),'io':self.diagnostic_io.snapshot(),'pipeline':self.pipeline.snapshot(),'commitAnchor':None}
  finally:
   self.stop_event.set()
   if self.socket_thread is not None:self.socket_thread.join(timeout=2)
   if self.socket_thread is not None and self.socket_thread.is_alive():self.pipeline.fail(RuntimeError('CLOCKPIPE09_SOCKET_CLOSE_TIMEOUT'));self.result.update(status='CLOCK_OWNER_FAILED_RETAINED_PREFIX',error=self.failed,commitAnchor=None)
   self.done.set()
   try:exclusive(self.out/'clock-owner-result.json',canonical(self.result)+b'\n')
   except Exception:pass
 def _write_delivery(self):
  if self.delivery_written:return
  self.delivery_written=True
  try:
   v=self.delivery.snapshot();v.update(run=self.run,epoch=self.epoch,boot=self.boot,ownerDone=self.done.is_set(),ownerFailure=self.failed,pipeline=self.pipeline.snapshot(),clockOriginalIO=self.diagnostic_io.snapshot(),unadmittedWaitCalls=self.waits,sourceSHA256={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in(__file__,__import__(ClockSocket.__module__,fromlist=['x']).__file__,__import__(DeliveryProbe.__module__,fromlist=['x']).__file__,__import__(OrderedClockQueue.__module__,fromlist=['x']).__file__)})
   raw=canonical(v)+b'\n'
   if len(raw)>32768:raise ValueError('DELIVERY_DIAGNOSTIC32KiB_BOUND')
   if self.journal is None:raise RuntimeError('DELIVERY_NO_PRIMED_OWNER_JOURNAL_GUARD')
   self.journal.guard.check(len(raw));exclusive(self.out/'clock-delivery-diagnostic.json',raw)
  except Exception as e:self.delivery_publication_error=type(e).__name__+':'+str(e)[:256]
 def close(self,timeout=5):
  try:return super().close(timeout=timeout)
  finally:self._write_delivery()
