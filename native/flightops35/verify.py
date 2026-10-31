"""Read-only acceptance of existing receipts/binaries; never build, sign or launch."""
from pathlib import Path
import json,hashlib,subprocess,datetime,shutil,zipfile
R=Path(__file__).resolve().parents[2];E=R/'evidence/airspace35';N=R/'native/flightops35';checks=[];attempt=1
while (E/f'verification{attempt}.json').exists():attempt+=1
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,value):
    checks.append({'name':name,'pass':bool(value)})
def receipt(name):return json.loads((E/name).read_text())
core=receipt('logic9.json');native=receipt('native-logic1.json');browser=receipt('browser5.json');build=receipt('build03.json');crash=receipt('crash1.json');protect=receipt('preservation-after.json')
check('current core85 checks host PASS',core['status']=='HOST_PASS' and core['passed']==core['checks']==85)
check('core receipt hashes exact current sources',all((R/p).is_file() and h(R/p)==v for p,v in core['sourceHashes'].items()))
check('native115 regressions PASS',native['status']=='PASS' and 'ℹ tests 115' in native['testSummary'] and 'ℹ fail 0' in native['testSummary'])
check('native regression receipt matches current source',all((R/p).is_file() and h(R/p)==v for p,v in native['sourceHashes'].items()))
check('current browser29 gates PASS',browser['status']=='PASS' and len(browser['checks'])==29 and all(x['pass'] for x in browser['checks']) and not browser['errors'] and not browser['external'])
check('browser receipt matches current assets/server',all(h(N/p)==v for p,v in browser['sourceHashes'].items()))
check('real owned JVM SIGKILL19 gates PASS',crash['status']=='PASS' and len(crash['checks'])==19 and all(x['pass'] for x in crash['checks']))
check('current Java algorithm equals build03 source used by crash suite',all(h(R/p)==v for p,v in build['sources'].items() if p.endswith('.java')))
check('31Java journal checks build03 PASS',build['hostJournalChecks']==31)
check('protected8883 original hashes unchanged',protect['status']=='PASS' and protect['checkedPaths']==8883 and not protect['failures'])
check('native core clone exactly same engine',all(p.read_bytes()==(R/'pilot/airspace35/core'/p.name).read_bytes() for p in (N/'core').glob('*.mjs')))
reuse=json.loads((E/'reuse-pins.json').read_text());check('exact pinned N33 editor/journey/compiler reuse',all(h(N/p)==v and h(R/'native/journey33'/p)==v for p,v in reuse['files'].items()))
roadmap=json.loads((R/'delivery/ROADMAP-AIRSPACE35.json').read_text());check('47requirements staged exactly once; none operational accepted',len(roadmap['features'])==47 and {f['id'] for f in roadmap['features']}=={'F%02d'%i for i in range(1,48)} and all(not f['operationalAccepted'] for f in roadmap['features']))
apk=R/build['apk'];check('prior APK03 bytes match build03 receipt',h(apk)==build['sha256'])
B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');env={'JAVA_HOME':'/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'}
import os
commands=[('signature','apksigner',['verify','--verbose','--print-certs']),('permissions','aapt2',['dump','permissions']),('badging','aapt2',['dump','badging'])];observed={}
for name,cmd,args in commands:
    p=subprocess.run([str(B/cmd),*args,str(apk)],text=True,capture_output=True,env={**os.environ,**env});observed[name]=p.stdout+p.stderr;(E/f'final-{name}{attempt}.txt').write_text(observed[name]);(E/f'final-{name}.txt').write_text(observed[name]);check('read-only '+name+' command success',p.returncode==0)
check('APK03 v2/v3 verified existing dedicated dev identity',all(t in observed['signature'] for t in ['Verified using v2 scheme (APK Signature Scheme v2): true','Verified using v3 scheme (APK Signature Scheme v3): true','3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800']))
check('APK03 zero permissions and separate package/API26..33', 'uses-permission:' not in observed['permissions'] and "name='vn.rtr.aeris.flightops35'" in observed['badging'] and "minSdkVersion:'26'" in observed['badging'] and "targetSdkVersion:'33'" in observed['badging'])
asset_matches=[]
with zipfile.ZipFile(apk) as z:
    for p,v in build['sources'].items():
        q=R/p
        if q.suffix=='.mjs' or q.suffix in ['.html','.css','.ttf']:
            member='assets/editor/'+str(q.relative_to(N));asset_matches.append(hashlib.sha256(z.read(member)).hexdigest()==v)
    check('APK03 assets exact build03 source hashes',all(asset_matches));check('APK03 DEX exists','classes.dex' in z.namelist())
drift=[p for p,v in build['sources'].items() if h(R/p)!=v]
check('APK03 explicitly prior revision; current build admission refused',bool(drift) and receipt('build-admission04.json')['status']=='NOT_STARTED_STORAGE_HEADROOM')
cleanup=[f'native/flightops35/.qa-store-{i}' for i in range(1,6)]+['native/flightops35/.build','native/flightops35/.crash-qa-1','native/flightops35/.diagnosis-store']
check('all owned build/test scratch removed',all(not(R/p).exists() for p in cleanup))
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_CURRENT_HOST_VERIFIED_APK_ANDROID_SITL_PENDING' if all(c['pass'] for c in checks) else 'FAIL','checks':checks,'hostTestCount':85+115+31+19+29,'hostScope':'Engine/corpus/models/Java journal/Chromium only; same agent verifies own work','APK':{'path':build['apk'],'sha256':h(apk),'currentSource':False,'driftSinceBuild03':drift,'currentSourceBuild':'NOT_CHECKED_STORAGE_ADMISSION_REFUSED','releaseSignature':False},'gates':{'actualAndroid':'NOT_CHECKED','actualAPFenceSITL':'NOT_CHECKED','HeraInputVideoSDK':'NOT_CHECKED','legalAirspaceProvider':'NOT_CHECKED','runtimeAI':'NOT_IMPLEMENTED','24hEndurance':'FAILED_HOST_EXTERNAL_POWER_LOST_UNCHANGED'},'preservation':{'checkedPaths':8883,'failures':0,'continuousOriginalPathPresence':'NOT_CLAIMED'},'cleanupRemoved':cleanup,'wholeProjectCopies':0,'dependencyInstalls':0,'freeBytes':shutil.disk_usage(R).free,'operationalAccepted':False}
(E/f'verification{attempt}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(E/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({**report,'checks':len(checks)},ensure_ascii=False));raise SystemExit(0 if all(c['pass'] for c in checks) else 1)
