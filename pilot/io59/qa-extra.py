from pathlib import Path
import json,errno,os,struct,sys
from instrument import IOTrace,TimedWal,KIND,OPS
R=Path(__file__).resolve().parents[2];E=R/'evidence/io59';out=E/'mock/extra01';out.mkdir();checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
class FsyncFault(IOTrace):
 def call(self,op,kind,frame,offset,requested,fn):
  if op=='fsync' and kind=='INTENT':
   def fail():raise OSError(errno.ENOSPC,'INJECTED_FSYNC_ENOSPC')
   fn=fail
  return super().call(op,kind,frame,offset,requested,fn)
t=FsyncFault(100);w=TimedWal(out,{},trace=t);published=False
try:w.append('INTENT',1,b'fixture',flush=True);published=True
except OSError:pass
finally:w.close()
rows=[t.data[i*12:(i+1)*12]for i in range(t.count)]
ck('fsync errno recorded at actual instrumented call boundary',any(r[1]==OPS['fsync'] and r[2]==KIND['INTENT'] and r[-1]==errno.ENOSPC for r in rows))
ck('failed barrier never returns publication permission',not published and w.failed is not None)
ck('full attempted record emergency separate from original WAL',(out/'wal-failure-1.bin').exists() and (out/'frames.wal').exists())
raw='Khảo sát Hera · frame完整'.encode();t.snapshot(out/'snapshot.pending',out/'snapshot.json',raw,1)
ck('atomic snapshot same exact UTF8 bytes',(out/'snapshot.json').read_bytes()==raw and not(out/'snapshot.pending').exists())
ck('snapshot uses independently tagged open/write/close/replace',set(r[1]for i in range(t.count)if (r:=t.data[i*12:(i+1)*12])[2]==KIND['SNAPSHOT'])=={1,3,4,5})
t.seal(out/'syscalls.bin',out/'syscalls-meta.json')
ck('sealed trace exact length no silent tail',(out/'syscalls.bin').stat().st_size==24+t.count*96)
with(E/'qa-extra.json').open('x')as f:json.dump({'status':'PASS_SCOPED_FAULT_SNAPSHOT','checks':checks},f,indent=2)
print(json.dumps({'checks':len(checks),'status':'PASS'}))
