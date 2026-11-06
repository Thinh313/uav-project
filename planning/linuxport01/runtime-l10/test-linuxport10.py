"""LINUXPORT01 runtime-l10: the owner's runtime-h10 plus the same Linux host fixes as runtime-l9.

Caps are unchanged (H10 has artifact 20 MiB, metadata 100 MiB). The regenerated
data assets are the source pins; reconcile-g103-originals.json is the runtime-l9
one, which pins the g103 evidence of the tree it runs in. The three H10 entries
(root-capture/native/owner-h10.py) are byte-identical to the owner's.
"""
from pathlib import Path
import difflib,hashlib,json,os,sys,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
OWNER=R/'planning/betarc01/runtime-h10'
ORIGINAL=OWNER/'source/aeris_runtime'
PORT=B/'source/aeris_runtime'
L1=R/'planning/linuxport01/runtime-l1/source/aeris_runtime'
L9=R/'planning/linuxport01/runtime-l9/source/aeris_runtime'
ENTRIES=('root-capture-h10.py','root-native-h10.py','root-owner-h10.py')

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
 def test_shared_fixes_are_the_runtime_l1_and_l9_fixes(self):
  # These files are identical in H5, H9 and H10, so the runtime-l1 fixes apply unchanged.
  for name in('host_health.py','monitor.py','power_worker.py','emulator.py','host_power_platform.py','linux_disk11.py'):
   with self.subTest(name=name):
    self.assertEqual((PORT/name).read_bytes(),(L1/name).read_bytes());self.assertEqual((PORT/name).read_bytes(),(L9/name).read_bytes())
  self.assertIn("probe=LinuxProbe(self.repo)",(PORT/'product_runtime.py').read_text())
 def test_product_runtime_is_h10_plus_the_l9_probe(self):
  # Same five inserted lines and one removed line as runtime-l9 applied to H9.
  h9=R/'planning/betarc01/runtime-h9/source/aeris_runtime/product_runtime.py'
  def delta(a,b):return[l for l in difflib.unified_diff(Path(a).read_text().splitlines(),Path(b).read_text().splitlines(),lineterm='',n=0)if l[:1]in'+-'and not l.startswith(('+++','---'))]
  self.assertEqual(delta(ORIGINAL/'product_runtime.py',PORT/'product_runtime.py'),delta(h9,L9/'product_runtime.py'))
 def test_caps_are_the_owner_h10_caps(self):
  for name in('candidate.py','metadata_budget.py','pipeline_contract.py','lifecycle.py','assets/resource-policy.json'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(ORIGINAL/name).read_bytes())
  self.assertIn('CAP=20*MIB',(PORT/'candidate.py').read_text());self.assertIn('CAP=100*MIB',(PORT/'metadata_budget.py').read_text())
 def test_h10_entries_and_new_modules_unchanged(self):
  for name in ENTRIES:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(OWNER/name).read_bytes())
  for name in('command_results_h10.py','forensic_h10.py','product_writer.py','product_inputs.py','node_alias_h9.py','mission16.py'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(ORIGINAL/name).read_bytes())

class ReconcileOriginals(unittest.TestCase):
 def test_same_as_runtime_l9(self):
  self.assertEqual((PORT/'assets/reconcile-g103-originals.json').read_bytes(),(L9/'assets/reconcile-g103-originals.json').read_bytes())
 @unittest.skipUnless((R/'evidence/betarc01/g103/reports/native17-plan-original.txt').is_file(),'team g103 evidence')
 def test_pins_this_tree_g103(self):
  for name,r in json.loads((PORT/'assets/reconcile-g103-originals.json').read_bytes())['files'].items():
   with self.subTest(name=name):
    raw=(R/name).read_bytes();self.assertEqual({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},r)

class WriterContract(unittest.TestCase):
 def load(self,root):return json.loads((root/'assets/pipeline-writer-pins.json').read_bytes())
 def test_same_writer_contract_as_owner_h10(self):
  a,b=self.load(ORIGINAL),self.load(PORT)
  self.assertEqual(len(b['sites']),257);self.assertEqual(len(b['owners']),14)
  for k in('envelope','format','frozenLeafSHA256','metadataBoundary','owners','siteFileHashBinding','version'):
   with self.subTest(key=k):self.assertEqual(a[k],b[k])
  # Same sites in the same order; only the files edited for Linux may move line numbers.
  edited={'aeris_runtime/'+n for n in NoPolicyDelta.EXPECTED}
  strip=lambda s:{k:v for k,v in s.items()if k!='siteSHA256'and not(k=='line'and s['module']in edited)}
  self.assertEqual([strip(s)for s in a['sites']],[strip(s)for s in b['sites']])
 def test_health_contract_differs_only_in_changed_actor_hashes(self):
  def flat(v,pre=''):
   if isinstance(v,dict):
    for k,x in v.items():yield from flat(x,pre+'/'+k)
   elif isinstance(v,list):
    for i,x in enumerate(v):yield from flat(x,pre+'/%d'%i)
   else:yield pre,v
  a,b=dict(flat(self.load(ORIGINAL)['healthContract'])),dict(flat(self.load(PORT)['healthContract']))
  self.assertEqual(set(a),set(b))
  for k in a:
   if a[k]!=b[k]:
    with self.subTest(key=k):self.assertRegex(k,r'^/(artifactCapPolicy|hostMetadataCapPolicy)/actorSourceBindings/\d+/sourceSHA256$')

class SourceGate(unittest.TestCase):
 def test_entries_point_at_runtime_l10(self):
  t=(B/'prepare-source-gate.py').read_text();self.assertNotIn('planning/betarc01/runtime-h10/',t)
  for n in ENTRIES:self.assertIn("'planning/linuxport01/runtime-l10/"+n+"'",t)
  # H10 itself keeps the unchanged H9 maintenance entry; so does the port.
  self.assertIn("'planning/betarc01/runtime-h9/root-maintenance-h9.py'",t)
  a=(OWNER/'prepare-source-gate.py').read_text().splitlines();b=t.splitlines()
  self.assertEqual(len(a),len(b));self.assertEqual([i for i,(x,y)in enumerate(zip(a,b))if x!=y],[16])
 def test_power_helper_launch_and_adb_pin(self):
  src=(PORT/'power_worker.py').read_text();self.assertIn("argv=[sys.executable,'-P','-B',",src)
  self.assertIn("'linux':'a902be8f45c6c62e76c9efaf6947a0fa747c9cabd89a2ac8e0d16ecb30b3ed01'",(PORT/'emulator.py').read_text())

if __name__=='__main__':unittest.main()
