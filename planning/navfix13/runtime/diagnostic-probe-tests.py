"""Mock-only tests of exactselectedreadonlyscenario/disposal and unchanged guards."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent;SCENARIO=HERE/'scenario-navfix13.py';OWNER=HERE/'root-owner-navfix13.py'
def load_scenario(fake):
 module=types.ModuleType('aeris_runtime.public_ui_workload');module.PublicUIDriver=fake
 def need(v,why):
  if not v:raise RuntimeError(why)
 module.need=need
 with patch.dict(sys.modules,{'aeris_runtime.public_ui_workload':module}):
  spec=importlib.util.spec_from_file_location('source_held_probe_mock',SCENARIO);out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out)
 return out
class FakeUI:
 navigation=True;preflight=True;armed=False;last=None
 def __init__(self,owner,case,check):self.actions=[];self.check=check;self.waits=[];self.compiled=False;type(self).last=self
 def bind_geometry(self):self.check()
 def observation(self):self.check();return{}
 def tap(self,name):self.check();self.actions.append(name);self.compiled|=name=='compile'
 def checked(self,name):self.check();self.actions.append('check:'+name)
 def wait_ui(self,predicate,**kwargs):
  self.check();v={'currentView':'plan','modal':False,'workbenchBusy':False,'planSha256':'a'*64 if self.compiled else None};assert predicate(v);return v
 def save_workspace(self):self.check();return{'planSHA256':'a'*64}
 def event(self,*args):self.check()
 def wait(self,predicate,*,seconds,description,**kw):
  self.check();self.waits.append((description,seconds));v={'flight':{'run':'mock-13','live':{'armed':type(self).armed},'navigationReadiness':{'phase':'DISARMED_READ_ONLY_NAVIGATION_READINESS','ready':type(self).navigation},'preflight':{'ready':type(self).preflight}}}
  if not predicate(v):raise TimeoutError(description)
  return v
class ScenarioTests(unittest.TestCase):
 def setUp(self):FakeUI.navigation=True;FakeUI.preflight=True;FakeUI.armed=False;self.s=load_scenario(FakeUI)
 def test_exact_disarmed_flow_does_not_request_flight_upload_or_video(self):
  out=self.s.run(None,{'plannedSeconds':180},lambda:None);self.assertEqual(out['status'],self.s.DIAGNOSTIC_STATUS);self.assertFalse(out['flightAcceptance']);self.assertFalse(out['recordingAccepted']);allowed={'workspace','sitl-fixture','check:datum','compile','close-modal','next-preflight','check:consent','approve','b-activate','check:b-home','b-connect','b-preflight'};self.assertEqual(set(FakeUI.last.actions),allowed);self.assertIn((self.s.NAVIGATION_PHASE,60),FakeUI.last.waits)
 def test_navigation_timeout_never_calls_preflight(self):
  FakeUI.navigation=False
  with self.assertRaises(TimeoutError):self.s.run(None,{'plannedSeconds':180},lambda:None)
  self.assertNotIn('b-preflight',FakeUI.last.actions)
 def test_armed_observation_never_advances(self):
  FakeUI.armed=True
  with self.assertRaises(TimeoutError):self.s.run(None,{'plannedSeconds':180},lambda:None)
  self.assertNotIn('b-preflight',FakeUI.last.actions)
 def test_original_preflight_rejection_propagates(self):
  FakeUI.preflight=False
  with self.assertRaisesRegex(TimeoutError,'TYPED_PREFLIGHT_DISARMED'):self.s.run(None,{'plannedSeconds':180},lambda:None)
 def test_guard_failure_stops_UI(self):
  def failed():raise RuntimeError('ORIGINAL_GUARD_FAILURE')
  with self.assertRaisesRegex(RuntimeError,'ORIGINAL_GUARD_FAILURE'):self.s.run(None,{'plannedSeconds':180},failed)
 def test_only180secondcase(self):
  with self.assertRaisesRegex(RuntimeError,'EXACT180S'):self.s.run(None,{'plannedSeconds':760},lambda:None)
class DisposalTests(unittest.TestCase):
 def setUp(self):
  tree=ast.parse(OWNER.read_text());selected=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('need','verify_diagnostic_disposal')];env={'json':json,'hashlib':hashlib};exec(compile(ast.Module(body=selected,type_ignores=[]),str(OWNER),'exec'),env);self.verify=env['verify_diagnostic_disposal']
  self.tmp=tempfile.TemporaryDirectory(prefix='diagnostic-mock-',dir=R/'evidence/navfix13');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.digest='c'*64;self.sentinel=RuntimeError('READ_ONLY_DIAGNOSTIC_COMPLETE_REQUESTED_PHYSICAL_DISPOSAL_NOT_FLIGHT_ACCEPTANCE');self.owner=types.SimpleNamespace(root=self.root,digest=self.digest,closed=True,guardian=types.SimpleNamespace(process=types.SimpleNamespace(pid=777,poll=lambda:1)))
  self.disposal={'status':'FAILED_PHYSICAL_DISPOSAL_RECORDED_NOT_ACCEPTANCE','secondaryErrors':[],'flightAcceptance':False,'normalCompletedClosureClaimed':False};ui=b'{"mockUI":true}\n';self.write_bytes('reports/ui-failure-final.json',ui)
  names=['writer-revoke-ingress','stop-command-producer','command-producer-EOF','interval-close','writer-close','simulator-physical-disposal','native-observer-close','resource-monitor-close','guardian-exceptional-disposal']
  self.terminal={'status':self.disposal['status'],'candidateSHA256':self.digest,'primaryFailure':str(self.sentinel),'secondaryErrors':[],'guardianCause':None,'normalCompletedClosureClaimed':False,'flightAcceptance':False,'cleanupSteps':[{'name':n,'returned':True}for n in names],'finalOriginalUIRef':{'path':'reports/ui-failure-final.json','bytes':len(ui),'sha256':hashlib.sha256(ui).hexdigest()}}
  self.guardian={'exit':0,'failure':'RuntimeError:SIMULATOR_FAILED_PHYSICAL_DISPOSAL_NOT_ACCEPTANCE','exceptionalPhysicalDisposal':True,'cleanupNotes':[],'flightCommands':0,'flightAcceptance':False,'health':{'failure':None,'durablyDrained':True,'audit':{'durablyDrained':True,'pendingRows':0,'producedSeq':4,'committedSeq':4}}}
  self.child={'pid':777,'exit':1,'capture':{k:{'captureComplete':True,'failure':None}for k in('stdout','stderr')}};self.flush()
 def write_bytes(self,name,data):p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 def flush(self):
  for p,v in [('reports/owner-terminal.json',self.terminal),('guardian/closure.json',self.guardian),('diagnostics/guardian-process/close.json',self.child)]:self.write_bytes(p,json.dumps(v).encode())
 def call(self):return self.verify(self.owner,self.disposal,self.sentinel)
 def test_complete_exceptional_disposal_is_not_flight_acceptance(self):self.assertFalse(self.call()['flightAcceptance'])
 def test_terminal_EIO_propagates_not_success(self):
  original=Path.read_bytes
  def read(p):
   if p.name=='owner-terminal.json':raise OSError('injected terminal EIO')
   return original(p)
  with patch.object(Path,'read_bytes',read):
   with self.assertRaisesRegex(OSError,'terminal EIO'):self.call()
 def test_terminal_missing_refuses(self):
  (self.root/'reports/owner-terminal.json').unlink()
  with self.assertRaises(RuntimeError):self.call()
 def test_terminal_undurable_note_refuses(self):
  self.sentinel.add_note('OWNER_TERMINAL_UNDURABLE:EIO')
  with self.assertRaises(RuntimeError):self.call()
 def test_guardian_error_refuses(self):
  self.guardian['cleanupNotes']=['failed'];self.flush()
  with self.assertRaises(RuntimeError):self.call()
 def test_guardian_health_fault_refuses(self):
  self.guardian['health']['failure']='DISK_FLOOR';self.flush()
  with self.assertRaises(RuntimeError):self.call()
 def test_guardian_stale_process_refuses(self):
  self.child['pid']=778;self.flush()
  with self.assertRaises(RuntimeError):self.call()
 def test_guardian_capture_truncation_refuses(self):
  self.child['capture']['stdout']['captureComplete']=False;self.flush()
  with self.assertRaises(RuntimeError):self.call()
 def test_original_UI_missing_or_changed_refuses(self):
  self.write_bytes('reports/ui-failure-final.json',b'changed')
  with self.assertRaises(RuntimeError):self.call()
 def test_secondary_cleanup_fault_refuses(self):
  self.disposal['secondaryErrors']=[{'step':'writer-close','error':'EIO'}]
  with self.assertRaises(RuntimeError):self.call()
 def test_terminal_candidate_foreign_refuses(self):
  self.terminal['candidateSHA256']='d'*64;self.flush()
  with self.assertRaises(RuntimeError):self.call()
 def test_terminal_flight_acceptance_or_normal_close_refuses(self):
  for key in('flightAcceptance','normalCompletedClosureClaimed'):
   with self.subTest(key=key):
    self.terminal[key]=True;self.flush()
    with self.assertRaises(RuntimeError):self.call()
    self.terminal[key]=False
class SourceTests(unittest.TestCase):
 def test_no_flight_literals_or_direct_control_in_scenario(self):
  s=SCENARIO.read_text();tree=ast.parse(s);literals={n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and isinstance(n.value,str)}
  self.assertFalse({'b-arm','b-grant','b-auto','b-upload','video-start','b-home-refresh','b-manual-grant'}&literals)
  self.assertNotIn('requests',s);self.assertNotIn('socket',s);self.assertNotIn('subprocess',s)
 def test_original_physics_freshness_and_journal_bytes_preserved(self):
  old=R/'planning/vidlife12/runtime/source/aeris_runtime';new=HERE/'source/aeris_runtime'
  for rel in ['foundation/frame_adapter.py','foundation/frame_core.py','foundation/owner.py','foundation/journal.py','foundation/fdm09.py','policy.py','flight_interval.py','metadata_budget.py']:
   self.assertEqual((new/rel).read_bytes(),(old/rel).read_bytes(),rel)
 def test_exact117source_files_200sites14owners_closed(self):
  pins=json.loads((HERE/'source/aeris_runtime/assets/pipeline-writer-pins.json').read_bytes());self.assertEqual(len(pins['sourceSHA256']),116);self.assertEqual(len(pins['sites']),200);self.assertEqual(len(pins['owners']),14);self.assertEqual(pins['envelope']['totalFutureBytes'],60686336)
 def test_original_and_new_selected_source_inodes_independent(self):
  receipt=json.loads((HERE.parent/'isolation-before-patches.json').read_bytes());self.assertEqual(len(receipt['receipts']),126)
  for x in receipt['receipts']:
   a,b=R/x['original'],R/x['selected'];self.assertNotEqual((a.stat().st_dev,a.stat().st_ino),(b.stat().st_dev,b.stat().st_ino))
 def test_artifact_cap_and_cumulative_roots(self):
  sys.path[:0]=[str(HERE/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
  from aeris_runtime.candidate import artifact_roots,CAP
  self.assertEqual(CAP,9437184);roots=artifact_roots(R/'evidence/navfix13/candidates');self.assertEqual(len(roots),7);self.assertEqual(roots[-2:],(R/'evidence/vidlife12/candidates',R/'evidence/navfix13/candidates'));self.assertEqual(len(set(roots)),7)
if __name__=='__main__':unittest.main(verbosity=2)
