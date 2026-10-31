"""Real Android command capture code, fake OS ADB pipes, no actor."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json,os,shutil,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.android import AndroidDevice
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.once_reader import read_ref
LAB=R/'evidence/betasim-integrated01/runtime/.scroll06';SWIPE=['shell','input','swipe','100','200','100','400','250']
class Peer:
 def __init__(self):self.argv=[]
 def __call__(self,argv,**kw):
  self.argv.append(argv);streams=[]
  for raw in(b'',b''):
   a,b=os.pipe();os.write(b,raw);os.close(b);streams.append(os.fdopen(a,'rb',buffering=0))
  return SimpleNamespace(stdout=streams[0],stderr=streams[1],returncode=0,poll=lambda:0,wait=lambda **k:0,terminate=lambda:None,kill=lambda:None)
def fixture(name,serial='emulator-5582',tag='AERIS_PRODUCT_STATUS'):
 root=LAB/name;root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();now=[1_000_000_000];d=AndroidDevice('/mock/adb',serial,root/'sessions/mock/android-api',budget=b,observer_tag=tag,now=lambda:now[0]);return d,now,Peer()
def deny(fn,part):
 try:fn()
 except(ValueError,TimeoutError)as e:
  assert part in str(e),str(e);return
 raise AssertionError('not denied')
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);groups=[]
 try:
  d,now,p=fixture('late');calls=[0]
  def guard():
   calls[0]+=1
   if calls[0]==2:now[0]+=201_000_000
  d.live_check=guard
  with patch('aeris_runtime.android.subprocess.Popen',p):deny(lambda:d.command(SWIPE,deadline_ns=3_000_000_000,maximum_bytes=64,dispatch_deadline_ns=1_200_000_000),'NAVIGATION_ACTUAL_DISPATCH200MS')
  assert not p.argv;row=json.loads(read_ref(d.root,d.last_command_ref));assert row['captureComplete']is False and row['exit']is None and row['failure'].endswith('NAVIGATION_ACTUAL_DISPATCH200MS');groups.append('201ms-liveguard-delay-after-fresh-observation-zeroPopen-original-failed-command-receipt')
  d,now,p=fixture('within');calls=[0]
  def guard():
   calls[0]+=1
   if calls[0]==2:now[0]+=199_000_000
  d.live_check=guard
  with patch('aeris_runtime.android.subprocess.Popen',p):d.command(SWIPE,deadline_ns=3_000_000_000,maximum_bytes=64,dispatch_deadline_ns=1_200_000_000)
  assert len(p.argv)==1;row=json.loads(read_ref(d.root,d.last_command_ref));assert row['startedHostNs']==1_199_000_000 and row['captureComplete']is True;groups.append('exactowned250ms-swipe-under200-prePopen-bound-original-capture-positive')
  cases=[('duration',SWIPE[:-1]+['200'],'emulator-5582','AERIS_PRODUCT_STATUS','UNDECLARED_ANDROID_COMMAND_WRITER'),('coords',SWIPE[:3]+['10000',*SWIPE[4:]],'emulator-5582','AERIS_PRODUCT_STATUS','UNDECLARED_ANDROID_COMMAND_WRITER'),('foreign',SWIPE,'emulator-5554','AERIS_PRODUCT_STATUS','NAVIGATION_DISPATCH_DEADLINE_EXACT'),('legacy',SWIPE,'emulator-5582','AERIS_MISSION','UNDECLARED_ANDROID_COMMAND_WRITER')]
  for name,args,serial,tag,part in cases:
   d,now,p=fixture(name,serial,tag)
   with patch('aeris_runtime.android.subprocess.Popen',p):deny(lambda:d.command(args,deadline_ns=3_000_000_000,maximum_bytes=64,dispatch_deadline_ns=1_200_000_000),part)
   assert not p.argv
  groups.append('wrong-duration-coordinate-unownedserial-legacytag-never-broadened-allowlist')
  d,now,p=fixture('legacy-tap');calls=[0]
  def guard():
   calls[0]+=1
   if calls[0]==2:now[0]+=201_000_000
  d.live_check=guard
  with patch('aeris_runtime.android.subprocess.Popen',p):deny(lambda:d.command(['shell','input','tap','100','200'],deadline_ns=3_000_000_000,maximum_bytes=64,dispatch_deadline_ns=1_200_000_000),'NAVIGATION_ACTUAL_DISPATCH200MS')
  assert not p.argv;groups.append('existing-tap201ms-final-guard-retained-unchanged')
  d,now,p=fixture('bool')
  with patch('aeris_runtime.android.subprocess.Popen',p):deny(lambda:d.command(SWIPE,deadline_ns=3_000_000_000,maximum_bytes=64,dispatch_deadline_ns=True),'NAVIGATION_DISPATCH_DEADLINE_EXACT')
  assert not p.argv;groups.append('typeddeadline-rejects-bool-beforePopen')
  report={'format':'aeris-ui-scroll-prePopen-dispatch-causal-mock','status':'PASS_REAL_SOURCE_CAPTURE_FAKE_ADB_PIPES_NOT_ANDROID_MOTION','groups':groups,'newAllowedAction':False,'dispatchBoundMs':200,'gestureDurationMs':250,'scope':'ORIGINAL_UI_AGE_TO_ROOT_PRE_POPEN_NOT_PHYSICAL_MOTION_TIME','actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))}
 finally:shutil.rmtree(LAB)
 p=R/'evidence/betasim-integrated01/runtime/scroll-dispatch-mock06-final.json';assert not p.exists();p.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
