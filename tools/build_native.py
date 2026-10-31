"""Build a native diagnostic APK using existing SDK/JDK. No network/install/Gradle cache."""
from pathlib import Path
import os,json,hashlib,subprocess,shutil,zipfile,datetime,re
R=Path(__file__).resolve().parents[1];N=R/'native/diagnostic';E=R/'evidence/hera03';E.mkdir(parents=True,exist_ok=True)
sdk=Path(os.environ.get('AERIS_ANDROID_SDK','/opt/homebrew/share/android-commandlinetools'));java=Path(os.environ.get('AERIS_JAVA_HOME','/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'));bt=sdk/'build-tools/36.0.0';jar=sdk/'platforms/android-37.0/android.jar';work=N/'.build';out=N/'dist';out.mkdir(exist_ok=True)
if shutil.disk_usage(R).free<20*1024**3:raise SystemExit('Disk free <20GiB; refusing build')
if work.exists():raise SystemExit('Existing native .build scratch; inspect before retry')
for p in [jar,java/'bin/javac',bt/'aapt2',bt/'d8',bt/'apksigner',bt/'zipalign']:
 if not p.exists():raise SystemExit(f'Existing tool unavailable: {p}')
work.mkdir();env={**os.environ,'JAVA_HOME':str(java)};logs=[]
def run(args):
 result=subprocess.run([str(x) for x in args],env=env,cwd=R,text=True,capture_output=True);logs.append(' '.join(str(x) for x in args)+'\n'+result.stdout+result.stderr)
 if result.returncode:raise RuntimeError(result.stderr or result.stdout)
 return result.stdout+result.stderr
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
try:
 sources=[N/'AndroidManifest.xml',*(N/'src').rglob('*.java'),*(N/'res').rglob('*')];source_hashes={str(p.relative_to(R)):hashfile(p) for p in sorted(sources) if p.is_file()};source_id=hashlib.sha256(json.dumps(source_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 generated=work/'BuildInfo.java';generated.write_text('package vn.rtr.aeris.diagnostic; public final class BuildInfo { public static final String SOURCE_ID="'+source_id+'"; }\n')
 classes=work/'classes';classes.mkdir();run([java/'bin/javac','-source','8','-target','8','-bootclasspath',str(bt/'core-lambda-stubs.jar')+os.pathsep+str(jar),'-d',classes,*sorted((N/'src').rglob('*.java')),generated])
 host=work/'host';host.mkdir();run([java/'bin/javac','--release','8','-d',host,N/'src/vn/rtr/aeris/diagnostic/CaptureSession.java',*sorted((N/'tests').glob('*.java'))]);host_result=run([java/'bin/java','-cp',host,'vn.rtr.aeris.diagnostic.CaptureSessionTest']);fixture=run([java/'bin/java','-cp',host,'vn.rtr.aeris.diagnostic.CaptureSessionFixture',source_id]);(E/'native-model-replay.json').write_text(fixture)
 run([bt/'aapt2','compile','--dir',N/'res','-o',work/'resources.zip']);run([bt/'aapt2','link','-I',jar,'--manifest',N/'AndroidManifest.xml','-o',work/'unsigned.apk',work/'resources.zip'])
 dex=work/'dex';dex.mkdir();run([bt/'d8','--min-api','26','--lib',jar,'--output',dex,*sorted(classes.rglob('*.class'))])
 with zipfile.ZipFile(work/'unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
 run([bt/'zipalign','-f','4',work/'unsigned.apk',work/'aligned.apk'])
 key=R/'.local/native-signing/diagnostic.p12';key.parent.mkdir(parents=True,exist_ok=True)
 if not key.exists():run([java/'bin/keytool','-genkeypair','-keystore',key,'-storetype','PKCS12','-storepass','android','-keypass','android','-alias','aeris-diagnostic-dev','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=AERIS LOCAL DIAGNOSTIC DEVELOPMENT, O=RtR, C=VN'])
 key.chmod(0o600);apk=out/'aeris-diagnostic-dev.apk';run([bt/'apksigner','sign','--ks',key,'--ks-key-alias','aeris-diagnostic-dev','--ks-pass','pass:android','--key-pass','pass:android','--out',apk,work/'aligned.apk']);signature=run([bt/'apksigner','verify','--verbose','--print-certs',apk]);badging=run([bt/'aapt2','dump','badging',apk]);permissions=run([bt/'aapt2','dump','permissions',apk]);assert 'uses-permission:' not in permissions
 with zipfile.ZipFile(apk) as z:assert 'classes.dex' in z.namelist() and 'AndroidManifest.xml' in z.namelist()
 toolfiles=[jar,bt/'core-lambda-stubs.jar',java/'bin/java',java/'bin/javac',bt/'aapt2',bt/'lib/d8.jar',bt/'lib/apksigner.jar',java/'release'];tools={str(p):hashfile(p) for p in toolfiles};report={'status':'BUILT_AND_STATICALLY_VERIFIED','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package':'vn.rtr.aeris.diagnostic','version':'0.6.0','minSdk':26,'targetSdk':33,'compilePlatform':'android-37.0 (existing host SDK)','sourceId':source_id,'source_files':source_hashes,'tool_hashes':tools,'apk':str(apk.relative_to(R)),'apk_sha256':hashfile(apk),'apk_bytes':apk.stat().st_size,'signing':'Local development certificate, not production release','host_tests':host_result.strip(),'permissions':'none','native_runtime':'NOT_CHECKED','scope':'Compilation/dex/packaging/signature + pure host report model; not installation or Android execution'}
 (E/'native-build.json').write_text(json.dumps(report,indent=2)+'\n');(E/'apk-signature.txt').write_text(signature);(E/'apk-badging.txt').write_text(badging);(E/'apk-permissions.txt').write_text(permissions)
 pins={'buildId':source_id,'package':report['package'],'version':'0.6.0','apkSha256':report['apk_sha256']};(R/'app/core/native-pins.mjs').write_text('export const NATIVE_PINS='+json.dumps(pins,indent=2)+';\n');sw=R/'app/offline-sw.mjs';sw.write_text(re.sub(r"const CACHE='[^']+'", "const CACHE='aeris-survey02-static-v0.6.0-"+report['apk_sha256'][:12]+"'",sw.read_text(),count=1));print(json.dumps({k:report[k] for k in ['status','apk','apk_bytes','apk_sha256','sourceId','host_tests','native_runtime']}))
finally:
 (E/'native-build-log.txt').write_text('\n'.join(logs));shutil.rmtree(work)
