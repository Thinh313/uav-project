"""G12 bounded evidence writers. Shared policy/ledger; no runtime/control effects on import."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,threading,subprocess,re
R=Path(__file__).resolve().parents[2]
_clock_path=Path(__file__).resolve().parents[2]/'pilot/beta06g12/clock_basis.py'
if 'aeris_g12_clock'in sys.modules:
 host_clock=sys.modules['aeris_g12_clock'];assert Path(host_clock.__file__).resolve()==_clock_path.resolve(),'CANONICAL_CLOCK_PATH_REQUIRED'
else:
 _clock_spec=importlib.util.spec_from_file_location('aeris_g12_clock',_clock_path);host_clock=importlib.util.module_from_spec(_clock_spec);sys.modules[_clock_spec.name]=host_clock;_clock_spec.loader.exec_module(host_clock)
_quota=None;_tickets={};_lock=threading.RLock()
def quota():
 global _quota
 if _quota is None:
  p=R/'pilot/beta06g12/quota.py';s=importlib.util.spec_from_file_location('g12_shared_quota',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);_quota=m
 return _quota
def validate_path(path,*,exclusive=False):
 path=Path(path);scope=R/'evidence/beta06/generation12';assert path.is_absolute()and path.is_relative_to(scope)and '..'not in path.parts and '.'not in path.parts,'G12_WRITER_ACTIVE_SCOPE_REQUIRED'
 for ancestor in [path.parent,*path.parents]:
  assert not ancestor.is_symlink(),'G12_WRITER_ANCESTOR_SYMLINK'
  if ancestor==R:break
 assert not path.is_symlink()and(not exclusive or not path.exists()),'EXCLUSIVE_G12_WRITER_REQUIRED';return path
def preclaim(path,maximum,*,category='native',kind='metadata',closure=False):
 path=validate_path(path,exclusive=True);key=str(path.resolve())
 if closure:assert category=='native'and re.fullmatch(r'android-(?:closure|stop-request)(?:24|25)\.json|android-admission(?:24|25)-[0-9]+\.json|root-controller-closure(?:24|25)\.jsonl|[a-z0-9-]+-completion-summary\.json',path.name),'DECLARED_CLOSURE_PATH_ONLY'
 with _lock:
  assert key not in _tickets,'WRITER_CLAIM_ALREADY_CONSUMED_NO_RETRY'
  if category=='screenshots':
   p=quota().load_policy()['categories']['screenshots'];assert maximum==p['perFileBytes']and kind in ['dispatch','prepare','direct'],'EXACT_PNG_POLICY_REQUIRED';claim='png-'+kind+':'+path.name
  else:claim=('closure'if closure else kind)+':'+hashlib.sha256(key.encode()).hexdigest()
  proof=quota().reserve_write(category=category,entries=1,bytes=maximum,claim_id=claim,closure=closure);_tickets[key]={'maximum':maximum,'used':False,'proof':proof}
 return proof
def ensure_claim(path,maximum,**kwargs):
 if str(Path(path).resolve())not in _tickets:return preclaim(path,maximum,**kwargs)
def alias(source,target):
 source=validate_path(source,exclusive=True);target=validate_path(target,exclusive=True);key=str(source.resolve());other=str(target.resolve());assert key in _tickets and other not in _tickets;_tickets[other]=_tickets[key]
def _consume(path,maximum,**kwargs):
 path=validate_path(path,exclusive=True);key=str(path.resolve())
 if key not in _tickets:preclaim(Path(path),maximum,**kwargs)
 ticket=_tickets[key];assert not ticket['used']and maximum<=ticket['maximum'],'WRITER_TICKET_REPLAY_OR_SIZE';ticket['used']=True;return ticket
class BoundedFile:
 def __init__(self,path,maximum,*,binary=False,**kwargs):
  self.path=Path(path);self.maximum=maximum;self.bytes=0;self.error=None;_consume(self.path,maximum,**kwargs);self.file=self.path.open('xb'if binary else'x');self.binary=binary
 def write(self,value):
  raw=value if isinstance(value,bytes)else value.encode();assert self.bytes+len(raw)<=self.maximum,'NATIVE_SERIALIZED_WRITER_BYTE_BOUND';result=self.file.write(value);self.bytes+=len(raw);return result
 def flush(self):return self.file.flush()
 def fileno(self):return self.file.fileno()
 def tell(self):return self.bytes
 @property
 def closed(self):return self.file.closed
 def close(self):
  if not self.closed:self.file.flush();os.fsync(self.file.fileno());self.file.close()
 def __enter__(self):return self
 def __exit__(self,*unused):self.close()
def write_bytes(path,raw,*,maximum=128*2**10,**kwargs):
 assert isinstance(raw,bytes)and len(raw)<=maximum,'NATIVE_SERIALIZED_FILE_BOUND'
 with BoundedFile(path,maximum,binary=True,**kwargs)as f:f.write(raw)
 return Path(path)
def write_json(path,value,*,maximum=128*2**10,**kwargs):return write_bytes(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode(),maximum=maximum,**kwargs)
def prepare_append(path,*,maximum=512*2**10):
 path=validate_path(path)
 if not path.exists():
  with BoundedFile(path,maximum,binary=True,kind='bounded-append'):pass
 assert path.is_file()and not path.is_symlink()and path.stat().st_size<maximum,'NATIVE_APPEND_FILE_BOUND';return path

def append(path,raw,*,maximum=512*2**10):
 path=prepare_append(path,maximum=maximum);old=path.stat().st_size;assert old+len(raw)<=maximum,'NATIVE_APPEND_BYTE_BOUND'
 with path.open('ab')as f:f.write(raw);f.flush();os.fsync(f.fileno())
class PipeCapture:
 """Retain complete output within cap; overflow is explicit failure and stops owned child."""
 def __init__(self,process,sink):
  self.process=process;self.sink=sink;self.error=None
  def pump():
   try:
    while True:
     chunk=(process.stdout.read1 if hasattr(process.stdout,'read1')else process.stdout.read)(4096)
     if not chunk:break
     sink.write(chunk if sink.binary else chunk.decode('utf-8',errors='replace'));sink.flush()
   except BaseException as e:
    self.error=e
    try:process.terminate()
    except ProcessLookupError:pass
   finally:sink.close()
  self.thread=threading.Thread(target=pump,daemon=True);self.thread.start()
 def check(self):
  if self.error:raise RuntimeError('OWNED_CONSOLE_CAPTURE_FAILED:'+str(self.error))
 def finish(self):self.thread.join(timeout=2);assert not self.thread.is_alive(),'OWNED_CONSOLE_CAPTURE_DRAIN_DEADLINE';self.check()
def load():return quota().load_policy()
def admit(phase,**kwargs):return quota().admit(phase,**kwargs)
class QuotaWatch:
 def __init__(self,*,clock,remaining_ap=4,remaining_hosts=2,closed_runs=(),claim='runtime'):
  self.clock=clock;self.last=None;self.error=None;self.proof=None;self.stopped=threading.Event()
  def check_once():
   self.proof=admit('runtime',remaining_ap=remaining_ap,remaining_hosts=remaining_hosts,closed_runs=list(closed_runs),claim_id=claim,cancel_event=self.stopped);self.last=clock()
  check_once()
  def run():
   while not self.stopped.wait(5):
    try:check_once()
    except BaseException as e:
     if not self.stopped.is_set():self.error=e
     return
  self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
 def check(self):
  if self.error:raise RuntimeError('SHARED_SCOPED_QUOTA_RUNTIME_REFUSED:'+str(self.error))
  assert self.last is not None and 0<=self.clock()-self.last<=load()['scanner']['staleMs']/1000,'SHARED_QUOTA_AUDIT_STALE'
  return {'policySha256':self.proof['policySha256'],'auditAgeS':self.clock()-self.last}
 def close(self):
  self.stopped.set();self.thread.join(timeout=4);assert not self.thread.is_alive(),'QUOTA_AUDIT_OWNED_READER_CLOSURE_UNKNOWN'
