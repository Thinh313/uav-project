"""Own unsigned APK + pure Java draft tests; never read/sign keys or mutate old files."""
from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/shell30';E=R/'evidence/native30';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');S=Path('/opt/homebrew/share/android-commandlinetools');B=S/'build-tools/36.0.0';A=S/'platforms/android-37.0/android.jar';W=N/'.build';D=N/'dist';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if shutil.disk_usage(R).free<20*1024**3:raise SystemExit('Disk floor20GiB')
if W.exists():raise SystemExit('Prior scratch exists')
W.mkdir();D.mkdir(exist_ok=True);attempt=1
while (E/f'build{attempt:02d}.txt').exists():attempt+=1
if (E/'native-build.json').exists():
 old=json.loads((E/'native-build.json').read_text());oldapk=R/old['apk']
 if oldapk.exists() and h(oldapk)==old['apkSha256']:
  alias=D/(old['apkSha256']+'.apk')
  if not alias.exists():shutil.copyfile(oldapk,alias)
  receipt=E/f"native-build{old['attempt']:02d}.json"
  if not receipt.exists():receipt.write_text(json.dumps(old,indent=2)+'\n')
env={**os.environ,'JAVA_HOME':str(J)};logs=[]
def run(args,allow=False):
 r=subprocess.run([str(x) for x in args],cwd=R,env=env,text=True,capture_output=True);logs.append(r.stdout+r.stderr)
 if r.returncode and not allow:raise RuntimeError(logs[-1])
 return r
try:
 vendor=N/'vendor';vendor.mkdir(exist_ok=True);cores={}
 for name in ['survey','compiler']:
  source=R/f'app/core/{name}.mjs';target=vendor/f'{name}.mjs';target.write_bytes(source.read_bytes());cores[str(source.relative_to(R))]=h(source)
 source_id=hashlib.sha256(json.dumps(cores,sort_keys=True,separators=(',',':')).encode()).hexdigest();(N/'pins.mjs').write_text('export const PINS='+json.dumps({'coreSourceId':source_id,'coreSourceHashes':cores},indent=2)+';\n')
 host=W/'host';host.mkdir();pure=[p for p in (N/'src').rglob('*.java') if p.name not in ['ShellActivity.java','AndroidProbe.java']];tests=list((N/'tests').rglob('*.java'));run([J/'bin/javac','--release','8','-d',host,*pure,*tests]);test=run([J/'bin/java','-cp',host,'vn.rtr.aeris.shell30.DraftStoreTest',W/'tests']);(E/f'host-tests{attempt:02d}.txt').write_text(test.stdout+test.stderr)
 hostjar=D/'journal-host.jar';run([J/'bin/jar','cf',hostjar,'-C',host,'.'])
 assets=W/'assets/editor';assets.mkdir(parents=True);paths=[N/'index.html',N/'shell.css',N/'shell.mjs',N/'editor.mjs',N/'pins.mjs',*vendor.glob('*.mjs')]
 for p in paths:
  dst=assets/p.relative_to(N);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
 classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*list((N/'src').rglob('*.java')),*tests]);run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',W/'assets','-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*classes.rglob('*.class')])
 with zipfile.ZipFile(W/'unsigned.apk','a') as z:z.write(dex/'classes.dex','classes.dex')
 apk=D/'aeris-native30-unsigned.apk';run([B/'zipalign','-f','4',W/'unsigned.apk',apk]);p=run([B/'aapt2','dump','permissions',apk]);(E/'apk-permissions.txt').write_text(p.stdout);assert 'uses-permission:' not in p.stdout
 signature=run([B/'apksigner','verify','--verbose',apk],True);(E/'unsigned-verification.txt').write_text(signature.stdout+signature.stderr);assert signature.returncode!=0 and 'DOES NOT VERIFY' in signature.stdout+signature.stderr
 sources=[*list((N/'src').rglob('*.java')),*tests,*paths,N/'AndroidManifest.xml',N/'build.py'];report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'BUILT_UNSIGNED_HOST_PASS_ANDROID_UI_NOT_CHECKED','attempt':attempt,'coreSourceId':source_id,'coreHashes':cores,'sourceHashes':{str(p.relative_to(R)):h(p) for p in sources},'hostTests':sum(x.startswith('PASS ') for x in test.stdout.splitlines()),'apk':str(apk.relative_to(R)),'apkSha256':h(apk),'apkBytes':apk.stat().st_size,'hostJarSha256':h(hostjar),'signing':'NONE','keyReads':0,'nativeUI':'NOT_CHECKED','scope':'Shared compiler/editor assets and Java storage; no network/vehicle/SDK permissions'};(E/'native-build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report|{'sourceHashes':'see receipt'}))
finally:
 (E/f'build{attempt:02d}.txt').write_text('\n'.join(logs));shutil.rmtree(W);(E/'build-cleanup.json').write_text(json.dumps({'removed':['native/shell30/.build'],'signOperations':0,'keyReads':0,'wholeProjectCopies':0},indent=2)+'\n')
