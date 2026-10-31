"""Explicit one-time execution seal. Run only after source/native build is fixed."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/betastability02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
predecessor=R/'evidence/missionbeta01/source-pins07.json'
old=json.loads(predecessor.read_text());files={}
for name,h in old['files'].items():
 p=R/name
 assert p.is_file() and not p.is_symlink(), 'PREDECESSOR_EXECUTION_FILE_MISSING_OR_LINK:'+name
 assert sha(p)==h, 'PREDECESSOR_EXECUTION_SOURCE_DRIFT:'+name
 files[name]=h
for folder in ['pilot/betastability02','native/betastability02']:
 for p in (R/folder).rglob('*'):
  if any(c in {'.build','.swift-cache','module-cache','__pycache__'} or c.startswith('.module-cache') for c in p.parts):continue
  if p.is_file():
   assert not p.is_symlink(), 'NEW_EXECUTION_SYMLINK:'+str(p)
   files[str(p.relative_to(R))]=sha(p)
apk=R/'native/betastability02/dist/aeris-betastability02-development01.apk'
assert apk.is_file(), 'DEVELOPMENT_APK_NOT_BUILT'
assert shutil.disk_usage(R).free>=20*2**30, 'DISK_ADMISSION_20GIB'
result={'format':'betastability02-execution-pins','version':1,'files':files,
 'predecessorPinFile':'evidence/missionbeta01/source-pins07.json','predecessorPinFileSha256':sha(predecessor),
 'legacyMissing':old.get('legacyMissing',[]),
 'scope':'WHOLE_PRESENT_PREDECESSOR_EXECUTION_CLOSURE_PLUS_ISOLATED_SUCCESSOR_RUNTIME_AND_APK; NOT_OLD_ALL_ARTIFACT_ACCEPTANCE',
 'maxAPRequests':12,'maxRetainedAPContainers':12,'maxHostStarts':8,'maxOwnEvidenceBytes':2*2**30,'taskWallBudgetMinutes':180,
 'speedup':1,'admissionGiB':20,'floorGiB':10,'floorReserveMiB':256,'admissionSamples':31,'admissionDeclineLimitMiB':256,'forecastSeconds':15}
with(E/'source-pins07.json').open('x')as f:json.dump(result,f,indent=2)
print('EXECUTION_PINS',len(files),'legacy preexisting gaps',len(result['legacyMissing']))
