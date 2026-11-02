"""Finite receiver negatives plus historical realbytes; never current authorization."""
from pathlib import Path
import hashlib,io,json,os,subprocess,sys,tarfile,tempfile,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;P=HERE.parent;sys.path.insert(0,str(P));import receiver17 as r
class Receiver(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='receiver-fixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def tar(self,names=None):
  out=self.root/'model.tar'
  with tarfile.open(out,'w',format=tarfile.USTAR_FORMAT)as t:
   for name in names or['files/product-input01/'+'a'*32+'.aj02']:
    q=tarfile.TarInfo(name);q.size=len(r.MAGIC);t.addfile(q,io.BytesIO(r.MAGIC))
  return out
 def test_complete_model_unused_never_closed(self):
  p=self.tar();v=r.native_tar(p,r.sha(p.read_bytes()));j=next(iter(v['journals'].values()));self.assertEqual(j['disposition'],'UNUSED');self.assertFalse(j['sourceClosedStatusBound']);self.assertEqual(j['records'],0);self.assertIsInstance(v['tarSHA256'],str)
 def test_wrong_full_tar_hash(self):
  p=self.tar()
  with self.assertRaisesRegex(ValueError,'COMPLETE_ORIGINAL_TAR_SHA'):r.native_tar(p,'f'*64)
 def test_trailing_nonzero_refused_even_hash_matches(self):
  p=self.tar();p.write_bytes(p.read_bytes()+b'EVIL')
  with self.assertRaisesRegex(ValueError,'TRAILING'):r.native_tar(p,r.sha(p.read_bytes()))
 def test_truncated_eoa_refused(self):
  p=self.tar();p.write_bytes(p.read_bytes()[:1024])
  with self.assertRaisesRegex(ValueError,'EOA'):r.native_tar(p,r.sha(p.read_bytes()))
 def test_dot_empty_parent_components(self):
  for name in ['files/./x','files//x','files/../x']:
   p=self.tar([name])
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'PATH_COMPONENTS'):r.native_tar(p,r.sha(p.read_bytes()))
 def test_tar_hardlink_no_extract(self):
  p=self.root/'hard.tar'
  with tarfile.open(p,'w',format=tarfile.USTAR_FORMAT)as t:
   q=tarfile.TarInfo('files/alias');q.type=tarfile.LNKTYPE;q.linkname='files/target';t.addfile(q)
  with self.assertRaisesRegex(ValueError,'NO_LINK'):r.native_tar(p,r.sha(p.read_bytes()))
 def test_unresolved_header_torn_is_not_closed(self):
  self.assertFalse(r.aj02(r.MAGIC)['sourceClosedStatusBound'])
  with self.assertRaisesRegex(ValueError,'TORN'):r.aj02(r.MAGIC+b'\0')
 def test_cli_historical_originals_only(self):
  proof=HERE/'historical-S01-cold-proof.json';v=json.loads(proof.read_bytes());run=subprocess.run([sys.executable,'-B',str(P/'receiver17.py'),'--backup',str(Path(v['androidEvidenceRoot']).parent/'native-restart-metadata.tar'),'--cold-proof',str(proof),'--cold-proof-sha',r.sha(proof.read_bytes()),'--new-source','c'*64,'--expected-head','ROOT'],capture_output=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});self.assertEqual(run.returncode,0,run.stderr.decode());q=json.loads(run.stdout);report=json.loads(__import__('base64').b64decode(q['reportBase64']));self.assertEqual(len(report['originals']),8);self.assertTrue(all(j['disposition']=='UNUSED'and not j['sourceClosedStatusBound']and j['records']==0 for j in report['originals']));self.assertFalse(report['actualFlightAccepted'])
 def test_stale_installed_receipts_fail_same_cold_window(self):
  original=json.loads((HERE/'historical-S01-cold-proof.json').read_bytes());root=Path(original['androidEvidenceRoot']);raw=(root/'receipts/command.jsonl').read_bytes();at=0
  for line in raw.splitlines(keepends=True):
   row=json.loads(line)
   if row['sequence']==21:original['installedPathRef']={'format':'aeris-original-byte-ref','version':3,'path':'receipts/command.jsonl','offset':at,'bytes':len(line),'sha256':r.sha(line)}
   at+=len(line)
  p=self.root/'stale.json';p.write_text(json.dumps(original));run=subprocess.run([sys.executable,'-B',str(P/'receiver17.py'),'--backup',str(root.parent/'native-restart-metadata.tar'),'--cold-proof',str(p),'--cold-proof-sha',r.sha(p.read_bytes()),'--new-source','c'*64,'--expected-head','ROOT'],capture_output=True,timeout=30);self.assertNotEqual(run.returncode,0);self.assertIn(b'COLD_BACKUP_CAUSAL_ORDER',run.stderr)
 def test_foreign_cached_modules_refused_before_import(self):
  proof=json.loads((HERE/'historical-S01-cold-proof.json').read_bytes());foreign=types.ModuleType('aeris_runtime');foreign.__file__=str(self.root/'foreign.py')
  with patch.dict(sys.modules,{'aeris_runtime':foreign}):
   with self.assertRaisesRegex(ValueError,'FOREIGN_CACHED_MODULE_REFUSED'):r.cold_originals(proof,Path(proof['androidEvidenceRoot']).parent/'native-restart-metadata.tar')
if __name__=='__main__':unittest.main(verbosity=2)
