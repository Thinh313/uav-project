"""Root visually reviews a fresh Android screenshot, then one touch + durable native row barrier. No retry."""
from android_qa import *
import base64,threading
owned();run,label,image,x,y,kind=sys.argv[1:];assert re.fullmatch('s[a-f0-9]{20}',run) and re.fullmatch('[a-z0-9-]+',label);x=int(x);y=int(y);assert 0<=x<1280 and 0<=y<800;picture=E/image;assert picture.is_file() and picture.suffix=='.png' and 0<=time.time()-picture.stat().st_mtime<60,'FRESH_VISUALLY_REVIEWED_SCREENSHOT_REQUIRED';out=E/'runs'/run/('manual-'+label+'.json');assert not out.exists();assert kind in ['PREFLIGHT','EXPLICIT_GRANT','READBACK_VERIFIED','POST_ARM_HOME_REVIEW_REQUIRED','AUTO_OBSERVED'];path='/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl';tip=json.loads(adb('exec-out','tail','-n','1',path));assert tip['kind']not in ['CLOSED','FLIGHT_DOMAIN_FAILURE01'];floor=tip['n'];events=[];errors=[];last=0
p=subprocess.Popen([ADB,'-s',S,'exec-out','tail','-n','+1','-f',path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def consume():
 global last
 try:
  for line in p.stdout:
   r=json.loads(line);last=r['n']
   if r['n']>floor and r['kind']in[kind,'CLOSED','FLIGHT_DOMAIN_FAILURE01']:events.append({'row':r,'data':json.loads(base64.b64decode(r['dataBase64']))})
 except Exception as ex:errors.append(repr(ex))
t=threading.Thread(target=consume,daemon=True);t.start();q={'run':run,'label':label,'screenshot':str(picture),'screenshotSHA256':hashlib.sha256(picture.read_bytes()).hexdigest(),'visualReview':'Root agent fresh screenshot inspected, enabled control and exact coordinates','tap':[x,y],'barrierN':floor,'expectedKind':kind,'automaticRetry':False,'error':None}
try:
 end=time.monotonic()+4
 while last<floor:assert not errors and time.monotonic()<end,'PASSIVE_TAIL_NOT_CAUGHT_UP';time.sleep(.01)
 q['intentHostMonoNs']=str(time.monotonic_ns());adb('shell','input','tap',x,y);end=time.monotonic()+12
 while True:
  assert not errors,errors
  bad=[e for e in events if e['row']['kind'] in ['CLOSED','FLIGHT_DOMAIN_FAILURE01']];assert not bad,bad
  hits=[e for e in events if e['row']['kind']==kind]
  if hits:q['result']=hits[0];break
  assert time.monotonic()<end,'FRESH_EVENT_DEADLINE_NO_RETRY';time.sleep(.02)
 if kind=='PREFLIGHT':assert q['result']['data']['assessment']['state']=='READY_SCOPED_READONLY',q['result']
 if kind=='READBACK_VERIFIED':assert q['result']['data']['matches'],q['result']
 print(json.dumps({'label':label,'kind':kind,'row':q['result']['row']['n'],'status':'OBSERVED_NEW_EVENT','assessment':q['result']['data'].get('assessment',{}).get('state')}))
except BaseException as ex:q['error']=repr(ex);raise
finally:
 p.terminate();p.wait(timeout=3);t.join(1);q['events']=events;q['readerErrors']=errors;out.open('x').write(json.dumps(q,indent=2)+'\n')
