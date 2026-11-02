"""Mock only: finite timings/grammar, original capture, actual owner startup guard."""
from pathlib import Path
import ast,importlib.util,json,os,sys,tempfile,time,types,unittest
from unittest.mock import patch
D=Path(__file__).resolve().parent;R=D.parents[2];C=R/'evidence/nativejournal17/candidates/86bc4cb7e37b77b2b585d7b3a7db08ca01f00a8197c52017ec695c90c86a5aa7';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(C/'source'),str(R)]
sp=importlib.util.spec_from_file_location('reboot_test_helper',D/'probe01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_writer import ProductWriter
BASE='/data/app/~~pjWsSNDU4cUTZcHPafxT8A==/vn.rtr.aeris.betasim09-imWuOa65KanROdr2I2bf4g==/base.apk'
class NoChild:
 def __init__(self,argv,**kw):
  self.pid=os.getpid();self.returncode=1
  for name,body in[('stdout',b''),('stderr',b"stat: '"+BASE.encode()+b"': No such file or directory\n")]:
   r,w=os.pipe();os.write(w,body);os.close(w);setattr(self,name,os.fdopen(r,'rb'))
 def poll(self):return self.returncode
 def wait(self,timeout=None):return self.returncode
class Probe(unittest.TestCase):
 def device(self,tmp):
  root=Path(tmp)/'m202';root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);b.admit();d=m.RebootReadOnlyDevice('/mock/adb','emulator-5582',root/'sessions/mock/android-api',budget=b,observer_tag='AERIS_PRODUCT_STATUS');d.bind_path(BASE);return d
 def test_only_fixed_read_grammar_correct_m201_path_no_mutations(self):
  with tempfile.TemporaryDirectory(prefix='reboot-probe-mock-',dir=D)as tmp:
   d=self.device(tmp)
   for cmd in[*m.SAMPLE_COMMANDS,*m.FIXED_COMMANDS]:self.assertLessEqual(d._command_bound(list(cmd)),131072)
   for cmd in[['install','-r','x'],['shell','sync'],['shell','pm','clear',m.PACKAGE],['shell','am','switch-user','1'],['shell','am','start','-n','x'],['shell','sha256sum','/data/foreign'],['shell','sh','-c','touch /data/x']]:
    with self.subTest(cmd=cmd),self.assertRaises(ValueError):d._command_bound(cmd)
   with self.assertRaises(ValueError):d.bind_path('/tmp/bad')
 def test_original_failed_stat_capture_remains_unknown_complete(self):
  with tempfile.TemporaryDirectory(prefix='reboot-probe-mock-',dir=D)as tmp,patch('aeris_runtime.android.subprocess.Popen',NoChild):
   d=self.device(tmp);row,out=m.observe(d,['shell','stat','-c','%F %u %g %s',BASE]);self.assertEqual(row['status'],'UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED');self.assertEqual(row['exit'],1);self.assertEqual(out,b'');self.assertTrue(d.last_command['captureComplete']);self.assertGreater(row['stderrBytes'],0)
 def test_three_source_fixed_offsets_no_retry_hash_only_after_regular_stat(self):
  clock=[1000000000];calls=[];checks=[];emitted=[]
  def observe(d,cmd):
   calls.append(tuple(cmd));row={'status':'OBSERVED_EXIT0_EMPTY_STDERR'}
   if cmd==['shell','stat','-c','%F %u %g %s',BASE]:return {'status':'UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED'},b''
   if tuple(cmd)==('shell','cat','/proc/sys/kernel/random/boot_id'):return row,b'known-boot\n'
   return row,b''
  def sleep(n):clock[0]+=round(n*1e9)
  with patch.object(m,'observe',observe):samples=m.sample_series(types.SimpleNamespace(current_base=BASE),lambda:checks.append(clock[0]),clock[0],emitted.append,now=lambda:clock[0],sleep=sleep)
  self.assertEqual([v['offsetSeconds']for v in samples],[0,30,60]);self.assertEqual([v['actualOffsetSeconds']for v in samples],[0,30,60]);self.assertEqual(len(samples),3);self.assertEqual(len(emitted),3);self.assertFalse(any('sha256sum'in c for c in calls));self.assertEqual(calls.count(('shell','pm','path','--user','0',m.PACKAGE)),3);self.assertTrue(checks)
 def test_actual_wait_recomputes_after_health_crosses_target_original_fails(self):
  import tarfile
  with tarfile.open(D/'HOLD01-TIMED-WAIT-ORIGINALS.tar.gz')as t:old=t.extractfile(str(D.relative_to(R)/'probe01.py')).read().decode()
  tree=ast.parse(old);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='sample_series');ns=dict(m.__dict__);exec(compile(ast.Module(body=[fn],type_ignores=[]),'held_original_sample_series','exec'),ns)
  def run(function):
   clock=[0];sleeps=[]
   def check():clock[0]+=90_000_000
   def sleep(n):
    if n<0:raise ValueError('NEGATIVE_SLEEP_AFTER_REAL_CHECK')
    sleeps.append(n);clock[0]+=round(n*1e9)
   def observation(d,cmd):return {'status':'UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED'},b''
   with patch.object(m,'observe',observation):
    function.__globals__['observe']=observation
    rows=function(types.SimpleNamespace(current_base=BASE),check,0,lambda v:None,now=lambda:clock[0],sleep=sleep)
   return rows,sleeps
  with self.assertRaisesRegex(ValueError,'NEGATIVE_SLEEP_AFTER_REAL_CHECK'):run(ns['sample_series'])
  rows,sleeps=run(m.sample_series);self.assertEqual([r['targetHostNs']for r in rows],[0,30_000_000_000,60_000_000_000]);self.assertTrue(all(n>0 for n in sleeps));self.assertTrue(all(r['startedHostNs']>=r['targetHostNs']for r in rows))
 def test_actual_entry_evidence_writer_before_device_livecheck(self):
  path=R/'planning/betarc01/runtime/test-writer-order02.py';sp=importlib.util.spec_from_file_location('reboot_order_fixture',path);q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q);self.assertIs(q.WorkbenchRuntime,WorkbenchRuntime);tree=ast.parse((D/'root_probe01.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=next(n.body for n in main.body if isinstance(n,ast.Try));prefix=[]
  for n in body:
   prefix.append(n);call=n.value if isinstance(n,(ast.Assign,ast.Expr))else None
   if isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute)and call.func.attr=='wait_owned_ready':break
  def execute(nodes):
   owner,events,_=q.Ordering().fixture();d=owner.case['device'];d.sequence=0;d.root=Path('/mock/empty');d.adb='/mock/adb';d.bind_path=lambda p:None;ns={'owner':owner,'intent':{'run':'mock17'},'mod':types.SimpleNamespace(RebootReadOnlyDevice=lambda *a,**kw:d),'need':m.need,'base':BASE,'check':owner.check,'time':time};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(D/'root_probe01.py'),'exec'),ns);return events
  events=execute(prefix);self.assertLess(events.index('host-writer-start'),events.index('wait-owned-ready-mock-no-adb'))
  old=[n for n in prefix if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='start_writer')]
  with self.assertRaisesRegex(ValueError,'NOT_STARTED_OR_CLOSED'):execute(old)
 def test_no_install_or_acceptance_source_and_positive_tar_guards(self):
  text=(D/'root_probe01.py').read_text();self.assertIn("intent.get('slot')=='m202'",text);self.assertIn("owner.start_writer()",text)
  for bad in['start_resources(', 'start_companion(', 'install_once(', 'close_maintenance(', "['shell','sync']"]:self.assertNotIn(bad,text)
  row={'status':'OBSERVED_EXIT0_EMPTY_STDERR','exit':0,'error':None,'stderrBytes':0};prep={'format':'aeris-owned-emulator-content-reader-preparation','version':2,'serial':'emulator-5582','actualUID0':True,'confirmation':'READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED'}
  self.assertTrue(m.private_export_eligible(row,b'directory 10141 10141 1\n',row,b'ABSENT\n',prep))
  self.assertFalse(m.private_export_eligible({**row,'status':'UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED'},b'directory 10141 10141 1\n',row,b'ABSENT\n',prep))
if __name__=='__main__':unittest.main(verbosity=2)
