import sys,time,json,urllib.request,os
from pathlib import Path
from android_qa import adb,capture,journal,E
TOKEN=Path('.local/native84/bridge-token').read_text();log=(E/'android84-loss-restart-driver.jsonl').open('x')
def state():return json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8847/state',data=b'{"observe":true}',headers={'Authorization':'Bearer '+TOKEN}),timeout=5))
def note(k,d):log.write(json.dumps({'at':time.time(),'kind':k,'data':d})+'\n');log.flush();os.fsync(log.fileno())
def tap(x,y):adb('shell','input','tap',x,y);note('UI_TAP',{'x':x,'y':y})
def until(fn,seconds=15):
 end=time.monotonic()+seconds
 while True:
  s=state()
  if fn(s):return s
  assert time.monotonic()<end,'OBSERVE_DEADLINE';time.sleep(.2)
try:
 assert state()['live']is None;tap(1163,758);time.sleep(.5);tap(206,327);s=until(lambda s:s['live']is not None,45);run=s['run'];note('NEW_READONLY',{'run':run});s=until(lambda s:s['live']['position']is not None and s['live']['gps']is not None and s['live']['gps']['fix']>=3 and s['live']['home']is not None,40);tap(1113,129);tap(52,166);time.sleep(1.5);capture('android84-before-bridge-loss09');before=state();adb('reverse','--remove','tcp:8847');note('CUT_ONLY_OWNED_ADB_REVERSE',{});s=until(lambda s:not s['grant']and bool(s['live']['failure']),10);time.sleep(2);capture('android84-bridge-loss-hidden09');adb('reverse','tcp:8847','tcp:8847');time.sleep(1.5);capture('android84-restored-no-reconnect09');assert state()['live']['failure'];tap(1163,758);time.sleep(.5);tap(635,383);s=until(lambda s:s['live']is None and s['review']['run']==run,30);assert s['review']['aborted']and not s['review']['accepted'];time.sleep(.5);tap(1113,129);tap(52,364);time.sleep(1);tap(270,270);time.sleep(.7);capture('android84-history-aborted09');tap(270,365);time.sleep(.7);capture('android84-history-completed09');a=journal('android84-before-restart');pid=adb('shell','pidof','vn.rtr.aeris.native84').decode().strip();adb('shell','am','force-stop','vn.rtr.aeris.native84');adb('shell','am','start','-W','-n','vn.rtr.aeris.native84/.ShellActivity','--es','bridgeToken',TOKEN);time.sleep(2);b=journal('android84-after-restart');pid2=adb('shell','pidof','vn.rtr.aeris.native84').decode().strip();assert pid!=pid2 and a['files']==b['files'];assert not state()['grant']and state()['live']is None;tap(52,166);time.sleep(.5);capture('android84-after-restart-no-authority09');tap(52,364);time.sleep(.7);tap(270,365);time.sleep(.7);capture('android84-after-restart-history09');
 # Cold Android reboot; host bridge is idle, no active aircraft or flight command.
 adb('shell','reboot');time.sleep(3);end=time.monotonic()+90
 while True:
  try:
   if adb('shell','getprop','sys.boot_completed',timeout=3).strip()==b'1':break
  except Exception:pass
  assert time.monotonic()<end,'COLD_BOOT_DEADLINE';time.sleep(1)
 adb('root');time.sleep(1);adb('wait-for-device',timeout=10);adb('shell','am','start','-W','-n','vn.rtr.aeris.native84/.ShellActivity');time.sleep(2);c=journal('android84-after-cold-reboot');assert a['files']==c['files'];tap(52,166);time.sleep(.5);capture('android84-cold-no-token09');tap(52,364);time.sleep(.8);tap(270,365);time.sleep(.8);capture('android84-cold-history09');reason=adb('shell','getprop','sys.boot.reason').decode().strip();note('COLD_RESTART',{'reason':reason,'identicalFiles':len(a['files'])});
 (E/'android84-loss-restart-result.json').open('x').write(json.dumps({'status':'PASS_ACTUAL_ANDROID_LOSS_HISTORY_RESTART','faultRun':run,'faultReview':s['review'],'cut':'Only owned adb reverse 8847','beforePosition':before['live']['position'],'appPidBefore':pid,'appPidAfter':pid2,'identicalJournalFiles':len(a['files']),'coldBootReason':reason,'authorityRestored':False,'historyReadOfflineWithoutToken':True,'inFlightFailsafe':'NOT_CHECKED_DISARMED_ONLY'},indent=2));print('PASS_ACTUAL_ANDROID_LOSS_HISTORY_RESTART',flush=True)
except BaseException as ex:
 (E/'android84-loss-restart-failure.json').open('x').write(json.dumps({'error':str(ex),'noAutomaticFlightRetry':True}));note('FAIL',{'error':str(ex)});raise
finally:log.close()
