"""Actual owned Android screenshot actions when WebView AX idle dump is unavailable.
No browser DOM/CDP or flight HTTP. Every target is selected from an inspected PNG.
"""
from pathlib import Path
from PIL import Image
import sys,subprocess,json,time,hashlib,re,urllib.request,io
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';PKG='vn.rtr.aeris.simhand01'
tag,action=sys.argv[1:3];assert re.fullmatch('[A-Za-z0-9-]+',tag);out=E/('visual-'+tag);out.mkdir(exist_ok=False)
def adb(*args,binary=False):
 p=subprocess.run([ADB,'-s','emulator-5582',*map(str,args)],capture_output=True,timeout=15);assert p.returncode==0,p.stderr.decode(errors='replace');return p.stdout if binary else p.stdout.decode(errors='replace')
assert adb('shell','getprop','ro.kernel.qemu').strip()=='1'
def capture(name):
 window=adb('shell','dumpsys','window');focus=re.search(r'mCurrentFocus=([^\n]+)',window);assert focus and PKG+'/'in focus.group(1),'OWNED_APP_NOT_FOCUSED'
 b=adb('exec-out','screencap','-p',binary=True);assert b[:8]==bytes.fromhex('89504e470d0a1a0a');im=Image.open(io.BytesIO(b));assert im.size==(1280,800),'VIEWPORT_CHANGED'
 (out/(name+'.png')).open('xb').write(b);(out/(name+'-window.txt')).open('x').write(window)
 return im,time.monotonic(),hashlib.sha256(b).hexdigest()
def state(name):
 with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=4)as response:s=json.load(response)
 (out/(name+'.json')).open('x').write(json.dumps(s,indent=2));return s
state('before-state');im,at,h=capture('before');event={'action':action,'atUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'beforePNG_SHA256':h,'provenance':'ACTUAL_ADB_SCREENSHOT_AND_OWNED_WINDOW_FOCUS_NO_AX_OR_DOM'}
if action=='tap':
 x,y=map(int,sys.argv[3:5]);ref=Path(sys.argv[5]);box=tuple(map(int,sys.argv[6:10]));assert len(box)==4 and box[0]<=x<box[2]and box[1]<=y<box[3]and 24<=y<740
 with Image.open(ref)as old:assert old.size==im.size and old.convert('RGBA').crop(box).tobytes()==im.convert('RGBA').crop(box).tobytes(),'TARGET_CHANGED_NO_TAP'
 if len(sys.argv)>10 and sys.argv[10]=='--fresh-heartbeat':
  until=time.monotonic()+2.5
  while True:
   with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=1)as r:observed=json.load(r)
   age=(observed.get('vehicle')or{}).get('heartbeatAgeMs',99999)
   if age<200:break
   assert time.monotonic()<until,'NO_FRESH_HEARTBEAT_NO_TAP';time.sleep(.03)
  event['observedHeartbeatAgeMsBeforeTap']=age
 assert time.monotonic()-at<5;event.update(x=x,y=y,reference=str(ref),verifiedRegion=box);(out/'intent.json').open('x').write(json.dumps(event,indent=2));adb('shell','input','tap',x,y)
elif action=='scroll':
 x0,y0,x1,y1=map(int,sys.argv[3:7]);assert 24<=y0<y1<=740 and 0<=x0<x1<=1280;event.update(region=[x0,y0,x1,y1]);(out/'intent.json').open('x').write(json.dumps(event,indent=2));adb('shell','input','swipe',(x0+x1)//2,y1-30,(x0+x1)//2,y0+30,350)
elif action=='stick':
 x0,y0,x1,y1=map(int,sys.argv[3:7]);dx,dy=float(sys.argv[7]),float(sys.argv[8]);ms=int(sys.argv[9]);assert abs(dx)<=.12 and abs(dy)<=.12 and 200<=ms<=1000 and 24<=y0<y1<740
 x=(x0+x1)//2;y=(y0+y1)//2;event.update(bounds=[x0,y0,x1,y1],dx=dx,dy=dy,durationMs=ms,pointerReleaseAtEnd=True);(out/'intent.json').open('x').write(json.dumps(event,indent=2));assert time.monotonic()-at<5;adb('shell','input','touchscreen','swipe',x,y,round(x+dx*(x1-x0)),round(y+dy*(y1-y0)),ms)
elif action!='snapshot':raise ValueError('ACTION_ALLOWLIST')
time.sleep(.25);capture('after');s=state('after-state');print(json.dumps({'image':str(out/'after.png'),'run':s['run'],'lifecycle':s.get('lifecycle'),'armed':(s.get('vehicle')or{}).get('armed'),'mode':(s.get('vehicle')or{}).get('mode'),'physicsError':s.get('physicsError'),'error':s.get('lastError')},ensure_ascii=False))
