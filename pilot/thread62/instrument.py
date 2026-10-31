"""Explicit syscall observations. Non-CPU time is not exclusive scheduler wait."""
from array import array
import os,time,json,threading,struct,errno,hashlib,zlib,resource
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'pilot/sim32-journal04'))
from wal_journal import MAGIC,HEADER,KINDS,encode
KIND={**KINDS,'MAGIC':8,'SNAPSHOT':9,'EMERGENCY':10,'EXTENT':11}
OPS={'write':1,'fsync':2,'replace':3,'open':4,'close':5,'preallocate':6}
class IOTrace:
 def __init__(self,capacity):
  self.capacity=capacity;self.data=array('q',[0])*(capacity*12);self.count=0;self.overflow=False
 def call(self,op,kind,frame,offset,requested,fn):
  if self.count>=self.capacity:self.overflow=True;raise RuntimeError('IO_TRACE_CAPACITY_BEFORE_SYSCALL')
  index=self.count;self.count+=1;failure=None;result=-1;err=0
  start=time.monotonic_ns();cpu_start=time.thread_time_ns()
  try:
   value=fn();result=value if isinstance(value,int)else 0
  except BaseException as exc:failure=exc;err=getattr(exc,'errno',None)or -1
  cpu_end=time.thread_time_ns();end=time.monotonic_ns()
  row=[index,OPS[op],KIND[kind],frame,offset,requested,start,end,cpu_start,cpu_end,result,err]
  self.data[index*12:(index+1)*12]=array('q',row)
  if failure:raise failure
  return value
 def snapshot(self,pending,target,raw,frame):
  fd=self.call('open','SNAPSHOT',frame,0,0,lambda:os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o666))
  try:
   pos=0
   while pos<len(raw):
    n=self.call('write','SNAPSHOT',frame,pos,len(raw)-pos,lambda:os.write(fd,memoryview(raw)[pos:]))
    if n<=0 or n>len(raw)-pos:raise RuntimeError('INVALID_SNAPSHOT_WRITE')
    pos+=n
  finally:self.call('close','SNAPSHOT',frame,0,0,lambda:os.close(fd))
  self.call('replace','SNAPSHOT',frame,0,0,lambda:os.replace(pending,target))
 def seal(self,path,meta):
  with path.open('xb')as f:
   f.write(struct.pack('<8sQQ',b'AERISIO9',self.count,12));f.write(memoryview(self.data).cast('B')[:self.count*96]);f.flush();os.fsync(f.fileno())
  with meta.open('x')as f:json.dump({'rows':self.count,'capacity':self.capacity,'overflow':self.overflow,'byteOrder':sys.byteorder,'columns':['sequence','operation','kind','frame','offset','requestedBytes','wallStartNs','wallEndNs','threadCpuStartNs','threadCpuEndNs','returnedValue','errno'],'operations':OPS,'kinds':KIND,'scope':'Measured Python syscall wrapper intervals include clock cost and possible preemption; nonCPU is I/O/GIL/preemption proxy, not kernel runnable wait. Trace-seal IO excluded from runtime measurements.'},f,indent=2)
class WakeProbe:
 def __init__(self,period_ns=10000000,capacity=16010):
  self.period=period_ns;self.capacity=capacity;self.data=array('q',[0])*(capacity*6);self.count=0;self.resources=array('q');self.error=None;self.stop=threading.Event();self.thread=None
 def start(self):
  self.thread=threading.Thread(target=self.work,name='thread62-wake',daemon=True);self.thread.start()
 def work(self):
  due=time.monotonic_ns()+self.period
  try:
   while not self.stop.is_set():
    if self.stop.wait(max(0,(due-time.monotonic_ns())/1e9)):break
    actual=time.monotonic_ns();cpu=time.thread_time_ns();missed=max(0,(actual-due)//self.period)
    if self.count>=self.capacity:raise RuntimeError('WAKE_TRACE_CAPACITY')
    row=[due,actual,cpu,missed,time.process_time_ns(),threading.get_native_id()]
    self.data[self.count*6:(self.count+1)*6]=array('q',row)
    if self.count%2==0:
     ru=resource.getrusage(resource.RUSAGE_SELF);self.resources.extend([actual,int(ru.ru_utime*1e9),int(ru.ru_stime*1e9),ru.ru_minflt,ru.ru_majflt,ru.ru_nvcsw,ru.ru_nivcsw,ru.ru_inblock,ru.ru_oublock])
    self.count+=1;due+=(missed+1)*self.period
  except BaseException as e:self.error=str(e)
 def seal(self,path):
  self.stop.set()
  if self.thread:self.thread.join(2)
  if self.thread and self.thread.is_alive():raise RuntimeError('WAKE_THREAD_NOT_CLOSED')
  with path.open('xb')as f:
   f.write(struct.pack('<8sQQ',b'AERISWK9',self.count,6));f.write(memoryview(self.data).cast('B')[:self.count*48]);f.flush();os.fsync(f.fileno())
  with path.with_suffix('.json').open('x')as f:json.dump({'error':self.error,'count':self.count,'periodNs':self.period,'columns':['scheduledHostMonotonicNs','actualWakeHostMonotonicNs','threadCpuNs','missedDeadlines','processCpuNs','nativeThreadId'],'scope':'Absolute-deadline wake latency; missed deadlines retained as exact count/range. Does not measure exclusive kernel scheduler runnable wait.'},f,indent=2)
  with path.with_name(path.stem+'-rusage.bin').open('xb')as f:f.write(struct.pack('<8sQQ',b'AERISRU1',len(self.resources)//9,9));f.write(self.resources.tobytes())
  if self.error:raise RuntimeError(self.error)

class TimedWal:
 def __init__(self,out,metadata,policy='fsync-before-publish',limit=16*1024**2,hook=lambda *a:None,trace=None,preallocate=False,allocation_fn=None,record_clock=None):
  from extent import reserve
  self.trace=trace or IOTrace(650010)
  if policy not in ['fsync-before-publish','process-crash-only']:raise ValueError('Explicit durability policy')
  self.out,self.policy,self.limit,self.hook=out,policy,limit,hook
  self.record_clock=record_clock or time.monotonic_ns
  self.seq=0;self.chain=bytes(32);self.bytes=0;self.failed=None;self.closed=False;self.flushes=0;self.append_cost=array('Q');self.flush_cost=array('Q')
  self.fd=self.trace.call('open','MAGIC',0,0,0,lambda:os.open(out/'frames.wal',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600))
  try:
   self.allocation=reserve(self.fd,limit,out,self.trace,allocation_fn) if preallocate else {'status':'DISABLED','requestedBytes':0,'fallback':False,'logicalSizeBefore':os.fstat(self.fd).st_size}
   with(out/'allocation.json').open('x')as f:json.dump(self.allocation,f,indent=2)
   pos=0
   while pos<len(MAGIC):
    n=self.trace.call('write','MAGIC',0,pos,len(MAGIC)-pos,lambda:os.write(self.fd,MAGIC[pos:]))
    if n<=0 or n>len(MAGIC)-pos:raise RuntimeError('Invalid WAL magic write')
    pos+=n
   self.bytes=8
   self.append('HEADER',0,encode({**metadata,'format':'aeris-journal04','version':1,'durabilityPolicy':policy,'hostPowerLoss':'NOT_CHECKED'}),flush=True)
  except BaseException as exc:
   self.failed=str(exc)
   # Preserve even a failed initialization; never truncate or remove the WAL.
   try:
    with(out/'allocation-initialization-failure.json').open('x')as f:json.dump({'error':str(exc),'preallocateRequested':preallocate,'noFallback':True,'logicalBytes':os.fstat(self.fd).st_size},f,indent=2)
   finally:
    try:self.close()
    except BaseException:
     try:os.close(self.fd)
     except OSError:pass
   raise
 def append(self,kind,frame,payload,flush=False):
  if self.failed or self.closed:raise RuntimeError('WAL unavailable: '+str(self.failed))
  if len(payload)>16384:raise RuntimeError('WAL record bound')
  head=HEADER.pack(KINDS[kind],0,0,frame,len(payload),self.seq,self.record_clock());digest=hashlib.sha256(self.chain+head+payload).digest();blob=head+payload+struct.pack('<I',zlib.crc32(head+payload))+digest
  start=time.perf_counter_ns();seq=self.seq
  try:
   if self.bytes+len(blob)>self.limit:raise RuntimeError('WAL quota')
   view=memoryview(blob);offset=0
   while offset<len(view):
    override=self.hook('wal-write',kind,frame,self.fd,view[offset:])
    n=self.trace.call('write',kind,frame,self.bytes+offset,len(view)-offset,lambda:os.write(self.fd,view[offset:]))if override is None else override
    if n<=0 or n>len(view)-offset:raise RuntimeError('Invalid WAL write length')
    offset+=n
   self.bytes+=len(blob);self.seq+=1;self.chain=digest
   if flush:
    a=time.perf_counter_ns();self.hook('wal-flush',kind,frame,self.fd,None);self.trace.call('fsync',kind,frame,self.bytes,0,lambda:os.fsync(self.fd));self.flush_cost.append(time.perf_counter_ns()-a);self.flushes+=1
   self.append_cost.append(time.perf_counter_ns()-start);return seq
  except Exception as e:
   self.failed=str(e)
   # Separate bounded failure record; no truncation/repair of the original WAL.
   try:
    fd=self.trace.call('open','EMERGENCY',frame,0,0,lambda:os.open(self.out/f'wal-failure-{seq}.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600))
    try:
     pos=0
     while pos<len(blob):
      n=self.trace.call('write','EMERGENCY',frame,pos,len(blob)-pos,lambda:os.write(fd,memoryview(blob)[pos:]))
      if n<=0 or n>len(blob)-pos:raise RuntimeError('Invalid emergency write')
      pos+=n
     self.trace.call('fsync','EMERGENCY',frame,len(blob),0,lambda:os.fsync(fd))
    finally:self.trace.call('close','EMERGENCY',frame,0,0,lambda:os.close(fd))
    (self.out/f'wal-failure-{seq}.json').write_bytes(encode({'kind':kind,'frame':frame,'error':self.failed,'fullAttemptedRecordSha256':hashlib.sha256(blob).hexdigest(),'completePublicationBarrier':False}))
   except Exception as spare:self.failed+='; emergency capture failed: '+str(spare)
   raise
 def close(self):
  if self.closed:return
  self.closed=True;self.trace.call('close','CLOSE',0,self.bytes,0,lambda:os.close(self.fd))

