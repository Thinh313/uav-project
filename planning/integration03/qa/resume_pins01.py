from pathlib import Path
import hashlib,json,zipfile,subprocess,os
R=Path(__file__).resolve().parents[3];os.chdir(R)
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
b=json.load(open('evidence/integration03/build03.json'));native=json.load(open('evidence/integration03/source-ready05.json'));viewer=json.load(open('evidence/integration03/observer-source-ready04.json'));need(b['sourceFiles']==native['files'],'build source map');apk=R/b['apk'];need(sha(apk.read_bytes())==b['sha256']and apk.stat().st_size==b['bytes'],'APKhashsize');expected={}
for p,h in native['files'].items():
 need(sha(Path(p).read_bytes())==h,'source '+p)
 prefix='native/crew02/assets/'
 if p.startswith(prefix):expected[p[len(prefix):]]=Path(p).read_bytes()
for p,h in native['files'].items():
 prefix='native/integration03/assets/'
 if p.startswith(prefix):expected[p[len(prefix):]]=Path(p).read_bytes()
for p,h in viewer['files'].items():need(sha(Path(p).read_bytes())==h,'observer '+p)
with zipfile.ZipFile(apk)as z:
 names=z.namelist();need(len(names)==len(set(names)),'APKduplicate');actual={x[len('assets/cockpit/'):]for x in names if x.startswith('assets/cockpit/')};need(actual==set(expected),'exactAPKassetmembership')
 for p,v in expected.items():need(z.read('assets/cockpit/'+p)==v,'APK asset '+p)
env={**os.environ,'JAVA_HOME':'/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'};c=subprocess.run(['/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0/apksigner','verify','--verbose','--print-certs',str(apk)],capture_output=True,text=True,timeout=30,env=env);need(c.returncode==0,'apksigner:'+c.stderr[:500]);need('Signer #1 certificate SHA-256 digest: 3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in c.stdout,'development signer')
r={'status':'PASS_EXISTING_APK03_SOURCE_NATIVE_AND_OBSERVER_PINS_NO_RUNTIME_CLAIM','nativeSourceId':native['sourceId'],'observerSourceId':viewer['sourceId'],'nativePins':len(native['files']),'observerPins':len(viewer['files']),'apk':b['apk'],'apkSha256':b['sha256'],'apkBytes':b['bytes'],'exactAPKAssetCount':len(expected),'developmentSignature':'Independent apksigner v2/v3 verification PASS; sameengineeringonly certificate','certificateSha256':'3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800','inputs':{p:sha(Path(p).read_bytes())for p in ['evidence/integration03/build03.json','evidence/integration03/source-ready05.json','evidence/integration03/observer-source-ready04.json']},'scope':'Existing artifact closure, no build/install/runtime/flight; final runtime gates pending','priorSignatureInvocation':{'status':'NOT_EXECUTED_ENVIRONMENT','message':'Unable to locate a Java Runtime; explicit existingJDK JAVA_HOME then used, no install or APK modification.'}}
p=Path('evidence/integration03-qa/resume-pins01.json');need(not p.exists(),'immutableoutput');p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'path':str(p),'assets':len(expected)}))
