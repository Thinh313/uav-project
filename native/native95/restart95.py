from ui94 import *
owned()
before=json.loads((E/'s095e2c41e36548be9071-closed-workspace.json').read_text())
def private_files(package):
 raw=adb('exec-out','tar','-C','/data/user/0/'+package+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:return raw,{m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t.getmembers() if m.isfile()}
raw,hashes=private_files(P)
protected={k:v for k,v in hashes.items() if k.startswith(('./workspaces/','./direct95/'))}
adb('shell','am','force-stop',P);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(1)
j=journal('95-process-restart');assert j['files']==before['files']
adb('shell','input','tap',52,375);time.sleep(.7);capture('95-process-restart-history')
adb('reboot');end=time.monotonic()+70
while time.monotonic()<end:
 if adb('shell','getprop','sys.boot_completed',allow_failure=True).strip()==b'1':break
 time.sleep(1)
else:raise AssertionError('ANDROID_REBOOT_DEADLINE')
owned();adb('root');time.sleep(.5);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(1)
j=journal('95-reboot');assert j['files']==before['files']
adb('shell','input','tap',52,375);time.sleep(.7);capture('95-reboot-history');rows=reports('95-reboot-ui')
assert rows[-1]['environment']['source']=='mock' and rows[-1]['environment']['owned95'] is None and rows[-1]['environment']['hasHostToken'] is False
raw,after=private_files(P);assert {k:v for k,v in after.items() if k.startswith(('./workspaces/','./direct95/'))}==protected
(E/'android95-final-files.tar').open('xb').write(raw)
old=json.loads((E/'old-private-before.json').read_text());checks={}
for package,expected in old.items():
 _,actual=private_files(package);assert actual==expected,package;checks[package]=len(actual)
(E/'restart95.json').open('x').write(json.dumps({'status':'PASS','processRestart':True,'androidReboot':True,'workspaceAndRawProtectedFiles':len(protected),'bytesUnchanged':True,'automaticReconnect':False,'authorityRestored':False,'oldAppPrivateFilesUnchanged':checks,'scope':'CLOSED_SESSION_RESTART_NOT_AIRBORNE_CRASH_RECOVERY'},indent=2))
print('RESTART_PERSISTENCE_PASS')
