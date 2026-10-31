"""Fault injection at explicit syscall seam; no global os monkeypatch."""
from pathlib import Path
import sys,os,time,json,struct,errno
from instrument import IOTrace,TimedWal,WakeProbe,OPS,KIND
R=Path(__file__).resolve().parents[2];E=R/'evidence/alloc60';sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import Wal,read_wal,encode
out=E/'mock/syscall01';out.mkdir();checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)});assert value,name
class Inject(IOTrace):
 def __init__(self,variant):super().__init__(10000);self.variant=variant;self.injected=False
 def call(self,op,kind,frame,offset,requested,fn):
  if kind=='INTENT' and not self.injected and ((self.variant=='delay' and op=='fsync')or(self.variant!='delay' and op=='write')):
   self.injected=True
   if self.variant=='short':fn=lambda:os.write(self.fd,self.body[:7])
   elif self.variant=='zero':fn=lambda:0
   elif self.variant in ['eio','eintr']:
    def fail():raise OSError(errno.EIO if self.variant=='eio'else errno.EINTR,'INJECTED')
    fn=fail
   elif self.variant=='delay':
    original=fn
    def delayed():time.sleep(.025);return original()
    fn=delayed
  return super().call(op,kind,frame,offset,requested,fn)
for variant in ['short','zero','eio','eintr','delay']:
 d=out/variant;d.mkdir();trace=Inject(variant);wal=TimedWal(d,{},trace=trace,preallocate=True,limit=2*2**20);trace.fd=wal.fd
 def hook(stage,kind,frame,fd,remaining):
  if stage=='wal-write' and kind=='INTENT':trace.body=bytes(remaining)
 wal.hook=hook;published=False;failure=None
 try:wal.append('INTENT',7,encode({'payload':'Độ chính xác'*10}),flush=True);published=True
 except OSError as e:failure=e.errno
 except RuntimeError as e:failure=str(e)
 finally:wal.close();trace.seal(d/'syscalls.bin',d/'syscalls-meta.json')
 rows=[list(trace.data[i*12:(i+1)*12])for i in range(trace.count)];io=[v for v in rows if v[2]==KIND['INTENT']]
 if variant in ['short','delay']:check(variant+' complete CRC/SHA WAL and publication after barrier',published and read_wal(d/'frames.wal')['error']is None)
 else:check(variant+' fails closed with full attempted emergency record',not published and (d/'wal-failure-1.bin').exists())
 if variant=='short':check('short write exact offset continuation',len([v for v in io if v[1]==1])==2 and [v for v in io if v[1]==1][1][4]==[v for v in io if v[1]==1][0][4]+7)
 if variant in ['eio','eintr']:check(variant+' errno retained',any(v[-1]==failure for v in io))
 if variant=='delay':
  q=[v for v in io if v[1]==2][0];check('blocking fsync >=20ms wall and <5ms CPU',q[7]-q[6]>=20000000 and q[9]-q[8]<5000000)
 check(variant+' every syscall row sealed once',struct.unpack('<8sQQ',(d/'syscalls.bin').read_bytes()[:24])==(b'AERISIO9',trace.count,12))
trace=IOTrace(1);trace.call('write','RX',0,0,0,lambda:0)
try:trace.call('write','RX',1,0,0,lambda:0);raise AssertionError('overflow accepted')
except RuntimeError:check('trace overflow fails before unobserved syscall',trace.overflow and trace.count==1)
w=WakeProbe();w.start();time.sleep(.055);w.seal(out/'wake.bin');check('wake missed deadlines reconstructable',w.count>=2 and all(w.data[(i+1)*6]==w.data[i*6]+(w.data[i*6+3]+1)*w.period for i in range(w.count-1)))
trace=IOTrace(20000);a=time.monotonic_ns();c=time.thread_time_ns()
for i in range(20000):trace.call('write','RX',i,0,0,lambda:0)
cal={'calls':20000,'totalWallNs':time.monotonic_ns()-a,'totalThreadCpuNs':time.thread_time_ns()-c,'scope':'No-op wrapper incl four clocks and row serialization; not subtracted from actual timing'}
cost=[]
for label,klass in [('original',Wal),('timed',TimedWal)]:
 d=out/label;d.mkdir();wal=klass(d,{});a=time.monotonic_ns();c=time.thread_time_ns()
 for i in range(1000):wal.append('RX',i,b'input');wal.append('INTENT',i,b'output',flush=True);wal.append('SENT',i,b'returned')
 wal.close();cost.append({'label':label,'frames':1000,'wallNs':time.monotonic_ns()-a,'threadCpuNs':time.thread_time_ns()-c})
 parsed=read_wal(d/'frames.wal');check(label+' 3001records CRC/hash replay',parsed['error']is None and len(parsed['records'])==3001)
 if label=='timed':wal.trace.seal(d/'syscalls.bin',d/'syscalls-meta.json')
report={'status':'PASS_SCOPED_IO_MOCK','checks':checks,'clockAndObserverCalibration':cal,'sequentialWalCosts':cost,'schedulingAttribution':'NONCPU_AND_WAKE_PROXY_ONLY_EXCLUSIVE_KERNEL_RUNNABLE_WAIT_UNKNOWN'}
with(E/'qa-io.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({'status':report['status'],'checks':len(checks),'calibration':cal,'costs':cost}))
