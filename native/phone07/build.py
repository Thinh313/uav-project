from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,datetime,sys
from assemble import R,N,stage,source,sha
E=R/'evidence/phone07/builder';W=N/'.build';D=N/'dist';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');B=SDK/'build-tools/36.0.0';A=SDK/'platforms/android-37.0/android.jar';attempt=sys.argv[1]
assert attempt in ['01','02'],'PHONE07 finite development build budget'
forecast=160*2**20;minimum=20*2**30+forecast+516*2**20;samples=[]
for index in range(31):
 free=shutil.disk_usage(R).free;samples.append({'hostMonoNs':str(__import__('time').monotonic_ns()),'freeBytes':free});assert free>=minimum,'PHONE07_STABLE_BUILD_HEADROOM'
 if index<30:__import__('time').sleep(1)
assert free>=20*2**30+forecast+516*2**20 and not W.exists(),'Actual resource admission/owned staging'
E.mkdir(exist_ok=True,parents=True);assert not(E/('build'+attempt+'.json')).exists();W.mkdir();D.mkdir(exist_ok=True);logs=[]
def run(a):
 assert shutil.disk_usage(R).free>=20*2**30+516*2**20,'PHONE07_BUILD_FLOOR';assert sum(p.stat().st_size for p in W.rglob('*')if p.is_file())<=160*2**20,'PHONE07_STAGING_BOUND'
 try:p=subprocess.run(list(map(str,a)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True,timeout=180)
 except subprocess.TimeoutExpired as e:
  logs.append({'command':list(map(str,a)),'exit':'TIMEOUT','output':(str(e.stdout or '')+str(e.stderr or ''))[-65536:]});raise
 logs.append({'command':list(map(str,a)),'exit':p.returncode,'output':(p.stdout+p.stderr)[-65536:]});assert p.returncode==0,logs[-1]['output'];return p.stdout+p.stderr
try:
 files=stage(W);sourceId=sha(json.dumps(files,sort_keys=True).encode());(E/('build-source-freeze'+attempt+'.json')).open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'sourceId':sourceId,'files':files,'admissionFreeBytes':free,'forecastBytes':forecast,'stableResourceSamples':samples},indent=2)+'\n')
 info=W/'src/BuildInfo90.java';info.write_text('package vn.rtr.aeris.phone07;public final class BuildInfo90{public static final String SOURCE_ID="'+sourceId+'";}');classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sorted((W/'src').glob('*.java'))]);assets=W/'pack/assets/cockpit';assets.parent.mkdir(parents=True);shutil.move(W/'assets',assets);run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',W/'pack/assets','-0','webm','-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*classes.rglob('*.class')]);
 with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
 unsigned=D/('aeris-phone07-unsigned'+attempt+'.apk');target=D/('aeris-phone07-development'+attempt+'.apk');assert not unsigned.exists()and not target.exists();run([B/'zipalign','-f','4',W/'unsigned.apk',unsigned]);K=R/'.local/native31';run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,unsigned]);sig=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in sig
 assert target.stat().st_size<=16*2**20,'PHONE07_APK_BOUND'
 with zipfile.ZipFile(unsigned)as a,zipfile.ZipFile(target)as b:assert all(a.read(n)==b.read(n)for n in a.namelist())
 report={'at':datetime.datetime.now().astimezone().isoformat(),'apk':str(target.relative_to(R)),'sha256':sha(target.read_bytes()),'bytes':target.stat().st_size,'sourceId':sourceId,'sourceFiles':files,'signature':sig,'permissions':run([B/'aapt2','dump','permissions',target]),'unsignedPayloadExact':True,'scope':'PHONE07_SIMULATION_DEVELOPMENT_ONLY_NOT_DEVICE_ACCEPTANCE','stableResourceSamples':samples};(E/('build'+attempt+'.json')).open('x').write(json.dumps(report,indent=2)+'\n');unsigned.unlink();print(json.dumps({k:report[k]for k in ['apk','sha256','sourceId','bytes']}))
finally:
 for extra in D.glob('aeris-phone07-unsigned'+attempt+'.apk'):extra.unlink()
 (E/('build-log'+attempt+'.json')).open('x').write(json.dumps(logs,indent=2)+'\n');shutil.rmtree(W)
