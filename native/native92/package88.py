"""Portable closed-run evidence. Independent receiver uses stdlib SHA/ZIP/JSON, never restores authority."""
from pathlib import Path,PurePosixPath
import os,sys,json,hashlib,zipfile,uuid,shutil,re,stat,datetime
MAX=64*2**20;MAXFILES=256;R=Path(__file__).resolve().parents[2];E=R/'evidence/native92'
def sha(b):return hashlib.sha256(b).hexdigest()
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(65536):h.update(b)
 return h.hexdigest()
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def put(p,v):
 with p.open('xb')as f:f.write(canon(v)+b'\n');f.flush();os.fsync(f.fileno())
def strict_json(b):
 def pairs(xs):
  d={}
  for k,v in xs:
   assert k not in d,'DUPLICATE_JSON_KEY';d[k]=v
  return d
 def constant(v):raise ValueError('NONFINITE_JSON')
 return json.loads(b,object_pairs_hook=pairs,parse_constant=constant)
def valid(s):assert re.fullmatch('[a-zA-Z0-9_-]{3,64}',s),'IDENTITY'
def build(run,receiver,nonce):
 valid(run);valid(receiver);valid(nonce);assert re.fullmatch('s[a-f0-9]{20}',run)
 root=E/'runs'/run;review=json.loads((root/'review.json').read_text());closure=json.loads((root/'closure.json').read_text());assert closure['stopped']and closure['error']is None,'NOT_CLOSED'
 assert review['run']==run and review['actualImages']==0 and not review['authorityRestorable']
 entries=list(root.rglob('*'));assert not any(p.is_symlink()for p in entries),'SYMLINK';paths=sorted(p for p in entries if p.is_file());assert len(paths)<=MAXFILES
 files={};total=0
 for p in paths:
  assert not p.is_symlink()and all(not x.is_symlink()for x in p.parents if x!=root.parent),'SYMLINK'
  n=p.relative_to(root).as_posix();total+=p.stat().st_size;assert total<=MAX,'TOTAL_BOUND';files[n]={'bytes':p.stat().st_size,'sha256':filehash(p)}
 required=['raw.jsonl','observer/raw.jsonl','observer/closure.json','plan.json','session.json','launch.json','closure.json','review.json','flight-pins-at-start.json']
 assert all(n in files for n in required),'MISSING_REQUIRED_RAW'
 key=sha(canon({'run':run,'receiver':receiver,'nonce':nonce,'files':files}));out=E/'packages';out.mkdir(exist_ok=True);dest=out/(key+'.zip');manifest={'format':'aeris-flight-evidence88','version':1,'run':run,'receiver':receiver,'nonce':nonce,'contentId':key,'files':files,'totalBytes':total,'scope':'ENGINEERING_INTERNAL_QUAD_NOT_HERA','authorityRestorable':False,'actualImages':0,'authenticated':False,'softwareSignature':False}
 assert shutil.disk_usage(R).free>21*2**30 and not dest.exists()
 with dest.open('xb')as sink:
  with zipfile.ZipFile(sink,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for p in paths:
    name=p.relative_to(root).as_posix();assert filehash(p)==files[name]['sha256'],'SOURCE_CHANGED';z.write(p,name)
   z.writestr('MANIFEST88.json',canon(manifest))
  sink.flush();os.fsync(sink.fileno())
 assert dest.stat().st_size<=MAX
 desc={'ok':True,'format':'aeris-flight-bundle88','id':key,'run':run,'receiver':receiver,'nonce':nonce,'sha256':filehash(dest),'bytes':dest.stat().st_size,'manifestSha256':sha(canon(manifest)),'authorityRestorable':False,'actualImages':0};put(out/(key+'.json'),desc);return desc

def chain(data):
 assert len(data)<=16*2**20 and(not data or data.endswith(b'\n')),'TORN_RAW';previous='';count=0;rows=[]
 for line in data.splitlines():
  v=json.loads(line);h=v.pop('sha256');count+=1;assert v['n']==count and v['previous']==previous,'RAW_CHAIN';assert sha(canon(v))==h,'RAW_DIGEST';previous=h;v['sha256']=h;rows.append(v)
 return previous,rows

def inspect(path,receiver,nonce):
 valid(receiver);valid(nonce);assert path.is_file()and not path.is_symlink()and path.stat().st_size<=MAX,'PACKAGE_BOUND'
 with zipfile.ZipFile(path)as z:
  infos=z.infolist();assert len(infos)<=MAXFILES+1 and len({i.filename for i in infos})==len(infos),'DUPLICATE_OR_COUNT'
  total=0
  for i in infos:
   n=PurePosixPath(i.filename);assert not n.is_absolute()and'..'not in n.parts and'\\'not in i.filename and not i.is_dir(),'PATH';assert (i.external_attr>>16)&0o170000!=stat.S_IFLNK,'SYMLINK';assert not i.flag_bits&1,'ENCRYPTED';total+=i.file_size;assert total<=MAX+2**20 and i.file_size<=16*2**20,'INFLATED_BOUND'
  assert z.getinfo('MANIFEST88.json').file_size<=2**20
  m=strict_json(z.read('MANIFEST88.json'));assert m['format']=='aeris-flight-evidence88'and m['version']==1 and m['receiver']==receiver and m['nonce']==nonce,'RECEIVER_NONCE';assert m['authorityRestorable']is False and m['actualImages']==0 and m['authenticated']is False and m['softwareSignature']is False,'SCOPE'
  assert set(z.namelist())==set(m['files'])|{'MANIFEST88.json'},'MISSING_OR_EXTRA';observed={}
  for n,f in m['files'].items():
   assert z.getinfo(n).file_size==f['bytes'],'LENGTH';h=hashlib.sha256();length=0
   with z.open(n)as src:
    while b:=src.read(65536):length+=len(b);assert length<=f['bytes'];h.update(b)
   assert length==f['bytes']and h.hexdigest()==f['sha256'],'SHA256';observed[n]=f
  assert sum(f['bytes']for f in observed.values())==m['totalBytes'],'TOTAL';assert sha(canon({'run':m['run'],'receiver':receiver,'nonce':nonce,'files':observed}))==m['contentId'],'CONTENT_ID'
  for n in ['raw.jsonl','observer/raw.jsonl','observer/closure.json','plan.json','session.json','launch.json','closure.json','review.json','flight-pins-at-start.json']:assert n in observed,'REQUIRED_EVIDENCE'
  # JSON number reserialization differs between JS/Python for some floats; raw chain SHA is verified by JS full semantic receiver after byte integrity.
  review=json.loads(z.read('review.json'));cl=json.loads(z.read('closure.json'));oc=json.loads(z.read('observer/closure.json'));assert review['run']==m['run']and cl['stopped']and cl['error']is None and oc['stopped']and oc['error']is None
  assert review['actualImages']==0 and review['authorityRestorable']is False
  return{'status':'INTEGRITY_VERIFIED_SEMANTIC_REPLAY_REQUIRED','contentId':m['contentId'],'run':m['run'],'receiver':receiver,'nonce':nonce,'files':len(observed),'bytes':m['totalBytes'],'packageSha256':filehash(path),'manifestSha256':sha(canon(m)),'missionAccepted':False,'authorityRestored':False,'sourceAuthenticated':False}

def receive(path,receiver,nonce,store):
 r=inspect(path,receiver,nonce);store.mkdir(exist_ok=True);lock=store/(receiver+'-'+nonce+'.lock');assert not lock.exists(),'REPLAY_OR_NONCE_REUSE'
 # Receipt publishes only after independent JS semantic replay; verifier reads ZIP bytes directly, never unpacks paths.
 import subprocess
 q=subprocess.run(['node',str(R/'native/native92/receiver_semantic88.mjs'),str(path)],capture_output=True,text=True,timeout=30);assert q.returncode==0,'SEMANTIC_REPLAY_FAILED:'+q.stderr[-500:];v=json.loads(q.stdout);assert v['status']=='PASS';r['semantic']=v;r['status']='VERIFIED_ENGINEERING_RECEIPT';r['missionAccepted']=v['missionAccepted']
 fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:
  os.write(fd,canon({'contentId':r['contentId'],'packageSha256':r['packageSha256']}));os.fsync(fd)
 finally:os.close(fd)
 put(store/(r['contentId']+'.receipt.json'),r);return r
if __name__=='__main__':
 a=sys.argv[1:]
 if a[0]=='build':r=build(*a[1:])
 elif a[0]=='inspect':r=inspect(Path(a[1]),a[2],a[3])
 elif a[0]=='receive':r=receive(Path(a[1]),a[2],a[3],Path(a[4]))
 else:raise ValueError('ACTION')
 print(json.dumps(r))
