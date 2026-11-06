"""LINUXPORT01 runtime-l13: runtime-l12 plus the G1 chain m903/m904/g107 from the m802 contract and the backup17 fix (team code).

Checks that every changed file is its runtime-l12 original plus exactly the patches in
l13_patches.py, that no team code uses the post-g103 75-file decoder, and (with the team
evidence of the work tree) that the contract admission, qualification proof check, SDK
boot check, G1 start and cold domain check accept the team m802 state and refuse the
earlier states and mocks. ArchiveCheck re-runs the owner's native17.archive_check, with
the owner's real registry verifier, on the real g106 export after its first native
session: the snapshot continuation_l11 used fails exactly as g106 attempt 1 did, the one
continuation_l13 uses passes, and a changed original file is still refused.
Run from the tree root (the bind mount) with Python 3.14 -B.
"""
from pathlib import Path
import ast,contextlib,copy,hashlib,io,json,os,shutil,subprocess,sys,tarfile,tempfile,time,types,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R),str(B)]
import l13_patches as P
L12=R/'planning/linuxport01/runtime-l12';PORT=B/'source/aeris_runtime';BASE=L12/'source/aeris_runtime'
REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json'}
M802=R/'evidence/betarc01/m802/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
M801=R/'evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
BASELINE=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
G106START=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-restart-metadata.tar'
G106FIRST=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-journal17-after-first-close.tar'
RETAINED=R/'evidence/betarc01/g106/sessions/beta-rc01-native02/native-original-before-quarantine.tar'
PIN12='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'
HAVE=M802.is_file()and M801.is_file()and BASELINE.is_file()and G106FIRST.is_file()
def sha(b):return hashlib.sha256(b).hexdigest()
def files(root):return{p.relative_to(root).as_posix()for p in Path(root).rglob('*')if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.json.gz')}

class Derivation(unittest.TestCase):
 def test_source_is_l12_plus_declared_patches_only(self):
  self.assertEqual(files(PORT)-files(BASE),{P.NEW_MODULE});self.assertEqual(files(BASE)-files(PORT),set())
  differ={n for n in files(BASE)if(PORT/n).read_bytes()!=(BASE/n).read_bytes()}
  self.assertEqual(differ,set(P.MODULES)|REGENERATED)
  for name,patches in P.MODULES.items():
   with self.subTest(name=name):self.assertEqual((PORT/name).read_text(),P.apply((BASE/name).read_text(),patches,name))
  self.assertEqual((PORT/P.NEW_MODULE).read_text(),P.apply_counted((BASE/P.NEW_MODULE_SOURCE).read_text(),P.NEW_MODULE_PATCHES,P.NEW_MODULE))
 def test_entries_are_originals_plus_declared_patches(self):
  for src,dst,patches in((P.QUALIFY_SOURCE,'root-qualify-l13.py',P.QUALIFY),(P.NATIVE_SOURCE,'root-native-l13.py',P.NATIVE)):
   with self.subTest(entry=dst):
    self.assertEqual((B/dst).read_text(),P.apply((R/src).read_text(),patches,dst));self.assertEqual((B/dst).stat().st_mode&0o111,(R/src).stat().st_mode&0o111)
 def test_other_top_level_files_unchanged_from_l12(self):
  new={'l13_patches.py','root-native-l13.py','root-qualify-l13.py','test-linuxport13.py','prepare-source-gate.py'}
  top={p.name for p in B.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}
  self.assertEqual(top-new,{p.name for p in L12.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}-{'l12_patches.py','test-linuxport12.py','prepare-source-gate.py'})
  for name in top-new:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(L12/name).read_bytes())
  self.assertEqual((B/'prepare-source-gate.py').read_text(),P.gate((L12/'prepare-source-gate.py').read_text()))
 def test_no_75_file_decoder_and_no_l11_module_in_team_code(self):
  for p in(PORT/P.NEW_MODULE,B/'root-native-l13.py',B/'root-qualify-l13.py'):
   with self.subTest(path=p.name):
    tree=ast.parse(p.read_text());mods={n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}
    self.assertFalse([m for m in mods if m and('reconcile'in m or'continuation_l11'in m)]);names={n.id for n in ast.walk(tree)if isinstance(n,ast.Name)}|{n.attr for n in ast.walk(tree)if isinstance(n,ast.Attribute)}
    self.assertFalse(names&{'reconcile','resume_existing','originals','resume_observation','verify_resume_domain'})
 def test_new_module_has_no_l11_or_m801_values_left(self):
  # Code only: the module docstring and the comment above the fix name continuation_l11 and g106 on purpose.
  t=(PORT/P.NEW_MODULE).read_text();body='\n'.join(l for l in t[t.index('"""',3)+3:].splitlines()if not l.lstrip().startswith('#'))
  for s in('contract-l10','m801','M801','m901','m902','g106',"'L11_",'l11-','L11_METADATA','b5318c62','nativeLifecycleContinuationL11'):self.assertNotIn(s,body,s)
  self.assertIn(PIN12,body);self.assertEqual(body.count('retained_originals17'),2)
 def test_graph_pins_contract_and_entries(self):
  g=json.loads((PORT/'assets/product-input-closure.json').read_bytes());c=R/'planning/linuxport01/contract-l12'
  self.assertEqual(g['pins']['planning/linuxport01/contract-l12/continuation_l12.py'],sha((c/'continuation_l12.py').read_bytes()))
  self.assertEqual(g['pins']['planning/linuxport01/contract-l12/m802-continuation-pin.json'],PIN12)
  self.assertEqual(len(g['entrypoints']),8);self.assertIn('planning/linuxport01/runtime-l13/root-native-l13.py',g['entrypoints']);self.assertIn('planning/linuxport01/runtime-l13/root-qualify-l13.py',g['entrypoints'])
  self.assertFalse([e for e in g['entrypoints']if'runtime-l12'in e or'runtime-l11'in e or e.endswith(('root-native-l11.py','root-qualify-l11.py'))])
  a=json.loads((BASE/'assets/product-input-closure.json').read_bytes());n=lambda k:k.replace('runtime-l12','L').replace('runtime-l13','L')
  ra={n(k):v for k,v in a['pins'].items()};rb={n(k):v for k,v in g['pins'].items()}
  self.assertEqual({k for k in ra if ra.get(k)!=rb.get(k)},{'planning/linuxport01/L/root-native-l11.py','planning/linuxport01/L/root-qualify-l11.py'})
  self.assertEqual(set(rb)-set(ra),{'planning/linuxport01/L/root-native-l13.py','planning/linuxport01/L/root-qualify-l13.py','planning/linuxport01/contract-l12/continuation_l12.py','planning/linuxport01/contract-l12/m802-continuation-pin.json'})
 def test_writer_contract_only_adds_the_new_module_sites(self):
  a=json.loads((BASE/'assets/pipeline-writer-pins.json').read_bytes());b=json.loads((PORT/'assets/pipeline-writer-pins.json').read_bytes())
  for k in('owners','envelope','frozenLeafSHA256','metadataBoundary','format','version'):
   with self.subTest(k=k):self.assertEqual(a[k],b[k])
  key=lambda r:(r['module'],r['function'],r['call'],r['siteSHA256']);sa={key(r)for r in a['sites']};sb={key(r)for r in b['sites']}
  self.assertEqual(sa-sb,set());self.assertEqual(sorted((m,f,c)for m,f,c,_ in sb-sa),[('aeris_runtime/continuation_l13.py','resume_continuation','write')]*3+[('aeris_runtime/continuation_l13.py','rich_table','open')])
  self.assertEqual(len(b['sites']),265)
 def test_slot_tables(self):
  from aeris_runtime import mission16,rc01
  for s in('m903','m904','g107'):self.assertEqual(mission16.SLOTS[s],180)
  self.assertEqual((rc01.KINDS['g107'],rc01.REMAINING['g107'],rc01.GENERATIONS['g107'],rc01.ARCHIVE_BOUNDARY['g107']),('native',0,2,rc01.ARCHIVE_BOUNDARY['g105']))
  f=rc01.generation_forecast(3,'g107',remaining_generations=0);self.assertEqual(f['projectedMaximumActive'],7)
  with self.assertRaises(ValueError):rc01.generation_forecast(3,'g107',remaining_generations=1)
  with self.assertRaises(ValueError):rc01.generation_forecast(5,'g107',remaining_generations=0)
 def test_native_entry_slot_and_qualify_entry_slots(self):
  self.assertIn("choices=('g107',)",(B/'root-native-l13.py').read_text());self.assertIn("choices=('m903','m904')",(B/'root-qualify-l13.py').read_text())
 def test_close_maintenance_routes_m903_m904_to_l13(self):
  t=(PORT/'product_runtime.py').read_text();i=t.index("elif self.root.name in('m903','m904'):");self.assertIn('from .continuation_l13 import verify_sdk',t[i:i+120])

def manifest():
 g=json.loads((PORT/'assets/product-input-closure.json').read_bytes())
 return{'native':{'APK_SHA256':'eed4ba78'+'0'*56,'sourceSHA256':'c'*64},'productInputClosure':g}

class FakeStore:
 """Original command / receipt reader stand-in: refs are dict keys."""
 def __init__(self):self.cmd={};self.raw={};self.diag=[]
 def command(self,store,ref):return self.cmd[ref]
 def read_ref(self,store,ref):return self.raw[ref]
 def read_receipts(self,store,kind):return self.diag if kind=='diagnostic'else[]
 def original_command(self,store,ref,args):row,argv,remote,out=self.cmd[ref];assert remote==args,(remote,args);return row,out,remote

@unittest.skipUnless(HAVE,'team m802/m801/g105/g106 evidence of the work tree')
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from aeris_runtime import continuation_l13 as C;cls.C=C;cls.m=manifest();cls.pin=json.loads((R/C.PIN).read_bytes())
 def test_m802_admitted(self):
  v=self.C.contract_check(M802,sha(M802.read_bytes()),self.m)
  self.assertEqual((v['registryHead'],v['activeJournals'],v['archivedJournals'],v['pendingTransactions']),(self.pin['registry']['head'],3,8,0));self.assertIs(v['decoder75FileUsed'],False)
  self.assertFalse([m for m in sys.modules if'reconcile'in m])
 def test_earlier_states_refused(self):
  for p in(M801,G106START,SESSION1,BASELINE):
   with self.subTest(p=p.parent.parent.parent.name+'/'+p.name),self.assertRaisesRegex(ValueError,'CONTINUATION_L12_MISSING'):self.C.contract_check(p,sha(p.read_bytes()),self.m)
 def test_wrong_tar_sha_refused(self):
  with self.assertRaisesRegex(ValueError,'RAW_SHA'):self.C.contract_check(M802,'0'*64,self.m)
 def test_contract_not_pinned_in_graph_refused(self):
  m=copy.deepcopy(self.m);m['productInputClosure']['pins'][self.C.CONTRACT]='0'*64
  with self.assertRaisesRegex(ValueError,'L13_CONTRACT_SOURCE_PIN'):self.C.contract_check(M802,sha(M802.read_bytes()),m)
 def test_m802_prior(self):
  boot,path=self.C.m802_prior();rep=json.loads((R/'evidence/betarc01/m802/reports/forensic-capture-h10.json').read_bytes())
  self.assertEqual(path,rep['baseAPK']);self.assertNotEqual(boot,rep['priorKernelBootUUID']);self.assertEqual(boot,'8b79cdee-809e-462c-af09-a4445925c1d7')
 def test_receiver_plan_is_current_archive_intent(self):
  r=self.C.receiver_originals(M802,sha(M802.read_bytes()));self.assertEqual(len({x['generation']for x in r['value']['originals']}),8);self.assertEqual(r['reportSHA256'],self.pin['receiver']['sha256'])
  with self.assertRaisesRegex(ValueError,'L13_ARCHIVE_PLAN_IS_CURRENT_INTENT_RECORD'):self.C.receiver_originals(RETAINED,sha(RETAINED.read_bytes()))

class Qualification(unittest.TestCase):
 """require_qualification on synthetic proofs in a temporary evidence root."""
 def setUp(self):
  from aeris_runtime import continuation_l13 as C,rc01;self.C=C;self.rc01=rc01;self.d=Path(tempfile.mkdtemp());(self.d/'evidence/betarc01').mkdir(parents=True)
  self.saved=(C.repository,rc01.repository);C.repository=rc01.repository=lambda:self.d;refs=[]
  for s in C.SLOTS:
   for k in('Observation','Guardian','SDKProcess','Private'):
    p=self.d/'evidence/betarc01'/s/k;p.parent.mkdir(exist_ok=True);p.write_bytes(k.encode());refs.append({'role':s+k,'ref':{'path':str(p),'bytes':len(k),'sha256':sha(k.encode())}})
  self.good={'format':C.QUALIFICATION,'version':1,'status':'ROOT_COLD_VERIFIED_CONTRACT_TWO_NORMAL_SDK_BOOTS_NOT_FLIGHT','candidateSHA256':'a'*64,'slots':['m903','m904'],'contractPinSHA256':C.PIN_SHA,'authorityRestorable':False,'SDKExitZeroNoForcedKillBoth':True,'actualKernelBootUUIDs':['11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222'],'originalEvidence':refs}
 def tearDown(self):self.C.repository,self.rc01.repository=self.saved;shutil.rmtree(self.d)
 def run_proof(self,v,candidate='a'*64):
  raw=json.dumps(v).encode();p=self.d/'evidence/betarc01'/('proof-%s.json'%sha(raw)[:8]);p.write_bytes(raw);return self.C.require_qualification(p,sha(raw),candidate)
 def test_positive(self):self.assertEqual(self.run_proof(self.good)['status'],'SOURCE_BOUND_L13_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE')
 def test_negatives(self):
  cases={'l11 proof m901/m902':dict(format='aeris-linuxport01-l11-root-contract-sdk-cold-acceptance',slots=['m901','m902']),'l11 slots':dict(slots=['m901','m902']),
   'contract-l10 pin':dict(contractPinSHA256='b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d'),'other candidate':dict(candidateSHA256='b'*64),
   'not both exit 0':dict(SDKExitZeroNoForcedKillBoth=False),'same boot twice':dict(actualKernelBootUUIDs=['11111111-1111-1111-1111-111111111111']*2),
   'authority':dict(authorityRestorable=True),'seven refs':dict(originalEvidence=self.good['originalEvidence'][:7])}
  for name,change in cases.items():
   with self.subTest(case=name),self.assertRaises(ValueError):self.run_proof({**self.good,**change})
 def test_changed_evidence_refused(self):
  (self.d/'evidence/betarc01/m904/Private').write_bytes(b'privatX')
  with self.assertRaisesRegex(ValueError,'RC01_REFERENCE_SHA'):self.run_proof(self.good)

@unittest.skipUnless(HAVE and RETAINED.is_file(),'team m802/m801/g105/g106 evidence of the work tree')
class StartAndDomain(unittest.TestCase):
 """resume_continuation, continuation_observation and verify_continuation_domain with a fake device and store."""
 def setUp(self):
  from aeris_runtime import continuation_l13 as C;from aeris_runtime.metadata_budget import encoded;self.C=C;self.m=manifest();self.digest=sha(encoded(self.m).rstrip(b'\n'))
  self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore();self.saved={k:getattr(C,k)for k in('command','read_ref','read_receipts')}
  C.command=self.fs.command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;shutil.copy(RETAINED,self.store.parent/'native-original-before-quarantine.tar')
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def fake(self,tar,*,argv=None,cold=b'ABSENT\n',apk=None,order=True):
  fs=self.fs;apk=apk or self.m['native']['APK_SHA256'];t=[0]
  def row(n):t[0]+=10;return{'startedHostNs':t[0],'endedHostNs':t[0]+1}
  base='/data/app/x/vn.rtr.aeris.betasim09-y/base.apk';target=self.store.parent/'native-restart-metadata.tar'
  owner=types.SimpleNamespace(digest=self.digest,manifest=self.m,root=self.d/'g107',writes=[],write=lambda n,v:owner.writes.append(n),budget=types.SimpleNamespace(write=lambda o,p,b:owner.writes.append(Path(p).name)))
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
 def test_start_from_m802_uses_the_owner_original_as_backup17(self):
  from aeris_runtime.adoption17 import retained_originals17
  from aeris_runtime.native17 import workspace17
  owner,case,receipts=self.run_start(M802);pin=json.loads((R/self.C.PIN).read_bytes());o=retained_originals17()
  self.assertEqual(case['admin17']['registryHead'],pin['registry']['head']);self.assertIs(case['admin17']['reconciledFromOriginalG103'],False)
  self.assertEqual(case['admin17']['originalReceiptTARSHA256'],pin['source']['sha256']);self.assertEqual(case['resumeL13']['backup']['sha256'],pin['source']['sha256'])
  # The fix: backup17 is the n02 pre-migration original (as resume_existing), not the current capture.
  self.assertEqual(case['backup17'],o['backup']);self.assertNotEqual(case['backup17']['sha256'],pin['source']['sha256']);self.assertEqual(case['coldProof17'],o['coldProof'])
  self.assertEqual(case['workspaceBefore17'],workspace17(o['backup']['path']));self.assertEqual(case['receiver17']['reportSHA256'],o['receiver']['reportSHA256'])
  self.assertIs(case['native'].application_domain['nativeLifecycleContinuationL13'],True);self.assertNotIn('nativeLifecycleContinuationL11',case['native'].application_domain)
  self.assertFalse(getattr(case['device'],'migration17_verified',False));self.assertEqual(receipts,['native17-continuation-l13.json','application-domain17-continuation-l13.json'])
  self.assertIn('native17-receiver-original.json',owner.writes)
  with self.assertRaisesRegex(ValueError,'L13_RESUME_ONCE'):self.C.resume_continuation(owner,case,deadline_ns=0)
 def test_refusals_happen_before_any_write(self):
  cases={'83-file m801 state':(dict(tar=M801),'CONTINUATION_L12_MISSING'),'75-file state':(dict(tar=BASELINE),'CONTINUATION_L12_MISSING'),
   'app running':(dict(tar=M802,cold=b'PRESENT\n'),'L13_CURRENT_COLD_SELECTED_APK'),'other APK':(dict(tar=M802,apk='f'*64),'L13_CURRENT_COLD_SELECTED_APK'),
   'root tar instead of run-as':(dict(tar=M802,argv=['adb','-s','emulator-5582','exec-out','tar','-C','/data/user/0/x','-cf','-','files']),'L13_ORIGINAL_CURRENT_TAR_CAPTURE'),
   'capture before APK check':(dict(tar=M802,order=False),'L13_RESUME_CAPTURE_SOURCE_ORDER')}
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
   owner,case,receipts=self.fake(M802)
   with self.assertRaisesRegex(ValueError,'L13_RETAINED_ORIGINALS_ARE_PINNED_RECEIVER'):self.C.resume_continuation(owner,case,deadline_ns=0)
   self.assertEqual((owner.writes,receipts),([],[]));self.assertNotIn('backup17',case)
  finally:adoption17.retained_originals17=real
 def test_cold_domain_check(self):
  owner,case,receipts=self.run_start(M802);fs=self.fs;domain=case['native'].application_domain
  legacy=self.store.parent/'android-api-retained';legacy.mkdir();old=self.C.rich_table(self.store.parent/'native-original-before-quarantine.tar')
  inv={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceStopped':True,'notNewDeviceGrowthCredit':True,'sourceDUCommandRef':'du','allocatedBytes':4096,
   'sourceOriginalTAR':{'path':str(self.store.parent/'native-original-before-quarantine.tar'),'sha256':sha(RETAINED.read_bytes())},'plaintextFileLengthBytes':sum(v['bytes']for v in old['files'].values()),'entries':len(old['files'])+len(old['directories'])}
  fs.diag.append(inv);fs.raw.update(retained=json.dumps(inv).encode(),dom=json.dumps(domain).encode(),**{'native17-continuation-l13.json':json.dumps(case['resumeL13']).encode()});fs.cmd['du']=({},None,['run-as','vn.rtr.aeris.mission','du','-k','-s','files'],b'4\tfiles\n')
  self.assertIs(self.C.verify_continuation_domain(self.store,'dom',self.m)['nativeLifecycleContinuationL13'],True)
  for name,change in{'l11 flag only':{'nativeLifecycleContinuationL13':None,'nativeLifecycleContinuationL11':True},'old resume flag only':{'nativeLifecycleContinuationL13':None,'nativeLifecycleResumeH7':True},'other candidate':{'candidateSHA256':'0'*64}}.items():
   with self.subTest(case=name):
    bad={**domain,**change};fs.diag.append(bad);fs.raw['bad']=json.dumps(bad).encode()
    with self.assertRaisesRegex(ValueError,'L13_ORIGINAL_CONTINUATION_DOMAIN'):self.C.verify_continuation_domain(self.store,'bad',self.m)
 def test_domain_dispatch_in_product_native09(self):
  from aeris_runtime import product_native09
  src=Path(product_native09.__file__).read_text();i=src.index("nativeLifecycleContinuationL13");self.assertLess(src.index("nativeLifecycleContinuationL11"),i);self.assertIn('continuation_l13 import verify_continuation_domain',src[i:i+200])

@unittest.skipUnless(HAVE,'team m802/m801/g105/g106 evidence of the work tree')
class ArchiveCheck(unittest.TestCase):
 """The owner's native17.archive_check (unchanged) with his real registry verifier, on the real g106 export after its first
 native session (the same entries as the m802 state). Only the stage that has no workspace-receipt check ('migration') is
 used; the byte-conservation loop that failed g106 attempt 1 is the same code for every stage. capture_command is replaced
 by a plain subprocess run of the same argv (the owner's metadata budget is not under test here)."""
 def setUp(self):
  from aeris_runtime import native17 as N;from aeris_runtime.adoption17 import retained_originals17;self.N=N;self.o=retained_originals17()
  self.saved=N.capture_command;self.d=Path(tempfile.mkdtemp());(self.d/'reports').mkdir()
  def capture(budget,owner,argv,*,deadline_ns,stdout_limit,stderr_limit):
   r=subprocess.run(argv,capture_output=True,timeout=120);return{'stdout':r.stdout[:stdout_limit],'stderr':r.stderr[:stderr_limit],'pid':1,'exit':r.returncode,'captureComplete':len(r.stdout)<=stdout_limit and len(r.stderr)<=stderr_limit,'failure':None}
  N.capture_command=capture
  self.pin=json.loads((R/'planning/linuxport01/contract-l12/m802-continuation-pin.json').read_bytes());recv=(R/self.pin['receiver']['path']).read_bytes();(self.d/'reports/native17-receiver-original.json').write_bytes(recv)
  plan=(R/self.pin['receiver']['path']).with_name('native17-plan-original.txt').read_bytes();self.receiver={'value':json.loads(recv),'planSHA256':sha(plan),'reportSHA256':sha(recv)}
 def tearDown(self):self.N.capture_command=self.saved;shutil.rmtree(self.d)
 def check(self,backup,export):
  budget=types.SimpleNamespace(tick=lambda k:None,operation=lambda q:contextlib.nullcontext(),write=lambda kind,path,raw:Path(path).write_bytes(raw))
  owner=types.SimpleNamespace(root=self.d,digest='a'*64,budget=budget,write=lambda n,v:(self.d/'reports'/n).write_text(json.dumps(v)))
  case={'admin17':{'registryHead':self.pin['registry']['head']},'backup17':{'path':str(backup),'sha256':sha(Path(backup).read_bytes())},'receiver17':self.receiver,'device':types.SimpleNamespace()}
  for f in(self.d/'reports').glob('native17-migration-*'):f.unlink()
  return self.N.archive_check(owner,case,{'path':str(export),'sha256':sha(Path(export).read_bytes())},'migration',deadline_ns=time.monotonic_ns()+120_000_000_000),case
 def test_l11_snapshot_fails_exactly_as_g106_attempt1(self):
  # continuation_l11 passed the capture taken at the start of g106 (the 83-file m801 state) as backup17.
  with self.assertRaisesRegex(ValueError,r'^NATIVE17_ALL_OLD_PRIVATE_BYTES_PRESERVED:files/product-input-registry17/highwater\.aj17$'):self.check(G106START,G106FIRST)
  term=json.loads((R/'evidence/betarc01/g106/reports/owner-terminal.json').read_bytes());self.assertEqual(term['primaryFailure'],'NATIVE17_ALL_OLD_PRIVATE_BYTES_PRESERVED:files/product-input-registry17/highwater.aj17')
 def test_l13_snapshot_passes_on_the_grown_registry(self):
  proof,case=self.check(self.o['backup']['path'],G106FIRST)
  self.assertEqual((proof['status'],proof['registryHead'],proof['activeJournals'],proof['archivedJournals'],proof['pendingTransactions']),('SOURCE_BOUND_ORIGINAL_ARCHIVE_INDEX_JOIN_VERIFIED',self.pin['registry']['head'],3,8,0))
  stage=json.loads((self.d/'reports/native17-migration-proof.json').read_bytes());self.assertIs(stage['originalPrivateBytesConserved'],True);self.assertEqual(stage['oldFileCount'],70)
  self.assertIs(case['device'].migration17_verified,True)
 def test_l13_snapshot_still_refuses_a_changed_original_file(self):
  from aeris_runtime.native17 import table
  before=table(self.o['backup']['path']);name=sorted(n for n in before if not n.startswith(('files/product-input','files/betasim-workspace01/HEAD')))[0]
  dst=self.d/'changed.tar'
  with tarfile.open(G106FIRST)as t,tarfile.open(dst,'w',format=tarfile.GNU_FORMAT)as o:
   for m in t:
    b=t.extractfile(m).read()if m.isfile()else None
    if m.name==name:b=bytes([b[0]^1])+b[1:]
    o.addfile(m,io.BytesIO(b)if b is not None else None)
  with self.assertRaisesRegex(ValueError,'^NATIVE17_ALL_OLD_PRIVATE_BYTES_PRESERVED:'+name.replace('.','[.]')+'$'):self.check(self.o['backup']['path'],dst)

@unittest.skipUnless(HAVE,'team m802/m801/g105/g106 evidence of the work tree')
class SDKBoot(unittest.TestCase):
 """verify_sdk (close_maintenance for m903/m904) with a fake original-command store; package parsing stubbed."""
 PRIOR='99999999-9999-9999-9999-999999999999';BOOT='12345678-1234-1234-1234-123456789abc'
 def setUp(self):
  from aeris_runtime import continuation_l13 as C;self.C=C;self.m=manifest();self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore()
  self.saved={k:getattr(C,k)for k in('original_command','read_ref','read_receipts','package_state','safe_code_path')}
  C.original_command=self.fs.original_command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;C.package_state=lambda out,broken:out.decode().strip();C.safe_code_path=lambda p:p+'/base.apk'
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def proof(self,tar,*,slot='m903',argv=None,boot=None,profile=None):
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
 def test_m903_on_m802_state(self):
  owner,p=self.proof(M802);r=self.C.verify_sdk(owner,p);self.assertIs(r['originalPrivateBytesConserved'],True);self.assertEqual(r['continuation']['TARSHA256'],sha(M802.read_bytes()));self.assertEqual(r['actualKernelBootUUID'],self.BOOT)
 def test_m904_needs_same_private_table_as_m903(self):
  rep=self.d/'evidence/betarc01/m903/reports/coldboot-h7.json';rep.parent.mkdir(parents=True)
  for prior,ok in((M802,True),(M801,False)):
   with self.subTest(prior=prior.name):
    rep.write_text(json.dumps({'rootPrivateBackup':{'path':str(prior)}}));self.fs.__init__();owner,p=self.proof(M802,slot='m904')
    if ok:self.C.verify_sdk(owner,p)
    else:
     with self.assertRaisesRegex(ValueError,'L13_SECOND_BOOT_WHOLE_PRIVATE_UNCHANGED'):self.C.verify_sdk(owner,p)
 def test_refusals(self):
  cases={'l11 slot m901':(dict(slot='m901'),'L13_SDK_ONLY_EXACT_CURRENT_SOURCE'),'83-file m801 state':(dict(tar=M801),'CONTINUATION_L12_MISSING'),
   'run-as tar instead of root tar':(dict(argv=['adb','-s','emulator-5582','exec-out','run-as',self.C.PACKAGE,'tar','-cf','-','files']),'L13_SDK_ONLY_FIXED_ROOT_TAR'),
   'boot not new':(dict(boot=self.PRIOR),'L13_SDK_ONLY_FRESH_STABLE_BOOT'),'profile not observed':(dict(profile={'x':1}),'L13_EXPLICIT_PROFILE_OBSERVATION')}
  for name,(k,error)in cases.items():
   with self.subTest(case=name):
    self.fs.__init__();tar=k.pop('tar',M802);owner,p=self.proof(tar,**k)
    with self.assertRaisesRegex(ValueError,error):self.C.verify_sdk(owner,p)

if __name__=='__main__':unittest.main(verbosity=2)
