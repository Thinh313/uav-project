from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,time,os,stat,concurrent.futures
R=Path(__file__).resolve().parents[2];E=R/'evidence/native84';W=R/'.local/native84-android';SDK=W/'sdk'
assert shutil.disk_usage(R).free>=32*2**30 and not SDK.exists();SDK.mkdir(parents=True);samples=[];receipts=[]
def gate():
 f=shutil.disk_usage(R).free;samples.append(f);assert f>=21*2**30,'DISK_HEADROOM';return f
sources=[('emulator','https://dl.google.com/android/repository/emulator-darwin_aarch64-16428233.zip',416112708,'f4c4a142bda54fcec064bdb32b51f19e25bae0a45ad019197ef968bf7a48979b'),('system','https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip',672331372,'55ba9a20d473dd5351c77342016956342c40375f3e073b65a43dc9db13ccc5c6')]
try:
 for name,url,size,pin in sources:
  parts=[]
  def download(i):
   start=i*((size+2)//3);end=min(size-1,(i+1)*((size+2)//3)-1);p=W/(name+'.part'+str(i));req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'});n=0
   with urllib.request.urlopen(req,timeout=60)as res,p.open('xb')as f:
    assert res.status==206 and res.headers['Content-Range']==f'bytes {start}-{end}/{size}'
    while b:=res.read(262144):gate();f.write(b);n+=len(b);assert n<=end-start+1
   assert n==end-start+1;return p
  with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:parts=list(pool.map(download,range(3)))
  p=W/(name+'.zip');h=hashlib.sha256()
  with p.open('xb')as f:
   for part in parts:
    with part.open('rb')as src:
     while b:=src.read(1048576):gate();f.write(b);h.update(b)
  assert p.stat().st_size==size and h.hexdigest()==pin,'ARCHIVE_PIN'
  with zipfile.ZipFile(p)as z:
   total=sum(i.file_size for i in z.infolist());assert gate()>=20*2**30+total+8*2**30
   for i in z.infolist():
    q=(SDK/i.filename).resolve();assert q.is_relative_to(SDK.resolve())and not i.filename.startswith('/')and not stat.S_ISLNK(i.external_attr>>16);gate()
    if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
    q.parent.mkdir(parents=True,exist_ok=True)
    with z.open(i)as src,q.open('xb')as dst:
     while b:=src.read(1048576):gate();dst.write(b)
    if (i.external_attr>>16)&0o111:os.chmod(q,0o755)
  if name=='system':
   dest=SDK/'system-images/android-33/default';dest.mkdir(parents=True);(SDK/'arm64-v8a').rename(dest/'arm64-v8a')
  receipts.append({'url':url,'bytes':size,'sha256':pin,'uncompressed':total});print(name+' PASS_PIN',flush=True)
 (SDK/'platform-tools').symlink_to('/opt/homebrew/share/android-commandlinetools/platform-tools',target_is_directory=True)
 (E/'provision.json').open('x').write(json.dumps(receipts,indent=2))
except BaseException as ex:(E/'provision-failure.json').open('x').write(json.dumps({'error':str(ex),'completed':receipts}));raise
finally:(E/'provision-resources.json').open('x').write(json.dumps({'minFreeBytes':min(samples)if samples else None,'finalFreeBytes':shutil.disk_usage(R).free}))
