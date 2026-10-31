from pathlib import Path
import subprocess,json,sys,time,hashlib,tarfile,io
R=Path(__file__).resolve().parents[2];E=R/'evidence/native79';A='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';P='vn.rtr.aeris.native79'
def adb(*args):
 p=subprocess.run([A,'-s',S,*map(str,args)],capture_output=True,timeout=30)
 with(E/'ui-command-log.jsonl').open('a')as f:f.write(json.dumps({'at':time.time(),'args':list(map(str,args)),'returncode':p.returncode,'stdoutSha256':hashlib.sha256(p.stdout).hexdigest()})+'\n')
 assert p.returncode==0,p.stderr.decode(errors='replace');return p.stdout
def tap(x,y):adb('shell','input','tap',x,y);time.sleep(.5)
def snap(name):
 assert not(E/(name+'.png')).exists()
 (E/(name+'.png')).write_bytes(adb('exec-out','screencap','-p'))
 raw=adb('exec-out','run-as',P,'tar','-C','files','-cf','-','native79-drafts')
 (E/(name+'.tar')).write_bytes(raw)
 with tarfile.open(fileobj=io.BytesIO(raw))as t:
  m={x.name:t.extractfile(x).read()for x in t.getmembers()if x.isfile()}
 head=m['native79-drafts/HEAD'].decode().strip();record=next(v for k,v in m.items()if k.endswith('-'+head+'.bin'));assert hashlib.sha256(record).hexdigest()==head
 fields=record.split(b'\n',6);body=fields[6];assert hashlib.sha256(body).hexdigest()==fields[3].decode()
 cap=json.loads(body);(E/(name+'.json')).write_text(json.dumps({'head':head,'revision':int(fields[1]),'capsule':cap,'files':{k:hashlib.sha256(v).hexdigest()for k,v in m.items()}},indent=2))
 cur=cap['journey'].get('current');print(json.dumps({'name':name,'revision':int(fields[1]),'phase':cur.get('phase')if cur else None,'cursor':cur.get('cursor')if cur else None}))
if __name__=='__main__':
 op=sys.argv[1]
 if op=='tap':tap(*sys.argv[2:])
 elif op=='snap':snap(sys.argv[2])
