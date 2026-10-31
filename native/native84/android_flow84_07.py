"""Actual taps only for operations. Host polling observes without renewing foreground."""
import sys,time,json,urllib.request,os
from pathlib import Path
from android_qa import adb,capture,E
TOKEN=Path('.local/native84/bridge-token').read_text();log=(E/'android84-mission-driver07.jsonl').open('x');run=None
def state():return json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8847/state',data=b'{"observe":true}',headers={'Authorization':'Bearer '+TOKEN}),timeout=5))
def note(k,d):log.write(json.dumps({'at':time.time(),'kind':k,'data':d})+'\n');log.flush();os.fsync(log.fileno())
def tap(x,y):adb('shell','input','tap',x,y);note('UI_TAP',{'x':x,'y':y})
def until(fn,seconds=12):
 end=time.monotonic()+seconds
 while True:
  s=state()
  if fn(s):return s
  assert time.monotonic()<end,'OBSERVE_DEADLINE';time.sleep(.2)
def action(name,x,y):
 rows=lambda:[json.loads(x)for x in(E/'runs'/run/'raw.jsonl').read_text().splitlines()];prior=rows()[-1]['n'];tap(x,y);end=time.monotonic()+15
 while True:
  outcomes=[r for r in rows()if r['n']>prior and r['kind']in ['NATIVE_OUTCOME','NATIVE_REJECTED_OR_UNKNOWN']and r['data'].get('action')==name]
  if outcomes:
   note('OBSERVED_OUTCOME',outcomes[-1]);assert outcomes[-1]['kind']=='NATIVE_OUTCOME',outcomes[-1];time.sleep(.15);return state()
  assert time.monotonic()<end,'ACTION_DEADLINE_'+name;time.sleep(.1)
try:
 assert state()['live']is None and state()['plan'];tap(207,327);s=until(lambda s:s['live']is not None,45);run=s['run'];note('READONLY_SESSION',{'run':run,'session':s['live']['sessionId'],'boot':s['live']['boot']});until(lambda s:s['live']['position']is not None,8);tap(1113,129);time.sleep(1.2);capture('android84-readonly-fly07');(E/'android84-readonly-state07.json').open('x').write(json.dumps(state(),indent=2));
 s=until(lambda s:all(x['pass']for x in s['live']['preflight']if x['id']!='configuration'),75)
 tap(1163,758);time.sleep(.7);s=action('preflight',347,327);assert s['live']['preflight63']['ready'];(E/'readonly-prefix07.jsonl').open('xb').write((E/'runs'/run/'raw.jsonl').read_bytes());capture('android84-preflight07');s=action('grant',512,327);assert s['grant'];s=action('upload',713,327);assert s['live']['readback63']['matches'];capture('android84-readback07');s=action('arm',861,327);assert s['live']['stage']=='ARMED_HOME_REVIEW';capture('android84-home-after-arm07');s=action('auto',252,383);assert s['live']['completion']['autoObserved'];tap(1113,129);time.sleep(.8);capture('android84-auto-main-fly07');started=time.monotonic();captured=set();observed=[]
 while True:
  s=state();assert not s['live']['failure'],s['live']['failure'];elapsed=time.monotonic()-started
  observed.append({'elapsed':elapsed,'presentation84':s['presentation84'],'live':{k:s['live'].get(k)for k in['position','home','attitude','mode','armed','completion','heartbeatAgeMs']}})
  for t in[10,25,40]:
   if elapsed>=t and t not in captured:capture('android84-auto-main-'+str(t)+'s07');captured.add(t)
  if s['live']['completion']['complete']:break
  assert elapsed<180,'AUTO_DEADLINE';time.sleep(.5)
 capture('android84-main-landed07');(E/'android84-display-observations07.json').open('x').write(json.dumps(observed,indent=2));tap(1163,758);time.sleep(.5);tap(455,383);s=until(lambda s:s['review']is not None and s['live']is None,30);assert s['review']['accepted'];time.sleep(.8);capture('android84-closed-review07');tap(1113,129);tap(52,364);time.sleep(1);capture('android84-history-list07');tap(270,270);time.sleep(1);capture('android84-history-selected07');
 (E/'android84-mission-result07.json').open('x').write(json.dumps({'status':'PASS_ACTUAL_ANDROID_UI_AUTO_SITL','run':run,'review':s['review'],'actualImages':0},indent=2));print('PASS_ACTUAL_ANDROID_UI_AUTO_SITL '+run,flush=True)
except BaseException as ex:
 note('FAIL',{'error':str(ex),'noAutomaticTransactionRetry':True});(E/'android84-mission-failure07.json').open('x').write(json.dumps({'run':run,'error':str(ex),'status':'NOT_ACCEPTED'}));raise
finally:log.close()
