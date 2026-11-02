"""No actors: fixed grammar plus actual inherited command capture and export."""
from pathlib import Path
import ast,io,json,os,sys,tarfile,tempfile,unittest
from unittest.mock import patch
D=Path(__file__).resolve().parent;R=D.parents[2];C=R/'evidence/nativejournal17/candidates/86bc4cb7e37b77b2b585d7b3a7db08ca01f00a8197c52017ec695c90c86a5aa7';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(C/'source'),str(R)]
from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,READ_COMMANDS,PRIVATE,private_export_eligible
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.once_reader import read_ref
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_writer import ProductWriter
class NoChild:
 out=b'';err=b'';code=0
 def __init__(self,argv,**kw):
  self.pid=os.getpid();self.args=argv;self.returncode=self.code
  for name,data in [('stdout',self.out),('stderr',self.err)]:
   r,w=os.pipe();os.write(w,data);os.close(w);setattr(self,name,os.fdopen(r,'rb'))
 def poll(self):return self.returncode
 def wait(self,timeout=None):return self.returncode
class PackageQA(unittest.TestCase):
 def device(self,tmp):
  root=Path(tmp)/'m102';root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);b.admit();b.write('campaign',root/'attempts/attempt-01-cases/case-01.json',json.dumps({'context':{'run':'qa'},'fixtureOnly':True}).encode());(root/'sessions/qa').mkdir(parents=True);d=ReadOnlyPackageDevice('/mock/adb','emulator-5582',root/'sessions/qa/android-api',budget=b,observer_tag='AERIS_PRODUCT_STATUS');return d
 def test_fixed_commands_and_mutation_physical_arbitrary_rejected(self):
  with tempfile.TemporaryDirectory(prefix='package-mock-',dir=D)as tmp:
   d=self.device(tmp)
   for c,n in READ_COMMANDS.items():self.assertEqual(d._command_bound(list(c)),n)
   for c in [['install','-r','/tmp/x'],['shell','pm','clear','vn.rtr.aeris.betasim09'],['shell','am','force-stop','vn.rtr.aeris.betasim09'],['shell','sh','-c','id'],['shell','pm','path','--user','10','vn.rtr.aeris.betasim09']]:
    with self.assertRaises(ValueError):d._command_bound(c)
   d.serial='physical'
   with self.assertRaises(ValueError):d._command_bound(next(iter(READ_COMMANDS)))
 def test_actual_inherited_capture_retains_nonzero_and_stderr(self):
  with tempfile.TemporaryDirectory(prefix='package-mock-',dir=D)as tmp:
   d=self.device(tmp)
   for code,err in[(1,b''),(0,b'warning')]:
    with patch('aeris_runtime.android.subprocess.Popen',NoChild),patch.object(NoChild,'out',b'observed'),patch.object(NoChild,'err',err),patch.object(NoChild,'code',code):
     with self.assertRaises(RuntimeError):d.command(['shell','pm','path','--user','0','vn.rtr.aeris.betasim09'],deadline_ns=d.now()+2_000_000_000)
    self.assertTrue(d.last_command['captureComplete']);self.assertEqual(d.last_command['exit'],code);self.assertEqual(read_ref(d.root,d.last_command['stdoutRef']),b'observed');self.assertEqual(read_ref(d.root,d.last_command['stderrRef']),err)
 def test_root_tar_has_exact_readonly_argv_real_capture_and_no_reset(self):
  buff=io.BytesIO()
  with tarfile.open(fileobj=buff,mode='w')as t:
   m=tarfile.TarInfo('files/original');m.size=3;t.addfile(m,io.BytesIO(b'OLD'))
  with tempfile.TemporaryDirectory(prefix='package-mock-',dir=D)as tmp:
   d=self.device(tmp)
   with self.assertRaises(ValueError):d.export_root_private(deadline_ns=d.now()+2_000_000_000)
   d.diagnostic_root_cold_private=True
   with patch('aeris_runtime.android.subprocess.Popen',NoChild),patch.object(NoChild,'out',buff.getvalue()),patch.object(NoChild,'err',b''),patch.object(NoChild,'code',0):r=d.export_root_private(deadline_ns=d.now()+2_000_000_000)
   self.assertEqual(r['argv'],['/mock/adb','-s','emulator-5582','exec-out','tar','-C',PRIVATE,'-cf','-','files']);self.assertEqual(Path(r['path']).read_bytes(),buff.getvalue());self.assertTrue(r['captureComplete'])
   with self.assertRaises(ValueError):d.export_root_private(deadline_ns=d.now()+2_000_000_000)
 def test_private_tar_rejects_positive_body_with_nonzero_stderr_or_unproven_root(self):
  row={'status':'OBSERVED_EXIT0_EMPTY_STDERR','exit':0,'error':None,'stderrBytes':0};prep={'format':'aeris-owned-emulator-content-reader-preparation','version':2,'serial':'emulator-5582','actualUID0':True,'confirmation':'READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED'};stat=b'directory 10000 10000 1\n';cold=b'ABSENT\n'
  self.assertTrue(private_export_eligible(row,stat,row,cold,prep))
  for field,val in [('status','UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED'),('exit',1),('exit',False),('error','ANDROID_COMMAND_EXIT:1'),('stderrBytes',1),('stderrBytes',False)]:
   bad={**row,field:val}
   for side in[0,1]:
    args=[row,stat,row,cold,prep];args[side*2]=bad
    with self.subTest(field=field,side=side):self.assertFalse(private_export_eligible(*args))
  for field,val in [('actualUID0',False),('serial','physical'),('confirmation','ASSERTED_ROOT')]:self.assertFalse(private_export_eligible(row,stat,row,cold,{**prep,field:val}))
 def test_actual_owner_check_requires_evidence_writer_before_readiness(self):
  import importlib.util,time,types
  path=R/'planning/betarc01/runtime/test-writer-order02.py';spec=importlib.util.spec_from_file_location('existing_writer_order_fixture',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);self.assertIs(module.WorkbenchRuntime,WorkbenchRuntime);self.assertTrue(Path(sys.modules[WorkbenchRuntime.__module__].__file__).is_relative_to(C))
  tree=ast.parse((D/'root_package01.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=next(n.body for n in main.body if isinstance(n,ast.Try));prefix=[]
  for n in body:
   prefix.append(n)
   if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='prepare_content_reader':break
  else:raise AssertionError('ACTUAL_ENTRY_PREFIX_CHANGED')
  def execute(nodes):
   owner,events,reports=module.Ordering().fixture();device=owner.case['device'];device.adb='/mock/adb';device.root=Path('/mock/empty-command-root');device.sequence=0
   ns={'owner':owner,'intent':{'run':'mock17'},'need':lambda v,n:None if v else(_ for _ in()).throw(ValueError(n)),'ReadOnlyPackageDevice':lambda *a,**kw:device,'check':owner.check,'time':time};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(D/'root_package01.py'),'exec'),ns);return owner,events,reports
  owner,events,reports=execute(prefix);self.assertLess(events.index('host-writer-start'),events.index('wait-owned-ready-mock-no-adb'));self.assertEqual(events.count('actual-trace-check'),2);self.assertEqual(events.count('host-writer-start'),1);self.assertFalse(owner.case['APStarted']);self.assertIsNone(owner.case['companion']);self.assertIn('product-descriptor-01.json',reports)
  import copy
  old=copy.deepcopy(prefix)
  old=[n for n in old if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='start_writer')]
  with self.assertRaisesRegex(ValueError,'PRODUCT_WRITER_NOT_STARTED_OR_CLOSED'):execute(old)
 def test_entry_has_no_activity_mavlink_ap_or_normal_success(self):
  text=(D/'root_package01.py').read_text();ast.parse(text)
  for absent in['start_resources(', 'start_companion(', 'close_maintenance(', '.start()']:self.assertNotIn(absent,text)
  self.assertIn("owner.fail_case(primary)",text);self.assertIn('SOURCE_READONLY_DIAGNOSTIC_COMPLETE_NOT_FLIGHT',text);self.assertIn("intent.get('slot')=='m101'",text)
if __name__=='__main__':unittest.main(verbosity=2)
