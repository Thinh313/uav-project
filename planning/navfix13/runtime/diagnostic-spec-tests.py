"""Pure constructor/AST mocks: selectedspecandavdIndexprerequisite surviveforwarding."""
from pathlib import Path
import ast,hashlib,json,os,tempfile,time,types,unittest
R=Path(__file__).resolve().parents[3];P=Path(__file__).parent/'source/aeris_runtime/product_runtime.py'
class SpecTests(unittest.TestCase):
 def setUp(self):
  self.tree=ast.parse(P.read_text());self.cls=next(x for x in self.tree.body if isinstance(x,ast.ClassDef)and x.name=='WorkbenchRuntime');self.init=next(x for x in self.cls.body if isinstance(x,ast.FunctionDef)and x.name=='__init__');self.bootstrap=next(x for x in self.cls.body if isinstance(x,ast.FunctionDef)and x.name=='bootstrap')
  self.tmp=tempfile.TemporaryDirectory(prefix='diagnostic-spec-',dir=R/'evidence/navfix13');self.addCleanup(self.tmp.cleanup);self.spec=Path(self.tmp.name)/'declared-spec.json';self.value={'AVD':'/declared/avd','prerequisites':{'avdIndex':{'path':'/declared/avd.ini','sha256':'a'*64}}};self.spec.write_text(json.dumps(self.value));env={'Path':Path,'json':json,'hashlib':hashlib,'os':os,'time':time,'repository':lambda:R,'load':lambda*a:{'native':{'productKind':'BETASIM_INTEGRATED'}}}
  def need(v,name):
   if not v:raise RuntimeError(name)
  env['need']=need;cl=ast.ClassDef(name='ConstructorOnly',bases=[],keywords=[],body=[self.init],decorator_list=[]);exec(compile(ast.fix_missing_locations(ast.Module(body=[cl],type_ignores=[])),str(P),'exec'),env);self.C=env['ConstructorOnly'];self.env=env
 def make(self):return self.C(R/'evidence/navfix13/candidates/mock','b'*64,evidence=R/'evidence/navfix13/s01',planning=R/'planning/navfix13',spec=self.spec)
 def test_constructor_retains_exactresolvedpath_SHA_and_index(self):
  o=self.make();self.assertEqual(o.spec_path,self.spec.resolve());self.assertEqual(o.specSHA256,hashlib.sha256(self.spec.read_bytes()).hexdigest());self.assertEqual(o.spec,self.value);self.assertIn('avdIndex',o.spec['prerequisites'])
 def test_guardian_argv_uses_selectedspec_not_hardcodedoldspec(self):
  argv=next(v.value for v in ast.walk(self.bootstrap)if isinstance(v,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='argv'for t in v.targets));parts=argv.elts;ix=next(i for i,x in enumerate(parts)if isinstance(x,ast.Constant)and x.value=='--spec');self.assertEqual(ast.unparse(parts[ix+1]),'str(self.spec_path)');self.assertNotIn('runtime-observe04/emulator-spec.json',ast.unparse(self.bootstrap))
 def test_selected_spec_mutation_fails_beforeguardian_constructed(self):
  o=self.make();o.spec_path.write_text('{}');check=next(x for x in self.bootstrap.body if isinstance(x,ast.Expr)and isinstance(x.value,ast.Call)and any(isinstance(a,ast.Constant)and a.value=='DECLARED_SPEC_BYTES_DRIFT_BEFORE_GUARDIAN'for a in x.value.args));env={**self.env,'self':o}
  with self.assertRaisesRegex(RuntimeError,'DECLARED_SPEC_BYTES_DRIFT'):exec(compile(ast.Module(body=[check],type_ignores=[]),str(P),'exec'),env)
 def test_exact_spec_propagation_delta_only_fromHOLD01(self):
  hold=json.loads((R/'evidence/navfix13/diagnostic-builder-HOLD01.json').read_bytes());expected=next(v['sha256']for v in hold['files']if v['path']==str(P.relative_to(R)));text=P.read_text()
  text=text.replace("self.spec_path=Path(spec).resolve();self.spec_raw=self.spec_path.read_bytes();self.specSHA256=hashlib.sha256(self.spec_raw).hexdigest();self.spec=json.loads(self.spec_raw);self.budget=None","self.spec=json.loads(Path(spec).read_bytes());self.budget=None")
  text=text.replace("  need(hashlib.sha256(self.spec_path.read_bytes()).hexdigest()==self.specSHA256,'DECLARED_SPEC_BYTES_DRIFT_BEFORE_GUARDIAN')\n",'').replace('str(self.spec_path)',"str(self.repo/'evidence/runtime-observe04/emulator-spec.json')")
  self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),expected)
 def test_spec_guard_precedes_guardian_creation(self):
  guards=[x.lineno for x in ast.walk(self.bootstrap)if isinstance(x,ast.Constant)and x.value=='DECLARED_SPEC_BYTES_DRIFT_BEFORE_GUARDIAN'];constructs=[x.lineno for x in ast.walk(self.bootstrap)if isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=='DiagnosticJob'];self.assertEqual(len(guards),1);self.assertEqual(len(constructs),1);self.assertLess(guards[0],constructs[0])
if __name__=='__main__':unittest.main(verbosity=2)
