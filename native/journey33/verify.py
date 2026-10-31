"""Read-only artifact/preservation verification; writes new NATIVE33 receipts only."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,shutil,datetime,os
R=Path(__file__).resolve().parents[2];N=R/'native/journey33';E=R/'evidence/native33';B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value,detail=None): checks.append({'name':name,'pass':bool(value),'detail':detail})
build=json.loads((E/'build02.json').read_text());apk=R/build['apk']
check('chosen development APK exact',h(apk)==build['sha256'],{'path':build['apk'],'sha256':h(apk),'bytes':apk.stat().st_size})
for rel,digest in build['sources'].items():check('packaged source unchanged '+rel,h(R/rel)==digest)
with zipfile.ZipFile(apk) as z:
    check('APK ZIP structure and DEX',z.testzip() is None and 'classes.dex' in z.namelist())
    for rel in ['index.html','shell.css','shell.mjs','journey.mjs','editor.mjs','pins.mjs','vendor/survey.mjs','vendor/compiler.mjs']:
        check('APK asset exact '+rel,z.read('assets/editor/'+rel)==(N/rel).read_bytes())
signature=subprocess.run([str(B/'apksigner'),'verify','--verbose','--print-certs',str(apk)],capture_output=True,text=True,env={**os.environ,'JAVA_HOME':'/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'})
check('existing development signature v2/v3',signature.returncode==0 and 'Verified using v2 scheme (APK Signature Scheme v2): true' in signature.stdout and 'Verified using v3 scheme (APK Signature Scheme v3): true' in signature.stdout and '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800' in signature.stdout)
permissions=subprocess.run([str(B/'aapt2'),'dump','permissions',str(apk)],capture_output=True,text=True)
check('zero Android permissions',permissions.returncode==0 and 'uses-permission:' not in permissions.stdout)
badging=subprocess.run([str(B/'aapt2'),'dump','badging',str(apk)],capture_output=True,text=True)
check('isolated debuggable package API26/33',badging.returncode==0 and "name='vn.rtr.aeris.journey33'" in badging.stdout and "minSdkVersion:'26'" in badging.stdout and "targetSdkVersion:'33'" in badging.stdout and 'application-debuggable' in badging.stdout)
ui=json.loads((E/'browser5.json').read_text())
check('final host UI30 checks/zero errors',ui['status']=='PASS' and len(ui['checks'])==30 and not ui['errors'] and not ui['external'])
check('final UI source fingerprints exact',all(h(N/p)==d for p,d in ui['sourceHashes'].items()))
logic=json.loads((E/'logic02.json').read_text());crash=json.loads((E/'crash1.json').read_text())
check('final editor and workspace85 host checks',logic['status']=='PASS' and logic['summary']=={'tests':85,'pass':85,'fail':0,'cancelled':0,'skipped':0})
check('actual host SIGKILL19 checks',crash['status']=='PASS' and len(crash['checks'])==19)
check('Java journal31 checks',build['hostJournalChecks']==31)
for rel in ['editor.mjs','pins.mjs','vendor/survey.mjs','vendor/compiler.mjs']:
    check('inherited exact pinned module '+rel,(N/rel).read_bytes()==(R/'native/shell30'/rel).read_bytes())
before=json.loads((E/'preservation-before.json').read_text());fail=[]
for rel,digest in before['files'].items():
    p=R/rel
    if not p.is_file() or h(p)!=digest:fail.append(rel)
preservation={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if not fail else 'FAIL','uniquePathsChecked':len(before['files']),'failures':fail,'scope':'Before/after exact bytes; no claim of uninterrupted historical path presence'}
(E/'preservation-after.json').write_text(json.dumps(preservation,indent=2)+'\n')
check('all prior protected paths exact',not fail,{'paths':len(before['files']),'failures':fail})
scratch=[str(p.relative_to(R)) for p in N.iterdir() if p.name.startswith(('.build','.qa-store','.crash-qa','.runtime'))]
check('owned build/test/runtime scratch removed',not scratch,scratch)
free=shutil.disk_usage(R).free;check('current disk floor20GiB',free>=20*1024**3,free)
android=json.loads((E/'android-admission-final.json').read_text())
check('unadmitted emulator not launched/downloaded',android['emulatorLaunches']==0 and android['SDKDownloads']==0 and android['forceStopAndReboot']=='NOT_CHECKED')
for rel in ['browser2.json','browser3.json','restart-race-incident.json']:
    check('historical failure receipt retained '+rel,(E/rel).is_file())
source={str(p.relative_to(R)):h(p) for p in N.rglob('*') if p.is_file()}
(E/'source-final-fingerprints.json').write_text(json.dumps({'files':source,'scope':'Separate engineering module and development artifacts'},indent=2)+'\n')
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_HOST_VERIFIED_ANDROID_NOT_CHECKED' if all(c['pass'] for c in checks) else 'FAIL','checks':checks,'hostScenarioChecks':{'logic':85,'javaJournal':31,'actualJVMSIGKILL':19,'browserUI':30},'implementedRequirements':7,'totalRequirements':8,'implementationCoveragePercent':87.5,'requirementCoverageScope':'7 implemented software/preservation scopes; actual Android acceptance R33-07 not performed. Not product maturity or full acceptance percentage. R33-01/02/03/05 native aspects remain NOT_CHECKED.','APK':build['apk'],'APKsha256':build['sha256'],'protectedPaths':len(before['files']),'currentFreeBytes':free,'AndroidART':'NOT_CHECKED','AndroidInstalledUI':'NOT_CHECKED','AndroidPrivatePersistence':'NOT_CHECKED','AndroidForceStopReboot':'NOT_CHECKED','physicalSDKInputVideo':'NOT_CHECKED','emulatorLaunches':0,'SDKDownloads':0,'softwareReleaseSignatures':0,'ENDUREMutations':0,'review':'Single-agent sequential verification, not independent audit'}
attempt=1
while (E/f'verification{attempt:02d}.json').exists():attempt+=1
(E/f'verification{attempt:02d}.json').write_text(json.dumps(report,indent=2)+'\n')
(E/'verification.json').write_text(json.dumps(report|{'receipt':f'verification{attempt:02d}.json'},indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','hostScenarioChecks','protectedPaths','currentFreeBytes','APK']}))
if any(not c['pass'] for c in checks): print(json.dumps([c for c in checks if not c['pass']]));raise SystemExit(1)
