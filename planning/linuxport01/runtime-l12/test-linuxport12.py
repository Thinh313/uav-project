"""LINUXPORT01 runtime-l12: runtime-l11 plus the m802 forensic capture slot and the 40 MiB artifact cap (team code).

Checks that every changed file is its runtime-l11 original plus exactly the patches in
l12_patches.py, that the capture entry is the owner's root-capture-h10.py plus the
declared patches and uses no registry decoder, that the graph and writer contract change
only as declared, and that the cap is 40 MiB everywhere it is bound, with the same
+20 MiB disk reserve the owner's 13 -> 20 MiB raise used and nothing else in the policy
changed. Run from the tree root (the bind mount) with Python 3.14 -B.
"""
from pathlib import Path
import ast,hashlib,json,os,sys,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R),str(B)]
import l12_patches as P
L11=R/'planning/linuxport01/runtime-l11';PORT=B/'source/aeris_runtime';BASE=L11/'source/aeris_runtime'
REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json'};MIB=2**20
def sha(b):return hashlib.sha256(b).hexdigest()
def files(root):return{p.relative_to(root).as_posix()for p in Path(root).rglob('*')if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.json.gz')}
def load(p):return json.loads(Path(p).read_bytes())

class Derivation(unittest.TestCase):
 def test_source_is_l11_plus_declared_patches_only(self):
  self.assertEqual(files(PORT),files(BASE))
  differ={n for n in files(BASE)if(PORT/n).read_bytes()!=(BASE/n).read_bytes()}
  self.assertEqual(differ,set(P.MODULES)|{P.POLICY}|REGENERATED)
  for name,patches in P.MODULES.items():
   with self.subTest(name=name):self.assertEqual((PORT/name).read_text(),P.apply((BASE/name).read_text(),patches,name))
  self.assertEqual((PORT/P.POLICY).read_bytes(),P.policy((BASE/P.POLICY).read_bytes()))
 def test_capture_entry_is_owner_original_plus_declared_patches(self):
  owner=R/'planning/betarc01/runtime-h10/root-capture-h10.py'
  self.assertEqual((R/P.CAPTURE_SOURCE).read_bytes(),owner.read_bytes())
  self.assertEqual((B/'root-capture-l12.py').read_text(),P.apply(owner.read_text(),P.CAPTURE,'root-capture-l12.py'))
  self.assertEqual((B/'root-capture-l12.py').stat().st_mode&0o111,owner.stat().st_mode&0o111)
 def test_other_top_level_files_unchanged_from_l11(self):
  new={'l12_patches.py','root-capture-l12.py','test-linuxport12.py','prepare-source-gate.py','test-caps03.py'}
  top={p.name for p in B.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}
  self.assertEqual(top-new,{p.name for p in L11.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}-{'l11_patches.py','test-linuxport11.py','prepare-source-gate.py','test-caps03.py'})
  for name in top-new:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(L11/name).read_bytes())
  self.assertEqual((B/'test-caps03.py').read_text(),P.apply((L11/'test-caps03.py').read_text(),P.TEST_CAPS,'test-caps03.py'))
  self.assertEqual((B/'prepare-source-gate.py').read_text(),P.gate((L11/'prepare-source-gate.py').read_text()))
 def test_capture_entry_uses_no_registry_decoder(self):
  tree=ast.parse((B/'root-capture-l12.py').read_text());mods={n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}
  self.assertFalse([m for m in mods if m and('reconcile'in m or'continuation'in m)])
 def test_graph_changes_only_the_capture_entry(self):
  a=load(BASE/'assets/product-input-closure.json');b=load(PORT/'assets/product-input-closure.json')
  self.assertLessEqual(len(b['entrypoints']),8);self.assertEqual(len(b['entrypoints']),len(a['entrypoints']))
  self.assertEqual({e.replace('runtime-l11','runtime-l12').replace('root-capture-h10.py','root-capture-l12.py')for e in a['entrypoints']},set(b['entrypoints']))
  self.assertFalse([e for e in b['entrypoints']if'runtime-l11'in e or e.endswith('root-capture-h10.py')])
  ra={k.replace('runtime-l11/root-capture-h10.py','CAPTURE').replace('runtime-l11','L'):v for k,v in a['pins'].items()}
  rb={k.replace('runtime-l12/root-capture-l12.py','CAPTURE').replace('runtime-l12','L'):v for k,v in b['pins'].items()}
  self.assertEqual(set(ra),set(rb));self.assertEqual({k for k in ra if ra[k]!=rb[k]},{'planning/linuxport01/CAPTURE'})
  self.assertEqual(b['pins']['planning/linuxport01/runtime-l12/root-capture-l12.py'],sha((B/'root-capture-l12.py').read_bytes()))
  self.assertEqual(b['pins']['planning/linuxport01/contract-l10/m801-continuation-pin.json'],'b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d')
  ren=lambda v:json.loads(json.dumps(v).replace('runtime-l11/root-capture-h10.py','runtime-l12/root-capture-l12.py').replace('runtime-l11','runtime-l12'))
  for k in('readInputs','moduleInputs','aliases'):self.assertEqual(sorted(map(json.dumps,ren(a[k])))if type(a[k])is list else ren(a[k]),sorted(map(json.dumps,b[k]))if type(b[k])is list else b[k],k)
 def test_writer_contract_unchanged_from_l11(self):
  a=load(BASE/'assets/pipeline-writer-pins.json');b=load(PORT/'assets/pipeline-writer-pins.json')
  # The one comment line added at the top of candidate.py moves its sites down by exactly one line.
  self.assertEqual(len(a['sites']),len(b['sites']));self.assertEqual(len(b['sites']),261)
  for x,y in zip(a['sites'],b['sites']):
   if x['module']=='aeris_runtime/candidate.py':x=dict(x,line=x['line']+1)
   self.assertEqual(x,y)
  for k in('owners','envelope','frozenLeafSHA256','metadataBoundary','format','version'):self.assertEqual(a[k],b[k],k)
  # healthContract differs only in the artifact cap numbers and the candidate.py source SHA.
  x=json.loads(json.dumps(a['healthContract']));y=json.loads(json.dumps(b['healthContract']));ca=x['artifactCapPolicy'];cb=y['artifactCapPolicy']
  self.assertEqual((ca['capBytes'],cb['capBytes']),(20*MIB,40*MIB));ca['capBytes']=cb['capBytes']
  self.assertEqual(set(ca['resourcePolicyReserves'].values()),{20*MIB});self.assertEqual(set(cb['resourcePolicyReserves'].values()),{40*MIB});ca['resourcePolicyReserves']=cb['resourcePolicyReserves']
  for r,s in zip(ca['actorSourceBindings'],cb['actorSourceBindings']):
   self.assertEqual((r['capBytes'],s['capBytes']),(20*MIB,40*MIB));r['capBytes']=s['capBytes']
   if r['module']=='candidate':self.assertEqual((r['sourceSHA256'],s['sourceSHA256']),(sha((BASE/'candidate.py').read_bytes()),sha((PORT/'candidate.py').read_bytes())));r['sourceSHA256']=s['sourceSHA256']
  self.assertEqual(x,y)
  from aeris_runtime.pipeline_contract import require_closed_contract
  proof=require_closed_contract();self.assertEqual((proof['sites'],proof['owners'],proof['futureBytes']),(261,14,60686336))

class Cap(unittest.TestCase):
 def test_cap_is_40MiB_and_bound_everywhere(self):
  from aeris_runtime import candidate,host_health,monitor,emulator,preview10
  from aeris_runtime.pipeline_contract import artifact_cap_contract
  self.assertEqual(candidate.CAP,40*MIB)
  for n in[0,20*MIB+1,40*MIB]:self.assertTrue(candidate.artifact_cap_admitted(n))
  for n in[-1,True,40.0,None,40*MIB+1]:self.assertFalse(candidate.artifact_cap_admitted(n))
  for m in(host_health,monitor,emulator,preview10):self.assertEqual(m.ARTIFACT_CAP,40*MIB,m.__name__)
  c=artifact_cap_contract();self.assertEqual(c['capBytes'],40*MIB);self.assertEqual(set(c['resourcePolicyReserves'].values()),{40*MIB})
  text=(PORT/'candidate.py').read_text();self.assertNotIn('ARTIFACT20MiB',text);self.assertEqual(text.count('ARTIFACT40MiB'),2)
 def test_policy_only_adds_20MiB_reserve_and_team_block(self):
  from aeris_runtime import policy
  from aeris_runtime.pipeline_contract import metadata_cap_contract
  a=load(BASE/P.POLICY);b=load(PORT/P.POLICY);d=20*MIB
  self.assertEqual(set(b)-set(a),{'linuxport01ArtifactCapAmendment'});self.assertEqual(b['betarc01HostCapAmendment'],a['betarc01HostCapAmendment'])
  for k in a:
   if k not in('cases','campaign'):self.assertEqual(a[k],b[k],k)
  for s in a['cases']:
   x=a['cases'][s];y=b['cases'][s];self.assertEqual({k:v for k,v in x.items()if k!='budget'},{k:v for k,v in y.items()if k!='budget'})
   x=x['budget'];y=y['budget']
   self.assertEqual({k:v for k,v in x.items()if k not in('categories','taskHardPeakBytes','requiredFreeBytes')},{k:v for k,v in y.items()if k not in('categories','taskHardPeakBytes','requiredFreeBytes')})
   self.assertEqual({k:y['categories'][k]-v for k,v in x['categories'].items()},{k:(d if k=='newIsolatedAPKAndArchiveReserve'else 0)for k in x['categories']})
   self.assertEqual(y['taskHardPeakBytes']-x['taskHardPeakBytes'],d);self.assertEqual(y['requiredFreeBytes']-x['requiredFreeBytes'],d)
   self.assertEqual(sum(y['categories'].values()),y['taskHardPeakBytes']);self.assertEqual(y['requiredFreeBytes'],y['taskHardPeakBytes']+10*2**30+256*MIB)
   self.assertFalse(policy.case_budget(y['requiredFreeBytes']-1,int(s))['admitted']);self.assertTrue(policy.case_budget(y['requiredFreeBytes'],int(s))['admitted'])
  self.assertEqual({k:b['campaign'][k]-v for k,v in a['campaign'].items()if type(v)is int and not isinstance(v,bool)},{k:(d if k in('newIsolatedAPKAndArchiveReserve','taskHardPeakBytes')else 0)for k,v in a['campaign'].items()if type(v)is int and not isinstance(v,bool)})
  self.assertEqual({k:v for k,v in a['campaign'].items()if not(type(v)is int and not isinstance(v,bool))},{k:v for k,v in b['campaign'].items()if not(type(v)is int and not isinstance(v,bool))})
  self.assertEqual(metadata_cap_contract()['capBytes'],100*MIB)
 def test_team_authorization_record(self):
  b=load(PORT/P.POLICY)['linuxport01ArtifactCapAmendment'];p=R/b['authorizationPath'];raw=p.read_bytes();v=json.loads(raw)
  self.assertEqual(sha(raw),b['authorizationSHA256']);self.assertEqual(b['authorizationSHA256'],P.AUTHORIZATION_SHA)
  self.assertEqual((v['format'],v['status'],v['ownerAuthorized'],v['artifactCapBytes'],v['previousArtifactCapBytes'],v['metadataCapChanged']),('aeris-linuxport01-team-resource-cap-update','TEAM_RESEARCHER_APPROVED_NOT_OWNER',False,40*MIB,20*MIB,False))
  o=R/v['ownerAuthorizationOfPreviousCap']['path'];self.assertEqual(sha(o.read_bytes()),v['ownerAuthorizationOfPreviousCap']['sha256']);self.assertEqual(load(o)['artifactCapBytes'],20*MIB)
  self.assertEqual(b['ownerAuthorized'],False);self.assertEqual(b['artifactCapBytes'],40*MIB)

class Slot(unittest.TestCase):
 def test_only_m802_added(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('l11_mission16',BASE/'mission16.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  from aeris_runtime.mission16 import SLOTS
  self.assertEqual(set(SLOTS)-set(old.SLOTS),{'m802'});self.assertEqual(SLOTS['m802'],180);self.assertTrue(all(SLOTS[k]==v for k,v in old.SLOTS.items()))
 def test_forensic_close_scope(self):
  from aeris_runtime.product_runtime import WorkbenchRuntime
  for name in('m801','m802'):
   fake=type('F',(),{'root':Path('/x')/name,'close_maintenance':lambda s:'CLOSED'})()
   self.assertEqual(WorkbenchRuntime.close_forensic_only(fake),'CLOSED')
  for name in('m803','g106','m901'):
   fake=type('F',(),{'root':Path('/x')/name,'close_maintenance':lambda s:'CLOSED'})()
   with self.assertRaisesRegex(RuntimeError,'PRODUCT_RUNTIME_FORENSIC_ONLY_SCOPE'):WorkbenchRuntime.close_forensic_only(fake)
 def test_capture_entry_scope_strings(self):
  t=(B/'root-capture-l12.py').read_text()
  for s in("choices=('m802',)","prior.get('priorSlot')=='g106'","run='beta-rc01-forensic-capture02'","intent.get('slot')=='m802'","scope=R/'evidence/betarc01/m802'",
           "'aeris-linuxport01-l12-root-forensic-prerequisite'","'ROOT_COLD_VERIFIED_G106_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'","'aeris-linuxport01-l12-root-forensic-intent'"):
   self.assertEqual(t.count(s),1,s)
  for s in("'m801'","'g105'","forensic-capture01","aeris-h10-root-forensic-prerequisite","aeris-h10-root-forensic-intent"):self.assertNotIn(s,t)

if __name__=='__main__':unittest.main(verbosity=2)
