"""Isolated N44 derivative signed with existing dedicated development identity."""
from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/runtime79';OLD=R/'native/preflight44';E=R/'evidence/native79';W=N/'.build';D=N/'dist';K=R/'.local/native31';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');B=SDK/'build-tools/36.0.0';A=SDK/'platforms/android-37.0/android.jar'
assert shutil.disk_usage(R).free>20.25*2**30 and not W.exists();assert (K/'development.p12').is_file() and (K/'password').is_file(),'EXISTING_DEVELOPMENT_IDENTITY_REQUIRED'
W.mkdir();D.mkdir(exist_ok=True);logs=[];source=N/'src/vn/rtr/aeris/native79';source.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(list(map(str,args)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True);logs.append(p.stdout+p.stderr);assert p.returncode==0,logs[-1];return p.stdout+p.stderr
try:
 derivatives=[]
 for p in (OLD/'src/vn/rtr/aeris/preflight44').glob('*.java'):
  text=p.read_text().replace('package vn.rtr.aeris.preflight44;','package vn.rtr.aeris.native79;')
  if p.name=='ShellActivity.java':text=text.replace('native44-drafts','native79-drafts').replace('getFilesDir(),"native79-drafts"','getFilesDir().getCanonicalFile(),"native79-drafts"').replace('catch(Exception e){Toast.makeText(this,','catch(Exception e){android.util.Log.e("NATIVE79","STORE_INIT",e);Toast.makeText(this,').replace('if(!trusted()){reply','if(!(Arrays.asList("save","load").contains(action)?storageTrusted():trusted())){reply').replace(' private boolean trusted()', ' private boolean storageTrusted(){return !dead&&web!=null&&PAGE.equals(web.getUrl());}\n private boolean trusted()')
  q=source/p.name;q.write_text(text);derivatives.append({'source':str(p.relative_to(R)),'sourceSha256':sha(p),'derived':str(q.relative_to(R)),'derivedSha256':sha(q)})
 for file in ['AndroidProbe.java']:
  p=R/'native/shell30/src/vn/rtr/aeris/shell30'/file;q=source/file;q.write_text(p.read_text().replace('package vn.rtr.aeris.shell30;','package vn.rtr.aeris.native79;'))
 p=R/'native/shell30/tests/vn/rtr/aeris/shell30/DraftStoreTest.java';q=source/'DraftStoreTest.java';q.write_text(p.read_text().replace('package vn.rtr.aeris.shell30;','package vn.rtr.aeris.native79;').replace('count()==64','count()==DraftStore.MAX_RECORDS').replace('quota retains64records','quota retains all bounded records'))
 manifest=(OLD/'AndroidManifest.xml').read_text().replace('vn.rtr.aeris.preflight44','vn.rtr.aeris.native79').replace('versionCode="44"','versionCode="83"').replace('0.4.4-native44-development','0.7.9-native79-development07').replace('AERIS Preflight Mock','AERIS Native79 · Mock')
 manifest=manifest.replace('</manifest>','<instrumentation android:name=".JournalInstrumentation" android:targetPackage="vn.rtr.aeris.native79" android:label="Development persistence QA only"/></manifest>');(N/'AndroidManifest.xml').write_text(manifest);assets=W/'assets/editor';assets.mkdir(parents=True);assetPins={}
 for p in OLD.rglob('*'):
  if not p.is_file() or not(p.suffix in ['.mjs','.html','.css','.ttf'])or p.name.endswith('-qa.mjs')or p.name in ['tests.mjs','server.mjs','memory-store.mjs']:continue
  q=assets/p.relative_to(OLD);q.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes()
  if p.name=='shell.css':data=data.replace(b'height:calc(100dvh - 310px)',b'height:calc(100vh - 310px);height:calc(100dvh - 310px)')
  q.write_bytes(data);assetPins[str(p.relative_to(OLD))]={'originalSha256':sha(p),'packagedSha256':sha(q)}
 host=W/'host';host.mkdir();pure=[p for p in source.glob('*.java')if p.name not in ['ShellActivity.java','AndroidProbe.java','JournalInstrumentation.java']]
 run([J/'bin/javac','--release','8','-d',host,*pure]);test=run([J/'bin/java','-cp',host,'vn.rtr.aeris.native79.DraftStoreTest',W/'tests']);(E/'host-journal07.txt').write_text(test)
 classes=W/'classes';classes.mkdir();run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*source.glob('*.java')]);run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',W/'assets','-o',W/'unsigned.apk']);dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*classes.rglob('*.class')])
 with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
 run([B/'zipalign','-f','4',W/'unsigned.apk',W/'aligned.apk']);apk=D/'aeris-native79-development07.apk';assert not apk.exists()
 run([B/'apksigner','sign','--ks',K/'development.p12','--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',apk,W/'aligned.apk']);signature=run([B/'apksigner','verify','--verbose','--print-certs',apk]);(E/'signature07.txt').write_text(signature)
 assert '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800' in signature
 permissions=run([B/'aapt2','dump','permissions',apk]);assert 'uses-permission:'not in permissions;(E/'permissions07.txt').write_text(permissions)
 with zipfile.ZipFile(apk)as z,zipfile.ZipFile(W/'aligned.apk')as u:assert all(z.read(n)==u.read(n)for n in u.namelist())
 report={'status':'DEVELOPMENT_APK_BUILT_HOST_JOURNAL_PASS_ANDROID_PENDING','apk':str(apk.relative_to(R)),'sha256':sha(apk),'bytes':apk.stat().st_size,'assets':assetPins,'derivatives':derivatives,'sourcePins':{str(p.relative_to(R)):sha(p)for p in [*source.glob('*.java'),N/'AndroidManifest.xml',N/'build.py']},'hostChecks':sum(l.startswith('PASS ')for l in test.splitlines()),'networkPermissions':0,'signature':'Existing NATIVE31 dedicated development only; no release/candidate signature'}
 with(E/'build07.json').open('x')as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:report[k]for k in ['status','apk','sha256','bytes','hostChecks']}))
finally:
 with(E/'build-log07.txt').open('x')as f:f.write('\n'.join(logs))
 shutil.rmtree(W)
