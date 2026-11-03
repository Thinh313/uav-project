"""Actual Node hook import/link and exact pre-spawn dispatch, no SDK/AP actors."""
from pathlib import Path
import copy,hashlib,json,os,subprocess,sys,tempfile,types,unittest
from unittest.mock import patch
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from aeris_runtime.product_inputs import validate
from aeris_runtime.node_alias_h9 import companion_argv,LOADER,LEGACY,ENTRY
from aeris_runtime.product_runtime import WorkbenchRuntime
GRAPH=validate();NODE='/usr/local/bin/node';ENC=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'))
def manifest():return{'native':{'productKind':'BETASIM_INTEGRATED'},'simulationOnly':True,'productSourceSHA256':copy.deepcopy(GRAPH['pins']),'productInputClosure':copy.deepcopy(GRAPH)}
def run_node(m,script,*,vm=False,sha_override=None,env=None):
 with tempfile.TemporaryDirectory(prefix='node-',dir=B)as tmp:
  p=Path(tmp)/'synthetic-source-only-manifest.json';raw=ENC(m);p.write_text(raw+'\n');sha=sha_override or hashlib.sha256(raw.encode()).hexdigest();argv=[NODE,*(['--experimental-vm-modules']if vm else[]),'--import',str(R/LOADER),'--input-type=module','-e',script,'--','--manifest',str(p),'--candidate-sha',sha];return subprocess.run(argv,cwd=R,capture_output=True,timeout=15,env=env)
class AliasH9(unittest.TestCase):
 def test_actual_server_import_and_every_selected_alias_without_actor_start(self):
  script="""import{selectedBoundary as b}from'./planning/betarc01/node_alias_h9/verified-loader.mjs';await import('./planning/betarc01/product/server-codec09c.mjs');for(const k of Object.keys(b.aliases)){await import(new URL(k,'file://'+process.cwd()+'/').href);}console.log(JSON.stringify({actualServerImported:true,aliases:Object.keys(b.aliases).length,actorsStarted:false}));"""
  p=run_node(manifest(),script);self.assertEqual(p.returncode,0,p.stderr.decode());self.assertEqual(json.loads(p.stdout),{'actualServerImported':True,'aliases':6,'actorsStarted':False})
 def test_actual_companion_graph_link_without_evaluating_top_level(self):
  script="""import vm from'node:vm';import{fileURLToPath,pathToFileURL}from'node:url';import{selectedBoundary as b}from'./planning/betarc01/node_alias_h9/verified-loader.mjs';const cache=new Map();async function get(u){if(cache.has(u))return cache.get(u);if(u.startsWith('node:')){const x=await import(u);const m=new vm.SyntheticModule(Object.keys(x),function(){for(const k of Object.keys(x))this.setExport(k,x[k]);},{identifier:u});cache.set(u,m);return m;}const m=new vm.SourceTextModule(b.verifyFile(fileURLToPath(u)).toString(),{identifier:u});cache.set(u,m);return m;}const entry=pathToFileURL(process.cwd()+'/planning/betarc01/runtime/product-companion-rc01.mjs').href;const m=await get(entry);await m.link((s,p)=>get(b.resolveSpecifier(s,p.identifier)));console.log(JSON.stringify({linked:cache.size,evaluated:false,status:m.status}));"""
  p=run_node(manifest(),script,vm=True);self.assertEqual(p.returncode,0,p.stderr.decode());v=json.loads(p.stdout);self.assertGreaterEqual(v['linked'],90);self.assertEqual((v['evaluated'],v['status']),(False,'linked'))
 def test_real_hook_forgeries_and_undeclared_imports_fail_closed(self):
  base=manifest();target='planning/betarc01/tar_profile_h7/native-cold-h7.mjs';old='planning/nativejournal17/native-cold17.mjs';cases=[]
  q=copy.deepcopy(base);q['productInputClosure']['aliases'].pop(old);cases.append(('missingAlias',q,None))
  q=copy.deepcopy(base);q['productInputClosure']['aliases'][old]='../outside.mjs';cases.append(('outside',q,None))
  q=copy.deepcopy(base);q['productSourceSHA256'].pop(target);q['productInputClosure']['pins'].pop(target);cases.append(('unheldTarget',q,None))
  q=copy.deepcopy(base);q['productSourceSHA256'][target]='0'*64;q['productInputClosure']['pins'][target]='0'*64;cases.append(('wrongHash',q,None))
  q=copy.deepcopy(base);q['productSourceSHA256'][old]=hashlib.sha256((R/old).read_bytes()).hexdigest();q['productInputClosure']['pins'][old]=q['productSourceSHA256'][old];cases.append(('oldFallback',q,None))
  q=copy.deepcopy(base);q['productInputClosure']['aliases'][old]=LEGACY;cases.append(('chain',q,None))
  q=copy.deepcopy(base);q['productInputClosure']['pins'][target]='f'*64;cases.append(('closureMismatch',q,None))
  cases.append(('manifestDigest',copy.deepcopy(base),'0'*64))
  for label,m,digest in cases:
   with self.subTest(label=label):p=run_node(m,"await import('./planning/betarc01/product/server-codec09c.mjs')",sha_override=digest);self.assertNotEqual(p.returncode,0);self.assertIn(b'PRODUCT_LOADER_H9_',p.stderr)
  for spec in ['data:text/javascript,export default 1','https://invalid.test/x.mjs','fs','./planning/nativejournal17/native-tar17.mjs?bypass=1','./planning/nativejournal17/archive-verifier-unknown.mjs']:
   with self.subTest(spec=spec):p=run_node(base,'await import('+json.dumps(spec)+');');self.assertNotEqual(p.returncode,0);self.assertIn(b'PRODUCT_LOADER_H9_',p.stderr)
  with tempfile.TemporaryDirectory(prefix='symlink-',dir=B)as tmp:
   p=Path(tmp)/'target.mjs';p.write_text('export default 1;');s=Path(tmp)/'alias.mjs';s.symlink_to(p);name=str(s.relative_to(R));m=copy.deepcopy(base);m['productInputClosure']['aliases'][old]=name;m['productSourceSHA256'][name]=hashlib.sha256(p.read_bytes()).hexdigest();m['productInputClosure']['pins'][name]=m['productSourceSHA256'][name];q=run_node(m,'');self.assertNotEqual(q.returncode,0);self.assertIn(b'MODULE_SYMLINK',q.stderr)
 def test_actual_central_start_dispatch_argv_and_pre_spawn_refusal(self):
  owner=types.SimpleNamespace(candidate=R/'evidence/nativejournal17/candidates'/('a'*64),digest='a'*64,root=R/'evidence/betarc01/g105',manifest=manifest(),budget=types.SimpleNamespace(snapshot=lambda:{'counters':{'cases':1}}),case={'companion':None,'context':{'run':'mock'}},event=lambda *x:None)
  argv=[NODE,'--import',str(R/LEGACY),str(R/ENTRY),'--manifest',str(owner.candidate/'candidate.json'),'--candidate-sha',owner.digest,'--descriptor',str(owner.root/'reports/product-descriptor-01.json'),'--owner-pid',str(os.getpid()),'--maximum-seconds','540']
  seen=[]
  class Job:
   def __init__(self,*a):self.process=types.SimpleNamespace(pid=1)
   def start(self,a):seen.append(a)
  with patch('aeris_runtime.product_runtime.DiagnosticJob',Job):WorkbenchRuntime.start_companion(owner,argv)
  self.assertEqual(seen[0][2],str(R/LOADER));self.assertEqual(argv[2],str(R/LEGACY));self.assertEqual(seen[0][:2],argv[:2]);self.assertEqual(seen[0][3:],argv[3:])
  for change in ['flag','manifest','sha','pid','preload','alias','aliasTarget']:
   bad=list(argv);m=copy.deepcopy(owner.manifest)
   if change=='flag':bad[6]='--eval'
   elif change=='manifest':bad[5]+='.foreign'
   elif change=='sha':bad[7]='b'*64
   elif change=='pid':bad[11]='1'
   elif change=='preload':bad.insert(1,'--inspect')
   elif change=='alias':m['productInputClosure']['aliases'].pop('planning/nativejournal17/native-cold17.mjs')
   else:m['productInputClosure']['aliases']['planning/nativejournal17/native-cold17.mjs']='planning/betarc01/tar_profile_h7/native-tar.mjs'
   owner.manifest=m
   with self.subTest(change=change),self.assertRaises(ValueError):companion_argv(owner,bad)
   owner.manifest=manifest()
  for key in ['NODE_OPTIONS','NODE_PATH']:
   with patch.dict(os.environ,{key:'uncontrolled'}),self.assertRaises(ValueError):companion_argv(owner,argv)
  self.assertEqual(len(seen),1)
if __name__=='__main__':unittest.main(verbosity=2)
