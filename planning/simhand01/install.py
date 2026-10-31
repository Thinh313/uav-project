"""Explicit USB serial only; isolated package, no phone root or other-app changes."""
import argparse,json,re,subprocess,sys,time,uuid,os
from pathlib import Path
from support import ROOT,E,ADB,PKG,sha,put,command,disk,verify_manifest
APK=ROOT/'native/simhand01/dist/aeris-simhand01-development01.apk'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['install','uninstall','status']);p.add_argument('--serial',required=True);p.add_argument('--wait-seconds',type=int,default=60);p.add_argument('--launch',action='store_true');p.add_argument('--confirm-own-app-data-removal',action='store_true');a=p.parse_args()
 if not re.fullmatch('[A-Za-z0-9_.-]{1,128}',a.serial)or a.serial.startswith('emulator-')and a.serial!='emulator-5582':raise RuntimeError('EXPLICIT_USB_OR_OWN_EMULATOR5582_SERIAL_REQUIRED')
 if not 0<=a.wait_seconds<=300:raise RuntimeError('WAIT_BOUND_300S')
 steps=[]
 def adb(*args):
  r=subprocess.run([str(ADB),'-s',a.serial,*map(str,args)],cwd=ROOT,capture_output=True,text=True,timeout=120);steps.append({'args':list(args),'exit':r.returncode,'stdout':r.stdout[-12000:],'stderr':r.stderr[-2000:]})
  if r.returncode:raise RuntimeError('ADB_ACTION_FAILED_NO_RETRY:'+str(args[0])+':'+r.stderr[-500:])
  return r.stdout.strip()
 end=time.monotonic()+a.wait_seconds
 while True:
  r=subprocess.run([str(ADB),'devices'],capture_output=True,text=True,timeout=10);states=dict(x.split()[:2]for x in r.stdout.splitlines()[1:]if len(x.split())>=2)
  if states.get(a.serial)=='device':break
  if states.get(a.serial)=='unauthorized':raise RuntimeError('AUTHORIZE_THIS_COMPUTER_ON_SELECTED_PHONE')
  if time.monotonic()>=end:print(json.dumps({'status':'NOT_CHECKED_SELECTED_SERIAL_NOT_ATTACHED','serial':a.serial,'automaticSelection':False}));return 3
  time.sleep(1)
 ident={'serial':a.serial,'model':adb('shell','getprop','ro.product.model'),'android':adb('shell','getprop','ro.build.version.release'),'sdk':adb('shell','getprop','ro.build.version.sdk'),'physical':not a.serial.startswith('emulator-'),'phoneRootRequested':False}
 if a.action=='install':
  disk(True)
  if(E/'budget.json').exists():expected=json.loads((E/'android-build01.json').read_text())['sha256']
  else:verify_manifest();expected=json.loads((ROOT/'bundle-manifest.json').read_text())['files'][str(APK.relative_to(ROOT))]['sha256']
  if sha(APK)!=expected:raise RuntimeError('APK_SHA_DRIFT')
  adb('reverse','tcp:8896','tcp:8896');adb('install','-r',str(APK))
  if a.launch:adb('shell','am','start','-W','-n',PKG+'/.ShellActivity','--es','initialPath','/phone')
 elif a.action=='uninstall':
  if not a.confirm_own_app_data_removal:raise RuntimeError('EXPLICIT_OWN_APP_DATA_REMOVAL_FLAG_REQUIRED')
  adb('shell','am','force-stop',PKG);adb('uninstall',PKG)
 else:adb('shell','dumpsys','package',PKG)
 q={'status':'PASS_SELECTED_DEVICE_COMMANDS_ONLY_NOT_FLIGHT_ACCEPTANCE','action':a.action,'device':ident,'apkSha256':sha(APK)if APK.exists()else None,'package':PKG,'steps':steps,'noOtherAppsTouched':True,'authorityRestored':False};put(E/'installs'/('install-'+uuid.uuid4().hex+'.json'),q);print(json.dumps(q,indent=2));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(2)
