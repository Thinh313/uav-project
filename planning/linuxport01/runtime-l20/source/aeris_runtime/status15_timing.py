"""Same-host calling-thread auxiliary timings, never replacement safety proof."""
import contextlib,time
CODES=('entry','validated','reserved','sendStart','bytesSent','firstByte','frameComplete','ackJoined','validateStart','validateEnd','persistStart','payloadPersisted','requestPersisted','returnReady')
class StatusTiming:
 def __init__(self,*,now=time.monotonic_ns,cpu=time.thread_time_ns):self.now=now;self.cpu=cpu;self.points={};self.fsync={};self.point('entry')
 def point(self,name):
  if name not in CODES or name in self.points:raise ValueError('STATUS15_FIXED_UNIQUE_TIMING')
  self.points[name]=[self.now(),self.cpu()]
 @contextlib.contextmanager
 def span(self,code):
  if code not in('payload_fsync','ledger_fsync'):
   yield;return
  wall=self.now();cpu=self.cpu()
  try:yield
  finally:
   w=self.now()-wall;c=self.cpu()-cpu
   if w<0 or c<0:raise ValueError('STATUS15_TIMING_CLOCK_MONOTONIC')
   r=self.fsync.setdefault(code,[0,0,0,0,0]);r[0]+=1;r[1]+=w;r[2]=max(r[2],w);r[3]+=c;r[4]=max(r[4],c)
 def projection(self,*,final=False):
  return {'codes':list(CODES),'points':[[CODES.index(k),*self.points[k]]for k in CODES if k in self.points],'fsync':dict(self.fsync),'clockDomain':'HOST_MONOTONIC_AND_CALLING_THREAD_CPU','nestedAndConcurrentWorkMayOverlap':True,'ACKWorkerNotIncludedInThreadCPU':True,'proofAndRequestReceiptSelfFsyncExcluded':not final,'measuredCut':'ALL_REQUEST_PERSISTENCE_AND_OUTER_RELEASE_COMPLETE_BEFORE_PYTHON_RETURN'if final else'RESPONSE_BYTES_DURABLE_BEFORE_PROOF_AND_REQUEST_RECEIPT','diagnosticNotSafetyProof':True}
