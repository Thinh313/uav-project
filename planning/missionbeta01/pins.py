from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/missionbeta01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R/'evidence/betaworkbench05/flight-pins06.json').read_text());files={};gaps=[]
for name,h in old['files'].items():
 p=R/name
 if not p.is_file():gaps.append({'path':name,'expectedSha256':h,'status':'PREEXISTING_MISSING_NOT_EXECUTION_INPUT'});continue
 assert sha(p)==h,name
 if not name.startswith('evidence/'):files[name]=h
for name in ['evidence/workbench01/handoff-manifest.json','evidence/beta06/generation17/flight-pins01.json','.local/beta06g3/arducopter','runtime/sitl/copter.parm','pilot/field02/flight/sitl.parm']:
 p=R/name;assert p.is_file(),name;files[name]=sha(p)
for folder in ['pilot/missionbeta01','native/missionbeta01']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and '.build'not in p.parts:files[str(p.relative_to(R))]=sha(p)
assert shutil.disk_usage(R).free>=20*2**30
result={'format':'missionbeta01-execution-pins','version':1,'files':files,'legacyPinFileSha256':sha(R/'evidence/betaworkbench05/flight-pins06.json'),'legacyMissing':gaps,'scope':'PRESENT_PREDECESSOR_EXECUTION_CODE_ASSETS_PLUS_NEW_SUCCESSOR_FILES_AND_EXPLICIT_RUNTIME_INPUTS; NOT_OLD_ALL_ARTIFACT_ACCEPTANCE','maxAPRequests':13,'maxRetainedAPContainers':12,'maxHostStarts':8,'speedup':1,'admissionGiB':20,'floorGiB':10}
with(E/'source-pins07.json').open('x')as f:json.dump(result,f,indent=2)
print('EXECUTION_PINS',len(files),'legacy gaps',len(gaps))
