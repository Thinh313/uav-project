"""Source boundaries and malformed trace corpus, no Android/AP/runtime actors."""
from pathlib import Path
import ast,hashlib,json,os,sys,unittest
R=Path(__file__).resolve().parents[3];N=Path(__file__).parent/'source/aeris_runtime';O=R/'planning/hostisolate14/runtime/source/aeris_runtime';sys.path[:0]=[str(N.parent),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import metadata_budget as B
from aeris_runtime import product_trace15 as T
class GuardTests(unittest.TestCase):
 def test_hosthealth100ms_and_powerpaths_unchanged(self):
  for name in ('host_health.py','power_worker.py','monitor.py','admission.py','policy.py','flight_interval.py','foundation/frame_core.py','foundation/frame_adapter.py','foundation/journal.py','foundation/owner.py','foundation/fdm09.py'):
   old=(O/name).read_bytes();new=(N/name).read_bytes()
   if name=='host_health.py':
    self.assertEqual(new.count(b"'artifactBytes':ARTIFACT_CAP"),1);new=new.replace(b"'artifactBytes':ARTIFACT_CAP",b"'artifactBytes':9*2**20").replace(b'from .candidate import CAP as ARTIFACT_CAP\n',b'')
   elif name=='monitor.py':
    self.assertEqual(new.count(b"'artifactBytes':ARTIFACT_CAP"),1);new=new.replace(b"'artifactBytes':ARTIFACT_CAP",b"'artifactBytes':9*MIB").replace(b'from .candidate import allocated_unique,put,CAP as ARTIFACT_CAP',b'from .candidate import allocated_unique,put')
   self.assertEqual(old,new,name)
 def test_budget_cap_ownership_and_predispatch_functions_unchanged(self):
  def node(path,name):
   t=ast.parse(path.read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef)and n.name=='MetadataBudget');return ast.dump(next(n for n in c.body if isinstance(n,ast.FunctionDef)and n.name==name),include_attributes=False)
  for fn in ('_ready','_spend','reserve_lease','tick','reserve_counter','require_real_actor'):
   self.assertEqual(node(O/'metadata_budget.py',fn),node(N/'metadata_budget.py',fn),fn)
  tree=ast.parse((O/'metadata_budget.py').read_text())
  for name in ('OWNERS','CLOSING_OWNERS','LIMITS'):
   old=next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets));newtree=ast.parse((N/'metadata_budget.py').read_text());new=next(n.value for n in newtree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets));self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))
  self.assertEqual(B.CAP,64*2**20);self.assertEqual(B.CLOSING_OWNERS['closure'],224*1024)
 def test_artifact10_all_nine_pools_are_charged(self):
  from aeris_runtime.candidate import CAP,artifact_roots
  roots=artifact_roots(R/'evidence/writerstage15/candidates');self.assertEqual(CAP,10*2**20);self.assertEqual(len(roots),9);self.assertEqual(roots[-2:],(R/'evidence/hostisolate14/candidates',R/'evidence/writerstage15/candidates'))
 def test_artifact_amendment_exact11_budget_values_and_no_other_policy_changes(self):
  oldp=O/'assets/resource-policy.json';hold=json.loads((R/'evidence/writerstage15/BUILDER-HOLD01.json').read_bytes());row=next(v for v in hold['files']if v['path']=='planning/writerstage15/runtime/source/aeris_runtime/assets/resource-policy.json');self.assertEqual(hashlib.sha256(oldp.read_bytes()).hexdigest(),row['sha256']);old=json.loads(oldp.read_bytes());new=json.loads((N/'assets/resource-policy.json').read_bytes());diff=[]
  def compare(a,b,path=()):
   self.assertEqual(type(a),type(b))
   if type(a)is dict:
    self.assertEqual(set(a),set(b))
    for k in a:compare(a[k],b[k],(*path,k))
   elif type(a)is list:
    self.assertEqual(len(a),len(b))
    for i,(x,y)in enumerate(zip(a,b)):compare(x,y,(*path,str(i)))
   elif a!=b:diff.append((path,a,b))
  compare(old,new);expected={('campaign','newIsolatedAPKAndArchiveReserve'),('campaign','taskHardPeakBytes')}
  for case in ('180','760','1960'):expected.update({('cases',case,'budget','categories','newIsolatedAPKAndArchiveReserve'),('cases',case,'budget','taskHardPeakBytes'),('cases',case,'budget','requiredFreeBytes')})
  self.assertEqual({p for p,a,b in diff},expected);self.assertEqual(len(diff),11)
  for p,a,b in diff:self.assertIs(type(a),int);self.assertEqual(b-a,2**20)
 def test_scenario_one_case_no_arm_upload_auto(self):
  p=Path(__file__).parent/'scenario-writerstage15.py';tree=ast.parse(p.read_text());values={n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and isinstance(n.value,str)};self.assertFalse({'b-arm','b-auto','b-grant','b-upload','video-start'}&values)
  from aeris_runtime.metadata_budget import LIMITS
  self.assertEqual(LIMITS['diagnosticChildren'],4);src=(N/'product_runtime.py').read_text();self.assertIn("self.root.name in('s01','s02')",src);self.assertIn("need(self.case is None,'HOSTISOLATE14_ONE_CASE_DIAGNOSTIC_CHILDREN4')",src)
  for name in ('root-owner-writerstage15-r03.py','preview-admission-r03.py'):self.assertIn("choices=('s01','s02')",(Path(__file__).parent/name).read_text())
 def test_all_mutable_isolation_inodes_are_independent(self):
  for row in json.loads((R/'planning/writerstage15/isolation.json').read_bytes())['files']:
   a,b=R/row['old'],R/row['new'];self.assertNotEqual((a.stat().st_dev,a.stat().st_ino),(b.stat().st_dev,b.stat().st_ino))
 def test_invalid_intent_still_has_decodable_failure_trace(self):
  context={'run':'case15','epoch':'e','boot':'b','operator':'o','generation':'g','profileId':'p'}
  for request in ({'op':'','path':'x','sequence':999999},{'op':None,'path':'風'*160,'sequence':True},{'op':'append','path':'x','sequence':-5}):
   with self.subTest(request=request):
    t=T.WriterTrace(context);op=t.begin(scope='DIRECT_CALL');op.bind(request);op.finish(error=ValueError('rejected'));v=T.decode(t.snapshot(),context=context);self.assertTrue(v['header']['frozen']);self.assertFalse(v['authority']);self.assertIsNotNone(v['rows'][-1]['operation']['q'])
if __name__=='__main__':unittest.main(verbosity=2)
