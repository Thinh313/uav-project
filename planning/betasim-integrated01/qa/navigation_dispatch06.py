"""Exact Android source dispatch guard with fake Popen; no process starts."""
from pathlib import Path
import os,sys,types,json,hashlib
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
import aeris_runtime.android as A
from aeris_runtime.metadata_budget import observer_envelope
checks=[];source=Path(A.__file__);pin=hashlib.sha256(source.read_bytes()).hexdigest()
class Store:
 def __init__(self):self.rows=[]
 def command_bytes(self,b):return{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'QA_MEMORY':True}
 def receipt(self,n,q,**kw):self.rows.append(q);return{'QA_RECEIPT':True}
class Budget:
 def tick(self,*a):pass
 def ensure(self,*a):pass
 def failure(self,*a,**kw):pass
def run(name,delay,*,serial='emulator-5582',tag='AERIS_PRODUCT_STATUS',duration='250',deadline=200_001_000,tap=False,admitted=False):
 d=types.SimpleNamespace(adb='QA_NOT_EXECUTED',serial=serial,observer=types.SimpleNamespace(tag=tag),budget=Budget(),io_broker=None,sequence=0,store=Store(),t=1000);d.now=lambda:d.t;d.live_check=lambda:setattr(d,'t',d.t+delay);args=['shell','input','tap','10','10']if tap else['shell','input','swipe','10','10','20','20',duration];old=A.subprocess.Popen;calls=[]
 def fake(*a,**kw):calls.append(a);raise RuntimeError('QA_FAKE_POPEN_ADMISSION_ONLY')
 A.subprocess.Popen=fake
 try:
  try:A.AndroidDevice._command(d,args,deadline_ns=1_000_001_000,maximum_bytes=64,dispatch_deadline_ns=deadline)
  except BaseException as e:
   if admitted:assert str(e)=='QA_FAKE_POPEN_ADMISSION_ONLY'and len(calls)==1
   else:assert not calls and('NAVIGATION_ACTUAL_DISPATCH200MS'in str(e)or'NAVIGATION_DISPATCH_DEADLINE_EXACT_TAP_OR_OWNED250MS_SWIPE'in str(e)),str(e)
   assert d.store.rows[-1]['captureComplete']is False and d.store.rows[-1]['exit']is None
  else:raise AssertionError('UNEXPECTED_COMMAND_SUCCESS')
  checks.append({'id':name,'pass':True,'fakePopenCalls':len(calls)})
 except BaseException as e:checks.append({'id':name,'pass':False,'error':str(e)})
 finally:A.subprocess.Popen=old
run('source-scroll-livecheck201ms-zeroPopen',201_000_000);run('source-scroll199ms-admitted-only-to-fakePopen',199_000_000,admitted=True);run('existing-tap-livecheck201ms-zeroPopen',201_000_000,tap=True);run('non250ms-swipe-refused',0,duration='249');run('physical-serial-refused',0,serial='phone');run('legacy-observer-refused',0,tag='AERIS_MISSION');run('bool-deadline-refused',0,deadline=True)
assert observer_envelope()['owners']['external_task']==1048576
report={'format':'aeris-independent-navigation-physical-dispatch06','version':1,'status':'PASS_SOURCE_GUARD_FAKE_POPEN_NOT_ACTUAL_ANDROID'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'sourceChanged':pin!=hashlib.sha256(source.read_bytes()).hexdigest(),'checks':checks,'actualActorsOrAndroid':False,'positiveIsOnlyFakePopenAdmissionNotExecution':True,'freshness250Lease200AndMetadataEnvelopeUnchanged':True}
n=1
while(out:=R/f'evidence/betasim-integrated01/qa/navigation-dispatch06-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'path':str(out)}))
