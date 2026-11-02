"""Focused H4 mocks only. No SDK/AP/Android actors or candidate creation."""
from pathlib import Path
import ast,gzip,hashlib,importlib.util,json,os,stat,sys,tempfile,time,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime import installclosure_h4 as h,guest_sync_h4 as g,metadata_budget as mb
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_writer import ProductWriter
from aeris_runtime.metadata_budget import MetadataBudget,capture_command
from aeris_runtime.once_reader import read_ref
# Reuse only inert fixture AST. Do not execute old module top-level M101 reads.
fixture_path=R/'planning/betarc01/repair/test-repair01.py';tree=ast.parse(fixture_path.read_text());nc=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='NoChild');rc=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Repair');rc.body=[n for n in rc.body if isinstance(n,ast.FunctionDef)and n.name=='fixture'];C=R/'evidence/nativejournal17/candidates/86bc4cb7e37b77b2b585d7b3a7db08ca01f00a8197c52017ec695c90c86a5aa7';N02=R/'evidence/nativejournal17/n02/sessions/nativejournal17-only02/native-restart-metadata.tar';prior=json.loads((R/'evidence/betarc01/m201/reports/known-state-repair01.json').read_bytes());oldstore=R/'evidence/betarc01/m201/sessions/beta-rc01-known-state-repair01/android-api';_,_,_,raw=__import__('aeris_runtime.status15_reader',fromlist=['command']).command(oldstore,prior['postDumpRef']);raw=h.re.sub(rb'^    pkg=.*$',b'    pkg=null',raw,flags=h.re.M)
ns={'shlex':__import__('shlex'),'ANDROID_READY_SCRIPT':__import__('aeris_runtime.android',fromlist=['ANDROID_READY_SCRIPT']).ANDROID_READY_SCRIPT,'unittest':unittest,'Path':Path,'os':os,'json':json,'threading':__import__('threading'),'subprocess':__import__('subprocess'),'types':types,'C':C,'R':R,'D':B,'N02':N02,'OLD_DUMP':raw,'CODE':h.package_state(raw,broken=True),'PACKAGE':h.PACKAGE,'PRIVATE':h.PRIVATE,'COLD':h.COLD,'STAT':h.STAT,'MetadataBudget':MetadataBudget,'KnownStateRepairDevice':h.PushInstallDeviceH4,'load':h.load};exec(compile(ast.Module(body=[nc,rc],type_ignores=[]),'inert_original_fixture_ast','exec'),ns);f=types.SimpleNamespace(**ns)
class PushNoChild(f.NoChild):
 mode='success';calls=0
 def __init__(self,argv,**kw):
  type(self).calls+=1
  if argv[3:5]!=['install','-r']:return super().__init__(argv,**kw)
  self.pid=os.getpid();self.args=argv;self.returncode=0;self.waits=0;self.installer=True;out=b'Performing Push Install\nSuccess\n';apk=argv[-1];size=Path(apk).stat().st_size;err=(apk+': 1 file pushed, 0 skipped. 12.3 MB/s ('+str(size)+' bytes in 0.012s)\n').encode()
  if self.mode=='warning':err+=b'warning\n'
  if self.mode=='badbytes':err=err.replace(str(size).encode(),str(size+1).encode())
  if self.mode=='nonzero':self.returncode=1
  if self.mode=='partial':out=b'x'*2049
  if self.mode=='grammar':out=b'Success\n'
  for name,data in [('stdout',out),('stderr',err)]:
   r,w=os.pipe();os.write(w,data);os.close(w);setattr(self,name,os.fdopen(r,'rb'))
class SyncNoChild:
 calls=0;body=b''
 def __init__(self,argv,**kw):
  type(self).calls+=1;self.pid=os.getpid();self.returncode=0;self.args=argv
  for name,data in [('stdout',self.body),('stderr',b'')]:
   r,w=os.pipe();os.write(w,data);os.close(w);setattr(self,name,os.fdopen(r,'rb'))
 def poll(self):return self.returncode
 def wait(self,timeout=None):return self.returncode
class H4(unittest.TestCase):
 def tearDown(self):
  for t in f.NoChild.threads:t.join(timeout=2)
  self.assertTrue(all(not t.is_alive()for t in f.NoChild.threads));f.NoChild.threads=[];PushNoChild.mode='success';SyncNoChild.body=b''
 def fixture(self,tmp):
  owner,d,pre=f.Repair().fixture(tmp)
  # Use H4 authorization and PRIMARY N02 verifier, not the old M101 join.
  ref=h.authorize_repair(owner,d,pre);a=h.verify_authorization(d.root,ref);owner.write('repair-dispatch-intent01.json',{'authorizationRef':ref,'candidateSHA256':owner.digest,'APKPath':str(f.C/'native.apk'),'RootIntentSHA256':pre['RootIntentSHA256'],'attempt':1,'consumedBeforeSend':True,'preparedHostNs':d.now(),'automaticRetry':False});return owner,d,ref
 def test_actual_push11_auth_capture_progress_and_once(self):
  with tempfile.TemporaryDirectory(prefix='h4-push-mock-',dir=B)as tmp,patch('aeris_runtime.android.subprocess.Popen',PushNoChild):
   owner,d,ref=self.fixture(tmp);n=PushNoChild.calls;result=d.install_push_once(f.C/'native.apk',ref,deadline_ns=d.now()+70_000_000_000);row=h.verify_push_install(d.root,result,ref,str(f.C/'native.apk'));self.assertEqual(row['version'],11);self.assertEqual(row['failure'],'RuntimeError:ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE');self.assertEqual(PushNoChild.calls,n+1);argv=json.loads(read_ref(d.root,row['argvRef']));self.assertEqual(argv[3:7],['install','-r','--no-streaming','--no-incremental'])
   with self.assertRaises(ValueError):d.install_push_once(f.C/'native.apk',ref,deadline_ns=d.now()+70_000_000_000)
 def test_push_not_arbitrary_stderr_or_suffix_and_failure_no_resend(self):
  for mode in['warning','badbytes','nonzero','partial','grammar','timeout']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='h4-push-mock-',dir=B)as tmp,patch('aeris_runtime.android.subprocess.Popen',PushNoChild):
    owner,d,ref=self.fixture(tmp);PushNoChild.mode=mode;n=PushNoChild.calls
    with self.assertRaises(Exception):d.install_push_once(f.C/'native.apk',ref,deadline_ns=d.now()+70_000_000_000)
    self.assertEqual(PushNoChild.calls,n+1);self.assertEqual(d.last_command['version'],11);self.assertEqual(d.last_command['authorizationRef'],ref);self.assertFalse(d.repair_dispatch_active)
    with self.assertRaises(ValueError):d.install_push_once(f.C/'native.apk',ref,deadline_ns=d.now()+70_000_000_000)
    PushNoChild.mode='success'
 def test_callback_fault_inside_capture_preserves_available_prefix(self):
  checks=[]
  def check():
   checks.append(1)
   if len(checks)==2:raise RuntimeError('HEALTH_FAILURE_DURING_CAPTURE')
  SyncNoChild.body=b'prefix';r=capture_command(None,'guardian',['/mock/adb','-s','emulator-5582','shell','sync'],deadline_ns=time.monotonic_ns()+2_000_000_000,stdout_limit=64,stderr_limit=128,spawn=SyncNoChild,check_live=check);self.assertFalse(r['captureComplete']);self.assertEqual(r['stdout'],b'prefix');self.assertIn('HEALTH_FAILURE_DURING_CAPTURE',str(r['failure']))
  n=SyncNoChild.calls
  with self.assertRaisesRegex(RuntimeError,'PRESPAWN'):capture_command(None,'guardian',['/mock'],deadline_ns=time.monotonic_ns()+2_000_000_000,spawn=SyncNoChild,check_live=lambda:(_ for _ in()).throw(RuntimeError('PRESPAWN')))
  self.assertEqual(n,SyncNoChild.calls)
 def test_actual_guardian_sync_receipt_and_health_checks(self):
  with tempfile.TemporaryDirectory(prefix='h4-sync-mock-',dir=B)as tmp:
   root=Path(tmp)/'m301';root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);b.admit();checks=[]
   def capture(*args,**kw):return capture_command(*args,**kw,spawn=SyncNoChild)
   with patch.object(g,'capture_command',capture):v=g.guardian_sync('/mock/adb',b,root/'guardian',lambda:checks.append(1))
   self.assertEqual(v['argv'][-2:],['shell','sync']);self.assertTrue(v['captureComplete']);self.assertIsNone(v['failure']);self.assertGreaterEqual(len(checks),3);self.assertLessEqual(v['finishedHostNs']-v['startedHostNs'],2_000_000_000)
   SyncNoChild.body=b'not empty'
   with patch.object(g,'capture_command',capture),self.assertRaisesRegex(RuntimeError,'EMPTY_SUCCESS'):g.guardian_sync('/mock/adb',b,root/'guardian-failed',lambda:None)
   self.assertEqual(json.loads((root/'guardian-failed/guest-sync-h4.json').read_bytes())['status'],'UNKNOWN_BARRIER_NOT_ACCEPTANCE')
 def test_sdk_normal_closure_sync_order_and_crash_rejection(self):
  import aeris_runtime.emulator as em
  tree=ast.parse((B/'source/aeris_runtime/emulator.py').read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run');final=next(n.finalbody for n in ast.walk(run)if isinstance(n,ast.Try)and any(isinstance(c,ast.FunctionDef)and c.name=='stop_emulator'for c in n.finalbody));fn=next(n for n in final if isinstance(n,ast.FunctionDef)and n.name=='stop_emulator');ns=dict(em.__dict__);ns.update(health=None,FAILED_DISPOSAL=False,child=types.SimpleNamespace(poll=lambda:-11,returncode=-11));exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_H4_sdk_stop','exec'),ns)
  with self.assertRaisesRegex(RuntimeError,'SDK_EXIT_NONZERO_NOT_NORMAL_CLOSURE'):ns['stop_emulator']()
  text=(B/'source/aeris_runtime/emulator.py').read_text();self.assertLess(text.index("ops.append(('guarded-guest-sync-before-sdk-stop'"),text.index("ops.append(('health-endpoint-drain-before-managed-closing'"));self.assertIn('primary is None and not FAILED_DISPOSAL',text)
 def test_primary_originals_only_and_protected_h3_modes_bytes(self):
  self.assertEqual(h.original_private_table(R),h.private_table(f.N02));source=(B/'source/aeris_runtime/installclosure_h4.py').read_text();self.assertNotIn("repository()/'evidence/betarc01/m101",source);self.assertNotIn("repo)/'evidence/betarc01/m101",source)
  baseline=json.loads(gzip.decompress((B/'H3-DERIVATION-BASELINE.json.gz').read_bytes()))
  for n,row in baseline['files'].items():
   p=R/row['oldPath'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256']);self.assertEqual(stat.S_IMODE(p.stat().st_mode),row['mode']);self.assertEqual(p.stat().st_ino,row['inode'])
  from aeris_runtime.mission16 import SLOTS
  for n in['m301','m302','g103','m303']:self.assertEqual(SLOTS[n],180)
  self.assertEqual(mb.observer_envelope()['totalFutureBytes'],60686336);self.assertEqual(len(mb.OWNERS),14);self.assertEqual(mb.CAP,66*2**20)
 def test_actual_h4_sdk_entries_start_writer_before_first_readiness(self):
  fixture=R/'planning/betarc01/runtime/test-writer-order02.py';sp=importlib.util.spec_from_file_location('h4_order_fixture',fixture);q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q);self.assertIs(q.WorkbenchRuntime,WorkbenchRuntime)
  for name in['root-install-h4.py','root-qualify-h4.py']:
   t=ast.parse((B/name).read_text());main=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=next(n.body for n in main.body if isinstance(n,ast.Try));prefix=[]
   for n in body:
    prefix.append(n);call=n.value if isinstance(n,(ast.Expr,ast.Assign))else None
    if isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute)and call.func.attr=='wait_owned_ready':break
   else:raise AssertionError('SDK_ENTRY_ORDER_SHAPE')
   def execute(nodes):
    owner,events,_=q.Ordering().fixture();d=owner.case['device'];d.adb='/mock/adb';d.root=Path('/mock/empty');d.sequence=0;d.bind=lambda p:None;d.bind_current_path=lambda p:None;env={'owner':owner,'intent':{'run':'mock17'},'need':h.need,'PushInstallDeviceH4':lambda *a,**kw:d,'ColdBootDeviceH4':lambda *a,**kw:d,'known_path':f.CODE,'path':f.CODE,'check':owner.check,'time':time};exec(compile(ast.Module(body=nodes,type_ignores=[]),name,'exec'),env);return events
   events=execute(prefix);self.assertLess(events.index('host-writer-start'),events.index('wait-owned-ready-mock-no-adb'))
   old=[n for n in prefix if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='start_writer')]
   with self.assertRaisesRegex(ValueError,'NOT_STARTED_OR_CLOSED'):execute(old)
 def test_source_held_g103_requires_prior_same_release_cold_gate(self):
  with tempfile.TemporaryDirectory(prefix='h4-proof-mock-',dir=B)as tmp:
   # Scope fails closed before any receipt can invent freshboot acceptance.
   p=Path(tmp)/'missing-proof.json'
   with self.assertRaises(ValueError):h.require_qualification(p,'a'*64,'b'*64)
  text=(B/'root-native-h4.py').read_text();self.assertIn("choices=('g103',)",text);self.assertLess(text.index('qualification=require_qualification'),text.index('owner=WorkbenchRuntime('));self.assertIn("owner.start_writer()",(B/'root-install-h4.py').read_text());self.assertIn("owner.start_writer()",(B/'root-qualify-h4.py').read_text())
if __name__=='__main__':
 run=unittest.main(verbosity=2,exit=False);origins={n:{'path':str(Path(v.__file__).resolve()),'sha256':hashlib.sha256(Path(v.__file__).read_bytes()).hexdigest()}for n,v in sys.modules.items()if n.startswith('aeris_runtime')and getattr(v,'__file__',None)};assert all(Path(v['path']).is_relative_to(B/'source')for v in origins.values());print(json.dumps({'format':'aeris-h4-actual-mock-module-origins','status':'ACTIVE_H4_SOURCE_ONLY_NOT_FROZEN_RELEASE_ACCEPTANCE','modules':origins,'actorsStarted':False},sort_keys=True));raise SystemExit(0 if run.result.wasSuccessful()else 1)
