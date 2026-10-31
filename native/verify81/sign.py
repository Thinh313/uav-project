from pathlib import Path
import hashlib,json,subprocess,os,shutil,zipfile
R=Path(__file__).resolve().parents[2]; E=R/'evidence/native81-development01'; D=R/'native/verify81'; B=Path('/opt/homebrew/share/android-commandlinetools/build-tools/36.0.0'); K=R/'.local/native31'
source=R/'native/cockpit81/dist/aeris-native81-unsigned03.apk'; target=D/'aeris-native81-development01.apk'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert shutil.disk_usage(R).free>21*2**30
assert sha(source)=='8c539276dfdece0d6291973987c49a766c5bafa7a2c15cea4278167269b8661d'
assert not target.exists() and not(E/'signing.json').exists()
env={**os.environ,'JAVA_HOME':'/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home'}
p=subprocess.run([str(B/'apksigner'),'sign','--ks',str(K/'development.p12'),'--ks-key-alias','native31-development','--ks-pass','file:'+str(K/'password'),'--out',str(target),str(source)],env=env,capture_output=True,text=True)
assert p.returncode==0,p.stderr
v=subprocess.run([str(B/'apksigner'),'verify','--verbose','--print-certs',str(target)],env=env,capture_output=True,text=True)
(E/'signature.txt').write_text(v.stdout+v.stderr)
assert v.returncode==0 and '3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800' in v.stdout
with zipfile.ZipFile(source)as a,zipfile.ZipFile(target)as b:
 assert all(a.read(n)==b.read(n)for n in a.namelist()); count=len(a.namelist())
per=subprocess.run([str(B/'aapt2'),'dump','permissions',str(target)],capture_output=True,text=True);assert per.returncode==0 and 'uses-permission:'not in per.stdout
r={'status':'PASS_DEVELOPMENT_SIGNATURE_ONLY','unsignedSha256':sha(source),'apk':str(target.relative_to(R)),'sha256':sha(target),'bytes':target.stat().st_size,'unchangedZipEntries':count,'sourceChanges':0,'networkPermissions':0,'identity':'existing dedicated native31 development certificate; not release/candidate','certSha256':'3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'}
(E/'signing.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
