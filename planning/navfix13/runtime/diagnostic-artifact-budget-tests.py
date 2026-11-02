"""Exactlythe userauthorizedNAVFIX13artifact8→9MiB amendment; no actors."""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,sys,unittest
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];SOURCE=HERE/'source';B=SOURCE/'aeris_runtime';M=2**20
HOLD=json.loads((R/'evidence/navfix13/diagnostic-builder-HOLD01.json').read_bytes());OLD={v['path']:v['sha256']for v in HOLD['files']}
class ArtifactBudgetTests(unittest.TestCase):
 def test_runtime_cap_only_text_changes_from_HOLD01(self):
  replacements={
   'candidate.py':[('MIB=2**20;CAP=9*MIB;','MIB=2**20;CAP=8*MIB;'),('CANDIDATE_PREFLIGHT_ARTIFACT9MiB_DISK10GiB','CANDIDATE_PREFLIGHT_ARTIFACT8MiB_DISK10GiB'),('ARTIFACT9MiB_FAILED_PREFIX_RETAINED','ARTIFACT8MiB_FAILED_PREFIX_RETAINED')],
   'preview10.py':[("'artifactCap':9*2**20,'artifactAdmitted':inv['artifactBytes']<=9*2**20","'artifactCap':8*2**20,'artifactAdmitted':inv['artifactBytes']<=8*2**20")],
   'emulator.py':[("'artifactBytes':9*2**20","'artifactBytes':8*2**20")],
   'host_health.py':[("'artifactBytes':9*2**20","'artifactBytes':8*2**20")],
   'monitor.py':[("'artifactBytes':9*MIB","'artifactBytes':8*MIB")]}
  for rel,pairs in replacements.items():
   with self.subTest(rel=rel):
    p=B/rel;text=p.read_text()
    for old,new in pairs:self.assertEqual(text.count(old),1);text=text.replace(old,new)
    self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),OLD[str(p.relative_to(R))])
 def test_resource_policy_exact11delta_paths(self):
  p=B/'assets/resource-policy.json';new=json.loads(p.read_bytes());old=json.loads((R/'planning/vidlife12/runtime/source/aeris_runtime/assets/resource-policy.json').read_bytes());want=copy.deepcopy(old);delta=[]
  for k in('newIsolatedAPKAndArchiveReserve','taskHardPeakBytes'):want['campaign'][k]+=M;delta.append('campaign.'+k)
  for n,item in want['cases'].items():
   b=item['budget'];b['categories']['newIsolatedAPKAndArchiveReserve']+=M;b['taskHardPeakBytes']+=M;b['requiredFreeBytes']+=M
   delta.extend('cases.'+n+'.budget.'+x for x in('categories.newIsolatedAPKAndArchiveReserve','taskHardPeakBytes','requiredFreeBytes'))
  self.assertEqual(len(delta),11);self.assertEqual(new,want)
 def test_journal_segments_floor_and_reserve_unchanged(self):
  old=json.loads((R/'planning/vidlife12/runtime/source/aeris_runtime/assets/resource-policy.json').read_bytes());new=json.loads((B/'assets/resource-policy.json').read_bytes());self.assertEqual(new['diskGuardPolicy'],old['diskGuardPolicy'])
  for n,item in new['cases'].items():
   for k in('mainJournal','transportJournal','clockJournal'):self.assertEqual(item[k],old['cases'][n][k])
   for k in('floorBytes','entryBytes','reserveBytes','maximumSeconds'):self.assertEqual(item['budget'][k],old['cases'][n]['budget'][k])
 def test_all_other_original_selected_source_unchanged(self):
  allowed={'candidate.py','preview10.py','emulator.py','host_health.py','monitor.py','product_runtime.py','android.py','assets/resource-policy.json','assets/product-input-closure.json','assets/pipeline-writer-pins.json'}
  for p in B.rglob('*'):
   if p.is_file()and '__pycache__'not in p.parts and str(p.relative_to(B))not in allowed:self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),OLD[str(p.relative_to(R))],str(p.relative_to(B)))
 def test_9MiB_consistent_caps_boundary_and_oldpool_inclusion(self):
  os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(SOURCE),str(R)]
  from aeris_runtime.candidate import CAP,artifact_roots
  from aeris_runtime.emulator import _caps
  from aeris_runtime.policy import campaign_budget,case_budget
  self.assertEqual(CAP,9*M);roots=artifact_roots(R/'evidence/navfix13/candidates');self.assertEqual(len(roots),7);self.assertEqual(roots[-2:],(R/'evidence/vidlife12/candidates',R/'evidence/navfix13/candidates'))
  v={'metadataBytes':0,'exportBytes':0,'AVDPositiveGrowthBytes':0,'artifactBytes':9*M,'taskAllocatedBytes':0};_caps(v)
  with self.assertRaisesRegex(RuntimeError,'SHARED_ORIGINAL_CAP'):_caps({**v,'artifactBytes':9*M+1})
  self.assertEqual(campaign_budget()['newIsolatedAPKAndArchiveReserve'],9*M)
  for n in(180,760,1960):self.assertEqual(case_budget(maximum_seconds=n)['categories']['newIsolatedAPKAndArchiveReserve'],9*M)
 def test_preflight_probe_timing_source_unmodified(self):
  for name in('root-owner-navfix13.py','scenario-navfix13.py'):
   p=HERE/name;self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),OLD[str(p.relative_to(R))])
if __name__=='__main__':unittest.main(verbosity=2)
