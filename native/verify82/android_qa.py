"""Authorized ADB/UIAutomator/root only owned emulator-5582. No WebView debugging/JS injection."""
from pathlib import Path
import subprocess,json,time,hashlib,re,xml.etree.ElementTree as ET,tarfile,io,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82-emulator04';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.cockpit82';WORK='native82-workspace'
def adb(*args,timeout=15):
 start=time.monotonic();record={'at':time.time(),'args':list(map(str,args))}
 try:
  p=subprocess.run([ADB,'-s',S,*map(str,args)],capture_output=True,timeout=timeout);record.update(exit=p.returncode,stdoutSha256=hashlib.sha256(p.stdout).hexdigest(),stderr=p.stderr.decode(errors='replace')[-1200:])
  if p.returncode:raise RuntimeError('ADB_EXIT_'+str(p.returncode)+':'+record['stderr'])
  return p.stdout
 except Exception as e:record['error']=str(e);raise
 finally:
  record['durationMs']=round((time.monotonic()-start)*1000,3)
  with(E/'adb-commands.jsonl').open('a')as f:f.write(json.dumps(record)+'\n')
def owned():
 assert adb('shell','getprop','ro.boot.qemu').strip()==b'1'
 assert adb('shell','getprop','ro.build.version.sdk').strip()==b'33'
 current=json.loads((E/'current-runtime.json').read_text());assert current['serial']==S
 assert current['avd'] in ['aeris-cockpit82','aeris-cockpit82-active04'] and adb('emu','avd','name').splitlines()[0].decode()==current['avd']
 os.kill(current['pid'],0)
def capture(name):
 assert re.fullmatch('[a-z0-9-]{1,80}',name)
 raw=adb('exec-out','screencap','-p');assert raw.startswith(b'\x89PNG\r\n\x1a\n'),'INVALID_SCREENSHOT'
 (E/(name+'.png')).open('xb').write(raw);(E/(name+'-capture.json')).open('x').write(json.dumps({'at':time.time(),'sha256':hashlib.sha256(raw).hexdigest(),'scope':'Fresh ADB screenshot. Wait for visible expected UI; screenshot may show an intermediate state.'})+'\n');print('CAPTURE '+name,flush=True)
def nodes(name):
 assert re.fullmatch('[a-z0-9-]{1,80}',name)
 answer=adb('shell','uiautomator','dump','/data/local/tmp/cockpit82-verify-window.xml',timeout=15)
 assert b'UI hierchary dumped to:' in answer,'NO_FRESH_XML'
 raw=adb('exec-out','cat','/data/local/tmp/cockpit82-verify-window.xml');t=ET.fromstring(raw);(E/(name+'.xml')).open('xb').write(raw)
 selected=[n.attrib for n in t.iter('node')if n.get('text')or n.get('content-desc')or n.get('class','').endswith('EditText')];print(json.dumps(selected,ensure_ascii=False));return selected
def journal(name):
 assert re.fullmatch('[a-z0-9-]{1,80}',name);assert b'uid=0' in adb('shell','id'),'OWNED_ADB_ROOT_REQUIRED'
 raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-',WORK)
 with tarfile.open(fileobj=io.BytesIO(raw))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 head=files[WORK+'/HEAD'].decode().strip();rows={}
 for k,v in files.items():
  if not k.endswith('.bin'):continue
  token=hashlib.sha256(v).hexdigest();assert k.endswith('-'+token+'.bin');h=v.split(b'\n',6);assert h[0]==b'AERISWORKSPACE33' and h[5]==b'1' and len(h[6])==int(h[4]) and hashlib.sha256(h[6]).hexdigest()==h[3].decode();rows[token]={'revision':int(h[1]),'previous':h[2].decode(),'body':h[6],'bodySha':h[3].decode()}
 assert head in rows;seen=set();at=head
 while at!='ROOT':assert at not in seen and at in rows;seen.add(at);at=rows[at]['previous']
 cap=json.loads(rows[head]['body']);cur=cap['journey'].get('current');r={'at':time.time(),'head':head,'revision':rows[head]['revision'],'bodySha256':rows[head]['bodySha'],'recordCount':len(rows),'chainCount':len(seen),'pending':any(n.endswith('.pending')for n in files),'capsule':cap,'files':{k:hashlib.sha256(v).hexdigest()for k,v in files.items()}}
 assert not r['pending'];(E/(name+'.tar')).open('xb').write(raw);(E/(name+'.json')).open('x').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n');(E/(name+'-capsule.json')).open('xb').write(rows[head]['body']);print(json.dumps({'name':name,'head':head,'revision':r['revision'],'phase':cur.get('phase')if cur else None,'cursor':cur.get('cursor')if cur else None,'pending':r['pending']}),flush=True);return r
if __name__=='__main__':
 import sys
 owned();op=sys.argv[1]
 if op=='capture':capture(sys.argv[2])
 elif op=='nodes':nodes(sys.argv[2])
 elif op=='journal':journal(sys.argv[2])
