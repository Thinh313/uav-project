from pathlib import Path
import sys,json,hashlib,zipfile,shutil,subprocess,datetime,os,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];E=R/'evidence/phone06-qa';W=R/'.local/phone06-qa-apk-stage01';OUT=E/'apk-verification01.json';assert not W.exists()and not OUT.exists();assert shutil.disk_usage(R).free>=20*2**30+32*2**20
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads((R/p).read_text());closure=read('evidence/phone06/builder/source-ready07.json');build=read('evidence/phone06/builder/build01.json');frozen=read('evidence/phone06/builder/build-source-freeze01.json');apk=R/build['apk'];logs=[];result={};error=None
B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0');J='/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'
def run(args):
 p=subprocess.run(list(map(str,args)),cwd=R,env={**os.environ,'JAVA_HOME':J},capture_output=True,text=True,timeout=20);logs.append({'command':list(map(str,args)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr;return p.stdout
try:
 for p,h in closure['files'].items():assert sha((R/p).read_bytes())==h,p
 for p,h in build['sourceFiles'].items():assert sha((R/p).read_bytes())==h,p
 assert frozen['files']==build['sourceFiles']
 assert sha(apk.read_bytes())==build['sha256']=='0a1423e38f29565b4b22c9c14b1ae1beaffce6dcb46618ee583bd7b2871a9c2b'and apk.stat().st_size==3799006
 assert sha(json.dumps(build['sourceFiles'],sort_keys=True).encode())==build['sourceId']=='46f38b12a9e2eec5f461322b6269b781b7142d6f09d0b5951eee3f7e71472cf1'
 sys.path.insert(0,str(R/'native/phone06'));from overlay import stage
 W.mkdir();pins=stage(W);assert pins==build['sourceFiles']
 with zipfile.ZipFile(apk)as z:
  names=z.namelist();assert len(set(names))==len(names)and z.testzip()is None
  expected={'assets/cockpit/'+str(p.relative_to(W/'assets')):sha(p.read_bytes())for p in (W/'assets').rglob('*')if p.is_file()}
  actual={n:sha(z.read(n))for n in names if n.startswith('assets/')and not n.endswith('/')}
  assert actual==expected,{'missing':list(set(expected)-set(actual)),'extra':list(set(actual)-set(expected))}
  nonassets=[n for n in names if not n.startswith('assets/')];assert set(nonassets)=={'AndroidManifest.xml','classes.dex'},nonassets
  dex=z.read('classes.dex');assert dex.startswith(b'dex\n')and dex.count(build['sourceId'].encode())==1
  result.update({'apkEntries':len(names),'assetsExact':len(actual),'assetPins':actual,'duplicateEntries':0,'unexpectedEntries':[],'classesDexSha256':sha(dex),'manifestBinarySha256':sha(z.read('AndroidManifest.xml')),'embeddedBuildSourceIdCount':1})
 sig=run([B/'apksigner','verify','--verbose','--print-certs',apk]);assert 'Verified using v2 scheme (APK Signature Scheme v2): true'in sig and 'Verified using v3 scheme (APK Signature Scheme v3): true'in sig and 'Number of signers: 1'in sig and '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in sig
 badging=run([B/'aapt2','dump','badging',apk]);assert "package: name='vn.rtr.aeris.phone06' versionCode='106' versionName='0.12.0-phone06-development'"in badging and "minSdkVersion:'26'"in badging and "targetSdkVersion:'33'"in badging
 perms=run([B/'aapt2','dump','permissions',apk]);assert [s for s in perms.splitlines()if s.startswith('uses-permission:')]==["uses-permission: name='android.permission.INTERNET'"]
 manifest=run([B/'aapt2','dump','xmltree','--file','AndroidManifest.xml',apk]);assert 'android:debuggable'in manifest and 'android:allowBackup'in manifest
 for p,h in closure['files'].items():assert sha((R/p).read_bytes())==h,p
 for p,h in build['sourceFiles'].items():assert sha((R/p).read_bytes())==h,p
except BaseException:error=traceback.format_exc()
finally:
 OUT.open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS_SCOPED_SIGNED_DEVELOPMENT_APK_INTEGRITY'if error is None else'FAIL_RETAINED','apk':build['apk'],'apkSha256':build['sha256'],'bytes':apk.stat().st_size,'fullClosureSourceId':closure['sourceId'],'fullClosurePins':len(closure['files']),'apkEmbeddedBuildSourceId':build['sourceId'],'buildSourcePins':len(build['sourceFiles']),'differentSourceSetsIntentional':True,'result':result,'logs':logs,'error':error,'scratchRemoved':str(W.relative_to(R)),'limits':['APK signature/assets/source metadata verified. DEX not independently recompiled; fullsemanticbehavior rests on priorboundednative tests and buildchain.','No install/ART, Xiaomi, USB, AP, manual qualification, actualSAF or humanUI acceptance.','Existing certificate DN says Engineering Emulator Only; this is reuseddevelopmentidentity, notphonehardwarecertification orproductiontrust.']},indent=2)+'\n')
 if W.exists():shutil.rmtree(W)
print(OUT,error or 'PASS')
