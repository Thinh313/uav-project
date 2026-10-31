"""Explicit isolated writer: byte-identical v2 envelope prepared once; same barriers."""
from importlib import import_module
import base64,hashlib,time,zlib
BASE=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal')
D=import_module('planning.betaintegrated01.cockpit05-clockdiag01.diagnostics')
W=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal.writer')
class ProfileIO(D.DiagnosticIO):
 def __init__(self,profile,hook=None):super().__init__(hook);self.profile=profile
 def _timed(self,kind,fd,n,operation):
  begin=time.monotonic_ns();cpu=time.thread_time_ns();error=None
  try:return operation()
  except BaseException as e:error=D.exception_chain(e);raise
  finally:
   cpu_end=time.thread_time_ns();end=time.monotonic_ns();self.operations+=1;self.last.append(dict(ordinal=self.operations,operation=kind,fd=fd,requestedBytes=n,beginHostNs=begin,endHostNs=end,wallNs=end-begin,threadCPUNs=cpu_end-cpu,nonCPUWallNs=max(0,end-begin-cpu_end+cpu),nonCPUWallMeaning='SYSCALL_WAIT_AND_OR_DESCHEDULE_NOT_FILESYSTEM_ONLY',errorChain=error));self.profile.observe(kind,begin,end,cpu_end-cpu)
class MeasuredGuard:
 """Composition only: every original actual guard call remains forwarded exactly."""
 def __init__(self,guard,profile):self._guard,self._profile=guard,profile
 def __getattr__(self,key):return getattr(self._guard,key)
 def check(self,*args,**kwargs):
  with self._profile.measure('guard'):return self._guard.check(*args,**kwargs)
class SegmentedJournal(BASE.SegmentedJournal):
 def __init__(self,*args,profile,**kwargs):
  self.profile=profile;super().__init__(*args,**kwargs);self.guard=MeasuredGuard(self.guard,profile)
 def _record(self,kind,frame,payload,sync=False):
  # Same schema/order/hash/CRC/bytes and all inherited write/fsync/failure behavior.
  with self.profile.measure('serialize'):
   if self.seq>=2**63-1:raise W.JournalError('SEQUENCE_BOUND')
   W.bounded_value(payload,self.policy.max_record_bytes)
   body={'v':W.VERSION,'run':self.run,'epoch':self.epoch,'segment':self.segment,'seq':self.seq,'previous':self.head,'kind':kind,'frame':frame,'payload':payload}
   raw=W.encode(body);head=W.digest(bytes.fromhex(self.head)+raw);b=b'{"body":'+raw+b',"crc32":"'+format(zlib.crc32(raw),'08x').encode()+b'","sha256":"'+head.encode()+b'"}\n'
   if len(b)>self.policy.max_record_bytes:raise W.JournalError('RECORD_SIZE_BOUND')
   if self.segment_used+len(b)>self.policy.segment_bytes or self.used+len(b)>self.policy.quota_bytes:raise W.JournalError('RECORD_CAPACITY')
  self._write_all(self.fd,b)
  if sync:self.io.fsync(self.fd)
  self.segment_hash.update(b);self.segment_used+=len(b);self.used+=len(b);self.head=head;self.seq+=1;return self.seq-1
 def append_stage(self,*args,**kwargs):
  with self.profile.measure('STAGE'):return super().append_stage(*args,**kwargs)
