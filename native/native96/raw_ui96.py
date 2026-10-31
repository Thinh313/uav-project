"""Actual Android UI only: APK hitboxes freshly reported, system SAF UIAutomator. No injected JS/RPC."""
from ui94 import *

def find_control(identifier,tries=10):
 for direction in ['up','down']:
  previous=None
  for _ in range(tries):
   controls=last()['controls'];rows=[x for x in controls if x['id']==identifier and not x['covered']and not x['disabled']]
   if rows:return rows[0]
   key=json.dumps([(x['id'],x['x'],x['y'])for x in controls],sort_keys=True)
   if key==previous:break
   previous=key;swipe94(direction)
 raise AssertionError('CONTROL_NOT_VISIBLE:'+identifier)
def raw_panel():
 adb('shell','input','tap',52,535);time.sleep(.4)
 find_control('list-raw96');tap94('list-raw96');time.sleep(.3)
def prepare(run,label):
 raw_panel();find_control('run-raw96');tap94('run-raw96');time.sleep(.2)
 capture(label+'-selector-needs-inspection');print('SELECT_RAW_WITH_ACTUAL_SCREENSHOT_THEN_CONFIRM');return
def save(name,label):
 assert name.endswith('.zip')and'/'not in name
 edits=[n for n in nodes()if n.get('class','').endswith('EditText')];assert len(edits)==1,edits;e=edits[0];v=list(map(int,re.findall(r'\d+',e['bounds'])));adb('shell','input','tap',(v[0]+v[2])//2,(v[1]+v[3])//2);adb('shell','input','keyevent','KEYCODE_MOVE_END');adb('shell','input','keyevent',*(['KEYCODE_DEL']*len(e['text'])));adb('shell','input','text',name)
 assert any(n.get('text')==name and n.get('class','').endswith('EditText')for n in nodes());capture(label+'-filename');labels=[n['text']for n in nodes()if n.get('text','').lower()=='save'];assert len(labels)==1;tap_label(labels[0]);time.sleep(.6);capture(label+'-provider-readback');b=adb('exec-out','cat','/sdcard/Download/'+name);assert b[:2]==b'PK';(E/name).open('xb').write(b);print(json.dumps({'file':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
if __name__=='__main__':
 owned();op=sys.argv[1]
 if op=='prepare':prepare(sys.argv[2],sys.argv[3])
 elif op=='save':save(sys.argv[2],sys.argv[3])
 elif op=='recover':
  raw_panel();identifier='Lưu bản sao đúng byte gói gốc';find_control(identifier);capture(sys.argv[2]+'-unknown-retained');tap94(identifier);time.sleep(.6);capture(sys.argv[2]+'-recovery-picker')
 elif op=='cancel':adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.5);capture(sys.argv[2]+'-cancelled')
 else:raise AssertionError('OP')
