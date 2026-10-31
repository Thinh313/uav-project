"""Independent NATIVE24 build. No legacy helper, frozen source edits, installs or release signing."""
from pathlib import Path
import os,json,hashlib,subprocess,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/shell24';E=R/'evidence/native24';E.mkdir(exist_ok=True)
sdk=Path('/opt/homebrew/share/android-commandlinetools');java=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');bt=sdk/'build-tools/36.0.0';jar=sdk/'platforms/android-37.0/android.jar';work=N/'.build';out=N/'dist';out.mkdir(exist_ok=True);key=R/'.local/native-signing/diagnostic.p12'
if shutil.disk_usage(R).free<20*1024**3:raise SystemExit('Disk below20GiB; refusing build')
if work.exists():raise SystemExit('Unexpected build scratch, inspect before retry')
for p in [jar,java/'bin/javac',bt/'aapt2',bt/'d8',bt/'apksigner',bt/'zipalign',key,N/'assets/synthetic.webm']:
 if not p.exists():raise SystemExit('Existing input unavailable: '+str(p))
attempt=1
while (E/f'build-attempt{attempt:02}.txt').exists():attempt+=1
work.mkdir();logs=[];env={**os.environ,'JAVA_HOME':str(java)};h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 res=subprocess.run([str(a) for a in args],env=env,cwd=R,capture_output=True,text=True);logs.append(res.stdout+res.stderr)
 if res.returncode:raise RuntimeError(res.stdout+res.stderr)
 return res.stdout+res.stderr
try:
 sources=[N/'AndroidManifest.xml',*(N/'src').rglob('*.java'),*(N/'res').rglob('*'),*(N/'assets').rglob('*')];pins={str(p.relative_to(R)):h(p) for p in sorted(sources) if p.is_file()};source_id=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 generated=work/'BuildInfo.java';generated.write_text('package vn.rtr.aeris.shell24; public final class BuildInfo {public static final String SOURCE_ID="'+source_id+'";}')
 host=work/'host';host.mkdir();core=[p for p in (N/'src').rglob('*.java') if p.name!='ShellActivity.java']
 run([java/'bin/javac','--release','8','-d',host,*core,*sorted((N/'tests').glob('*.java'))]);test=run([java/'bin/java','-cp',host,'vn.rtr.aeris.shell24.ModelTest']);(E/f'model-tests-attempt{attempt:02}.txt').write_text(test)
 replay=run([java/'bin/java','-cp',host,'vn.rtr.aeris.shell24.Replay']);(E/'host-replays.json').write_text(replay);(N/'walkthrough/replays.json').write_text(replay)
 classes=work/'classes';classes.mkdir();run([java/'bin/javac','-source','8','-target','8','-bootclasspath',str(bt/'core-lambda-stubs.jar')+os.pathsep+str(jar),'-d',classes,*sorted((N/'src').rglob('*.java')),generated])
 run([bt/'aapt2','compile','--dir',N/'res','-o',work/'resources.zip']);run([bt/'aapt2','link','-I',jar,'--manifest',N/'AndroidManifest.xml','-A',N/'assets','-o',work/'unsigned.apk',work/'resources.zip']);dex=work/'dex';dex.mkdir();run([bt/'d8','--min-api','26','--lib',jar,'--output',dex,*sorted(classes.rglob('*.class'))])
 with zipfile.ZipFile(work/'unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
 run([bt/'zipalign','-f','4',work/'unsigned.apk',work/'aligned.apk']);apk=out/'aeris-native24-preparation-dev.apk';run([bt/'apksigner','sign','--ks',key,'--ks-key-alias','aeris-diagnostic-dev','--ks-pass','pass:android','--key-pass','pass:android','--out',apk,work/'aligned.apk']);signature=run([bt/'apksigner','verify','--verbose','--print-certs',apk]);badging=run([bt/'aapt2','dump','badging',apk]);permissions=run([bt/'aapt2','dump','permissions',apk]);assert 'uses-permission:' not in permissions
 with zipfile.ZipFile(apk) as z:assert {'classes.dex','AndroidManifest.xml','assets/synthetic.webm'}.issubset(set(z.namelist()))
 report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'BUILT_STATICALLY_VERIFIED_HOST_MODELS_PASS','attempt':attempt,'sourceId':source_id,'sourceHashes':pins,'package':'vn.rtr.aeris.shell24','version':'0.1.0-native24','minApi':26,'targetApi':33,'compilePlatform':37,'permissions':'NONE','signing':'Existing local diagnostic development certificate; not official/software-release signature','apk':str(apk.relative_to(R)),'apkSha256':h(apk),'apkBytes':apk.stat().st_size,'hostTestCount':len([l for l in test.splitlines() if l.startswith('PASS ')]),'nativeRuntime':'NOT_CHECKED','emulator':'NOT_AVAILABLE_IN_INITIAL_TOOL_INVENTORY','toolHashes':{str(p):h(p) for p in [jar,java/'bin/javac',bt/'aapt2',bt/'lib/d8.jar',bt/'lib/apksigner.jar']},'scope':'Compilation, packaging/signature and host pure-Java fault models only; no installed GCS or native decode measurement'}
 (E/'native-build.json').write_text(json.dumps(report,indent=2)+'\n');(E/'apk-signature.txt').write_text(signature);(E/'apk-badging.txt').write_text(badging);(E/'apk-permissions.txt').write_text(permissions)
 (N/'walkthrough/pins.mjs').write_text('export const PINS='+json.dumps({'sourceId':source_id,'replaysSha256':h(N/'walkthrough/replays.json'),'fixtureSha256':h(N/'assets/synthetic.webm'),'apkSha256':h(apk)},indent=2)+';\n');print(json.dumps({k:report[k] for k in ['status','apkSha256','apkBytes','hostTestCount','nativeRuntime']}))
finally:
 (E/f'build-attempt{attempt:02}.txt').write_text('\n'.join(logs));shutil.rmtree(work);(E/'cleanup.json').write_text(json.dumps({'removed':['native/shell24/.build'],'projectCopies':0,'dependencyInstalls':0,'note':'APK, idsig, original fixture and receipts intentionally retained'},indent=2)+'\n')
