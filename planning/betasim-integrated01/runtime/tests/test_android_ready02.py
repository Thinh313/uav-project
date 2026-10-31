"""Actual original capture code over fake ADB pipes; no Android/QEMU/AP actor."""
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import hashlib,json,os,shutil,sys,time
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)];os.environ['AERIS_REPOSITORY_ROOT']=str(REPO)
from aeris_runtime.android import AndroidDevice,ANDROID_READY_SCRIPT
from aeris_runtime.metadata_budget import MetadataBudget,encoded,CLOSING_OWNERS
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_native import ProductNativeProbe
from aeris_runtime.once_reader import read_ref
from aeris_runtime.candidate import load
LAB=REPO/'evidence/betasim-integrated01/runtime/.ready02-mock'
class Peer:
 def __init__(self,replies):self.replies=list(replies);self.argv=[]
 def __call__(self,argv,**kwargs):
  self.argv.append(argv);out,err,code=self.replies.pop(0)
  streams=[]
  for raw in(out,err):
   read,write=os.pipe();os.write(write,raw);os.close(write);streams.append(os.fdopen(read,'rb',buffering=0))
  return SimpleNamespace(stdout=streams[0],stderr=streams[1],returncode=code,poll=lambda:code,wait=lambda **k:code,terminate=lambda:None,kill=lambda:None)
def denied(fn,phrase):
 try:fn()
 except BaseException as e:
  assert phrase in str(e),(phrase,type(e).__name__,str(e));return e
 raise AssertionError('not denied '+phrase)
def make(name,serial='emulator-5582'):
 root=LAB/name;root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();d=AndroidDevice('/mock/adb',serial,root/'sessions/test/android-api',budget=b,observer_tag='AERIS_PRODUCT_STATUS');return root,b,d
checks=[]
def main():
 assert not LAB.exists();LAB.mkdir(parents=True)
 try:
  root,b,d=make('normal');peer=Peer([(b'',b'',0),(b'BOOT:\nBOOT:0\nBOOT:1\nPM:package:/system/framework/framework-res.apk\nANDROID_READY\n',b'',0),(b'0\n',b'',0),(b'0\n',b'',0)]);live=[];d.live_check=lambda:live.append(d.sequence)
  with patch('aeris_runtime.android.subprocess.Popen',peer):
   ready=d.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);d.prepare_content_reader(deadline_ns=time.monotonic_ns()+10**9)
  row=json.loads(read_ref(d.root,ready));assert row['bootObservations']==3 and row['APStarted']is False and peer.argv[0][-1]=='wait-for-device' and 'getprop sys.boot_completed'in peer.argv[1][-1] and all('id -u'in x[-1]for x in peer.argv[2:])and len(live)>=12;assert read_ref(d.root,row['bootAndPackageManagerCommandRef']);assert d.sequence==4;checks.append('original-pipe-ready-then-id-once-genuine-refs-and-live-guard-through-wait')
  with patch('aeris_runtime.android.subprocess.Popen',peer):denied(lambda:d.wait_owned_ready(deadline_ns=time.monotonic_ns()+10**9),'FIRST_ONCE')
  checks.append('ready-no-repeat-enrollment')
  for name,reply,phrase in [('notfound',(b'',b"adb: device 'emulator-5582' not found\n",1),'ANDROID_COMMAND_EXIT:1'),('timeout',(b'BOOT:0\n',b'',21),'ANDROID_COMMAND_EXIT:21'),('pm',(b'BOOT:1\nPM:\n',b'',22),'ANDROID_COMMAND_EXIT:22'),('forged',(b'BOOT:0\nPM:package:/system/x\nANDROID_READY\n',b'',0),'ORIGINAL_ANDROID_BOOT')]:
   root,b,d=make(name);p=Peer([reply]if name=='notfound'else[(b'',b'',0),reply])
   with patch('aeris_runtime.android.subprocess.Popen',p):
    denied(lambda:d.wait_owned_ready(deadline_ns=time.monotonic_ns()+10**9),phrase)
    denied(lambda:d.prepare_content_reader(deadline_ns=time.monotonic_ns()+10**9),'GENUINE_ANDROID_READY')
   assert d._android_ready is None and not p.replies and not any('id -u'in v[-1]or'install'in v for v in p.argv);assert d.last_command_ref and read_ref(d.root,d.last_command_ref);checks.append(name+'-original-failure-preserved-no-root-install-AP-or-retry')
  root,b,d=make('guard');p=Peer([(b'',b'',0)]);count=[0]
  def guard():
   count[0]+=1
   if count[0]==3:raise RuntimeError('GUARDIAN_POWER_OR_DISK_FAILURE')
  d.live_check=guard
  with patch('aeris_runtime.android.subprocess.Popen',p):denied(lambda:d.wait_owned_ready(deadline_ns=time.monotonic_ns()+10**9),'GUARDIAN_POWER_OR_DISK_FAILURE')
  assert len(p.argv)==1 and d._android_ready is None and d.last_command_ref;checks.append('guard-fails-during-pipewait-capture-cleanup-no-following-shell')
  root,b,d=make('late-tap');now=[1_000_000_000];d.now=lambda:now[0];p=Peer([]);checks_seen=[0]
  def slow_guard():
   checks_seen[0]+=1
   if checks_seen[0]==2:now[0]+=201_000_000
  d.live_check=slow_guard
  with patch('aeris_runtime.android.subprocess.Popen',p):denied(lambda:d.command(['shell','input','tap','100','100'],deadline_ns=2_000_000_000,dispatch_deadline_ns=1_200_000_000,maximum_bytes=64),'NAVIGATION_ACTUAL_DISPATCH200MS')
  assert not p.argv and d.last_command_ref;checks.append('guard201ms-delay-rechecked-before-UI-tap-dispatch-zeroTX')
  root,b,d=make('foreign',serial='emulator-5554');p=Peer([])
  with patch('aeris_runtime.android.subprocess.Popen',p):denied(lambda:d.wait_owned_ready(deadline_ns=time.monotonic_ns()+10**9),'FIRST_ONCE')
  assert not p.argv;checks.append('foreignserial-zero-dispatch')
  root,b,d=make('terminal');owner=WorkbenchRuntime.__new__(WorkbenchRuntime);owner.root=root;owner.budget=b;owner.digest='a'*64;owner.case=None;owner.closed=False;
  with b._locked():
   state=b._state();state['remaining']['external_task']=0;b._save(state)
  owner.close_guardian=lambda **k:(_ for _ in()).throw(RuntimeError('GUARDIAN_CLOSE_FAILED'));primary=RuntimeError('PRIMARY_BOOT_FAILURE');trace='Traceback original fixture\nRuntimeError: PRIMARY_BOOT_FAILURE\n';trace_ref=owner.persist_owner_error(trace);result=owner.fail_case(primary);terminal=json.loads((root/'reports/owner-terminal.json').read_bytes());assert (root/'reports/owner-error.txt').read_bytes()==trace.encode()and terminal['ownerErrorRef']==trace_ref and trace_ref['captureComplete']is True;assert terminal['primaryFailure']=='PRIMARY_BOOT_FAILURE' and terminal['secondaryErrors'][0]['step']=='guardian-exceptional-disposal' and terminal['APGroundProven']is False and terminal['flightAcceptance']is False and terminal['normalCompletedClosureClaimed']is False and b.snapshot()['closingOwners']['closure']<CLOSING_OWNERS['closure'];denied(lambda:owner.write('other.json',{},closing=True),'ONLY_OWNER_TERMINAL');denied(lambda:owner.write('owner-terminal.json',{'huge':'x'*4096},closing=True),'REPORT_SOURCE_BOUND');denied(lambda:b.write('closure',root/'reports/owner-error.txt',b'x'*16385,closing=True),'SOURCE_OWNER_TERMINAL_OR_TRACE_EXACT_BOUND');checks.append('FAILED-primary-original-trace-and-secondary-durable-via-original-closure-reserve-only-exact4KiB-path')
  old=REPO/'evidence/betasim-integrated01/candidates/924d3c6e658f1a89243827f578c9f7d25d1cab79439585a5df843c2a1412b6b4';load(old,old.name);checks.append('old924d-full-transitive-load-unchanged-after-active-repair')
  report={'format':'aeris-ready02-causal-mock','status':'PASS_SOURCE_MOCK_NOT_ANDROID_READY_OR_BETA_ACCEPTANCE','checks':checks,'groups':len(checks),'guardsChanged':False,'actorsStarted':False,'oldCandidate924dStillValid':True,'readinessScriptSHA256':hashlib.sha256(ANDROID_READY_SCRIPT.encode()).hexdigest(),'scratchRemoved':str(LAB.relative_to(REPO))}
 finally:shutil.rmtree(LAB)
 path=REPO/'evidence/betasim-integrated01/runtime/ready02-causal-mock04.json';assert not path.exists();path.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
