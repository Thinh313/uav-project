"""Bounded IO-free delivery diagnostics, never a calibration/authority source."""
from collections import deque
import threading,time
PHASES=frozenset(('POLL','CORRELATOR_RECEIVE','MATCHED_CALLBACK','REQUEST_TICK','REQUEST_REGISTER','REQUEST_SEND','DURABLE_APPEND','PUBLICATION'))
class DeliveryProbe:
 def __init__(self):self.lock=threading.Lock();self.ring=deque(maxlen=64);self.summary={};self.errors=0;self.count=0;self.polls=0;self.receives=0;self.callbacks=0;self.cadenceSkips=0
 def measure(self,phase,callback,**detail):
  try:begin=time.monotonic_ns();cpu=time.thread_time_ns();failure=None
  except Exception:self.errors+=1;return callback()
  try:return callback()
  except BaseException as e:failure=type(e).__name__;raise
  finally:
   try:self.record(phase,begin,time.monotonic_ns(),time.thread_time_ns()-cpu,failure,detail)
   except Exception:self.errors+=1
 def record(self,phase,begin,end,cpu,failure,detail):
  if phase not in PHASES or end<begin or cpu<0:raise ValueError('DELIVERY_DIAGNOSTIC_DOMAIN')
  with self.lock:
   self.count+=1;wall=end-begin;item=dict(phase=phase,beginHostNs=begin,endHostNs=end,wallNs=wall,threadCPUNs=cpu,nonCPUWallNs=max(0,wall-cpu),failureClass=failure,detail=detail)
   self.ring.append(item);s=self.summary.setdefault(phase,dict(count=0,wallTotalNs=0,wallMaxNs=0,threadCPUTotalNs=0));s['count']+=1;s['wallTotalNs']+=wall;s['wallMaxNs']=max(s['wallMaxNs'],wall);s['threadCPUTotalNs']+=cpu
 def snapshot(self):
  with self.lock:return dict(format='aeris-clockterm14-delivery-diagnostic',version=1,diagnosticOnly=True,ringCapacity=64,observedOperations=self.count,measurementErrors=self.errors,phases={k:dict(v)for k,v in self.summary.items()},lastOperations=list(self.ring),polls=self.polls,receivedDatagrams=self.receives,matchedCallbacks=self.callbacks,requestCadenceSkips=self.cadenceSkips,wallClock='HOST_MONOTONIC_NS',cpuClock='CURRENT_THREAD_TIME_NS',nonCPUWallMeaning='SYSCALL_WAIT_AND_OR_DESCHEDULE_NOT_FILESYSTEM_OR_NETWORK_ALONE',receiveClockMeaning='ORIGINAL_USERSPACE_RECVMSG_RETURN_NOT_KERNEL_ARRIVAL',boundedReceiveBudgetPerPoll=8,requestPeriodNs=100000000,timingOverhead='NOT_MATCHED_AB_BENCHMARKED',authorityOrClockCalibrationFromDiagnostic=False)
