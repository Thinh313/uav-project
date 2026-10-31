"""Independent immutable admission capture; SHA follows historical baseline symlink semantics."""
from pathlib import Path
import json,hashlib,datetime
R=Path.cwd();E=R/'evidence/field02/clockvideo05'
def sha(p):
 p=R/p
 return hashlib.sha256(p.read_bytes()).hexdigest()if p.is_file()else None
def read(p):return json.loads((R/p).read_text())
b=read('evidence/field02/cockpitvideo04/preservation-before.json');inventoryPath='evidence/field02/cockpitvideo04/final-artifact-fingerprints01.json';assert sha(inventoryPath)=='20e4ecfef935c83559159baa1c83b3eebf2e8dc61f485041a7db4b4963675160';inv=read(inventoryPath);assert len(inv['files'])==431
groups={'originalProtected1486':read(b['protectedBaseline'])['files'],'unchangedNative7':read(b['nativeBaseline'])['files'],'previousEvidence1496':b['oldEvidenceFiles'],'frozenCurrentSource93':b['frozenCurrentSources'],'priorCOCKPITVIDEO04Artifacts431':{p:v['sha256']for p,v in inv['files'].items()}}
rows={}
for k,files in groups.items():
 diffs=[{'path':p,'expected':s,'actual':sha(p)}for p,s in files.items()if sha(p)!=s];rows[k]={'files':len(files),'differences':diffs};assert not diffs,(k,diffs)
requests=[]
for p in sorted((R/'evidence/field02/flight/runs').glob('s*/request.json')):
 q=json.loads(p.read_text())
 if q['mode']=='sitl':requests.append({'run':p.parent.name,'path':str(p.relative_to(R)),'sha256':sha(p.relative_to(R)),'at':q['at']})
assert len(requests)==10
extra={p:sha(p)for p in [inventoryPath,'evidence/field02/cockpitvideo04/final-verification01.json','evidence/field02/flight/source-pins.json','evidence/field02/repair01/flight-source-pins.json','evidence/field02/cockpitvideo04/generation02-flight-pins.json','pilot/field02/flight/flight01.mjs','pilot/field02/flight/flight02.mjs','pilot/field02/flight/runtime.py','pilot/cockpitvideo04/flight/flight03.mjs','pilot/cockpitvideo04/flight/runtime03.py']};assert all(extra.values());r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_READONLY_CLOCKVIDEO05_ADMISSION_BASELINE','groups':groups,'verification':rows,'extraPins':extra,'priorSITLRequests':requests,'totalPriorSITLRequests':10,'preexistingGitDeletedPaths':b['gitDeletedBefore'],'preexistingGitDeletedCount':len(b['gitDeletedBefore']),'noWholeRepositoryCompletenessClaim':True,'historicalBaselineSemantics':'DEREFERENCED_SHA_SEVEN_NEGATIVE_TEST_SYMLINKS_NOT_LITERAL_LINK_TARGET_IDENTITY','unknownClockCause':'CLOCK_CALIBRATION_UNKNOWN/SOURCE_CLOCK_RECOVERY_BOUND observed; background throttling remains hypothesis, not causally proven.','scope':'Read-only capture authenticates previous inventory431, original1486/native7/1496/source93 and10requesthashes; no runtime, control, build/sign or newfiles outside ownQA.'}
with(E/'qa-preservation-before01.json').open('x')as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({'status':r['status'],'groups':{k:v['files']for k,v in rows.items()},'diffs':0,'priorSITL':len(requests),'oldGitDeleted':len(b['gitDeletedBefore'])}))
