from ui94 import *
import base64

_capture97=capture
def capture(name):
 original=name
 for i in range(1,101):
  if not(E/(name+'.png')).exists():return _capture97(name)
  name=original+'-r'+str(i)
 raise AssertionError('SCREENSHOT_HISTORY_BOUND')

def last97():
 current=adb('exec-out','cat','/data/user/0/'+P+'/files/ui96/CURRENT').decode().strip();raw=adb('exec-out','cat','/data/user/0/'+P+'/files/ui96/'+current+'.jsonl');receipt=json.loads(raw.splitlines()[-1]);uptime=float(adb('shell','cat','/proc/uptime').split()[0])*1000
 if 0<=uptime-receipt['nativeElapsedMs']<1800:return receipt['renderer']
 return last()

def find97(identifier):
 for direction in (['down','up']if identifier in ['value97','yaw97','target-front97','target-center97','target-rear97','fixture97','open97','discover97','close97','refresh97']else['up','down']):
  old=None
  for _ in range(12):
   c=last()['controls'];found=[x for x in c if x['id']==identifier and not x['covered']and not x['disabled']]
   if found:return found[0]
   key=json.dumps([(x['id'],x['x'],x['y'])for x in c])
   if key==old:break
   old=key;swipe94(direction)
 raise AssertionError('UI_CONTROL_NOT_VISIBLE:'+identifier)
def tap97(identifier):
 x=find97(identifier);adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));time.sleep(.3)
def current_run():
 names=adb('shell','ls','-t','/data/user/0/'+P+'/files/payload97').decode().split();assert names;return names[0]
def rows(run):
 b=adb('exec-out','cat','/data/user/0/'+P+'/files/payload97/'+run+'/raw.jsonl');return[json.loads(l)for l in b.splitlines()]
def parsed(run):return[(r['kind'],json.loads(base64.b64decode(r['dataBase64'])))for r in rows(run)if r['kind']not in['RX','TX_INTENT','TX_WRITTEN']]
def state(run):return next(v for k,v in reversed(parsed(run))if k=='STATE')
def wait97(run,predicate,timeout=8):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  p=parsed(run)
  if predicate(p):return p
  if any(k=='CLOSED'for k,v in p):raise AssertionError('NATIVE_CLOSED:'+str(p[-3:]))
  time.sleep(.15)
 raise AssertionError('NATIVE_EVENT_DEADLINE')
def choose97(index,label):
 tap97('target-'+['front','center','rear'][index]+'97');time.sleep(.1);capture(label+'-target-selected')
def value97(identifier,value):
 x=find97(identifier);adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent',*(['KEYCODE_DEL']*12));adb('shell','input','text',str(value));adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.2)
if __name__=='__main__':
 owned();op=sys.argv[1]
 if op=='tap':tap97(sys.argv[2]);show()
 elif op=='choose':choose97(int(sys.argv[2]),sys.argv[3])
 elif op=='value':value97(sys.argv[2],sys.argv[3]);capture(sys.argv[4])
 elif op=='state':print(json.dumps(state(current_run()),ensure_ascii=False))
