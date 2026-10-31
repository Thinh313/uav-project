"""Short native UI qualification: every action is explicit, observed, non-retried.
GET observes actual gateway only. Mutations traverse the owned Android UI.
"""
from pathlib import Path
from PIL import Image
import json,urllib.request,time,subprocess,io,re
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';PYTHON='/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
def state():
 with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=2)as r:return json.load(r)
def save(n,v):(E/(n+'.json')).open('x').write(json.dumps(v,indent=2))
def waitfor(f,seconds):
 end=time.monotonic()+seconds
 while True:
  s=state()
  if f(s):return s
  assert time.monotonic()<end,'OBSERVATION_DEADLINE_NO_MUTATION_RETRY';time.sleep(.1)
def adb(*args):return subprocess.check_output([ADB,'-s','emulator-5582',*map(str,args)])
def pixels(ref,box,seconds=10):
 with Image.open(R/ref)as old:expected=old.convert('RGBA').crop(box).tobytes()
 end=time.monotonic()+seconds
 while True:
  w=adb('shell','dumpsys','window').decode();assert re.search('mCurrentFocus=.*vn.rtr.aeris.simhand01/',w)
  b=adb('exec-out','screencap','-p');im=Image.open(io.BytesIO(b));assert im.size==(1280,800)
  if im.convert('RGBA').crop(box).tobytes()==expected:return
  assert time.monotonic()<end,'WAIT_PIXELS_NO_ACTION';time.sleep(.2)
def step(n,*args):
 print('UI_STEP',n,flush=True)
 with(E/(n+'-console.json')).open('x')as f:subprocess.run([PYTHON,'-B',str(R/'planning/simstability03/ui-visual.py'),n,*map(str,args)],cwd=R,stdout=f,check=True)
def tap(n,x,y,ref,box,fresh=False):pixels(ref,box);step(n,'tap',x,y,ref,*box,*(['--fresh-heartbeat']if fresh else[]))
try:
 s=state();save('cold-host04-before-start',s);assert not s['controllerActive']and s['session']is None and s['boot']is None and not s['input']['active'];assert s['reviewHistory']and all(r['historyOnly']and not r['authorityRestored']for r in s['reviewHistory'])
 adb('shell','am','force-stop','vn.rtr.aeris.simhand01');adb('shell','am','start','-W','-n','vn.rtr.aeris.simhand01/.ShellActivity','--es','initialPath','/phone')
 tap('auto04-start',285,399,'evidence/simstability03/android-open01/001-after-open.png',[129,375,443,423])
 tap('auto04-pre',61,354,'evidence/simstability03/android-open01/001-after-open.png',[35,328,87,380])
 tap('auto04-reference',141,495,'evidence/simstability03/visual-pre02/after.png',[129,484,152,507]);step('auto04-scroll','scroll',107,166,466,608)
 s=waitfor(lambda s:bool((s.get('vehicle')or{}).get('home'))and bool(s['preflight']['checks'])and all(c['pass']for c in s['preflight']['checks']if c['id']!='configuration'),95);save('auto04-home-observed',s);assert s['vehicle']['home']['horizontalDeltaM']<1 and abs(s['vehicle']['home']['amslDeltaM'])<.5
 tap('auto04-home',141,370,'evidence/simstability03/visual-scroll02/after.png',[129,359,152,382])
 tap('auto04-refresh',201,247,'evidence/simstability03/visual-scroll02/after.png',[130,224,272,270],True);waitfor(lambda s:s['preflight']['ready'],4)
 tap('auto04-approve',285,433,'evidence/simstability03/visual-refresh03/after.png',[129,409,443,457],True);waitfor(lambda s:bool(s['approvalId']),4)
 tap('auto04-takeoff',285,495,'evidence/simstability03/visual-approve03/after.png',[130,472,442,518],True);s=waitfor(lambda s:(s.get('vehicle')or{}).get('armed')and s['vehicle']['mode']=='GUIDED'and-s['physics']['position'][2]>4.5,45);save('auto04-airborne',s)
 tap('auto04-fly',61,411,'evidence/simstability03/visual-scroll02/after.png',[35,384,87,436])
 for name,bounds,dx,dy in [('pitch',(1023,420,1175,573),0,-.07),('yaw',(124,420,278,573),.07,0)]:
  tap('auto04-claim-'+name,640,254,'evidence/simstability03/visual-fly03/after.png',[539,231,741,277],True);s=waitfor(lambda s:s['input']['active']and s['vehicle']['mode']=='LOITER',5);save('auto04-'+name+'-active',s)
  step('auto04-'+name,'stick',*bounds,dx,dy,650);s=waitfor(lambda s:not s['input']['active']and s['vehicle']['mode']=='GUIDED',7);save('auto04-'+name+'-released',s)
 tap('auto04-land',1167,689,'evidence/simstability03/visual-fly02/after.png',[1102,666,1232,712],True);s=waitfor(lambda s:(s.get('vehicle')or{}).get('mode')=='LAND'and s['vehicle']['armed']is False and s['physics']['ground'],45);save('auto04-ground-disarm',s)
 tap('auto04-review',61,467,'evidence/simstability03/visual-fly02/after.png',[35,440,87,492]);step('auto04-reviewscroll','scroll',107,166,466,608);print('READY_FOR_OBSERVED_END',json.dumps({'run':s['run'],'remaining':s['remainingHostSeconds'],'modelSeconds':s['physics']['timestamp']}),flush=True)
except Exception as e:
 try:save('auto04-failure-observation',{'error':repr(e),'state':state()})
 except Exception:pass
 raise
