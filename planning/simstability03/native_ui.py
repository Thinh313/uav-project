"""Owned emulator-only UIAutomator/ADB helper. No runtime start, install, CDP or DOM execution.
Every tap/gesture is based on fresh native XML and preceded by an actual screenshot.
Mutating UI calls must be explicitly selected by the Contractor; no failed flight retry.
"""
from pathlib import Path
import subprocess,time,json,re,hashlib,uuid,xml.etree.ElementTree as ET
ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
SERIAL='emulator-5582'
PACKAGE='vn.rtr.aeris.simhand01'
class NativeUI:
 def __init__(self,out):
  self.out=Path(out).resolve();assert 'evidence/simstability03/' in str(self.out)+'/'
  self.out.mkdir(parents=True,exist_ok=False);self.n=0;self.last=None
 def adb(self,*args,binary=False,timeout=20):
  q=subprocess.run([ADB,'-s',SERIAL,*map(str,args)],capture_output=True,timeout=timeout)
  if q.returncode:raise RuntimeError('ADB_FAILED:'+str(args[:3])+':'+q.stderr.decode(errors='replace')[:250])
  return q.stdout if binary else q.stdout.decode(errors='replace')
 def require_owned(self):
  if self.adb('get-state').strip()!='device':raise RuntimeError('OWNED_EMULATOR_NOT_READY')
  if self.adb('shell','getprop','ro.kernel.qemu').strip()!='1':raise RuntimeError('EMULATOR5582_ONLY')
 def log(self,kind,data):
  row={'kind':kind,'atUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'mono':time.monotonic(),'serial':SERIAL,**data}
  with (self.out/'actions.jsonl').open('a')as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
 @staticmethod
 def validate_dump_result(code,stdout,stderr,remote):
  text=stdout.decode(errors='replace')if isinstance(stdout,bytes)else stdout
  err=stderr.decode(errors='replace')if isinstance(stderr,bytes)else stderr
  if code!=0 or re.search(r'\berror\b',text+' '+err,re.I)or not re.search(r'UI (?:hierchary|hierarchy) dumped to:\s*'+re.escape(remote)+r'(?:\s|$)',text):raise RuntimeError('NATIVE_XML_DUMP_NOT_CONFIRMED')
  return True
 def dump_xml(self,remote):
  q=subprocess.run([ADB,'-s',SERIAL,'shell','uiautomator','dump','--compressed',remote],capture_output=True,timeout=15)
  self.validate_dump_result(q.returncode,q.stdout,q.stderr,remote)
 def snapshot(self,label):
  self.last=None;self.require_owned();self.n+=1;stem=f'{self.n:03d}-'+re.sub('[^A-Za-z0-9_-]','_',label)[:75]
  remote='/sdcard/simstability03-'+stem+'-'+uuid.uuid4().hex+'.xml'
  self.dump_xml(remote)
  data=self.adb('exec-out','cat',remote,binary=True);root=ET.fromstring(data)
  if root.tag!='hierarchy'or not list(root.iter('node')):raise RuntimeError('NATIVE_XML_HIERARCHY_REQUIRED')
  png=self.adb('exec-out','screencap','-p',binary=True)
  if png[:8]!=bytes.fromhex('89504e470d0a1a0a'):raise RuntimeError('SCREENSHOT_NOT_PNG')
  for ext,b in [('xml',data),('png',png)]:
   with (self.out/(stem+'.'+ext)).open('xb')as f:f.write(b)
  parents={c:p for p in root.iter()for c in p};self.last={'stem':stem,'at':time.monotonic(),'root':root,'parents':parents,'pngSha256':hashlib.sha256(png).hexdigest()}
  self.log('OBSERVATION',{'stem':stem,'pngSha256':self.last['pngSha256'],'xmlSha256':hashlib.sha256(data).hexdigest(),'nodes':len(list(root.iter()))})
  return self.last
 @staticmethod
 def bounds(node):
  m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
  if not m:return None
  a=list(map(int,m.groups()));return a if a[2]>a[0]and a[3]>a[1]else None
 def find(self,label,attribute=None,require_enabled=True):
  if not self.last:raise RuntimeError('FRESH_SNAPSHOT_REQUIRED')
  matches=[]
  for node in self.last['root'].iter('node'):
   fields=[node.get(attribute,'')]if attribute else[node.get('text',''),node.get('content-desc',''),node.get('resource-id','')]
   if not any(v==label or attribute=='resource-id'and v.endswith('/'+label)for v in fields):continue
   rect=self.bounds(node)
   if not rect:continue
   if require_enabled and node.get('enabled')!='true':continue
   matches.append((node,rect))
  if len(matches)!=1:raise RuntimeError('UI_TARGET_NOT_UNIQUE_VISIBLE:'+label+':'+str(len(matches)))
  return matches[0]
 def tap(self,label,attribute=None):
  q=self.snapshot('before-tap-'+label);node,b=self.find(label,attribute)
  if time.monotonic()-q['at']>2:raise RuntimeError('UI_OBSERVATION_STALE')
  self.log('TAP_NATIVE_XML',{'label':label,'attribute':attribute,'bounds':b,'observation':q['stem'],'node':{k:node.get(k)for k in['text','content-desc','resource-id','class','enabled','clickable']}})
  self.adb('shell','input','tap',(b[0]+b[2])//2,(b[1]+b[3])//2)
 def tap_observed(self,x,y,observation):
  if not self.last or self.last['stem']!=observation or time.monotonic()-self.last['at']>5:raise RuntimeError('FRESH_VISIBLE_SCREENSHOT_REQUIRED')
  b=self.bounds(next(iter(self.last['root'].iter('node'))));assert b and b[0]<=x<b[2]and b[1]<=y<b[3]
  self.log('TAP_REVIEWED_SCREENSHOT',{'x':x,'y':y,'observation':observation,'scope':'CONTRACTOR_CHOSEN_ACTUAL_SCREENSHOT_NOT_INFERRED_DOM'})
  self.adb('shell','input','tap',int(x),int(y))
 def gesture_stick(self,label,dx_fraction=0,dy_fraction=0,duration_ms=650):
  if not(-.12<=dx_fraction<=.12 and -.12<=dy_fraction<=.12 and 200<=duration_ms<=1000):raise RuntimeError('BOUNDED_STICK_GESTURE')
  q=self.snapshot('before-stick-'+label);node,b=self.find(label);x=(b[0]+b[2])/2;y=(b[1]+b[3])/2;end=[x+(b[2]-b[0])*dx_fraction,y+(b[3]-b[1])*dy_fraction]
  self.log('BOUNDED_NATIVE_SWIPE',{'label':label,'bounds':b,'from':[x,y],'to':end,'durationMs':duration_ms,'observation':q['stem'],'pointerReleaseAtEnd':True})
  self.adb('shell','input','touchscreen','swipe',round(x),round(y),round(end[0]),round(end[1]),duration_ms)
 def scroll_observed(self,bounds,direction='up'):
  if not self.last or time.monotonic()-self.last['at']>5:raise RuntimeError('FRESH_SCREENSHOT_REQUIRED')
  x0,y0,x1,y1=map(int,bounds)
  if x1-x0<60 or y1-y0<100:raise RuntimeError('SCROLL_REGION')
  # Contractor supplies the visible panel rectangle from the immediately reviewed
  # screenshot; no guessed page offset or CSS-pixel/statusbar conversion is used.
  x=(x0+x1)//2;ya=y1-30;yb=y0+30
  if direction=='down':ya,yb=yb,ya
  self.log('SCROLL_REVIEWED_REGION',{'bounds':[x0,y0,x1,y1],'direction':direction,'observation':self.last['stem']})
  self.adb('shell','input','swipe',x,ya,x,yb,350)
 def key(self,name):
  if name not in['BACK','HOME','ENTER','KEYCODE_BACK','KEYCODE_HOME','KEYCODE_ENTER']:raise RuntimeError('FIXED_KEY_ONLY')
  self.log('KEY',{'key':name});self.adb('shell','input','keyevent',name)
 def visible_nodes(self):
  if not self.last:return[]
  return[{**n.attrib,'rect':self.bounds(n)}for n in self.last['root'].iter('node')if self.bounds(n)]
