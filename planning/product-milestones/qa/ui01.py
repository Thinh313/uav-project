from ui98 import *

def control01(identifier,enabled=True):
 for direction in ['up','down']:
  previous=None
  for _ in range(6):
   controls=last()['controls'];rs=[x for x in controls if x['id']==identifier and not x['covered']]
   if rs:
    if not enabled or not rs[0]['disabled']:return rs[0]
    time.sleep(.35);again=[x for x in last()['controls']if x['id']==identifier and not x['covered']and not x['disabled']]
    if again:return again[0]
    raise AssertionError('MAIN_FLY_CONTROL_DISABLED:'+identifier)
   key=[(x['id'],round(x['y']))for x in controls]
   if key==previous:break
   previous=key;swipe94(direction)
 raise AssertionError('MAIN_FLY_CONTROL_NOT_VISIBLE_OR_DISABLED:'+identifier)

def tap01(identifier):
 x=control01(identifier)
 with(E/'actions01.jsonl').open('a')as f:f.write(json.dumps({'atHostMonoNs':time.monotonic_ns(),'action':'tap','id':identifier,'observedControl':x})+'\n')
 adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));time.sleep(.25)

def value01(identifier,value):
 x=control01(identifier);adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent',*(['KEYCODE_DEL']*12));adb('shell','input','text',str(value));adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.15)

def select01(identifier,label):
 options={'op-actor':['Phi công A','Payload B'],'op-target':['Trước · 100','Giữa · 102','Sau · 101']};index=options[identifier].index(label)
 x=control01(identifier);tap01(identifier);time.sleep(.15)
 # Visually verified native WebView select list: 54px rows below this 48px control.
 # Keyboard Enter bubbles to cockpit actions in WebView101, so use touch only.
 adb('shell','input','tap',round((x['x']+x['right'])/2),round(x['bottom']+27+54*index));time.sleep(.25)

if __name__=='__main__':
 owned();op=sys.argv[1]
 if op=='tap':tap01(sys.argv[2]);show()
 elif op=='value':value01(sys.argv[2],sys.argv[3]);show()
 elif op=='show':show()
