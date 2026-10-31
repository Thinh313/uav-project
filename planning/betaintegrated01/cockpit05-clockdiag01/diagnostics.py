"""Bounded diagnostic-only FileIO timing and honest local send classification."""
from collections import deque
from importlib import import_module
import time
FileIO=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal').FileIO


def exception_chain(error):
    rows=[];seen=set()
    while error is not None and id(error)not in seen and len(rows)<4:
        seen.add(id(error));rows.append({'type':type(error).__name__,'message':str(error)[:512]})
        error=error.__cause__ if error.__cause__ is not None else error.__context__ if not error.__suppress_context__ else None
    return rows


class DiagnosticIO(FileIO):
    """Original syscalls/fsync behavior; timing overhead disclosed, no batching."""
    def __init__(self,hook=None):
        super().__init__(hook);self.last=deque(maxlen=8);self.operations=0
    def _timed(self,kind,fd,n,operation):
        begin=time.monotonic_ns();cpu=time.thread_time_ns();error=None
        try:return operation()
        except BaseException as exc:error=exception_chain(exc);raise
        finally:
            cpu_end=time.thread_time_ns();end=time.monotonic_ns();self.operations+=1
            self.last.append({'ordinal':self.operations,'operation':kind,'fd':fd,'requestedBytes':n,
              'beginHostNs':begin,'endHostNs':end,'wallNs':end-begin,'threadCPUNs':cpu_end-cpu,
              'nonCPUWallNs':max(0,(end-begin)-(cpu_end-cpu)),
              'nonCPUWallMeaning':'SYSCALL_WAIT_AND_OR_DESCHEDULE_NOT_FILESYSTEM_ONLY','errorChain':error})
    def write(self,fd,data):return self._timed('write',fd,len(data),lambda:super(DiagnosticIO,self).write(fd,data))
    def fsync(self,fd):return self._timed('fsync',fd,0,lambda:super(DiagnosticIO,self).fsync(fd))
    def snapshot(self):return {'maximumRetainedOperations':8,'totalObservedOperations':self.operations,'lastOperations':list(self.last),'timingInstrumentationOverhead':'NOT_YET_BENCHMARKED','threadCPUDoesNotIdentifyOSWaitReason':True}


def send_classification(current):
    if current.get('localCallbackInvoked')is False:
        return {'type':'NOT_SENT_SOCKET_CALLBACK_NOT_ENTERED','networkCallbackEntered':False,
          'socketCallOutcome':'NOT_INVOKED_IN_THIS_FRAME','journalUNKNOWNMustRemainUnchanged':True,
          'proofBasis':'VERSIONED_ADAPTER_FLAG_SET_IMMEDIATELY_BEFORE_SEND_CALLBACK'}
    if current.get('localReturnKnown')is True:
        return {'type':'LOCAL_RETURN_KNOWN_NOT_AP_EXECUTION','networkCallbackEntered':True,'socketCallOutcome':'LOCAL_EXPECTED_LENGTH_RETURN_ONLY','journalUNKNOWNMustRemainUnchanged':True}
    return {'type':'SOCKET_CALLBACK_OUTCOME_UNKNOWN','networkCallbackEntered':True,'socketCallOutcome':'UNKNOWN','journalUNKNOWNMustRemainUnchanged':True}
