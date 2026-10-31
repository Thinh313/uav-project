"""Root-only Android UI operations for the explicitly owned emulator."""
from pathlib import Path
import json,re,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[3]
E=R/'evidence/betaintegrated01-cockpit05-native/android'
ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
PKG='vn.rtr.aeris.cockpit05'
def command(args,timeout=15,required=True):
 E.mkdir(exist_ok=True);n=len(list(E.glob('*-command.json')))+1;base=E/f'{n:04d}';started=time.monotonic_ns()
 p=subprocess.run([ADB,'-s','emulator-5582',*map(str,args)],capture_output=True,timeout=timeout)
 base.with_name(base.name+'-stdout.bin').open('xb').write(p.stdout);base.with_name(base.name+'-stderr.bin').open('xb').write(p.stderr)
 base.with_name(base.name+'-command.json').open('x').write(json.dumps(dict(argv=[ADB,'-s','emulator-5582',*map(str,args)],exit=p.returncode,startedNs=started,endedNs=time.monotonic_ns(),noAutomaticActionRetry=True),indent=2))
 if required and p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[:500])
 return p.stdout
def state():return json.loads(command(['shell','run-as',PKG,'cat','files/workspace-state.json']))
def layout():return json.loads(command(['shell','run-as',PKG,'cat','files/native-controls-layout.json']))
def ready(view=None,seconds=12,after_epoch=None):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  try:
   s=state();l=layout()
   if s['viewReady']and l['viewReady']and s['presentedView']==s['chosenView']and(view is None or s['chosenView']==view)and(after_epoch is None or s['viewEpoch']!=after_epoch):return s,l
  except (RuntimeError,KeyError,json.JSONDecodeError):pass
  time.sleep(.2)
 raise RuntimeError('FRESH_UI_VIEW_NOT_READY')
def screen(name):
 b=command(['exec-out','screencap','-p']);assert b[:8]==b'\x89PNG\r\n\x1a\n';p=E/(name+'.png');p.open('xb').write(b);return p
def tree():
 remote='/sdcard/aeris-cockpit05-ui.xml';command(['shell','uiautomator','dump',remote],timeout=20)
 raw=command(['exec-out','cat',remote]);assert len(raw)<1024*1024
 p=E/f'ax-{time.monotonic_ns()}.xml';p.open('xb').write(raw)
 return ET.fromstring(raw),p
def tap(label):
 t,p=tree();matches=[n for n in t.iter('node')if label in(n.get('text'),n.get('content-desc'))and n.get('enabled')=='true'];assert len(matches)==1,(label,[n.attrib for n in matches])
 m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',matches[0].get('bounds'));assert m
 x,y,r,b=map(int,m.groups());assert r>x and b>y
 command(['shell','input','tap',(x+r)//2,(y+b)//2]);return str(p)
