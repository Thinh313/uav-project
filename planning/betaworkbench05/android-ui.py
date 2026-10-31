from pathlib import Path
import subprocess,json,xml.etree.ElementTree as ET,re,sys,time,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/betaworkbench05';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';serial='emulator-5582'
def adb(*a):
 p=subprocess.run([ADB,'-s',serial,*a],capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode(errors='replace');return p.stdout
def tree():
 adb('shell','uiautomator','dump','/sdcard/beta05-ui.xml');b=adb('exec-out','cat','/sdcard/beta05-ui.xml');n=len(list(E.glob('ui-*.xml')))+1;(E/('ui-%03d.xml'%n)).open('xb').write(b);return ET.fromstring(b)
def summary(root):
 for n in root.iter('node'):
  t=n.get('text')or n.get('content-desc')
  if t:print(t[:700],n.get('bounds'),'enabled='+str(n.get('enabled')))
def record(action,detail):
 p=E/'android-actions01.jsonl'
 assert not p.exists()or p.stat().st_size<256*1024
 with p.open('a')as f:f.write(json.dumps({'at':time.time(),'action':action,'detail':detail})+'\n');f.flush();os.fsync(f.fileno())
if __name__=='__main__':
 action=sys.argv[1]
 if action=='snapshot':summary(tree())
 elif action=='click':
  root=tree();text=sys.argv[2];xs=[n for n in root.iter('node')if(n.get('text')==text or n.get('content-desc')==text)and n.get('enabled')=='true'];assert len(xs)==1,[(n.get('text'),n.get('bounds'))for n in xs]
  b=list(map(int,re.findall(r'\d+',xs[0].get('bounds'))));adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));record(action,{'text':text,'bounds':b});summary(tree())
 elif action=='key':
  assert sys.argv[2]in['4','66','123'];adb('shell','input','keyevent',sys.argv[2]);record(action,sys.argv[2]);summary(tree())
 elif action=='swipe':
  a=list(map(int,sys.argv[2:]));assert len(a)==4 and all(0<=x<=1280 for x in a);adb('shell','input','swipe',*map(str,a),'400');record(action,a);summary(tree())
 elif action=='tap':
  x,y=map(int,sys.argv[2:4]);assert 0<=x<1280 and 0<=y<800;adb('shell','input','tap',str(x),str(y));record(action,[x,y]);time.sleep(.6);name=sys.argv[4];assert re.fullmatch(r'[a-z0-9-]+\.png',name);(E/name).open('xb').write(adb('exec-out','screencap','-p'));print(name)
 elif action=='drag':
  a=list(map(int,sys.argv[2:6]));assert all(0<=x<=1280 for x in a);adb('shell','input','swipe',*map(str,a),'400');record(action,a);time.sleep(1.8);name=sys.argv[6];(E/name).open('xb').write(adb('exec-out','screencap','-p'));print(name)
 elif action=='screenshot':
  name=sys.argv[2];assert re.fullmatch(r'[a-z0-9-]+\.png',name);(E/name).open('xb').write(adb('exec-out','screencap','-p'));print(name)
