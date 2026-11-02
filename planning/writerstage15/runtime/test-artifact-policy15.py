"""Explicit mock boundary vectors, never real inventory/native observations."""
from pathlib import Path
import json,os,sys,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent/'source';sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import candidate,host_health,monitor,emulator,preview10
from aeris_runtime.pipeline_contract import artifact_cap_contract
from aeris_runtime.policy import campaign_budget
class ArtifactPolicyTests(unittest.TestCase):
 def values(self,artifact):return {'metadataBytes':0,'metadataAccountingUpperBoundAtScan':0,'metadataAccountingWriteSequenceAtScan':0,'exportBytes':0,'AVDPositiveGrowthBytes':0,'artifactBytes':artifact,'taskAllocatedBytes':0,'nativePhysicalBytes':0,'nativeLogicalBytes':0,'checkpointArchiveBytes':0,'checkpointArchiveCount':0}
 def actor_methods(self):return [('emulator',emulator._caps),('HostHealth',lambda v:host_health._inventory_counters(v,'guardian')),('monitor',monitor.ResourceMonitor.__new__(monitor.ResourceMonitor)._caps)]
 def test_shared10MiB_boundary_acceptance_all_five_predicates(self):
  self.assertEqual(candidate.CAP,10*2**20)
  for value,wanted in [(9*2**20+1,True),(10*2**20,True),(10*2**20+1,False)]:
   for name,fn in self.actor_methods():
    with self.subTest(value=value,actor=name):
     if wanted:fn(self.values(value))
     else:
      with self.assertRaises((ValueError,RuntimeError)):fn(self.values(value))
   self.assertIs(candidate.artifact_cap_admitted(value),wanted);self.assertIs(preview10._artifact_admitted(value),wanted)
 def test_boolean_noninteger_and_negative_refused_everywhere(self):
  for value in (True,False,1.,'1',None,-1):
   for name,fn in self.actor_methods():
    with self.subTest(value=value,actor=name):
     with self.assertRaises((ValueError,RuntimeError)):fn(self.values(value))
   self.assertFalse(candidate.artifact_cap_admitted(value));self.assertFalse(preview10._artifact_admitted(value))
 def test_unrelated_limits_still_refuse_same_values(self):
  for key,value in [('metadataBytes',64*2**20+1),('exportBytes',192*2**20+1),('AVDPositiveGrowthBytes',512*2**20+1),('taskAllocatedBytes',campaign_budget()['taskHardPeakBytes']+1)]:
   v=self.values(candidate.CAP);v[key]=value
   if key=='metadataBytes':v['metadataAccountingUpperBoundAtScan']=value
   for name,fn in self.actor_methods():
    with self.subTest(field=key,actor=name):
     with self.assertRaises((ValueError,RuntimeError)):fn(v)
  v=self.values(candidate.CAP);v['nativePhysicalBytes']=160*2**20+1
  with self.assertRaises(RuntimeError):monitor.ResourceMonitor.__new__(monitor.ResourceMonitor)._caps(v)
 def test_pure_contract_exact_binding_and_all_policy_reserves(self):
  v=artifact_cap_contract({'artifactCapBytes':candidate.CAP});self.assertEqual(v['capBytes'],candidate.CAP);self.assertTrue(v['manifestCapChecked']);self.assertTrue(v['pureSourceOnly']);self.assertFalse(v['inventoryOrNativeFactsProduced']);self.assertFalse(v['actorsStarted']);self.assertEqual(len(v['actorSourceBindings']),5);self.assertEqual(set(v['resourcePolicyReserves']),{'campaign','180','760','1960'});self.assertEqual(set(v['resourcePolicyReserves'].values()),{candidate.CAP})
 def test_stale_alias_refused_before_inventory_or_actor(self):
  for module in (host_health,monitor,emulator,preview10):
   with self.subTest(module=module.__name__),patch.object(module,'ARTIFACT_CAP',9*2**20):
    with self.assertRaises(ValueError):artifact_cap_contract()
 def test_stale_actor_literal_refused_even_alias_is_correct(self):
  original=Path.read_bytes
  def read(path):
   raw=original(path)
   return raw.replace(b"'artifactBytes':ARTIFACT_CAP",b"'artifactBytes':9*2**20")if path.name=='emulator.py'else raw
  with patch.object(Path,'read_bytes',read):
   with self.assertRaisesRegex(ValueError,'ACTOR_CAP_SOURCE_BINDING'):artifact_cap_contract()
 def test_manifest_wrong_missing_or_bool_cap_refused(self):
  for manifest in ({},{'artifactCapBytes':9*2**20},{'artifactCapBytes':True},{'artifactCapBytes':'10485760'}):
   with self.subTest(manifest=manifest):
    with self.assertRaisesRegex(ValueError,'MANIFEST_CAP'):artifact_cap_contract(manifest)
 def test_one_policy_reserve_mismatch_refused(self):
  original=Path.read_bytes
  def read(path):
   raw=original(path)
   if path.name=='resource-policy.json':
    v=json.loads(raw);v['cases']['180']['budget']['categories']['newIsolatedAPKAndArchiveReserve']=9*2**20;return json.dumps(v).encode()
   return raw
  with patch.object(Path,'read_bytes',read):
   with self.assertRaisesRegex(ValueError,'POLICY_CAP_MISMATCH'):artifact_cap_contract()
 def test_preview_rejects_stale_actor_before_inventory_sdk_or_slot(self):
  root=R/'evidence/writerstage15';slot=root/'s02';self.assertFalse(slot.exists())
  with patch.object(emulator,'ARTIFACT_CAP',9*2**20),patch.object(preview10,'inputs',side_effect=AssertionError('inputquery')),patch.object(preview10,'avd_allocations',side_effect=AssertionError('AVDscan')),patch.object(preview10,'Inventory',side_effect=AssertionError('inventory')):
   with self.assertRaisesRegex(ValueError,'ACTOR_CAP_SOURCE_BINDING'):preview10.preview(root/'candidates'/('f'*64),'f'*64,slot,R/'planning/writerstage15',R/'evidence/navfix13/emulator-spec.json',validate_candidate=False)
  self.assertFalse(slot.exists())
 def test_bootstrap_manifest_check_precedes_baseline_ledger_and_actors(self):
  import ast
  t=ast.parse((S/'aeris_runtime/product_runtime.py').read_text());cls=next(n for n in t.body if isinstance(n,ast.ClassDef)and n.name=='WorkbenchRuntime');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='bootstrap');calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)];check=next(n for n in calls if isinstance(n.func,ast.Name)and n.func.id=='artifact_cap_contract');self.assertEqual(ast.unparse(check.args[0]),'self.manifest')
  for target in ('capture_avd_baseline','Inventory','MetadataBudget','DiagnosticJob'):
   actor=next(n for n in calls if isinstance(n.func,ast.Name)and n.func.id==target);self.assertLess(check.lineno,actor.lineno,target)
 def test_contract_produces_no_writes_queries_or_actor_creations(self):
  import subprocess,socket
  from aeris_runtime.metadata_budget import MetadataBudget
  from aeris_runtime.inventory import Inventory
  with patch.object(Path,'write_bytes',side_effect=AssertionError('write')),patch.object(Path,'write_text',side_effect=AssertionError('write')),patch.object(Path,'mkdir',side_effect=AssertionError('mkdir')),patch.object(subprocess,'Popen',side_effect=AssertionError('spawn')),patch.object(socket,'socket',side_effect=AssertionError('socket')),patch.object(MetadataBudget,'__init__',side_effect=AssertionError('ledger')),patch.object(Inventory,'__call__',side_effect=AssertionError('inventory')):
   v=artifact_cap_contract();self.assertFalse(v['actorsStarted'])
if __name__=='__main__':unittest.main(verbosity=2)
