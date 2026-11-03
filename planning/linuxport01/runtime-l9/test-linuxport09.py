"""LINUXPORT01 runtime-l9: the owner's runtime-h9 plus the same Linux host fixes as runtime-l1.

Caps are unchanged (H9 already has artifact 20 MiB, metadata 100 MiB). The only
regenerated data assets are the source pins and reconcile-g103-originals.json,
which pins the g103 evidence of the tree it runs in.
"""
from pathlib import Path
import difflib,hashlib,json,os,sys,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
ORIGINAL=R/'planning/betarc01/runtime-h9/source/aeris_runtime'
PORT=B/'source/aeris_runtime'
L1=R/'planning/linuxport01/runtime-l1/source/aeris_runtime'

class NoPolicyDelta(unittest.TestCase):
 EXPECTED={'host_health.py':(3+2,4+4),'monitor.py':(4,4),'power_worker.py':(2,5),'product_runtime.py':(1,5),'emulator.py':(1,3)}
 REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json','assets/reconcile-g103-originals.json'}
 def changed(self,name):
  a=(ORIGINAL/name).read_text().splitlines();b=(PORT/name).read_text().splitlines()
  rows=[l for l in difflib.unified_diff(a,b,lineterm='',n=0)if l[:1]in'+-'and not l.startswith(('+++','---'))]
  return[l for l in rows if l[0]=='-'],[l for l in rows if l[0]=='+']
 def test_only_declared_files_and_lines_differ(self):
  differ=[p.relative_to(ORIGINAL).as_posix()for p in ORIGINAL.rglob('*')if p.is_file()and'__pycache__'not in p.parts and(PORT/p.relative_to(ORIGINAL)).read_bytes()!=p.read_bytes()]
  self.assertEqual(sorted(differ),sorted([*self.EXPECTED,*self.REGENERATED]))
  added={p.relative_to(PORT).as_posix()for p in PORT.rglob('*')if p.is_file()and'__pycache__'not in p.parts}-{p.relative_to(ORIGINAL).as_posix()for p in ORIGINAL.rglob('*')if p.is_file()}
  self.assertEqual(added,{'host_power_platform.py','linux_disk11.py'})
  for name,(removed,inserted)in self.EXPECTED.items():
   with self.subTest(name=name):
    minus,plus=self.changed(name);self.assertEqual((len(minus),len(plus)),(removed,inserted))
 def test_shared_fixes_are_the_runtime_l1_fixes(self):
  # These five files are identical in H5 and H9, so the runtime-l1 fixes apply unchanged.
  for name in('host_health.py','monitor.py','power_worker.py','emulator.py','host_power_platform.py','linux_disk11.py'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(L1/name).read_bytes())
  self.assertIn("probe=LinuxProbe(self.repo)",(PORT/'product_runtime.py').read_text())
 def test_caps_are_the_owner_h9_caps(self):
  for name in('candidate.py','metadata_budget.py','pipeline_contract.py','lifecycle.py','assets/resource-policy.json'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(ORIGINAL/name).read_bytes())
  self.assertIn('CAP=20*MIB',(PORT/'candidate.py').read_text());self.assertIn('CAP=100*MIB',(PORT/'metadata_budget.py').read_text())

class ReconcileOriginals(unittest.TestCase):
 def load(self,root):return json.loads((root/'assets/reconcile-g103-originals.json').read_bytes())
 def test_same_structure_as_owner(self):
  a,b=self.load(ORIGINAL),self.load(PORT)
  self.assertEqual({k:a[k] for k in a if k!='files'},{k:b[k] for k in b if k!='files'})
  self.assertEqual(sorted(a['files']),sorted(b['files']))
  for name in b['files']:self.assertEqual(set(b['files'][name]),{'bytes','sha256'})
  raw=(PORT/'assets/reconcile-g103-originals.json').read_bytes()
  self.assertEqual(raw,json.dumps(b,sort_keys=True,separators=(',',':')).encode()+b'\n')
 def test_matches_owner_where_bytes_are_machine_independent(self):
  a,b=self.load(ORIGINAL)['files'],self.load(PORT)['files']
  for name in('evidence/betarc01/g103/reports/native17-plan-original.txt','evidence/betarc01/g103/reports/native17-receiver-original.json','evidence/betarc01/g103/sessions/beta-rc01-native01/native-restart-metadata.tar'):
   with self.subTest(name=name):self.assertEqual(a[name],b[name])
 @unittest.skipUnless((R/'evidence/betarc01/g103/reports/native17-plan-original.txt').is_file(),'team g103 evidence')
 def test_pins_this_tree_g103(self):
  for name,r in self.load(PORT)['files'].items():
   with self.subTest(name=name):
    raw=(R/name).read_bytes();self.assertEqual({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},r)

class SourceGate(unittest.TestCase):
 def test_entries_point_at_runtime_l9(self):
  t=(B/'prepare-source-gate.py').read_text();self.assertNotIn('planning/betarc01/runtime-h9/',t)
  for n in('root-maintenance-h9.py','root-native-h9.py','root-reconcile-h9.py'):self.assertIn("'planning/linuxport01/runtime-l9/"+n+"'",t)
 def test_power_helper_launch_and_adb_pin(self):
  src=(PORT/'power_worker.py').read_text();self.assertIn("argv=[sys.executable,'-P','-B',",src)
  self.assertIn("'linux':'a902be8f45c6c62e76c9efaf6947a0fa747c9cabd89a2ac8e0d16ecb30b3ed01'",(PORT/'emulator.py').read_text())

if __name__=='__main__':unittest.main()
