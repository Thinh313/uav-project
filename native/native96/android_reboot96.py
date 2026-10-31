from android_qa import *
import sys
owned();label=sys.argv[1];assert not(E/'android-closure02.json').exists();start=time.monotonic_ns();adb('reboot');end=time.monotonic()+80
while time.monotonic()<end:
 try:
  if adb('shell','getprop','sys.boot_completed',allow_failure=True).strip()==b'1':break
 except Exception:pass
 time.sleep(1)
else:raise AssertionError('ANDROID_BOOT_DEADLINE')
owned();adb('root');time.sleep(1);assert b'uid=0'in adb('shell','id');adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(1);capture(label+'-after-android-reboot');b=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.');(E/(label+'-after-android-reboot.tar')).open('xb').write(b)
def unpack(raw):
 with tarfile.open(fileobj=io.BytesIO(raw))as t:return{m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
before=unpack((E/'rawsaf-loss05-pending-before-reboot.tar').read_bytes());after=unpack(b);keys=[k for k in before if k.startswith(('./direct95/','./workspaces/','./raw-packages96/'))];assert keys and all(before[k]==after.get(k)for k in keys);assert sorted(k for k in before if k.startswith('./direct95/'))==sorted(k for k in after if k.startswith('./direct95/'))
ops=[]
for n,h in after.items():
 if n.startswith('./raw-fileops96/')and n.endswith('/HEAD'):
  head=h.decode().strip();member=next(k for k in after if k.startswith(n[:-4])and k.endswith(head+'.bin'));fields=[__import__('base64').b64decode(l).decode()for l in after[member].split(b'\n',6)[6].splitlines()[1:]];ops.append(fields)
unknown=[o for o in ops if o[4]=='UNKNOWN'];assert len(unknown)==1 and unknown[0][-1]=='PROCESS_RESTART_OUTCOME_UNCONFIRMED_NO_RETRY';assert any(o[4]=='COMPLETED'for o in ops)
(E/(label+'-restart-verification.json')).open('x').write(json.dumps({'status':'PASS','serial':S,'androidReboot':True,'elapsedHostMs':(time.monotonic_ns()-start)/1e6,'preservedBytesFiles':len(keys),'sameDirectRawGenerationList':True,'pendingRecoveredAsUnknown':unknown,'oldCompletedRetained':True,'authorityRestorable':False,'restoredSource':'default mock, no owned launch assertion','operations':ops},indent=2));print('ANDROID_REBOOT_RAW_WORKSPACE_STAGE_PRESERVED_PENDING_UNKNOWN')
