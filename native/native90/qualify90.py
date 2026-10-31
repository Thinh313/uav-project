from android_qa import *
def tap(x,y):adb('shell','input','tap',x,y)
def traces(name):
 b=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','diagnostics90');(E/(name+'.tar')).open('xb').write(b)
def media():
 owned();adb('shell','am','force-stop',P);adb('install','-r','native/native90/dist/aeris-native90-development08.apk');adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(7);capture('android90-08-cold');tap(52,490);time.sleep(.2);capture('android90-08-diagnostics');print(json.dumps(compact(),ensure_ascii=False));tap(960,350);tap(1140,285);adb('shell','input','dpad','keyevent','19');adb('shell','input','gamepad','keyevent','96');adb('shell','input','joystick','motionevent','MOVE','.5','-.25');tap(780,280);time.sleep(.65);tap(960,285);tap(230,310);time.sleep(.4);capture('android90-08-playing');time.sleep(2);capture('android90-08-ended');tap(52,490);time.sleep(.15);tap(410,310);time.sleep(1.4);capture('android90-08-stale');tap(452,255);time.sleep(.35);adb('shell','input','keyevent','3');time.sleep(.2);capture('android90-08-home');adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(.6);capture('android90-08-resumed');tap(52,490);time.sleep(.15);tap(780,280);time.sleep(.20);adb('shell','input','keyevent','3');time.sleep(.2);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(.6);capture('android90-08-input-resumed');traces('diagnostics08-media');print('MEDIA_CAPTURED')
if __name__=='__main__':
 import sys
 if sys.argv[1]=='media':media()
