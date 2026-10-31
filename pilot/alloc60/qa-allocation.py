from pathlib import Path
import sys,os,json,errno,ctypes,struct
from instrument import TimedWal,IOTrace,KIND,OPS
from extent import FStore,native_allocate
R=Path(__file__).resolve().parents[2];E=R/'evidence/alloc60';sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import read_wal
out=E/'mock/allocation01';out.mkdir();checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
ck('Darwin fstore_t 32-byte ABI and 64bit fields',ctypes.sizeof(FStore)==32 and [getattr(FStore,k).offset for k in ['flags','posmode','offset','length','bytesalloc']]==[0,4,8,16,24])
results=[]
for enabled in [False,True]:
 d=out/('preallocate'if enabled else'none');d.mkdir();t=IOTrace(10000);counter=iter(range(100000,200000));w=TimedWal(d,{'fixture':'same bytes'},limit=2*2**20,trace=t,preallocate=enabled,record_clock=lambda:next(counter))
 if enabled:ck('reserve exact extent with zero EOF and offset',w.allocation['returnedAllocatedBytes']>=2*2**20 and w.allocation['logicalSizeAfter']==w.allocation['positionAfter']==0)
 for i in range(100):w.append('RX',i,b'RX');w.append('INTENT',i,b'SENSOR',flush=True);w.append('SENT',i,b'SENT')
 w.append('CLOSE',0,b'{}',flush=True);expected=w.bytes;w.close();raw=(d/'frames.wal').read_bytes();results.append(raw)
 parsed=read_wal(d/'frames.wal');ck(('preallocated'if enabled else'none')+' exact logical EOF CRC/SHA records no filler',len(raw)==expected and not parsed['error'] and len(parsed['records'])==302)
 t.seal(d/'syscalls.bin',d/'syscalls-meta.json');ck(('preallocated'if enabled else'none')+' all INTENTs own fsync',sum(t.data[i*12+1]==OPS['fsync'] and t.data[i*12+2]==KIND['INTENT']for i in range(t.count))==100)
ck('whole WAL bytes identical with controlled record clock',results[0]==results[1])
for variant in ['enospc','unsupported','partial','changesEOF']:
 d=out/variant;d.mkdir();trace=IOTrace(100);fds=[]
 def fail(fd,n):
  fds.append(fd)
  if variant in ['enospc','unsupported']:raise OSError(errno.ENOSPC if variant=='enospc'else errno.ENOTSUP,'INJECTED_ALLOCATION')
  if variant=='changesEOF':os.ftruncate(fd,1);return n
  return n-1
 error=None
 try:TimedWal(d,{},limit=2*2**20,trace=trace,preallocate=True,allocation_fn=fail)
 except (OSError,RuntimeError)as exc:error=str(exc)
 ck(variant+' fail closed no HEADER/MAGIC or silent fallback',error is not None and not(d/'allocation.json').exists() and (d/'allocation-initialization-failure.json').exists())
 try:os.fstat(fds[0]);closed=False
 except OSError as exc:closed=exc.errno==errno.EBADF
 ck(variant+' descriptor closed on initialization failure',closed)
 ck(variant+' physical attempt trace retained with error/short return',any(trace.data[i*12+1]==OPS['preallocate']for i in range(trace.count)))
 trace.seal(d/'syscalls.bin',d/'syscalls-meta.json')
# A very small trace must fail before any unobserved writes and release the fd.
d=out/'overflow';d.mkdir();trace=IOTrace(1)
try:TimedWal(d,{},trace=trace,preallocate=True,limit=2*2**20);raise AssertionError('overflow accepted')
except RuntimeError:ck('allocation trace overflow fails closed and leaves empty WAL',trace.overflow and (d/'frames.wal').stat().st_size==0)
report={'status':'PASS_NATIVE_EXTENT_AND_FAULT_MOCK','checks':checks,'physicalReservationMayPersistAfterClose':True,'noPowerLossClaim':True}
with(E/'qa-allocation.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({'status':report['status'],'checks':len(checks)}))
