"""Receive every bounded poll; request cadence is separate from response delivery."""
import socket,struct,time
from pilot.betaintegrated01.clock.correlation import Context,BoundedCorrelator
from .delivery import DeliveryProbe
class ClockSocket:
 def __init__(self,run,epoch,boot,sink,peer=('127.0.0.1',9014),*,maximum_seconds=60,diagnostic=None,on_matched_response=None,socket_factory=socket.socket,now_ns=time.monotonic_ns,probe=None):
  if peer!=('127.0.0.1',9014):raise ValueError('CLOCK_ENDPOINT_ALLOWLIST')
  if type(maximum_seconds)is not int or not 1<=maximum_seconds<=1960:raise ValueError('CLOCK_DURATION_BOUND')
  if not callable(on_matched_response)or not callable(now_ns)or not callable(socket_factory):raise ValueError('CLOCKTERM14_DELIVERY_CALLBACK_AND_CLOCK_REQUIRED')
  self.context=Context(run,epoch,boot);self.peer=peer;self.max_events=(maximum_seconds+15)*120+100;self.events=0;self.diagnostic=diagnostic;self.diagnostic_written=False;self.on_matched_response=on_matched_response;self.now_ns=now_ns;self.probe=probe if probe is not None else DeliveryProbe()
  self.sock=socket_factory(socket.AF_INET,socket.SOCK_DGRAM)
  try:self.sock.bind(('127.0.0.1',0));self.sock.setblocking(False)
  except BaseException:self.sock.close();raise
  def durable(row):
   if self.events>=self.max_events:
    if self.diagnostic is not None and not self.diagnostic_written:self.diagnostic(dict(reason='CLOCK_TOTAL_EVENT_CAPACITY',attemptedEvent=row,retainedEvents=self.events,complete=False));self.diagnostic_written=True
    raise RuntimeError('CLOCK_TOTAL_EVENT_CAPACITY')
   sink(row);self.events+=1
  self.correlator=BoundedCorrelator(self.context,peer,durable,max_pending=8,recent_limit=64);self.next_request=0;self.request_id=0;self.closed=False
 def _poll(self):
  if self.closed:raise RuntimeError('CLOCK_CLOSED')
  self.probe.polls+=1
  for _ in range(8):
   try:raw,ancillary,flags,peer=self.sock.recvmsg(4097)
   except BlockingIOError:break
   received=self.now_ns();self.probe.receives+=1
   try:
    if flags&socket.MSG_TRUNC:raise RuntimeError('CLOCK_DATAGRAM_TRUNCATED')
    result=self.probe.measure('CORRELATOR_RECEIVE',lambda:self.correlator.receive(raw,peer,received,self.context),originalReceiveNs=received,rawBytes=len(raw))
    if result.get('freshCalibration')is True:
     bracket=self.correlator.calibration(self.now_ns(),self.context)
     if bracket is not None:
      if bracket['id']!=result['id']or bracket['hostReceiveNs']!=result['hostReceiveNs']:raise RuntimeError('MATCHED_RESPONSE_CALIBRATION_BINDING')
      self.probe.callbacks+=1;self.probe.measure('MATCHED_CALLBACK',lambda:self.on_matched_response(bracket),id=bracket['id'],originalReceiveNs=bracket['hostReceiveNs'])
   except Exception as exc:
    if self.diagnostic is not None and not self.diagnostic_written:
     self.diagnostic(dict(reason=type(exc).__name__+':'+str(exc),rawHex=raw.hex(),peer=repr(peer),socketTruncated=bool(flags&socket.MSG_TRUNC),exactReceivedBytesRetained=not bool(flags&socket.MSG_TRUNC)));self.diagnostic_written=True
    raise
  now=self.now_ns()
  if now>=self.next_request:
   self.probe.measure('REQUEST_TICK',lambda:self.correlator.tick(now,self.context));self.request_id+=1
   self.probe.measure('REQUEST_REGISTER',lambda:self.correlator.register(self.request_id,now,self.context),id=self.request_id,originalRegisterNs=now)
   raw=struct.pack('<Q',self.request_id);sent=self.probe.measure('REQUEST_SEND',lambda:self.sock.sendto(raw,self.peer),id=self.request_id)
   if sent!=len(raw):raise RuntimeError('CLOCK_LOCAL_SEND_UNKNOWN')
   self.next_request=now+100000000
  else:self.probe.cadenceSkips+=1
 def poll(self):return self.probe.measure('POLL',self._poll)
 def calibration(self):return self.correlator.calibration(self.now_ns(),self.context)
 def close(self):self.closed=True;self.sock.close();return self.correlator.snapshot()
