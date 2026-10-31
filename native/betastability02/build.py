from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,time
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent;E=R/'evidence/betastability02';W=N/'.build';D=N/'dist';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');B=SDK/'build-tools/36.0.0';A=SDK/'platforms/android-37.0/android.jar'
assert not W.exists() and not(E/'android-build01.json').exists()
assert shutil.disk_usage(R).free>=20*2**30
W.mkdir();D.mkdir(exist_ok=True);logs=[]
def run(a):
 assert shutil.disk_usage(R).free>=10*2**30+256*2**20
 p=subprocess.run(list(map(str,a)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True,timeout=120)
 logs.append({'command':list(map(str,a)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr
 return p.stdout+p.stderr
try:
 classes=W/'classes';classes.mkdir();sources=sorted((N/'src').rglob('*.java'))+[N/'OperationGate.java']
 run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*sources])
 run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*sorted(classes.rglob('*.class'))])
 with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
 run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk']);K=R/'.local/native31';target=D/'aeris-betastability02-development01.apk';run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',target,W/'aligned.apk']);sig=run([B/'apksigner','verify','--verbose','--print-certs',target]);assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in sig
 (E/'android-build01.json').write_text(json.dumps({'status':'PASS_DEVELOPMENT_NOT_PRODUCTION','apk':str(target.relative_to(R)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'signature':sig,'sourceFiles':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},'originPredicatePort':8896,'freeBytes':shutil.disk_usage(R).free},indent=2)+'\n');print('DEVELOPMENT_APK_SIGNATURE_VERIFIED')
finally:
 (E/'android-build-log01.json').write_text(json.dumps(logs,indent=2)+'\n');shutil.rmtree(W)
