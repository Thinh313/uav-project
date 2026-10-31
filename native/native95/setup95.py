from android_qa import *
owned()
assert b'uid=0' in adb('shell','id')
baseline={}
for version in range(90,95):
 package='vn.rtr.aeris.native'+str(version)
 raw=adb('exec-out','tar','-C','/data/user/0/'+package+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
  baseline[package]={m.name:hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive.getmembers() if m.isfile()}
(E/'old-private-before.json').open('x').write(json.dumps(baseline,indent=2))
apk=R/'native/native95/dist/aeris-native95-development02.apk'
assert hashlib.sha256(apk.read_bytes()).hexdigest()==json.loads((E/'build02.json').read_text())['sha256']
adb('install','-r',apk,timeout=60)
adb('shell','am','start','-n',P+'/.ShellActivity')
time.sleep(2)
capture('android95-offline-initial')
reports('android95-offline-initial')
print({p:len(x) for p,x in baseline.items()})
