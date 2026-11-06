"""LINUXPORT01 runtime-l16: runtime-l15 plus the G1 chain m905/m906/g108 from the m803 contract and the
continuation shape of VERIFY_NATIVE_UNUSED17 (team code).

Checks that every changed file is its runtime-l15 (or owner) original plus exactly the patches in
l16_patches.py: the slot tables, the new team module continuation_l16.py (continuation_l13.py moved to
contract-l16), the two new entries, the source gate, and the team copy native-unused-l16.mjs of the owner's
VERIFY_NATIVE_UNUSED17 module, which the product graph reaches through one new alias. The owner's Node loader is
run for real on the generated graph and must link the team copy. The runtime-l14/l13 behaviour tests (contract
admission, two-boot proof check with the 64 MiB Private bound, G1 start with the owner's original as backup17,
cold domain check, archive_check on real data, SDK boot check) are repeated on the m803 state. The 200 ms writer
limit, the 40 MiB cap and the owner modules are unchanged.
Run from the tree root (the bind mount) with Python 3.14 -B.
"""
from pathlib import Path
import ast,contextlib,copy,hashlib,inspect,io,json,os,shutil,subprocess,sys,tarfile,tempfile,time,types,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R),str(B)]
import l16_patches as P
L15=R/'planning/linuxport01/runtime-l15';L13=R/'planning/linuxport01/runtime-l13';PORT=B/'source/aeris_runtime';BASE=L15/'source/aeris_runtime'
REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json'}
M803=R/'evidence/betarc01/m803/sessions/beta-rc01-forensic-capture03/native-restart-metadata.tar'
M802=R/'evidence/betarc01/m802/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
M801=R/'evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
BASELINE=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
G106START=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-restart-metadata.tar'
RETAINED=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-original-before-quarantine.tar'
PIN16='15039006e060302d18acf0f45ce5304bdfb78d6fa1c4b8883f4016ee2f57ac95';PIN12='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'
M803SHA='5ddb603c6250d7564bdce4d331433ec77d80611d75a52e8e28dea37dd325feb3';OWNER_UNUSED_SHA='dea941f32c63b1dd1420322684c8071861eeb85846684619b78985a4ec140511'
NODE='/home/thinh/.local/bin/node';UNUSED_KEY='planning/betarc01/tar_profile_h7/native-unused-h7.mjs';UNUSED_TEAM='planning/linuxport01/runtime-l16/native-unused-l16.mjs'
HAVE=M803.is_file()and M802.is_file()and M801.is_file()and BASELINE.is_file()
def sha(b):return hashlib.sha256(b).hexdigest()
def files(root):return{p.relative_to(root).as_posix()for p in Path(root).rglob('*')if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.json.gz')}
def graph(p):return json.loads((p/'assets/product-input-closure.json').read_bytes())

class Derivation(unittest.TestCase):
 def test_source_is_l15_plus_declared_patches_only(self):
  self.assertEqual(files(PORT)-files(BASE),{P.NEW_MODULE});self.assertEqual(files(BASE)-files(PORT),set())
  differ={n for n in files(BASE)if(PORT/n).read_bytes()!=(BASE/n).read_bytes()}
  self.assertEqual(differ,set(P.MODULES)|REGENERATED)
  for name,patches in P.MODULES.items():
   with self.subTest(name=name):self.assertEqual((PORT/name).read_text(),P.apply((BASE/name).read_text(),patches,name))
  self.assertEqual((PORT/P.NEW_MODULE).read_text(),P.apply_counted((BASE/P.NEW_MODULE_SOURCE).read_text(),P.NEW_MODULE_PATCHES,P.NEW_MODULE))
 def test_entries_and_node_copy_are_originals_plus_declared_patches(self):
  for src,dst,patches in((P.QUALIFY_SOURCE,'root-qualify-l16.py',P.QUALIFY),(P.NATIVE_SOURCE,'root-native-l16.py',P.NATIVE),(P.NODE_SOURCE,P.NODE,P.NODE_PATCHES)):
   with self.subTest(entry=dst):
    self.assertEqual((B/dst).read_text(),P.apply((R/src).read_text(),patches,dst));self.assertEqual((B/dst).stat().st_mode&0o111,(R/src).stat().st_mode&0o111)
  # The chain back: the l15 entries are the l13 ones unchanged, and the owner's verifier module is unchanged.
  for n in('root-qualify-l13.py','root-native-l13.py'):self.assertEqual((L15/n).read_bytes(),(L13/n).read_bytes())
  self.assertEqual(sha((R/P.NODE_SOURCE).read_bytes()),OWNER_UNUSED_SHA)
 def test_other_top_level_files_unchanged_from_l15(self):
  new={'l16_patches.py','root-native-l16.py','root-qualify-l16.py','test-linuxport16.py','prepare-source-gate.py',P.NODE}
  top={p.name for p in B.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}
  self.assertEqual(top-new,{p.name for p in L15.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}-{'l15_patches.py','test-linuxport15.py','prepare-source-gate.py'})
  for name in top-new:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(L15/name).read_bytes())
  self.assertEqual((B/'prepare-source-gate.py').read_text(),P.gate((L15/'prepare-source-gate.py').read_text()))
 def test_guards_and_owner_modules_unchanged(self):
  for name in('continuation_l13.py','product_writer.py','candidate.py','installclosure_h4.py','native17.py','adoption17.py','node_alias_h9.py','assets/resource-policy.json'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(BASE/name).read_bytes())
  from aeris_runtime import candidate,product_writer
  self.assertEqual(candidate.CAP,40*2**20);self.assertEqual(product_writer.RPC_NS,200_000_000)
  self.assertIn("TimeoutError('PRODUCT_WRITER_COMMITTED_AFTER200MS_NO_RETRY')",(PORT/'product_writer.py').read_text())
 def test_no_75_file_decoder_in_team_code(self):
  for p in(PORT/P.NEW_MODULE,B/'root-native-l16.py',B/'root-qualify-l16.py'):
   with self.subTest(path=p.name):
    tree=ast.parse(p.read_text());mods={n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}
    self.assertFalse([m for m in mods if m and('reconcile'in m or'continuation_l11'in m or'continuation_l13'in m)])
 def test_new_module_has_no_l13_or_m802_values_left(self):
  # Code only: the module docstring names continuation_l13 and g107 on purpose.
  t=(PORT/P.NEW_MODULE).read_text();body='\n'.join(l for l in t[t.index('"""',3)+3:].splitlines()if not l.lstrip().startswith('#'))
  for s in('contract-l12','m802','M802','m903','m904','g107',"'L13_",'l13-','L13_METADATA',PIN12,'nativeLifecycleContinuationL13','resumeL13'):self.assertNotIn(s,body,s)
  self.assertIn(PIN16,body);self.assertEqual(body.count('retained_originals17'),2);self.assertIn("RUNS={'m905':'beta-rc01-sdk-continuation05','m906':'beta-rc01-sdk-continuation06'}",body)
 def test_graph_pins_contract_entries_and_the_alias(self):
  a,g=graph(BASE),graph(PORT);c=R/'planning/linuxport01/contract-l16'
  self.assertEqual(g['pins']['planning/linuxport01/contract-l16/continuation_l16.py'],sha((c/'continuation_l16.py').read_bytes()))
  self.assertEqual(g['pins']['planning/linuxport01/contract-l16/m803-continuation-pin.json'],PIN16)
  self.assertEqual(g['pins'][UNUSED_TEAM],sha((B/P.NODE).read_bytes()))
  self.assertEqual(len(g['entrypoints']),8);self.assertIn('planning/linuxport01/runtime-l16/root-native-l16.py',g['entrypoints']);self.assertIn('planning/linuxport01/runtime-l16/root-qualify-l16.py',g['entrypoints'])
  self.assertFalse([e for e in g['entrypoints']if'runtime-l15'in e or e.endswith(('root-native-l13.py','root-qualify-l13.py'))])
  self.assertEqual({k:v for k,v in g['aliases'].items()if a['aliases'].get(k)!=v},{UNUSED_KEY:UNUSED_TEAM});self.assertEqual(set(a['aliases'])-set(g['aliases']),set())
  n=lambda k:k.replace('runtime-l15','L').replace('runtime-l16','L')
  ra={n(k):v for k,v in a['pins'].items()};rb={n(k):v for k,v in g['pins'].items()}
  self.assertEqual({k for k in ra if k in rb and ra[k]!=rb[k]},set())
  self.assertEqual(set(ra)-set(rb),{UNUSED_KEY,'planning/linuxport01/L/root-native-l13.py','planning/linuxport01/L/root-qualify-l13.py'})
  self.assertEqual(set(rb)-set(ra),{'planning/linuxport01/L/native-unused-l16.mjs','planning/linuxport01/L/root-native-l16.py','planning/linuxport01/L/root-qualify-l16.py','planning/linuxport01/contract-l16/continuation_l16.py','planning/linuxport01/contract-l16/m803-continuation-pin.json'})
  e=lambda k:n(k).replace('root-native-l13.py','root-native-ENTRY').replace('root-native-l16.py','root-native-ENTRY').replace('root-qualify-l13.py','root-qualify-ENTRY').replace('root-qualify-l16.py','root-qualify-ENTRY')
  self.assertEqual(set(map(e,a['moduleInputs']))-set(map(e,g['moduleInputs'])),{UNUSED_KEY});self.assertEqual(set(map(e,g['moduleInputs']))-set(map(e,a['moduleInputs'])),{'planning/linuxport01/L/native-unused-l16.mjs'})
  self.assertEqual(set(a['readInputs'])-set(g['readInputs']),{UNUSED_KEY});self.assertEqual(set(g['readInputs'])-set(a['readInputs']),{'planning/linuxport01/contract-l16/continuation_l16.py','planning/linuxport01/contract-l16/m803-continuation-pin.json'})
 def test_writer_contract_only_adds_the_new_module_sites(self):
  a=json.loads((BASE/'assets/pipeline-writer-pins.json').read_bytes());b=json.loads((PORT/'assets/pipeline-writer-pins.json').read_bytes())
  for k in('owners','envelope','frozenLeafSHA256','metadataBoundary','format','version','healthContract'):
   with self.subTest(k=k):self.assertEqual(a[k],b[k])
  key=lambda r:(r['module'],r['function'],r['call'],r['siteSHA256']);sa={key(r)for r in a['sites']};sb={key(r)for r in b['sites']}
  self.assertEqual(sa-sb,set());self.assertEqual(sorted((m,f,c)for m,f,c,_ in sb-sa),[('aeris_runtime/continuation_l16.py','resume_continuation','write')]*3+[('aeris_runtime/continuation_l16.py','rich_table','open')])
  self.assertEqual(len(b['sites']),269)

class Slots(unittest.TestCase):
 def test_slot_tables_and_generation_budget(self):
  from aeris_runtime import mission16,rc01
  self.assertEqual({s:mission16.SLOTS[s]for s in('m905','m906','g108')},{'m905':180,'m906':180,'g108':180})
  self.assertEqual((rc01.KINDS['g108'],rc01.REMAINING['g108'],rc01.GENERATIONS['g108'],rc01.ARCHIVE_BOUNDARY['g108']),('native',0,2,rc01.ARCHIVE_BOUNDARY['g107']))
  # The m803 state has 4 active journals: g108 needs 2 more and keeps the repair reserve of 2, exactly the limit of 8.
  f=rc01.generation_forecast(4,'g108',remaining_generations=0);self.assertEqual(f['projectedMaximumActive'],8)
  with self.assertRaises(ValueError):rc01.generation_forecast(5,'g108',remaining_generations=0)
  with self.assertRaises(ValueError):rc01.generation_forecast(4,'g108',remaining_generations=1)
 def test_entry_slots_and_routing(self):
  self.assertIn("choices=('g108',)",(B/'root-native-l16.py').read_text());self.assertIn("choices=('m905','m906')",(B/'root-qualify-l16.py').read_text())
  t=(PORT/'product_runtime.py').read_text();i=t.index("elif self.root.name in('m905','m906'):");self.assertIn('from .continuation_l16 import verify_sdk',t[i:i+120])
  self.assertEqual(t.count("'m903','m904','m905','m906'"),4)

class UnusedVerifier(unittest.TestCase):
 """The team copy of VERIFY_NATIVE_UNUSED17: only the shape lines differ from the owner's module."""
 def test_only_the_declared_shape_lines_differ(self):
  owner=(R/P.NODE_SOURCE).read_text();team=(B/P.NODE).read_text()
  a,b=owner.split('need('),team.split('need(');self.assertEqual(len(a),len(b))
  code=lambda x:x[:x.index("')",x.index("'UNUSED17_"))+2]if"'UNUSED17_"in x else x
  changed={i for i,(x,y)in enumerate(zip(a,b))if x!=y};conditions={i for i in changed if i and code(a[i])!=code(b[i])}
  # Header + import (0); the three shape checks; two neighbours where only code after the check moved (counter, generation name).
  self.assertEqual(conditions,{i for i,x in enumerate(a)if any(c in x[:x.find(';')if';'in x else len(x)]for c in("'UNUSED17_SOURCE_BOUND_REGISTRY_CLOSE'","'UNUSED17_EXACT_ACTIVE_SET'","'UNUSED17_ALL_ORIGINAL_ARCHIVE_INDEX_CONTROL_JOIN'"))})
  self.assertEqual(len(changed-conditions-{0}),2)
  for s in("'UNUSED17_SOURCE_BOUND_REGISTRY_CLOSE'","'UNUSED17_EXACT_ACTIVE_SET'","'UNUSED17_ALL_ORIGINAL_ARCHIVE_INDEX_CONTROL_JOIN'"):self.assertEqual(owner.count(s),1);self.assertEqual(team.count(s),1)
  self.assertNotIn('===10',team);self.assertIn("need(r.raw.equals(AJ02_MAGIC),'UNUSED17_ALL_ORIGINAL_JOURNALS_UNUSED')",team)
 def test_old_active_set_is_the_pinned_new_generations(self):
  pin=json.loads((R/'planning/linuxport01/contract-l16/m803-continuation-pin.json').read_bytes())
  self.assertEqual(list(P.OLD_ACTIVE),pin['registry']['newGenerations']);self.assertEqual(pin['registry']['counters']['committedGenerations'],12)
  self.assertIn("CONTINUATION_PRIOR_GENERATIONS=12",(B/P.NODE).read_text())

@unittest.skipUnless(Path(NODE).is_file(),'node')
class NodeLoader(unittest.TestCase):
 """The owner's verified loader, run for real on the generated graph (synthetic source-only manifest, no actors)."""
 def run_node(self,g,script):
  m={'native':{'productKind':'BETASIM_INTEGRATED'},'simulationOnly':True,'productSourceSHA256':copy.deepcopy(g['pins']),'productInputClosure':copy.deepcopy(g)};raw=json.dumps(m,sort_keys=True,separators=(',',':'))
  with tempfile.TemporaryDirectory(prefix='node-',dir=B)as tmp:
   p=Path(tmp)/'synthetic-source-only-manifest.json';p.write_text(raw+'\n')
   return subprocess.run([NODE,'--import',str(R/'planning/betarc01/node_alias_h9/verified-loader.mjs'),'--input-type=module','-e',script,'--','--manifest',str(p),'--candidate-sha',sha(raw.encode())],cwd=R,capture_output=True,timeout=30,env={'PATH':'/usr/bin:/bin'})
 def test_server_links_the_team_verifier_through_the_alias(self):
  script="""import{selectedBoundary as b}from'./planning/betarc01/node_alias_h9/verified-loader.mjs';import{fileURLToPath,pathToFileURL}from'node:url';import path from'node:path';const u=pathToFileURL(path.join(process.cwd(),'planning/betarc01/tar_profile_h7/native-unused-h7.mjs')).href;const r=b.resolveSpecifier(u);await import('./planning/betarc01/product/server-codec09c.mjs');const m=await import('./planning/nativejournal17/native-cold17.mjs');console.log(JSON.stringify({resolved:path.relative(process.cwd(),fileURLToPath(r)),team:m.verifyNativeUnused17.toString().includes('CONTINUATION_OLD_ACTIVE'),aliases:Object.keys(b.aliases).length}));"""
  p=self.run_node(graph(PORT),script);self.assertEqual(p.returncode,0,p.stderr.decode()[-2000:])
  self.assertEqual(json.loads(p.stdout),{'resolved':UNUSED_TEAM,'team':True,'aliases':8})
 def test_l15_graph_still_links_the_owner_verifier(self):
  script="""const m=await import('./planning/nativejournal17/native-cold17.mjs');console.log(JSON.stringify({team:m.verifyNativeUnused17.toString().includes('CONTINUATION_OLD_ACTIVE')}));"""
  p=self.run_node(graph(BASE),script);self.assertEqual(p.returncode,0,p.stderr.decode()[-2000:]);self.assertEqual(json.loads(p.stdout),{'team':False})
 def test_alias_key_still_held_is_refused(self):
  g=graph(PORT);g['pins'][UNUSED_KEY]=OWNER_UNUSED_SHA
  p=self.run_node(g,"console.log(1)");self.assertNotEqual(p.returncode,0);self.assertIn('PRODUCT_LOADER_H9_ALIAS_UNHELD_CHAIN_OR_OLD_FALLBACK',p.stderr.decode())

def manifest():
 g=graph(PORT)
 return{'native':{'APK_SHA256':'eed4ba78'+'0'*56,'sourceSHA256':'c'*64},'productInputClosure':g}

class FakeStore:
 """Original command / receipt reader stand-in: refs are dict keys."""
 def __init__(self):self.cmd={};self.raw={};self.diag=[]
 def command(self,store,ref):return self.cmd[ref]
 def read_ref(self,store,ref):return self.raw[ref]
 def read_receipts(self,store,kind):return self.diag if kind=='diagnostic'else[]
 def original_command(self,store,ref,args):row,argv,remote,out=self.cmd[ref];assert remote==args,(remote,args);return row,out,remote

@unittest.skipUnless(HAVE,'team m803/m802/m801/g105 evidence of the work tree')
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from aeris_runtime import continuation_l16 as C;cls.C=C;cls.m=manifest();cls.pin=json.loads((R/C.PIN).read_bytes())
 def test_m803_admitted(self):
  v=self.C.contract_check(M803,sha(M803.read_bytes()),self.m)
  self.assertEqual((v['registryHead'],v['activeJournals'],v['archivedJournals'],v['pendingTransactions']),(self.pin['registry']['head'],4,8,0));self.assertIs(v['decoder75FileUsed'],False)
  self.assertFalse([m for m in sys.modules if'reconcile'in m])
 def test_earlier_states_refused(self):
  for p in(M802,M801,G106START,SESSION1,BASELINE):
   with self.subTest(p=p.parent.parent.parent.name+'/'+p.name),self.assertRaisesRegex(ValueError,'CONTINUATION_L16_MISSING'):self.C.contract_check(p,sha(p.read_bytes()),self.m)
 def test_wrong_tar_sha_refused(self):
  with self.assertRaisesRegex(ValueError,'RAW_SHA'):self.C.contract_check(M803,'0'*64,self.m)
 def test_contract_not_pinned_in_graph_refused(self):
  m=copy.deepcopy(self.m);m['productInputClosure']['pins'][self.C.CONTRACT]='0'*64
  with self.assertRaisesRegex(ValueError,'L16_CONTRACT_SOURCE_PIN'):self.C.contract_check(M803,sha(M803.read_bytes()),m)
 def test_m803_prior(self):
  boot,path=self.C.m803_prior();rep=json.loads((R/'evidence/betarc01/m803/reports/forensic-capture-h10.json').read_bytes())
  self.assertEqual(path,rep['baseAPK']);self.assertNotEqual(boot,rep['priorKernelBootUUID']);self.assertEqual(boot,'734d948a-7377-403c-9d1a-905d77881dc9')
 def test_receiver_plan_is_current_archive_intent(self):
  r=self.C.receiver_originals(M803,sha(M803.read_bytes()));self.assertEqual(len({x['generation']for x in r['value']['originals']}),8);self.assertEqual(r['reportSHA256'],self.pin['receiver']['sha256'])
  with self.assertRaisesRegex(ValueError,'L16_ARCHIVE_PLAN_IS_CURRENT_INTENT_RECORD'):self.C.receiver_originals(RETAINED,sha(RETAINED.read_bytes()))

@unittest.skipUnless(HAVE,'team m803/m802/m801 evidence of the work tree')
class Qualification(unittest.TestCase):
 """require_qualification on synthetic proofs in a temporary evidence root; the Private refs are copies of the real m802 TAR."""
 def setUp(self):
  from aeris_runtime import continuation_l16 as C,rc01;self.C=C;self.rc01=rc01;self.d=Path(tempfile.mkdtemp());(self.d/'evidence/betarc01').mkdir(parents=True)
  self.saved=(C.repository,rc01.repository);C.repository=rc01.repository=lambda:self.d;refs=[]
  pin=self.d/C.PIN;pin.parent.mkdir(parents=True);shutil.copy(R/C.PIN,pin)
  for s in C.SLOTS:
   for k in('Observation','Guardian','SDKProcess','Private'):
    if k=='Private':p=self.tar(s);shutil.copy(M803,p)
    else:p=self.d/'evidence/betarc01'/s/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(k.encode())
    refs.append({'role':s+k,'ref':self.ref(p)})
  self.good={'format':C.QUALIFICATION,'version':1,'status':'ROOT_COLD_VERIFIED_CONTRACT_TWO_NORMAL_SDK_BOOTS_NOT_FLIGHT','candidateSHA256':'a'*64,'slots':['m905','m906'],'contractPinSHA256':C.PIN_SHA,'authorityRestorable':False,'SDKExitZeroNoForcedKillBoth':True,'actualKernelBootUUIDs':['11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222'],'originalEvidence':refs}
 def tearDown(self):self.C.repository,self.rc01.repository=self.saved;shutil.rmtree(self.d)
 def tar(self,slot,run=None,name='native-restart-metadata.tar'):
  p=self.d/'evidence/betarc01'/slot/'sessions'/(run or self.C.RUNS[slot])/name;p.parent.mkdir(parents=True,exist_ok=True);return p
 def ref(self,p):return{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
 def with_ref(self,role,ref):return{**self.good,'originalEvidence':[{'role':r['role'],'ref':ref if r['role']==role else r['ref']}for r in self.good['originalEvidence']]}
 def run_proof(self,v,candidate='a'*64):
  raw=json.dumps(v).encode();p=self.d/'evidence/betarc01'/('proof-%s.json'%sha(raw)[:8]);p.write_bytes(raw);return self.C.require_qualification(p,sha(raw),candidate)
 def private(self,slot):return next(r['ref']for r in self.good['originalEvidence']if r['role']==slot+'Private')
 def test_positive_with_the_real_m803_tar_for_both_boots(self):
  for s in self.C.SLOTS:self.assertEqual((self.private(s)['bytes'],self.private(s)['sha256']),(268800,M803SHA))
  self.assertEqual(self.run_proof(self.good)['status'],'SOURCE_BOUND_L16_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE')
 def test_the_owner_bound_alone_refuses_this_tar(self):
  # Why the runtime-l14 bound is kept: the unchanged owner check with its default bound refuses the m803 state TAR.
  self.assertGreater(M803.stat().st_size,262144)
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.rc01.ref_file(self.private('m905'))
 def test_negatives_kept_from_l13(self):
  cases={'l11 proof m901/m902':dict(format='aeris-linuxport01-l11-root-contract-sdk-cold-acceptance',slots=['m901','m902']),'l11 slots':dict(slots=['m901','m902']),
   'contract-l10 pin':dict(contractPinSHA256='b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d'),'other candidate':dict(candidateSHA256='b'*64),
   'not both exit 0':dict(SDKExitZeroNoForcedKillBoth=False),'same boot twice':dict(actualKernelBootUUIDs=['11111111-1111-1111-1111-111111111111']*2),
   'authority':dict(authorityRestorable=True),'seven refs':dict(originalEvidence=self.good['originalEvidence'][:7]),
   'l13 proof':dict(format='aeris-linuxport01-l13-root-contract-sdk-cold-acceptance',slots=['m903','m904']),'contract-l12 pin':dict(contractPinSHA256=PIN12)}
  for name,change in cases.items():
   with self.subTest(case=name),self.assertRaises(ValueError):self.run_proof({**self.good,**change})
 def test_other_roles_keep_the_owner_bound(self):
  for role in('m905Observation','m906Guardian','m905SDKProcess'):
   with self.subTest(role=role):
    p=self.d/'evidence/betarc01/big'/role;p.parent.mkdir(exist_ok=True);shutil.copy(M803,p)
    with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.run_proof(self.with_ref(role,self.ref(p)))
 def test_private_at_another_path_refused(self):
  m803cap=self.d/'evidence/betarc01/m803/sessions/beta-rc01-forensic-capture03/native-restart-metadata.tar';m803cap.parent.mkdir(parents=True);shutil.copy(M803,m803cap)
  other=self.tar('m905',name='other.tar');shutil.copy(M803,other);l11=self.tar('m905',run='beta-rc01-sdk-continuation01');shutil.copy(M803,l11)
  cases={'the other boot TAR':('m905Private',self.private('m906')),'the m803 capture itself':('m906Private',self.ref(m803cap)),'other name in the run':('m905Private',self.ref(other)),'l11 run name':('m905Private',self.ref(l11))}
  for name,(role,ref)in cases.items():
   with self.subTest(case=name),self.assertRaisesRegex(ValueError,'^L16_PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE$'):self.run_proof(self.with_ref(role,ref))
 def test_private_of_another_state_refused(self):
  # The 83-file m801 TAR (250,880 B) fits the owner's bound, but it is not the pinned state.
  p=self.tar('m906');shutil.copy(M801,p)
  with self.assertRaisesRegex(ValueError,'^L16_PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE$'):self.run_proof(self.with_ref('m906Private',self.ref(p)))
  for change in({'bytes':268799},{'sha256':'0'*64},{'path':None}):
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'^L16_PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE$'):self.run_proof(self.with_ref('m905Private',{**self.private('m905'),**change}))
 def test_private_changed_bytes_refused(self):
  p=self.tar('m906');b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(bytes(b))
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SHA$'):self.run_proof(self.good)
 def test_private_symlink_or_hard_link_refused(self):
  p=self.tar('m905');elsewhere=self.d/'evidence/elsewhere.tar';p.rename(elsewhere);p.symlink_to(elsewhere)
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.run_proof(self.good)
  p.unlink();os.link(elsewhere,p)
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.run_proof(self.good)
 def test_changed_pin_refused(self):
  pin=self.d/self.C.PIN;pin.write_bytes(pin.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'^L16_CONTRACT_PIN_SHA$'):self.run_proof(self.good)
 def test_changed_other_evidence_refused(self):
  (self.d/'evidence/betarc01/m906/Guardian').write_bytes(b'GuardiaX')
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SHA$'):self.run_proof(self.good)
 def test_bound_and_runs_match_the_harness(self):
  # 64 MiB is the harness's own bound for this root TAR capture; RUNS are the run names the qualification entry uses.
  self.assertEqual(self.C.PRIVATE_MAXIMUM,64*2**20);self.assertIn("st_size<=64*2**20,'BOUNDED_PRIVATE_TAR'",(PORT/'installclosure_h4.py').read_text())
  self.assertIn("run='beta-rc01-sdk-continuation05'if a.slot=='m905'else'beta-rc01-sdk-continuation06'",(B/'root-qualify-l16.py').read_text())

@unittest.skipUnless(HAVE and RETAINED.is_file(),'team m803/m802/m801/g105/g106 evidence of the work tree')
class StartAndDomain(unittest.TestCase):
 """resume_continuation, continuation_observation and verify_continuation_domain with a fake device and store."""
 def setUp(self):
  from aeris_runtime import continuation_l16 as C;from aeris_runtime.metadata_budget import encoded;self.C=C;self.m=manifest();self.digest=sha(encoded(self.m).rstrip(b'\n'))
  self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore();self.saved={k:getattr(C,k)for k in('command','read_ref','read_receipts')}
  C.command=self.fs.command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;shutil.copy(RETAINED,self.store.parent/'native-original-before-quarantine.tar')
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def fake(self,tar,*,argv=None,cold=b'ABSENT\n',apk=None,order=True):
  fs=self.fs;apk=apk or self.m['native']['APK_SHA256'];t=[0]
  def row(n):t[0]+=10;return{'startedHostNs':t[0],'endedHostNs':t[0]+1}
  base='/data/app/x/vn.rtr.aeris.betasim09-y/base.apk';target=self.store.parent/'native-restart-metadata.tar'
  owner=types.SimpleNamespace(digest=self.digest,manifest=self.m,root=self.d/'g108',writes=[],write=lambda n,v:owner.writes.append(n),budget=types.SimpleNamespace(write=lambda o,p,b:owner.writes.append(Path(p).name)))
  receipts=[]
  class Device:
   root=self.store;serial='emulator-5582';last_command_ref='privref';budget=types.SimpleNamespace(operation=lambda q:contextlib.nullcontext())
   store=types.SimpleNamespace(receipt=lambda n,v:(fs.diag.append(v),receipts.append(n),n)[2])
   def _cold_absence(s,deadline):k='cold%d'%len(fs.cmd);fs.cmd[k]=(row(k),None,['sh','-c',self.C.COLD],cold);return k
   def _installed_sha(s,want,deadline):fs.cmd['path']=(row('p'),None,['pm','path',self.C.PACKAGE],('package:'+base+'\n').encode());fs.cmd['sha']=(row('h'),None,['sha256sum',base],(apk+'  '+base+'\n').encode());return'path','sha'
   def _export_private(s,run,path,**k):
    shutil.copy(tar,target);r=row('cap');cap={'captureComplete':True,'failure':None,'exit':0,'fullOriginalFiles':True,'path':str(target),'bytesRetained':target.stat().st_size,'stderrRef':'err','argvRef':'argv','startedHostNs':r['startedHostNs'],'finishedHostNs':r['endedHostNs']}
    if not order:cap['startedHostNs']=0
    fs.diag.append(cap);fs.raw.update(capref=json.dumps(cap).encode(),err=b'',argv=json.dumps(argv or['adb','-s','emulator-5582','exec-out','run-as',self.C.PACKAGE,'tar','-cf','-','files']).encode())
    return{'path':str(target),'sha256':sha(target.read_bytes()),'bytes':target.stat().st_size,'captureReceiptRef':'capref'}
   def command(s,args,**k):fs.cmd['privref']=(row('pw'),None,['run-as',self.C.PACKAGE,'pwd','-P'],('/data/user/0/'+self.C.PACKAGE+'\n').encode());return('/data/user/0/'+self.C.PACKAGE+'\n').encode()
  native=types.SimpleNamespace(retained_inventory_ref='retained')
  case={'device':Device(),'context':{'run':'run'},'root':self.d,'native':native}
  return owner,case,receipts
 def run_start(self,tar,**k):
  owner,case,receipts=self.fake(tar,**k);self.C.resume_continuation(owner,case,deadline_ns=0);return owner,case,receipts
 def test_start_from_m803_uses_the_owner_original_as_backup17(self):
  from aeris_runtime.adoption17 import retained_originals17
  from aeris_runtime.native17 import workspace17
  owner,case,receipts=self.run_start(M803);pin=json.loads((R/self.C.PIN).read_bytes());o=retained_originals17()
  self.assertEqual(case['admin17']['registryHead'],pin['registry']['head']);self.assertIs(case['admin17']['reconciledFromOriginalG103'],False)
  self.assertEqual(case['admin17']['originalReceiptTARSHA256'],pin['source']['sha256']);self.assertEqual(case['resumeL16']['backup']['sha256'],pin['source']['sha256'])
  # The fix: backup17 is the n02 pre-migration original (as resume_existing), not the current capture.
  self.assertEqual(case['backup17'],o['backup']);self.assertNotEqual(case['backup17']['sha256'],pin['source']['sha256']);self.assertEqual(case['coldProof17'],o['coldProof'])
  self.assertEqual(case['workspaceBefore17'],workspace17(o['backup']['path']));self.assertEqual(case['receiver17']['reportSHA256'],o['receiver']['reportSHA256'])
  self.assertIs(case['native'].application_domain['nativeLifecycleContinuationL16'],True);self.assertNotIn('nativeLifecycleContinuationL11',case['native'].application_domain)
  self.assertFalse(getattr(case['device'],'migration17_verified',False));self.assertEqual(receipts,['native17-continuation-l16.json','application-domain17-continuation-l16.json'])
  self.assertIn('native17-receiver-original.json',owner.writes)
  with self.assertRaisesRegex(ValueError,'L16_RESUME_ONCE'):self.C.resume_continuation(owner,case,deadline_ns=0)
 def test_refusals_happen_before_any_write(self):
  cases={'87-file m802 state':(dict(tar=M802),'CONTINUATION_L16_MISSING'),'83-file m801 state':(dict(tar=M801),'CONTINUATION_L16_MISSING'),'75-file state':(dict(tar=BASELINE),'CONTINUATION_L16_MISSING'),
   'app running':(dict(tar=M803,cold=b'PRESENT\n'),'L16_CURRENT_COLD_SELECTED_APK'),'other APK':(dict(tar=M803,apk='f'*64),'L16_CURRENT_COLD_SELECTED_APK'),
   'root tar instead of run-as':(dict(tar=M803,argv=['adb','-s','emulator-5582','exec-out','tar','-C','/data/user/0/x','-cf','-','files']),'L16_ORIGINAL_CURRENT_TAR_CAPTURE'),
   'capture before APK check':(dict(tar=M803,order=False),'L16_RESUME_CAPTURE_SOURCE_ORDER')}
  for name,(k,error)in cases.items():
   with self.subTest(case=name):
    self.fs.__init__();tar=k.pop('tar');owner,case,receipts=self.fake(tar,**k)
    with self.assertRaisesRegex(ValueError,error):self.C.resume_continuation(owner,case,deadline_ns=0)
    self.assertEqual((owner.writes,receipts),([],[]));self.assertNotIn('admin17',case);self.assertNotIn('backup17',case)
 def test_retained_original_with_other_receiver_refused_before_any_write(self):
  from aeris_runtime import adoption17
  real=adoption17.retained_originals17
  def other():o=real();o=dict(o);o['receiver']=dict(o['receiver'],reportSHA256='0'*64);return o
  adoption17.retained_originals17=other
  try:
   owner,case,receipts=self.fake(M803)
   with self.assertRaisesRegex(ValueError,'L16_RETAINED_ORIGINALS_ARE_PINNED_RECEIVER'):self.C.resume_continuation(owner,case,deadline_ns=0)
   self.assertEqual((owner.writes,receipts),([],[]));self.assertNotIn('backup17',case)
  finally:adoption17.retained_originals17=real
 def test_cold_domain_check(self):
  owner,case,receipts=self.run_start(M803);fs=self.fs;domain=case['native'].application_domain
  legacy=self.store.parent/'android-api-retained';legacy.mkdir();old=self.C.rich_table(self.store.parent/'native-original-before-quarantine.tar')
  inv={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceStopped':True,'notNewDeviceGrowthCredit':True,'sourceDUCommandRef':'du','allocatedBytes':4096,
   'sourceOriginalTAR':{'path':str(self.store.parent/'native-original-before-quarantine.tar'),'sha256':sha(RETAINED.read_bytes())},'plaintextFileLengthBytes':sum(v['bytes']for v in old['files'].values()),'entries':len(old['files'])+len(old['directories'])}
  fs.diag.append(inv);fs.raw.update(retained=json.dumps(inv).encode(),dom=json.dumps(domain).encode(),**{'native17-continuation-l16.json':json.dumps(case['resumeL16']).encode()});fs.cmd['du']=({},None,['run-as','vn.rtr.aeris.mission','du','-k','-s','files'],b'4\tfiles\n')
  self.assertIs(self.C.verify_continuation_domain(self.store,'dom',self.m)['nativeLifecycleContinuationL16'],True)
  for name,change in{'l11 flag only':{'nativeLifecycleContinuationL16':None,'nativeLifecycleContinuationL11':True},'l13 flag only':{'nativeLifecycleContinuationL16':None,'nativeLifecycleContinuationL13':True},'old resume flag only':{'nativeLifecycleContinuationL16':None,'nativeLifecycleResumeH7':True},'other candidate':{'candidateSHA256':'0'*64}}.items():
   with self.subTest(case=name):
    bad={**domain,**change};fs.diag.append(bad);fs.raw['bad']=json.dumps(bad).encode()
    with self.assertRaisesRegex(ValueError,'L16_ORIGINAL_CONTINUATION_DOMAIN'):self.C.verify_continuation_domain(self.store,'bad',self.m)
 def test_domain_dispatch_in_product_native09(self):
  from aeris_runtime import product_native09
  src=Path(product_native09.__file__).read_text();i=src.index("nativeLifecycleContinuationL16");self.assertLess(src.index("nativeLifecycleContinuationL11"),src.index("nativeLifecycleContinuationL13"));self.assertLess(src.index("nativeLifecycleContinuationL13"),i);self.assertIn('continuation_l16 import verify_continuation_domain',src[i:i+200])

@unittest.skipUnless(HAVE,'team m803/m802/m801/g105 evidence of the work tree')
class ArchiveCheck(unittest.TestCase):
 """The owner's native17.archive_check (unchanged) with his real registry verifier, on the real m803 TAR (the pinned state,
 with the open journal). Only the stage that has no workspace-receipt check ('migration') is used; capture_command is
 replaced by a plain subprocess run of the same argv (the owner's metadata budget is not under test here)."""
 def setUp(self):
  from aeris_runtime import native17 as N;from aeris_runtime.adoption17 import retained_originals17;self.N=N;self.o=retained_originals17()
  self.saved=N.capture_command;self.d=Path(tempfile.mkdtemp());(self.d/'reports').mkdir()
  def capture(budget,owner,argv,*,deadline_ns,stdout_limit,stderr_limit):
   r=subprocess.run(argv,capture_output=True,timeout=120);return{'stdout':r.stdout[:stdout_limit],'stderr':r.stderr[:stderr_limit],'pid':1,'exit':r.returncode,'captureComplete':len(r.stdout)<=stdout_limit and len(r.stderr)<=stderr_limit,'failure':None}
  N.capture_command=capture
  self.pin=json.loads((R/'planning/linuxport01/contract-l16/m803-continuation-pin.json').read_bytes());recv=(R/self.pin['receiver']['path']).read_bytes();(self.d/'reports/native17-receiver-original.json').write_bytes(recv)
  plan=(R/self.pin['receiver']['path']).with_name('native17-plan-original.txt').read_bytes();self.receiver={'value':json.loads(recv),'planSHA256':sha(plan),'reportSHA256':sha(recv)}
 def tearDown(self):self.N.capture_command=self.saved;shutil.rmtree(self.d)
 def check(self,backup,export):
  budget=types.SimpleNamespace(tick=lambda k:None,operation=lambda q:contextlib.nullcontext(),write=lambda kind,path,raw:Path(path).write_bytes(raw))
  owner=types.SimpleNamespace(root=self.d,digest='a'*64,budget=budget,write=lambda n,v:(self.d/'reports'/n).write_text(json.dumps(v)))
  case={'admin17':{'registryHead':self.pin['registry']['head']},'backup17':{'path':str(backup),'sha256':sha(Path(backup).read_bytes())},'receiver17':self.receiver,'device':types.SimpleNamespace()}
  for f in(self.d/'reports').glob('native17-migration-*'):f.unlink()
  return self.N.archive_check(owner,case,{'path':str(export),'sha256':sha(Path(export).read_bytes())},'migration',deadline_ns=time.monotonic_ns()+120_000_000_000),case
 def test_previous_capture_as_backup17_fails_like_g106_attempt1(self):
  # The continuation_l11 mistake on this state: the previous capture (m802) as backup17; its registry grew by two rows.
  with self.assertRaisesRegex(ValueError,r'^NATIVE17_ALL_OLD_PRIVATE_BYTES_PRESERVED:files/product-input-registry17/highwater\.aj17$'):self.check(M802,M803)
 def test_owner_original_passes_on_the_new_state_with_the_open_journal(self):
  proof,case=self.check(self.o['backup']['path'],M803)
  self.assertEqual((proof['status'],proof['registryHead'],proof['activeJournals'],proof['archivedJournals'],proof['pendingTransactions']),('SOURCE_BOUND_ORIGINAL_ARCHIVE_INDEX_JOIN_VERIFIED',self.pin['registry']['head'],4,8,0))
  stage=json.loads((self.d/'reports/native17-migration-proof.json').read_bytes());self.assertIs(stage['originalPrivateBytesConserved'],True);self.assertEqual(stage['oldFileCount'],70)
  self.assertIs(case['device'].migration17_verified,True)
 def test_owner_original_still_refuses_a_changed_original_file(self):
  from aeris_runtime.native17 import table
  before=table(self.o['backup']['path']);name=sorted(n for n in before if not n.startswith(('files/product-input','files/betasim-workspace01/HEAD')))[0]
  dst=self.d/'changed.tar'
  with tarfile.open(M803)as t,tarfile.open(dst,'w',format=tarfile.GNU_FORMAT)as o:
   for m in t:
    b=t.extractfile(m).read()if m.isfile()else None
    if m.name==name:b=bytes([b[0]^1])+b[1:]
    o.addfile(m,io.BytesIO(b)if b is not None else None)
  with self.assertRaisesRegex(ValueError,'^NATIVE17_ALL_OLD_PRIVATE_BYTES_PRESERVED:'+name.replace('.','[.]')+'$'):self.check(self.o['backup']['path'],dst)

@unittest.skipUnless(HAVE,'team m803/m802/m801/g105 evidence of the work tree')
class SDKBoot(unittest.TestCase):
 """verify_sdk (close_maintenance for m905/m906) with a fake original-command store; package parsing stubbed."""
 PRIOR='99999999-9999-9999-9999-999999999999';BOOT='12345678-1234-1234-1234-123456789abc'
 def setUp(self):
  from aeris_runtime import continuation_l16 as C;self.C=C;self.m=manifest();self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore()
  self.saved={k:getattr(C,k)for k in('original_command','read_ref','read_receipts','package_state','safe_code_path')}
  C.original_command=self.fs.original_command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;C.package_state=lambda out,broken:out.decode().strip();C.safe_code_path=lambda p:p+'/base.apk'
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def proof(self,tar,*,slot='m905',argv=None,boot=None,profile=None):
  fs=self.fs;C=self.C;base='/data/app/x/pkg';apk=base+'/base.apk';t=[100]
  def put(k,args,out):t[0]+=10;fs.cmd[k]=({'startedHostNs':t[0],'endedHostNs':t[0]+1},None,args,out);return k
  target=self.store.parent/'native-restart-metadata.tar';shutil.copy(tar,target);digest=sha(target.read_bytes())
  prep={'actualUID0':True,'confirmation':'READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','kernelBootUUID':self.BOOT};fs.diag.append(prep);fs.raw['prep']=json.dumps(prep).encode();samples=[]
  start=t[0]
  for i,off in enumerate((0,30)):
   t[0]=start+off*1_000_000_000;due=t[0]+5
   refs={k:put('%s%d'%(k,i),a,o)for k,a,o in(('boot',C.BOOT,((boot or self.BOOT)+'\n').encode()),('user',['am','get-current-user'],b'0\n'),('cold',['sh','-c',C.COLD],b'ABSENT\n'),('path',['pm','path',C.PACKAGE],('package:'+apk+'\n').encode()),('sha',['sha256sum',apk],(self.m['native']['APK_SHA256']+'  '+apk+'\n').encode()),('dump',['dumpsys','package',C.PACKAGE],base.encode()))}
   samples.append({'offsetSeconds':off,'targetHostNs':due,'commandRefs':refs})
  uid=put('uid',['id','-u'],b'0\n');st=put('stat',['sh','-c',C.STAT],b'directory 10141 10141 0771\n');cold=put('fcold',['sh','-c',C.COLD],b'ABSENT\n')
  cap={'captureComplete':True,'failure':None,'exit':0,'bytesRetained':target.stat().st_size,'path':str(target),'fullOriginalFiles':True,'stderrRef':'err','argvRef':'argv','finishedHostNs':t[0]+5};fs.diag.append(cap)
  fs.raw.update(cap=json.dumps(cap).encode(),err=b'',argv=json.dumps(argv or['adb','-s','emulator-5582','exec-out','tar','-C',C.PRIVATE,'-cf','-','files']).encode());t[0]+=10;after=put('after',['sh','-c',C.COLD],b'ABSENT\n')
  from aeris_runtime.tar_profile_h7 import native_tar
  v={'candidateSHA256':'d'*64,'preparationRef':'prep','baseAPK':base,'samples':samples,'priorKernelBootUUID':self.PRIOR,'finalUIDRef':uid,'finalStatRef':st,'finalColdRef':cold,'afterBackupColdRef':after,
   'rootPrivateBackup':{'path':str(target),'sha256':digest,'captureReceiptRef':'cap'},'tarProfileObservation':{'observation':profile or native_tar(target,digest,allow_empty_active=True)['transportProfile'],'originalCaptureRef':'cap'}}
  owner=types.SimpleNamespace(digest='d'*64,manifest=self.m,repo=self.d,root=types.SimpleNamespace(name=slot),case={'device':types.SimpleNamespace(root=self.store,adb='adb')})
  return owner,{'sdkOnlyH7':v}
 def test_m905_on_m803_state(self):
  owner,p=self.proof(M803);r=self.C.verify_sdk(owner,p);self.assertIs(r['originalPrivateBytesConserved'],True);self.assertEqual(r['continuation']['TARSHA256'],sha(M803.read_bytes()));self.assertEqual(r['actualKernelBootUUID'],self.BOOT)
 def test_m906_needs_same_private_table_as_m905(self):
  rep=self.d/'evidence/betarc01/m905/reports/coldboot-h7.json';rep.parent.mkdir(parents=True)
  for prior,ok in((M803,True),(M802,False)):
   with self.subTest(prior=prior.name):
    rep.write_text(json.dumps({'rootPrivateBackup':{'path':str(prior)}}));self.fs.__init__();owner,p=self.proof(M803,slot='m906')
    if ok:self.C.verify_sdk(owner,p)
    else:
     with self.assertRaisesRegex(ValueError,'L16_SECOND_BOOT_WHOLE_PRIVATE_UNCHANGED'):self.C.verify_sdk(owner,p)
 def test_refusals(self):
  cases={'l11 slot m901':(dict(slot='m901'),'L16_SDK_ONLY_EXACT_CURRENT_SOURCE'),'l13 slot':(dict(slot='m903'),'L16_SDK_ONLY_EXACT_CURRENT_SOURCE'),'87-file m802 state':(dict(tar=M802),'CONTINUATION_L16_MISSING'),'83-file m801 state':(dict(tar=M801),'CONTINUATION_L16_MISSING'),
   'run-as tar instead of root tar':(dict(argv=['adb','-s','emulator-5582','exec-out','run-as',self.C.PACKAGE,'tar','-cf','-','files']),'L16_SDK_ONLY_FIXED_ROOT_TAR'),
   'boot not new':(dict(boot=self.PRIOR),'L16_SDK_ONLY_FRESH_STABLE_BOOT'),'profile not observed':(dict(profile={'x':1}),'L16_EXPLICIT_PROFILE_OBSERVATION')}
  for name,(k,error)in cases.items():
   with self.subTest(case=name):
    self.fs.__init__();tar=k.pop('tar',M803);owner,p=self.proof(tar,**k)
    with self.assertRaisesRegex(ValueError,error):self.C.verify_sdk(owner,p)

class Package(unittest.TestCase):
 def test_behaviour_tests_use_the_l16_package(self):
  import aeris_runtime
  from aeris_runtime import continuation_l16,native17,product_runtime
  for m in(aeris_runtime,continuation_l16,native17,product_runtime):self.assertEqual(Path(m.__file__).parent,PORT,m.__name__)

if __name__=='__main__':unittest.main(verbosity=2)
