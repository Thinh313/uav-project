"""Contractor-selected bounded manual gestures on actual owned Android UI only."""
from pathlib import Path
import subprocess,json,time,urllib.request
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';PYTHON='/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';REF='evidence/simstability03/visual-fly03/after.png';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
def state():
 with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=2)as r:return json.load(r)
def waitfor(test,seconds):
 end=time.monotonic()+seconds
 while True:
  s=state()
  if test(s):return s
  if time.monotonic()>end:raise RuntimeError('OBSERVED_MANUAL_STATE_NOT_READY_NO_RETRY')
  time.sleep(.05)
def record(name,s):(E/(name+'.json')).open('x').write(json.dumps(s,indent=2))
def step(tag,*args):
 with(E/(tag+'-console.json')).open('x')as f:subprocess.run([PYTHON,'-B',str(R/'planning/simstability03/ui-visual.py'),tag,*map(str,args)],cwd=R,stdout=f,check=True)
def claim(tag):
 s=state();assert s['vehicle']['armed']and s['vehicle']['mode']=='GUIDED'and not s['input']['active']and s['remainingHostSeconds']>60
 step(tag,'tap',640,254,REF,539,231,741,277,'--fresh-heartbeat');s=waitfor(lambda s:s['input']['active']and s['vehicle']['mode']=='LOITER',5);record(tag+'-active',s)
claim('claim03-pitch');step('pitch03','stick',1023,420,1175,573,0,-.07,650);s=waitfor(lambda s:not s['input']['active']and s['vehicle']['mode']=='GUIDED',7);record('pitch03-released',s)
claim('claim03-yaw');step('yaw03','stick',124,420,278,573,.07,0,650);s=waitfor(lambda s:not s['input']['active']and s['vehicle']['mode']=='GUIDED',7);record('yaw03-released',s)
claim('claim03-background');record('background03-before',state());subprocess.run([ADB,'-s','emulator-5582','shell','input','keyevent','HOME'],check=True,capture_output=True);s=waitfor(lambda s:not s['input']['active']and s['vehicle']['mode']=='GUIDED',7);record('background03-revoked',s)
print({'run':s['run'],'mode':s['vehicle']['mode'],'armed':s['vehicle']['armed'],'position':s['physics']['position'],'authorityActive':s['input']['active'],'remaining':s['remainingHostSeconds']})
