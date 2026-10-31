from saf94 import *
end=time.monotonic()+70
while time.monotonic()<end:
 try:
  if adb('shell','getprop','sys.boot_completed',allow_failure=True).strip()==b'1':break
 except Exception:pass
 time.sleep(1)
owned();adb('root');time.sleep(.5);adb('install','-r',R/'native/native94/dist/aeris-native94-development05.apk',timeout=60);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(1);journal('05-offline-reopened');capture('05-offline-reopened');adb('push',E/'kml94-prototype.kml','/sdcard/Download/kml94-prototype.kml');swipe94();tap94('import-kml94');choose94('kml94-prototype.kml');capture('05-xml-attribute-rejected');journal('05-xml-rejected');show()
for i in range(8):
 if any(x['id']=='native-compile'and not x['disabled']and not x['covered']for x in last()['controls']):break
 swipe94()
tap94('native-compile');time.sleep(.7);journal('05-offline-compiled');capture('05-offline-compiled');print('FINAL05_OFFLINE_COMPILE_DONE',flush=True)
