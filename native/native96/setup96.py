from android_qa import *
owned();adb('root');time.sleep(.6);assert b'uid=0'in adb('shell','id')
before={}
for v in range(90,96):
 package='vn.rtr.aeris.native'+str(v);raw=adb('exec-out','tar','-C','/data/user/0/'+package+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw))as t:before[package]={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest()for m in t.getmembers()if m.isfile()}
(E/'old-private-before.json').open('x').write(json.dumps(before,indent=2));b=json.loads((E/'build01.json').read_text());apk=R/b['apk'];assert hashlib.sha256(apk.read_bytes()).hexdigest()==b['sha256'];adb('install','-r',apk,timeout=60);path=adb('shell','pm','path',P).decode().strip()[8:];assert path.startswith('/data/app/')and hashlib.sha256(adb('exec-out','cat',path)).hexdigest()==b['sha256']
(E/'installed01.json').open('x').write(json.dumps({'status':'PASS','apkSha256':b['sha256'],'sourceId':b['sourceId'],'package':P,'serial':S},indent=2));adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(1.5);capture('96-offline-installed');reports('96-offline-installed');print({p:len(x)for p,x in before.items()})
