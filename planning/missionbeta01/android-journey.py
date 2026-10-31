"""Owned emulator5582 only. UI taps from fresh read-only observations, no flight POST/eval."""
from pathlib import Path
import urllib.request,json,time,subprocess,os,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/missionbeta01';A='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';BASE='http://127.0.0.1:8896';step=max([int(q.name.split('-')[1])for q in E.glob('journey-*.png')]+[0])

def get(route):
 with urllib.request.urlopen(BASE+route,timeout=8)as r:return json.load(r)
def state():return get('/api/state')['result']
def adb(*args):
 p=subprocess.run([A,'-s','emulator-5582',*map(str,args)],capture_output=True,timeout=20)
 log('ADB_RESULT',{'args':list(args),'exit':p.returncode,'stderr':p.stderr.decode(errors='replace')[:2000]})
 assert p.returncode==0,p.stderr
 return p.stdout
def log(kind,data):
 with(E/'android-journey01.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'kind':kind,'data':data})+'\n');f.flush();os.fsync(f.fileno())
def wait(fn,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  s=state()
  if fn(s):return s
  time.sleep(.25)
 raise RuntimeError('OBSERVED_STATE_DEADLINE')
def obs():
 end=time.monotonic()+8
 while True:
  q=get('/api/ui-observation')
  if q['ageMs']is not None and q['ageMs']<2000:break
  assert time.monotonic()<end,'UI_OBSERVATION_STALE';time.sleep(.3)
 v=q['observation'];assert v['foreground']and v['platform']=='ANDROID',v
 return v
def shot(label):
 b=adb('exec-out','screencap','-p');p=E/label;p.open('xb').write(b);return str(p.relative_to(R))
def tap(name):
 global step
 for _ in range(10):
  v=obs();c=v['controls'].get(name);assert c is not None,'MISSING_UI_'+name
  if c['visible']:break
  delta=max(-140,min(140,c['y']-350));assert abs(delta)>5,'UI_TARGET_OBSCURED_'+name;adb('shell','input','swipe',1010,450,1010,round(450-delta),300);time.sleep(.8)
 else:raise RuntimeError('CONTROL_NOT_VISIBLE_'+name)
 enabledDeadline=time.monotonic()+5
 while not c['enabled']:
  assert time.monotonic()<enabledDeadline,'DISABLED_'+name;time.sleep(.2);v=obs();c=v['controls'].get(name);assert c is not None,'MISSING_UI_'+name
 stableDeadline=time.monotonic()+6
 while True:
  old=c;oldReceipt=v['receivedMs'];time.sleep(.6);v=obs();c=v['controls'].get(name);assert c is not None,'MISSING_UI_'+name
  if c['visible'] and c['enabled'] and v['receivedMs']>oldReceipt and abs(c['x']-old['x'])<.5 and abs(c['y']-old['y'])<.5:break
  assert time.monotonic()<stableDeadline,'UI_GEOMETRY_NOT_STABLE_'+name
  if not c['visible']:
   delta=max(-120,min(120,c['y']-350));assert abs(delta)>5,'UI_TARGET_OBSCURED_'+name;adb('shell','input','swipe',1010,450,1010,round(450-delta),300);time.sleep(.6)
 step+=1;image=shot('journey-%03d-%s.png'%(step,name));confirmed=obs()['controls'][name];assert confirmed['visible']and confirmed['enabled']and abs(confirmed['x']-c['x'])<.5 and abs(confirmed['y']-c['y'])<.5,'UI_POSITION_CHANGED_NO_TAP';log('VISIBLE_TAP_INTENT',{'name':name,'document':v['instance'],'control':confirmed,'screenshot':image});adb('shell','input','tap',round(confirmed['x']),round(confirmed['y']+24));time.sleep(.75)
def check(name):
 if not obs()['controls'][name]['checked']:tap(name)
def prepare(kind):
 tap('nav-plan');tap('sample-'+kind);check('datum');tap('compile');tap('nav-preflight');v=obs()
 if 'reconnect'in v['controls']and v['controls']['reconnect']['enabled']:tap('reconnect')
 check('consent');tap('approve')
def connect():
 if obs()['controls']['b-activate']['enabled']:tap('b-activate')
 check('b-home');tap('b-connect');return wait(lambda s:s['flight']['run']is not None,115)
def ready():
 # Wait on fresh read-only estimator/pre-arm observations; no parameter change or flight retry.
 wait(lambda s:all(next((c['pass']for c in s['flight']['preflight']['checks']if c['id']==name),False)for name in ['estimator','autopilot-prearm']),100)
 tap('b-preflight');wait(lambda s:not s['busy'],20);s=state();assert s['flight']['preflight']['ready'],'PREFLIGHT_NOT_READY'
 tap('b-grant');wait(lambda s:s['flight']['authority']is not None);tap('b-upload');wait(lambda s:s['flight']['live']['readback63'])
def nominal(kind,index):
 prepare(kind);s=connect();run=s['flight']['run'];log('OWNED_CONNECTED',{'run':run,'source':s['flight']['source'],'kind':kind,'index':index});assert s['flight']['source']=='OBSERVED_OWNED_SITL'
 tap('video-start');time.sleep(1);ready();return finish_connected(kind,index,run)
def finish_connected(kind,index,run):
 tap('video-measure');tap('b-arm');s=wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW');h=s['flight']['homeReview'];uiDeadline=time.monotonic()+4
 while True:
  v=obs()
  if h['sha256'][:10]in(v['homeText']or''):break
  assert time.monotonic()<uiDeadline,'HOME_UI_RECEIPT_NOT_FRESH';time.sleep(.2)
 log('SIMULATED_HOME_REVIEW',{'shown':v['homeText'],'sha256':h['sha256'],'humanOrHeraApproval':False});check('b-home-after');tap('b-auto');wait(lambda s:s['flight']['live']['stage']=='AUTO');wait(lambda s:s['flight']['completion'].get('takeoffEvidence',{}).get('valid') is True,45)
 tap('b-pause');wait(lambda s:s['flight']['live']['stage']=='HOLD');time.sleep(1);tap('b-resume');wait(lambda s:s['flight']['live']['stage']=='AUTO')
 tap('b-discover');tap('b-select');tap('b-payload-grant');tap('b-gimbal');before=len(state()['captures']);tap('video-capture');wait(lambda s:len(s['captures'])>before)
 wait(lambda s:s['flight']['completion']['complete'],180)
 deadline=time.monotonic()+190
 while not obs()['controls']['video-save']['enabled']:
  v=obs();log('VIDEO_WAIT',{'run':run,'video':v.get('video')});assert time.monotonic()<deadline,'VIDEO_REPORT_NOT_READY';time.sleep(3)
 tap('video-save');tap('b-close');s=wait(lambda s:any(r['run']==run for r in s['reviews']));r=next(r for r in s['reviews']if r['run']==run);assert r['accepted'];history=get('/api/history')['result'];assert any(h['run']==run for h in history['reviews']);log('NOMINAL_COMPLETE',{'kind':kind,'index':index,'review':r,'history':history});print('NOMINAL_COMPLETE',kind,index,run,flush=True);return run
if __name__=='__main__':
 try:
  if sys.argv[1]=='snapshot':print(json.dumps(obs(),ensure_ascii=False,indent=2))
  elif sys.argv[1]=='tap':tap(sys.argv[2])
  elif sys.argv[1]=='nominal':nominal(sys.argv[2],int(sys.argv[3]))
 except BaseException as e:log('FAILURE',{'error':repr(e)});raise
