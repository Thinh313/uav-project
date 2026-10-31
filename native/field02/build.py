from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,datetime,sys,time
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent;E=R/'evidence/field02';W=N/'.build';D=N/'dist';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');B=SDK/'build-tools/36.0.0';A=SDK/'platforms/android-37.0/android.jar';attempt=sys.argv[1]
assert attempt in ['01','02'],'FIELD02_FINITE_BUILD_BUDGET';assert not(E/('android-build'+attempt+'.json')).exists() and not(E/('android-build-log'+attempt+'.json')).exists(),'ATTEMPT_ALREADY_CONSUMED'
forecast=32*2**20;reserve=512*2**20;samples=[]
for i in range(31):
 free=shutil.disk_usage(R).free;samples.append({'monoNs':str(time.monotonic_ns()),'freeBytes':free});assert free>=20*2**30+forecast+reserve,'FIELD02_BUILD_DISK_HEADROOM'
 if i<30:time.sleep(1)
assert not W.exists(),'OWN_STAGE_MUST_BE_ABSENT';W.mkdir();D.mkdir(exist_ok=True);E.mkdir(exist_ok=True,parents=True);logs=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
files={str(p.relative_to(R)):sha(p.read_bytes()) for p in sorted(N.rglob('*')) if p.is_file() and not any(x in ['.build','dist','__pycache__'] for x in p.relative_to(N).parts)}
sourceId=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode());(E/('android-source-freeze'+attempt+'.json')).open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'files':files,'sourceId':sourceId,'resourceSamples':samples},indent=2)+'\n')
def run(a):
 assert shutil.disk_usage(R).free>=20*2**30+reserve,'FIELD02_BUILD_FLOOR';assert sum(p.stat().st_size for p in W.rglob('*') if p.is_file())<=forecast,'FIELD02_STAGE_BOUND'
 try:p=subprocess.run(list(map(str,a)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True,timeout=180)
 except subprocess.TimeoutExpired as e:logs.append({'command':list(map(str,a)),'exit':'TIMEOUT','output':str(e)[-2048:]});raise
 logs.append({'command':list(map(str,a)),'exit':p.returncode,'output':(p.stdout+p.stderr)[-32768:]});assert p.returncode==0,logs[-1]['output'];return p.stdout+p.stderr
try:
 s=W/'src';s.mkdir();classes=W/'classes';classes.mkdir()
 for p in (N/'src').glob('*.java'):shutil.copyfile(p,s/p.name)
 (s/'BuildInfo02.java').write_text('package vn.rtr.aeris.field02; public final class BuildInfo02{public static final String SOURCE_ID="'+sourceId+'";}')
 run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sorted(s.glob('*.java'))])
 run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
 with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
 unsigned=W/'aligned.apk';target=D/('aeris-field02-development'+attempt+'.apk');assert not target.exists();run([B/'zipalign','-f','4',W/'unsigned.apk',unsigned]);K=R/'.local/native31';run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,unsigned]);sig=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in sig
 assert target.stat().st_size<=16*2**20,'FIELD02_APK_BOUND'
 with zipfile.ZipFile(unsigned)as a,zipfile.ZipFile(target)as b:assert all(a.read(n)==b.read(n)for n in a.namelist())
 report={'at':datetime.datetime.now().astimezone().isoformat(),'apk':str(target.relative_to(R)),'sha256':sha(target.read_bytes()),'bytes':target.stat().st_size,'sourceId':sourceId,'signature':sig,'permissions':run([B/'aapt2','dump','permissions',target]),'unsignedPayloadExact':True,'scope':'FIELD02_DEVELOPMENT_ANDROID_HOST_COMPANION_NOT_HARDWARE_OR_PRODUCTION','freeBytes':shutil.disk_usage(R).free};(E/('android-build'+attempt+'.json')).open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:
 (E/('android-build-log'+attempt+'.json')).open('x').write(json.dumps(logs,indent=2)+'\n');shutil.rmtree(W)
