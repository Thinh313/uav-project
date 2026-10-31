import sys,time,json,urllib.request,subprocess,os
from pathlib import Path
from android_qa import adb,capture,E
TOKEN=Path('.local/native83/bridge-token').read_text();log=(E/'android83-fault-driver.jsonl').open('x')
def note(k,d):log.write(json.dumps({'at':time.time(),'kind':k,'data':d})+'\n');log.flush();os.fsync(log.fileno())
def state():return json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8846/state',data=b'{"observe":true}',headers={'Authorization':'Bearer '+TOKEN}),timeout=5))
def until(fn,timeout=15):
 end=time.monotonic()+timeout
 while True:
  s=state()
  if fn(s):return s
  assert time.monotonic()<end,'OBSERVATION_DEADLINE';time.sleep(.15)
def tap(x,y):adb('shell','input','tap',x,y);note('UI_TAP',{'x':x,'y':y})
def setup():
 tap(447,185);time.sleep(.2);tap(206,327);s=until(lambda s:s['live'] is not None);run=s['run'];note('NEW_READONLY_RUN',{'run':run,'session':s['live']['sessionId'],'boot':s['live']['boot']});until(lambda s:all(x['pass']for x in s['live']['preflight']if x['id']!='configuration'),75)
 before=len((E/'runs'/run/'raw.jsonl').read_text().splitlines());tap(346,327);s=until(lambda s:not s['busy']and s['live']['preflight63']['ready'],8);time.sleep(.2);tap(512,327);s=until(lambda s:s['grant'],5);return s
results=[]
try:
 s=setup();run=s['run'];beforePID=adb('shell','pidof','vn.rtr.aeris.native83').decode().strip();capture('android83-fault-before-native-restart');adb('shell','am','force-stop','vn.rtr.aeris.native83');adb('shell','am','start','-W','-n','vn.rtr.aeris.native83/.ShellActivity','--es','bridgeToken',TOKEN);s=until(lambda s:not s['grant']and s['live']['failure']is not None);afterPID=adb('shell','pidof','vn.rtr.aeris.native83').decode().strip();assert beforePID!=afterPID;results.append({'scenario':'NATIVE_PROCESS_RESTART','run':run,'beforePID':beforePID,'afterPID':afterPID,'grant':s['grant'],'failure':s['live']['failure'],'epoch':s['epoch']});note('REVOKED_RESTART',results[-1]);tap(52,600);time.sleep(.2);tap(446,185);time.sleep(.2);capture('android83-native-restart-revoked');tap(635,383);until(lambda s:s['live']is None,30)
 # Same final app, explicit new readonly session. No ARM/AUTO commands are issued.
 s=setup();run=s['run'];launch=json.loads((E/'runs'/run/'launch.json').read_text());i=json.loads(subprocess.check_output(['docker','inspect','aeris-native83'],text=True))[0];assert i['Id']==launch['containerId']and i['State']['Pid']==launch['pid']and i['Config']['Labels']['aeris.run']==run;note('OWNED_REBOOT_BEFORE',{'cid':i['Id'],'pid':i['State']['Pid'],'startedAt':i['State']['StartedAt']});(E/'fault-reboot-before.json').open('x').write(json.dumps(i,indent=2));subprocess.run(['docker','restart','-t','3','aeris-native83'],check=True,capture_output=True,timeout=20);j=json.loads(subprocess.check_output(['docker','inspect','aeris-native83'],text=True))[0];assert j['Id']==i['Id']and j['State']['Pid']!=i['State']['Pid']and j['State']['StartedAt']!=i['State']['StartedAt'];(E/'fault-reboot-after.json').open('x').write(json.dumps(j,indent=2));s=until(lambda s:not s['grant']and bool(s['live']['failure']),8);results.append({'scenario':'OWNED_AP_REBOOT_SOCKET_LOSS','run':run,'beforePid':i['State']['Pid'],'afterPid':j['State']['Pid'],'grant':s['grant'],'failure':s['live']['failure'],'transport':s['live']['transport']});capture('android83-owned-ap-reboot-revoked');note('REVOKED_REBOOT',results[-1]);tap(635,383);until(lambda s:s['live']is None,30)
 (E/'android83-fault-results.json').open('x').write(json.dumps({'status':'PASS_DISARMED_ACTUAL_LIFECYCLE','results':results,'scope':'Owned simulator and Android process restart; no physical or in-flight failsafe claim'},indent=2));print('PASS_DISARMED_ACTUAL_LIFECYCLE',flush=True)
except BaseException as ex:(E/'android83-fault-failure.json').open('x').write(json.dumps({'error':str(ex),'completed':results}));note('FAIL',{'error':str(ex),'noTransactionRetry':True});raise
finally:log.close()
