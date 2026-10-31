"""Bounded, single-writer full evidence FIFO; failures are never hidden."""
import gzip,json,hashlib,os,time,queue,threading
from pathlib import Path

class Journal:
 def __init__(self,out,state,threaded):
  self.out,self.state,self.threaded=out,state,threaded
  self.queue=queue.Queue(maxsize=256);self.error=None;self.digest=hashlib.sha256();self.bytes=0;self.rows=0;self.snapshots=0;self.highwater=0;self.costs=[];self.ready=threading.Event();self.log=None
  if threaded:
   self.worker=threading.Thread(target=self.work,name='sim32-evidence',daemon=True);self.worker.start()
   if not self.ready.wait(3):raise RuntimeError('Journal startup timeout')
   self.check()
  else:self.log=gzip.open(out/'physics-raw.jsonl.gz','xb',compresslevel=1)
 def check(self):
  if self.error:raise RuntimeError('Journal failed: '+self.error)
 def write(self,item):
  row,snapshot=item;start=time.perf_counter_ns();data=json.dumps(row,separators=(',',':'),allow_nan=False).encode()+b'\n'
  if self.bytes+len(data)>128*1024**2:raise RuntimeError('Raw evidence bound; incomplete evidence')
  self.log.write(data);self.digest.update(data);self.bytes+=len(data);self.rows+=1
  if snapshot is not None:
   tmp=self.state/'physics.pending';tmp.write_text(json.dumps(snapshot,allow_nan=False));os.replace(tmp,self.state/'physics.json');self.snapshots+=1
  self.costs.append((time.perf_counter_ns()-start)/1e6)
 def submit(self,row,snapshot):
  self.check()
  if self.threaded:
   try:self.queue.put_nowait((row,snapshot))
   except queue.Full:raise RuntimeError('Journal queue full; no evidence drop allowed')
   self.highwater=max(self.highwater,self.queue.qsize())
  else:self.write((row,snapshot))
 def work(self):
  try:
   self.log=gzip.open(self.out/'physics-raw.jsonl.gz','xb',compresslevel=1);self.ready.set()
   while True:
    item=self.queue.get()
    if item is None:break
    self.write(item)
  except Exception as e:self.error=str(e);self.ready.set()
  finally:
   if self.log:
    try:self.log.close()
    except Exception as e:self.error=str(e)
 def seal(self):
  if self.threaded:
   if self.worker.is_alive():
    try:self.queue.put(None,timeout=3)
    except queue.Full:raise RuntimeError('Journal cannot seal full queue')
    self.worker.join(5)
    if self.worker.is_alive():raise RuntimeError('Journal drain deadline; evidence incomplete')
  elif self.log:self.log.close()
  self.check()
  with (self.out/'physics-raw.jsonl.gz').open('rb') as f:os.fsync(f.fileno())
