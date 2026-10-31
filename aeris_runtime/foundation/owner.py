"""Narrow clock delivery wiring; immutable publication/latch/dispatch are inherited."""
from importlib import import_module
from pathlib import Path
import hashlib,json
from pilot.betaintegrated01.runtime.ap_stage import canonical,exclusive
from .clock_socket import ClockSocket
from .delivery import DeliveryProbe
BASE=import_module('aeris_runtime.foundation.owner_base')
Publication=BASE.Publication
class ClockOwner(BASE.ClockOwner):
 def __init__(self,*args,socket_factory=None,**kwargs):
  self.delivery=DeliveryProbe();self.delivery_written=False;self.delivery_publication_error=None
  def make_socket(*a,**kw):return ClockSocket(*a,**kw,on_matched_response=self.publish,probe=self.delivery)
  super().__init__(*args,socket_factory=socket_factory or make_socket,**kwargs)
 def _append(self,kind,data):return self.delivery.measure('DURABLE_APPEND',lambda:super(ClockOwner,self)._append(kind,data),eventKind=kind,clockKind=data.get('kind'),id=data.get('id'))
 def publish(self,bracket):
  return self.delivery.measure('PUBLICATION',lambda:super(ClockOwner,self).publish(bracket),id=None if bracket is None else bracket.get('id'),originalReceiveNs=None if bracket is None else bracket.get('hostReceiveNs'))
 def _write_delivery(self):
  if self.delivery_written:return
  self.delivery_written=True
  try:
   v=self.delivery.snapshot();v.update(run=self.run,epoch=self.epoch,boot=self.boot,ownerDone=self.done.is_set(),ownerFailure=self.failed,sourceSHA256={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in(__file__,__import__(ClockSocket.__module__,fromlist=['x']).__file__,__import__(DeliveryProbe.__module__,fromlist=['x']).__file__)})
   raw=canonical(v)+b'\n'
   if len(raw)>32768:raise ValueError('DELIVERY_DIAGNOSTIC32KiB_BOUND')
   if self.journal is None:raise RuntimeError('DELIVERY_NO_PRIMED_OWNER_JOURNAL_GUARD')
   self.journal.guard.check(len(raw));exclusive(self.out/'clock-delivery-diagnostic.json',raw)
  except Exception as e:self.delivery_publication_error=type(e).__name__+':'+str(e)[:256]
 def close(self,timeout=5):
  try:return super().close(timeout=timeout)
  finally:self._write_delivery()
