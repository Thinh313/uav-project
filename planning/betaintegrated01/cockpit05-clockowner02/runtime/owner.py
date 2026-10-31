"""Independent single-writer durable clock owner; immutable post-fsync publication."""
from pathlib import Path
from dataclasses import dataclass,asdict
from importlib import import_module
import hashlib,json,threading,time,re
from collections import deque
from pilot.betaintegrated01.cockpit04.clock_socket import ClockSocket
from pilot.betaintegrated01.runtime.ap_stage import canonical,exclusive
from ..policy import clock_policy,clock_events
J=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal')
D=import_module('planning.betaintegrated01.cockpit05-clockdiag01.diagnostics')


@dataclass(frozen=True)
class Publication:
    run:str
    epoch:str
    boot:str
    id:int
    hostReceiveNs:int
    offsetLowNs:int
    offsetHighNs:int
    uncertaintyNs:int
    clockResponseSequence:int
    clockResponseSHA256:str
    clockPublicationSequence:int
    clockPublicationSHA256:str
    publicationCompleteHostNs:int


class ClockOwner:
    def __init__(self,out,run,epoch,boot,maximum_seconds,source_amendment,*,origin_ns=None,journal_factory=None,socket_factory=None):
        self.origin_ns=time.monotonic_ns()if origin_ns is None else origin_ns
        if type(self.origin_ns)is not int or self.origin_ns<0:raise ValueError('OWNER_ORIGIN_CLOCK')
        self.out=Path(out);self.run,self.epoch,self.boot=run,epoch,boot;self.maximum_seconds=maximum_seconds;self.source_amendment=source_amendment
        self.maximum_events=clock_events(maximum_seconds);self.events=0;self.diagnostic_written=False;self.publication=None;self.history=deque(maxlen=8);self.last_response=None;self.last_publication_id=None
        self.lock=threading.Lock();self.ready=threading.Event();self.done=threading.Event();self.stop_event=threading.Event();self.failed=None;self.result=None;self.thread=None;self.journal=None;self.clock=None
        self.diagnostic_io=D.DiagnosticIO();self.journal_factory=journal_factory or (lambda *a:J.SegmentedJournal(*a,io=self.diagnostic_io));self.socket_factory=socket_factory or ClockSocket
    def start(self):
        if self.thread is not None:raise RuntimeError('CLOCK_OWNER_SINGLE_START')
        self.thread=threading.Thread(target=self._run,name='clockowner02-durable',daemon=False);self.thread.start()
    def _append(self,kind,data):
        if self.events>=self.maximum_events:raise RuntimeError('CLOCK_OWNER_TOTAL_EVENTS_CAPACITY')
        seq=self.journal.append_event(kind,data);self.events+=1
        return {'sequence':seq,'sha256':self.journal.head,'durableHostNs':time.monotonic_ns()}
    def sink(self,row):
        if any(row.get(k)!=v for k,v in [('run',self.run),('epoch',self.epoch),('boot',self.boot)]):raise ValueError('CLOCK_OWNER_FOREIGN_EVENT')
        try:ref=self._append('CLOCK',row)
        except Exception as error:
            self.diagnostic({'reason':'CLOCK_DURABLE_EVENT_FAILED','attemptedEvent':row,'errorChain':D.exception_chain(error)})
            raise
        if row.get('kind')=='RESPONSE'and row.get('freshCalibration')is True:
            self.last_response=(dict(row),dict(ref))
    def diagnostic(self,data):
        if self.diagnostic_written:return
        self.diagnostic_written=True
        value={'run':self.run,'epoch':self.epoch,'boot':self.boot,'retainedEvents':self.events,'complete':False,'data':data}
        raw=canonical(value)+b'\n'
        if len(raw)>32768:return
        try:
            self.journal.guard.check(len(raw));exclusive(self.out/'clock-owner-diagnostic.json',raw)
        except Exception:pass
    def publish(self,bracket):
        """Owner-thread only. Append publication before making snapshot visible."""
        if bracket is None or bracket['id']==self.last_publication_id:return
        if self.last_response is None or self.last_response[0]['id']!=bracket['id']:raise ValueError('CLOCK_PUBLICATION_REQUIRES_DURABLE_MATCHED_RESPONSE')
        row,ref=self.last_response
        data={'run':self.run,'epoch':self.epoch,'boot':self.boot,'id':row['id'],
          'responseSequence':ref['sequence'],'responseSHA256':ref['sha256'],
          'responseDurableHostNs':ref['durableHostNs'],'publicationBeginHostNs':time.monotonic_ns(),
          'hostReceiveNs':row['hostReceiveNs'],'offsetLowNs':row['offsetLowNs'],'offsetHighNs':row['offsetHighNs']}
        publication_ref=self._append('CLOCK_PUBLICATION',data)
        value=Publication(self.run,self.epoch,self.boot,row['id'],row['hostReceiveNs'],row['offsetLowNs'],row['offsetHighNs'],row['uncertaintyNs'],ref['sequence'],ref['sha256'],publication_ref['sequence'],publication_ref['sha256'],publication_ref['durableHostNs'])
        with self.lock:
            if self.failed is not None:raise RuntimeError('CLOCK_OWNER_FAILURE_LATCHED')
            if self.publication is not None and(value.id<=self.publication.id or value.hostReceiveNs<self.publication.hostReceiveNs):raise ValueError('CLOCK_PUBLICATION_REGRESSION')
            self.publication=value;self.history.append(value);self.last_publication_id=value.id
    def _validated(self,value,now):
        if self.failed is not None:raise RuntimeError('CLOCK_OWNER_FAILED:'+self.failed)
        if self.thread is None or not self.thread.is_alive()or self.done.is_set():raise RuntimeError('CLOCK_OWNER_NOT_ALIVE')
        if type(value)is Publication:
            for field in ('id','hostReceiveNs','offsetLowNs','offsetHighNs','uncertaintyNs','clockResponseSequence','clockPublicationSequence','publicationCompleteHostNs'):
                if type(getattr(value,field))is not int:raise ValueError('CLOCK_PUBLICATION_NUMERIC_TYPE')
            for field in ('clockResponseSHA256','clockPublicationSHA256'):
                if type(getattr(value,field))is not str or re.fullmatch('[0-9a-f]{64}',getattr(value,field))is None:raise ValueError('CLOCK_PUBLICATION_HASH_TYPE')
        if type(value)is not Publication or (value.run,value.epoch,value.boot)!=(self.run,self.epoch,self.boot):raise ValueError('CLOCK_OWNER_PUBLICATION_CONTEXT')
        if not 0<=now-value.hostReceiveNs<=250_000_000 or not value.publicationCompleteHostNs<=now:raise ValueError('CLOCK_OWNER_PUBLICATION_NOT_FRESH_250MS')
        if value not in self.history:raise ValueError('CLOCK_UNPUBLISHED_OR_FORGED_REFERENCE')
        return value
    def calibration(self):
        # This lock never spans disk IO or correlator calls.
        with self.lock:
            if self.publication is None:
                if self.failed is not None:raise RuntimeError('CLOCK_OWNER_FAILED:'+self.failed)
                return None
            try:value=self._validated(self.publication,time.monotonic_ns())
            except Exception as error:
                if self.failed is None:self.failed=type(error).__name__+':'+str(error)[:512]
                raise
            return asdict(value)
    def dispatch(self,reference,callback):
        # Linearization: no network callback may begin after a known fault latch.
        with self.lock:
            try:
                value=Publication(**reference);checked=time.monotonic_ns();self._validated(value,checked)
            except Exception as error:
                if self.failed is None:self.failed=type(error).__name__+':'+str(error)[:512]
                raise
            return callback(checked)
    def latch_failure(self,error):
        with self.lock:
            if self.failed is None:self.failed=type(error).__name__+':'+str(error)[:512]
    def _run(self):
        try:
            self.journal=self.journal_factory(self.out/'clock-journal',self.run,self.epoch,clock_policy(self.maximum_seconds))
            self._append('CLOCK_OWNER_BINDING',{'run':self.run,'epoch':self.epoch,'boot':self.boot,'sourceAmendmentSHA256':self.source_amendment,'originHostNs':self.origin_ns,'maximumEvents':self.maximum_events,'maximumRecordBytes':2048})
            self.clock=self.socket_factory(self.run,self.epoch,self.boot,self.sink,maximum_seconds=self.maximum_seconds,diagnostic=self.diagnostic)
            self.ready.set();started=time.monotonic()
            while not self.stop_event.wait(.01):
                self.journal.guard.check()
                if time.monotonic()-started>self.maximum_seconds+30:raise RuntimeError('CLOCK_OWNER_LIFETIME')
                self.clock.poll();self.publish(self.clock.calibration())
            self.clock.close();self.clock=None;result=self.journal.close()
            self.result={'status':'CLOCK_OWNER_CLOSED_NOT_FLIGHT_ACCEPTANCE','run':self.run,'epoch':self.epoch,'boot':self.boot,'events':self.events,'commitAnchor':result['commitAnchor']}
        except BaseException as error:
            self.latch_failure(error)
            if self.journal is not None:
                try:self.journal.abort(self.failed)
                except Exception:pass
            self.result={'status':'CLOCK_OWNER_FAILED_RETAINED_PREFIX','run':self.run,'epoch':self.epoch,'boot':self.boot,'events':self.events,'error':self.failed,'errorChain':D.exception_chain(error),'io':self.diagnostic_io.snapshot(),'commitAnchor':None}
        finally:
            if self.clock is not None:
                try:self.clock.close()
                except Exception:pass
            self.done.set()
            try:exclusive(self.out/'clock-owner-result.json',canonical(self.result)+b'\n')
            except Exception:pass
    def close(self,timeout=5):
        self.stop_event.set()
        if self.thread is not None:self.thread.join(timeout=timeout)
        if not self.done.is_set():self.latch_failure(RuntimeError('CLOCK_OWNER_CLOSE_TIMEOUT'));raise RuntimeError('CLOCK_OWNER_CLOSE_TIMEOUT')
        if self.failed is not None:raise RuntimeError('CLOCK_OWNER_FAILED:'+self.failed)
        return self.result
