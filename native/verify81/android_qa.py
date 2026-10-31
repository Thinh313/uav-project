"""Scoped ADB/UIAutomator for the explicitly authorized owned emulator-5582.
No WebView debugging, injected DOM state, physical device or vehicle commands.
"""
from pathlib import Path
import subprocess,json,time,hashlib,xml.etree.ElementTree as ET,re,tarfile,io
R=Path(__file__).resolve().parents[2];E=R/'evidence/native81-development01';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.cockpit81'
def adb(*args,timeout=25):
 p=subprocess.run([ADB,'-s',S,*map(str,args)],capture_output=True,timeout=timeout)
 with(E/'adb-command-log.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'args':list(map(str,args)),'exit':p.returncode,'stdoutSha256':hashlib.sha256(p.stdout).hexdigest(),'stderr':p.stderr.decode(errors='replace')[-1500:]})+'\n')
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
 return p.stdout
def owned():
 assert adb('shell','getprop','ro.boot.qemu').strip()==b'1' and adb('shell','getprop','ro.build.version.sdk').strip()==b'33','OWNED_API33_ONLY'
 assert json.loads((E/'launch05.json').read_text())['serial']==S
def dump():
 result=adb('shell','uiautomator','dump','/data/local/tmp/native81-window.xml')
 if b'UI hierchary dumped to:'not in result:raise RuntimeError('UIAUTOMATOR_NO_FRESH_DUMP_NO_STALE_XML')
 raw=adb('exec-out','cat','/data/local/tmp/native81-window.xml');return raw,ET.fromstring(raw)
def nodes():
 raw,tree=dump();return [{**n.attrib}for n in tree.iter('node')if n.attrib.get('text')or n.attrib.get('content-desc')or n.attrib.get('class','').endswith('EditText')]
def capture(name):
 assert re.fullmatch('[a-z0-9-]{1,80}',name)
 (E/(name+'.png')).open('xb').write(adb('exec-out','screencap','-p'))
 (E/(name+'-capture.json')).open('x').write(json.dumps({'scope':'ADB screenshot, not AX/DOM','uiAutomator':'NOT_AVAILABLE: periodic WebView rendering prevents idle; stale dump is never used','screenshotSha256':hashlib.sha256((E/(name+'.png')).read_bytes()).hexdigest()})+'\n')
 print(json.dumps({'capture':name,'scope':'FRESH_ADB_SCREENSHOT'}))
def tap_label(label):
 raw,t=dump();found=[n for n in t.iter('node')if n.get('text')==label or n.get('content-desc')==label]
 assert len(found)==1,(label,len(found))
 n=found[0];assert n.get('enabled')=='true','CONTROL_DISABLED';v=list(map(int,re.findall(r'\d+',n.get('bounds'))));assert len(v)==4
 adb('shell','input','tap',(v[0]+v[2])//2,(v[1]+v[3])//2)
 print(json.dumps({'tap':label,'bounds':v}));print(json.dumps(nodes(),ensure_ascii=False))
def journal(name):
 assert re.fullmatch('[a-z0-9-]{1,80}',name)
 raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','native81-workspace')
 (E/(name+'.tar')).open('xb').write(raw)
 with tarfile.open(fileobj=io.BytesIO(raw))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 head=files['native81-workspace/HEAD'].decode().strip();rows={}
 for k,data in files.items():
  if not k.endswith('.bin'):continue
  token=hashlib.sha256(data).hexdigest();assert k.endswith('-'+token+'.bin');f=data.split(b'\n',6);assert f[0]==b'AERISWORKSPACE33' and f[5]==b'1' and len(f[6])==int(f[4]) and hashlib.sha256(f[6]).hexdigest()==f[3].decode()
  rows[token]={'revision':int(f[1]),'previous':f[2].decode(),'body':f[6],'bodySha':f[3].decode()}
 assert head in rows;seen=set();at=head
 while at!='ROOT':
  assert at not in seen and at in rows;seen.add(at);at=rows[at]['previous']
 c=json.loads(rows[head]['body']);cur=c['journey'].get('current');receipt={'head':head,'revision':rows[head]['revision'],'bodySha256':rows[head]['bodySha'],'recordCount':len(rows),'chainCount':len(seen),'pending':any(k.endswith('.pending')for k in files),'capsule':c,'files':{k:hashlib.sha256(v).hexdigest()for k,v in files.items()}}
 (E/(name+'.json')).open('x').write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');(E/(name+'-capsule.json')).open('xb').write(rows[head]['body'])
 print(json.dumps({'name':name,'head':head,'revision':receipt['revision'],'phase':cur.get('phase')if cur else None,'cursor':cur.get('cursor')if cur else None,'pending':receipt['pending']}));return receipt
if __name__=='__main__':
 import sys
 owned();op=sys.argv[1]
 if op=='nodes':print(json.dumps(nodes(),ensure_ascii=False))
 elif op=='capture':capture(sys.argv[2])
 elif op=='tap':tap_label(sys.argv[2])
 elif op=='journal':journal(sys.argv[2])
