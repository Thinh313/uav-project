"""Actual selected H8 caps and exact authorized delta; no actors or freeze."""
from pathlib import Path
import gzip,hashlib,json,os,stat,sys,tempfile,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime import candidate,metadata_budget as m,policy
from aeris_runtime.pipeline_contract import artifact_cap_contract,metadata_cap_contract,require_closed_contract
class Caps03(unittest.TestCase):
 def test_actual_artifact_strict_typed_boundary_all_original_pools(self):
  self.assertEqual(candidate.CAP,20*2**20)
  for n in [0,13*2**20+1,candidate.CAP]:self.assertTrue(candidate.artifact_cap_admitted(n))
  for n in [-1,True,20.0,None,candidate.CAP+1]:self.assertFalse(candidate.artifact_cap_admitted(n))
  self.assertEqual(artifact_cap_contract()['capBytes'],candidate.CAP)
  self.assertEqual(len(candidate.artifact_roots(R/'evidence/nativejournal17/candidates')),11)
 def test_actual_metadata_admit_boundary_owner_limits_not_relaxed(self):
  self.assertEqual(m.CAP,100*2**20);future=m.observer_envelope()['totalFutureBytes'];self.assertEqual(future,60686336);self.assertEqual(len(m.OWNERS),14)
  for extra in [0,1]:
   with tempfile.TemporaryDirectory(prefix='caps-',dir=B)as tmp:
    budget=m.MetadataBudget(Path(tmp)/'metadata-budget',lambda:{'metadataBytes':m.CAP-future+extra},free=lambda:100*2**30,mock=True)
    if extra:
     with self.assertRaisesRegex(ValueError,'METADATA_CURRENT_PLUS_SOURCE_ENVELOPES_AND_CLOSURE'):budget.admit()
    else:self.assertTrue(budget.admit()['admitted'])
  self.assertEqual(metadata_cap_contract()['capBytes'],m.CAP)
 def test_case_and_campaign_real_reserve_delta_and_no_other_policy_delta(self):
  old=json.loads((R/'planning/betarc01/runtime-h7/source/aeris_runtime/assets/resource-policy.json').read_bytes());new=policy._DATA;delta=39*2**20
  for seconds in ['180','760','1960']:
   a=old['cases'][seconds];b=new['cases'][seconds];self.assertEqual({k:v for k,v in a.items()if k!='budget'},{k:v for k,v in b.items()if k!='budget'})
   a=a['budget'];b=b['budget'];self.assertEqual(b['taskHardPeakBytes']-a['taskHardPeakBytes'],delta);self.assertEqual(b['requiredFreeBytes']-a['requiredFreeBytes'],delta);self.assertEqual(sum(b['categories'].values()),b['taskHardPeakBytes']);self.assertEqual(b['requiredFreeBytes'],b['taskHardPeakBytes']+10*2**30+256*2**20)
   self.assertEqual({k:v for k,v in a.items()if k not in['categories','taskHardPeakBytes','requiredFreeBytes']},{k:v for k,v in b.items()if k not in['categories','taskHardPeakBytes','requiredFreeBytes']})
   self.assertEqual({k:v for k,v in a['categories'].items()if k not in['globalMetadata','newIsolatedAPKAndArchiveReserve']},{k:v for k,v in b['categories'].items()if k not in['globalMetadata','newIsolatedAPKAndArchiveReserve']})
   self.assertEqual(b['categories']['globalMetadata'],100*2**20);self.assertEqual(b['categories']['newIsolatedAPKAndArchiveReserve'],20*2**20)
   self.assertFalse(policy.case_budget(b['requiredFreeBytes']-1,int(seconds))['admitted']);self.assertTrue(policy.case_budget(b['requiredFreeBytes'],int(seconds))['admitted'])
  self.assertEqual(new['campaign']['taskHardPeakBytes']-old['campaign']['taskHardPeakBytes'],delta)
  self.assertEqual(new['diskGuardPolicy'],old['diskGuardPolicy']);self.assertEqual(new['pipeline06ProfileAmendment'],old['pipeline06ProfileAmendment'])
 def test_predecessors_and_exact_guard_source_preservation(self):
  baseline=json.loads(gzip.decompress((B/'H7-H8-DERIVATION-BASELINE.json.gz').read_bytes()))
  for n,x in baseline['files'].items():
   p=R/n;s=p.stat();self.assertEqual((hashlib.sha256(p.read_bytes()).hexdigest(),s.st_size,stat.S_IMODE(s.st_mode),s.st_ino,s.st_dev),(x['sha256'],x['bytes'],x['mode'],x['inode'],x['device']))
  for n in ['candidate.py','metadata_budget.py','pipeline_contract.py','lifecycle.py','android.py','inventory.py','guest_sync_h4.py','emulator.py','assets/resource-policy.json']:
   self.assertEqual((B/'source/aeris_runtime'/n).read_bytes(),(R/'planning/betarc01/runtime-h8/source/aeris_runtime'/n).read_bytes())
  from aeris_runtime.mission16 import SLOTS
  import ast
  oldtree=ast.parse((R/'planning/betarc01/runtime-h8/source/aeris_runtime/mission16.py').read_bytes());oldslots=ast.literal_eval(next(n.value for n in oldtree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SLOTS'for t in n.targets)))
  self.assertEqual(set(SLOTS)-set(oldslots),{'m701','m702','g105'});self.assertTrue(all(SLOTS[k]==v for k,v in oldslots.items()))
  proof=require_closed_contract();self.assertEqual((proof['sourceFiles'],proof['sites'],proof['owners'],proof['futureBytes']),(138,254,14,60686336))
if __name__=='__main__':unittest.main(verbosity=2)
