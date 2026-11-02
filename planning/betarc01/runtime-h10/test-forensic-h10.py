"""Actual raw-only closure using original command fixtures, no Android process."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime.forensic_h10 import verify_capture
from aeris_runtime.metadata_budget import encoded
from aeris_runtime.once_reader import read_ref
spec=importlib.util.spec_from_file_location('inert_h10_coupled_fixture',B/'test-h7.py');th=importlib.util.module_from_spec(spec);spec.loader.exec_module(th)
mt=ast.parse((R/'planning/betarc01/runtime/test-maintenance-close02.py').read_bytes());mc=next(n for n in mt.body if isinstance(n,ast.ClassDef)and n.name=='MaintenanceClose');mc.body=[n for n in mc.body if isinstance(n,ast.FunctionDef)and n.name=='fixture'];[setattr(n,'value','m801')for n in ast.walk(mc)if isinstance(n,ast.Constant)and n.value=='m101'];exec(compile(ast.Module(body=[mc],type_ignores=[]),'inert_H10_forensic_fixture','exec'),th.ns)
class ForensicH10(unittest.TestCase):
 def fixture(self,tmp):
  o,m,b,_=th.H7().sdk_fixture(tmp);v=o.case['maintenanceRC01']['sdkOnlyH7'];root=o.case['device'].root;backup=v['rootPrivateBackup'];p=Path(backup['path']);p.unlink();p.write_bytes(b'COMPLETE_MOCK_FORENSIC_BYTES_DELIBERATELY_NOT_A_TAR');cap=json.loads(read_ref(root,backup['captureReceiptRef']));backup.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());cap.update(bytesRetained=p.stat().st_size,bytesAcceptedByWriter=p.stat().st_size,bytesObservedLowerBound=p.stat().st_size);backup['captureReceiptRef']=th.append_row(root,'diagnostic',cap);o.case['maintenanceRC01']={'forensicOnlyH10':{k:copy.deepcopy(v[k])for k in ['candidateSHA256','priorKernelBootUUID','baseAPK','samples','rootPrivateBackup','preparationRef','finalUIDRef','finalStatRef','finalColdRef','afterBackupColdRef']}};v=o.case['maintenanceRC01']['forensicOnlyH10'];v.update(format='aeris-h10-forensic-raw-observation',version=1,status='COMPLETE_ORIGINAL_CAPTURE_AWAITING_GENUINE_SDK_CLOSE_AND_INDEPENDENT_SEMANTICS',disposition='FORENSIC_NOT_QUALIFICATION_NOT_G1',APKInstalled=False,ActivityStarted=False,APStarted=False,authorityRestorable=False,flightAcceptance=False,SDKQualificationClaimed=False,registrySemanticsChecked=False);return o,m,b
 def test_actual_capture_proof_closes_without_semantic_decoder_or_false_acceptance(self):
  with tempfile.TemporaryDirectory(prefix='forensic-',dir=B)as tmp:
   o,m,b=self.fixture(tmp)
   with patch('aeris_runtime.reconcile_h7.reconcile',side_effect=AssertionError('NO_SEMANTIC_DECODER_ALLOWED')):
    v=verify_capture(o,o.case['maintenanceRC01']);r=o.close_forensic_only()
   self.assertTrue(v['rawCaptureComplete']);self.assertFalse(r['SDKQualificationClaimed']);self.assertFalse(r['G1AcceptanceClaimed']);self.assertFalse(r['registrySemanticsChecked']);self.assertNotIn('originalPrivateBytesConserved',r);self.assertNotIn('pendingTransactions',r);self.assertFalse(r['monitor']['durablyDrained']);self.assertTrue(o.case['closed']);self.assertEqual(o.case['phase'],'FORENSIC_CAPTURE_MANAGED_CLOSED')
 def test_false_claim_raw_tampering_incomplete_capture_and_old_boot_refused(self):
  for mode in ['pending0','conserved','qualification','sha','capture','oldBoot','source','scope']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='forensic-',dir=B)as tmp:
    o,m,b=self.fixture(tmp);v=o.case['maintenanceRC01']['forensicOnlyH10']
    if mode=='pending0':v['pendingTransactions']=0
    elif mode=='conserved':v['originalPrivateBytesConserved']=True
    elif mode=='qualification':v['SDKQualificationClaimed']=True
    elif mode=='sha':v['rootPrivateBackup']['sha256']='0'*64
    elif mode=='capture':v['rootPrivateBackup']['captureReceiptRef']['sha256']='0'*64
    elif mode=='oldBoot':v['priorKernelBootUUID']=json.loads(read_ref(o.case['device'].root,v['preparationRef']))['kernelBootUUID']
    elif mode=='source':v['candidateSHA256']='0'*64
    else:o.root=o.root.parent/'foreign'
    with self.assertRaises(Exception):o.close_forensic_only()
    self.assertFalse(o.case['closed'])
 def test_entry_capture_persisted_before_normal_closure_no_semantic_path(self):
  p=B/'root-capture-h10.py';text=p.read_text();tree=ast.parse(text);self.assertNotIn('reconcile(',text);self.assertNotIn('verify_sdk',text);self.assertNotIn('APPLY',text);self.assertLess(text.index("owner.write('forensic-capture-h10.json'"),text.index('closed=owner.close_forensic_only()'));self.assertLess(text.index('closed=owner.close_forensic_only()'),text.index('guardian=owner.close_guardian(failed=False)'));self.assertIn('FORENSIC_CAPTURE_CLOSED_AWAITING_INDEPENDENT_SEMANTICS_NOT_QUALIFICATION_NOT_G1',text)
  with tempfile.TemporaryDirectory(prefix='forensic-',dir=B)as tmp:
   o,m,b=self.fixture(tmp);o.close_forensic_only();del o.write;o.write('forensic-capture-h10.json',{'mockOriginalOnly':True});b.write('guardian',o.root/'guardian/closure.json',encoded({'mockOnly':True}));b.write('external_task',o.root/'diagnostics/guardian-process/close.json',encoded({'mockOnly':True}));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='terminal_summary');ns={'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_H10_terminal_summary','exec'),ns);call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='write'and n.args and isinstance(n.args[0],ast.Constant)and n.args[0].value=='owner-terminal.json');eval(compile(ast.Expression(body=call),'actual_H10_terminal_write','eval'),dict(ns,owner=o));v=json.loads((o.root/'reports/owner-terminal.json').read_bytes());self.assertFalse(v['SDKQualificationClaimed']);self.assertFalse(v['G1AcceptanceClaimed']);self.assertEqual(len(v['originalEvidence']),4)
if __name__=='__main__':unittest.main(verbosity=2)
