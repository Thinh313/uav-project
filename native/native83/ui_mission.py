import sys,time,json,urllib.request
from pathlib import Path
from android_qa import adb,capture,E
TOKEN=Path('.local/native83/bridge-token').read_text();log=(E/'android83-mission-driver02.jsonl').open('x');run=None
# Read-only observation. All mission operations below are actual touchscreen taps.
def state():return json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8846/state',data=b'{"observe":true}',headers={'Authorization':'Bearer '+TOKEN}),timeout=5))
def note(kind,data):log.write(json.dumps({'at':time.time(),'kind':kind,'data':data})+'\n');log.flush();__import__('os').fsync(log.fileno())
def rows():return[json.loads(x)for x in(E/'runs'/run/'raw.jsonl').read_text().splitlines()]
def tapaction(action,x,y,timeout=12):
 prior=rows()[-1]['n'];note('UI_TAP',{'action':action,'x':x,'y':y,'afterRawRecord':prior});adb('shell','input','tap',x,y);end=time.monotonic()+timeout
 while True:
  recent=[r for r in rows()if r['n']>prior and r['kind']in['NATIVE_OUTCOME','NATIVE_REJECTED_OR_UNKNOWN']and r['data'].get('action')==action]
  if recent:
   r=recent[-1];note('OBSERVED_OUTCOME',r);assert r['kind']=='NATIVE_OUTCOME',r;time.sleep(.2);return state()
  assert time.monotonic()<end,'UI_ACTION_DEADLINE_'+action;time.sleep(.1)
try:
 s=state();run=s['run'];assert run and not s['live']['failure'];end=time.monotonic()+75
 while not all(x['pass'] for x in s['live']['preflight']if x['id']!='configuration'):
  assert time.monotonic()<end,'READONLY_HEALTH_WAIT';time.sleep(.5);s=state()
 s=tapaction('preflight',347,327);assert s['live']['preflight63']['ready'],s['live']['preflight63'];(E/'android83-qualified-readonly02.json').open('x').write(json.dumps(s,indent=2));(E/'readonly-prefix02.jsonl').open('xb').write((E/'runs'/run/'raw.jsonl').read_bytes());capture('android83-qualified-readonly02');s=tapaction('grant',512,327);assert s['grant'];s=tapaction('upload',713,327);assert s['live']['readback63']['matches'];capture('android83-upload-readback02');s=tapaction('arm',861,327);assert s['live']['stage']=='ARMED_HOME_REVIEW';capture('android83-post-arm-home02');s=tapaction('auto',252,383);assert s['live']['completion']['autoObserved'];capture('android83-auto-live02');end=time.monotonic()+180;last=0
 while True:
  s=state();assert not s['live']['failure'],s['live']['failure']
  if s['live']['completion']['complete']:break
  assert time.monotonic()<end,'AUTO_OBSERVATION_DEADLINE'
  if time.monotonic()-last>4:note('OBSERVE',{'position':s['live']['position'],'mode':s['live']['mode'],'armed':s['live']['armed'],'completion':s['live']['completion']});last=time.monotonic()
  time.sleep(.4)
 capture('android83-auto-completed02');adb('shell','input','tap','455','383');end=time.monotonic()+30
 while True:
  s=state()
  if s['review']and s['review']['run']==run and not s['live']:break
  assert time.monotonic()<end,'CLOSURE_DEADLINE';time.sleep(.2)
 assert s['review']['accepted'];(E/'android83-mission-result02.json').open('x').write(json.dumps({'status':'PASS_ACTUAL_ANDROID_UI_AUTO_SITL','run':run,'review':s['review'],'actualImages':0},indent=2));capture('android83-sitl-review02');print('PASS_ACTUAL_ANDROID_UI_AUTO_SITL '+run,flush=True)
except BaseException as ex:
 note('FAIL',{'error':str(ex),'noAutomaticTransactionRetry':True});(E/'android83-mission-failure02.json').open('x').write(json.dumps({'run':run,'error':str(ex),'status':'NOT_ACCEPTED'}));raise
finally:log.close()
