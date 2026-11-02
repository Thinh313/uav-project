"""Coupled entry-order regression, actual runtime/writer guards, zero actors."""
from pathlib import Path
import ast,collections,hashlib,json,os,sys,time,types,unittest
R=Path(__file__).resolve().parents[3];S=Path(__file__).resolve().parent;os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(S/'source'),str(R)]
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_writer import ProductWriter

class Ordering(unittest.TestCase):
 def fixture(self):
  events=[];w=object.__new__(ProductWriter);w.closed=False;w.server=None;w.thread=None;w.failure=None;w.sequence=0;w.inflight=None;w.stage_trace=types.SimpleNamespace(check=lambda:events.append('actual-trace-check'));w.descriptor=lambda:{'kind':'MOCK_HOST_WRITER_ONLY'}
  def start():events.append('host-writer-start');w.server=object();w.thread=types.SimpleNamespace(is_alive=lambda:True);return w.descriptor()
  w.start=start
  class Device:
   live_check=None
   def wait_owned_ready(self,**kw):self.live_check();events.append('wait-owned-ready-mock-no-adb')
   def prepare_content_reader(self,**kw):self.live_check();events.append('reader-mock-no-adb')
  o=object.__new__(WorkbenchRuntime);ctx={'run':'mock17','epoch':'1'*32,'boot':'2'*32,'operator':'QA','generation':'3'*32,'profileId':'WORKBENCH_SIM_V1'};cfg={'APSHA256':'a'*64,'modelSHA256':'b'*64,'expectedConfigSHA256':'c'*64,'externalRecordingPolicy':{'amendmentSHA256':'d'*64}};o.root=Path('/mock/betarc01/g101');o.digest='e'*64;o.candidate=S;o.manifest={'native':{'sourceSHA256':'a'*64,'APK_SHA256':'b'*64},'sourceSHA256':collections.defaultdict(lambda:'f'*64),'productInputClosure':{'pins':collections.defaultdict(lambda:'a'*64)}}
  o.case={'root':o.root/'sessions/mock17','context':ctx,'device':Device(),'writer':w,'config':cfg,'admissionRevoked':False,'companion':None,'monitor':types.SimpleNamespace(_never_started=lambda:True),'APStarted':False,'phase':'CREATED','resources':types.SimpleNamespace(children={})};o.budget=types.SimpleNamespace(snapshot=lambda:{'counters':{'cases':1}},require_real_actor=lambda:events.append('guard-real-actor-stub-only'));o.guardian=types.SimpleNamespace(process=types.SimpleNamespace(poll=lambda:None),output=types.SimpleNamespace(check=lambda:None));o.health=lambda:events.append('guard-health-stub-only');o.check_deadline=lambda:None;o.bootstrap=lambda:events.append('bootstrap-mock');o.create_case=lambda *a,**kw:o.case;outputs={}
  def write(name,value):outputs[name]=value;return {'sha256':hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()}
  o.write=write;return o,events,outputs
 def prefix(self,path,o):
  tree=ast.parse(path.read_text());body=next(n.body for n in tree.body if isinstance(n,ast.Try));selected=[]
  for n in body:
   selected.append(n)
   if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='prepare_content_reader':break
  else:raise AssertionError('ENTRY_PREFIX_SHAPE_CHANGED')
  ns={'owner':o,'args':types.SimpleNamespace(run='mock17'),'time':time,'check':o.check};exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),ns);return ns
 def test_old_entry_reproduces_real_not_started_guard_before_adb(self):
  o,events,_=self.fixture()
  with self.assertRaisesRegex(ValueError,'PRODUCT_WRITER_NOT_STARTED_OR_CLOSED'):self.prefix(R/'planning/nativejournal17/runtime/root-owner-native17.py',o)
  self.assertNotIn('wait-owned-ready-mock-no-adb',events);self.assertNotIn('host-writer-start',events)
 def test_repaired_entry_actual_writer_and_runtime_guards_no_weakening(self):
  o,events,outputs=self.fixture();ns=self.prefix(S/'root-native-rc01.py',o)
  self.assertLess(events.index('host-writer-start'),events.index('wait-owned-ready-mock-no-adb'));self.assertEqual(events.count('actual-trace-check'),2);self.assertEqual(events.count('host-writer-start'),1)
  d=outputs['product-descriptor-01.json'];self.assertEqual(d['nativeOnlyScope17']['APStarted'],False);self.assertEqual(d['nativeOnlyScope17']['flightAcceptance'],False);self.assertEqual(d['inputFreshnessNs'],250000000);self.assertEqual(d['inputLeaseNs'],200000000);self.assertFalse(d['authorityRestorable']);self.assertIsNone(o.case['companion']);self.assertFalse(o.case['APStarted']);self.assertEqual(ns['descriptor'],d)
 def test_only_order_changed_old_owner_preserved_no_companion_early(self):
  old=(R/'planning/nativejournal17/runtime/root-owner-native17.py').read_text();new=(R/'planning/nativejournal17/runtime/root-owner-native17-r02.py').read_text();expected=old.replace("owner.bootstrap();case=owner.create_case(args.run,seconds=180);device=case['device'];","owner.bootstrap();case=owner.create_case(args.run,seconds=180);descriptor=owner.start_writer();device=case['device'];").replace(' descriptor=owner.start_writer();descriptor_path=',' descriptor_path=');self.assertEqual(new,expected);self.assertLess(new.index('archive_check(owner,case,post'),new.index('owner.start_companion(argv)'));self.assertEqual(new.count('owner.start_writer()'),1)
if __name__=='__main__':unittest.main(verbosity=2)
