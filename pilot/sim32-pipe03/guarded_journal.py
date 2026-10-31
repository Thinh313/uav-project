"""Bounded, single-writer full evidence FIFO; failures are never hidden."""
import gzip,json,hashlib,os,time,queue,threading
from pathlib import Path

class Journal:
 def __init__(self,out,state,threaded,raw_limit=512*1024**2,compressed_limit=192*1024**2):
  self.out,self.state,self.threaded=out,state,threaded
  self.raw_limit,self.compressed_limit=raw_limit,compressed_limit;self.rescue=[];self.rescue_lock=threading.Lock()
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
  if len(data)>8192:raise RuntimeError('Raw row bound; preserve incomplete tail')
  if self.log.fileobj.tell()+len(data)+128*1024>self.compressed_limit:raise RuntimeError('Compressed evidence bound; incomplete evidence')
  if self.bytes+len(data)>self.raw_limit:raise RuntimeError('Raw evidence bound; incomplete evidence')
  self.log.write(data);self.digest.update(data);self.bytes+=len(data);self.rows+=1
  if snapshot is not None:
   tmp=self.state/'physics.pending';tmp.write_text(json.dumps(snapshot,allow_nan=False));os.replace(tmp,self.state/'physics.json');self.snapshots+=1
  self.costs.append((time.perf_counter_ns()-start)/1e6)
 def submit(self,row,snapshot):
  try:self.check()
  except Exception:
   self.rescue_unsubmitted(row);raise
  if self.threaded:
   try:self.queue.put_nowait((row,snapshot))
   except queue.Full:
    self.error='Journal queue full';self.rescue_unsubmitted(row);raise RuntimeError('Journal queue full; incomplete tail preserved')
   self.highwater=max(self.highwater,self.queue.qsize())
  else:
   try:self.write((row,snapshot))
   except Exception as e:
    self.error=str(e);self.rescue_unsubmitted(row);raise
 def rescue_unsubmitted(self,row):
  with self.rescue_lock:
   if row['frame']<self.rows or any(x['frame']==row['frame']for x in self.rescue):return
   if len(self.rescue)>=258:raise RuntimeError('Rescue tail bound; incomplete capture')
   self.rescue.append(row)
 def drain_failed(self):
  while True:
   try:item=self.queue.get_nowait()
   except queue.Empty:break
   if item is not None:self.rescue_unsubmitted(item[0])
 def work(self):
  item=None
  try:
   self.log=gzip.open(self.out/'physics-raw.jsonl.gz','xb',compresslevel=1);self.ready.set()
   while True:
    item=self.queue.get()
    if item is None:break
    self.write(item)
  except Exception as e:
   self.error=str(e);self.ready.set()
   if item is not None:self.rescue_unsubmitted(item[0])
   self.drain_failed()
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
  self.drain_failed()
  if self.rescue:
   with (self.out/'journal-incomplete-tail.jsonl').open('x')as f:
    for row in sorted(self.rescue,key=lambda x:x['frame']):f.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
    f.flush();os.fsync(f.fileno())
  self.check()
  with (self.out/'physics-raw.jsonl.gz').open('rb') as f:os.fsync(f.fileno())
