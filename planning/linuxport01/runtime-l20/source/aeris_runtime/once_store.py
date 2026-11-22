"""Version3 original bytes once, compact bounded append receipt journals."""
from pathlib import Path
import hashlib,json,threading
from .metadata_budget import encoded
class OnceStore:
 def __init__(self,root,*,budget):
  if budget is None:raise ValueError('EXPLICIT_METADATA_BUDGET_REQUIRED')
  self.root=Path(root).absolute();self.budget=budget;self.lock=threading.RLock();self.stream_offset=0
  if (self.root/'ack-stream.raw').exists()or(self.root/'command-stream.raw').exists():raise ValueError('ONCE_STORE_NO_STREAM_RESUME')
 def ref(self,path,offset,raw):return {'format':'aeris-original-byte-ref','version':3,'path':path,'offset':offset,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 def blob(self,raw,owner='dto'):
  raw=bytes(raw)
  if len(raw)>16384:raise ValueError('DTO_ACCEPTED16KiB_BOUND')
  self.budget.tick('dtoSnapshots')
  h=hashlib.sha256(raw).hexdigest();name='objects/'+h;path=self.root/name
  with self.lock:
   if path.exists():
    if path.is_symlink()or path.read_bytes()!=raw:raise ValueError('ONCE_BLOB_CONFLICT')
   else:self.budget.write(owner,path,raw)
  return self.ref(name,0,raw)
 def command_bytes(self,raw,*,closing=False):
  raw=bytes(raw)
  if len(raw)>131073:raise ValueError('COMMAND_PREFIX_SOURCE_BOUND')
  with self.lock:
   path=self.root/'command-stream.raw';offset=path.stat().st_size if path.exists()else 0
   self.budget.write('commands',path,raw,append=True,closing=closing)
   return self.ref('command-stream.raw',offset,raw)
 def stream(self,raw):
  raw=bytes(raw)
  with self.lock:
   if self.stream_offset+len(raw)>4*2**20:raise ValueError('ACK_STREAM4MiB_BOUND')
   offset=self.stream_offset;self.budget.write('stream',self.root/'ack-stream.raw',raw,append=True);self.stream_offset+=len(raw)
   return self.ref('ack-stream.raw',offset,raw)
 def retain_failed_stream_chunk(self,raw,offset):
  """Retain already-read failed prefix with closure funds, never publish ACK."""
  raw=bytes(raw);path=self.root/'ack-stream.raw';size=path.stat().st_size if path.exists()else 0
  if not offset<=size<=offset+len(raw):raise ValueError('FAILED_STREAM_PREFIX_OFFSET')
  if size>offset:
   with path.open('rb')as f:f.seek(offset);existing=f.read(size-offset)
   if existing!=raw[:size-offset]:raise ValueError('FAILED_STREAM_PREFIX_BYTES')
  self.budget.write('stream',path,raw[size-offset:],append=True,closing=True);self.stream_offset=offset+len(raw)
 def receipt(self,name,value,owner='command_receipts',closing=False):
  if name.startswith('request-'):kind='request';owner='requests';maximum=16384 if value.get('action')=='BOOTSTRAP'else 2048
  elif name.startswith('command-'):kind='command';owner='command_receipts';maximum=1280
  elif name.startswith('barrier-'):kind='barrier';owner='barriers';maximum=512
  elif name=='stream-close.json':kind='close';maximum=4096;closing=True
  else:kind='diagnostic';maximum=4096
  raw=encoded(value)
  if len(raw)>maximum:raise ValueError('ONCE_'+kind.upper()+'_RECEIPT_BOUND')
  with self.lock:
   rel='receipts/'+kind+'.jsonl';path=self.root/rel;offset=path.stat().st_size if path.exists()else 0;self.budget.write(owner,path,raw,append=True,closing=closing)
   return self.ref(rel,offset,raw)
 def broker_proof(self,value):
  """Original wire header/footer/provenance once in the commands owner."""
  if type(value)is not dict or value.get('format')not in('aeris-device-io-broker-command','aeris-device-io-broker-command-failure')or type(value.get('version'))is not int or value['version']!=1:raise ValueError('BROKER_WIRE_TYPED_PROOF')
  raw=encoded(value)
  if len(raw)>1280:raise ValueError('BROKER_WIRE_ROW1280')
  with self.lock:
   path=self.root/'broker-wire.jsonl';offset=path.stat().st_size if path.exists()else 0
   if offset+len(raw)>3700*1280:raise ValueError('BROKER_WIRE3700_ROWS_ENVELOPE')
   self.budget.write('commands',path,raw,append=True)
   return self.ref('broker-wire.jsonl',offset,raw)
 def status15_proof(self,value):
  if type(value)is not dict or value.get('format')not in('aeris-status15-exchange','aeris-status15-failed-prefix')or type(value.get('version'))is not int or value['version']!=1:raise ValueError('STATUS15_TYPED_WIRE_PROOF')
  raw=encoded(value)
  if len(raw)>4096:raise ValueError('STATUS15_PROOF4096')
  with self.lock:
   path=self.root/'status15-wire.jsonl';offset=path.stat().st_size if path.exists()else 0
   if offset+len(raw)>900*4096:raise ValueError('STATUS15_900_EXCHANGE_ENVELOPE')
   self.budget.write('commands',path,raw,append=True)
   return self.ref('status15-wire.jsonl',offset,raw)
 def receipts(self,kind='request'):
  if kind not in('request','command','barrier','close','diagnostic'):raise ValueError('TYPED_RECEIPT_JOURNAL')
  from .once_reader import unique
  path=self.root/'receipts'/(kind+'.jsonl')
  if not path.exists():return []
  result=[]
  with path.open('rb')as f:
   while True:
    line=f.readline(16385)
    if not line:break
    if len(line)>16384 or not line.endswith(b'\n'):raise ValueError('RECEIPT_JOURNAL_INCOMPLETE')
    result.append(json.loads(line,object_pairs_hook=unique))
  return result
