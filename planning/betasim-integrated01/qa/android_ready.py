"""Independent actor-free Android OS-readiness/order and late-health dispatch fixtures."""
from pathlib import Path
import sys,os,json,hashlib,types
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
import aeris_runtime.android as A
from aeris_runtime.product_native import ProductNativeProbe
checks=[];pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[R/'planning/betasim-integrated01/runtime/root-owner-ready02.py',Path(A.__file__),R/'planning/betasim-integrated01/runtime/source/aeris_runtime/product_native.py',R/'planning/betasim-integrated01/runtime/source/aeris_runtime/product_runtime.py']}
class Store:
 def __init__(self):self.rows=[]
 def receipt(self,n,q,**kw):self.rows.append((n,q));return{'path':n,'qaMemory':True,'sha256':hashlib.sha256(json.dumps(q,sort_keys=True).encode()).hexdigest()}
 def command_bytes(self,b):return{'qaMemory':True,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
class Budget:
 def tick(self,*a):pass
 def ensure(self,*a):pass
 def failure(self,*a,**kw):pass
class Device:
 def __init__(self,output=b'BOOT:\nBOOT:0\nBOOT:1\nPM:package:/system/framework/framework-res.apk\nANDROID_READY\n',fail=None):
  self.serial='emulator-5582';self.observer=types.SimpleNamespace(tag='AERIS_PRODUCT_STATUS',process=None);self._android_ready=None;self.sequence=0;self.t=1000;self.now=lambda:self.t;self.calls=[];self.store=Store();self.output=output;self.fail=fail;self.last_command_ref=None;self._check_budget_actor=lambda:None
 def command(self,args,**kw):
  self.calls.append(args);self.sequence+=1;self.t+=1000;self.last_command_ref={'originalMockCommandSequence':self.sequence}
  if self.fail==self.sequence:raise RuntimeError('ORIGINAL_COMMAND_FAILURE_NO_RETRY')
  return b''if self.sequence==1 else self.output
 def ready(self):return A.AndroidDevice.wait_owned_ready(self,deadline_ns=60_000_000_000)
def test(name,fn):
 try:fn();checks.append({'id':name,'pass':True})
 except BaseException as e:checks.append({'id':name,'pass':False,'error':type(e).__name__+':'+str(e)})
def refuse(fn,code):
 try:fn()
 except BaseException as e:
  assert code in str(e),(code,str(e));return
 raise AssertionError('UNEXPECTED_ACCEPTANCE:'+code)
def good():
 d=Device();ref=d.ready();assert d.calls==[['wait-for-device'],['shell','sh','-c',A.ANDROID_READY_SCRIPT]];assert ref==d._android_ready;row=d.store.rows[-1][1];assert row['APKInstalled']is False and row['APStarted']is False and row['flightAcceptance']is False and row['bootObservations']==3;assert row['transportCommandRef']!=row['bootAndPackageManagerCommandRef']
test('one-transport-wait-then-original-boot-and-PM-before-privilege',good)
for name,b in [('no-boot-one',b'BOOT:0\nPM:package:/x\nANDROID_READY\n'),('nonabsolute-PM',b'BOOT:1\nPM:package:x\nANDROID_READY\n'),('duplicate-PM',b'BOOT:1\nPM:package:/x\nPM:package:/x\nANDROID_READY\n'),('boot-one-before-last',b'BOOT:1\nBOOT:1\nPM:package:/x\nANDROID_READY\n'),('noise',b'NOISE\nBOOT:1\nPM:package:/x\nANDROID_READY\n'),('too-many-polls',(b'BOOT:0\n'*120)+b'BOOT:1\nPM:package:/x\nANDROID_READY\n')]:
 test(name,lambda b=b:refuse(Device(b).ready,'ORIGINAL_ANDROID_BOOT_AND_PM_READINESS_REQUIRED'))
def failed_first():
 d=Device(fail=1);refuse(d.ready,'ORIGINAL_COMMAND_FAILURE_NO_RETRY');assert len(d.calls)==1 and d._android_ready is None and not d.store.rows
test('failed-original-transport-never-retried-or-promoted',failed_first)
def no_ready():
 d=Device();refuse(lambda:A.AndroidDevice.prepare_content_reader(d,deadline_ns=1000),'GENUINE_ANDROID_READY_BEFORE_CONTENT_PREPARATION');p=object.__new__(ProductNativeProbe);p.device=d;refuse(lambda:p.install_selected(Path('/NOT_READ'), '0'*64,deadline_ns=1000),'GENUINE_ANDROID_READY_BEFORE_INSTALL');assert not d.calls
test('root-content-and-install-both-refuse-without-ready',no_ready)
def once():
 d=Device();d.ready();refuse(d.ready,'OWNED_ANDROID_READINESS_FIRST_ONCE');assert len(d.calls)==2
test('readiness-not-cached-reused-or-repeated',once)
def wrong_serial():
 d=Device();d.serial='physical-phone';refuse(d.ready,'OWNED_ANDROID_READINESS_FIRST_ONCE');assert not d.calls
test('physical-phone-cannot-use-owned-emulator-preparation',wrong_serial)
def delayed_dispatch(delay,dispatch,expected):
 d=Device();d.adb='QA_NO_EXEC';d.budget=Budget();d.io_broker=None;d.live_check=lambda:setattr(d,'t',d.t+delay);popen=A.subprocess.Popen;calls=[]
 def forbidden(*a,**kw):calls.append(a);raise AssertionError('QA_NO_PROCESS_ALLOWED')
 A.subprocess.Popen=forbidden
 try:
  refuse(lambda:A.AndroidDevice._command(d,['shell','input','tap','10','10'],deadline_ns=1_000_001_000,maximum_bytes=64,dispatch_deadline_ns=dispatch),expected);assert not calls;assert d.store.rows[-1][1]['captureComplete']is False;assert d.store.rows[-1][1]['exit']is None
 finally:A.subprocess.Popen=popen
test('health-call-aging201ms-refuses-before-Popen',lambda:delayed_dispatch(201_000_000,200_001_000,'NAVIGATION_ACTUAL_DISPATCH200MS'))
test('health-call-exceeding-command-deadline-refuses-before-Popen',lambda:delayed_dispatch(1_000_000_000,2_000_001_000,'ANDROID_COMMAND_DEADLINE'))
entry=(R/'planning/betasim-integrated01/runtime/root-owner-ready02.py').read_text();test('actual-source-entry-readiness-precedes-root-and-install',lambda: (None if entry.index('wait_owned_ready(')<entry.index('prepare_content_reader(')<entry.index('install_selected(')else (_ for _ in()).throw(AssertionError('SOURCE_ORDER'))))
report={'format':'aeris-independent-owned-android-readiness','version':1,'status':'PASS_ACTOR_FREE_ORIGINAL_METHOD_FIXTURE_NOT_ANDROID_BOOT'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourcePins':pins,'checks':checks,'actualProcessADBEmulatorOrAP':False,'mockOriginalReferences':'MEMORY_EXPLICIT_NOT_GENUINE_ANDROID','sourceChanged':any(hashlib.sha256((R/p).read_bytes()).hexdigest()!=h for p,h in pins.items())}
n=1
while (out:=R/f'evidence/betasim-integrated01/qa/android-ready-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'path':str(out)}))
