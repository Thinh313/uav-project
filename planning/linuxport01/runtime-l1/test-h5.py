"""Finite original-method H5 mocks. Synthetic cold rows, no SDK/ADB/AP actors."""
from pathlib import Path
import ast,copy,gzip,hashlib,json,os,stat,sys,tempfile,time,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.monitor import ResourceMonitor,host_power
from aeris_runtime.metadata_budget import MetadataBudget,encoded,observer_envelope,OWNERS
from aeris_runtime import sdk_only_h5 as h
from aeris_runtime.once_reader import read_ref,read_receipts
from aeris_runtime.status15_reader import journal
# Inert existing actual ResourceMonitor+Owner fixture, never old module import.
tree=ast.parse((R/'planning/betarc01/runtime/test-maintenance-close02.py').read_bytes());node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='MaintenanceClose');node.body=[n for n in node.body if isinstance(n,ast.FunctionDef)and n.name=='fixture'];[setattr(n,'value','m401')for n in ast.walk(node)if isinstance(n,ast.Constant)and n.value=='m101'];ns=dict(globals(),HERE=B);exec(compile(ast.Module(body=[node],type_ignores=[]),'inert_maintenance_fixture','exec'),ns)
class H5(unittest.TestCase):
 def fixture(self,tmp):
  owner,monitor,budget=ns['MaintenanceClose']().fixture(tmp);new=owner.root;owner.write=lambda name,v,**kw:budget.write('external_task',new/'reports'/name,encoded(v),**kw)
  src=R/'evidence/betarc01/m302/sessions/beta-rc01-coldboot01/android-api';dst=new/'sessions/mock-sdk/android-api';dst.mkdir(parents=True);(dst/'receipts').mkdir()
  for n in['command-stream.raw','receipts/command.jsonl','receipts/diagnostic.jsonl']:(dst/n).write_bytes((src/n).read_bytes())
  v=json.loads((R/'evidence/betarc01/m302/reports/coldboot-h4.json').read_bytes());v.update(candidateSHA256='d'*64,priorKernelBootUUID='00000000-0000-0000-0000-000000000000');v['baseAPK']=h.package_state(h.original_command(dst,v['samples'][-1]['commandRefs']['dump'],['dumpsys','package',h.PACKAGE])[1],broken=False)
  def append(kind,row):
   p=dst/'receipts'/ (kind+'.jsonl');offset=p.stat().st_size;raw=encoded(row)
   with p.open('ab')as f:f.write(raw)
   return {'format':'aeris-original-byte-ref','version':3,'path':str(p.relative_to(dst)),'offset':offset,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
  prep=next(r for r in read_receipts(src,'diagnostic')if r.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED');v['preparationRef']=append('diagnostic',prep)
  backup=v['rootPrivateBackup'];target=dst.parent/'native-restart-metadata.tar';os.link(Path(backup['path']),target);cap=json.loads(read_ref(dst,backup['captureReceiptRef']));cap['path']=str(target);backup['path']=str(target);backup['captureReceiptRef']=append('diagnostic',cap)
  cold=journal(dst,v['finalColdRef'],'command');cold['startedHostNs']=cap['finishedHostNs']+1;cold['endedHostNs']=cold['startedHostNs']+1;v['afterBackupColdRef']=append('command',cold)
  owner.repo=R;owner.digest='d'*64;owner.manifest['native']={'APK_SHA256':json.loads((R/'evidence/nativejournal17/candidates/0a45b70a6c6e10860b303785d5041dc4fab2db416d7ee5218e1d718a32420a22/candidate.json').read_bytes())['native']['APK_SHA256']};owner.case['device']=types.SimpleNamespace(root=dst,adb=backup['argv'][0],observer=types.SimpleNamespace(process=None));owner.case['maintenanceRC01']={'sdkOnlyH5':v};return owner,monitor,budget
 def test_actual_original_join_positive_and_no_global_pending_claim(self):
  with tempfile.TemporaryDirectory(prefix='h5-',dir=B)as tmp:
   o,m,b=self.fixture(tmp);proof=h.verify(o,o.case['maintenanceRC01']);self.assertEqual(proof['pendingTransactions'],'NOT_CLAIMED_SDK_ONLY');value=o.close_sdk_only();self.assertTrue(o.case['closed']);self.assertFalse(value['flightAcceptance']);self.assertFalse(value['monitorDurableDrainClaimed']);self.assertFalse(value['monitor']['durablyDrained'])
 def test_raw_mismatch_old_boot_and_fake_pending_cannot_close(self):
  for mode in['boot','sha','capture','coldAfter','booleanOnly','source']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='h5-',dir=B)as tmp:
    o,m,b=self.fixture(tmp);v=o.case['maintenanceRC01']['sdkOnlyH5']
    if mode=='boot':v['priorKernelBootUUID']=h.original_command(o.case['device'].root,v['samples'][0]['commandRefs']['boot'],['cat','/proc/sys/kernel/random/boot_id'])[1].decode().strip()
    elif mode=='sha':o.manifest['native']['APK_SHA256']='0'*64
    elif mode=='capture':v['rootPrivateBackup']['captureReceiptRef']['sha256']='0'*64
    elif mode=='coldAfter':v['afterBackupColdRef']=v['finalColdRef']
    elif mode=='source':v['candidateSHA256']='0'*64
    else:o.case['maintenanceRC01']={'originalPrivateBytesConserved':True,'pendingTransactions':0,'activityStarted':False}
    with self.assertRaises(Exception):o.close_maintenance()
    self.assertFalse(o.case['closed'])
 def test_real_guardian_signal_normal_vs_failure_and_entry_positive_order(self):
  o=WorkbenchRuntime.__new__(WorkbenchRuntime);calls=[];p=types.SimpleNamespace(poll=lambda:None,send_signal=lambda sig:calls.append(sig));o.guardian=types.SimpleNamespace(process=p,wait=lambda deadline:{'exit':0});o.case={'closed':True};o.health=lambda:None;o.budget=None;o.root=B
  with patch('aeris_runtime.ipc_trace10.flush_clients',lambda *a:None):o.close_guardian(failed=False)
  import signal
  self.assertEqual(calls,[signal.SIGTERM]);calls.clear();o.close_guardian(failed=True);self.assertEqual(calls,[signal.SIGUSR1]);s=(B/'root-positive-h5.py').read_text();self.assertNotIn('QualifiedDiagnostic',s);self.assertLess(s.index('owner.start_writer()'),s.index('device.wait_owned_ready'));self.assertLess(s.index('closed=owner.close_sdk_only()'),s.index('guardian=owner.close_guardian(failed=False)'));self.assertIn('closing=True',s)
 def test_actual_terminal_write_success_expression_with_real_budget(self):
  with tempfile.TemporaryDirectory(prefix='h5-',dir=B)as tmp:
   o,m,b=self.fixture(tmp);del o.write
   for name in('coldboot-h5.json','native-maintenance-case-closure.json'):o.write(name,{'originalMockOnly':True})
   for name in('guardian/closure.json','diagnostics/guardian-process/close.json'):b.write('guardian'if name.startswith('guardian/')else'external_task',o.root/name,encoded({'mockOnly':True}))
   tree=ast.parse((B/'root-positive-h5.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='terminal_summary');ns=dict(Path=Path,hashlib=hashlib);exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_H5_terminal_summary','exec'),ns)
   call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='write'and n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='owner-terminal.json');eval(compile(ast.Expression(body=call),'actual_H5_success_terminal_write','eval'),dict(ns,owner=o));raw=(o.root/'reports/owner-terminal.json').read_bytes();self.assertLessEqual(len(raw),4096);self.assertEqual(json.loads(raw)['status'],'SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE');self.assertEqual(len(json.loads(raw)['originalEvidence']),4)
   with self.assertRaisesRegex(RuntimeError,'ONLY_OWNER_TERMINAL_CLOSURE_REPORT'):o.write('sdk-positive-close-h5.json',{},closing=True)
 def test_h4_bytes_modes_and_fixed_all_guards(self):
  baseline=json.loads(gzip.decompress((B/'H4-DERIVATION-BASELINE.json.gz').read_bytes()))
  for v in baseline['files'].values():
   p=R/v['oldPath'];s=p.stat();self.assertEqual((hashlib.sha256(p.read_bytes()).hexdigest(),stat.S_IMODE(s.st_mode),s.st_ino,s.st_dev),(v['sha256'],v['mode'],v['inode'],v['device']))
  self.assertEqual(observer_envelope()['totalFutureBytes'],60686336);self.assertEqual(len(OWNERS),14);self.assertEqual((B/'source/aeris_runtime/emulator.py').read_bytes(),(R/'planning/betarc01/runtime-h4/source/aeris_runtime/emulator.py').read_bytes());self.assertEqual((B/'source/aeris_runtime/guest_sync_h4.py').read_bytes(),(R/'planning/betarc01/runtime-h4/source/aeris_runtime/guest_sync_h4.py').read_bytes())
 def test_g1_newproof_cannot_accept_old_h4_fixedslots(self):
  s=(B/'root-native-h5.py').read_text();self.assertIn('from aeris_runtime.sdk_only_h5 import require_qualification',s)
  with self.assertRaises(Exception):h.require_qualification(str(B/'missing'),'0'*64,'a'*64)
if __name__=='__main__':
 result=unittest.main(verbosity=2,exit=False).result
 print(json.dumps({'format':'aeris-h5-actual-mock-module-origins','modules':{n:{'path':str(Path(m.__file__).resolve()),'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}for n,m in sys.modules.items()if(n=='aeris_runtime'or n.startswith('aeris_runtime.'))and getattr(m,'__file__',None)},'actorsStarted':False}))

 if not result.wasSuccessful():raise SystemExit(1)
