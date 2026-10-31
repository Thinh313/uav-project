from ui94 import *
owned();b=json.loads((E/'build03.json').read_text());apk=R/b['apk'];assert hashlib.sha256(apk.read_bytes()).hexdigest()==b['sha256']
adb('shell','am','force-stop',P);adb('install','-r',apk,timeout=60)
path=adb('shell','pm','path',P).decode().strip();assert path.startswith('package:/data/app/') and path.endswith('/base.apk') and '\n'not in path
installed=adb('exec-out','cat',path[8:]);assert hashlib.sha256(installed).hexdigest()==b['sha256']
(E/'installed03.json').open('x').write(json.dumps({'status':'PASS','apk':b['apk'],'deviceSha256':b['sha256'],'sourceId':b['sourceId'],'serial':S,'package':P,'scope':'OWNED_EMULATOR_ONLY'},indent=2))
print('APK03_INSTALLED_SHA_VERIFIED')
