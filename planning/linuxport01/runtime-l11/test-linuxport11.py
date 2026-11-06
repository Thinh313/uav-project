"""LINUXPORT01 runtime-l11: runtime-l10 plus the G1 continuation from the m801 contract (team code).

Checks that every changed file is its original plus exactly the patches in
l11_patches.py, that the new team module and entries never use the post-g103
75-file decoder, and (with the team evidence of the work tree) that the
contract admission, qualification proof check, SDK boot check, G1 start and
cold domain check accept the team m801 state and refuse the earlier states and
mocks. Run from the tree root (the bind mount) with Python 3.14 -B.
"""
from pathlib import Path
import ast,copy,hashlib,json,os,shutil,sys,tempfile,types,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R),str(B)]
import l11_patches as P
L10=R/'planning/linuxport01/runtime-l10';PORT=B/'source/aeris_runtime';BASE=L10/'source/aeris_runtime'
NEW_MODULE='continuation_l11.py';REGENERATED={'assets/product-input-closure.json','assets/pipeline-writer-pins.json'}
M801=R/'evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
BASELINE=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
RETAINED=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-original-before-quarantine.tar'
HAVE=M801.is_file()and BASELINE.is_file()
def sha(b):return hashlib.sha256(b).hexdigest()
def files(root):return{p.relative_to(root).as_posix()for p in Path(root).rglob('*')if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.json.gz')}

class Derivation(unittest.TestCase):
 def test_source_is_l10_plus_declared_patches_only(self):
  self.assertEqual(files(PORT)-files(BASE),{NEW_MODULE});self.assertEqual(files(BASE)-files(PORT),set())
  differ={n for n in files(BASE)if(PORT/n).read_bytes()!=(BASE/n).read_bytes()}
  self.assertEqual(differ,set(P.MODULES)|REGENERATED)
  for name,patches in P.MODULES.items():
   with self.subTest(name=name):self.assertEqual((PORT/name).read_text(),P.apply((BASE/name).read_text(),patches,name))
 def test_entries_are_originals_plus_declared_patches(self):
  for src,dst,patches in((P.NATIVE_SOURCE,'root-native-l11.py',P.NATIVE),(P.QUALIFY_SOURCE,'root-qualify-l11.py',P.QUALIFY)):
   with self.subTest(entry=dst):
    self.assertEqual((B/dst).read_text(),P.apply((R/src).read_text(),patches,dst));self.assertEqual((B/dst).stat().st_mode&0o111,(R/src).stat().st_mode&0o111)
 def test_other_top_level_files_unchanged_from_l10(self):
  new={'l11_patches.py','root-native-l11.py','root-qualify-l11.py','test-linuxport11.py','prepare-source-gate.py'}
  top={p.name for p in B.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}
  self.assertEqual(top-new,{p.name for p in L10.iterdir()if p.is_file()and not p.name.endswith('.json.gz')}-{'test-linuxport10.py','prepare-source-gate.py'})
  for name in top-new:
   with self.subTest(name=name):self.assertEqual((B/name).read_bytes(),(L10/name).read_bytes())
 def test_source_gate_changes_only_entries_and_contract_reads(self):
  a=(L10/'prepare-source-gate.py').read_text();b=(B/'prepare-source-gate.py').read_text()
  a=a.replace("'planning/linuxport01/runtime-l10/root-native-h10.py',",'').replace('runtime-l10','runtime-l11')
  a=a.replace("'planning/linuxport01/runtime-l11/root-capture-h10.py']","'planning/linuxport01/runtime-l11/root-capture-h10.py','planning/linuxport01/runtime-l11/root-native-l11.py','planning/linuxport01/runtime-l11/root-qualify-l11.py']")
  a=a.replace("'planning/nativejournal17/verify-signatures17.mjs'];","'planning/nativejournal17/verify-signatures17.mjs','planning/linuxport01/contract-l10/continuation_l10.py','planning/linuxport01/contract-l10/m801-continuation-pin.json'];")
  self.assertEqual(a,b)
 def test_no_75_file_decoder_in_team_code(self):
  # The owner forbids reconcile_h7 (reconcile, originals, resume_existing) for the 83-file state.
  for p in(PORT/NEW_MODULE,B/'root-native-l11.py',B/'root-qualify-l11.py'):
   with self.subTest(path=p.name):
    tree=ast.parse(p.read_text());mods={n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names}
    self.assertFalse([m for m in mods if m and'reconcile'in m]);names={n.id for n in ast.walk(tree)if isinstance(n,ast.Name)}|{n.attr for n in ast.walk(tree)if isinstance(n,ast.Attribute)}
    self.assertFalse(names&{'reconcile','resume_existing','originals','resume_observation','verify_resume_domain'})
 def test_graph_pins_contract_and_entries(self):
  g=json.loads((PORT/'assets/product-input-closure.json').read_bytes());c=R/'planning/linuxport01/contract-l10'
  self.assertEqual(g['pins']['planning/linuxport01/contract-l10/continuation_l10.py'],sha((c/'continuation_l10.py').read_bytes()))
  self.assertEqual(g['pins']['planning/linuxport01/contract-l10/m801-continuation-pin.json'],'b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d')
  self.assertLessEqual(len(g['entrypoints']),8);self.assertIn('planning/linuxport01/runtime-l11/root-native-l11.py',g['entrypoints']);self.assertIn('planning/linuxport01/runtime-l11/root-qualify-l11.py',g['entrypoints'])
  self.assertFalse([e for e in g['entrypoints']if'runtime-l10'in e or e.endswith('root-native-h10.py')])
 def test_writer_contract_only_adds_the_new_module_sites(self):
  a=json.loads((BASE/'assets/pipeline-writer-pins.json').read_bytes());b=json.loads((PORT/'assets/pipeline-writer-pins.json').read_bytes())
  for k in('owners','envelope','frozenLeafSHA256','healthContract','metadataBoundary','format','version'):
   if k=='healthContract':continue
   with self.subTest(k=k):self.assertEqual(a[k],b[k])
  key=lambda r:(r['module'],r['function'],r['call'],r['siteSHA256']);sa={key(r)for r in a['sites']};sb={key(r)for r in b['sites']}
  self.assertEqual(sa-sb,set());self.assertEqual(sorted((m,f,c)for m,f,c,_ in sb-sa),[('aeris_runtime/continuation_l11.py','resume_continuation','write')]*3+[('aeris_runtime/continuation_l11.py','rich_table','open')])
 def test_slot_tables(self):
  from aeris_runtime import mission16,rc01
  for s in('m901','m902','g106'):self.assertEqual(mission16.SLOTS[s],180)
  self.assertEqual((rc01.KINDS['g106'],rc01.REMAINING['g106'],rc01.GENERATIONS['g106'],rc01.ARCHIVE_BOUNDARY['g106']),('native',0,2,rc01.ARCHIVE_BOUNDARY['g105']))
  f=rc01.generation_forecast(2,'g106',remaining_generations=0);self.assertEqual(f['projectedMaximumActive'],6)
  with self.assertRaises(ValueError):rc01.generation_forecast(2,'g106',remaining_generations=1)
  with self.assertRaises(ValueError):rc01.generation_forecast(5,'g106',remaining_generations=0)
 def test_native_entry_slot_and_qualify_entry_slots(self):
  self.assertIn("choices=('g106',)",(B/'root-native-l11.py').read_text());self.assertIn("choices=('m901','m902')",(B/'root-qualify-l11.py').read_text())

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

@unittest.skipUnless(HAVE,'team m801 and g105 evidence of the work tree')
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from aeris_runtime import continuation_l11 as C;cls.C=C;cls.m=manifest();cls.pin=json.loads((R/C.PIN).read_bytes())
 def test_m801_admitted(self):
  v=self.C.contract_check(M801,sha(M801.read_bytes()),self.m)
  self.assertEqual((v['registryHead'],v['activeJournals'],v['archivedJournals'],v['pendingTransactions']),(self.pin['registry']['head'],2,8,0));self.assertIs(v['decoder75FileUsed'],False)
  self.assertFalse([m for m in sys.modules if'reconcile'in m])
 def test_earlier_states_refused(self):
  for p in(BASELINE,SESSION1):
   with self.subTest(p=p.name),self.assertRaisesRegex(ValueError,'CONTINUATION_L10_MISSING'):self.C.contract_check(p,sha(p.read_bytes()),self.m)
 def test_wrong_tar_sha_refused(self):
  with self.assertRaisesRegex(ValueError,'RAW_SHA'):self.C.contract_check(M801,'0'*64,self.m)
 def test_contract_not_pinned_in_graph_refused(self):
  m=copy.deepcopy(self.m);m['productInputClosure']['pins'][self.C.CONTRACT]='0'*64
  with self.assertRaisesRegex(ValueError,'L11_CONTRACT_SOURCE_PIN'):self.C.contract_check(M801,sha(M801.read_bytes()),m)
 def test_m801_prior(self):
  boot,path=self.C.m801_prior();rep=json.loads((R/'evidence/betarc01/m801/reports/forensic-capture-h10.json').read_bytes())
  self.assertEqual(path,rep['baseAPK']);self.assertNotEqual(boot,rep['priorKernelBootUUID']);self.assertRegex(boot,'^[0-9a-f-]{36}$')
 def test_receiver_plan_is_current_archive_intent(self):
  r=self.C.receiver_originals(M801,sha(M801.read_bytes()));self.assertEqual(len({x['generation']for x in r['value']['originals']}),8);self.assertEqual(r['reportSHA256'],self.pin['receiver']['sha256'])
  with self.assertRaisesRegex(ValueError,'L11_ARCHIVE_PLAN_IS_CURRENT_INTENT_RECORD'):self.C.receiver_originals(RETAINED,sha(RETAINED.read_bytes()))

class Qualification(unittest.TestCase):
 """require_qualification on synthetic proofs in a temporary evidence root."""
 def setUp(self):
  from aeris_runtime import continuation_l11 as C,rc01;self.C=C;self.rc01=rc01;self.d=Path(tempfile.mkdtemp());(self.d/'evidence/betarc01').mkdir(parents=True)
  self.saved=(C.repository,rc01.repository);C.repository=rc01.repository=lambda:self.d;refs=[]
  for s in C.SLOTS:
   for k in('Observation','Guardian','SDKProcess','Private'):
    p=self.d/'evidence/betarc01'/s/k;p.parent.mkdir(exist_ok=True);p.write_bytes(k.encode());refs.append({'role':s+k,'ref':{'path':str(p),'bytes':len(k),'sha256':sha(k.encode())}})
  self.good={'format':C.QUALIFICATION,'version':1,'status':'ROOT_COLD_VERIFIED_CONTRACT_TWO_NORMAL_SDK_BOOTS_NOT_FLIGHT','candidateSHA256':'a'*64,'slots':['m901','m902'],'contractPinSHA256':C.PIN_SHA,'authorityRestorable':False,'SDKExitZeroNoForcedKillBoth':True,'actualKernelBootUUIDs':['11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222'],'originalEvidence':refs}
 def tearDown(self):self.C.repository,self.rc01.repository=self.saved;shutil.rmtree(self.d)
 def run_proof(self,v,candidate='a'*64):
  raw=json.dumps(v).encode();p=self.d/'evidence/betarc01'/('proof-%s.json'%sha(raw)[:8]);p.write_bytes(raw);return self.C.require_qualification(p,sha(raw),candidate)
 def test_positive(self):self.assertEqual(self.run_proof(self.good)['status'],'SOURCE_BOUND_L11_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE')
 def test_negatives(self):
  cases={'old owner format m701/m702':dict(format='aeris-h7-root-reconciled-sdk-cold-acceptance',slots=['m701','m702']),'other candidate':dict(candidateSHA256='b'*64),
   'not both exit 0':dict(SDKExitZeroNoForcedKillBoth=False),'same boot twice':dict(actualKernelBootUUIDs=['11111111-1111-1111-1111-111111111111']*2),
   'other contract pin':dict(contractPinSHA256='0'*64),'authority':dict(authorityRestorable=True),'seven refs':dict(originalEvidence=self.good['originalEvidence'][:7])}
  for name,change in cases.items():
   with self.subTest(case=name),self.assertRaises(ValueError):self.run_proof({**self.good,**change})
 def test_changed_evidence_refused(self):
  (self.d/'evidence/betarc01/m902/Private').write_bytes(b'privatX')
  with self.assertRaisesRegex(ValueError,'RC01_REFERENCE_SHA'):self.run_proof(self.good)

@unittest.skipUnless(HAVE and RETAINED.is_file(),'team m801 and g105 evidence of the work tree')
class StartAndDomain(unittest.TestCase):
 """resume_continuation, continuation_observation and verify_continuation_domain with a fake device and store."""
 def setUp(self):
  from aeris_runtime import continuation_l11 as C;from aeris_runtime.metadata_budget import encoded;self.C=C;self.m=manifest();self.digest=sha(encoded(self.m).rstrip(b'\n'))
  self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore();self.saved={k:getattr(C,k)for k in('command','read_ref','read_receipts')}
  C.command=self.fs.command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;shutil.copy(RETAINED,self.store.parent/'native-original-before-quarantine.tar')
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def fake(self,tar,*,argv=None,cold=b'ABSENT\n',apk=None,order=True):
  fs=self.fs;apk=apk or self.m['native']['APK_SHA256'];t=[0]
  def row(n):t[0]+=10;return{'startedHostNs':t[0],'endedHostNs':t[0]+1}
  base='/data/app/x/vn.rtr.aeris.betasim09-y/base.apk';target=self.store.parent/'native-restart-metadata.tar'
  owner=types.SimpleNamespace(digest=self.digest,manifest=self.m,root=self.d/'g106',writes=[],write=lambda n,v:owner.writes.append(n),budget=types.SimpleNamespace(write=lambda o,p,b:owner.writes.append(Path(p).name)))
  receipts=[]
  class Device:
   root=self.store;serial='emulator-5582';last_command_ref='privref';budget=types.SimpleNamespace(operation=lambda q:__import__('contextlib').nullcontext())
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
 def test_start_from_m801(self):
  owner,case,receipts=self.run_start(M801);pin=json.loads((R/self.C.PIN).read_bytes())
  self.assertEqual(case['admin17']['registryHead'],pin['registry']['head']);self.assertIs(case['admin17']['reconciledFromOriginalG103'],False)
  self.assertEqual(case['backup17']['sha256'],pin['source']['sha256']);self.assertEqual(len(case['receiver17']['value']['originals']),8)
  self.assertIs(case['native'].application_domain['nativeLifecycleContinuationL11'],True);self.assertNotIn('nativeLifecycleResumeH7',case['native'].application_domain)
  self.assertFalse(getattr(case['device'],'migration17_verified',False));self.assertEqual(receipts,['native17-continuation-l11.json','application-domain17-continuation-l11.json'])
  self.assertIn('native17-receiver-original.json',owner.writes)
  with self.assertRaisesRegex(ValueError,'L11_RESUME_ONCE'):self.C.resume_continuation(owner,case,deadline_ns=0)
 def test_refusals_happen_before_any_write(self):
  cases={'75-file state':(dict(tar=BASELINE),'CONTINUATION_L10_MISSING'),'79-file state':(dict(tar=SESSION1),'CONTINUATION_L10_MISSING'),
   'app running':(dict(tar=M801,cold=b'PRESENT\n'),'L11_CURRENT_COLD_SELECTED_APK'),'other APK':(dict(tar=M801,apk='f'*64),'L11_CURRENT_COLD_SELECTED_APK'),
   'root tar instead of run-as':(dict(tar=M801,argv=['adb','-s','emulator-5582','exec-out','tar','-C','/data/user/0/x','-cf','-','files']),'L11_ORIGINAL_CURRENT_TAR_CAPTURE'),
   'capture before APK check':(dict(tar=M801,order=False),'L11_RESUME_CAPTURE_SOURCE_ORDER')}
  for name,(k,error)in cases.items():
   with self.subTest(case=name):
    self.fs.__init__();tar=k.pop('tar');owner,case,receipts=self.fake(tar,**k)
    with self.assertRaisesRegex(ValueError,error):self.C.resume_continuation(owner,case,deadline_ns=0)
    self.assertEqual((owner.writes,receipts),([],[]));self.assertNotIn('admin17',case)
 def test_cold_domain_check(self):
  owner,case,receipts=self.run_start(M801);fs=self.fs;domain=case['native'].application_domain
  legacy=self.store.parent/'android-api-retained';legacy.mkdir();old=self.C.rich_table(self.store.parent/'native-original-before-quarantine.tar')
  inv={'format':'aeris-retained-old-application-private-inventory','package':'vn.rtr.aeris.mission','sourceStopped':True,'notNewDeviceGrowthCredit':True,'sourceDUCommandRef':'du','allocatedBytes':4096,
   'sourceOriginalTAR':{'path':str(self.store.parent/'native-original-before-quarantine.tar'),'sha256':sha(RETAINED.read_bytes())},'plaintextFileLengthBytes':sum(v['bytes']for v in old['files'].values()),'entries':len(old['files'])+len(old['directories'])}
  fs.diag.append(inv);fs.raw.update(retained=json.dumps(inv).encode(),dom=json.dumps(domain).encode(),**{'native17-continuation-l11.json':json.dumps(case['resumeL11']).encode()});fs.cmd['du']=({},None,['run-as','vn.rtr.aeris.mission','du','-k','-s','files'],b'4\tfiles\n')
  self.assertIs(self.C.verify_continuation_domain(self.store,'dom',self.m)['nativeLifecycleContinuationL11'],True)
  for name,change in{'old resume flag only':{'nativeLifecycleContinuationL11':None,'nativeLifecycleResumeH7':True},'other candidate':{'candidateSHA256':'0'*64}}.items():
   with self.subTest(case=name):
    bad={**domain,**change};fs.diag.append(bad);fs.raw['bad']=json.dumps(bad).encode()
    with self.assertRaisesRegex(ValueError,'L11_ORIGINAL_CONTINUATION_DOMAIN'):self.C.verify_continuation_domain(self.store,'bad',self.m)
 def test_domain_dispatch_in_product_native09(self):
  from aeris_runtime import product_native09
  src=Path(product_native09.__file__).read_text();i=src.index("nativeLifecycleContinuationL11");self.assertLess(src.index("nativeLifecycleResumeH7"),i);self.assertIn('verify_continuation_domain',src[i:i+200])

@unittest.skipUnless(HAVE,'team m801 and g105 evidence of the work tree')
class SDKBoot(unittest.TestCase):
 """verify_sdk (close_maintenance for m901/m902) with a fake original-command store; package parsing stubbed."""
 PRIOR='99999999-9999-9999-9999-999999999999';BOOT='12345678-1234-1234-1234-123456789abc'
 def setUp(self):
  from aeris_runtime import continuation_l11 as C;self.C=C;self.m=manifest();self.d=Path(tempfile.mkdtemp());self.store=self.d/'sessions/run/android-api';self.store.mkdir(parents=True);self.fs=FakeStore()
  self.saved={k:getattr(C,k)for k in('original_command','read_ref','read_receipts','package_state','safe_code_path')}
  C.original_command=self.fs.original_command;C.read_ref=self.fs.read_ref;C.read_receipts=self.fs.read_receipts;C.package_state=lambda out,broken:out.decode().strip();C.safe_code_path=lambda p:p+'/base.apk'
 def tearDown(self):
  for k,v in self.saved.items():setattr(self.C,k,v)
  shutil.rmtree(self.d)
 def proof(self,tar,*,slot='m901',argv=None,boot=None,profile=None):
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
 def test_m901_on_m801_state(self):
  owner,p=self.proof(M801);r=self.C.verify_sdk(owner,p);self.assertIs(r['originalPrivateBytesConserved'],True);self.assertEqual(r['continuation']['TARSHA256'],sha(M801.read_bytes()));self.assertEqual(r['actualKernelBootUUID'],self.BOOT)
 def test_m902_needs_same_private_table_as_m901(self):
  rep=self.d/'evidence/betarc01/m901/reports/coldboot-h7.json';rep.parent.mkdir(parents=True)
  for prior,ok in((M801,True),(SESSION1,False)):
   with self.subTest(prior=prior.name):
    rep.write_text(json.dumps({'rootPrivateBackup':{'path':str(prior)}}));self.fs.__init__();owner,p=self.proof(M801,slot='m902')
    if ok:self.C.verify_sdk(owner,p)
    else:
     with self.assertRaisesRegex(ValueError,'L11_SECOND_BOOT_WHOLE_PRIVATE_UNCHANGED'):self.C.verify_sdk(owner,p)
 def test_refusals(self):
  cases={'owner slot m701':(dict(slot='m701'),'L11_SDK_ONLY_EXACT_CURRENT_SOURCE'),'75-file state':(dict(tar=BASELINE),'CONTINUATION_L10_MISSING'),
   'run-as tar instead of root tar':(dict(argv=['adb','-s','emulator-5582','exec-out','run-as',self.C.PACKAGE,'tar','-cf','-','files']),'L11_SDK_ONLY_FIXED_ROOT_TAR'),
   'boot not new':(dict(boot=self.PRIOR),'L11_SDK_ONLY_FRESH_STABLE_BOOT'),'profile not observed':(dict(profile={'x':1}),'L11_EXPLICIT_PROFILE_OBSERVATION')}
  for name,(k,error)in cases.items():
   with self.subTest(case=name):
    self.fs.__init__();tar=k.pop('tar',M801);owner,p=self.proof(tar,**k)
    with self.assertRaisesRegex(ValueError,error):self.C.verify_sdk(owner,p)

if __name__=='__main__':unittest.main(verbosity=2)
