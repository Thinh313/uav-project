"""Darwin per-thread CPU/state samples; never label samples as exact wait durations."""
import ctypes as C,json,os,sys,time,signal,threading,struct,subprocess
from pathlib import Path
from array import array
PERIOD=5_000_000;CAPACITY=32010
COLS=['scheduledNs','queryStartNs','queryEndNs','missedDeadlines','returnBytes','errno','targetUserCpuNs','targetSystemCpuNs','runState','flags','sleepSeconds','currentPriority','basePriority','maxPriority','observerThreadCpuNs']
class Info(C.Structure):
 _fields_=[('user',C.c_uint64),('system',C.c_uint64)]+[(n,C.c_int32)for n in ['cpu','policy','state','flags','sleep','cur','pri','max']]+[('name',C.c_char*64)]
class Reader:
 def __init__(self,pid,tid):
  if sys.platform!='darwin':raise RuntimeError('DARWIN_REQUIRED')
  assert C.sizeof(Info)==112
  self.pid,self.tid=pid,tid;self.lib=C.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
  self.lib.proc_pidinfo.argtypes=[C.c_int,C.c_int,C.c_uint64,C.c_void_p,C.c_int];self.lib.proc_pidinfo.restype=C.c_int
 def query(self):
  q=Info();C.set_errno(0);a=time.monotonic_ns();n=self.lib.proc_pidinfo(self.pid,15,self.tid,C.byref(q),112);b=time.monotonic_ns();err=C.get_errno()
  return [a,b,n,err,q.user,q.system,q.state,q.flags,q.sleep,q.cur,q.pri,q.max]
def save(p,v):
 with p.open('x')as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
def collect(out,capacity=CAPACITY,period=PERIOD):
 identity=json.loads((out/'thread-target.json').read_text());assert identity['pid']==os.getppid(),'OBSERVER_MUST_BE_TARGET_CHILD'
 reader=Reader(identity['pid'],identity['nativeThreadId']);initial=reader.query();assert initial[2]==112 and initial[3]==0,'TARGET_THREAD_NOT_READABLE'
 # Cross-process CPU-unit sanity check versus the parent's captured thread_time_ns.
 assert initial[4]+initial[5]>=identity['threadCpuNs']-5_000_000,'CPU_UNITS_OR_IDENTITY'
 stopped=False
 def stop(*_):
  nonlocal stopped;stopped=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 save(out/'thread-observer-ready.json',{'pid':os.getpid(),'parentPid':os.getppid(),'target':identity,'initial':initial,'abiBytes':112,'flavor':15,'periodNs':period,'capacity':capacity})
 rows=array('q',[0])*(capacity*len(COLS));count=0;error=None;due=time.monotonic_ns()+period;start=time.monotonic_ns();cpu=time.process_time_ns()
 try:
  previous=None
  while not stopped:
   if time.monotonic_ns()-start>160_000_000_000:raise RuntimeError('SAMPLER_DEADLINE')
   if count>=capacity:raise RuntimeError('THREAD_TRACE_CAPACITY_BEFORE_QUERY')
   delay=due-time.monotonic_ns()
   if delay>0:time.sleep(delay/1e9)
   if stopped:break
   q=reader.query();missed=max(0,(q[0]-due)//period)
   row=[due,q[0],q[1],missed,q[2],q[3],*q[4:],time.thread_time_ns()]
   rows[count*len(COLS):(count+1)*len(COLS)]=array('q',row);count+=1;due+=(missed+1)*period
   if q[2]!=112 or q[3]:raise RuntimeError('THREAD_QUERY_FAILED:'+str(q[:4]))
   if q[6]not in range(1,6):raise RuntimeError('UNKNOWN_THREAD_STATE')
   if previous and (q[4]<previous[4]or q[5]<previous[5]):raise RuntimeError('THREAD_CPU_REGRESSION')
   previous=q
 except BaseException as exc:error=str(exc)
 # Seal even failed samples; never fabricate a successful tail.
 with(out/'thread-samples.bin').open('xb')as f:
  f.write(struct.pack('<8sQQ',b'AERIST62',count,len(COLS)));f.write(memoryview(rows).cast('B')[:count*len(COLS)*8]);f.flush();os.fsync(f.fileno())
 save(out/'thread-samples.json',{'status':'PASS_BOUNDED_THREAD_SAMPLES'if error is None else'FAILED','error':error,'rows':count,'capacity':capacity,'periodNs':period,'columns':COLS,'target':identity,'observerPid':os.getpid(),'stoppedBySignal':stopped,'observerCpuNs':time.process_time_ns()-cpu,'states':{'1':'RUNNING_OR_RUNNABLE','2':'STOPPED','3':'WAITING','4':'UNINTERRUPTIBLE','5':'HALTED'},'scope':'External child samples target main thread independently of target GIL. Query time bracket, sampled state and cumulative CPU only; no exclusive kernel runnable or filesystem wait duration. CPU counters ns with kernel microsecond quantization. Missed deadlines retained, no interpolation.'})
 if error:raise SystemExit(1)
def start(out,capacity=CAPACITY):
 save(out/'thread-target.json',{'pid':os.getpid(),'nativeThreadId':threading.get_native_id(),'threadCpuNs':time.thread_time_ns(),'hostMonotonicNs':time.monotonic_ns(),'role':'BACKEND_MAIN_THREAD'})
 log=(out/'thread-observer-console.txt').open('x');p=subprocess.Popen([sys.executable,'-B',str(Path(__file__)),str(out),str(capacity)],stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+4
  while not(out/'thread-observer-ready.json').exists():
   if p.poll()is not None:raise RuntimeError('THREAD_OBSERVER_START_FAILED')
   if time.monotonic()>deadline:raise RuntimeError('THREAD_OBSERVER_START_TIMEOUT')
   time.sleep(.01)
  return p,log
 except BaseException:
  if p.poll()is None:p.terminate();p.wait(timeout=4)
  log.close();raise
def seal(handle,out):
 p,log=handle
 try:
  if p.poll()is None:p.terminate()
  p.wait(timeout=4)
 finally:log.close()
 if p.returncode!=0 or not(out/'thread-samples.json').exists():raise RuntimeError('THREAD_OBSERVER_NOT_CLEANLY_SEALED')
 result=json.loads((out/'thread-samples.json').read_text());assert result['status']=='PASS_BOUNDED_THREAD_SAMPLES'and result['target']['pid']==os.getpid()
if __name__=='__main__':collect(Path(sys.argv[1]),int(sys.argv[2])if len(sys.argv)>2 else CAPACITY)
