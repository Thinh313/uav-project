"""Bounded auxiliary diagnostics. These timings never constitute safety observations."""
from collections import deque
from contextlib import contextmanager,nullcontext
import json,os,threading,time
CODES=('reserve','release','lock_thread','lock_file','lock_hold','ledger_save','ledger_fsync','ledger_publish','popen','first_stdout','first_stderr','eof_stdout','eof_stderr','wait','cleanup','payload_write','payload_fsync','prefix_persist','query','disk_check','inventory','health_read','queue_drain','barrier','rpc_receive','rpc_parse','data_lock','rpc_validate','reply_encode','reply_send','ledger_serial','ledger_write','ledger_file_fsync','ledger_dir_fsync','payload_data_write','payload_dir_fsync','quota_charge','payload_file_fsync')
MAX_ROWS=48;MAX_EVENTS=200000;MAX_NS=5400_000_000_000;MAX_SNAPSHOT=8192
class StageTrace:
 def __init__(self,*,now=time.monotonic_ns,cpu=time.thread_time_ns):
  self.pid=os.getpid();self.now=now;self.cpu=cpu;self.lock=threading.RLock();self.rows=deque(maxlen=MAX_ROWS);self.total=0;self.stats={};self.active={};self.threads=set();self.first_failure=None;self.failure=None
 @contextmanager
 def span(self,code):
  if code not in CODES:raise ValueError('FIXED_AUXILIARY_STAGE_CODE')
  try:thread=threading.get_native_id();start=self.now();cpu=self.cpu()
  except BaseException as timing:
   self.failure=timing;yield;return
  error=None
  with self.lock:
   if os.getpid()!=self.pid:self.failure=RuntimeError('STAGE_TRACE_PROCESS_EPOCH_MISMATCH')
   disabled=self.failure is not None
   if not disabled:
    self.threads.add(thread);stack=self.active.setdefault(thread,[])
    if len(self.threads)>4 or len(stack)>=8:self.failure=RuntimeError('STAGE_TRACE_THREAD_DEPTH_BOUND');disabled=True
    else:token=[CODES.index(code),start,cpu];stack.append(token)
  if disabled:
   yield;return
  try:yield
  except BaseException as primary:error=primary;raise
  finally:
   try:
    end=self.now();cost=self.cpu()-cpu;wall=end-start
    if any(type(n)is not int or n<0 for n in(start,end,cost,wall))or end>=2**63 or wall>MAX_NS or cost>MAX_NS:raise RuntimeError('STAGE_TRACE_TYPED_CLOCK_BOUND')
    with self.lock:
     stack=self.active[thread]
     if not stack or stack[-1]is not token:raise RuntimeError('STAGE_TRACE_NESTING')
     stack.pop()
     if self.total>=MAX_EVENTS:raise RuntimeError('STAGE_TRACE_EVENT_BOUND')
     self.total+=1
     row=[self.total,token[0],thread,start,wall,cost,error is not None];self.rows.append(row)
     stats=self.stats.setdefault(token[0],[0,0,0,0,0]);stats[0]+=1;stats[1]+=wall;stats[2]=max(stats[2],wall);stats[3]+=cost;stats[4]=max(stats[4],cost)
     if error is not None and self.first_failure is None:self.first_failure={'row':list(row),'type':type(error).__name__[:64],'reason':str(error)[:128]}
   except BaseException as secondary:
    self.failure=secondary
    if error is not None:error.add_note('STAGE_TRACE_SECONDARY:'+type(secondary).__name__+':'+str(secondary)[:256])
 def point(self,code):
  with self.span(code):pass
 def check(self):
  if self.failure is not None:raise self.failure
 def snapshot(self):
  with self.lock:
   result={'format':'aeris-auxiliary-stage-trace','version':1,'createdPID':self.pid,'actualPID':os.getpid(),'scope':'DIAGNOSTIC_TIMINGS_NOT_GUARD_OBSERVATIONS_OR_CAUSAL_PROOF','codes':list(CODES),'rowFields':['sequence','code','actualThreadID','enteredMonotonicNs','durationNs','threadCPUDeltaNs','failed'],'rows':[list(r)for r in self.rows],'totalCompleted':self.total,'overwrittenDiagnosticRows':max(0,self.total-len(self.rows)),'aggregates':{str(k):list(v)for k,v in self.stats.items()},'aggregateFields':['count','sumWallNs','maxWallNs','sumThreadCPUNs','maxThreadCPUNs'],'active':[[tid,*stack[-1]]for tid,stack in self.active.items()if stack],'firstFailure':self.first_failure,'traceFailure':None if self.failure is None else type(self.failure).__name__+':'+str(self.failure)[:128],'originalObservationRowsDropped':False,'nestedStageDurationsOverlap':True}
  if len(json.dumps(result,separators=(',',':')).encode())>MAX_SNAPSHOT:
   self.failure=RuntimeError('STAGE_TRACE_SNAPSHOT8KiB')
   return {'format':'aeris-auxiliary-stage-trace','version':1,'actualPID':os.getpid(),'traceFailure':str(self.failure),'totalCompleted':self.total,'snapshotDataOmittedBecauseBound':True,'scope':'FAILED_DIAGNOSTIC_NEVER_SAFETY_AUTHORITY'}
  return result

def span(trace,code):return nullcontext()if trace is None else trace.span(code)
