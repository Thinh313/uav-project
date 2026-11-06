"""LINUXPORT01 runtime-l15: runtime-l14 plus the m803 forensic capture slot (team code).

Checks that every changed file is its runtime-l14 original plus exactly the patches in
l15_patches.py, that the capture entry is runtime-l14's root-capture-l12.py (itself the
owner's root-capture-h10.py plus l12_patches.CAPTURE) plus the declared patches and uses
no registry decoder, that the graph changes only the entry paths and the capture entry,
that the writer sites are the same, and that the team continuation module, the owner's
reference check, the 200 ms writer limit and the 40 MiB cap are unchanged. The runtime-l14
behaviour tests (contract admission, two-boot proof check, G1 start, cold domain check,
archive_check on real data, SDK boot check) are repeated on the runtime-l15 source.
Run from the tree root (the bind mount) with Python 3.14 -B.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R),str(B)]
import l15_patches as P
import aeris_runtime
L14=R/'planning/linuxport01/runtime-l14';L12=R/'planning/linuxport01/runtime-l12';PORT=B/'source/aeris_runtime';BASE=L14/'source/aeris_runtime'
REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json'};MIB=2**20
PIN12='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'
def sha(b):return hashlib.sha256(b).hexdigest()
def files(root):return{p.relative_to(root).as_posix()for p in Path(root).rglob('*')if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.json.gz')}
def load(p):return json.loads(Path(p).read_bytes())
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Derivation(unittest.TestCase):
 def test_source_is_l14_plus_declared_patches_only(self):
  self.assertEqual(files(PORT),files(BASE))
  differ={n for n in files(BASE)if(PORT/n).read_bytes()!=(BASE/n).read_bytes()}
  self.assertEqual(differ,set(P.MODULES)|REGENERATED)
  for name,patches in P.MODULES.items():
   with self.subTest(name=name):self.assertEqual((PORT/name).read_text(),P.apply((BASE/name).read_text(),patches,name))
 def test_capture_entry_is_l14_capture_plus_declared_patches(self):
  owner=R/'planning/betarc01/runtime-h10/root-capture-h10.py';l12=module(L12/'l12_patches.py','l12_patches_for_l15_test')
  # The chain back to the owner: runtime-l14/root-capture-l12.py is the owner's entry plus l12_patches.CAPTURE.
  self.assertEqual((R/P.CAPTURE_SOURCE).read_text(),l12.apply(owner.read_text(),l12.CAPTURE,'root-capture-l12.py'))
  self.assertEqual((B/'root-capture-l15.py').read_text(),P.apply((R/P.CAPTURE_SOURCE).read_text(),P.CAPTURE,'root-capture-l15.py'))
  self.assertEqual((B/'root-capture-l15.py').stat().st_mode&0o111,(R/P.CAPTURE_SOURCE).stat().st_mode&0o111)
 def test_other_top_level_files_unchanged_from_l14(self):
  new={'l15_patches.py','root-capture-l15.py','test-linuxport15.py','prepare-source-gate.py'}
  top={p.name for p in B.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}
  self.assertEqual(top-new,{p.name for p in L14.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}-{'l14_patches.py','test-linuxport14.py','prepare-source-gate.py'})
  for name in top-new:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(L14/name).read_bytes());self.assertEqual((B/name).stat().st_mode&0o111,(L14/name).stat().st_mode&0o111)
  self.assertEqual((B/'prepare-source-gate.py').read_text(),P.gate((L14/'prepare-source-gate.py').read_text()))
 def test_capture_entry_uses_no_registry_decoder(self):
  tree=ast.parse((B/'root-capture-l15.py').read_text());mods={n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}
  self.assertFalse([m for m in mods if m and('reconcile'in m or'continuation'in m)])
 def test_guards_and_team_module_unchanged(self):
  for name in('continuation_l13.py','rc01.py','product_writer.py','candidate.py','installclosure_h4.py','native17.py','assets/resource-policy.json'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(BASE/name).read_bytes())
  from aeris_runtime import candidate,product_writer
  self.assertEqual(candidate.CAP,40*MIB);self.assertEqual(product_writer.RPC_NS,200_000_000)
  self.assertIn("TimeoutError('PRODUCT_WRITER_COMMITTED_AFTER200MS_NO_RETRY')",(PORT/'product_writer.py').read_text())
 def test_graph_changes_only_entry_paths_and_the_capture_entry(self):
  a=load(BASE/'assets/product-input-closure.json');b=load(PORT/'assets/product-input-closure.json')
  self.assertEqual(len(b['entrypoints']),8);self.assertEqual(len(a['entrypoints']),8)
  self.assertEqual({e.replace('runtime-l14/root-capture-l12.py','runtime-l15/root-capture-l15.py').replace('runtime-l14','runtime-l15')for e in a['entrypoints']},set(b['entrypoints']))
  self.assertFalse([e for e in b['entrypoints']if'runtime-l14'in e or e.endswith('root-capture-l12.py')])
  ra={k.replace('runtime-l14/root-capture-l12.py','CAPTURE').replace('runtime-l14','L'):v for k,v in a['pins'].items()}
  rb={k.replace('runtime-l15/root-capture-l15.py','CAPTURE').replace('runtime-l15','L'):v for k,v in b['pins'].items()}
  self.assertEqual(set(ra),set(rb));self.assertEqual({k for k in ra if ra[k]!=rb[k]},{'planning/linuxport01/CAPTURE'})
  self.assertEqual(b['pins']['planning/linuxport01/runtime-l15/root-capture-l15.py'],sha((B/'root-capture-l15.py').read_bytes()))
  self.assertEqual(b['pins']['planning/linuxport01/contract-l12/m802-continuation-pin.json'],PIN12)
  ren=lambda v:json.loads(json.dumps(v).replace('runtime-l14/root-capture-l12.py','runtime-l15/root-capture-l15.py').replace('runtime-l14','runtime-l15'))
  for k in set(a)|set(b):
   if k in('pins','entrypoints'):continue
   with self.subTest(k=k):self.assertEqual(sorted(map(json.dumps,ren(a[k])))if type(a[k])is list else ren(a[k]),sorted(map(json.dumps,b[k]))if type(b[k])is list else b[k])
 def test_writer_sites_unchanged(self):
  a=load(BASE/'assets/pipeline-writer-pins.json');b=load(PORT/'assets/pipeline-writer-pins.json')
  self.assertEqual(a['sites'],b['sites']);self.assertEqual(len(b['sites']),265)
  for k in('owners','envelope','frozenLeafSHA256','metadataBoundary','format','version','healthContract'):
   with self.subTest(k=k):self.assertEqual(a[k],b[k])
  self.assertEqual({k for k in set(a)|set(b)if a.get(k)!=b.get(k)},{'productInputClosure','sourceSHA256'})
  self.assertEqual({k for k in set(a['sourceSHA256'])|set(b['sourceSHA256'])if a['sourceSHA256'].get(k)!=b['sourceSHA256'].get(k)},{'aeris_runtime/'+n for n in P.MODULES}|{'aeris_runtime/assets/product-input-closure.json'})
  from aeris_runtime.pipeline_contract import require_closed_contract
  proof=require_closed_contract();self.assertEqual((proof['sites'],proof['owners'],proof['futureBytes']),(265,14,60686336))

class Slot(unittest.TestCase):
 def test_only_m803_added(self):
  old=module(BASE/'mission16.py','l14_mission16')
  from aeris_runtime.mission16 import SLOTS
  self.assertEqual(set(SLOTS)-set(old.SLOTS),{'m803'});self.assertEqual(SLOTS['m803'],180);self.assertEqual({k:SLOTS[k]for k in old.SLOTS},old.SLOTS)
 def test_forensic_close_scope(self):
  from aeris_runtime.product_runtime import WorkbenchRuntime
  for name in('m801','m802','m803'):
   fake=type('F',(),{'root':Path('/x')/name,'close_maintenance':lambda s:'CLOSED'})()
   self.assertEqual(WorkbenchRuntime.close_forensic_only(fake),'CLOSED')
  for name in('m804','g107','m903','m904'):
   fake=type('F',(),{'root':Path('/x')/name,'close_maintenance':lambda s:'CLOSED'})()
   with self.assertRaisesRegex(RuntimeError,'PRODUCT_RUNTIME_FORENSIC_ONLY_SCOPE'):WorkbenchRuntime.close_forensic_only(fake)
 def test_forensic_paths_name_m803_like_m802(self):
  t=(PORT/'product_runtime.py').read_text();f=(PORT/'forensic_h10.py').read_text()
  self.assertEqual(t.count("('m801','m802','m803')"),3);self.assertNotIn("('m801','m802')",t);self.assertEqual(t.count("'m801','m802','m803','m901'"),1)
  self.assertEqual(f.count("owner.root.name in('m801','m802','m803')"),1);self.assertNotIn("('m801','m802')",f)
 def test_capture_entry_scope_strings(self):
  t=(B/'root-capture-l15.py').read_text()
  for s in("choices=('m803',)","prior.get('priorSlot')=='g107'","run='beta-rc01-forensic-capture03'","intent.get('slot')=='m803'","scope=R/'evidence/betarc01/m803'",
           "'aeris-linuxport01-l15-root-forensic-prerequisite'","'ROOT_COLD_VERIFIED_G107_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'","'aeris-linuxport01-l15-root-forensic-intent'"):
   self.assertEqual(t.count(s),1,s)
  for s in("'m801'","'m802'","'g105'","'g106'","forensic-capture01","forensic-capture02","l12-root-forensic","G106_FAILED","aeris-h10-root-forensic"):self.assertNotIn(s,t)

# The runtime-l14 behaviour tests, run on the runtime-l15 package (already imported above, so the l14 test module's
# own sys.path entry does not replace it). Its Derivation class compares l14 with l13 and is not repeated here.
assert Path(aeris_runtime.__file__).parent==PORT,aeris_runtime.__file__
_l14=module(L14/'test-linuxport14.py','test_linuxport14_behaviour')
class L14Contract(_l14.Contract):pass
class L14Qualification(_l14.Qualification):pass
class L14StartAndDomain(_l14.StartAndDomain):pass
class L14ArchiveCheck(_l14.ArchiveCheck):pass
class L14SDKBoot(_l14.SDKBoot):pass
del _l14

class Package(unittest.TestCase):
 def test_behaviour_tests_use_the_l15_package(self):
  from aeris_runtime import continuation_l13,native17,product_runtime
  for m in(continuation_l13,native17,product_runtime):self.assertEqual(Path(m.__file__).parent,PORT,m.__name__)

if __name__=='__main__':unittest.main(verbosity=2)
