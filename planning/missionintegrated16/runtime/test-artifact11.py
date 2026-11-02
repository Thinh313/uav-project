"""Explicit user-authorized11MiB cap; exact delta, no old10MiB expectations."""
from pathlib import Path
import ast,json,os,sys,tarfile,unittest
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent/'source';sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import candidate,host_health,monitor,emulator,preview10
from aeris_runtime.pipeline_contract import artifact_cap_contract
from aeris_runtime.policy import campaign_budget
class Cap11(unittest.TestCase):
 def values(self,n):return dict(metadataBytes=0,metadataAccountingUpperBoundAtScan=0,metadataAccountingWriteSequenceAtScan=0,exportBytes=0,AVDPositiveGrowthBytes=0,artifactBytes=n,taskAllocatedBytes=0,nativePhysicalBytes=0,nativeLogicalBytes=0,checkpointArchiveBytes=0,checkpointArchiveCount=0)
 def predicates(self):return [('guardian',emulator._caps),('hosthealth',lambda v:host_health._inventory_counters(v,'guardian')),('monitor',monitor.ResourceMonitor.__new__(monitor.ResourceMonitor)._caps)]
 def test_shared11_boundary_all_actor_predicates(self):
  self.assertEqual(candidate.CAP,11*2**20)
  for value,admit in [(10*2**20+1,True),(11*2**20,True),(11*2**20+1,False)]:
   for name,fn in self.predicates():
    with self.subTest(actor=name,value=value):
     if admit:fn(self.values(value))
     else:
      with self.assertRaises((ValueError,RuntimeError)):fn(self.values(value))
   self.assertIs(candidate.artifact_cap_admitted(value),admit);self.assertIs(preview10._artifact_admitted(value),admit)
 def test_typed_and_unrelated_guard_rejections_unchanged(self):
  for value in (True,False,1.,None,'1',-1):
   self.assertFalse(candidate.artifact_cap_admitted(value));self.assertFalse(preview10._artifact_admitted(value))
   for name,fn in self.predicates():
    with self.subTest(actor=name,value=value),self.assertRaises((ValueError,RuntimeError)):fn(self.values(value))
  for key,value in [('metadataBytes',64*2**20+1),('exportBytes',192*2**20+1),('AVDPositiveGrowthBytes',512*2**20+1),('taskAllocatedBytes',campaign_budget()['taskHardPeakBytes']+1)]:
   row=self.values(candidate.CAP);row[key]=value
   if key=='metadataBytes':row['metadataAccountingUpperBoundAtScan']=value
   for name,fn in self.predicates():
    with self.subTest(actor=name,guard=key),self.assertRaises((ValueError,RuntimeError)):fn(row)
 def test_exact_authorized_candidate_and11_policy_deltas(self):
  prefix='planning/missionintegrated16/runtime/source/aeris_runtime/'
  with tarfile.open(R/'evidence/missionintegrated16/HOLD02-artifact11-inputs.tar.gz','r:gz')as t:
   old=t.extractfile(prefix+'candidate.py').read();new=(S/'aeris_runtime/candidate.py').read_bytes();self.assertEqual(old.replace(b'CAP=10*MIB',b'CAP=11*MIB').replace(b'ARTIFACT10MiB',b'ARTIFACT11MiB'),new)
   old=json.loads(t.extractfile(prefix+'assets/resource-policy.json').read());new=json.loads((S/'aeris_runtime/assets/resource-policy.json').read_bytes())
  changes=[]
  def walk(a,b,p=()):
   if type(a)is dict:self.assertEqual(set(a),set(b));[walk(a[k],b[k],p+(k,))for k in a]
   elif a!=b:changes.append((p,a,b))
  walk(old,new);expected={('campaign','newIsolatedAPKAndArchiveReserve'),('campaign','taskHardPeakBytes')}
  for c in ('180','760','1960'):expected.update({('cases',c,'budget','categories','newIsolatedAPKAndArchiveReserve'),('cases',c,'budget','taskHardPeakBytes'),('cases',c,'budget','requiredFreeBytes')})
  self.assertEqual(len(changes),11);self.assertEqual({p for p,a,b in changes},expected)
  for p,a,b in changes:self.assertIs(type(a),int);self.assertIs(type(b),int);self.assertEqual(b-a,2**20)
 def test_source_policy_and_selected_manifest_consistency(self):
  proof=artifact_cap_contract({'artifactCapBytes':11*2**20});self.assertTrue(proof['manifestCapChecked']);self.assertEqual(proof['capBytes'],11*2**20);self.assertEqual(len(proof['actorSourceBindings']),5)
  for value in (10*2**20,True,None):
   with self.assertRaisesRegex(ValueError,'MANIFEST_CAP'):artifact_cap_contract({'artifactCapBytes':value})
if __name__=='__main__':unittest.main(verbosity=2)
