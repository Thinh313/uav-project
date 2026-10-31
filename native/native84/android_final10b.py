import sys,time,json,urllib.request,os,subprocess
from pathlib import Path
from android_resume02_qa import adb,capture,journal,E
TOKEN=Path('.local/native84/bridge-token').read_text();log=(E/'android84-loss-restart-driver10b.jsonl').open('x')
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
 adb('reverse','tcp:8847','tcp:8847');assert state()['live'] is None;tap(1163,758);time.sleep(.5);tap(206,327);until(lambda s:s['live'] is not None,45);before=until(lambda s:s['live']['position'] is not None and s['live']['gps'] is not None and s['live']['gps']['fix']>=3 and s['live']['home'] is not None,40);run=before['run'];assert before['live']['armed'] is False;tap(1113,129);tap(52,166);time.sleep(1);launch=json.loads((E/'runs'/run/'launch.json').read_text());owned=json.loads(subprocess.check_output(['docker','inspect','aeris-native84'],text=True))[0];assert owned['Id']==launch['containerId']and owned['State']['Pid']==launch['pid']and owned['State']['Running']and owned['Config']['Labels']['aeris.run']==run
 capture('android84-before-mavlink-loss10');(E/'owned-before-pause10.json').open('x').write(json.dumps(owned,indent=2));subprocess.run(['docker','pause',owned['Id']],check=True,capture_output=True,timeout=10);note('PAUSE_EXACT_DISARMED_SIMULATOR',{'containerId':owned['Id'],'run':run,'armed':False})
 try:
  s=until(lambda s:not s['grant']and bool(s['live']['failure']),10);time.sleep(1.5);capture('android84-mavlink-loss-hidden10');(E/'mavlink-loss-state10.json').open('x').write(json.dumps(s,indent=2))
 finally:subprocess.run(['docker','unpause',owned['Id']],check=True,capture_output=True,timeout=10)
 time.sleep(1);capture('android84-ap-restored-no-reconnect10');assert state()['live']['failure'];tap(1163,758);time.sleep(.5);tap(635,383);s=until(lambda s:s['live'] is None and s['review']['run']==run,30);assert s['review']['aborted']and not s['review']['accepted'];time.sleep(.5);tap(1113,129);tap(52,364);time.sleep(1);tap(270,270);time.sleep(.7);capture('android84-history-aborted10');tap(270,462);time.sleep(.7);capture('android84-history-completed10');a=journal('android84-before-restart10');pid=adb('shell','pidof','vn.rtr.aeris.native84').decode().strip();adb('shell','am','force-stop','vn.rtr.aeris.native84');adb('shell','am','start','-W','-n','vn.rtr.aeris.native84/.ShellActivity','--es','bridgeToken',TOKEN);time.sleep(2);b=journal('android84-after-restart10');pid2=adb('shell','pidof','vn.rtr.aeris.native84').decode().strip();assert pid!=pid2 and a['files']==b['files'];assert not state()['grant']and state()['live']is None;tap(52,166);time.sleep(.5);capture('android84-after-restart10-no-authority09');tap(52,364);time.sleep(.7);tap(270,462);time.sleep(.7);capture('android84-after-restart10-history09');
 # Cold Android reboot; host bridge is idle, no active aircraft or flight command.
 previousBoot=adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip();adb('reboot');time.sleep(3);end=time.monotonic()+90
 while True:
  try:
   if adb('shell','getprop','sys.boot_completed',timeout=3).strip()==b'1':break
  except Exception:pass
  assert time.monotonic()<end,'COLD_BOOT_DEADLINE';time.sleep(1)
 assert adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip()!=previousBoot;adb('root');time.sleep(1);adb('wait-for-device',timeout=10);adb('shell','am','start','-W','-n','vn.rtr.aeris.native84/.ShellActivity');time.sleep(2);c=journal('android84-after-cold-reboot10');assert a['files']==c['files'];tap(52,166);time.sleep(.5);capture('android84-cold-no-token10');tap(52,364);time.sleep(.8);tap(270,462);time.sleep(.8);capture('android84-cold-history10');reason=adb('shell','getprop','sys.boot.reason').decode().strip();note('COLD_RESTART',{'reason':reason,'identicalFiles':len(a['files'])});
 (E/'android84-loss-restart-result10b.json').open('x').write(json.dumps({'status':'PASS_ACTUAL_ANDROID_LOSS_HISTORY_RESTART','faultRun':run,'faultReview':s['review'],'cut':'Pause exact owned disarmed ArduPilot container; genuine MAVLink telemetry gap','beforePosition':before['live']['position'],'appPidBefore':pid,'appPidAfter':pid2,'identicalJournalFiles':len(a['files']),'coldBootReason':reason,'authorityRestored':False,'historyReadOfflineWithoutToken':True,'inFlightFailsafe':'NOT_CHECKED_DISARMED_ONLY'},indent=2));print('PASS_ACTUAL_ANDROID_LOSS_HISTORY_RESTART',flush=True)
except BaseException as ex:
 (E/'android84-loss-restart-failure10b.json').open('x').write(json.dumps({'error':str(ex),'noAutomaticFlightRetry':True}));note('FAIL',{'error':str(ex)});raise
finally:log.close()
