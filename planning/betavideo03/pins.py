"""One-time execution seal; reused APK/native encoder, no build or signing."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/betavideo03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
oldPath=R/'evidence/betastability02/source-pins07.json';old=json.loads(oldPath.read_text());files={}
for n,h in old['files'].items():
 p=R/n;assert p.is_file()and not p.is_symlink()and sha(p)==h,'PREDECESSOR_SOURCE_DRIFT:'+n;files[n]=h
for p in(R/'pilot/betavideo03').rglob('*'):
 if p.is_file():assert not p.is_symlink();files[str(p.relative_to(R))]=sha(p)
for n in ['planning/betavideo03/video-check.html','planning/betavideo03/video-check-client.mjs','planning/betavideo03/video-check.css','planning/betavideo03/video-only-qualification.mjs']:
 p=R/n;assert p.is_file(),n;files[n]=sha(p)
apk='native/betastability02/dist/aeris-betastability02-development01.apk';encoder='native/betastability02/host-source/aeris-native-source'
assert apk in files and encoder in files,'EXACT_REUSED_ARTIFACTS_REQUIRED';assert shutil.disk_usage(R).free>=20*2**30,'ENTRY20GIB'
result={'format':'betavideo03-execution-pins','version':1,'files':files,'predecessorPinFile':str(oldPath.relative_to(R)),'predecessorPinFileSha256':sha(oldPath),'legacyMissing':old.get('legacyMissing',[]),'reusedAPK':{'path':apk,'sha256':files[apk],'package':'vn.rtr.aeris.betastability02','wireFormat':'aeris-betastability02-diagnostic-package','newSignature':False},'reusedNativeEncoder':{'path':encoder,'sha256':files[encoder]},'scope':'COMPLETE_PREDECESSOR_EXECUTION_CLOSURE_PLUS_NEW_HOST_MEDIA_DIAGNOSTIC_ASSETS; NO_NEW_APK_OR_SOURCE_REWRITE','budgetAnchorUTC':'2026-10-26T03:26:06+00:00','maxAPRequests':10,'maxRetainedAPContainers':10,'maxHostStarts':8,'maxOwnEvidenceBytes':2*2**30,'maxEvidenceFiles':12000,'taskWallBudgetMinutes':180,'speedup':1,'pacingCapMs':500,'admissionGiB':20,'floorGiB':10,'floorReserveMiB':256,'admissionSamples':31,'admissionDeclineLimitMiB':256,'forecastSeconds':15}
with(E/'source-pins01.json').open('x')as f:json.dump(result,f,indent=2)
print('SEALED',len(files),'files; reused APK/native encoder; no build/signing')
