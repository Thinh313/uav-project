"""LINUXPORT01 runtime-l18: runtime-l17 plus (A) the Linux port of the G2/G3 path and (B) the G1 chain m909/m910/g110 from
the same m803 contract (team code; the user's decisions are quoted in l18_patches.py, none is the owner's).

Derivation: every changed file is its runtime-l17 original plus exactly the patches in l18_patches.py; the new module
continuation_l18.py is continuation_l17.py moved to the new slots; json_forwarder.py is derived from the pinned tool copy
sitl_json_udp_forwarder.py; root-owner-h10.py (the G2/G3 entry) is byte-identical to the owner's.
A. G2/G3 on Linux, on fakes and on loopback only (no Docker, no AP, no emulator, no harness run):
 - AP identity under ARM user emulation (launch.ap_identity_l18) on container answers shaped like log 2026-11-11/03, and the
   real host-query allowlist (commands.HostCommands._call) for the five query forms;
 - the Linux physics kernel: declared in LEAVES, loaded from the tree, always required for the backend, named by the provider
   only; the G2 run config and the AP argv (JSON:172.17.0.1) built by the real policy and ap_supervisor code;
 - the JSON forwarder: ready hand-off through the captured stdout, the real forward() on 127.0.0.1 with ephemeral ports;
 - the forwarder as a third owned child: real resources.py, disposal.py and raw_export.py code on fake processes.
 Not tested here (later probes or real runs): the forwarder's real bind on 172.17.0.1/docker0, the clock probe's UDP path,
 the identity queries against a real container, the backend with journal and fsync.
B. G1 chain: the runtime-l17 behaviour tests (contract admission, two-boot proof check with the 64 MiB Private bound, G1 start
 with the owner's original as backup17, cold domain check, archive_check on real data, SDK boot check) repeated for the new
 slots; the m908 prior is read back from the real m908 raw records of runtime-l17.
The two pin assets (product-input-closure.json, pipeline-writer-pins.json) are rewritten by the source gate. The tests of
their content (classes AfterSourceGate and NodeLoader) are skipped, with that reason, until the gate has run; then the whole
file must be run again. The 200 ms writer limit, the 40 MiB cap and every guard not named in l18_patches.py are unchanged.
Run with Python 3.14 -B from the tree root at the owner's pinned path /Users/os/Downloads/AI technique/aeris (the bind mount
of work-l1/aeris): the owner's adoption17.retained_originals17 binds that path, so from any other path six cases (classes
StartAndDomain and ArchiveCheck) stop with NATIVE17_RETAINED_ORIGINAL_COLD_BACKUP.
"""
from pathlib import Path
import ast,contextlib,copy,hashlib,io,json,os,platform,re,shutil,signal,socket,subprocess,sys,tarfile,tempfile,time,types,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R),str(B)]
import l18_patches as P
L17=R/'planning/linuxport01/runtime-l17';PORT=B/'source/aeris_runtime';BASE=L17/'source/aeris_runtime'
def sha(b):return hashlib.sha256(b).hexdigest()
REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json'}
M803=R/'evidence/betarc01/m803/sessions/beta-rc01-forensic-capture03/native-restart-metadata.tar'
M802=R/'evidence/betarc01/m802/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
M801=R/'evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
M908=R/'evidence/betarc01/m908';M908_RUN='beta-rc01-sdk-continuation08'
BASELINE=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
G106START=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-restart-metadata.tar'
RETAINED=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-original-before-quarantine.tar'
PIN16='15039006e060302d18acf0f45ce5304bdfb78d6fa1c4b8883f4016ee2f57ac95';PIN12='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'
M803SHA='5ddb603c6250d7564bdce4d331433ec77d80611d75a52e8e28dea37dd325feb3';M908BOOT='d685407d-0690-44ed-b6da-1987f3c2aff3'
NODE='/home/thinh/.local/bin/node';UNUSED_KEY='planning/betarc01/tar_profile_h7/native-unused-h7.mjs';UNUSED_TEAM='planning/linuxport01/runtime-l16/native-unused-l16.mjs'
OWNER_UNUSED_SHA='dea941f32c63b1dd1420322684c8071861eeb85846684619b78985a4ec140511'
HAVE=M803.is_file()and M802.is_file()and M801.is_file()and BASELINE.is_file()and(M908/'reports/coldboot-h7.json').is_file()
def files(root):return{p.relative_to(root).as_posix()for p in Path(root).rglob('*')if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.json.gz')}
def graph(p):return json.loads((p/'assets/product-input-closure.json').read_bytes())
ENTRIES=('planning/linuxport01/runtime-l18/root-native-l18.py','planning/linuxport01/runtime-l18/root-qualify-l18.py')
GATED=all(e in graph(PORT)['entrypoints']for e in ENTRIES)
NOT_GATED='the source gate (prepare-source-gate.py --write) has not rewritten the two pin assets of runtime-l18 yet'

class Derivation(unittest.TestCase):
 def test_source_is_l17_plus_declared_patches_only(self):
  self.assertEqual(files(PORT)-files(BASE),{P.NEW_MODULE,P.FORWARDER_MODULE});self.assertEqual(files(BASE)-files(PORT),set())
  differ={n for n in files(BASE)if(PORT/n).read_bytes()!=(BASE/n).read_bytes()}
  self.assertEqual(differ-REGENERATED,set(P.MODULES)|{P.ASSET})
  for name,patches in P.MODULES.items():
   with self.subTest(name=name):self.assertEqual((PORT/name).read_text(),P.apply((BASE/name).read_text(),patches,name))
  self.assertEqual((PORT/P.ASSET).read_text(),P.apply((BASE/P.ASSET).read_text(),P.ASSET_PATCHES,P.ASSET))
  self.assertEqual((PORT/P.NEW_MODULE).read_text(),P.apply((BASE/P.NEW_MODULE_SOURCE).read_text(),P.NEW_MODULE_PATCHES,P.NEW_MODULE))
  self.assertEqual(sha((B/P.FORWARDER_TOOL).read_bytes()),P.FORWARDER_TOOL_SHA256);self.assertEqual((PORT/P.FORWARDER_MODULE).read_text(),P.forwarder((B/P.FORWARDER_TOOL).read_text()))
 def test_entries_are_l17_entries_plus_declared_patches(self):
  for src,dst,patches in((P.QUALIFY_SOURCE,'root-qualify-l18.py',P.QUALIFY),(P.NATIVE_SOURCE,'root-native-l18.py',P.NATIVE)):
   with self.subTest(entry=dst):
    self.assertEqual((B/dst).read_text(),P.apply((R/src).read_text(),patches,dst));self.assertEqual((B/dst).stat().st_mode&0o111,(R/src).stat().st_mode&0o111)
 def test_other_top_level_files_unchanged_from_l17(self):
  new={'l18_patches.py','root-native-l18.py','root-qualify-l18.py','test-linuxport18.py','prepare-source-gate.py',P.FORWARDER_TOOL}
  top={p.name for p in B.iterdir()if p.is_file()};self.assertEqual(Path(P.__file__).resolve(),B/'l18_patches.py')
  self.assertEqual(top-new,{p.name for p in L17.iterdir()if p.is_file()}-{'l17_patches.py','test-linuxport17.py','prepare-source-gate.py'})
  for name in top-new:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(L17/name).read_bytes())
  self.assertEqual((B/'prepare-source-gate.py').read_text(),P.gate((L17/'prepare-source-gate.py').read_text()))
  self.assertEqual([p.name for p in B.iterdir()if p.is_dir()and p.name!='__pycache__'],['source'])
 def test_g2g3_entry_is_byte_identical_to_the_owners(self):
  self.assertEqual((B/'root-owner-h10.py').read_bytes(),(R/'planning/betarc01/runtime-h10/root-owner-h10.py').read_bytes())
  self.assertIn("'planning/linuxport01/runtime-l18/root-owner-h10.py'",(B/'prepare-source-gate.py').read_text())
 def test_guards_owner_modules_alias_and_team_verifier_unchanged(self):
  for name in('continuation_l17.py','continuation_l16.py','continuation_l13.py','product_inputs.py','product_writer.py','candidate.py','installclosure_h4.py','native17.py','adoption17.py','node_alias_h9.py','assets/resource-policy.json',
    'supervisor.py','backend.py','policy.py','identity.py','acceptance_rc01.py','owned_output.py'):
   with self.subTest(name=name):self.assertEqual((PORT/name).read_bytes(),(BASE/name).read_bytes())
  from aeris_runtime import candidate,product_writer
  self.assertEqual(candidate.CAP,40*2**20);self.assertEqual(product_writer.RPC_NS,200_000_000)
  self.assertIn("TimeoutError('PRODUCT_WRITER_COMMITTED_AFTER200MS_NO_RETRY')",(PORT/'product_writer.py').read_text())
  self.assertIn("'"+UNUSED_KEY+"':'"+UNUSED_TEAM+"'",(PORT/'product_inputs.py').read_text())
  self.assertEqual(sha((R/'planning/betarc01/tar_profile_h7/native-unused-h7.mjs').read_bytes()),OWNER_UNUSED_SHA)
 def test_no_75_file_decoder_in_team_code(self):
  for p in(PORT/P.NEW_MODULE,B/'root-native-l18.py',B/'root-qualify-l18.py'):
   with self.subTest(path=p.name):
    tree=ast.parse(p.read_text());mods={n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}
    self.assertFalse([m for m in mods if m and('reconcile'in m or m.endswith(('continuation_l11','continuation_l13','continuation_l16','continuation_l17')))])
    if p.name!=P.NEW_MODULE:self.assertTrue([m for m in mods if m and m.endswith('continuation_l18')])
 def test_new_module_has_no_l17_slot_or_format_values_left(self):
  # Code only: the module docstring names continuation_l17 and g109 on purpose; m908 is the new prior boot.
  t=(PORT/P.NEW_MODULE).read_text();body='\n'.join(l for l in t[t.index('"""',3)+3:].splitlines()if not l.lstrip().startswith('#'))
  for s in('m907','g109','M906','m906','L16_CANDIDATE',"'L17_",'l17-','L17_METADATA','nativeLifecycleContinuationL17','resumeL17','continuation-l17.json','contract-l12',PIN12):self.assertNotIn(s,body,s)
  self.assertIn(PIN16,body);self.assertEqual(body.count('retained_originals17'),2);self.assertIn("RUNS={'m909':'beta-rc01-sdk-continuation09','m910':'beta-rc01-sdk-continuation10'}",body)
  self.assertIn("M908='evidence/betarc01/m908';M908_RUN='beta-rc01-sdk-continuation08';L17_CANDIDATE='"+P.L17_CANDIDATE+"'",body);self.assertIn("CONTRACT='planning/linuxport01/contract-l16/continuation_l16.py'",body)
 def test_only_the_declared_writer_sites_are_new(self):
  # Computed from the two source trees with the owner's own discovery code (not from the pin asset, so it holds before the gate).
  from aeris_runtime import pipeline_contract as pc
  key=lambda r:(r['module'],r['function'],r['call'],r['siteSHA256']);a=pc.sites(BASE,include_source_sha=False);b=pc.sites(PORT,include_source_sha=False);sa={key(r)for r in a};sb={key(r)for r in b}
  self.assertEqual(sa-sb,set());self.assertEqual((len(a),len(b)),(273,282))
  self.assertEqual(sorted((m,f,c)for m,f,c,_ in sb-sa),[('aeris_runtime/continuation_l18.py','resume_continuation','write')]*3+[('aeris_runtime/continuation_l18.py','rich_table','open')]+[('aeris_runtime/json_forwarder.py','forward','bind')]*2+[('aeris_runtime/json_forwarder.py','forward','print')]*2+[('aeris_runtime/launch.py','__call__','bind')])

@unittest.skipUnless(GATED,NOT_GATED)
class AfterSourceGate(unittest.TestCase):
 """The two regenerated pin assets: they must differ from runtime-l17 only by what l18_patches.py declares."""
 def test_both_assets_were_regenerated(self):
  for name in REGENERATED:
   with self.subTest(name=name):self.assertNotEqual((PORT/name).read_bytes(),(BASE/name).read_bytes())
 def test_graph_moves_only_the_entries(self):
  a,g=graph(BASE),graph(PORT);c=R/'planning/linuxport01/contract-l16'
  self.assertEqual(g['pins']['planning/linuxport01/contract-l16/continuation_l16.py'],sha((c/'continuation_l16.py').read_bytes()))
  self.assertEqual(g['pins']['planning/linuxport01/contract-l16/m803-continuation-pin.json'],PIN16)
  self.assertEqual(g['pins'][UNUSED_TEAM],sha((R/UNUSED_TEAM).read_bytes()));self.assertEqual(g['pins'][UNUSED_TEAM],a['pins'][UNUSED_TEAM])
  self.assertEqual(len(g['entrypoints']),8)
  for e in(*ENTRIES,'planning/linuxport01/runtime-l18/root-owner-h10.py'):self.assertIn(e,g['entrypoints'])
  self.assertFalse([e for e in g['entrypoints']if'runtime-l17'in e or e.endswith(('root-native-l17.py','root-qualify-l17.py'))])
  self.assertEqual(g['aliases'],a['aliases'])
  n=lambda k:k.replace('runtime-l17','L').replace('runtime-l18','L')
  ra={n(k):v for k,v in a['pins'].items()};rb={n(k):v for k,v in g['pins'].items()}
  self.assertEqual({k for k in ra if k in rb and ra[k]!=rb[k]},set())
  self.assertEqual(set(ra)-set(rb),{'planning/linuxport01/L/root-native-l17.py','planning/linuxport01/L/root-qualify-l17.py'})
  self.assertEqual(set(rb)-set(ra),{'planning/linuxport01/L/root-native-l18.py','planning/linuxport01/L/root-qualify-l18.py'})
  e=lambda k:n(k).replace('root-native-l17.py','root-native-ENTRY').replace('root-native-l18.py','root-native-ENTRY').replace('root-qualify-l17.py','root-qualify-ENTRY').replace('root-qualify-l18.py','root-qualify-ENTRY')
  self.assertEqual(set(map(e,a['moduleInputs'])),set(map(e,g['moduleInputs'])));self.assertIn(UNUSED_TEAM,g['moduleInputs']);self.assertNotIn(UNUSED_KEY,g['moduleInputs'])
  self.assertEqual(set(a['readInputs']),set(g['readInputs']))
 def test_writer_contract_follows_the_declared_changes_only(self):
  from aeris_runtime import pipeline_contract as pc
  a=json.loads((BASE/'assets/pipeline-writer-pins.json').read_bytes());b=json.loads((PORT/'assets/pipeline-writer-pins.json').read_bytes())
  for k in('metadataBoundary','format','version','healthContract','siteFileHashBinding'):
   with self.subTest(k=k):self.assertEqual(a[k],b[k])
  self.assertEqual(b['sites'],pc.sites(PORT,include_source_sha=False));self.assertEqual(len(b['sites']),282);self.assertEqual(b['sourceSHA256'],pc.source_pins(PORT));self.assertEqual(b['productInputClosure'],graph(PORT))
  self.assertEqual({k:v for k,v in b['frozenLeafSHA256'].items()if k!=P.LINUX_KERNEL},a['frozenLeafSHA256']);self.assertEqual(b['frozenLeafSHA256'][P.LINUX_KERNEL],P.LINUX_KERNEL_SHA256)
  self.assertEqual(b['owners'],pc.owners());self.assertEqual([x['owner']for x,y in zip(b['owners'],a['owners'])if x!=y],['child_output']);self.assertEqual([x['futureBytes']for x in b['owners']],[y['futureBytes']for y in a['owners']])
  ea,eb=a['envelope'],b['envelope'];self.assertEqual([k for k in eb if eb[k]!=ea[k]],['sourceEnforcedCounts']);self.assertEqual(set(ea),set(eb))
  self.assertEqual({k:(ea['sourceEnforcedCounts'][k],v)for k,v in eb['sourceEnforcedCounts'].items()if v!=ea['sourceEnforcedCounts'][k]},{'children':(4,6)});self.assertEqual(eb['totalFutureBytes'],ea['totalFutureBytes'])

class Slots(unittest.TestCase):
 def test_slot_tables_and_generation_budget(self):
  from aeris_runtime import mission16,rc01
  self.assertEqual({s:mission16.SLOTS[s]for s in('m909','m910','g110')},{'m909':180,'m910':180,'g110':180})
  self.assertEqual((rc01.KINDS['g110'],rc01.REMAINING['g110'],rc01.GENERATIONS['g110'],rc01.ARCHIVE_BOUNDARY['g110']),('native',0,2,rc01.ARCHIVE_BOUNDARY['g109']))
  # The restored m803 state has 4 active journals: g110 needs 2 more and keeps the repair reserve of 2, exactly the limit of 8.
  f=rc01.generation_forecast(4,'g110',remaining_generations=0);self.assertEqual(f['projectedMaximumActive'],8)
  with self.assertRaises(ValueError):rc01.generation_forecast(5,'g110',remaining_generations=0)
  with self.assertRaises(ValueError):rc01.generation_forecast(4,'g110',remaining_generations=1)
  # the G2/G3/G4 slots of the owner's table are untouched
  for name in('SLOTS',):
   a=ast.literal_eval(next(l for l in(BASE/'mission16.py').read_text().splitlines()if l.startswith('SLOTS=')).split('=',1)[1]);self.assertEqual({k:v for k,v in mission16.SLOTS.items()if k not in('m909','m910','g110')},a)
 def test_entry_slots_and_routing(self):
  q=(B/'root-qualify-l18.py').read_text()
  self.assertIn("choices=('g110',)",(B/'root-native-l18.py').read_text());self.assertIn("choices=('m909','m910')",q)
  self.assertIn("'ROOT_COLD_VERIFIED_M908_L17_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m909'else",q);self.assertIn(" if a.slot=='m909':\n  priorBoot,path=m908_prior()\n",q)
  t=(PORT/'product_runtime.py').read_text();i=t.index("elif self.root.name in('m909','m910'):");self.assertIn('from .continuation_l18 import verify_sdk',t[i:i+120])
  self.assertEqual(t.count("'m905','m906','m907','m908','m909','m910'"),4)

@unittest.skipUnless(GATED and Path(NODE).is_file(),NOT_GATED+' (or no node)')
class NodeLoader(unittest.TestCase):
 """The owner's verified loader, run for real on the generated graph (synthetic source-only manifest, no actors)."""
 def run_node(self,g,script):
  m={'native':{'productKind':'BETASIM_INTEGRATED'},'simulationOnly':True,'productSourceSHA256':copy.deepcopy(g['pins']),'productInputClosure':copy.deepcopy(g)};raw=json.dumps(m,sort_keys=True,separators=(',',':'))
  with tempfile.TemporaryDirectory(prefix='node-',dir=B)as tmp:
   p=Path(tmp)/'synthetic-source-only-manifest.json';p.write_text(raw+'\n')
   return subprocess.run([NODE,'--import',str(R/'planning/betarc01/node_alias_h9/verified-loader.mjs'),'--input-type=module','-e',script,'--','--manifest',str(p),'--candidate-sha',sha(raw.encode())],cwd=R,capture_output=True,timeout=30,env={'PATH':'/usr/bin:/bin'})
 def test_server_still_links_the_team_verifier_through_the_alias(self):
  script="""import{selectedBoundary as b}from'./planning/betarc01/node_alias_h9/verified-loader.mjs';import{fileURLToPath,pathToFileURL}from'node:url';import path from'node:path';const u=pathToFileURL(path.join(process.cwd(),'planning/betarc01/tar_profile_h7/native-unused-h7.mjs')).href;const r=b.resolveSpecifier(u);await import('./planning/betarc01/product/server-codec09c.mjs');const m=await import('./planning/nativejournal17/native-cold17.mjs');console.log(JSON.stringify({resolved:path.relative(process.cwd(),fileURLToPath(r)),team:m.verifyNativeUnused17.toString().includes('CONTINUATION_OLD_ACTIVE'),aliases:Object.keys(b.aliases).length}));"""
  p=self.run_node(graph(PORT),script);self.assertEqual(p.returncode,0,p.stderr.decode()[-2000:])
  self.assertEqual(json.loads(p.stdout),{'resolved':UNUSED_TEAM,'team':True,'aliases':8})
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

@unittest.skipUnless(HAVE,'team m803/m802/m801/g105/m908 evidence of the work tree')
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from aeris_runtime import continuation_l18 as C;cls.C=C;cls.m=manifest();cls.pin=json.loads((R/C.PIN).read_bytes())
 def test_m803_state_admitted(self):
  v=self.C.contract_check(M803,sha(M803.read_bytes()),self.m)
  self.assertEqual((v['format'],v['registryHead'],v['activeJournals'],v['archivedJournals'],v['pendingTransactions']),('aeris-linuxport01-l18-continuation-admission',self.pin['registry']['head'],4,8,0));self.assertIs(v['decoder75FileUsed'],False)
  self.assertFalse([m for m in sys.modules if'reconcile'in m])
 def test_m908_tar_is_the_pinned_state_and_admitted(self):
  t=M908/'sessions'/M908_RUN/'native-restart-metadata.tar';self.assertEqual(sha(t.read_bytes()),M803SHA);self.assertEqual(self.C.contract_check(t,M803SHA,self.m)['activeJournals'],4)
 def test_earlier_states_refused(self):
  for p in(M802,M801,G106START,SESSION1,BASELINE):
   with self.subTest(p=p.parent.parent.parent.name+'/'+p.name),self.assertRaisesRegex(ValueError,'CONTINUATION_L16_MISSING'):self.C.contract_check(p,sha(p.read_bytes()),self.m)
 def test_wrong_tar_sha_refused(self):
  with self.assertRaisesRegex(ValueError,'RAW_SHA'):self.C.contract_check(M803,'0'*64,self.m)
 def test_contract_not_pinned_in_graph_refused(self):
  m=copy.deepcopy(self.m);m['productInputClosure']['pins'][self.C.CONTRACT]='0'*64
  with self.assertRaisesRegex(ValueError,'L18_CONTRACT_SOURCE_PIN'):self.C.contract_check(M803,sha(M803.read_bytes()),m)
 def test_receiver_plan_is_current_archive_intent(self):
  r=self.C.receiver_originals(M803,sha(M803.read_bytes()));self.assertEqual(len({x['generation']for x in r['value']['originals']}),8);self.assertEqual(r['reportSHA256'],self.pin['receiver']['sha256'])
  with self.assertRaisesRegex(ValueError,'L18_ARCHIVE_PLAN_IS_CURRENT_INTENT_RECORD'):self.C.receiver_originals(RETAINED,sha(RETAINED.read_bytes()))

@unittest.skipUnless(HAVE,'team m908 evidence of the work tree')
class M908Prior(unittest.TestCase):
 """m908_prior on the real m908 raw records of runtime-l17, and on a plain copy with one record changed (never the original)."""
 def setUp(self):
  from aeris_runtime import continuation_l18 as C;self.C=C;self.saved=C.repository
 def tearDown(self):self.C.repository=self.saved
 def test_real_m908(self):
  boot,path=self.C.m908_prior();rep=json.loads((M908/'reports/coldboot-h7.json').read_bytes())
  self.assertEqual(boot,M908BOOT);self.assertEqual(path,rep['baseAPK']);self.assertEqual(rep['candidateSHA256'],P.L17_CANDIDATE);self.assertEqual(self.C.L17_CANDIDATE,P.L17_CANDIDATE)
 def changed(self,rel,edit):
  # Plain copies (never hard links: the harness refuses evidence files with more than one link).
  d=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,d)
  shutil.copytree(M908,d/'evidence/betarc01/m908');pin=d/self.C.PIN;pin.parent.mkdir(parents=True);shutil.copy(R/self.C.PIN,pin)
  p=d/'evidence/betarc01/m908'/rel;raw=p.read_bytes();p.write_bytes(edit(raw));self.assertEqual(sha((M908/rel).read_bytes()),sha(raw))
  self.C.repository=lambda:d;return d
 def js(self,change):return lambda raw:json.dumps({**json.loads(raw),**change}).encode()
 def test_refusals_on_a_copy(self):
  cases={'emulator exit -6':('guardian/closure.json',self.js({'exit':-6}),'L18_M908_ORIGINAL_NORMAL_SDK_CLOSURE'),
   'guardian process exit 1':('diagnostics/guardian-process/close.json',self.js({'exit':1}),'L18_M908_ORIGINAL_NORMAL_SDK_CLOSURE'),
   'exceptional disposal':('guardian/closure.json',self.js({'exceptionalPhysicalDisposal':True}),'L18_M908_ORIGINAL_NORMAL_SDK_CLOSURE'),
   'other candidate':('reports/coldboot-h7.json',self.js({'candidateSHA256':'0'*64}),'L18_M908_QUALIFICATION_SCOPE'),
   'the runtime-l16 candidate':('reports/coldboot-h7.json',self.js({'candidateSHA256':'b07badbf8e31d19d62bba7133ffd9cb34634660eb963f556d132d4a87784840d'}),'L18_M908_QUALIFICATION_SCOPE'),
   'not a qualification boot':('reports/owner-terminal.json',self.js({'status':'FORENSIC_CAPTURE_CLOSED_AWAITING_INDEPENDENT_SEMANTICS_NOT_QUALIFICATION_NOT_G1'}),'L18_M908_QUALIFICATION_SCOPE'),
   'TAR bytes changed':('sessions/'+M908_RUN+'/native-restart-metadata.tar',lambda raw:raw[:-1]+bytes([raw[-1]^1]),'L18_M908_IS_PINNED_STATE')}
  for name,(rel,edit,error)in cases.items():
   with self.subTest(case=name):
    self.changed(rel,edit)
    with self.assertRaisesRegex(ValueError,'^'+error+'$'):self.C.m908_prior()
    self.C.repository=self.saved
  self.assertEqual(self.C.m908_prior()[0],M908BOOT)

@unittest.skipUnless(HAVE,'team m803/m802/m801 evidence of the work tree')
class Qualification(unittest.TestCase):
 """require_qualification on synthetic proofs in a temporary evidence root; the Private refs are copies of the real m803 TAR."""
 def setUp(self):
  from aeris_runtime import continuation_l18 as C,rc01;self.C=C;self.rc01=rc01;self.d=Path(tempfile.mkdtemp());(self.d/'evidence/betarc01').mkdir(parents=True)
  self.saved=(C.repository,rc01.repository);C.repository=rc01.repository=lambda:self.d;refs=[]
  pin=self.d/C.PIN;pin.parent.mkdir(parents=True);shutil.copy(R/C.PIN,pin)
  for s in C.SLOTS:
   for k in('Observation','Guardian','SDKProcess','Private'):
    if k=='Private':p=self.tar(s);shutil.copy(M803,p)
    else:p=self.d/'evidence/betarc01'/s/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(k.encode())
    refs.append({'role':s+k,'ref':self.ref(p)})
  self.good={'format':C.QUALIFICATION,'version':1,'status':'ROOT_COLD_VERIFIED_CONTRACT_TWO_NORMAL_SDK_BOOTS_NOT_FLIGHT','candidateSHA256':'a'*64,'slots':['m909','m910'],'contractPinSHA256':C.PIN_SHA,'authorityRestorable':False,'SDKExitZeroNoForcedKillBoth':True,'actualKernelBootUUIDs':['11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222'],'originalEvidence':refs}
 def tearDown(self):self.C.repository,self.rc01.repository=self.saved;shutil.rmtree(self.d)
 def tar(self,slot,run=None,name='native-restart-metadata.tar'):
  p=self.d/'evidence/betarc01'/slot/'sessions'/(run or self.C.RUNS[slot])/name;p.parent.mkdir(parents=True,exist_ok=True);return p
 def ref(self,p):return{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
 def with_ref(self,role,ref):return{**self.good,'originalEvidence':[{'role':r['role'],'ref':ref if r['role']==role else r['ref']}for r in self.good['originalEvidence']]}
 def run_proof(self,v,candidate='a'*64):
  raw=json.dumps(v).encode();p=self.d/'evidence/betarc01'/('proof-%s.json'%sha(raw)[:8]);p.write_bytes(raw);return self.C.require_qualification(p,sha(raw),candidate)
 def private(self,slot):return next(r['ref']for r in self.good['originalEvidence']if r['role']==slot+'Private')
 def test_positive_with_the_real_m803_tar_for_both_boots(self):
  self.assertEqual((self.C.SLOTS,self.C.QUALIFICATION),(('m909','m910'),'aeris-linuxport01-l18-root-contract-sdk-cold-acceptance'))
  for s in self.C.SLOTS:self.assertEqual((self.private(s)['bytes'],self.private(s)['sha256']),(268800,M803SHA))
  self.assertEqual(self.run_proof(self.good)['status'],'SOURCE_BOUND_L18_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE')
 def test_the_owner_bound_alone_refuses_this_tar(self):
  self.assertGreater(M803.stat().st_size,262144)
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.rc01.ref_file(self.private('m909'))
 def test_negatives_kept_from_l17(self):
  cases={'l17 proof m907/m908':dict(format='aeris-linuxport01-l17-root-contract-sdk-cold-acceptance',slots=['m907','m908']),'l17 slots':dict(slots=['m907','m908']),'l17 format':dict(format='aeris-linuxport01-l17-root-contract-sdk-cold-acceptance'),
   'l16 proof':dict(format='aeris-linuxport01-l16-root-contract-sdk-cold-acceptance',slots=['m905','m906']),'contract-l12 pin':dict(contractPinSHA256=PIN12),
   'contract-l10 pin':dict(contractPinSHA256='b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d'),'other candidate':dict(candidateSHA256='b'*64),
   'not both exit 0':dict(SDKExitZeroNoForcedKillBoth=False),'same boot twice':dict(actualKernelBootUUIDs=['11111111-1111-1111-1111-111111111111']*2),
   'authority':dict(authorityRestorable=True),'seven refs':dict(originalEvidence=self.good['originalEvidence'][:7])}
  for name,change in cases.items():
   with self.subTest(case=name),self.assertRaises(ValueError):self.run_proof({**self.good,**change})
 def test_other_roles_keep_the_owner_bound(self):
  for role in('m909Observation','m910Guardian','m909SDKProcess'):
   with self.subTest(role=role):
    p=self.d/'evidence/betarc01/big'/role;p.parent.mkdir(exist_ok=True);shutil.copy(M803,p)
    with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.run_proof(self.with_ref(role,self.ref(p)))
 def test_private_at_another_path_refused(self):
  m908cap=self.d/'evidence/betarc01/m908/sessions'/M908_RUN/'native-restart-metadata.tar';m908cap.parent.mkdir(parents=True);shutil.copy(M803,m908cap)
  other=self.tar('m909',name='other.tar');shutil.copy(M803,other);l17=self.tar('m909',run='beta-rc01-sdk-continuation07');shutil.copy(M803,l17)
  cases={'the other boot TAR':('m909Private',self.private('m910')),'the m908 boot TAR':('m910Private',self.ref(m908cap)),'other name in the run':('m909Private',self.ref(other)),'l17 run name':('m909Private',self.ref(l17))}
  for name,(role,ref)in cases.items():
   with self.subTest(case=name),self.assertRaisesRegex(ValueError,'^L18_PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE$'):self.run_proof(self.with_ref(role,ref))
 def test_private_of_another_state_refused(self):
  p=self.tar('m910');shutil.copy(M801,p)
  with self.assertRaisesRegex(ValueError,'^L18_PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE$'):self.run_proof(self.with_ref('m910Private',self.ref(p)))
  for change in({'bytes':268799},{'sha256':'0'*64},{'path':None}):
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'^L18_PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE$'):self.run_proof(self.with_ref('m909Private',{**self.private('m909'),**change}))
 def test_private_changed_bytes_refused(self):
  p=self.tar('m910');b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(bytes(b))
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SHA$'):self.run_proof(self.good)
 def test_private_symlink_or_hard_link_refused(self):
  p=self.tar('m909');elsewhere=self.d/'evidence/elsewhere.tar';p.rename(elsewhere);p.symlink_to(elsewhere)
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.run_proof(self.good)
  p.unlink();os.link(elsewhere,p)
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SCOPE_BOUND$'):self.run_proof(self.good)
 def test_changed_pin_refused(self):
  pin=self.d/self.C.PIN;pin.write_bytes(pin.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'^L18_CONTRACT_PIN_SHA$'):self.run_proof(self.good)
 def test_changed_other_evidence_refused(self):
  (self.d/'evidence/betarc01/m910/Guardian').write_bytes(b'GuardiaX')
  with self.assertRaisesRegex(ValueError,'^RC01_REFERENCE_SHA$'):self.run_proof(self.good)
 def test_bound_and_runs_match_the_harness(self):
  self.assertEqual(self.C.PRIVATE_MAXIMUM,64*2**20);self.assertIn("st_size<=64*2**20,'BOUNDED_PRIVATE_TAR'",(PORT/'installclosure_h4.py').read_text())
  self.assertIn("run='beta-rc01-sdk-continuation09'if a.slot=='m909'else'beta-rc01-sdk-continuation10'",(B/'root-qualify-l18.py').read_text())

@unittest.skipUnless(HAVE and RETAINED.is_file(),'team m803/m802/m801/g105/g106 evidence of the work tree')
class StartAndDomain(unittest.TestCase):
 """resume_continuation, continuation_observation and verify_continuation_domain with a fake device and store."""
 def setUp(self):
  from aeris_runtime import continuation_l18 as C;from aeris_runtime.metadata_budget import encoded;self.C=C;self.m=manifest();self.digest=sha(encoded(self.m).rstrip(b'\n'))
  self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore();self.saved={k:getattr(C,k)for k in('command','read_ref','read_receipts')}
  C.command=self.fs.command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;shutil.copy(RETAINED,self.store.parent/'native-original-before-quarantine.tar')
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def fake(self,tar,*,argv=None,cold=b'ABSENT\n',apk=None,order=True):
  fs=self.fs;apk=apk or self.m['native']['APK_SHA256'];t=[0]
  def row(n):t[0]+=10;return{'startedHostNs':t[0],'endedHostNs':t[0]+1}
  base='/data/app/x/vn.rtr.aeris.betasim09-y/base.apk';target=self.store.parent/'native-restart-metadata.tar'
  owner=types.SimpleNamespace(digest=self.digest,manifest=self.m,root=self.d/'g110',writes=[],write=lambda n,v:owner.writes.append(n),budget=types.SimpleNamespace(write=lambda o,p,b:owner.writes.append(Path(p).name)))
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
 def test_start_from_m803_state_uses_the_owner_original_as_backup17(self):
  from aeris_runtime.adoption17 import retained_originals17
  from aeris_runtime.native17 import workspace17
  owner,case,receipts=self.run_start(M803);pin=json.loads((R/self.C.PIN).read_bytes());o=retained_originals17()
  self.assertEqual(case['admin17']['registryHead'],pin['registry']['head']);self.assertIs(case['admin17']['reconciledFromOriginalG103'],False)
  self.assertEqual(case['admin17']['originalReceiptTARSHA256'],pin['source']['sha256']);self.assertEqual(case['resumeL18']['backup']['sha256'],pin['source']['sha256'])
  self.assertEqual(case['backup17'],o['backup']);self.assertNotEqual(case['backup17']['sha256'],pin['source']['sha256']);self.assertEqual(case['coldProof17'],o['coldProof'])
  self.assertEqual(case['workspaceBefore17'],workspace17(o['backup']['path']));self.assertEqual(case['receiver17']['reportSHA256'],o['receiver']['reportSHA256'])
  self.assertIs(case['native'].application_domain['nativeLifecycleContinuationL18'],True);self.assertNotIn('nativeLifecycleContinuationL17',case['native'].application_domain)
  self.assertFalse(getattr(case['device'],'migration17_verified',False));self.assertEqual(receipts,['native17-continuation-l18.json','application-domain17-continuation-l18.json'])
  self.assertIn('native17-receiver-original.json',owner.writes)
  with self.assertRaisesRegex(ValueError,'L18_RESUME_ONCE'):self.C.resume_continuation(owner,case,deadline_ns=0)
 def test_refusals_happen_before_any_write(self):
  cases={'87-file m802 state':(dict(tar=M802),'CONTINUATION_L16_MISSING'),'83-file m801 state':(dict(tar=M801),'CONTINUATION_L16_MISSING'),'75-file state':(dict(tar=BASELINE),'CONTINUATION_L16_MISSING'),
   'app running':(dict(tar=M803,cold=b'PRESENT\n'),'L18_CURRENT_COLD_SELECTED_APK'),'other APK':(dict(tar=M803,apk='f'*64),'L18_CURRENT_COLD_SELECTED_APK'),
   'root tar instead of run-as':(dict(tar=M803,argv=['adb','-s','emulator-5582','exec-out','tar','-C','/data/user/0/x','-cf','-','files']),'L18_ORIGINAL_CURRENT_TAR_CAPTURE'),
   'capture before APK check':(dict(tar=M803,order=False),'L18_RESUME_CAPTURE_SOURCE_ORDER')}
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
   with self.assertRaisesRegex(ValueError,'L18_RETAINED_ORIGINALS_ARE_PINNED_RECEIVER'):self.C.resume_continuation(owner,case,deadline_ns=0)
   self.assertEqual((owner.writes,receipts),([],[]));self.assertNotIn('backup17',case)
  finally:adoption17.retained_originals17=real
 def test_cold_domain_check(self):
  owner,case,receipts=self.run_start(M803);fs=self.fs;domain=case['native'].application_domain
  legacy=self.store.parent/'android-api-retained';legacy.mkdir();old=self.C.rich_table(self.store.parent/'native-original-before-quarantine.tar')
  inv={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceStopped':True,'notNewDeviceGrowthCredit':True,'sourceDUCommandRef':'du','allocatedBytes':4096,
   'sourceOriginalTAR':{'path':str(self.store.parent/'native-original-before-quarantine.tar'),'sha256':sha(RETAINED.read_bytes())},'plaintextFileLengthBytes':sum(v['bytes']for v in old['files'].values()),'entries':len(old['files'])+len(old['directories'])}
  fs.diag.append(inv);fs.raw.update(retained=json.dumps(inv).encode(),dom=json.dumps(domain).encode(),**{'native17-continuation-l18.json':json.dumps(case['resumeL18']).encode()});fs.cmd['du']=({},None,['run-as','vn.rtr.aeris.mission','du','-k','-s','files'],b'4\tfiles\n')
  self.assertIs(self.C.verify_continuation_domain(self.store,'dom',self.m)['nativeLifecycleContinuationL18'],True)
  for name,change in{'l17 flag only':{'nativeLifecycleContinuationL18':None,'nativeLifecycleContinuationL17':True},'l16 flag only':{'nativeLifecycleContinuationL18':None,'nativeLifecycleContinuationL16':True},'old resume flag only':{'nativeLifecycleContinuationL18':None,'nativeLifecycleResumeH7':True},'other candidate':{'candidateSHA256':'0'*64}}.items():
   with self.subTest(case=name):
    bad={**domain,**change};fs.diag.append(bad);fs.raw['bad']=json.dumps(bad).encode()
    with self.assertRaisesRegex(ValueError,'L18_ORIGINAL_CONTINUATION_DOMAIN'):self.C.verify_continuation_domain(self.store,'bad',self.m)
 def test_domain_dispatch_in_product_native09(self):
  from aeris_runtime import product_native09
  src=Path(product_native09.__file__).read_text();i=src.index("nativeLifecycleContinuationL18");self.assertLess(src.index("nativeLifecycleContinuationL17"),i);self.assertIn('continuation_l18 import verify_continuation_domain',src[i:i+200])

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
  with self.assertRaisesRegex(ValueError,r'^NATIVE17_ALL_OLD_PRIVATE_BYTES_PRESERVED:files/product-input-registry17/highwater\.aj17$'):self.check(M802,M803)
 def test_owner_original_passes_on_the_restored_state_with_the_open_journal(self):
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
 """verify_sdk (close_maintenance for m909/m910) with a fake original-command store; package parsing stubbed."""
 PRIOR='99999999-9999-9999-9999-999999999999';BOOT='12345678-1234-1234-1234-123456789abc'
 def setUp(self):
  from aeris_runtime import continuation_l18 as C;self.C=C;self.m=manifest();self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore()
  self.saved={k:getattr(C,k)for k in('original_command','read_ref','read_receipts','package_state','safe_code_path')}
  C.original_command=self.fs.original_command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;C.package_state=lambda out,broken:out.decode().strip();C.safe_code_path=lambda p:p+'/base.apk'
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def proof(self,tar,*,slot='m909',argv=None,boot=None,profile=None):
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
 def test_m909_on_m803_state(self):
  owner,p=self.proof(M803);r=self.C.verify_sdk(owner,p);self.assertIs(r['originalPrivateBytesConserved'],True);self.assertEqual(r['continuation']['TARSHA256'],sha(M803.read_bytes()));self.assertEqual(r['actualKernelBootUUID'],self.BOOT)
 def test_m910_needs_same_private_table_as_m909(self):
  rep=self.d/'evidence/betarc01/m909/reports/coldboot-h7.json';rep.parent.mkdir(parents=True)
  for prior,ok in((M803,True),(M802,False)):
   with self.subTest(prior=prior.name):
    rep.write_text(json.dumps({'rootPrivateBackup':{'path':str(prior)}}));self.fs.__init__();owner,p=self.proof(M803,slot='m910')
    if ok:self.C.verify_sdk(owner,p)
    else:
     with self.assertRaisesRegex(ValueError,'L18_SECOND_BOOT_WHOLE_PRIVATE_UNCHANGED'):self.C.verify_sdk(owner,p)
 def test_refusals(self):
  cases={'l17 slot m907':(dict(slot='m907'),'L18_SDK_ONLY_EXACT_CURRENT_SOURCE'),'l17 slot m908':(dict(slot='m908'),'L18_SDK_ONLY_EXACT_CURRENT_SOURCE'),'87-file m802 state':(dict(tar=M802),'CONTINUATION_L16_MISSING'),'83-file m801 state':(dict(tar=M801),'CONTINUATION_L16_MISSING'),
   'run-as tar instead of root tar':(dict(argv=['adb','-s','emulator-5582','exec-out','run-as',self.C.PACKAGE,'tar','-cf','-','files']),'L18_SDK_ONLY_FIXED_ROOT_TAR'),
   'boot not new':(dict(boot=self.PRIOR),'L18_SDK_ONLY_FRESH_STABLE_BOOT'),'profile not observed':(dict(profile={'x':1}),'L18_EXPLICIT_PROFILE_OBSERVATION')}
  for name,(k,error)in cases.items():
   with self.subTest(case=name):
    self.fs.__init__();tar=k.pop('tar',M803);owner,p=self.proof(tar,**k)
    with self.assertRaisesRegex(ValueError,error):self.C.verify_sdk(owner,p)

AP=P.AP_ARTIFACT;INTERPRETER='/usr/libexec/qemu-binfmt/aarch64-binfmt-P';APSHA='77344f3c6f715cb326b99356815e8315769e9331dcb1e4c88bc4076804cb0d53'
# Shapes recorded by log 2026-11-11/03 (maps lines, readlink text); the AP command is the owner's with the l18 model address.
MAPS=[a+' '*28+AP for a in('00400000-008d3000 r--p 00000000 08:04 9599427','008e6000-00920000 r--p 004d6000 08:04 9599427','00920000-00924000 rw-p 00510000 08:04 9599427')]
COMMAND=[AP,'-w','--model','JSON:172.17.0.1','--home','10.854,106.807,10,0','--defaults','/candidate/copter.parm,/control/nominal/control.parm','--serial0=tcp:5760:nowait','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait','--sim-port-out','9012','--rate','1200','--speedup','1']
CONTEXT={'run':'linuxport01-l18-test','epoch':3,'boot':'boot-1'}
def nul(parts):return'\0'.join(parts)+'\0'
def container(**over):
 """The five docker exec answers of one AP container; returns (query, argv list seen)."""
 answers={'exe':P.EMULATOR_SHA256+'  /proc/8/exe\n','readlink':'/usr/bin/qemu-aarch64-static\n','file':APSHA+'  '+AP+'\n','cmdline':nul([INTERPRETER,AP,*COMMAND]),'maps':'\n'.join(MAPS)+'\n'};answers.update(over);seen=[]
 def query(argv):
  seen.append(list(argv));kind=argv[3]
  return answers['exe'if kind=='sha256sum'and argv[4].endswith('/exe')else'file'if kind=='sha256sum'else{'readlink':'readlink','cat':'cmdline','grep':'maps'}[kind]]
 return query,seen

class APIdentity(unittest.TestCase):
 """launch.ap_identity_l18 (the user's "Option (a): keep key", "Yes, pin qemu") on fake container answers shaped like log 2026-11-11/03."""
 def setUp(self):
  from aeris_runtime import launch;self.L=launch;self.ap={'APPID':8,'command':list(COMMAND)};self.cfg={'APSHA256':APSHA}
 def test_pins(self):
  self.assertEqual((self.L.AP_ARTIFACT_L18,self.L.BINFMT_INTERPRETER_L18,self.L.EMULATOR_SHA256_L18),(AP,INTERPRETER,P.EMULATOR_SHA256))
  self.assertEqual(sha((R/'runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03').read_bytes()),APSHA)
  self.assertEqual(json.loads((PORT/P.ASSET).read_bytes())['APSHA256'],APSHA)
 def test_accepts_the_mapped_pinned_artifact_under_the_pinned_emulator(self):
  query,seen=container();r=self.L.ap_identity_l18(query,'aeris-run',self.ap,self.cfg)
  self.assertEqual(r,{'actualAPExecutableSHA256':APSHA,'APIdentityMethod':'ARM_USER_EMULATION_MAPPED_ARTIFACT_L18','emulatorExecutablePath':'/usr/bin/qemu-aarch64-static','emulatorExecutableSHA256':P.EMULATOR_SHA256,'APCmdline':[INTERPRETER,AP,*COMMAND],'APMappedArtifactLines':MAPS})
  # the harness's own exe query first, the maps query last
  self.assertEqual(seen,[['docker','exec','aeris-run','sha256sum','/proc/8/exe'],['docker','exec','aeris-run','readlink','/proc/8/exe'],['docker','exec','aeris-run','sha256sum',AP],['docker','exec','aeris-run','cat','/proc/8/cmdline'],['docker','exec','aeris-run','grep','-F',AP,'/proc/8/maps']])
 def test_refusals(self):
  cases={'exe is the AP itself (the owner\'s l17 expectation)':(dict(exe=APSHA+'  x\n'),'PINNED_EMULATOR_SHA256'),'another emulator build':(dict(exe='0'*64+'  x\n'),'PINNED_EMULATOR_SHA256'),'no exe answer':(dict(exe=''),'PINNED_EMULATOR_SHA256'),
   'AP file changed':(dict(file='0'*64+'  '+AP+'\n'),'ARTIFACT_SHA256'),'cmdline without the interpreter':(dict(cmdline=nul([AP,*COMMAND])),'CMDLINE'),'cmdline of another binary':(dict(cmdline=nul([INTERPRETER,'/candidate/other','/candidate/other',*COMMAND[1:]])),'CMDLINE'),
   'cmdline with one more argument':(dict(cmdline=nul([INTERPRETER,AP,*COMMAND,'--extra'])),'CMDLINE'),'process argv names the Mac host address':(dict(cmdline=nul([INTERPRETER,AP,*[c.replace('172.17.0.1','192.168.65.254')for c in COMMAND]])),'CMDLINE'),
   'cmdline not NUL-terminated':(dict(cmdline=nul([INTERPRETER,AP,*COMMAND])[:-1]),'CMDLINE'),'no mapping of the AP file':(dict(maps=''),'MAPS'),'no mapping at offset 0':(dict(maps='\n'.join(MAPS[1:])+'\n'),'MAPS'),
   'mapped file deleted':(dict(maps=MAPS[0]+' (deleted)\n'),'MAPS'),'another file with the same prefix':(dict(maps=MAPS[0]+'\n'+MAPS[1]+'-other\n'),'MAPS'),'more than 16 lines':(dict(maps='\n'.join(MAPS[:1]*17)+'\n'),'MAPS')}
  for name,(over,reason)in cases.items():
   with self.subTest(case=name):
    query,_=container(**over)
    with self.assertRaisesRegex(ValueError,'^ACTUAL_AP_MAPPED_ARTIFACT_L18:'+reason+'$'):self.L.ap_identity_l18(query,'aeris-run',self.ap,self.cfg)
 def test_bad_launch_record_refused_before_any_query(self):
  for name,ap in{'pid 0':{'APPID':0,'command':COMMAND},'pid bool':{'APPID':True,'command':COMMAND},'pid text':{'APPID':'8','command':COMMAND},'no command':{'APPID':8},'command of another binary':{'APPID':8,'command':['/bin/sh','-c','x']},'non-text argument':{'APPID':8,'command':[AP,1]}}.items():
   with self.subTest(case=name):
    query,seen=container()
    with self.assertRaisesRegex(ValueError,'^ACTUAL_AP_MAPPED_ARTIFACT_L18:LAUNCH_RECORD$'):self.L.ap_identity_l18(query,'aeris-run',ap,self.cfg)
    self.assertEqual(seen,[])
 def test_launch_source_order_and_receipt(self):
  t=(PORT/'launch.py').read_text();order=["resources.start('backend'","'ORIGINAL3_GUARDS_REAL15S_PRIME'","resources.start('forwarder'","self._wait_forwarder(resources,campaign_deadline)","resources.start('ap'","'ACTUAL_OWNED_AP_CONTAINER'","ap_identity_l18(self.query,name,ap,cfg)","self.receipt={"]
  at=[t.index(s)for s in order];self.assertEqual(at,sorted(at))
  self.assertIn("**proof_l18,'forwarder':forwarder,'forwarderTiming':forwarder_timing,",t);self.assertIn("s.bind(FORWARDER_LISTEN_L18)",t);self.assertEqual(self.L.FORWARDER_LISTEN_L18,('172.17.0.1',9012))
  for s in("'ACTUAL_AP_EXECUTABLE')","--platform","192.168.65"):self.assertNotIn(s,t,s)
  # supervisor.py (byte-identical to l17) still reads the kept key
  self.assertIn("resource_receipt.get('actualAPExecutableSHA256')==provider.get('binarySHA256')",(PORT/'supervisor.py').read_text())

class HostQueryAllowlist(unittest.TestCase):
 """The real commands.HostCommands._call with a fake budget and a fake capture: only the allowlist line is under test."""
 def setUp(self):
  from aeris_runtime import commands;self.M=commands;self.saved=commands.capture_command;self.d=Path(tempfile.mkdtemp());self.ticks=[]
  query,self.seen=container()
  commands.capture_command=lambda budget,owner,argv,**k:{'failure':None,'stdout':query(argv).encode(),'stderr':b'','exit':0,'captureComplete':True}
  def write(owner,path,raw,append=False):
   with open(path,'ab')as f:f.write(raw)
  budget=types.SimpleNamespace(tick=self.ticks.append,write=write,append_json=lambda owner,path,row,maximum:write(owner,path,json.dumps(row).encode()+b'\n'))
  self.h=commands.HostCommands(self.d,types.SimpleNamespace(check=lambda:None,deadline_ns=time.monotonic_ns()+60_000_000_000),budget=budget)
 def tearDown(self):self.M.capture_command=self.saved;shutil.rmtree(self.d)
 def test_the_five_identity_queries_pass_the_real_allowlist(self):
  from aeris_runtime import launch,metadata_budget
  r=launch.ap_identity_l18(self.h._call,'aeris-run',{'APPID':8,'command':list(COMMAND)},{'APSHA256':APSHA})
  self.assertEqual(r['actualAPExecutableSHA256'],APSHA);self.assertEqual((self.h.n,self.ticks),(5,['queries']*5))
  rows=[json.loads(l)for l in(self.d/'queries.jsonl').read_text().splitlines()];self.assertEqual([x['argv']for x in rows],self.seen)
  # per launch: image inspect, ps, inspect + these five; two cases stay inside the owner's 32 queries
  self.assertEqual(metadata_budget.LIMITS['queries'],32);self.assertLessEqual(2*(3+5),32)
 def test_the_owner_forms_are_still_allowed(self):
  for argv in(['docker','image','inspect','sha256:'+'a'*64,'--format','{{.Id}}'],['docker','ps','-aq','--filter','name=^/aeris-run$'],['docker','inspect','aeris-run'],['docker','exec','aeris-run','sha256sum','/proc/8/exe']):
   with self.subTest(argv=argv):self.M.capture_command=lambda budget,owner,argv,**k:{'failure':None,'stdout':b'x','stderr':b'','exit':0,'captureComplete':True};self.assertEqual(self.h._call(argv),'x')
 def test_everything_else_is_refused_before_any_dispatch(self):
  bad=[['docker','exec','aeris-run','cat','/etc/passwd'],['docker','exec','aeris-run','cat','/proc/8/environ'],['docker','exec','aeris-run','cat','/proc/self/cmdline'],['docker','exec','aeris-run','cat','/proc/8/cmdline','/etc/passwd'],
   ['docker','exec','aeris-run','grep','-F',AP,'/proc/8/environ'],['docker','exec','aeris-run','grep','-rF',AP,'/proc/8/maps'],['docker','exec','aeris-run','grep','-F','/candidate/other','/proc/8/maps'],
   ['docker','exec','aeris-run','readlink','/proc/8/cwd'],['docker','exec','aeris-run','readlink','/proc/8/exe','x'],['docker','exec','aeris-run','sha256sum','/candidate/other'],['docker','exec','aeris-run','sha256sum',AP,'/etc/shadow'],
   ['docker','exec','other','cat','/proc/8/cmdline'],['docker','exec','-u','0','aeris-run','cat','/proc/8/cmdline'],['docker','exec','aeris-run','sh','-c','id'],['docker','run','aeris-run'],['docker','exec','aeris-run','cat','/proc/08/cmdline']]
  for argv in bad:
   with self.subTest(argv=argv),self.assertRaisesRegex(ValueError,'^READ_ONLY_HOST_QUERY_ALLOWLIST$'):self.h._call(argv)
  self.assertEqual((self.h.n,self.ticks,self.seen),(0,[],[]))

FORWARD_CHILD="import importlib.util,json,sys\nspec=importlib.util.spec_from_file_location('json_forwarder',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\nraise SystemExit(m.forward('127.0.0.1',0,int(sys.argv[2]),None,'127.0.0.0/8',json.loads(sys.argv[3])))"
class Forwarder(unittest.TestCase):
 """json_forwarder.py: derived from the tested tool; ready hand-off; the real forward() on loopback only (ephemeral ports).
 Not tested here: main() binding the real 172.17.0.1:9012 on docker0 (that needs Docker's bridge; a later probe)."""
 def setUp(self):
  from aeris_runtime import json_forwarder;self.F=json_forwarder;self.d=Path(tempfile.mkdtemp());self.procs=[];self.socks=[]
  self.good={**CONTEXT,'kind':'ready','tool':'aeris_runtime.json_forwarder','pid':4242,'listen':['172.17.0.1',9012],'port':9012,'backSocket':['127.0.0.1',40000],'backend':['127.0.0.1',9012],'device':'docker0','subnet':'172.17.0.0/16'}
 def tearDown(self):
  for p in self.procs:
   if p.poll()is None:p.kill()
   p.communicate()
  for s in self.socks:s.close()
  shutil.rmtree(self.d)
 def test_module_is_the_tested_tool_function_plus_declared_changes(self):
  tool=(B/P.FORWARDER_TOOL).read_text();self.assertEqual(sha(tool.encode()),P.FORWARDER_TOOL_SHA256);module=(PORT/P.FORWARDER_MODULE).read_text()
  def function(text,name):a=text.index('def '+name+'(');return text[a:text.index('\ndef ',a+1)]
  undone=function(module,'forward').replace('subnet,context):','subnet):').replace("{**context,'kind':'ready','tool':'aeris_runtime.json_forwarder',","{'kind':'ready','tool':'sitl_json_udp_forwarder.py',")
  self.assertEqual(undone,function(tool,'forward'));self.assertEqual(function(module,'hist_stats'),function(tool,'hist_stats'))
  names={n.name for n in ast.parse(module).body if isinstance(n,ast.FunctionDef)};self.assertEqual(names,{'hist_stats','forward','ready_line','main'})
  mods={a.name for n in ast.walk(ast.parse(module))if isinstance(n,ast.Import)for a in n.names}|{n.module for n in ast.walk(ast.parse(module))if isinstance(n,ast.ImportFrom)}
  self.assertEqual(mods,{'argparse','hashlib','ipaddress','json','os','select','signal','socket','time','pathlib'})
  self.assertEqual((self.F.LISTEN_IP,self.F.LISTEN_PORT,self.F.BACKEND_IP,self.F.BACKEND_PORT,self.F.DEVICE,self.F.SUBNET),('172.17.0.1',9012,'127.0.0.1',9012,'docker0','172.17.0.0/16'))
 def test_ready_line(self):
  line=json.dumps(self.good).encode()
  self.assertIsNone(self.F.ready_line(b'',CONTEXT));self.assertIsNone(self.F.ready_line(line,CONTEXT));self.assertEqual(self.F.ready_line(line+b'\n{"kind":"summary"}\n',CONTEXT),self.good)
  cases={'another run':(dict(run='other'),'CONTEXT'),'another epoch':(dict(epoch=4),'CONTEXT'),'another boot':(dict(boot='x'),'CONTEXT'),'summary line first':(dict(kind='summary'),'ENDPOINTS'),'the tool, not the module':(dict(tool='sitl_json_udp_forwarder.py'),'ENDPOINTS'),
   'listens on every address':(dict(listen=['0.0.0.0',9012]),'ENDPOINTS'),'another port':(dict(listen=['172.17.0.1',9013]),'ENDPOINTS'),'another backend':(dict(backend=['127.0.0.1',9013]),'ENDPOINTS'),'no device bind':(dict(device=None),'ENDPOINTS'),'no subnet rule':(dict(subnet=None),'ENDPOINTS'),'no pid':(dict(pid=None),'ENDPOINTS')}
  for name,(change,error)in cases.items():
   with self.subTest(case=name),self.assertRaisesRegex(ValueError,'^L18_FORWARDER_READY_'+error+'$'):self.F.ready_line(json.dumps({**self.good,**change}).encode()+b'\n',CONTEXT)
  with self.assertRaisesRegex(ValueError,'^L18_FORWARDER_READY_CONTEXT$'):self.F.ready_line(b'[1]\n',CONTEXT)
  for raw in(b'x'*1025,b'x'*1025+b'\n'):
   with self.assertRaisesRegex(ValueError,'^L18_FORWARDER_READY_BOUND$'):self.F.ready_line(raw,CONTEXT)
  with self.assertRaises(ValueError):self.F.ready_line(b'not json\n',CONTEXT)
 def launcher(self,events,*,alive=lambda name:None):
  """SimulationLauncher with a fake clock; events maps a poll number to bytes appended to the forwarder's captured stdout."""
  from aeris_runtime.launch import SimulationLauncher
  log=self.d/'forwarder.stdout.log';log.write_bytes(b'');clock=[0];polls=[0]
  def sleep(seconds):
   clock[0]+=int(seconds*1e9);polls[0]+=1
   if polls[0]in events:
    with open(log,'ab')as f:f.write(events[polls[0]])
  launch=SimulationLauncher(dict(CONTEXT),self.d,image='sha256:'+'0'*64,query=None,check_live=lambda:None,now=lambda:clock[0],sleep=sleep)
  resources=types.SimpleNamespace(children={'forwarder':types.SimpleNamespace(stdout_path=str(log))},require_alive=alive)
  return launch,resources,clock
 def test_launcher_waits_for_the_ready_line_in_the_captured_stdout(self):
  line=json.dumps(self.good).encode();launch,resources,clock=self.launcher({2:line[:40],4:line[40:]+b'\n'})
  value,timing=launch._wait_forwarder(resources,10**12);self.assertEqual(value,self.good);self.assertEqual(timing,{'startHostNs':0,'readyHostNs':200_000_000,'gateSeconds':5})
 def test_launcher_refusals(self):
  line=json.dumps(self.good).encode()
  launch,resources,clock=self.launcher({})
  with self.assertRaisesRegex(TimeoutError,'^OWNED_FORWARDER_START_DEADLINE$'):launch._wait_forwarder(resources,10**12)
  self.assertGreater(clock[0],5_000_000_000);self.assertLess(clock[0],5_200_000_000)
  launch,resources,clock=self.launcher({})
  with self.assertRaisesRegex(TimeoutError,'^OWNED_FORWARDER_START_DEADLINE$'):launch._wait_forwarder(resources,1_000_000_000)
  self.assertLess(clock[0],1_200_000_000)
  launch,resources,clock=self.launcher({1:json.dumps({**self.good,'run':'other'}).encode()+b'\n'})
  with self.assertRaisesRegex(ValueError,'^L18_FORWARDER_READY_CONTEXT$'):launch._wait_forwarder(resources,10**12)
  def dead(name):raise RuntimeError('OWNED_CHILD_EXIT:'+name+':4:x')
  launch,resources,clock=self.launcher({1:line+b'\n'},alive=dead)
  with self.assertRaisesRegex(RuntimeError,'^OWNED_CHILD_EXIT:forwarder:4:x$'):launch._wait_forwarder(resources,10**12)
 def start(self):
  backend=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);backend.bind(('127.0.0.1',0));backend.settimeout(5);self.socks.append(backend)
  p=subprocess.Popen([sys.executable,'-I','-B','-c',FORWARD_CHILD,str(PORT/P.FORWARDER_MODULE),str(backend.getsockname()[1]),json.dumps(CONTEXT)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.procs.append(p)
  ready=json.loads(p.stdout.readline());ap=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);ap.bind(('127.0.0.1',0));ap.settimeout(5);self.socks.append(ap)
  return p,ready,backend,ap
 def finish(self,p,signum=None):
  if signum is not None:p.send_signal(signum)
  out,err=p.communicate(timeout=10);return p.returncode,json.loads(out.splitlines()[-1]),err
 def test_real_forward_on_loopback_passes_packets_and_stops_cleanly(self):
  p,ready,backend,ap=self.start();target=('127.0.0.1',ready['port'])
  self.assertEqual({k:ready[k]for k in CONTEXT},CONTEXT);self.assertEqual((ready['kind'],ready['tool'],ready['backend']),('ready','aeris_runtime.json_forwarder',['127.0.0.1',backend.getsockname()[1]]))
  # the same line with the harness endpoints is what launch.py admits
  self.assertEqual(self.F.ready_line(json.dumps({**ready,'listen':['172.17.0.1',9012],'backend':['127.0.0.1',9012],'device':'docker0','subnet':'172.17.0.0/16'}).encode()+b'\n',CONTEXT)['pid'],p.pid)
  with self.assertRaisesRegex(ValueError,'^L18_FORWARDER_READY_ENDPOINTS$'):self.F.ready_line(json.dumps(ready).encode()+b'\n',CONTEXT)
  for frame in range(200):
   servo=frame.to_bytes(4,'little')*10;ap.sendto(servo,target);data,sender=backend.recvfrom(65535);self.assertEqual((data,list(sender)),(servo,ready['backSocket']))
   reply=b'\n{"frame":%d}\n'%frame;backend.sendto(reply,sender);data,sender=ap.recvfrom(65535);self.assertEqual((data,sender),(reply,target))
  code,summary,err=self.finish(p,signal.SIGTERM)
  self.assertEqual((code,summary['kind'],summary['stopped'],summary['toBackend']['packets'],summary['toAP']['packets'],summary['toBackend']['bytes'],summary['refused'],err),(0,'summary','SIGNAL',200,200,8000,None,b''))
 def test_real_forward_fails_closed_on_a_second_sender(self):
  p,ready,backend,ap=self.start();target=('127.0.0.1',ready['port']);ap.sendto(b'a'*40,target);self.assertEqual(backend.recvfrom(65535)[0],b'a'*40)
  other=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);other.bind(('127.0.0.1',0));self.socks.append(other);other.sendto(b'b'*40,target)
  code,summary,err=self.finish(p);self.assertEqual((code,summary['stopped'],summary['toBackend']['packets'],summary['refused']['peer']),(3,'FOREIGN_PEER',1,list(other.getsockname())))
  backend.settimeout(.3)
  with self.assertRaises(TimeoutError):backend.recvfrom(65535)
 def test_main_refuses_a_config_with_another_backend_address_before_any_socket(self):
  config=self.d/'run-config.json';config.write_text(json.dumps({**CONTEXT,'bind':['0.0.0.0',9012]}))
  p=subprocess.run([sys.executable,'-I','-B',str(PORT/P.FORWARDER_MODULE),'--config',str(config)],capture_output=True,timeout=20)
  self.assertNotEqual(p.returncode,0);self.assertIn(b'L18_FORWARDER_BACKEND_BIND',p.stderr);self.assertEqual(p.stdout,b'')
 def test_entry_admits_the_component(self):
  t=(PORT/'entry.py').read_text();self.assertIn("choices=['backend','ap_supervisor','json_forwarder','inspect']",t)
  self.assertIn("forwarder_argv=['python3','-B','-m','aeris_runtime.entry','json_forwarder','--config',str(out/'run-config.json')]",(PORT/'launch.py').read_text())

LINUX_PYTHON=sys.implementation.cache_tag=='cpython-314'and platform.machine()=='x86_64'and sys.platform=='linux'
KERNEL_MODULE='pilot.betaintegrated01.runtime._sim32_kernel'
class Kernel(unittest.TestCase):
 """The Linux physics kernel (the user's "Yes, provider only"): declared, loaded, required, and named by the provider only."""
 def setUp(self):
  from aeris_runtime import dependencies;self.D=dependencies
 def test_leaves_declare_both_kernels_and_all_exist(self):
  darwin='pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-darwin.so'
  self.assertIn(P.LINUX_KERNEL,self.D.LEAVES);self.assertIn(darwin,self.D.LEAVES);self.assertEqual(len(self.D.LEAVES),17);self.assertEqual(len(set(self.D.LEAVES)),17)
  for name in self.D.LEAVES:
   with self.subTest(leaf=name):self.assertTrue((R/name).is_file())
  self.assertEqual(sha((R/P.LINUX_KERNEL).read_bytes()),P.LINUX_KERNEL_SHA256);self.assertEqual(sha((R/darwin).read_bytes()),P.DARWIN_KERNEL_SHA256)
  self.assertEqual((self.D.LINUX_KERNEL,self.D.LINUX_KERNEL_SHA256),(P.LINUX_KERNEL,P.LINUX_KERNEL_SHA256))
 @unittest.skipUnless(LINUX_PYTHON,'CPython 3.14 on x86_64 Linux')
 def test_loaded_kernel_is_required_and_must_be_the_pinned_file(self):
  import pilot.betaintegrated01.runtime.physics as physics
  self.assertEqual(Path(sys.modules[KERNEL_MODULE].__file__),R/P.LINUX_KERNEL);self.assertIs(physics.native_derivative,sys.modules[KERNEL_MODULE].derivative)
  self.assertEqual(self.D.require_linux_kernel(P.LINUX_KERNEL_SHA256),{'path':P.LINUX_KERNEL,'sha256':P.LINUX_KERNEL_SHA256})
  for declared in(P.DARWIN_KERNEL_SHA256,None,''):
   with self.subTest(declared=declared),self.assertRaisesRegex(RuntimeError,'^L18_PINNED_LINUX_SIM32_KERNEL_REQUIRED$'):self.D.require_linux_kernel(declared)
  saved=self.D.LINUX_KERNEL_SHA256
  try:
   self.D.LINUX_KERNEL_SHA256='0'*64
   with self.assertRaisesRegex(RuntimeError,'^L18_PINNED_LINUX_SIM32_KERNEL_REQUIRED$'):self.D.require_linux_kernel('0'*64)
  finally:self.D.LINUX_KERNEL_SHA256=saved
  module=sys.modules.pop(KERNEL_MODULE)
  try:
   # the allowlist alone says nothing when no kernel is loaded; the l18 check refuses
   self.assertNotIn(KERNEL_MODULE,self.D.loaded_leaf_origins())
   with self.assertRaisesRegex(RuntimeError,'^L18_PINNED_LINUX_SIM32_KERNEL_REQUIRED$'):self.D.require_linux_kernel(P.LINUX_KERNEL_SHA256)
  finally:sys.modules[KERNEL_MODULE]=module
  self.assertEqual(self.D.require_linux_kernel(P.LINUX_KERNEL_SHA256)['sha256'],P.LINUX_KERNEL_SHA256)
 def test_entry_checks_the_backend_only_after_its_import(self):
  tree=ast.parse((PORT/'entry.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
  checks=[n for n in main.body if isinstance(n,ast.If)and ast.unparse(n.test)=="args.component == 'backend'"];self.assertEqual(len(checks),1)
  self.assertEqual(ast.unparse(checks[0].body[-1]),"require_linux_kernel(json.loads(Path(args.config).read_bytes()).get('modelKernelSHA256'))")
  at=main.body.index(checks[0]);self.assertEqual(len(main.body),at+3)
  self.assertEqual([ast.unparse(n)for n in main.body[at-2:at]],["module = importlib.import_module('aeris_runtime.' + args.component)",'module_origin_receipt(path)'])
  self.assertEqual([ast.unparse(n)for n in main.body[at+1:]],["sys.argv = [module.__file__, '--config', args.config]",'module.main()'])
 def test_provider_only_names_the_linux_kernel(self):
  a=json.loads((BASE/P.ASSET).read_bytes());b=json.loads((PORT/P.ASSET).read_bytes())
  self.assertEqual([k for k in a if a[k]!=b[k]],['modelKernelSHA256']);self.assertEqual(set(a),set(b));self.assertEqual((a['modelKernelSHA256'],b['modelKernelSHA256']),(P.DARWIN_KERNEL_SHA256,P.LINUX_KERNEL_SHA256))
  self.assertFalse((PORT/'assets/linux-profiles').exists())
  for variant in('nominal','loss'):
   with self.subTest(owner_profile=variant):self.assertEqual(json.loads((R/'pilot/betaintegrated01/cockpit04/profiles'/variant/'run-profile02.json').read_bytes())['modelKernelSHA256'],P.DARWIN_KERNEL_SHA256)
 def test_g2_run_config_declares_the_linux_kernel(self):
  from aeris_runtime import policy
  c=policy.build_config('workbench','linuxport01-l18-test',1,'boot',str(Path(tempfile.gettempdir())/'l18-no-such-evidence'),'case',maximum_seconds=180)
  self.assertEqual((c['providerKind'],c['modelKernelSHA256'],c['bind'],c['referenceProfile']),('WORKBENCH_SIM_V1',P.LINUX_KERNEL_SHA256,['127.0.0.1',9012],'planning/linuxport01/runtime-l18/source/aeris_runtime/'+P.ASSET))
  self.assertEqual(c['expectedConfigSHA256'],sha((PORT/P.ASSET).read_bytes()));self.assertNotEqual(c['expectedConfigSHA256'],sha((BASE/P.ASSET).read_bytes()))
  self.assertEqual(policy.validate_recording_policy(c)['amendmentSHA256'],c['externalRecordingPolicy']['amendmentSHA256'])

class APArgv(unittest.TestCase):
 def test_owner_argv_with_the_bridge_address_on_the_real_pinned_files(self):
  from aeris_runtime import ap_supervisor,policy
  c=policy.build_config('workbench','linuxport01-l18-test',1,'boot',str(Path(tempfile.gettempdir())/'l18-no-such-evidence'),'case',maximum_seconds=180);saved=ap_supervisor.validate_state
  try:
   ap_supervisor.validate_state=lambda config,state,out:{'stateValidationStubbedInTest':True}
   v=ap_supervisor.validate_pre_popen(c,candidate=str(R/'runtime/betaintegrated01/dist'),control=str(PORT/'assets/workbench-profiles'),state='/l18-no-such-state',out='/l18-no-such-evidence')
  finally:ap_supervisor.validate_state=saved
  self.assertEqual(v['command'][0],str(R/'runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03'));self.assertEqual(v['command'][1:],COMMAND[1:])
  self.assertEqual(c['APSHA256'],APSHA)
 def test_no_mac_host_address_left_in_the_source(self):
  self.assertEqual([str(p.relative_to(PORT))for p in PORT.rglob('*')if p.is_file()and b'192.168.65'in p.read_bytes()],[])
  self.assertEqual((PORT/'ap_supervisor.py').read_text().count("'JSON:172.17.0.1'"),1)

class FakeProcess:
 def __init__(self,pid,argv,*,exited=0,stuck=False):self.pid=pid;self.args=list(argv);self.code=exited;self.stuck=stuck;self.calls=[];self.stdout=self.stderr=None
 def poll(self):return self.code
 def wait(self,timeout=None):
  self.calls.append('wait')
  if self.code is None:raise subprocess.TimeoutExpired(self.args,timeout)
  return self.code
 def terminate(self):
  self.calls.append('terminate')
  if not self.stuck:self.code=-15
 def kill(self):self.calls.append('kill');self.code=-9
class FakeOutput:
 made=[]
 def __init__(self,budget=None,owner=None,process=None,paths=None,*,maximum_each=None,lease=None):
  self.maximum=maximum_each;self.lease=lease;self.released=True;self.thread=types.SimpleNamespace(is_alive=lambda:False);FakeOutput.made.append(self)
 def check(self):pass
 def close(self,timeout=2):return{'stdout':{'bytes':0,'captureComplete':True,'failure':None},'stderr':{'bytes':0,'captureComplete':True,'failure':None}}
class ThirdChild(unittest.TestCase):
 """The forwarder as a third owned child (the user's "Yes, write it"): the owner's ap/backend guards widened to ap, forwarder, backend.
 Real resources.py, disposal.py and raw_export.py code on fake processes (already exited, so no signal is ever sent)."""
 def setUp(self):
  from aeris_runtime import resources,metadata_budget,owned_output,disposal,raw_export
  self.RS=resources;self.MB=metadata_budget;self.OO=owned_output;self.DP=disposal;self.RX=raw_export;self.saved=owned_output.OwnedOutput;owned_output.OwnedOutput=FakeOutput;FakeOutput.made=[]
  self.d=Path(tempfile.mkdtemp());self.clock=[1000];self.leases=[];self.ticks=[];self.spawned=[]
 def tearDown(self):self.OO.OwnedOutput=self.saved;shutil.rmtree(self.d)
 def now(self):self.clock[0]+=1;return self.clock[0]
 def owner(self):
  budget=object.__new__(self.MB.MetadataBudget);budget.root=self.d/'metadata-budget';budget.mock=True;budget.tick=self.ticks.append
  budget.reserve_lease=lambda claims:(self.leases.append(dict(claims)),len(self.leases))[1];budget.bind_lease_child=lambda lease,pid:None;budget.release_lease=lambda lease:None;budget.failure=lambda error,detail=None:None
  def spawn(argv,**k):p=FakeProcess(5000+len(self.spawned),argv);self.spawned.append(p);return p
  r=object.__new__(self.RS.OwnedResources);r.candidate=B;r.manifest={'simulationOnly':True};r.digest='d'*64;r.root=self.d/'sessions'/'run'/'processes';r.spawn=spawn;r.now=self.now
  r.children={};r.files=[];r.outputs={};r.output_leases={};r.budget=budget;r.closure=None;r._completed_closure=None;r.scene_pipe=None;return r
 def start_all(self,r,names=('backend','forwarder','ap')):
  for name in names:r.start(name,['python3','-B',name],deadline_ns=10**18,candidate_python=name!='ap')
 def ground(self,r):
  t=self.clock[0];group=lambda:{'heartbeat':{'hostNs':t,'armed':False},'landed':{'hostNs':t,'landedState':1},'position':{'hostNs':t,'relativeAltitudeMm':0}}
  return{'groups':[group(),group()],'currentProofHostNs':t,'context':{'run':r.root.parent.name}}
 def test_start_admits_the_forwarder_with_its_small_lease(self):
  r=self.owner();self.start_all(r)
  self.assertEqual(self.leases,[{'child_output':1040384},{'child_output':16384},{'child_output':1040384}]);self.assertEqual([o.maximum for o in FakeOutput.made],[512000,4096,512000])
  self.assertEqual(self.ticks,['children']*3);self.assertEqual(list(r.children),['backend','forwarder','ap'])
  for name in('json_forwarder','emulator',''):
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'^SOURCE_OWNED_PROCESS_AND_BUDGET_REQUIRED$'):r.start(name,['x'],deadline_ns=10**18)
  with self.assertRaisesRegex(RuntimeError,'^RESOURCE_OWNERSHIP_START$'):r.start('forwarder',['x'],deadline_ns=10**18)
  self.assertEqual(len(self.spawned),3)
 def test_child_output_budget_two_cases_fit_the_unchanged_owner_cap_exactly(self):
  self.assertEqual(self.MB.OWNERS['child_output'],4*2**20);self.assertEqual(self.MB.LIMITS['children'],6);self.assertEqual(self.MB.LIMITS['cases'],2)
  self.assertEqual(2*(1040384+16384+1040384),4*2**20)
  line=lambda p:next(l for l in(p/'metadata_budget.py').read_text().splitlines()if l.startswith('OWNERS='))
  self.assertEqual(line(PORT),line(BASE))
  t=(PORT/'metadata_budget.py').read_text();self.assertIn(r"processes/(?:ap|forwarder|backend)\.(?:stdout|stderr)\.log",t);self.assertNotIn(r"processes/(?:ap|backend)\.",t)
  from aeris_runtime import pipeline_contract
  row=next(o for o in pipeline_contract.owners()if o['owner']=='child_output');self.assertEqual(row['futureBytes'],4*2**20);self.assertIn('2 runtime-l18 forwarder children',row['sourceEnforcement'])
 def test_normal_drain_stops_ap_then_forwarder_then_backend(self):
  r=self.owner();self.start_all(r);seal={'x':1}
  receipt=r._drain_proven(self.ground(r),seal,deadline_ns=10**18,seal_kind='workbenchSealProof')
  self.assertEqual(list(receipt['children']),['ap','forwarder','backend']);self.assertEqual(set(receipt['outputCapture']),{'ap','forwarder','backend'});self.assertIs(r.completed_closure(),receipt)
  self.assertEqual([p.calls for p in self.spawned],[['wait']]*3)
 def test_normal_drain_without_a_forwarder_is_refused(self):
  r=self.owner();self.start_all(r,('backend','ap'))
  with self.assertRaisesRegex(RuntimeError,'^OWNED_RESOURCE_MISSING:forwarder$'):r._drain_proven(self.ground(r),{'x':1},deadline_ns=10**18,seal_kind='workbenchSealProof')
 def test_failed_start_stops_the_forwarder_before_the_backend(self):
  r=self.owner();self.start_all(r,('backend','forwarder'))
  receipt=r.abort_preparation({'APNeverDispatched':True},deadline_ns=10**18)
  self.assertEqual((receipt['status'],list(receipt['children'])),('FAILED_STARTUP_OWNED_DRAIN_NOT_ACCEPTANCE',['forwarder','backend']));self.assertEqual(set(receipt['outputCapture']),{'backend','forwarder'})
 def test_raw_export_needs_all_three_children_in_the_normal_closure(self):
  r=self.owner();self.start_all(r);r._drain_proven(self.ground(r),{'x':1},deadline_ns=10**18,seal_kind='workbenchSealProof')
  # with the l18 closure the owner's next check is reached (no native probe in this test)
  with self.assertRaisesRegex(ValueError,'^RAW_EXPORT_GENUINE_NATIVE_CLOSED_FILE_EXPORT_REQUIRED$'):self.RX.prepare_export(r.budget,r,{},None)
  old=self.owner();self.start_all(old,('backend','ap'));start=self.now()
  old.closure=old._completed_closure={'startedNs':start,'finishedNs':start,'workbenchSealProof':{'x':1},'outputCapture':{'ap':{},'backend':{}},'children':{n:{'pid':c.process.pid,'exit':0}for n,c in old.children.items()}}
  self.assertIs(old.completed_closure(),old.closure)
  with self.assertRaisesRegex(ValueError,'^RAW_EXPORT_NORMAL_WORKBENCH_SOURCE_DRAIN_REQUIRED$'):self.RX.prepare_export(old.budget,old,{},None)
 def disposable(self,names,*,stuck=()):
  children={n:types.SimpleNamespace(name=n,process=FakeProcess(7000+i,['x',n],exited=None,stuck=n in stuck),argv=['x',n],started_ns=1)for i,n in enumerate(names)}
  return types.SimpleNamespace(manifest={'simulationOnly':True},children=children,outputs={n:FakeOutput()for n in names},closure=None,_completed_closure=None,scene_pipe=None,budget=types.SimpleNamespace(mock=True,failure=lambda error,detail=None:None))
 def test_disposal_stops_and_counts_the_forwarder(self):
  r=self.disposable(('backend','forwarder','ap'));v=self.DP.dispose_resources(r,primary_failure='test',admission_revoked=True,deadline_ns=time.monotonic_ns()+30_000_000_000)
  self.assertEqual(v['status'],'SIMULATOR_PHYSICALLY_DISPOSED_MISSION_FAILED');self.assertEqual(list(v['children']),['ap','apOutput','forwarder','forwarderOutput','backend','backendOutput'])
  self.assertEqual({n:(v['children'][n]['exit'],v['children'][n]['signals'])for n in('ap','forwarder','backend')},{n:(-15,['TERM'])for n in('ap','forwarder','backend')});self.assertEqual(v['errors'],[])
 def test_disposal_is_incomplete_while_the_forwarder_has_no_exit(self):
  r=self.disposable(('backend','forwarder','ap'));r.children['forwarder'].process.args=['changed']
  v=self.DP.dispose_resources(r,primary_failure='test',admission_revoked=True,deadline_ns=time.monotonic_ns()+30_000_000_000)
  self.assertEqual(v['status'],'SIMULATOR_DISPOSAL_INCOMPLETE_OWNERS_RETAINED');self.assertIsNone(v['children']['forwarder']);self.assertEqual([e['step']for e in v['errors']],['stop-forwarder'])
 def test_disposal_refuses_any_other_child(self):
  r=self.disposable(('backend','forwarder','ap','other'))
  with self.assertRaisesRegex(RuntimeError,'^SIM_DISPOSAL_ONLY_SOURCE_SIMULATION_CHILDREN$'):self.DP.dispose_resources(r,primary_failure='test',admission_revoked=True,deadline_ns=time.monotonic_ns()+30_000_000_000)
  self.assertEqual([c.process.calls for c in r.children.values()],[[]]*4)

class Package(unittest.TestCase):
 def test_behaviour_tests_use_the_l18_package(self):
  import aeris_runtime
  from aeris_runtime import continuation_l18,native17,product_runtime,launch,commands,dependencies,resources,disposal,raw_export,metadata_budget,json_forwarder,ap_supervisor,policy,entry
  for m in(aeris_runtime,continuation_l18,native17,product_runtime,launch,commands,dependencies,resources,disposal,raw_export,metadata_budget,json_forwarder,ap_supervisor,policy,entry):self.assertEqual(Path(m.__file__).parent,PORT,m.__name__)

if __name__=='__main__':unittest.main(verbosity=2)
