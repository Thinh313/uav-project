"""Independent read-only package/input closure. No build, signing or install."""
from pathlib import Path
import hashlib,json,subprocess,tarfile,zipfile,datetime,os
R=Path(__file__).resolve().parents[4];E=R/'evidence/betaintegrated01-cockpit05-native';B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 receipt=E/'build-02.json';r=json.loads(receipt.read_text());apk=R/r['apk'];assert sha(apk)==r['sha256'];assert len(r['sourcePins'])==37
 assert all(sha(R/p)==s for p,s in r['sourcePins'].items())
 archive=R/r['inputArchive'];assert sha(archive)==r['inputArchiveSHA256']
 with tarfile.open(archive,'r:')as t:
  assert {m.name for m in t}==set(r['sourcePins'])
  for member in t:
   assert member.isfile();assert hashlib.sha256(t.extractfile(member).read()).hexdigest()==r['sourcePins'][member.name]
 ui=R/'native/betaintegrated01/cockpit05/assets';expected={str(p.relative_to(ui)):p for p in ui.rglob('*')if p.is_file()};assert len(expected)==8
 with zipfile.ZipFile(apk)as z:
  names=z.namelist();assert len(names)==len(set(names));assert not any('mock-bridge' in n or '/mock.' in n for n in names)
  assert {n[len('assets/cockpit/'):]for n in names if n.startswith('assets/cockpit/')}==set(expected)
  for n,p in expected.items():assert z.read('assets/cockpit/'+n)==p.read_bytes()
  identity=json.loads(z.read('assets/source-identity.json'));assert identity['sourceSHA256']==r['sourceSHA256'] and identity['OwnerRevision']=='OWNER03_ALGORITHM_CAPACITY160_SHADOW'
  assert identity['UIRevision']=='UI05_VALIDATION_NOTICE_FOOTER_ONLY_NO_LOGIC_CHANGE'
  dex=z.read('classes.dex');assert b'Lvn/rtr/aeris/cockpit05/CockpitActivity;'in dex and b'Lvn/rtr/aeris/cockpit04/CockpitActivity;'not in dex
  assert b'Lvn/rtr/aeris/control01/ControlOwner;'in dex
 oldReceipt=json.loads((E/'build-01.json').read_text());oldAPK=R/oldReceipt['apk'];assert sha(oldAPK)==oldReceipt['sha256']
 with zipfile.ZipFile(oldAPK)as old,zipfile.ZipFile(apk)as new:
  assert set(old.namelist())==set(new.namelist());functional=[n for n in old.namelist()if not n.startswith('META-INF/')and old.read(n)!=new.read(n)]
  assert set(functional)=={'assets/cockpit/index.html','assets/cockpit/cockpit.css','assets/source-identity.json'}
  assert old.read('classes.dex')==new.read('classes.dex')
 sig=subprocess.run([str(B/'apksigner'),'verify','--verbose','--print-certs',str(apk)],capture_output=True,text=True,env={**os.environ,'JAVA_HOME':'/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'});assert sig.returncode==0 and '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'in sig.stdout
 badging=subprocess.run([str(B/'aapt2'),'dump','badging',str(apk)],capture_output=True,text=True);assert badging.returncode==0 and "package: name='vn.rtr.aeris.cockpit05'"in badging.stdout
 manifest=(R/'native/betaintegrated01/cockpit05/AndroidManifest.xml').read_text();assert 'android:debuggable="true"'in manifest and 'android:allowBackup="false"'in manifest
 prior=json.loads((R/'evidence/betaintegrated01-m1cockpit04/native/build-02.json').read_text());assert all(sha(R/p)==s for p,s in prior['sourcePins'].items())
 result={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_PACKAGED_CLOSURE_DEVELOPMENT_NOT_RUNTIME','apkSHA256':sha(apk),'sourceSHA256':r['sourceSHA256'],'inputs':len(r['sourcePins']),'inputArchiveSHA256':sha(archive),'UIAssetCount':len(expected),'UIAssetsExact':True,'mockBridgePackaged':False,'package':'vn.rtr.aeris.cockpit05','signature':sig.stdout,'badging':badging.stdout,'prior04InputsUnchanged':True,'sourcePins':r['sourcePins'],'functionalPayloadChangesFrom01':functional,'classesDexByteExact01':True,'runtimeClaim':False,'installOrBuildOrSignByQA':False}
 out=E/'qa/apk-closure02.json';out.open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],result['apkSHA256'])
if __name__=='__main__':main()
