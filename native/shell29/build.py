"""Independent unsigned native29 build. Never signs or touches frozen build helpers."""
from pathlib import Path
import os,json,hashlib,subprocess,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/shell29';E=R/'evidence/native29';S=R/'native/shell24';sdk=Path('/opt/homebrew/share/android-commandlinetools');java=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');bt=sdk/'build-tools/36.0.0';jar=sdk/'platforms/android-37.0/android.jar';work=N/'.build';out=N/'dist'
if shutil.disk_usage(R).free<20*1024**3:raise SystemExit('Disk reserve below20GiB')
if work.exists():raise SystemExit('Prior scratch exists; inspect before build')
for p in [jar,java/'bin/javac',bt/'aapt2',bt/'d8',bt/'zipalign',S/'assets/synthetic.webm']:
 if not p.exists():raise SystemExit('Existing tool/input unavailable: '+str(p))
attempt=1
while (E/f'build-attempt{attempt:02}.txt').exists():attempt+=1
work.mkdir();out.mkdir(exist_ok=True)
if (E/'native-build.json').exists():
 old=json.loads((E/'native-build.json').read_text());old_apk=R/old['apk']
 if old_apk.exists() and hashlib.sha256(old_apk.read_bytes()).hexdigest()==old['apkSha256']:
  alias=out/(old['apkSha256']+'.apk')
  if not alias.exists():shutil.copyfile(old_apk,alias)
  receipt=E/f"native-build-attempt{old['attempt']:02}.json"
  if not receipt.exists():receipt.write_text(json.dumps(old,indent=2)+'\n')
logs=[];env={**os.environ,'JAVA_HOME':str(java)};h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,receipt=None,allow_failure=False):
 r=subprocess.run([str(a) for a in args],env=env,cwd=R,capture_output=True,text=True);text=r.stdout+r.stderr;logs.append(text)
 if receipt:(E/receipt).write_text(text)
 if r.returncode and not allow_failure:raise RuntimeError(text)
 return r,text
try:
 dependencies=[p for p in (S/'src').rglob('*.java') if p.name!='ShellActivity.java'];native=[p for p in (N/'src').rglob('*.java')];inputs=[N/'AndroidManifest.xml',*(N/'res').rglob('*'),*native,*dependencies,S/'assets/synthetic.webm',N/'walkthrough/catalog.json',N/'catalog.mjs']
 pins={str(p.relative_to(R)):h(p) for p in sorted(inputs) if p.is_file()};source_id=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest();fixture_sha=h(S/'assets/synthetic.webm')
 generated=work/'BuildInfo.java';generated.write_text('package vn.rtr.aeris.shell29;public final class BuildInfo{public static final String SOURCE_ID="'+source_id+'",FIXTURE_SHA="'+fixture_sha+'";}')
 host=work/'host';host.mkdir();core=[p for p in native if p.name!='ShellActivity.java'];run([java/'bin/javac','--release','8','-d',host,*dependencies,*core,*sorted((N/'tests').glob('*.java')),*sorted((S/'tests').glob('*.java'))]);_,test=run([java/'bin/java','-cp',host,'vn.rtr.aeris.shell29.WorkflowTest',work/'test-history'],f'model-tests-attempt{attempt:02}.txt');_,reg=run([java/'bin/java','-cp',host,'vn.rtr.aeris.shell24.ModelTest'],f'native24-regression-attempt{attempt:02}.txt');_,replay=run([java/'bin/java','-cp',host,'vn.rtr.aeris.shell29.Replay']);json.loads(replay);(E/f'host-replays-attempt{attempt:02}.json').write_text(replay);(N/'walkthrough/replays.json').write_text(replay)
 classes=work/'classes';classes.mkdir();run([java/'bin/javac','-source','8','-target','8','-bootclasspath',str(bt/'core-lambda-stubs.jar')+os.pathsep+str(jar),'-d',classes,*dependencies,*native,generated]);run([bt/'aapt2','compile','--dir',N/'res','-o',work/'resources.zip']);run([bt/'aapt2','link','-I',jar,'--manifest',N/'AndroidManifest.xml','-A',S/'assets','-0','webm','-o',work/'unsigned.apk',work/'resources.zip']);dex=work/'dex';dex.mkdir();run([bt/'d8','--min-api','26','--lib',jar,'--output',dex,*sorted(classes.rglob('*.class'))])
 with zipfile.ZipFile(work/'unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
 apk=out/'aeris-native29-unsigned.apk';run([bt/'zipalign','-f','4',work/'unsigned.apk',apk]);_,badging=run([bt/'aapt2','dump','badging',apk],'apk-badging.txt');_,permissions=run([bt/'aapt2','dump','permissions',apk],'apk-permissions.txt');assert 'uses-permission:' not in permissions
 r,signature=run([bt/'apksigner','verify','--verbose',apk],'unsigned-verification.txt',allow_failure=True);assert r.returncode!=0 and 'DOES NOT VERIFY' in signature
 with zipfile.ZipFile(apk) as z:
  assert {'classes.dex','AndroidManifest.xml','assets/synthetic.webm'}.issubset(z.namelist());assert z.getinfo('assets/synthetic.webm').compress_type==zipfile.ZIP_STORED;assert not any(n.startswith('META-INF/') and n.endswith(('.RSA','.DSA','.EC','.SF')) for n in z.namelist());assert hashlib.sha256(z.read('assets/synthetic.webm')).hexdigest()==fixture_sha
 report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'BUILT_UNSIGNED_NATIVE_STATIC_AND_HOST_VERIFIED','attempt':attempt,'sourceId':source_id,'sourceHashes':pins,'package':'vn.rtr.aeris.shell29','version':'0.2.0-native29-unsigned','minApi':26,'targetApi':33,'compilePlatform':37,'permissions':'NONE','signing':'NONE; unsigned APK, no key read/sign operation','apk':str(apk.relative_to(R)),'apkSha256':h(apk),'apkBytes':apk.stat().st_size,'hostTests':sum(x.startswith('PASS ') for x in test.splitlines()),'native24Regression':sum(x.startswith('PASS ') for x in reg.splitlines()),'nativeRuntime':'NOT_CHECKED','toolHashes':{str(p):h(p) for p in [jar,java/'bin/javac',bt/'aapt2',bt/'zipalign',bt/'lib/d8.jar']},'scope':'Unsigned Android compilation/packaging, pure Java mocks/history and captured core catalog only. No Android install/Hera/SDK/flight/release'}
 (E/'native-build.json').write_text(json.dumps(report,indent=2)+'\n');(N/'walkthrough/pins.mjs').write_text('export const PINS='+json.dumps({'sourceId':source_id,'replaysSha256':h(N/'walkthrough/replays.json'),'catalogSha256':h(N/'walkthrough/catalog.json'),'fixtureSha256':fixture_sha,'apkSha256':h(apk)},indent=2)+';\n');print(json.dumps({k:report[k] for k in ['status','hostTests','native24Regression','apkSha256','apkBytes','nativeRuntime']}))
finally:
 (E/f'build-attempt{attempt:02}.txt').write_text('\n'.join(logs));shutil.rmtree(work);(E/'cleanup-build.json').write_text(json.dumps({'removed':['native/shell29/.build'],'wholeProjectCopies':0,'dependencyInstalls':0,'keyReads':0,'signOperations':0},indent=2)+'\n')
