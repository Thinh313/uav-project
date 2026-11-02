"""Strict framing boundary only. Registry contents here are structural fixtures,
not verified lifecycle evidence or Android acceptance. No actors.
"""
from pathlib import Path
import hashlib,io,os,sys,tarfile,tempfile,unittest
R=Path(__file__).resolve().parents[3];H=Path(__file__).resolve().parent;os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(H/'source'),str(R)]
from aeris_runtime.native17 import table
class Shape(unittest.TestCase):
 def raw(self):
  out=io.BytesIO()
  with tarfile.open(fileobj=out,mode='w',format=tarfile.USTAR_FORMAT)as t:
   for n in('files','files/product-input-registry17','files/product-input-archives17','files/product-input-archives17/'+'a'*64):
    m=tarfile.TarInfo(n);m.type=tarfile.DIRTYPE;t.addfile(m)
   for n,b in[('files/product-input-registry17/highwater.aj17',b'STRUCTURAL_ONLY'),('files/product-input-archives17/'+'a'*64+'/'+'b'*32+'.aj02',b'AERIS_INPUT_JOURNAL_V2\n')]:
    m=tarfile.TarInfo(n);m.size=len(b);t.addfile(m,io.BytesIO(b))
  return out.getvalue()
 def test_generic_post_apply_namespaces_remain_allowed(self):
  with tempfile.TemporaryDirectory(prefix='mock-tar17-',dir=H)as p:
   path=Path(p)/'archive.tar';path.write_bytes(self.raw());rows=table(path);self.assertEqual(len(rows),2);self.assertIn('files/product-input-registry17/highwater.aj17',rows)
 def test_nonzero_hidden_trailer_rejected(self):
  with tempfile.TemporaryDirectory(prefix='mock-tar17-',dir=H)as p:
   path=Path(p)/'hidden.tar';path.write_bytes(self.raw()+b'HIDDEN')
   with self.assertRaisesRegex(ValueError,'TAR_TRAILING'):table(path)
 def test_missing_both_eoa_blocks_rejected(self):
  raw=self.raw();at=0
  while raw[at:at+512]!=bytes(512):size=int(raw[at+124:at+136].split(b'\0',1)[0].strip(),8);at+=512+((size+511)//512)*512
  with tempfile.TemporaryDirectory(prefix='mock-tar17-',dir=H)as p:
   path=Path(p)/'no-eoa.tar';path.write_bytes(raw[:at])
   with self.assertRaisesRegex(ValueError,'TAR_HEADER_OR_EOA_TRUNCATED'):table(path)
if __name__=='__main__':unittest.main(verbosity=2)
