from raw_ui96 import *
import base64
owned();run=sys.argv[2];out=E/'runs'/run
def rows():return[json.loads(l)for l in adb('exec-out','cat','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl').splitlines()]
def events():return{r['kind']:json.loads(base64.b64decode(r['dataBase64']))for r in rows()if r['kind']not in['RX','TX_INTENT','TX_WRITTEN']}
if sys.argv[1]=='cut':
 end=time.monotonic()+35
 while 'TAKEOFF_GEOMETRY_OBSERVED'not in events():assert time.monotonic()<end,'TAKEOFF_WITNESS_DEADLINE';time.sleep(.3)
 adb('shell','input','tap',52,605);time.sleep(.3);x=find_control('cut-native96');capture(run+'-before-link-cut');x=next(x for x in last()['controls']if x['id']=='cut-native96'and not x['disabled']and not x['covered']);(out/'fault-cut-host.json').open('x').write(json.dumps({'beforeTapHostNs':time.monotonic_ns(),'actualUIControl':'cut-native96','coordinates':x,'hostFlightPayloadBytes':0}));adb('shell','input','tap',round((x['x']+x['right'])/2),round((x['y']+x['bottom'])/2));time.sleep(.5);capture(run+'-link-cut');ev=events();assert ev['CLOSED']['reason']=='INJECTED_LINK_LOSS96'and ev['CLOSED']['safeComplete']is False;print('NATIVE_SOCKET_CLOSED_NO_RETRY')
elif sys.argv[1]=='archive':
 assert 'CLOSED'in events();x=find_control('archive-interrupted96');tap94('archive-interrupted96');time.sleep(.5);capture(run+'-interrupted-review-saved');journal(run+'-interrupted-workspace');raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.');(E/(run+'-interrupted-files.tar')).open('xb').write(raw)
 with tarfile.open(fileobj=io.BytesIO(raw))as t:
  b=t.extractfile('./direct95/'+run+'/raw.jsonl').read();(out/'android-raw.jsonl').open('xb').write(b);reviews=[]
  for e in t.getmembers():
   if e.isfile()and'/sitl/'in e.name and e.name.endswith('.bin'):
    r=json.loads(t.extractfile(e).read().split(b'\n',6)[6])
    if r['run']==run:reviews.append(r)
  assert len(reviews)==1;review=reviews[0];assert review['accepted']is False and review['execution']['complete']is False and review['outcome96']=='INTERRUPTED_UNKNOWN_AIRCRAFT_STATE'and review['execution']['groundDisarmed']is False and review['authorityRestorable']is False;(out/'review.json').open('x').write(json.dumps(review,ensure_ascii=False))
 (out/'stop-request.json').open('x').write(json.dumps({'reason':'Unknown interrupted native review retained; runtime controller checks fresh observer ground if ever armed'}));print('UNKNOWN_REVIEW_RETAINED')
else:raise AssertionError('ACTION')
