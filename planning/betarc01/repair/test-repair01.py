"""Mock only: real frozen authorization/load/budget/capture, no Android actors."""
from pathlib import Path
import copy,importlib.util,json,os,shlex,subprocess,sys,tempfile,threading,time,types,unittest
from unittest.mock import patch
D=Path(__file__).resolve().parent;R=D.parents[2];C=R/'evidence/nativejournal17/candidates/86bc4cb7e37b77b2b585d7b3a7db08ca01f00a8197c52017ec695c90c86a5aa7';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(C/'source'),str(R)]
from planning.betarc01.repair.repair_device01 import *
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_writer import ProductWriter
from aeris_runtime.android import ANDROID_READY_SCRIPT
class NoChild:
 mode='success';threads=[];install_calls=0
 def __init__(self,argv,**kw):
  self.pid=os.getpid();self.args=argv;self.returncode=0;self.waits=0;self.installer=argv[3:5]==['install','-r'];remote=shlex.split(argv[4])if len(argv)==5 and argv[3]=='shell'else argv[3:];out=b'';err=b''
  if self.installer:
   type(self).install_calls+=1;out=b'Performing Streamed Install\nSuccess\n'
   if self.mode=='nonzero':self.returncode=1;out=b'Failure [INSTALL_FAILED_TEST]\n'
   if self.mode=='stderr':err=b'warning\n'
   if self.mode=='partial':out=b'x'*2049
   if self.mode=='grammar':out=b'OK\n'
  elif remote==['id','-u']:out=b'0\n'
  elif remote==['cat','/proc/sys/kernel/random/boot_id']:out=b'11111111-2222-3333-4444-555555555555\n'
  elif remote==['sh','-c',ANDROID_READY_SCRIPT]:out=b'BOOT:1\nPM:package:/system/framework/framework-res.apk\nANDROID_READY\n'
  elif remote==['am','get-current-user']:out=b'0\n'
  elif remote==['sh','-c',COLD]:out=b'ABSENT\n'
  elif remote==['sh','-c',STAT]:out=b'directory 10141 10141 123585\n'
  elif remote==['dumpsys','package',PACKAGE]:out=OLD_DUMP
  elif remote[:3]==['stat','-c','%F %u %g %s']:self.returncode=1;err=("stat: '"+remote[3]+"': No such file or directory\n").encode()
  elif remote[:3]==['exec-out','tar','-C']:out=N02.read_bytes()
  for name,data in [('stdout',out),('stderr',err)]:
   r,w=os.pipe();setattr(self,name,os.fdopen(r,'rb'))
   def emit(fd=w,body=data):
    try:
     while body:
      n=os.write(fd,body);body=body[n:]
    except BrokenPipeError:pass
    finally:os.close(fd)
   t=threading.Thread(target=emit,daemon=True);t.start();self.threads.append(t)
 def poll(self):return self.returncode
 def wait(self,timeout=None):
  self.waits+=1
  if self.installer and self.mode=='timeout'and self.waits==1:raise subprocess.TimeoutExpired(self.args,timeout)
  return self.returncode
 def terminate(self):self.returncode=-15
 def kill(self):self.returncode=-9
N02=R/'evidence/nativejournal17/n02/sessions/nativejournal17-only02/native-restart-metadata.tar'
oldroot=R/'evidence/betarc01/m101/sessions/beta-rc01-package-diagnostic02/android-api';oldreport=json.loads((R/'evidence/betarc01/m101/reports/package-diagnostic01.json').read_bytes());oldref=next(r['commandReceiptRef']for r in oldreport['observations']if r['command']==['shell','dumpsys','package',PACKAGE]);_,OLD_DUMP,_=original_command(oldroot,oldref,['dumpsys','package',PACKAGE]);CODE=package_state(OLD_DUMP,broken=True)
class Repair(unittest.TestCase):
 def tearDown(self):
  for t in NoChild.threads:t.join(timeout=2)
  self.assertTrue(all(not t.is_alive()for t in NoChild.threads));NoChild.threads=[];NoChild.mode='success'
 def fixture(self,tmp):
  root=Path(tmp)/'m201';root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);b.admit();b.write('campaign',root/'attempts/attempt-01-cases/case-01.json',json.dumps({'context':{'run':'qa'},'fixtureOnly':True}).encode());(root/'sessions/qa').mkdir(parents=True);d=KnownStateRepairDevice('/mock/adb','emulator-5582',root/'sessions/qa/android-api',budget=b,observer_tag='AERIS_PRODUCT_STATUS');d.bind_current_path(CODE);m=load(C,C.name);owner=types.SimpleNamespace(root=root,repo=R,candidate=C,digest=C.name,manifest=m)
  owner.write=lambda n,v:b.write('external_task',root/'reports'/n,(json.dumps(v,sort_keys=True)+'\n').encode())
  d.wait_owned_ready(deadline_ns=d.now()+60_000_000_000);d.prepare_content_reader(deadline_ns=d.now()+30_000_000_000);refs={}
  for key,cmd in [('uid',['shell','id','-u']),('user',['shell','am','get-current-user']),('cold',['shell','sh','-c',COLD]),('dump',['shell','dumpsys','package',PACKAGE]),('private',['shell','sh','-c',STAT]),('codeStat',['shell','stat','-c','%F %u %g %s',d.current_base])]:
   try:d.command(cmd,deadline_ns=d.now()+10_000_000_000)
   except RuntimeError:
    if key!='codeStat':raise
   refs[key]=d.last_command_ref
  d.diagnostic_root_cold_private=True;backup=d.export_stage('before',deadline_ns=d.now()+60_000_000_000);d.command(['shell','sh','-c',COLD],deadline_ns=d.now()+10_000_000_000);refs['coldAfter']=d.last_command_ref;pre={'commandRefs':refs,'preparationRef':d.content_reader_preparation,'currentCodePath':CODE,'backup':backup,'RootIntentSHA256':'a'*64};return owner,d,pre
 def authorize(self,owner,d,pre):
  ref=authorize_repair(owner,d,pre);a=verify_authorization(d.root,ref);owner.write('repair-dispatch-intent01.json',{'authorizationRef':ref,'candidateSHA256':owner.digest,'APKPath':str(C/'native.apk'),'RootIntentSHA256':pre['RootIntentSHA256'],'attempt':1,'consumedBeforeSend':True,'preparedHostNs':d.now(),'automaticRetry':False});return ref
 def test_real_selected_apk_certificate_and_full_private_table(self):
  m=load(C,C.name);self.assertEqual(selected_apk(C,C.name,m),C/'native.apk');self.assertEqual(private_table(N02),original_private_table(R));bad=copy.deepcopy(m);bad['native']['sourceSHA256']='0'*64
  with self.assertRaises(ValueError):selected_apk(C,C.name,bad)
  for path in['/tmp/arbitrary','/data/app/../../bad','/data/app/~~x/foreign/base.apk']:
   with self.assertRaises(ValueError):safe_code_path(path)
  self.assertEqual(package_state(OLD_DUMP.replace(b'pkg=null',b'pkg=Package{new parsed}'),broken=False),CODE)
  for raw in[OLD_DUMP.replace(b'userId=10141',b'userId=10142'),OLD_DUMP.replace(b'pkg=null',b'pkg=Package{ok}')]:
   with self.assertRaises(ValueError):package_state(raw,broken=True)
 def test_actual_auth_load_capture_success10_and_no_resend(self):
  with tempfile.TemporaryDirectory(prefix='repair-mock-',dir=D)as tmp,patch('aeris_runtime.android.subprocess.Popen',NoChild):
   owner,d,pre=self.fixture(tmp);auth=self.authorize(owner,d,pre);before=NoChild.install_calls;ref=d.install_once(C/'native.apk',auth,deadline_ns=d.now()+70_000_000_000);row=verify_install(d.root,ref,auth,str(C/'native.apk'));self.assertEqual(row['version'],10);self.assertEqual(NoChild.install_calls,before+1)
   with self.assertRaises(ValueError):d.install_once(C/'native.apk',auth,deadline_ns=d.now()+70_000_000_000)
 def test_installer_failures_keep_original_auth_capture_and_never_retry(self):
  for mode in['nonzero','stderr','timeout','partial','grammar']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='repair-mock-',dir=D)as tmp,patch('aeris_runtime.android.subprocess.Popen',NoChild):
    owner,d,pre=self.fixture(tmp);auth=self.authorize(owner,d,pre);NoChild.mode=mode;before=NoChild.install_calls
    with self.assertRaises(Exception):d.install_once(C/'native.apk',auth,deadline_ns=d.now()+70_000_000_000)
    self.assertEqual(NoChild.install_calls,before+1);self.assertEqual(d.last_command['version'],10);self.assertEqual(d.last_command['authorizationRef'],auth);self.assertFalse(d.repair_dispatch_active);self.assertEqual(d.last_command['captureComplete'],mode not in('timeout','partial'))
    if mode=='nonzero':self.assertEqual(d.last_command['exit'],1)
    if mode=='stderr':self.assertEqual(read_ref(d.root,d.last_command['stderrRef']),b'warning\n')
    if mode=='partial':self.assertEqual(len(read_ref(d.root,d.last_command['stdoutRef'])),2049)
    with self.assertRaises(ValueError):verify_install(d.root,d.last_command_ref,auth,str(C/'native.apk'))
    with self.assertRaises(ValueError):d.install_once(C/'native.apk',auth,deadline_ns=d.now()+70_000_000_000)
    NoChild.mode='success'
 def test_bad_certificate_private_precheck_or_dispatch_refuses_before_send(self):
  with tempfile.TemporaryDirectory(prefix='repair-mock-',dir=D)as tmp,patch('aeris_runtime.android.subprocess.Popen',NoChild):
   owner,d,pre=self.fixture(tmp);bad=copy.deepcopy(pre);bad['currentCodePath']='/tmp/bad';before=NoChild.install_calls
   with self.assertRaises(ValueError):authorize_repair(owner,d,bad)
   self.assertEqual(NoChild.install_calls,before);auth=self.authorize(owner,d,pre);a=json.loads(read_ref(d.root,auth));a['certificateSHA256']='0'*64;badref=d.store.receipt('bad-cert-auth.json',a)
   with self.assertRaises(ValueError):d.install_once(C/'native.apk',badref,deadline_ns=d.now()+70_000_000_000)
   self.assertEqual(NoChild.install_calls,before)
   p=owner.root/'reports/repair-dispatch-intent01.json';v=json.loads(p.read_bytes());v['attempt']=2;p.write_text(json.dumps(v))
   with self.assertRaises(ValueError):d.install_once(C/'native.apk',auth,deadline_ns=d.now()+70_000_000_000)
   self.assertEqual(NoChild.install_calls,before)
 def test_changed_private_bytes_and_unrelated_commands_refuse_before_send(self):
  with tempfile.TemporaryDirectory(prefix='repair-mock-',dir=D)as tmp,patch('aeris_runtime.android.subprocess.Popen',NoChild):
   owner,d,pre=self.fixture(tmp);before=NoChild.install_calls;p=Path(pre['backup']['path']);raw=p.read_bytes();needle=b'AERIS_INPUT_JOURNAL_V2';self.assertIn(needle,raw);changed=raw.replace(needle,b'XERIS_INPUT_JOURNAL_V2',1);p.write_bytes(changed);pre['backup']['sha256']=file_sha(p)
   with self.assertRaisesRegex(ValueError,'PRIVATE70_TABLE_CONSERVATION'):authorize_repair(owner,d,pre)
   self.assertEqual(NoChild.install_calls,before)
   for cmd in[['install','-r','/arbitrary.apk'],['shell','pm','clear',PACKAGE],['shell','pm','uninstall',PACKAGE],['shell','am','switch-user','1'],['shell','am','start','-n',PACKAGE+'/.Activity'],['shell','sh','-c','rm -rf /data']]:
    with self.subTest(command=cmd),self.assertRaises(ValueError):d._command_bound(cmd)
 def test_actual_entry_owner_writer_order_before_readiness(self):
  import ast
  path=R/'planning/betarc01/runtime/test-writer-order02.py';spec=importlib.util.spec_from_file_location('repair_writer_fixture',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);self.assertIs(mod.WorkbenchRuntime,WorkbenchRuntime)
  tree=ast.parse((D/'root_repair01.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=next(n.body for n in main.body if isinstance(n,ast.Try));prefix=[]
  for n in body:
   prefix.append(n)
   if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='prepare_content_reader':break
  def execute(nodes):
   owner,events,_=mod.Ordering().fixture();device=owner.case['device'];device.adb='/mock/adb';device.root=Path('/mock/empty');device.sequence=0;device.bind_current_path=lambda p:None;ns={'owner':owner,'intent':{'run':'mock17'},'KnownStateRepairDevice':lambda *a,**kw:device,'need':need,'check':owner.check,'known_path':CODE,'time':time};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(D/'root_repair01.py'),'exec'),ns);return events
  events=execute(prefix);self.assertLess(events.index('host-writer-start'),events.index('wait-owned-ready-mock-no-adb'));self.assertEqual(events.count('actual-trace-check'),2)
  old=[n for n in prefix if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='start_writer')]
  with self.assertRaisesRegex(ValueError,'NOT_STARTED_OR_CLOSED'):execute(old)
if __name__=='__main__':unittest.main(verbosity=2)
