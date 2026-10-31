from ui94 import *
def choose94(name):
 time.sleep(.4)
 present=nodes()
 if not any(n.get('text')==name for n in present):
  tap_label('Show roots');time.sleep(.3);tap_label('Downloads');time.sleep(.4)
 tap_label(name);time.sleep(.8)
if __name__=='__main__':
 owned()
 if sys.argv[1]=='install03':
  adb('shell','am','force-stop',P);adb('install','-r',R/'native/native96/dist/aeris-native94-development03.apk',timeout=60);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(1);swipe94();tap94('import-kml94');choose94('kml94-corridor.kml');capture('kml94-read03');show();tap94('inspect92');swipe94();show();capture('kml94-feature03')
 elif sys.argv[1]=='choose':choose94(sys.argv[2]);show()
