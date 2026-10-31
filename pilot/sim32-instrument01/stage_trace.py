"""Host-only bounded mmap stage observer; no physics or journal changes."""
import mmap,struct,os,time
class StageTrace:
 def __init__(self,path):
  self.fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);os.ftruncate(self.fd,16*1024**2)
  self.map=mmap.mmap(self.fd,16*1024**2);self.n=0;self.failed=False;self.capacity=(16*1024**2-4096)//88
  struct.pack_into('<8sQQQ',self.map,0,b'AERISBH1',self.capacity,0,88)
 def record(self,values):
  if self.n>=self.capacity:self.failed=True;raise RuntimeError('Backend stage trace capacity; no drop')
  start=time.monotonic_ns();struct.pack_into('<11Q',self.map,4096+self.n*88,*values,start);self.n+=1
  struct.pack_into('<Q',self.map,16,self.n)
 def seal(self):
  self.map.flush();os.fsync(self.fd);self.map.close();os.close(self.fd)
