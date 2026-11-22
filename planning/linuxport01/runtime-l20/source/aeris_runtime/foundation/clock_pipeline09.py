"""CLOCKPIPE09 tentative socket state, never an authority/calibration source.

The frozen correlator algorithm is reused only as an untrusted staging parser.
Its sink here is an ordered bounded queue, NOT the original durable-sink API.
Only ClockOwner's separate writer can publish a post-fsync Publication.
"""
from collections import deque
import heapq,json,threading,time
from pilot.betaintegrated01.clock.correlation import BoundedCorrelator
from .diagnostics import DiagnosticIO

class ClockIO(DiagnosticIO):
    """Keep eight worst original syscall spans as well as the original tail."""
    def __init__(self,hook=None):super().__init__(hook);self.worst=[]
    def _timed(self,*args):
        try:return super()._timed(*args)
        finally:
            row=self.last[-1];entry=(row['wallNs'],row['ordinal'],dict(row))
            if len(self.worst)<8:heapq.heappush(self.worst,entry)
            elif entry[:2]>self.worst[0][:2]:heapq.heapreplace(self.worst,entry)
    def snapshot(self):return {**super().snapshot(),'maximumWorstOperations':8,'worstOriginalOperations':[r[2]for r in sorted(self.worst,reverse=True)]}

class TentativeCorrelator(BoundedCorrelator):
    """All returned state is tentative; no caller may use it for dispatch."""
    def calibration(self,*args):
        value=super().calibration(*args)
        return None if value is None else {**value,'tentativeNotDurable':True}
    def snapshot(self):
        return {**super().snapshot(),'pipelineContract':'CLOCKPIPE09_TENTATIVE_ONLY','durableAuthority':False}

class SerializedGuard:
    """Forward EVERY original guard check; lock excludes write/fsync IO."""
    def __init__(self,guard):self.original=guard;self.lock=threading.RLock()
    def __getattr__(self,name):return getattr(self.original,name)
    def check(self,*args,**kwargs):
        with self.lock:return self.original.check(*args,**kwargs)

class OrderedClockQueue:
    def __init__(self):
        self.condition=threading.Condition();self.rows=deque();self.inflight=None;self.closed=False;self.failure=None;self.staged=0;self.committed=0;self.high_water=0;self.unknown=None;self.authority_lock=threading.RLock();self.authority_failure=None;self.requested_failure=None;self.failure_observed_ns=None;self.failure_effective_ns=None
    def bind_authority(self,lock,latch):
        if self.staged or self.failure is not None:raise RuntimeError('CLOCKPIPE09_BIND_BEFORE_INGRESS')
        self.authority_lock=lock;self.authority_failure=latch
    def stage(self,kind,data):
        raw=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        if kind not in ('CLOCK','PUBLICATION')or len(raw)>2048:raise ValueError('CLOCKPIPE09_EVENT_TYPE_OR2048')
        # Own immutable bytes. Producer/correlator trees cannot change this row.
        overflow=False
        with self.condition:
            if self.closed or self.failure or self.requested_failure:raise RuntimeError('CLOCKPIPE09_INGRESS_CLOSED')
            if len(self.rows)+(self.inflight is not None)>=64:
                self.unknown={'kind':kind,'original':json.loads(raw),'reason':'CLOCKPIPE09_QUEUE64_OVERFLOW'}
                overflow=True
            else:
                self.staged+=1;row=(self.staged,kind,raw);self.rows.append(row);self.high_water=max(self.high_water,len(self.rows)+(self.inflight is not None));self.condition.notify_all();return row[0]
        if overflow:
            error=RuntimeError('CLOCKPIPE09_QUEUE64_OVERFLOW');self.fail(error);raise error
    def take(self):
        with self.condition:
            if self.failure:raise RuntimeError(self.failure)
            if self.inflight is not None:raise RuntimeError('CLOCKPIPE09_SINGLE_DURABLE_WRITER')
            if not self.rows:return None
            self.inflight=self.rows.popleft();return self.inflight
    def finish(self,row):
        with self.condition:
            if self.inflight is not row or row[0]!=self.committed+1:raise RuntimeError('CLOCKPIPE09_COMMIT_ORDER')
            self.committed=row[0];self.inflight=None;self.condition.notify_all()
    def pending(self):
        with self.condition:return self.inflight is not None or bool(self.rows)
    def close_ingress(self):
        with self.condition:self.closed=True;self.condition.notify_all()
    def fail(self,error):
        # Never wait for authority while holding the queue condition. Fault
        # observation is diagnostic; effective failure shares the exact owner
        # authority lock with dispatch/publication. A requested fault also
        # refuses subsequent permits even before the producer gets that lock.
        with self.condition:
            if self.requested_failure is None:self.requested_failure=type(error).__name__+':'+str(error)[:512];self.failure_observed_ns=time.monotonic_ns()
            self.closed=True;self.condition.notify_all()
        with self.authority_lock:
            with self.condition:
                if self.failure is None:self.failure=self.requested_failure;self.failure_effective_ns=time.monotonic_ns()
                self.condition.notify_all()
            if self.authority_failure is not None:self.authority_failure(error)
    def snapshot(self):
        with self.condition:
            return {'contract':'CLOCKPIPE09_READONLY_QUERY_MAY_PRECEDE_REGISTER_FSYNC_NEVER_AUTHORITY','maximumEvents':64,'maximumSerializedEventBytes':2048,'highWaterEvents':self.high_water,'staged':self.staged,'committed':self.committed,'queued':len(self.rows),'inflightSequence':None if self.inflight is None else self.inflight[0],'inflightOrQueuedUnknown':self.inflight is not None or bool(self.rows),'failure':self.failure,'faultObservedHostNs':self.failure_observed_ns,'faultEffectiveHostNs':self.failure_effective_ns,'faultLinearization':'OWNER_AUTHORITY_LOCK_NOT_DIAGNOSTIC_OBSERVATION','ingressClosed':self.closed,'overflowOriginal':self.unknown}
