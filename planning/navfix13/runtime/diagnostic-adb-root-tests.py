"""UNCERTAIN_DISPATCH mocks write real OnceStore refs, use original cold reader.
No adb, emulator, APK, SITL, subprocess or candidate mutation by these tests.
"""
from pathlib import Path
import hashlib,json,os,sys,tempfile,types,unittest,shlex
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];B=Path(__file__).parent/'source';sys.path[:0]=[str(B),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.android import AndroidDevice
from aeris_runtime.once_store import OnceStore
from aeris_runtime.once_reader import read_ref,read_receipts
from pilot.betaintegrated01.runtime.ap_stage import canonical
BOOT=b'8c111111-2222-4333-8444-555555555555\n';OTHER=b'8c111111-2222-4333-8444-666666666666\n';CLOSED=b'adb: unable to connect for root: closed\n'
class MockBudget:
 def write(self,owner,path,raw,*,append=False,closing=False):
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('ab'if append else'xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
class Fixture:
 def __init__(self,path):
  d=object.__new__(AndroidDevice);self.d=d;d.adb='/mock/adb';d.serial='emulator-5582';d.sequence=0;d.observer=types.SimpleNamespace(tag='AERIS_PRODUCT_STATUS',process=None);d._android_ready={'mock':True};d._content_reader_preparation_attempted=False;d.last_command_ref=None;d.store=OnceStore(path,budget=MockBudget());self.t=10_000;d.now=lambda:self.t;d.command=self.command;self.calls=[];self.uid=b'2000\n';self.after_uid=b'0\n';self.boot_before=BOOT;self.boot_after=BOOT;self.boot_count=0;self.root_exit=1;self.root_err=CLOSED;self.root_out=b'';self.root_complete=True;self.root_notes=[];self.root_error=None;self.corrupt=False;self.wrong_argv=False;self.after_root_jump=0
 def command(self,args,*,deadline_ns,maximum_bytes):
  if self.t>=deadline_ns:raise TimeoutError('ANDROID_COMMAND_DEADLINE')
  args=list(args);self.calls.append((args,deadline_ns,maximum_bytes));self.d.sequence+=1;started=self.t;self.t+=1000;out=err=b'';exitcode=0;failure=None;error=None
  if args==['shell','cat','/proc/sys/kernel/random/boot_id']:
   out=self.boot_before if self.boot_count==0 else self.boot_after;self.boot_count+=1
  elif args==['shell','id','-u']:out=self.uid
  elif args==['root']:
   out=self.root_out;err=self.root_err;exitcode=self.root_exit;self.uid=self.after_uid
   if exitcode:
    error=RuntimeError('ANDROID_COMMAND_EXIT:'+str(exitcode));self.root_error=error;failure=type(error).__name__+':'+str(error)
    for note in self.root_notes:error.add_note(note)
  elif args!=['wait-for-device']:raise AssertionError(args)
  argv=[self.d.adb,'-s','emulator-5584'if args==['root']and self.wrong_argv else self.d.serial,*(['shell',shlex.join(args[1:])]if args[0]=='shell'else args)]
  outref=self.d.store.command_bytes(out);errref=self.d.store.command_bytes(err);argref=self.d.store.command_bytes(canonical(argv));row={'format':'aeris-command','version':3,'sequence':self.d.sequence,'argvRef':argref,'startedHostNs':started,'endedHostNs':self.t,'exit':exitcode,'stdoutRef':outref,'stderrRef':errref,'captureComplete':self.root_complete if args==['root']else True,'failure':failure};self.d.last_command_ref=self.d.store.receipt('command-%05d.json'%self.d.sequence,row)
  if args==['root']:
   if self.corrupt:
    p=self.d.store.root/'command-stream.raw'
    with p.open('r+b')as f:f.seek(errref['offset']);f.write(b'X')
   self.t+=self.after_root_jump
  if error is not None:raise error
  if exitcode!=0 or err:raise RuntimeError('mockunexpectedstderr')
  return out
class RootPreparationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='diagnostic-root-',dir=R/'evidence/navfix13');self.addCleanup(self.tmp.cleanup);self.f=Fixture(Path(self.tmp.name));self.d=self.f.d
 def prepare(self,deadline=30_000_010_000):return self.d.prepare_content_reader(deadline_ns=deadline)
 def prep(self):return json.loads(read_ref(self.d.store.root,self.d.content_reader_preparation))
 def root_count(self):return sum(v[0]==['root']for v in self.f.calls)
 def test_uncertain_root_dispatch_uid0_sameboot_confirmed_separately(self):
  self.prepare();p=self.prep();self.assertEqual(p['version'],2);self.assertTrue(p['originalRootCommandFailed']);self.assertFalse(p['originalRootCommandAcceptedAsSuccess']);self.assertTrue(p['actualUID0']);self.assertFalse(p['rootResent']);self.assertEqual(p['kernelBootUUID'],BOOT.decode().strip());self.assertEqual(self.root_count(),1);self.assertEqual([v[0]for v in self.f.calls],[['shell','cat','/proc/sys/kernel/random/boot_id'],['shell','id','-u'],['root'],['wait-for-device'],['shell','id','-u'],['shell','cat','/proc/sys/kernel/random/boot_id']]);row=json.loads(read_ref(self.d.store.root,p['rootRef']));self.assertEqual(row['exit'],1);self.assertEqual(row['failure'],'RuntimeError:ANDROID_COMMAND_EXIT:1');self.assertEqual(read_ref(self.d.store.root,row['stderrRef']),CLOSED);self.assertEqual(self.f.root_error.__notes__ if hasattr(self.f.root_error,'__notes__')else[],[])
 def test_still_uid2000_refuses_without_second_root(self):
  self.f.after_uid=b'2000\n'
  with self.assertRaisesRegex(ValueError,'ACTUAL_EMULATOR_ROOT_UID_REQUIRED'):self.prepare()
  self.assertEqual(self.root_count(),1);self.assertFalse(hasattr(self.d,'content_reader_preparation'))
 def test_foreign_boot_refuses(self):
  self.f.boot_after=OTHER
  with self.assertRaisesRegex(ValueError,'SAME_KERNEL_BOOT_REQUIRED'):self.prepare()
  self.assertEqual(self.root_count(),1)
 def test_wrong_serial_device_refuses_before_anycommand(self):
  self.d.serial='emulator-5584'
  with self.assertRaisesRegex(ValueError,'ROOT_ONLY_OWNED'):self.prepare()
  self.assertEqual(self.f.calls,[])
 def test_wrong_serial_in_durable_root_argv_refuses(self):
  self.f.wrong_argv=True
  with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertEqual(self.root_count(),1);self.assertNotIn(['wait-for-device'],[v[0]for v in self.f.calls])
 def test_incomplete_capture_never_confirms(self):
  self.f.root_complete=False
  with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertEqual(len(self.f.calls),3)
 def test_corrupt_original_stderr_hash_refuses(self):
  self.f.corrupt=True
  with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertTrue(any('COLD_REF_SHA'in v for v in e.exception.__notes__));self.assertEqual(len(self.f.calls),3)
 def test_cleanup_notes_refuse_even_exactstderr(self):
  self.f.root_notes=['COMMAND_STDERR_CLOSE_FAILED']
  with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertEqual(e.exception.__notes__,self.f.root_notes);self.assertEqual(len(self.f.calls),3)
 def test_verifier_EIO_preserves_original_firstfailure(self):
  original=read_ref
  def fail(root,ref):
   if self.root_count()and ref.get('path')=='receipts/command.jsonl':raise OSError('injected receipt EIO')
   return original(root,ref)
  with patch('aeris_runtime.once_reader.read_ref',fail):
   with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertIsInstance(e.exception.__cause__,OSError);self.assertEqual(len(self.f.calls),3)
 def test_deadline_not_extended_after_uncertain_root(self):
  self.f.after_root_jump=31_000_000_000
  with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertIsInstance(e.exception.__cause__,TimeoutError);self.assertEqual(len(self.f.calls),3)
 def test_all_commands_share_original30s_cap(self):
  self.prepare(deadline=90_000_000_000);self.assertEqual({v[1]for v in self.f.calls},{30_000_010_000});self.assertEqual({v[2]for v in self.f.calls},{2048})
 def test_shorter_caller_deadline_preserved(self):
  self.prepare(deadline=2_000_000_000);self.assertEqual({v[1]for v in self.f.calls},{2_000_000_000})
 def test_other_stderr_not_accepted(self):
  self.f.root_err=b'permission denied\n'
  with self.assertRaises(RuntimeError)as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertEqual(len(self.f.calls),3)
 def test_exit2_not_accepted(self):
  self.f.root_exit=2
  with self.assertRaisesRegex(RuntimeError,'ANDROID_COMMAND_EXIT:2')as e:self.prepare()
  self.assertIs(e.exception,self.f.root_error);self.assertEqual(len(self.f.calls),3)
 def test_stdout_nonempty_unknown_root_not_accepted(self):
  self.f.root_out=b'restarting adbd as root\n'
  with self.assertRaises(RuntimeError):self.prepare()
  self.assertEqual(len(self.f.calls),3)
 def test_root_normal_exit0_still_requires_actualUID0(self):
  self.f.root_exit=0;self.f.root_err=b'';self.f.root_out=b'restarting adbd as root\n';self.prepare();p=self.prep();self.assertFalse(p['originalRootCommandFailed']);self.assertEqual(p['rootCommandOutcome'],'COMMAND_EXIT0_OBSERVED_NOT_UID_PROOF');self.assertEqual(self.root_count(),1)
 def test_already_uid0_does_not_root(self):
  self.f.uid=b'0\n';self.prepare();self.assertEqual(self.root_count(),0);self.assertIsNone(self.prep()['rootRef']);self.assertEqual(self.prep()['rootCommandOutcome'],'NOT_REQUESTED_UID_ALREADY0')
 def test_invalid_bootUUID_refuses_before_root(self):
  self.f.boot_before=b'not-a-boot-id\n'
  with self.assertRaisesRegex(ValueError,'ORIGINAL_KERNEL_BOOT_UUID'):self.prepare()
  self.assertEqual(self.root_count(),0)
 def test_no_method_retry_after_failure(self):
  self.f.after_uid=b'2000\n'
  with self.assertRaises(ValueError):self.prepare()
  with self.assertRaisesRegex(ValueError,'NO_RETRY_AFTER_ATTEMPT'):self.prepare()
  self.assertEqual(self.root_count(),1)
 def test_expired_deadline_no_dispatch(self):
  with self.assertRaisesRegex(TimeoutError,'SAME30S_DEADLINE'):self.prepare(deadline=9999)
  self.assertEqual(self.f.calls,[])
 def test_preparation_commit_over_deadline_not_published(self):
  original=self.d.store.receipt
  def delayed(name,*args,**kwargs):
   ref=original(name,*args,**kwargs)
   if name=='product-content-reader-preparation.json':self.f.t=30_000_010_000
   return ref
  self.d.store.receipt=delayed
  with self.assertRaisesRegex(TimeoutError,'PREPARATION_DURABILITY_DEADLINE'):self.prepare()
  self.assertFalse(hasattr(self.d,'content_reader_preparation'));self.assertEqual(self.root_count(),1)
 def test_nonandroid_frozen_source_and_owner_same_asHOLD02(self):
  hold=json.loads((R/'evidence/navfix13/diagnostic-builder-HOLD02.json').read_bytes());expected={v['path']:v['sha256']for v in hold['files']}
  for p in B.rglob('*'):
   if p.is_file()and '__pycache__'not in p.parts and str(p.relative_to(B))not in('aeris_runtime/android.py','aeris_runtime/assets/pipeline-writer-pins.json'):
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),expected[str(p.relative_to(R))],str(p))
  for name in('root-owner-navfix13.py','scenario-navfix13.py'):
   p=B.parent/name;self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),expected[str(p.relative_to(R))])
 def test_android_changes_only_owned_preparation_captures_and_bootread(self):
  p=B/'aeris_runtime/android.py';new=p.read_text();old=(R/'evidence/navfix13/candidates/6bfe4119afe27d1608a0c529bb6ae447501609d2dec0cda3879e4b36f8a86b17/source/aeris_runtime/android.py').read_text()
  originalprep=old[old.index(' def prepare_content_reader('):old.index(' def open_saf_document(')];start=new.index(' def _content_reader_capture(');end=new.index(' def open_saf_document(');restored=new[:start]+originalprep+new[end:]
  restored=restored.replace('self._android_ready=None;self._content_reader_preparation_attempted=False','self._android_ready=None').replace("(['root'],['wait-for-device'],['shell','id','-u'],['shell','cat','/proc/sys/kernel/random/boot_id'])","(['root'],['wait-for-device'],['shell','id','-u'])")
  self.assertEqual(restored,old)
 def test_boot_read_command_allowlist_exact_target(self):
  self.d.status_socket=None;self.d._install_authorization=None
  self.assertEqual(self.d._command_bound(['shell','cat','/proc/sys/kernel/random/boot_id']),2048)
  self.d.serial='emulator-5584'
  with self.assertRaises(ValueError):self.d._command_bound(['shell','cat','/proc/sys/kernel/random/boot_id'])
if __name__=='__main__':unittest.main(verbosity=2)
