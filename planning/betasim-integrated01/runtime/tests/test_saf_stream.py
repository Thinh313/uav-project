"""Actual OS byte pipes through scoped source reader; no ADB/Android child."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,os,shutil,sys,time
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime import saf_stream as m
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.once_store import OnceStore
LAB=REPO/'evidence/betasim-integrated01/runtime/.safpipe'
class Pipes:
 def __init__(self,raw,error=b''):
  self.pid=1234;self.exit=0;self.stdout,self.wout=self.pipe(raw);self.stderr,self.werr=self.pipe(error)
 def pipe(self,raw):
  a,b=os.pipe();os.write(b,raw);os.close(b);return os.fdopen(a,'rb',buffering=0),None
 def poll(self):return self.exit
 def wait(self,timeout=None):return self.exit
 def terminate(self):self.exit=-15
 def kill(self):self.exit=-9

def device(name):
 p=LAB/name;p.mkdir();budget=MetadataBudget(p/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);budget.admit();d=SimpleNamespace(serial='emulator-5582',adb='/owned/mock/adb',sequence=0,budget=budget,now=time.monotonic_ns,_check_budget_actor=lambda:None);d.store=OnceStore(p/'sessions/mock/android-api',budget=budget);return d

def cap(d,raw):return m.SafDocument(m._TOKEN,d,{'documentUri':'content://com.android.externalstorage.documents/document/primary%3Atest','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'manifestSHA256':'a'*64,'stream':'bundle','index':0},{'path':'genuine-native-success-reference'})
def denied(f):
 try:f()
 except(ValueError,OSError,RuntimeError):return
 raise AssertionError('not refused')
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  raw=b'original-SAF-bytes'*100;d=device('valid');p=Pipes(raw)
  with patch.object(m.subprocess,'Popen',return_value=p):
   with m.open_document(d,cap(d,raw),deadline_ns=time.monotonic_ns()+2_000_000_000)as r:
    output=b''
    while b:=r.read(67):output+=b
   assert output==raw and r.closed and p.stdout.closed and p.stderr.closed
  assert d.budget.snapshot()['counters']['commands']==1;checks.append('actual-OS-pipe-source-bytes-streamed-SHA-EOF-no-host-archive-copy')
  for name,out,err in [('truncated',raw[:-1],b''),('extra',raw+b'x',b''),('sha',b'x'+raw[1:],b''),('stderr',raw,b'error')]:
   d=device(name);p=Pipes(out,err)
   def attempt():
    with patch.object(m.subprocess,'Popen',return_value=p):
     with m.open_document(d,cap(d,raw),deadline_ns=time.monotonic_ns()+2_000_000_000)as r:
      while r.read(64):pass
   denied(attempt);assert p.stdout.closed and p.stderr.closed;checks.append(name+'-retains-failure-no-success-no-retry')
  d=device('partial');p=Pipes(raw)
  def partial():
   with patch.object(m.subprocess,'Popen',return_value=p):
    with m.open_document(d,cap(d,raw),deadline_ns=time.monotonic_ns()+2_000_000_000)as r:r.read(1)
  denied(partial);assert p.stdout.closed and p.stderr.closed;checks.append('consumer-early-exit-not-success-and-bounded-cleanup')
  d=device('constructor');p=Pipes(raw);original=m.os.set_blocking
  def bad(fd,value):raise OSError(5,'injected registration failure')
  with patch.object(m.subprocess,'Popen',return_value=p),patch.object(m.os,'set_blocking',side_effect=bad):denied(lambda:m.Reader(d,cap(d,raw),time.monotonic_ns()+2_000_000_000,lambda:None))
  assert p.stdout.closed and p.stderr.closed;checks.append('constructor-fault-closes-owned-pipes-before-yield')
  report={'status':'PASS_OS_PIPE_MOCK_NOT_ANDROID_SAF','groups':checks,'actualADB':False,'sourceAuthority':'capability factory genuine source validation separately required'}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/saf-stream-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
if __name__=='__main__':main()
