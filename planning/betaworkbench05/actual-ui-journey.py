"""Actual ADB taps grounded in fresh read-only DOM receipts. No control HTTP/eval."""
from pathlib import Path
import urllib.request,json,time,subprocess,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/betaworkbench05';A='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';BASE='http://127.0.0.1:8896';step=0
def get(route):
 with urllib.request.urlopen(BASE+route,timeout=5)as r:return json.load(r)
def state():return get('/api/state')['result']
def adb(*args):
 p=subprocess.run([A,'-s','emulator-5582',*map(str,args)],capture_output=True,timeout=15);assert p.returncode==0,p.stderr;return p.stdout
def log(kind,data):
 with(E/'actual-ui-journey01.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'kind':kind,'data':data})+'\n');f.flush()
def wait(fn,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  s=state()
  if fn(s):return s
  time.sleep(.2)
 raise RuntimeError('OBSERVED_STATE_DEADLINE')
def obs():
 
 end=time.monotonic()+6
 while True:
  q=get('/api/ui-observation')
  if q['ageMs']is not None and q['ageMs']<2000:break
  assert time.monotonic()<end,'UI_OBSERVATION_STALE';time.sleep(.2)
 v=q['observation'];assert v['foreground']and v['platform']=='ANDROID'and v['viewport']=={'w':1280,'h':716};return v
def tap(name):
 global step
 for _ in range(6):
  v=obs();c=v['controls'].get(name);assert c is not None,'MISSING_UI_'+name
  if c['visible']:break
  y1,y2=(550,260)if c['y']>380 else(260,550);adb('shell','input','swipe',1010,y1,1010,y2,500);time.sleep(1)
 else:raise RuntimeError('CONTROL_NOT_VISIBLE_'+name)
 assert c['enabled'],'DISABLED_'+name
 step+=1;image='actual-ui-%03d-%s.png'%(step,name);(E/image).open('xb').write(adb('exec-out','screencap','-p'));log('VISIBLE_TAP_INTENT',{'name':name,'document':v['instance'],'control':c,'screenshot':image});adb('shell','input','tap',round(c['x']),round(c['y']+24));time.sleep(.55)
def check(name):
 if not obs()['controls'][name]['checked']:tap(name)
def prepare():
 tap('nav-preflight')
 # Native data restored without flight authority. Workflow consent is per-model.
 for _ in range(5):
  v=obs()
  if 'consent'in v['controls']:break
  time.sleep(.5)
 if 'reconnect'in v['controls']and v['controls']['reconnect']['enabled']:tap('reconnect')
 check('consent');tap('approve');time.sleep(.5)
def connect():
 if obs()['controls']['b-activate']['enabled']:tap('b-activate')
 check('b-home');tap('b-connect');return wait(lambda s:s['flight']['run']is not None,110)
def nominal():
 prepare();s=connect();log('OWNED_CONNECTED',{'run':s['flight']['run'],'source':s['flight']['source']});assert s['flight']['source']=='OBSERVED_OWNED_SITL'
 tap('video-start');time.sleep(2);tap('video-measure')
 tap('b-preflight');wait(lambda s:s['flight']['preflight']['ready']);tap('b-grant');wait(lambda s:s['flight']['authority']is not None);tap('b-upload');wait(lambda s:s['flight']['live']['readback63']);tap('b-arm');s=wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW')
 v=obs();h=s['flight']['homeReview'];assert h['sha256'][:10]in(v['homeText']or'');log('AUTOMATED_SIM_HOME_REVIEW',{'shown':v['homeText'],'reviewSha256':h['sha256'],'scope':'AUTOMATED_QA_NOT_HUMAN_OR_HERA_APPROVAL'});check('b-home-after');tap('b-auto');wait(lambda s:s['flight']['live']['stage']=='AUTO');log('AUTO_OBSERVED',{'run':s['flight']['run']})
 tap('b-discover');tap('b-select');tap('b-payload-grant');tap('b-gimbal');tap('video-capture');wait(lambda s:len(s['captures'])>0)
 wait(lambda s:s['flight']['completion']['complete'],150)
 end=time.monotonic()+40
 while not obs()['controls']['video-save']['enabled']:
  assert time.monotonic()<end,'VIDEO_REPORT_NOT_READY';time.sleep(.5)
 tap('video-save');tap('b-close');wait(lambda s:len(s['reviews'])>0);log('NOMINAL_REVIEW',state()['reviews'][-1]);print('NOMINAL_UI_COMPLETE',flush=True)
if __name__=='__main__':
 try:
  if sys.argv[1]=='nominal':nominal()
  else:tap(sys.argv[1])
 except BaseException as e:log('FAILURE',{'error':str(e)});raise
