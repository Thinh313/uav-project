"""Final separate development handoff; preserve original failure and all old bytes."""
from pathlib import Path
import hashlib,json,zipfile,shutil,datetime,subprocess,os,ast
R=Path(__file__).resolve().parents[2];M=R/'native/runtime31';E=R/'evidence/native31';N=R/'native/shell30';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text());checks=[]
def check(n,v,detail=None):checks.append({'name':n,'pass':bool(v),'detail':detail})
baseline=load(E/'preservation-before.json');bad=[p for p,s in baseline['files'].items()if not(R/p).is_file()or h(R/p)!=s]
check('3547 prior/frozen files exact',len(baseline['files'])==3547 and not bad,bad)
(E/'preservation-after.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(baseline['files']),'mismatches':bad},indent=2)+'\n')
b=load(E/'build02.json');apk=M/'dist/aeris-native30-development.apk';check('handoff APK exact signed build',h(apk)==b['sha256']and apk.read_bytes()==(R/b['apk']).read_bytes()and b['signaturePayloadExact'])
check('dedicated public certificate exact',h(M/'dist/development-certificate.der')==b['certificateSha256'])
sig=(E/'final-signature.txt').read_text();check('v2/v3 verified dedicated development identity',sig.startswith('Verifies')and 'v2): true'in sig and 'v3): true'in sig and b['certificateSha256']in sig and 'Engineering Emulator Only'in sig)
manifest=(E/'final-manifest.txt').read_text();check('development only manifest/zero permissions','debuggable(0x0101000f)=true'in manifest and 'allowBackup(0x01010280)=false'in manifest and 'targetSdkVersion(0x01010270)=33'in manifest and 'uses-permission'not in manifest)
for s in b['sourceOverlays']:check(s['source']+' original preserved',h(R/s['source'])==s['sourceSha256'])
with zipfile.ZipFile(apk)as z:
 check('DEX present','classes.dex'in z.namelist())
 for p,v in b['assets'].items():check('packaged asset '+p,hashlib.sha256(z.read('assets/editor/'+p)).hexdigest()==v['packagedSha256']and h(N/p)==v['originalSha256'])
check('31 fixed journal checks on host',sum(s.startswith('PASS ')for s in(E/'journal-host-retest.txt').read_text().splitlines())==31 and 'TOTAL 31 PASS'in(E/'journal-host-retest.txt').read_text())
test=(E/'editor-regression.txt').read_text();check('46 editor regression,0 failed/skipped','ℹ tests 46'in test and 'ℹ pass 46'in test and 'ℹ fail 0'in test and 'ℹ skipped 0'in test)
check('ART fix compiled source remains File usable space','root.toFile().getUsableSpace()'in(N/'src/vn/rtr/aeris/shell30/DraftStore.java').read_text())
check('old ART failure remains FAIL',load(R/'evidence/native30/runtime-qa.json')['status']=='FAIL')
incident=load(E/'resource-attempt01.json');check('resource failure truth preserved',incident['status']=='STOPPED_EXTRACTION_DISK_FLOOR_INCIDENT'and incident['observedFreeBytes']<20*1024**3 and incident['emulator']=='NOT_STARTED')
check('owned scratch removed',all(not(M/p).exists()for p in ['.runtime','.build','.host-tests']))
free=shutil.disk_usage(R).free;check('current free above20GiB',free>=20*1024**3,free)
check('development private permissions600; not packaged',all((R/'.local/native31'/p).stat().st_mode&0o777==0o600 for p in ['password','development.p12']))
for p in M.glob('*.py'):ast.parse(p.read_text())
ok=all(c['pass']for c in checks)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_DEVELOPMENT_SIGNED_HOST_VERIFIED_ANDROID_NOT_RUN'if ok else'NOT_READY','handoffChecksPass':ok,'checks':checks,'hostTests':{'journal':31,'editor':46,'total':77},'protectedFiles':len(baseline['files']),'apk':str(apk.relative_to(R)),'apkSha256':h(apk),'certificateSha256':b['certificateSha256'],'currentFreeBytes':free,'resourceFloorThroughout':'FAIL_EXTRACTION_INCIDENT_RETAINED','userDecision':'Retain current capacity; hand off APK and completed checks','androidRuntime':{'ARTFixRetest':'NOT_CHECKED','installedN30UI':'NOT_CHECKED','applicationPrivatePersistence':'NOT_CHECKED','SIGKILLAndReboot':'NOT_CHECKED','SAFAndKeyboard':'NOT_CHECKED','HeraSDKInputVideo':'NOT_CHECKED'},'emulatorLaunches':0,'softwareReleaseSignatures':0,'ENDUREMutations':0,'review':'Single-agent sequential verification; not independent audit'}
(E/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
module=[p for p in M.rglob('*')if p.is_file()]+[R/'delivery/TIP-NATIVE31.md',R/'delivery/COMPLETION-NATIVE31.md',R/'docs/ADR-040-ISOLATED-DEVELOPMENT-ANDROID-RETEST.md']
(E/'module-fingerprints.json').write_text(json.dumps({'files':{str(p.relative_to(R)):h(p)for p in sorted(module)}},indent=2)+'\n')
(E/'evidence-fingerprints.json').write_text(json.dumps({'files':{str(p.relative_to(R)):h(p)for p in sorted(E.rglob('*'))if p.is_file()and p.name!='evidence-fingerprints.json'}},indent=2)+'\n')
print(report['status'],len(checks),'handoff checks',sum(not c['pass']for c in checks),'failures','freeGiB',free/1024**3)
if not ok:print(json.dumps([c for c in checks if not c['pass']],indent=2));raise SystemExit(1)
