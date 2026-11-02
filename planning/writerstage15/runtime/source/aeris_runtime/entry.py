"""Fresh candidate process entry: reject cached active runtime/module origins."""
from pathlib import Path
import argparse,importlib,json,os,sys
from .candidate import load

def module_origin_receipt(candidate):
 root=(Path(candidate)/'source').resolve();origins={}
 for name,module in list(sys.modules.items()):
  if name=='aeris_runtime' or name.startswith('aeris_runtime.'):
   origin=getattr(module,'__file__',None)
   if origin is None or not Path(origin).resolve().is_relative_to(root):raise RuntimeError('ACTIVE_OR_CACHED_RUNTIME_ORIGIN:'+name)
   origins[name]=str(Path(origin).resolve().relative_to(root))
 from .dependencies import loaded_leaf_origins
 origins['_explicitPinnedLeafModules']=loaded_leaf_origins()
 return origins

def main():
 parser=argparse.ArgumentParser();parser.add_argument('component',choices=['backend','ap_supervisor','inspect']);parser.add_argument('--config');args=parser.parse_args()
 path=Path(os.environ['AERIS_CANDIDATE_DIR']);digest=os.environ['AERIS_CANDIDATE_SHA256'];manifest=load(path,digest);module_origin_receipt(path)
 if args.component=='inspect':print(json.dumps({'candidateSHA256':digest,'moduleOrigins':module_origin_receipt(path),'nativeSourceSHA256':manifest['native']['sourceSHA256']}));return
 if not args.config:raise ValueError('EXPLICIT_CONFIG_REQUIRED')
 module=importlib.import_module('aeris_runtime.'+args.component);module_origin_receipt(path);sys.argv=[module.__file__,'--config',args.config];module.main()
if __name__=='__main__':main()
