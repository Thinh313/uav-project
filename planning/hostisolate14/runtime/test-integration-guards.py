"""Source and behavioral regression boundaries; no runtime actors."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,struct,sys,tempfile,types,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent;OLD=R/'planning/navfix13/runtime/source/aeris_runtime';NEW=HERE/'source/aeris_runtime';sys.path[:0]=[str(HERE/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import host_health as H
from aeris_runtime.pipeline_contract import health_contract
from aeris_runtime.power_worker import PowerWorker,_capture_error
from aeris_runtime.metadata_budget import LIMITS,OWNERS,CLOSING_OWNERS
class Invariants(unittest.TestCase):
 def test_unchanged_flight_freshness_physics_power_floor_guard(self):
  for name in ('metadata_budget.py','policy.py','admission.py','flight_interval.py','foundation/frame_adapter.py','foundation/frame_core.py','foundation/owner.py','foundation/journal.py','foundation/fdm09.py'):
   self.assertEqual((OLD/name).read_bytes(),(NEW/name).read_bytes(),name)
  def function(p,cl,method):
   tree=ast.parse(p.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cl);return ast.dump(next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name==method),include_attributes=False)
  self.assertEqual(function(OLD/'host_health.py','GuardianClient','__call__'),function(NEW/'host_health.py','GuardianClient','__call__'))
 def test_no_periodic_spawn_in_parent_and_creation_before_service(self):
  tree=ast.parse((NEW/'host_health.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='HostHealth');loop=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='_power_loop');calls=[ast.unparse(n.func)for n in ast.walk(loop)if isinstance(n,ast.Call)];self.assertIn('self.power_worker.query',calls);self.assertFalse(any('capture_command'in c or 'Popen'in c for c in calls));start=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='start');calls=[(n.lineno,ast.unparse(n.func))for n in ast.walk(start)if isinstance(n,ast.Call)];self.assertLess(next(n for n,c in calls if c=='self.power_worker.start'),next(n for n,c in calls if c=='self.audit.start'))
  e=(NEW/'emulator.py').read_text();self.assertLess(e.index('health.start'),e.index('server.start()'))
 def test_one_case_counter_budget_and_no_selected_broker_dispatch(self):
  source=(NEW/'product_runtime.py').read_text();self.assertIn("need(self.case is None,'HOSTISOLATE14_ONE_CASE_DIAGNOSTIC_CHILDREN4')",source);self.assertIn("self.root.name=='s01'",source);self.assertEqual(LIMITS['diagnosticChildren'],4)
  for p in NEW.rglob('*.py'):
   calls=[n for n in ast.walk(ast.parse(p.read_text()))if isinstance(n,ast.Call)and getattr(n.func,'attr',None)=='start_io_broker'];self.assertEqual(calls,[],str(p))
  # guardian DiagnosticJob + companion DiagnosticJob + two health helpers.
  self.assertEqual(2+2,LIMITS['diagnosticChildren'])
 def test_per_owner_audit_helper_and_closure_bounds_unchanged_caps(self):
  c=health_contract();self.assertEqual(c['readDeadlineNs'],100000000);self.assertEqual(c['powerFreshnessAndQueryDeadlineNs'],2000000000)
  for o,n in c['logicalMaximumAuditBytes'].items():self.assertLessEqual(n,H.AUDIT_LEASE[o]-16384)
  self.assertLessEqual(H.AUDIT_LEASE['guardian']+516*1024+16*1024,OWNERS['guardian']);self.assertLessEqual(H.AUDIT_LEASE['monitor']+16*1024,OWNERS['monitor'])
  # New helper close<=8KiB plus two monitor terminal records<=32KiB each.
  self.assertLessEqual(8192+32768*2,CLOSING_OWNERS['monitor']);self.assertEqual(CLOSING_OWNERS['guardian'],136*1024)
 def test_artifact9_and_all_seven_prior_pools_charged(self):
  from aeris_runtime.candidate import artifact_roots,CAP
  roots=artifact_roots(R/'evidence/hostisolate14/candidates');self.assertEqual(len(roots),8);self.assertEqual(CAP,9*2**20);self.assertEqual(roots[-2:],(R/'evidence/navfix13/candidates',R/'evidence/hostisolate14/candidates'))
 def test_capture_secondary_notes_are_not_silently_dropped(self):
  e=OSError('fsync failed');e.add_note('cleanup still failed'*30);raw=_capture_error(e);self.assertLessEqual(len(raw),512);r=json.loads(raw);self.assertEqual(r['notesCount'],1);self.assertTrue(r['diagnosticIsBoundedPrefix']);self.assertEqual(r['notesSHA256'],hashlib.sha256(json.dumps(e.__notes__,ensure_ascii=True,separators=(',',':')).encode()).hexdigest())
 def test_unicode_error_remains_valid_bounded_json_and_marks_truncation(self):
  e=OSError('ắ'*120);e.add_note('風'*80);raw=_capture_error(e);self.assertLessEqual(len(raw),512);v=json.loads(raw);self.assertTrue(v['diagnosticIsBoundedPrefix']);self.assertEqual(v['reasonSHA256'],hashlib.sha256(str(e).encode()).hexdigest())
 def test_no_arm_authority_or_upload_in_bounded_scenario(self):
  tree=ast.parse((HERE/'scenario-hostisolate14.py').read_text());strings={n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and isinstance(n.value,str)};self.assertFalse({'b-arm','b-grant','b-auto','b-upload','video-start'}&strings);self.assertIn('b-preflight',strings)
 def test_mutable_source_inodes_are_independent(self):
  rows=json.loads((HERE.parent/'isolation.json').read_bytes())['files']
  for v in rows:
   a,b=R/v['old'],R/v['new'];self.assertNotEqual((a.stat().st_dev,a.stat().st_ino),(b.stat().st_dev,b.stat().st_ino))
if __name__=='__main__':unittest.main(verbosity=2)
