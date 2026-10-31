"""Three explicit aged-session cohorts, passive raw tail only during collection. No flight commands."""
from ui01 import *
import threading,collections,signal
owned();run=sys.argv[1];events=collections.defaultdict(list);errors=[];lock=threading.Lock();seen=[]
tail=subprocess.Popen([ADB,'-s',S,'exec-out','tail','-n','+1','-f','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def consume():
 try:
  for line in tail.stdout:
   assert len(line)<1048576;r=json.loads(line)
   with lock:
    seen.append((r['n'],r['kind'],r['elapsedMs']))
    if r['kind'] in ['PREFLIGHT','FLIGHT_DOMAIN_FAILURE01','CLOSED']:events[r['kind']].append((r['elapsedMs'],json.loads(base64.b64decode(r['dataBase64']))))
 except Exception as e:errors.append(str(e))
t=threading.Thread(target=consume,daemon=True);t.start();results=[];load=None
try:
 end=time.monotonic()+500
 while True:
  with lock:
   assert not events['CLOSED'] and not events['FLIGHT_DOMAIN_FAILURE01'],'AGED_SESSION_FAILED_NO_RETRY'
   rx=[x for x in seen if x[1]=='RX'];age=(rx[-1][2]-rx[0][2])if len(rx)>1 else 0
  if age>=480000:break
  assert time.monotonic()<end,'AGED_TRAFFIC_DEADLINE';assert not errors;time.sleep(.5)
 for i in range(3):
  c=control01('preflight83');before=len(events['PREFLIGHT'])
  with lock:snapshot={'rawRows':len(seen),'rxRows':len([x for x in seen if x[1]=='RX']),'nativeFirst':rx[0][2],'nativeLast':seen[-1][2]}
  if i==2:
   load=subprocess.Popen([sys.executable,'-B','-c','import time,hashlib;end=time.monotonic()+15;v=b"owned integration03 load"\nwhile time.monotonic()<end:v=hashlib.sha256(v).digest()']);snapshot['ownedLoadPID']=load.pid;snapshot['load']='one CPU SHA256 loop15s, declared engineering load'
  intent=time.monotonic_ns();adb('shell','input','tap',round((c['x']+c['right'])/2),round((c['y']+c['bottom'])/2));deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   with lock:
    if events['CLOSED'] or events['FLIGHT_DOMAIN_FAILURE01']:raise AssertionError('COHORT_FAILED_NO_AUTOMATIC_RETRY:'+str(dict(events)))
    if len(events['PREFLIGHT'])>before:r=events['PREFLIGHT'][-1];break
   assert not errors;time.sleep(.02)
  else:raise AssertionError('COHORT_DEADLINE_NO_RETRY')
  assert r[1]['assessment']['state']=='READY_SCOPED_READONLY',r
  results.append({'trial':i+1,'before':snapshot,'hostIntentNs':str(intent),'preflight':r,'explicitIntent':True,'automaticRetry':False});time.sleep(.5)
 if load:load.wait(timeout=20)
 print('THREE_AGED_COHORTS_READY')
finally:
 if load and load.poll() is None:load.terminate();load.wait(timeout=5)
 tail.terminate();tail.wait(timeout=5);t.join(2)
 (E/'runs'/run/'aged-cohorts.json').open('x').write(json.dumps({'results':results,'errors':errors,'lastEvents':dict(events),'passiveTailOnlyDuringCohort':True,'requiredAgedTrafficMs':480000,'requireIndependentActualFrameCountAbove20000':True},indent=2)+'\n')
