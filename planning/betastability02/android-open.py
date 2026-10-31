import time,subprocess,json,sys
from pathlib import Path
A='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';end=time.monotonic()+100;rows=[]
while time.monotonic()<end:
 p=subprocess.run([A,'devices'],capture_output=True,text=True)
 if 'emulator-5582\tdevice'in p.stdout:
  q=subprocess.run([A,'-s','emulator-5582','shell','getprop','sys.boot_completed'],capture_output=True,text=True,timeout=5);rows.append({'at':time.time(),'boot':q.stdout.strip(),'exit':q.returncode})
  if q.stdout.strip()=='1':break
 time.sleep(2)
else:raise RuntimeError('OWNED_ANDROID_BOOT_DEADLINE')
with Path('evidence/betastability02/android-boot-observation'+sys.argv[1]+'.json').open('x')as f:json.dump(rows,f,indent=2)
p=subprocess.run([sys.executable,'-B','pilot/betastability02/companion.py','android']);sys.exit(p.returncode)
