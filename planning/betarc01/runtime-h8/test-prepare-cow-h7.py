"""Actual prepare writer AST, disposable hardlinks only, never actual H6 writes."""
from pathlib import Path
import ast,os,stat,tempfile,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;tree=ast.parse((B/'prepare-source-gate.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='write_generated');env=dict(Path=Path,os=os,stat=stat,P=B/'prepare-source-gate.py',SOURCE=B/'source');exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_H7_atomic_generated_writer','exec'),env);write=env['write_generated']
class Cow(unittest.TestCase):
 def test_actual_hardlink_copy_on_write_and_prepublication_failure(self):
  for fault in [False,True]:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory(prefix='cow-',dir=B)as tmp:
    root=Path(tmp)/'source';assets=root/'aeris_runtime/assets';assets.mkdir(parents=True);old=Path(tmp)/'old';old.write_bytes(b'original');old.chmod(0o440);target=assets/'product-input-closure.json';os.link(old,target);before=old.stat();identity=(old.read_bytes(),before.st_ino,stat.S_IMODE(before.st_mode))
    if fault:
     with patch.object(os,'fsync',side_effect=OSError('INJECTED_BEFORE_PUBLISH')),self.assertRaises(OSError):write(target,b'new',_source_root=root)
     self.assertEqual(target.read_bytes(),b'original');self.assertEqual(target.stat().st_ino,before.st_ino)
    else:
     write(target,b'new',_source_root=root);self.assertEqual(target.read_bytes(),b'new');self.assertNotEqual(target.stat().st_ino,before.st_ino);self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o440)
    self.assertEqual((old.read_bytes(),old.stat().st_ino,stat.S_IMODE(old.stat().st_mode)),identity)
 def test_scope_symlink_and_pending_refused(self):
  with tempfile.TemporaryDirectory(prefix='cow-',dir=B)as tmp:
   root=Path(tmp)/'source';assets=root/'aeris_runtime/assets';assets.mkdir(parents=True);target=assets/'pipeline-writer-pins.json';target.write_bytes(b'old')
   with self.assertRaises(AssertionError):write(assets/'foreign.json',b'new',_source_root=root)
   pending=target.with_name('.'+target.name+'.pending-h7');pending.write_bytes(b'held')
   with self.assertRaises(AssertionError):write(target,b'new',_source_root=root)
   pending.unlink();target.unlink();target.symlink_to(assets/'not-there')
   with self.assertRaises(AssertionError):write(target,b'new',_source_root=root)
if __name__=='__main__':unittest.main(verbosity=2)
