from ui94 import *
owned();adb('shell','am','force-stop',P);adb('reverse','--remove','tcp:8874');adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(.8);journal('05-closed-offline');adb('reboot');end=time.monotonic()+70
while time.monotonic()<end:
 try:
  if adb('shell','getprop','sys.boot_completed',allow_failure=True).strip()==b'1':break
 except Exception:pass
 time.sleep(1)
owned();adb('root');time.sleep(.5);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(.8);journal('05-after-reboot');adb('shell','input','tap',52,375);time.sleep(.6);capture('05-review-offline-list');show()
