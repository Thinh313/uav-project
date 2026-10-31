"""Reuse frozen G3 fake-subprocess cases against isolated additive G4 launcher."""
from pathlib import Path
import importlib.util,unittest,types
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old_path=ROOT/'pilot/beta06g3/test_runtime.py';old=types.ModuleType('namespace_adapted_frozen_g3tests');old.__file__=str(old_path)
# Adapt only fixture output namespace in memory; frozen G3 test bytes stay untouched.
exec(compile(old_path.read_text().replace('generation03','generation04'),str(old_path),'exec'),old.__dict__)
g4=load('isolated_g4runtime',ROOT/'pilot/beta06g4/flight/runtime.py');old.m=g4
class G4FakeRunner(old.FakeRunner):
 def info(self):
  i=super().info();i['Name']='/aeris-beta06g4-'+old.RID;i['Config']['Labels']['aeris.task']='beta06g4';return i
 def capture(self,argv,label,kind='meta'):
  c=super().capture(argv,label,kind)
  if label=='attach':
   (self.out/'attach-stderr.bin').write_bytes(b'SERIAL0 on TCP port 5760\n')
   if self.mode=='normal':(self.out/'attach-stdout.bin').write_bytes(b'Waiting for connection\n')
  return c
old.FakeRunner=G4FakeRunner
NAMES=[n for n in unittest.defaultTestLoader.getTestCaseNames(old.Tests) if n not in ['test_four_retained_cap','test_exact_metadata_rejects_old_profile']]
def suite():return unittest.TestSuite(old.Tests(n) for n in NAMES)
if __name__=='__main__':
 result=unittest.TextTestRunner().run(suite());raise SystemExit(not result.wasSuccessful())
