"""Coupled read-only adoption mocks. Actual budget, OnceStore, command capture,
TAR export and cold readers; only Popen is simulated, zero external actors.
"""
from pathlib import Path
import ast,hashlib,io,json,os,shlex,sys,tarfile,tempfile,threading,time,types,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(HERE/'source'),str(R)]
from aeris_runtime import android
from aeris_runtime.native17 import AndroidDomain17
from aeris_runtime.adoption17 import retained_originals17,adopt_existing17,verify_adoption_domain17
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.candidate import load
from aeris_runtime.lifecycle import Context
from aeris_runtime.once_reader import read_receipts
C=R/'evidence/nativejournal17/candidates/f92b5a69bbec960f42b48f03bb2581fe0b6a9929fa69430f761638e3ded5cce7';M=load(C,C.name)
class PopenNoChild:
 calls=[];APK=M['native']['APK_SHA256'];tar=None
 def __init__(self,argv,**kw):
  type(self).calls.append(argv);self.returncode=0;self.pid=700017;self.threads=[];remote=shlex.split(argv[4])if len(argv)==5 and argv[3]=='shell'else argv[3:]
  if remote[:2]==['am','force-stop']:out=b''
  elif remote[:2]==['sh','-c']:out=b'ABSENT\n'
  elif remote[:2]==['pm','path']:out=b'package:/data/app/mock/base.apk\n'
  elif remote[0]=='sha256sum':out=(type(self).APK+'  /data/app/mock/base.apk\n').encode()
  elif remote[:3]==['run-as','vn.rtr.aeris.betasim09','pwd']:out=b'/data/user/0/vn.rtr.aeris.betasim09\n'
  elif remote[:3]==['exec-out','run-as','vn.rtr.aeris.betasim09']:out=type(self).tar
  else:raise AssertionError('UNEXPECTED_ACTOR_COMMAND:'+repr(remote))
  def pipe(raw):
   r,w=os.pipe()
   def send():
    try:
     at=0
     while at<len(raw):at+=os.write(w,raw[at:at+16384])
    finally:os.close(w)
   t=threading.Thread(target=send);t.start();self.threads.append(t);return os.fdopen(r,'rb',buffering=0)
  self.stdout=pipe(out);self.stderr=pipe(b'')
 def poll(self):return self.returncode
 def wait(self,**kwargs):
  for t in self.threads:t.join(timeout=2);assert not t.is_alive()
  return self.returncode
 def terminate(self):raise AssertionError('No child exists')
 def kill(self):raise AssertionError('No child exists')

class Adoption(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.old=retained_originals17();cls.raw=Path(cls.old['backup']['path']).read_bytes()
 def attempt(self,root,*,apk=None,tar=None):
  budget=MetadataBudget(root/'metadata-budget',inventory=lambda:{'metadataBytes':0},free=lambda:64*2**30,mock=True);budget.admit();ctx=Context('mock','1'*32,'2'*32,'QA','3'*32,'WORKBENCH_SIM_V1').value();budget.tick('cases');budget.write('campaign',root/'attempts/attempt-01-cases/case-01.json',encoded({'format':'aeris-product-case','version':1,'context':ctx,'candidateSHA256':C.name,'mockOnly':True}));d=AndroidDomain17('/mock/adb','emulator-5582',root/'sessions/mock/android-api',budget=budget,observer_tag='AERIS_PRODUCT_STATUS');owner=types.SimpleNamespace(root=root,digest=C.name,manifest=M,budget=budget);owner.write=lambda name,value:budget.write('external_task',root/'reports'/name,encoded(value));case={'root':d.root.parent,'device':d,'native':types.SimpleNamespace(retained_inventory_ref=d.store.receipt('mock-retained-inventory.json',{'mockOnly':True})),'context':ctx};PopenNoChild.calls=[];PopenNoChild.APK=apk or M['native']['APK_SHA256'];PopenNoChild.tar=self.raw if tar is None else tar
  with patch.object(android.subprocess,'Popen',PopenNoChild):result=adopt_existing17(owner,case,deadline_ns=time.monotonic_ns()+30_000_000_000)
  return d,owner,case,result
 def test_positive_true_new_apk_byteexact_old_data_no_install_and_cold_replay(self):
  with tempfile.TemporaryDirectory(prefix='mock-adopt17-',dir=HERE)as p:
   d,o,c,result=self.attempt(Path(p));self.assertTrue(result['installDispatchedInThisCase']is False);self.assertEqual(result['oldInstallOutcome'],'UNCONFIRMED_COMMAND_RECEIPT_NOT_PERSISTED');self.assertNotIn('upgrade17',c);self.assertEqual(c['backup17'],self.old['backup']);self.assertEqual(c['receiver17']['raw'],self.old['receiver']['raw']);self.assertTrue(all('install'not in q for q in PopenNoChild.calls));self.assertEqual(verify_adoption_domain17(d.root,c['native'].application_domain_ref,M)['oldInstallOutcome'],result['oldInstallOutcome']);self.assertTrue(all(r['version']==3 for r in read_receipts(d.root,'command')))
 def test_old_or_foreign_apk_stops_before_export_no_reinstall(self):
  for apk in('8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1','0'*64):
   with tempfile.TemporaryDirectory(prefix='mock-adopt17-',dir=HERE)as p,self.subTest(apk=apk),self.assertRaises(Exception):self.attempt(Path(p),apk=apk)
   self.assertTrue(all('install'not in q and'exec-out'not in q for q in PopenNoChild.calls))
 def test_new_private_ledger_or_pending_bytes_refuse_before_apply(self):
  for added in('files/product-input-registry17/highwater.aj17','files/new.pending'):
   out=io.BytesIO()
   with tarfile.open(fileobj=io.BytesIO(self.raw),mode='r:')as old,tarfile.open(fileobj=out,mode='w')as new:
    for m in old:new.addfile(m,old.extractfile(m)if m.isfile()else None)
    m=tarfile.TarInfo(added);m.size=1;new.addfile(m,io.BytesIO(b'x'))
   with tempfile.TemporaryDirectory(prefix='mock-adopt17-',dir=HERE)as p,self.subTest(added=added),self.assertRaisesRegex(ValueError,'EXACT_FULL_PRIVATE_FILE_SET'):self.attempt(Path(p),tar=out.getvalue())
   self.assertTrue(all('install'not in q and'broadcast'not in' '.join(q)for q in PopenNoChild.calls))
 def test_source_entry_scope_and_guards_no_install_hidden_adoption(self):
  source=(HERE/'root-native-rc01.py').read_text();tree=ast.parse(source);calls=[n.func.id for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)];self.assertIn('adopt_existing17',calls);self.assertNotIn('install_upgrade',calls);self.assertNotIn('cold_backup',calls);self.assertNotIn('independent_receiver',calls);self.assertIn("choices=('g101','g102')",source);self.assertLess(source.index('descriptor=owner.start_writer()'),source.index('device.live_check=check'));self.assertIn('seconds=180',source)
if __name__=='__main__':unittest.main(verbosity=2)
