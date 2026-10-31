"""Bounded read-only-source filesystem probe, never launches AP or modifies runtime."""
from pathlib import Path
import os,struct,json,time,hashlib,statistics,fcntl,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';assert shutil.disk_usage(R).free>=20*2**30
src=R/'.local/simverify02/receiver04/evidence/simhand01/runs/rfebb3af9a261492cabd8/frames.wal';H=struct.Struct('<BBHIIQQ');records=[]
with src.open('rb')as f:
 magic=f.read(8);assert magic==b'AERISJ04'
 while len(records)<6001:
  head=f.read(H.size);kind,_,_,frame,n,seq,at=H.unpack(head);tail=f.read(n+36);assert len(tail)==n+36
  records.append((kind,frame,head+tail))
assert sum(k==3 for k,_,_ in records)==2000
raw=magic+b''.join(blob for _,_,blob in records);assert len(raw)*2<=32*2**20
expected=hashlib.sha256(raw).hexdigest();results=[]
def summary(a):
 a=sorted(a);return {'n':len(a),'meanUs':statistics.mean(a)/1000,'p50Us':a[len(a)//2]/1000,'p95Us':a[int(len(a)*.95)]/1000,'p99Us':a[int(len(a)*.99)]/1000,'maxUs':a[-1]/1000}
for preallocate in [False,True]:
 p=E/('wal-probe-preallocated.bin'if preallocate else'wal-probe-normal.bin');fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);reserve=None;writes=[];syncs=[];failed=None
 try:
  if preallocate:
   reserveStart=time.monotonic_ns()
   try:
    # Darwin fstore_t: allocate physical extents; preserve logical EOF=0.
    fcntl.fcntl(fd,42,struct.pack('=IIqqq',4,3,0,len(raw),0));assert os.fstat(fd).st_size==0
    reserve={'supported':True,'ns':time.monotonic_ns()-reserveStart,'logicalEOFBeforeWrite':0}
   except OSError as e:reserve={'supported':False,'errno':e.errno,'error':str(e)}
  os.write(fd,magic);start=time.monotonic_ns()
  for kind,frame,blob in records:
   begin=time.monotonic_ns();view=memoryview(blob);offset=0
   while offset<len(view):
    n=os.write(fd,view[offset:]);assert n>0;offset+=n
   writes.append(time.monotonic_ns()-begin)
   if kind in [1,3]:
    begin=time.monotonic_ns();os.fsync(fd);syncs.append(time.monotonic_ns()-begin)
  os.fsync(fd);elapsed=time.monotonic_ns()-start
 finally:os.close(fd)
 actual=p.read_bytes();assert actual==raw and p.stat().st_size==len(raw)
 results.append({'preallocationRequested':preallocate,'allocation':reserve,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest(),'write':summary(writes),'fsync':summary(syncs),'elapsedSeconds':elapsed/1e9})
receipt={'status':'PASS_EXACT_BYTES_PROBE_ONLY','source':str(src),'prefixRecords':len(records),'frames':2000,'totalNewDataBytes':len(raw)*2,'expectedSHA256':expected,'results':results,'decision':'NO_RUNTIME_PREALLOCATION_ADOPTED','limitations':['Single sequential filesystem probe; host load/order/cache uncontrolled','No AP/network scheduling measurement','Physical allocation success is separate from speed improvement','fsync remains before sensor publication; no frame omissions or zero-padding']}
(E/'wal-preallocation-probe01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
