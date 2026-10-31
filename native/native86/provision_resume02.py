"""Resume only unverified download bytes; retain attempt01 failure and require exact official full SHA before use."""
from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,os,stat,concurrent.futures,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/native86';W=R/'.local/native86-android';SDK=W/'sdk';D=W/'download02';D.mkdir();assert shutil.disk_usage(R).free>=32*2**30 and not list(SDK.iterdir());receipts=[];samples=[]
def gate():
 f=shutil.disk_usage(R).free;samples.append(f);assert f>=21*2**30,'DISK_HEADROOM';return f

def fetch(url,start,end,total,p):
 req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'});n=0;h=hashlib.sha256()
 with urllib.request.urlopen(req,timeout=60)as res,p.open('xb')as f:
  assert res.status==206 and res.headers['Content-Range']==f'bytes {start}-{end}/{total}'
  while b:=res.read(131072):gate();f.write(b);h.update(b);n+=len(b);assert n<=end-start+1
 assert n==end-start+1;return {'path':str(p.relative_to(R)),'start':start,'end':end,'bytes':n,'sha256':h.hexdigest()}

def extract(p,name,pin,total):
 assert p.stat().st_size==total and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==pin,'FULL_ARCHIVE_PIN'
 with zipfile.ZipFile(p)as z:
  expanded=sum(i.file_size for i in z.infolist());assert gate()>=20*2**30+expanded+8*2**30
  for i in z.infolist():
   q=(SDK/i.filename).resolve();assert q.is_relative_to(SDK.resolve())and not i.filename.startswith('/')and not stat.S_ISLNK(i.external_attr>>16);gate()
   if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
   q.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i)as src,q.open('xb')as dst:
    while b:=src.read(1048576):gate();dst.write(b)
   if(i.external_attr>>16)&0o111:os.chmod(q,0o755)
 if name=='system':
  dest=SDK/'system-images/android-33/default';dest.mkdir(parents=True);(SDK/'arm64-v8a').rename(dest/'arm64-v8a')
 receipts.append({'name':name,'archive':str(p.relative_to(R)),'bytes':total,'sha256':pin,'expandedBytes':expanded});print(name+' PASS_FULL_SHA',flush=True)
try:
 url='https://dl.google.com/android/repository/emulator-darwin_aarch64-16428233.zip';total=416112708;pin='f4c4a142bda54fcec064bdb32b51f19e25bae0a45ad019197ef968bf7a48979b';width=(total+2)//3;prefix=[];tails={}
 for i in range(3):
  p=W/('emulator.part'+str(i));start=i*width;end=min(total-1,(i+1)*width-1);n=p.stat().st_size;assert 0<=n<=end-start+1;prefix.append({'path':str(p.relative_to(R)),'bytes':n,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'expectedRange':[start,end]})
  if n<end-start+1:
   tail=D/('emulator-tail'+str(i));tails[i]=tail;receipts.append(fetch(url,start+n,end,total,tail))
 (E/'download02-prefixes.json').open('x').write(json.dumps(prefix,indent=2)+'\n');archive=D/'emulator.zip'
 with archive.open('xb')as out:
  for i in range(3):
   for p in [W/('emulator.part'+str(i))]+([tails[i]]if i in tails else[]):
    with p.open('rb')as src:
     while b:=src.read(1048576):gate();out.write(b)
 extract(archive,'emulator',pin,total)
 total=672331372;pin='55ba9a20d473dd5351c77342016956342c40375f3e073b65a43dc9db13ccc5c6';url='https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip';chunk=8*1024*1024;count=(total+chunk-1)//chunk
 def part(i):
  result=fetch(url,i*chunk,min(total-1,(i+1)*chunk-1),total,D/('system-chunk%03d'%i));print('system chunk '+str(i+1)+'/'+str(count),flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:chunks=list(pool.map(part,range(count)))
 (E/'download02-system-chunks.json').open('x').write(json.dumps(chunks,indent=2)+'\n');archive=D/'system.zip'
 with archive.open('xb')as out:
  for i in range(count):
   with(D/('system-chunk%03d'%i)).open('rb')as src:
    while b:=src.read(1048576):gate();out.write(b)
 extract(archive,'system',pin,total)
 (SDK/'platform-tools').symlink_to('/opt/homebrew/share/android-commandlinetools/platform-tools',target_is_directory=True)
 (E/'provision02.json').open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS_OFFICIAL_ARCHIVE_SHA','receipts':receipts},indent=2)+'\n')
except BaseException as ex:(E/'provision02-failure.json').open('x').write(json.dumps({'error':str(ex),'completed':receipts},indent=2));raise
finally:(E/'provision02-resources.json').open('x').write(json.dumps({'minFreeBytes':min(samples)if samples else None,'finalFreeBytes':shutil.disk_usage(R).free}))
