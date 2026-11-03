"""Authorized RC-only capacity amendment; actual predicates, no runtime actors."""
from pathlib import Path
import copy,json,os,sys,tarfile,tempfile,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];S=B/'source';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(S),str(R)]
from aeris_runtime import candidate as c,metadata_budget as m,host_health as h,monitor as mon,emulator as e,policy as p,pipeline_contract as pc
from aeris_runtime.lifecycle import Lifecycle
from aeris_runtime.inventory import Inventory
class Caps(unittest.TestCase):
 def values(self):return {'metadataBytes':m.CAP,'metadataAccountingUpperBoundAtScan':m.CAP,'metadataAccountingWriteSequenceAtScan':1,'exportBytes':192*2**20,'AVDPositiveGrowthBytes':512*2**20,'artifactBytes':c.CAP,'nativePhysicalBytes':160*2**20,'nativeLogicalBytes':512*2**20,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8,'taskAllocatedBytes':p.campaign_budget()['taskHardPeakBytes']}
 def test_artifact_boundary_all11_and_old_manifest_refusal(self):
  self.assertEqual(c.CAP,20*2**20);self.assertEqual(len(c.artifact_roots(R/'evidence/nativejournal17/candidates')),11);self.assertTrue(c.artifact_cap_admitted(c.CAP));self.assertFalse(c.artifact_cap_admitted(c.CAP+1))
  for v in[-1,True,1.0,None]:self.assertFalse(c.artifact_cap_admitted(v))
  self.assertEqual(pc.artifact_cap_contract({'artifactCapBytes':c.CAP})['capBytes'],c.CAP)
  with self.assertRaisesRegex(ValueError,'MANIFEST_CAP_MISMATCH'):pc.artifact_cap_contract({'artifactCapBytes':12*2**20})
 def test_actual_health_monitor_guardian_boundaries(self):
  for fn in[lambda v:h._inventory_counters(v,'monitor'),lambda v:mon.ResourceMonitor._caps(None,v),e._caps]:
   fn(self.values())
   for k in['metadataBytes','artifactBytes']:
    for val in[self.values()[k]+1,True,-1]:
     v=self.values();v[k]=val
     with self.subTest(fn=str(fn),key=k,value=val),self.assertRaises((ValueError,RuntimeError)):fn(v)
 def test_actual_ledger_current_plus_unchanged_future_boundary(self):
  self.assertEqual(m.CAP,100*2**20);future=m.observer_envelope()['totalFutureBytes'];self.assertEqual(future,60686336)
  for n in[m.CAP-future,m.CAP-future+1,True,-1]:
   with tempfile.TemporaryDirectory(prefix='caps-ledger-',dir=B)as tmp:
    b=m.MetadataBudget(Path(tmp)/'metadata-budget',lambda:{'metadataBytes':n},free=lambda:100*2**30,mock=True)
    if n==m.CAP-future:self.assertTrue(b.admit()['admitted'])
    else:
     with self.assertRaises(ValueError):b.admit()
 def test_actual_lifecycle_proof_host_capacity(self):
  with tempfile.TemporaryDirectory(prefix='caps-proof-',dir=B)as tmp:
   root=Path(tmp);o=object.__new__(Lifecycle);o.root=root/'sessions/case';o.proof_root=o.root/'lifecycle-proofs';o.journal=types.SimpleNamespace(io=None);inv=object.__new__(Inventory);inv.evidence=root.resolve();required=4096+32768+16384+8192
   for n in[m.CAP-required,m.CAP-required+1]:
    o.budget=types.SimpleNamespace(inventory=inv,snapshot_inventory=lambda *a,**kw:{'metadataBytes':n})
    with patch('aeris_runtime.audit.lifecycle.allocated',return_value=0):
     if n==m.CAP-required:o._proof_capacity(1)
     else:
      with self.assertRaisesRegex(RuntimeError,'GLOBAL_HOST_METADATA100MiB'):o._proof_capacity(1)
 def test_central_actor_and_policy_mismatch_refuses(self):
  self.assertEqual(pc.metadata_cap_contract()['capBytes'],m.CAP)
  with patch.object(h,'METADATA_CAP',64*2**20),self.assertRaisesRegex(ValueError,'ACTOR_CAP_BINDING'):pc.metadata_cap_contract()
  bad=copy.deepcopy(p._DATA);bad['campaign']['globalMetadataCapBytes']=64*2**20
  with patch.object(p,'_DATA',bad),self.assertRaisesRegex(ValueError,'POLICY_CAP_OR_RESERVE'):pc.metadata_cap_contract()
  bad=copy.deepcopy(p._DATA);bad['cases']['760']['budget']['requiredFreeBytes']-=1
  with patch.object(p,'_DATA',bad),self.assertRaisesRegex(ValueError,'POLICY_CAP_OR_RESERVE'):pc.metadata_cap_contract()
 def test_exact_three_mib_reserve_and_unrelated_source_byte_preservation(self):
  with tarfile.open(B/'HOLD02-CAPS02-ORIGINALS.tar.gz')as t:
   old=lambda n:t.extractfile('aeris_runtime/'+n).read()
   for n,replacements in {'candidate.py':[('CAP=12*MIB','CAP=13*MIB'),('ARTIFACT12MiB','ARTIFACT13MiB')],'metadata_budget.py':[('CAP=66*MIB','CAP=68*MIB')],'pipeline_contract.py':[('cap!=66*2**20','cap!=68*2**20')],'lifecycle.py':[('GLOBAL_HOST_METADATA66MiB','GLOBAL_HOST_METADATA68MiB')]}.items():
    expected=old(n).decode()
    for a,b in replacements:expected=expected.replace(a,b)
    self.assertEqual((S/'aeris_runtime'/n).read_text(),expected,n)
   before=json.loads(old('assets/resource-policy.json'));after=p._DATA;self.assertEqual(before['diskGuardPolicy'],after['diskGuardPolicy']);self.assertEqual(before['pipeline06ProfileAmendment'],after['pipeline06ProfileAmendment'])
   for seconds in['180','760','1960']:
    a=before['cases'][seconds];b=after['cases'][seconds]
    for key in['mainJournal','clockJournal','transportJournal','clockEvents']:self.assertEqual(a[key],b[key])
    self.assertEqual(b['budget']['requiredFreeBytes']-a['budget']['requiredFreeBytes'],3*2**20);self.assertEqual(b['budget']['taskHardPeakBytes'],sum(b['budget']['categories'].values()));self.assertEqual(b['budget']['nativeExportCapBytes'],a['budget']['nativeExportCapBytes']);self.assertEqual(b['budget']['categories']['globalMetadata']-a['budget']['categories']['globalMetadata'],2*2**20);self.assertEqual(b['budget']['categories']['newIsolatedAPKAndArchiveReserve']-a['budget']['categories']['newIsolatedAPKAndArchiveReserve'],2**20)
   self.assertEqual(after['campaign']['taskHardPeakBytes']-before['campaign']['taskHardPeakBytes'],3*2**20)
  hold=json.loads((B/'BUILDER-RUNTIME-H5-HOLD02.json').read_bytes());import hashlib
  changed={'candidate.py','metadata_budget.py','pipeline_contract.py','lifecycle.py','assets/resource-policy.json','assets/product-input-closure.json','assets/pipeline-writer-pins.json'}
  for name,digest in hold['selectedSourceSHA256'].items():
   if name[len('aeris_runtime/'):]not in changed:self.assertEqual(hashlib.sha256((S/name).read_bytes()).hexdigest(),digest,name)
if __name__=='__main__':unittest.main(verbosity=2)
