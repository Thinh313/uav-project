from pathlib import Path
import subprocess,time,json,hashlib,os,tarfile,io,re
R=Path(__file__).resolve().parents[2];E=R/'evidence/native84';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.native84'
def adb(*args,timeout=20):
 start=time.monotonic();r=subprocess.run([ADB,'-s',S,*map(str,args)],capture_output=True,timeout=timeout);display=list(map(str,args));
 if 'bridgeToken'in display:display[display.index('bridgeToken')+1]='REDACTED_EPHEMERAL'
 with(E/'adb-commands.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'args':display,'exit':r.returncode,'elapsedMs':(time.monotonic()-start)*1000,'stdoutSha256':hashlib.sha256(r.stdout).hexdigest(),'stderr':r.stderr.decode(errors='replace')[-1000:]})+'\n')
 assert r.returncode==0,r.stderr;return r.stdout
def owned():
 l=json.loads((E/'android-launch.json').read_text());os.kill(l['pid'],0);assert l['avd']=='aeris-native84'and adb('shell','getprop','ro.boot.qemu').strip()==b'1'and adb('emu','avd','name').splitlines()[0]==b'aeris-native84'
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
if __name__=='__main__':
 import sys
 if sys.argv[1]=='capture':capture(sys.argv[2])
 elif sys.argv[1]=='journal':journal(sys.argv[2])
