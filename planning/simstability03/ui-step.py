"""One explicitly selected UI action on owned emulator5582. No flight HTTP."""
from pathlib import Path
import sys,json,urllib.request,time
from native_ui import NativeUI
assert len(sys.argv)>=3
tag,action=sys.argv[1:3];assert tag.replace('-','').isalnum()
E=Path(__file__).resolve().parents[2]/'evidence/simstability03'
u=NativeUI(E/('android-'+tag));u.require_owned()
def state():
 with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=5)as r:q=json.load(r)
 (u.out/('state-'+str(time.time_ns())+'.json')).open('x').write(json.dumps(q,indent=2));return q
if action=='open':
 end=time.monotonic()+60
 while True:
  try:state();break
  except Exception:
   assert time.monotonic()<end,'HOST_NOT_READY';time.sleep(.5)
 u.adb('shell','am','force-stop',u.PACKAGE if hasattr(u,'PACKAGE')else'vn.rtr.aeris.simhand01')
 u.adb('shell','am','start','-W','-n','vn.rtr.aeris.simhand01/.ShellActivity','--es','initialPath',sys.argv[3]if len(sys.argv)>3 else'/phone');time.sleep(2)
elif action=='tap':u.tap(sys.argv[3],sys.argv[4]if len(sys.argv)>4 else None);time.sleep(.5)
elif action=='gesture':u.gesture_stick(sys.argv[3],float(sys.argv[4]),float(sys.argv[5]),int(sys.argv[6]));time.sleep(.4)
elif action=='scroll':
 u.snapshot('before-contractor-chosen-panel-scroll');u.scroll_observed(tuple(map(int,sys.argv[3:7])),sys.argv[7]if len(sys.argv)>7 else'up');time.sleep(.3)
elif action=='background':
 u.snapshot('before-explicit-background');u.key('HOME');time.sleep(.6)
elif action=='foreground':
 u.adb('shell','am','start','-W','-n','vn.rtr.aeris.simhand01/.ShellActivity');time.sleep(.7)

elif action=='stable-tap':
 # When WebView exposes no inner AX nodes, act only on a fresh screenshot
 # identical to the Contractor-reviewed app area (exclude Android system bars).
 from PIL import Image
 ref=Path(sys.argv[5]);assert ref.is_file()
 snap=u.snapshot('before-reviewed-stable-tap');fresh=u.out/(snap['stem']+'.png')
 with Image.open(ref)as a,Image.open(fresh)as b:
  assert a.size==b.size,'VIEWPORT_CHANGED'
  box=tuple(map(int,sys.argv[6:10]))if len(sys.argv)==10 else(0,24,a.width,a.height-60)
  assert 0<=box[0]<box[2]<=a.width and 0<=box[1]<box[3]<=a.height,'REVIEW_REGION'
  assert box[0]<=int(sys.argv[3])<box[2]and box[1]<=int(sys.argv[4])<box[3],'TAP_OUTSIDE_REVIEW_REGION'
  assert a.crop(box).tobytes()==b.crop(box).tobytes(),'APP_SCREEN_CHANGED_NO_TAP'
 u.log('REVIEWED_TARGET_PIXELS_IDENTICAL',{'reference':str(ref),'fresh':str(fresh),'verifiedRegion':box})
 u.tap_observed(int(sys.argv[3]),int(sys.argv[4]),snap['stem']);time.sleep(.5)
elif action!='snapshot':raise RuntimeError('UNSUPPORTED_QA_ACTION')
q=u.snapshot('after-'+action);s=state();print(json.dumps({'image':str(u.out/(q['stem']+'.png')),'nodes':[{'text':n.get('text'),'desc':n.get('content-desc'),'id':n.get('resource-id'),'enabled':n.get('enabled'),'bounds':n.get('bounds')}for n in q['root'].iter('node')if n.get('text')or n.get('content-desc')],'state':{'run':s['run'],'controller':s['controllerActive'],'mode':(s.get('vehicle')or{}).get('mode'),'armed':(s.get('vehicle')or{}).get('armed'),'physicsError':s.get('physicsError'),'error':s.get('lastError')}},ensure_ascii=False,indent=2))
