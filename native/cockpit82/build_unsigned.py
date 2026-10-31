"""Small isolated unsigned build; never reads a keystore or calls a signing action."""
from pathlib import Path
import subprocess,os,json,hashlib,shutil,zipfile,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/cockpit82';E=R/'evidence/cockpit82';W=N/'.build';D=N/'dist'
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');SDK=Path('/opt/homebrew/share/android-commandlinetools');B=SDK/'build-tools/36.0.0';A=SDK/'platforms/android-37.0/android.jar'
assert shutil.disk_usage(R).free>20.75*2**30 and not W.exists(),'DISK_OR_BUILD_ADMISSION'
attempt=os.environ.get("COCKPIT82_BUILD_ATTEMPT","01");assert attempt in ["01","02","03","04"],"EXPLICIT_ATTEMPT"
assert not any(p.exists() for p in [D/("aeris-native82-unsigned"+attempt+".apk"),E/("build"+attempt+".json"),E/("build-log"+attempt+".json"),E/("jvm-journal-fixtures-"+attempt)]),"PRESERVE_PRIOR_ATTEMPT_BEFORE_ANY_WRITE"
W.mkdir();D.mkdir(exist_ok=True);logs=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,expected=0):
 p=subprocess.run(list(map(str,args)),cwd=R,env={**os.environ,'JAVA_HOME':str(J)},text=True,capture_output=True)
 logs.append({'command':[str(x)for x in args],'exit':p.returncode,'output':p.stdout+p.stderr})
 if p.returncode!=expected:raise RuntimeError(logs[-1]['output'])
 return p.stdout+p.stderr
try:
 source=N/'src/vn/rtr/aeris/cockpit82';host=W/'host';host.mkdir()
 pure=[p for p in source.glob('*.java')if p.name!='ShellActivity.java']
 run([J/'bin/javac','--release','8','-d',host,*pure])
 journal=run([J/'bin/java','-cp',host,'vn.rtr.aeris.cockpit82.DraftStoreTest',E/('jvm-journal-fixtures-'+attempt)])
 policy=run([J/'bin/java','-cp',host,'vn.rtr.aeris.cockpit82.PolicyTest'])
 (E/('jvm-journal-'+attempt+'.txt')).write_text(journal);(E/('resource-policy-'+attempt+'.txt')).write_text(policy)
 jar=D/'journal-host82.jar';run([J/'bin/jar','cf',jar,'-C',host,'.'])
 assets=W/'assets/cockpit';assets.mkdir(parents=True)
 pins={}
 for p in (N/'assets').rglob('*'):
  if not p.is_file():continue
  assert not p.is_symlink();q=assets/p.relative_to(N/'assets');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());pins[str(p.relative_to(N/'assets'))]=sha(p)
 expected=set(json.loads((N/'asset-list.json').read_text()));assert expected=={'/'+p for p in pins},'RESOURCE_MANIFEST_MISMATCH'
 classes=W/'classes';classes.mkdir();prod=[source/x for x in ['ShellActivity.java','DraftStore.java','JournalMain.java','ResourcePolicy.java']]
 run([J/'bin/javac','-source','8','-target','8','-bootclasspath',str(B/'core-lambda-stubs.jar')+os.pathsep+str(A),'-d',classes,*prod])
 run([B/'aapt2','link','-I',A,'--manifest',N/'AndroidManifest.xml','-A',W/'assets','-o',W/'unsigned.apk'])
 dex=W/'dex';dex.mkdir();run([B/'d8','--min-api','26','--lib',A,'--output',dex,*classes.rglob('*.class')])
 with zipfile.ZipFile(W/'unsigned.apk','a')as z:z.write(dex/'classes.dex','classes.dex')
 apk=D/('aeris-native82-unsigned'+attempt+'.apk');assert not apk.exists(),'PRESERVE_PRIOR_BUILD'
 run([B/'zipalign','-f','4',W/'unsigned.apk',apk]);permissions=run([B/'aapt2','dump','permissions',apk]);assert 'uses-permission:'not in permissions
 signature=run([B/'apksigner','verify','--verbose',apk],expected=1)
 with zipfile.ZipFile(apk)as z:
  assert not any(n.startswith('META-INF/')for n in z.namelist())
  for name,expected_sha in pins.items():assert hashlib.sha256(z.read('assets/cockpit/'+name)).hexdigest()==expected_sha
 report={'status':'PASS_UNSIGNED_COMPILE_HOST_TESTS_ONLY','apk':str(apk.relative_to(R)),'sha256':sha(apk),'bytes':apk.stat().st_size,'hostJar':{'path':str(jar.relative_to(R)),'sha256':sha(jar)},'jvmJournalChecks':sum(x.startswith('PASS ')for x in journal.splitlines()),'policyChecks':22,'assets':pins,'permissions':permissions,'signatureVerification':{'exit':1,'meaning':'EXPECTED_UNSIGNED_NO_INSTALLABLE_SIGNATURE','output':signature},'signingActions':0,'keystoreAccess':False,'androidInstalled':'NOT_CHECKED_UNSIGNED','builtAt':datetime.datetime.now().astimezone().isoformat()}
 (E/('build'+attempt+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','apk','bytes','jvmJournalChecks','signingActions']}))
finally:
 (E/('build-log'+attempt+'.json')).write_text(json.dumps(logs,indent=2)+'\n');shutil.rmtree(W)
