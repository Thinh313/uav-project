"""Builder mocks only: no ADB, emulator, AP, APK build/sign or network."""
from pathlib import Path
import ast,base64,contextlib,copy,hashlib,io,json,os,sys,tarfile,tempfile,types,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=Path(__file__).resolve().parent/'source';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(S),str(R)]
from aeris_runtime import native17 as n
from aeris_runtime.candidate import artifact_roots,CAP
from aeris_runtime.product_runtime import WorkbenchRuntime
class Budget:
 def __init__(self):self.data={};self.ticks=[]
 def tick(self,k):self.ticks.append(k)
 def operation(self,v):return contextlib.nullcontext()
 def write(self,owner,path,raw,**kw):self.data[str(path)]=bytes(raw);return{'bytes':len(raw),'sha256':n.sha(raw),'writeSequence':len(self.data)}
class Owner:
 def __init__(self,p):self.root=p;self.budget=Budget();self.manifest={'native':{'sourceSHA256':'b'*64}};self.digest='c'*64
 def write(self,name,value):return self.budget.write('external_task',self.root/'reports'/name,json.dumps(value).encode())
class Runtime17(unittest.TestCase):
 def device(self):
  d=object.__new__(n.AndroidDomain17);d.serial='emulator-5582';d.observer=types.SimpleNamespace(tag='AERIS_PRODUCT_STATUS');return d
 def args(self):return['shell','am','broadcast','-a',n.ADMIN_ACTION,'-n',n.ADMIN_COMPONENT,'--es','requestNonce','a'*32,'--es','operation','APPLY','--es','planBase64',base64.b64encode(b'bounded mock plan').decode()]
 def test_exact_admin_grammar_and_bad_target_nonce_encoding(self):
  d=self.device();self.assertEqual(d._command_bound(self.args()),2048)
  for index,value in[(4,'foreign.action'),(6,'foreign/component'),(9,'notnonce'),(12,'RESET'),(15,'@@')]:
   q=self.args();q[index]=value
   with self.subTest(index=index),self.assertRaises(Exception):d._command_bound(q)
 def test_foreign_device_or_tag_never_admitted(self):
  for serial,tag in[('physical-phone','AERIS_PRODUCT_STATUS'),('emulator-5582','FOREIGN')]:
   d=self.device();d.serial=serial;d.observer.tag=tag
   with self.assertRaisesRegex(ValueError,'EXACT_OWNED'):d._command_bound(self.args())
 def test_oversized_plan_and_no_unreviewed_install(self):
  q=self.args();q[15]=base64.b64encode(b'x'*4097).decode()
  with self.assertRaisesRegex(ValueError,'BOUNDED_CANONICAL'):self.device()._command_bound(q)
  with self.assertRaisesRegex(ValueError,'ONE_SOURCE_BOUND_INSTALL'):self.device()._command_bound(['install','-r','arbitrary.apk'])
 def test_activity_start_requires_archive_proof(self):
  with self.assertRaisesRegex(ValueError,'ARCHIVE_VERIFIED'):self.device()._command_bound(['shell','am','start','-W','-n',n.ACTIVITY])
 def test_receiver_before_install_and_admin_never_retry(self):
  with self.assertRaisesRegex(ValueError,'POSITIVE_RECEIVER'):n.install_upgrade(None,{'device':object()},deadline_ns=1)
  case={'device':object(),'upgrade17':{'mockOnly':True},'adminAttempts17':{'APPLY'}}
  with self.assertRaisesRegex(ValueError,'NO_ADMIN_RETRY'):n.admin(None,case,'APPLY',deadline_ns=1)
 def test_both_actual_starts_and_cold_verifier_use_wait_shape(self):
  probe=(S/'aeris_runtime/product_native09.py').read_text()
  self.assertIn("d.command(['shell','am','start','-W','-n',ACTIVITY]",probe)
  self.assertIn("remote==['am','start','-W','-n',ACTIVITY]",probe)
  self.assertNotIn("d.command(['shell','am','start','-n',ACTIVITY]",probe)
  runtime=(S/'aeris_runtime/product_runtime.py').read_text();self.assertIn("snapshot=c['native'].start(deadline_ns=deadline_ns)",runtime)
 def test_AP_refused_in_native_gate_before_any_case_attribute(self):
  with self.assertRaisesRegex(RuntimeError,'NATIVE_GATE_NO_AP'):WorkbenchRuntime.start_resources(types.SimpleNamespace(root=Path('g101')),None)
 def test_all11_pools_and_numeric_cap_preserved(self):
  roots=artifact_roots(R/'evidence/nativejournal17/candidates');self.assertEqual(len(roots),11);self.assertIn(R/'evidence/missionintegrated16/candidates',roots);self.assertEqual(roots[-1],R/'evidence/nativejournal17/candidates');self.assertEqual(CAP,12*2**20)
 def envelope(self):
  rows=[{'generation':('%032x'%i),'bytes':23,'sha256':n.sha(b'AERIS_INPUT_JOURNAL_V2\n'),'disposition':'UNUSED','sourceClosedStatusBound':False}for i in range(8)]
  report={'status':'COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT','package':n.PACKAGE,'oldAPKSHA256':n.OLD_APK,'backupSHA256':'a'*64,'newSourceSHA256':'b'*64,'coldProofSHA256':'d'*64,'expectedHostRegistryHead':'ROOT','originals':rows};raw=json.dumps(report).encode();plan=b'opaque exact returned plan';q={'format':'aeris-journal17-fresh-cold-receiver-result','readOnly':True,'actorsStarted':False,'reportBase64':base64.b64encode(raw).decode(),'reportSHA256':n.sha(raw),'planBase64':base64.b64encode(plan).decode(),'planSHA256':n.sha(plan)};return q
 def run_receiver(self,p,envelope,**changes):
  owner=Owner(p);case={'backup17':{'path':str(p/'old.tar'),'sha256':'a'*64},'coldProof17':{'path':p/'proof.json','sha256':'d'*64}};result={'stdout':json.dumps(envelope).encode(),'stderr':b'','exit':0,'captureComplete':True,'failure':None,'pid':12345};result.update(changes)
  with patch.object(n,'capture_command',return_value=result)as call:
   value=n.independent_receiver(owner,case,'/mock/node',deadline_ns=1);self.assertEqual(call.call_count,1);self.assertEqual(call.call_args.args[2][1],'-B');self.assertIn('--cold-proof-sha',call.call_args.args[2]);self.assertEqual(owner.budget.ticks,['commands'])
  return owner,case,value
 def test_fresh_receiver_valid8unused_no_closure_credit(self):
  with tempfile.TemporaryDirectory(prefix='mock17-',dir=Path(__file__).parent)as p:
   owner,case,value=self.run_receiver(Path(p),self.envelope());self.assertEqual(len(value['originals']),8);self.assertTrue(all(not r['sourceClosedStatusBound']for r in value['originals']));self.assertIn('receiver17',case)
 def test_receiver_failures_no_positive_fallback(self):
  for changes in[{'exit':1},{'captureComplete':False},{'stderr':b'error'},{'failure':TimeoutError('mockdeadline')}]:
   with tempfile.TemporaryDirectory(prefix='mock17-',dir=Path(__file__).parent)as p,self.subTest(changes=str(changes)),self.assertRaisesRegex(ValueError,'COMPLETE_POSITIVE_EXIT'):self.run_receiver(Path(p),self.envelope(),**changes)
 def test_receiver_corrupt_foreign_duplicate_or_false_closed(self):
  for kind in('hash','closed','foreign','duplicate'):
   q=self.envelope();raw=json.loads(base64.b64decode(q['reportBase64']))
   if kind=='hash':q['reportSHA256']='0'*64
   else:
    if kind=='closed':raw['originals'][0]['sourceClosedStatusBound']=True
    if kind=='foreign':raw['backupSHA256']='0'*64
    if kind=='duplicate':raw['originals'][1]['generation']=raw['originals'][0]['generation']
    b=json.dumps(raw).encode();q['reportBase64']=base64.b64encode(b).decode();q['reportSHA256']=n.sha(b)
   with tempfile.TemporaryDirectory(prefix='mock17-',dir=Path(__file__).parent)as p,self.subTest(kind=kind),self.assertRaises(ValueError):self.run_receiver(Path(p),q)
 def test_full_tar_bytes_and_hardlink_member_refusal(self):
  with tempfile.TemporaryDirectory(prefix='mock17-',dir=Path(__file__).parent)as p:
   p=Path(p);tar=p/'valid.tar'
   with tarfile.open(tar,'w')as t:
    info=tarfile.TarInfo('files/original.bin');info.size=3;t.addfile(info,io.BytesIO(b'abc'))
   self.assertEqual(n.table(tar),{'files/original.bin':{'bytes':3,'sha256':n.sha(b'abc')}})
   bad=p/'bad.tar'
   with tarfile.open(bad,'w')as t:info=tarfile.TarInfo('files/link');info.type=tarfile.LNKTYPE;info.linkname='files/original.bin';t.addfile(info)
   with self.assertRaisesRegex(ValueError,'TAR_SHAPE'):n.table(bad)
 def test_workspace_exact_one_public_save_no_old_body_mutation(self):
  with tempfile.TemporaryDirectory(prefix='mock17-',dir=Path(__file__).parent)as d:
   p=Path(d);prefix='files/betasim-workspace01/';old=b'{"old":true}';new=b'{"new":true}';h1=n.sha(old);h2=n.sha(new)
   def build(path,seq,mutate=False):
    with tarfile.open(path,'w')as t:
     members={prefix+'0001-'+h1+'.json':b'bad'if mutate else old,prefix+'HEAD':('%d %s\n'%(seq,h1 if seq==1 else h2)).encode()}
     if seq==2:members[prefix+'0002-'+h2+'.json']=new
     for name,b in members.items():
      i=tarfile.TarInfo(name);i.size=len(b);t.addfile(i,io.BytesIO(b))
   a=p/'a.tar';b=p/'b.tar';build(a,1);build(b,2);before=n.workspace17(a);after=n.workspace17(b)
   saved={'head':after['head'],'observation':{'workspaceSaveReceipt':{'format':'aeris-verified-native-workspace-save','status':'COMMITTED','platform':'ANDROID','verification':'ORIGINAL_NATIVE_REPLY_ID_SESSION_ACTION_AND_BODY_SHA_VERIFIED','authorityRestorable':False,'completionSequence':1,'previousHead':before['head'],'head':after['head'],'bodySha256':h2}}}
   self.assertEqual(n.conserved_workspace17(a,b,saved)['newSequence'],2)
   for key,value in [('previousHead','0'*64),('bodySha256','0'*64),('platform','MOCK_NATIVE_BRIDGE'),('completionSequence',False)]:
    bad=copy.deepcopy(saved);bad['observation']['workspaceSaveReceipt'][key]=value
    with self.subTest(key=key),self.assertRaises(ValueError):n.conserved_workspace17(a,b,bad)
   build(b,2,True)
   with self.assertRaisesRegex(ValueError,'BODY_SHA'):n.conserved_workspace17(a,b,saved)
 def test_explicit_unused_verifier_and_fresh_registry_stage_anchor(self):
  source=(S/'aeris_runtime/native17.py').read_text();owner=Path(__file__).with_name('root-native-rc01.py').read_text();scenario=(R/'planning/nativejournal17/runtime/scenario-native-only17.py').read_text()
  self.assertIn("else previous['registryHead']",source);self.assertIn('MONOTONIC_REGISTRY_COUNTERS',source);self.assertIn("'VERIFY_NATIVE_UNUSED17'",owner);self.assertNotIn("'VERIFY_NATIVE_INPUTS'",owner)
  self.assertIn("ui.tap('sitl-fixture')",scenario);self.assertIn('ui.save_workspace()',scenario);self.assertIn('NO_PUBLIC_WORKSPACE_SAVE_GENERATION_BUDGET',source)
 def test_native_only_entry_no_mission_or_private_JS_actions(self):
  owner=Path(__file__).with_name('root-native-rc01.py').read_text();scenario=(R/'planning/nativejournal17/runtime/scenario-native-only17.py').read_text();ast.parse(owner);ast.parse(scenario)
  for forbidden in("start_resources(","ui.tap('b-arm')","ui.tap('b-auto')","evaluateJavascript","execute_script"):
   self.assertNotIn(forbidden,owner+scenario)
  self.assertIn("ui.tap('nav-review')",scenario);self.assertIn('force-stop',owner);self.assertIn('archive_check(owner,case,post',owner)
if __name__=='__main__':unittest.main(verbosity=2)
