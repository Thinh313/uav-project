"""One deliberate UI sequence after Contractor Home/reference checks. No flight HTTP."""
from pathlib import Path
import json,urllib.request,time,subprocess,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';PYTHON='/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';tag=sys.argv[1]; expectedMode=sys.argv[2]if len(sys.argv)>2 else'LOITER';assert expectedMode in['LOITER','GUIDED']
def state():
 with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=2)as r:return json.load(r)
def waitfor(test,seconds):
 end=time.monotonic()+seconds
 while True:
  s=state()
  if test(s):return s
  if time.monotonic()>end:raise RuntimeError('OBSERVED_STATE_NOT_READY_NO_NEXT_UI_ACTION')
  time.sleep(.1)
def tap(name,x,y,ref,box):
 with(E/(name+'-console.json')).open('x')as f:subprocess.run([PYTHON,'-B',str(R/'planning/simstability03/ui-visual.py'),name,'tap',str(x),str(y),ref,*map(str,box),'--fresh-heartbeat'],cwd=R,stdout=f,check=True)
s=state();assert s['lifecycle']['phase']=='ACTIVE'and not s['vehicle']['armed']and s['remainingHostSeconds']>100
assert s['vehicle']['home']and s['vehicle']['home']['horizontalDeltaM']<1 and s['vehicle']['home']['amslDeltaM']<.5
# References are actual Contractor-inspected enabled controls at the same fixed viewport.
tap(tag+'-refresh',201,247,'evidence/simstability03/visual-scroll02/after.png',[130,224,272,270]);waitfor(lambda s:s['preflight']['ready'],4)
tap(tag+'-approve',285,433,'evidence/simstability03/visual-refresh03/after.png',[129,409,443,457]);waitfor(lambda s:bool(s['approvalId']),4);time.sleep(.3)
tap(tag+'-takeoff',285,495,'evidence/simstability03/visual-approve03/after.png',[130,472,442,518]);s=waitfor(lambda s:(s.get('vehicle')or{}).get('armed')and(s.get('vehicle')or{}).get('mode')==expectedMode and -(s.get('physics')or{}).get('position',[0,0,0])[2]>4.5,50)
(E/(tag+'-airborne.json')).open('x').write(json.dumps(s,indent=2));print({'run':s['run'],'mode':s['vehicle']['mode'],'armed':s['vehicle']['armed'],'position':s['physics']['position'],'remaining':s['remainingHostSeconds']})
