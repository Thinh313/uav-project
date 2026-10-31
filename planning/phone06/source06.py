"""Offline source closure/syntax only; no compilation, servers, ADB or runtime startup."""
from pathlib import Path
import ast,json,hashlib,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'native/phone06'));from overlay import source
from rig06 import derived
sha=lambda b:hashlib.sha256(b).hexdigest()
def inspect06():
 native=source();deps=json.loads((R/'planning/phone06/runtime-dependencies.json').read_text())['files'];visual=json.loads((R/'pilot/phone06/dependencies.json').read_text())['files']
 for p,s in deps.items():
  if sha((R/p).read_bytes())!=s:raise ValueError('HOST_DEPENDENCY_SHA:'+p)
 for d in visual.values():
  p=R/d['path'];b=p.read_bytes()
  if p.is_symlink()or len(b)!=d['bytes']or sha(b)!=d['sha256']:raise ValueError('OBSERVER_FULL_ASSET_SHA:'+str(p))
 own={}
 for folder in ['native/phone06','pilot/phone06','planning/phone06']:
  for p in sorted((R/folder).rglob('*')):
   if not p.is_file()or any(x.startswith('.')or x in ['qa','dist','__pycache__']for x in p.relative_to(R/folder).parts):continue
   if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
   elif p.suffix=='.mjs':subprocess.run(['node','--check',str(p)],check=True,capture_output=True,timeout=10)
   own[str(p.relative_to(R))]=sha(p.read_bytes())
 helper,controller,lineage=derived();ast.parse(helper);ast.parse(controller)
 files={**native,**deps,**{d['path']:d['sha256']for d in visual.values()},**own}
 return {'status':'PASS_SOURCE_CLOSURE_AND_SYNTAX_ONLY','sourceId':sha(json.dumps(files,sort_keys=True).encode()),'files':files,'ownFiles':own,'nativeDependencyCount':len(native),'hostDependencyCount':len(deps),'fullViewerAssetCount':len(visual),'rigLineage':lineage,'actualPhoneOrAP':'NOT_CHECKED','broadHistoricalPreservation':'SEPARATE_KNOWN_MISSING_PATHS_NOT_REPAIRED'}
if __name__=='__main__':print(json.dumps(inspect06(),indent=2))
