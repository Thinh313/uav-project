"""ADB/UIAutomator limited to owned emulator. Uses APK self-reported hit boxes; no JS/DOM injection."""
from pathlib import Path
import sys,json,time
sys.path.insert(0,str(Path(__file__).parent));from android_qa import *
def last():
 raw=adb('exec-out','cat','/data/user/0/'+P+'/files/ui86.jsonl');return json.loads(raw.splitlines()[-1])['renderer']
def tap94(id):
 rows=[x for x in last()['controls']if x['id']==id and not x['covered']and not x['disabled']]
 assert len(rows)==1,(id,rows)
 x=rows[0];adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));time.sleep(.35)
def swipe94(direction='up'):
 adb('shell','input','swipe',655,515 if direction=='up'else 260,655,260 if direction=='up'else 515,350);time.sleep(.35)
def show():print(json.dumps({'status':last().get('sourceStatus'),'controls':[{k:x[k]for k in['id','x','y','disabled','covered']}for x in last()['controls']if x.get('inPanel')]},ensure_ascii=False))
if __name__=='__main__':
 owned()
 if sys.argv[1]=='install':
  adb('shell','am','force-stop',P);adb('install','-r',R/'native/native94/dist/aeris-native94-development02.apk',timeout=60);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(2);capture('offline-build02');show()
 elif sys.argv[1]=='tap':tap94(sys.argv[2]);show()
 elif sys.argv[1]=='swipe':swipe94(sys.argv[2]if len(sys.argv)>2 else'up');show()
 elif sys.argv[1]=='show':show()
