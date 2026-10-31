"""Authorized UIAutomator/ADB only on owned FIELD02 emulator-5582; no JS controls."""
from pathlib import Path
import subprocess,time,json,hashlib,os,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/repair01';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.field02'
def adb(*a,timeout=20,allow=False):
 t=time.monotonic();r=subprocess.run([ADB,'-s',S,*map(str,a)],capture_output=True,timeout=timeout)
 with(E/'qa-adb-commands.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'args':list(map(str,a)),'exit':r.returncode,'elapsedMs':(time.monotonic()-t)*1000,'stdoutSha256':hashlib.sha256(r.stdout).hexdigest(),'stderr':r.stderr.decode(errors='replace')[-500:]})+'\n')
 if not allow:assert r.returncode==0,r.stderr.decode(errors='replace')
 return r.stdout
def owned():
 receipts=sorted(E.glob('android-launch[0-9][0-9].json'));assert receipts
 l=json.loads(receipts[-1].read_text());os.kill(l['pid'],0);assert l['avd']=='aeris-field02'and l['serial']==S
 assert adb('shell','getprop','ro.boot.qemu').strip()==b'1';assert adb('emu','avd','name').splitlines()[0]==b'aeris-field02'
def dump():
 owned();v=adb('shell','uiautomator','dump','/data/local/tmp/field02-window.xml',timeout=30);assert b'UI hierchary dumped to:'in v
 raw=adb('exec-out','cat','/data/local/tmp/field02-window.xml');n=len(list(E.glob('qa-ui-*.xml')))+1
 (E/('qa-ui-%04d.xml'%n)).open('xb').write(raw);return ET.fromstring(raw)
def nodes():return[{**n.attrib}for n in dump().iter('node')if n.get('text')or n.get('content-desc')or n.get('class','').endswith('EditText')]
def tap(label):
 ns=[n for n in dump().iter('node')if label in [n.get('text'),n.get('content-desc'),n.get('resource-id')]];assert len(ns)==1,(label,len(ns));n=ns[0];assert n.get('enabled')=='true','DISABLED';v=list(map(int,re.findall(r'\d+',n.get('bounds',''))));assert len(v)==4 and v[2]>v[0]and v[3]>v[1]
 adb('shell','input','tap',(v[0]+v[2])//2,(v[1]+v[3])//2);print(json.dumps({'tap':label,'bounds':v},ensure_ascii=False))
def capture(name):
 owned();assert re.fullmatch('[a-z0-9-]+',name);b=adb('exec-out','screencap','-p');assert b.startswith(b'\x89PNG');(E/(name+'.png')).open('xb').write(b)
if __name__=='__main__':
 import sys
 op=sys.argv[1]
 if op=='nodes':print(json.dumps(nodes(),ensure_ascii=False))
 elif op=='tap':tap(sys.argv[2]);print(json.dumps(nodes(),ensure_ascii=False))
 elif op=='capture':capture(sys.argv[2])
 elif op=='xy':
  owned();x,y=map(int,sys.argv[2:4]);assert 0<=x<1280 and 0<=y<800
  adb('shell','input','tap',x,y);time.sleep(.35);capture(sys.argv[4])
 elif op=='swipe':
  owned();a=list(map(int,sys.argv[2:6]));assert all(0<=v<1280 for v in a[::2]) and all(0<=v<800 for v in a[1::2])
  adb('shell','input','swipe',*a,500);time.sleep(.35);capture(sys.argv[6])
