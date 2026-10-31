"""Synthetic trace writer only, no AP or flight protocol."""
import os,signal,time,struct,mmap
from pathlib import Path
stop=False
signal.signal(signal.SIGTERM,lambda *_:None)
p=Path(os.environ['AERIS_AP_TRACE']);capacity=8000;size=4096+capacity*64
with p.open('xb')as f:f.truncate(size)
with p.open('r+b')as f:
 m=mmap.mmap(f.fileno(),size);m[:40]=struct.pack('<8s4Q',b'AERISD02',capacity,0,0,64);i=0
 while not stop and i<capacity:
  a=time.monotonic_ns();m[4096+i*64:4096+(i+1)*64]=struct.pack('<QQIIQQQQq',i,i,10,os.getpid(),a,a,0,0,0);i+=1;m[16:24]=struct.pack('<Q',i)
  # Small deterministic CPU work and waits exercise kernel counters without host load.
  sum(x*x for x in range(500));time.sleep(.001)
 m.flush();m.close()
