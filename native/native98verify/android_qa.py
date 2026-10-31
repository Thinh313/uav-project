"""Authorized ADB/UIAutomator on owned emulator-5582 only; no physical device, DOM injection or WebView debugging."""
from pathlib import Path
import subprocess,time,json,hashlib,os,tarfile,io,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];E=R/'evidence/native98verify';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.native98'
def adb(*args,timeout=30,allow_failure=False):
 start=time.monotonic();r=subprocess.run([ADB,'-s',S,*map(str,args)],capture_output=True,timeout=timeout)
 with(E/'adb-commands.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'args':[('<REDACTED_HOST_TOKEN>' if i>0 and str(args[i-1])=='bridgeToken' else str(v)) for i,v in enumerate(args)],'exit':r.returncode,'elapsedMs':(time.monotonic()-start)*1000,'stdoutSha256':hashlib.sha256(r.stdout).hexdigest(),'stderr':r.stderr.decode(errors='replace')[-1000:]})+'\n')
 if not allow_failure:assert r.returncode==0,r.stderr.decode(errors='replace')
 return r.stdout

def owned():
 receipt=max(E.glob('android-launch*.json'),key=lambda p:p.name);l=json.loads(receipt.read_text());os.kill(l['pid'],0);assert l['avd']=='aeris-native90'and l['serial']==S
 assert adb('shell','getprop','ro.boot.qemu').strip()==b'1'and adb('shell','getprop','ro.build.version.sdk').strip()==b'33'
 assert adb('emu','avd','name').splitlines()[0]==b'aeris-native90'

def dump():
 owned();res=adb('shell','uiautomator','dump','/data/local/tmp/native94-window.xml')
 assert b'UI hierchary dumped to:'in res,'NO_FRESH_UI_DUMP_NO_STALE_XML'
 raw=adb('exec-out','cat','/data/local/tmp/native94-window.xml');index=len(list(E.glob('ui-*.xml')))+1;(E/('ui-%04d.xml'%index)).open('xb').write(raw);return raw,ET.fromstring(raw)

def nodes():
 raw,tree=dump();return[{**n.attrib}for n in tree.iter('node')if n.get('text')or n.get('content-desc')or n.get('class','').endswith('EditText')]

def tap_label(label):
 raw,t=dump();found=[n for n in t.iter('node')if n.get('text')==label or n.get('content-desc')==label]
 assert len(found)==1,(label,len(found));n=found[0];assert n.get('enabled')=='true','CONTROL_DISABLED';v=list(map(int,re.findall(r'\d+',n.get('bounds',''))));assert len(v)==4 and v[2]>v[0]and v[3]>v[1]
 adb('shell','input','tap',(v[0]+v[2])//2,(v[1]+v[3])//2);print(json.dumps({'tap':label,'bounds':v}),flush=True)

def tap_id(resource):
 raw,t=dump();found=[n for n in t.iter('node')if n.get('resource-id')==resource];assert len(found)==1,(resource,len(found));n=found[0];assert n.get('enabled')=='true';v=list(map(int,re.findall(r'\d+',n.get('bounds',''))));assert len(v)==4 and v[2]>v[0]and v[3]>v[1];adb('shell','input','tap',(v[0]+v[2])//2,(v[1]+v[3])//2);print(json.dumps({'tapId':resource,'bounds':v}),flush=True)

def compact():
 return[{k:n.get(k)for k in['resource-id','text','bounds','enabled','class']}for n in nodes()if n.get('class','').endswith(('EditText','Button','CheckBox','Spinner'))or n.get('resource-id')in['native-status','native-progress','pane-title','confirmation-progress']]

def capture(name):
 owned();assert re.fullmatch('[a-z0-9-]+',name);b=adb('exec-out','screencap','-p');assert b.startswith(b'\x89PNG');(E/(name+'.png')).open('xb').write(b);print(name,flush=True)

def journal(name):
 owned();assert b'uid=0'in adb('shell','id');b=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','workspaces');(E/(name+'.tar')).open('xb').write(b)
 with tarfile.open(fileobj=io.BytesIO(b))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 selected=files.get('workspaces/CURRENT',b'initial').decode().strip();out={'selected':selected,'files':{k:hashlib.sha256(v).hexdigest()for k,v in files.items()},'journals':{}}
 for k,headraw in files.items():
  if not k.endswith('/HEAD'):continue
  parent=k[:-5];head=headraw.decode().strip();rows={}
  for f,raw in files.items():
   if str(Path(f).parent)!=parent or not f.endswith('.bin'):continue
   h=raw.split(b'\n',6);token=hashlib.sha256(raw).hexdigest();assert f.endswith(token+'.bin')and h[0]==b'AERISWORKSPACE33'and len(h[6])==int(h[4])and hashlib.sha256(h[6]).hexdigest()==h[3].decode();rows[token]={'revision':int(h[1]),'previous':h[2].decode(),'body':h[6].decode(),'bodySha256':h[3].decode()}
  at=head;seen=set()
  while at!='ROOT':assert at in rows and at not in seen;seen.add(at);at=rows[at]['previous']
  out['journals'][parent]={'head':head,'recordCount':len(rows),'chainCount':len(seen),'latest':rows[head]}
 assert not any(x.endswith('.pending')for x in files);(E/(name+'.json')).open('x').write(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'selected':selected,'heads':{k:v['head']for k,v in out['journals'].items()}}));return out

def reports(name):
 owned();assert b'uid=0'in adb('shell','id');current=adb('exec-out','cat','/data/user/0/'+P+'/files/ui96/CURRENT').decode().strip();assert re.fullmatch('[a-f0-9-]{36}',current);raw=adb('exec-out','cat','/data/user/0/'+P+'/files/ui96/'+current+'.jsonl');(E/(name+'.jsonl')).open('xb').write(raw);rows=[json.loads(l)for l in raw.splitlines()];print(json.dumps({'reports':len(rows),'environment':rows[-1]['environment'],'last':{k:rows[-1]['renderer'].get(k)for k in['view','theme','supports','alignmentDelta','sourceStatus']}}));return rows

if __name__=='__main__':
 import sys;owned();op=sys.argv[1]
 if op=='nodes':print(json.dumps(nodes(),ensure_ascii=False))
 elif op=='tap':tap_label(sys.argv[2]);print(json.dumps(nodes(),ensure_ascii=False))
 elif op=='capture':capture(sys.argv[2])
 elif op=='journal':journal(sys.argv[2])
 elif op=='reports':reports(sys.argv[2])
