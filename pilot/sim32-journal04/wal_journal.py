"""Single-owner pre-send WAL; bounded derived archive. No flight transport."""
import os,json,struct,hashlib,zlib,gzip,time,queue,threading
from dataclasses import dataclass

MAGIC=b'AERISJ04'
HEADER=struct.Struct('<BBHIIQQ')
KINDS={'HEADER':1,'RX':2,'INTENT':3,'SENT':4,'OUTCOME':5,'CLOSE':6,'ERROR':7}
NAMES={v:k for k,v in KINDS.items()}
def encode(obj):return json.dumps(obj,separators=(',',':'),allow_nan=False).encode()
def unpack_intent(payload):
 a,b=struct.unpack_from('<II',payload);assert len(payload)==8+a+b
 return payload[8:8+a],payload[8+a:]

class ArchiveSink:
 # Unbuffered exact-write adapter: gzip must never silently accept short writes.
 def __init__(self,file,hook,frame):self.file,self.hook,self.frame=file,hook,frame
 def write(self,data):
  view=memoryview(data);offset=0
  while offset<len(view):
   override=self.hook('compressed-write','ARCHIVE',self.frame(),self.file.fileno(),view[offset:])
   n=self.file.write(view[offset:])if override is None else override
   if n<=0 or n>len(view)-offset:raise RuntimeError('Invalid compressed write length')
   offset+=n
  return len(data)
 def tell(self):return self.file.tell()
 def flush(self):return self.file.flush()

class Wal:
 def __init__(self,out,metadata,policy='fsync-before-publish',limit=16*1024**2,hook=lambda *a:None):
  if policy not in ['fsync-before-publish','process-crash-only']:raise ValueError('Explicit durability policy')
  self.out,self.policy,self.limit,self.hook=out,policy,limit,hook
  self.fd=os.open(out/'frames.wal',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(self.fd,MAGIC)
  self.seq=0;self.chain=bytes(32);self.bytes=8;self.failed=None;self.closed=False;self.flushes=0;self.append_cost=[];self.flush_cost=[]
  self.append('HEADER',0,encode({**metadata,'format':'aeris-journal04','version':1,'durabilityPolicy':policy,'hostPowerLoss':'NOT_CHECKED'}),flush=True)
 def append(self,kind,frame,payload,flush=False):
  if self.failed or self.closed:raise RuntimeError('WAL unavailable: '+str(self.failed))
  if len(payload)>16384:raise RuntimeError('WAL record bound')
  head=HEADER.pack(KINDS[kind],0,0,frame,len(payload),self.seq,time.monotonic_ns());digest=hashlib.sha256(self.chain+head+payload).digest();blob=head+payload+struct.pack('<I',zlib.crc32(head+payload))+digest
  start=time.perf_counter_ns();seq=self.seq
  try:
   if self.bytes+len(blob)>self.limit:raise RuntimeError('WAL quota')
   view=memoryview(blob);offset=0
   while offset<len(view):
    override=self.hook('wal-write',kind,frame,self.fd,view[offset:])
    n=os.write(self.fd,view[offset:])if override is None else override
    if n<=0 or n>len(view)-offset:raise RuntimeError('Invalid WAL write length')
    offset+=n
   self.bytes+=len(blob);self.seq+=1;self.chain=digest
   if flush:
    a=time.perf_counter_ns();self.hook('wal-flush',kind,frame,self.fd,None);os.fsync(self.fd);self.flush_cost.append(time.perf_counter_ns()-a);self.flushes+=1
   self.append_cost.append(time.perf_counter_ns()-start);return seq
  except Exception as e:
   self.failed=str(e)
   # Separate bounded failure record; no truncation/repair of the original WAL.
   try:
    with(self.out/f'wal-failure-{seq}.bin').open('xb')as f:f.write(blob);f.flush();os.fsync(f.fileno())
    (self.out/f'wal-failure-{seq}.json').write_bytes(encode({'kind':kind,'frame':frame,'error':self.failed,'fullAttemptedRecordSha256':hashlib.sha256(blob).hexdigest(),'completePublicationBarrier':False}))
   except Exception as spare:self.failed+='; emergency capture failed: '+str(spare)
   raise
 def close(self):
  if self.closed:return
  self.closed=True;os.close(self.fd)

@dataclass(frozen=True)
class Prepared:
 frame:int
 row:bytes
 snapshot:bytes
 intent_seq:int
 archive:bytes

class Journal:
 def __init__(self,out,state,metadata,policy='fsync-before-publish',raw_limit=512*1024**2,compressed_limit=192*1024**2,wal_limit=16*1024**2,slots=256,seal_seconds=2,hook=lambda *a:None):
  self.out,self.state,self.hook,self.seal_seconds=out,state,hook,seal_seconds
  self.wal=Wal(out,metadata,policy,wal_limit,hook);self.queue=queue.Queue(maxsize=slots);self.slots=threading.BoundedSemaphore(slots);self.capacity=slots
  self.error=None;self.errors=[];self.lock=threading.Lock();self.reserved=set();self.admitted=set();self.intents={};self.sent=set();self.not_sent=set();self.pending=0;self.highwater=0
  self.raw_limit,self.compressed_limit=raw_limit,compressed_limit;self.raw_bytes=0;self.rows=0;self.snapshots=0;self.digest=hashlib.sha256();self.costs=[];self.ready=threading.Event();self.sealed=False
  self.worker=threading.Thread(target=self.work,name='journal04-archive',daemon=True);self.worker.start()
  if not self.ready.wait(2):raise RuntimeError('Archive start deadline')
  self.check()
 def fail(self,error):
  with self.lock:
   if self.error is None:self.error=str(error)
   if len(self.errors)<16:self.errors.append(str(error))
 def check(self):
  if self.error or self.wal.failed or self.sealed:raise RuntimeError('Journal unavailable: '+str(self.error or self.wal.failed or 'sealed'))
 def receive(self,frame,data,peer):
  if self.sealed or self.wal.failed:raise RuntimeError('Cannot retain received datagram: WAL unavailable')
  return self.wal.append('RX',frame,encode({'rawHex':data.hex(),'peer':peer,'source':'MOCK_DATAGRAM','counterDomain':'mock-backend-python-monotonic'}))
 def reserve(self,frame):
  self.check()
  if self.prepared_bytes+8192>self.raw_limit:self.fail('Raw admission quota before model');raise RuntimeError(self.error)
  if frame in self.admitted:raise RuntimeError('Duplicate journal admission')
  if not self.slots.acquire(blocking=False):self.fail('Queue admission full before model');raise RuntimeError(self.error)
  with self.lock:self.reserved.add(frame);self.admitted.add(frame);self.pending+=1;self.highwater=max(self.highwater,self.pending)
 def release(self,frame):
  with self.lock:
   if frame not in self.reserved:return
   self.reserved.remove(frame);self.pending-=1;self.intents.pop(frame,None);self.slots.release()
 def prepare(self,row,snapshot):
  frame=row['frame'];self.check()
  if frame not in self.reserved:raise RuntimeError('Intent without queue reservation')
  if 'sensorSent'in row:raise ValueError('Intent cannot assert transmission')
  body=encode(row);snap=encode(snapshot)if snapshot is not None else b''
  archive=body[:-1]+b',"sensorSent":true,"sendObservation":"UDP_SEND_RETURNED_LENGTH"}\n'
  if len(archive)>8192:raise RuntimeError('Archive row bound')
  # Total generated archive bytes is bounded before publication, not after compression.
  if self.prepared_bytes+len(archive)>self.raw_limit:raise RuntimeError('Raw admission quota before publication')
  payload=struct.pack('<II',len(body),len(snap))+body+snap
  seq=self.wal.append('INTENT',frame,payload,flush=self.wal.policy=='fsync-before-publish')
  p=Prepared(frame,body,snap,seq,archive);self.intents[frame]=p;self.prepared_bytes+=len(archive);return p
 @property
 def prepared_bytes(self):return getattr(self,'_prepared_bytes',0)
 @prepared_bytes.setter
 def prepared_bytes(self,n):self._prepared_bytes=n
 def transmitted(self,p,returned_bytes,expected_bytes):
  if returned_bytes!=expected_bytes:
   self.wal.append('OUTCOME',p.frame,encode({'intentSeq':p.intent_seq,'outcome':'PARTIAL_OR_UNKNOWN_SEND','returnedBytes':returned_bytes,'expectedBytes':expected_bytes}));self.fail('Partial UDP result');self.release(p.frame);raise RuntimeError(self.error)
  self.wal.append('SENT',p.frame,encode({'intentSeq':p.intent_seq,'outcome':'UDP_SEND_RETURNED_LENGTH','returnedBytes':returned_bytes}))
  self.sent.add(p.frame)
  try:self.queue.put_nowait(p)
  except queue.Full:self.fail('Reserved queue invariant failed');self.release(p.frame);raise RuntimeError(self.error)
 def aborted(self,frame,reason):
  if not self.wal.failed:
   try:self.wal.append('OUTCOME',frame,encode({'outcome':'NO_SEND_CALLED','reason':str(reason)}));self.not_sent.add(frame)
   except Exception as e:self.fail(e)
  self.release(frame)
 def work(self):
  log=None;item=None;raw=None;archive_frame=0
  try:
   raw=(self.out/'physics-raw.jsonl.gz').open('xb',buffering=0);sink=ArchiveSink(raw,self.hook,lambda:archive_frame)
   log=gzip.GzipFile(filename='physics-raw.jsonl',mode='wb',fileobj=sink,compresslevel=1);self.ready.set()
   while True:
    item=self.queue.get()
    if item is None:break
    archive_frame=item.frame
    start=time.perf_counter_ns();self.hook('archive-before-write','SENT',item.frame,None,None)
    if log.fileobj.tell()+len(item.archive)+128*1024>self.compressed_limit:raise RuntimeError('Compressed archive quota')
    self.hook('archive-write','SENT',item.frame,None,None);log.write(item.archive);self.digest.update(item.archive);self.raw_bytes+=len(item.archive);self.rows+=1
    if item.snapshot:
     self.hook('snapshot-write','SENT',item.frame,None,None);tmp=self.state/'physics.pending';tmp.write_bytes(item.snapshot);os.replace(tmp,self.state/'physics.json');self.snapshots+=1
    self.costs.append(time.perf_counter_ns()-start);self.release(item.frame)
  except Exception as e:
   self.fail(e);self.ready.set()
   if item is not None:self.release(item.frame)
   while True:
    try:p=self.queue.get_nowait()
    except queue.Empty:break
    if p is not None:self.release(p.frame)
  finally:
   if log:
    try:self.hook('archive-close','CLOSE',0,None,None);log.close()
    except Exception as e:self.fail(e)
   if raw:
    try:raw.close()
    except Exception as e:self.fail(e)
 def seal(self):
  if self.sealed:raise RuntimeError('Journal already finalized')
  self.sealed=True
  try:
   if self.worker.is_alive():
    self.queue.put(None,timeout=self.seal_seconds);self.worker.join(self.seal_seconds)
   if self.worker.is_alive():raise RuntimeError('Archive drain deadline; worker still alive')
   if self.error or self.wal.failed:raise RuntimeError(self.error or self.wal.failed)
   if self.rows!=len(self.sent)or self.reserved:raise RuntimeError('Archive/sent/reservation mismatch')
   with(self.out/'physics-raw.jsonl.gz').open('rb')as f:self.hook('archive-flush','CLOSE',0,f.fileno(),None);os.fsync(f.fileno())
   self.wal.append('CLOSE',0,encode({'archiveRows':self.rows,'sentFrames':len(self.sent),'notSentFrames':sorted(self.not_sent),'archiveSha256':self.digest.hexdigest(),'completeAcceptedCapture':True}),flush=True)
   return {'status':'COMPLETE_ACCEPTED_MOCK_CAPTURE','rows':self.rows,'workerAlive':False}
  except Exception as e:
   self.fail(e);return {'status':'INCOMPLETE_CAPTURE','error':self.error,'errors':self.errors,'workerAlive':self.worker.is_alive(),'rows':self.rows}
  finally:
   if not self.worker.is_alive():self.wal.close()

def read_wal(path):
 records=[];chain=bytes(32);offset=8;error=None
 with path.open('rb')as f:
  if f.read(8)!=MAGIC:raise ValueError('WAL magic')
  while True:
   head=f.read(HEADER.size)
   if not head:break
   if len(head)!=HEADER.size:error='TORN_HEADER';break
   kind,flags,reserved,frame,size,seq,ns=HEADER.unpack(head)
   if kind not in NAMES or flags or reserved or size>16384 or seq!=len(records):error='INVALID_HEADER';break
   payload=f.read(size);tail=f.read(36)
   if len(payload)!=size or len(tail)!=36:error='TORN_PAYLOAD';break
   crc=struct.unpack_from('<I',tail)[0];digest=hashlib.sha256(chain+head+payload).digest()
   if crc!=zlib.crc32(head+payload)or tail[4:]!=digest:error='CRC_OR_CHAIN_MISMATCH';break
   records.append({'kind':NAMES[kind],'frame':frame,'seq':seq,'ns':ns,'payload':payload});chain=digest;offset+=len(head)+size+36
 return {'records':records,'error':error,'verifiedPrefixBytes':offset,'chainHex':chain.hex(),'originalUnchanged':True}
