from ui97 import *
RUN=sys.argv[1]if len(sys.argv)>1 and sys.argv[1].startswith('s')else None
def raw98(run):return adb('exec-out','cat','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl')
def rows98(run):return[json.loads(l)for l in raw98(run).splitlines()]
def events98(run,kind):return[(r,json.loads(base64.b64decode(r['dataBase64'])))for r in rows98(run)if r['kind']==kind]
def state98(run):return events98(run,'PAYLOAD_STATE')[-1][1]
def wait98(run,kind,pred=lambda x:True,seconds=12):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  events=events98(run,kind)
  if events and pred(events[-1][1]):return events[-1]
  closed=events98(run,'CLOSED')
  if closed:raise AssertionError('NATIVE_CLOSED:'+str(closed[-1][1]))
  time.sleep(.15)
 raise AssertionError('EVENT_DEADLINE:'+kind)
def tap98(identifier,scroll='up'):
 for _ in range(7):
  c=[x for x in last()['controls']if x['id']==identifier and not x['covered']and not x['disabled']]
  if c:
   x=c[0];adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));time.sleep(.2);return
  swipe94(scroll)
 raise AssertionError('NOT_VISIBLE:'+identifier)
def workspace98():
 adb('shell','input','tap',52,537);time.sleep(.2);tap94('Workspace')
