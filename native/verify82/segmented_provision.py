from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,os,stat,time,concurrent.futures,threading
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82-emulator04';W=R/'.local/cockpit82-android';SDK=W/'sdk';p=W/'system.zip';TOTAL=672331372;PIN='55ba9a20d473dd5351c77342016956342c40375f3e073b65a43dc9db13ccc5c6';URL='https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip'
parts=W/'download-parts03';assert not parts.exists()and not(E/'provision03.json').exists()and not(SDK/'system-images').exists();parts.mkdir();prefix=p.stat().st_size;prefixSha=hashlib.sha256(p.read_bytes()).hexdigest();assert 0<prefix<TOTAL;lock=threading.Lock();samples=[];receipts=[];began=time.monotonic()
def gate():
 free=shutil.disk_usage(R).free
 with lock:samples.append(free)
 assert free>=21*2**30,'DISK_HEADROOM';return free
def part(i,start,end):
 name=parts/('part'+str(i)+'.bin');h=hashlib.sha256();n=0;t=time.monotonic();request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
 with urllib.request.urlopen(request,timeout=60)as response,name.open('xb')as f:
  assert response.status==206 and response.headers.get('Content-Range')==f'bytes {start}-{end}/{TOTAL}','EXACT_HTTP_RANGE'
  while b:=response.read(262144):gate();f.write(b);h.update(b);n+=len(b);assert n<=end-start+1
 assert n==end-start+1;row={'index':i,'start':start,'end':end,'bytes':n,'sha256':h.hexdigest(),'seconds':time.monotonic()-t};(E/('download-part03-'+str(i)+'.json')).open('x').write(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True);return row
(E/'download03-before.json').open('x').write(json.dumps({'prefixBytes':prefix,'prefixSha256':prefixSha,'parts':3,'noPrefixRewrite':True,'priorResume':'User-task-controlled SIGINT to improve throughput; prior partial bytes kept','url':URL},indent=2)+'\n')
try:
 count=TOTAL-prefix;span=(count+2)//3;ranges=[(i,prefix+i*span,min(TOTAL-1,prefix+(i+1)*span-1))for i in range(3)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:receipts=list(ex.map(lambda x:part(*x),ranges))
 assert p.stat().st_size==prefix and hashlib.sha256(p.read_bytes()).hexdigest()==prefixSha
 with p.open('ab')as dst:
  for row in receipts:
   partfile=parts/('part'+str(row['index'])+'.bin');assert hashlib.sha256(partfile.read_bytes()).hexdigest()==row['sha256']
   with partfile.open('rb')as src:
    while b:=src.read(1048576):gate();dst.write(b)
  dst.flush();os.fsync(dst.fileno())
 assert p.stat().st_size==TOTAL and hashlib.sha256(p.read_bytes()).hexdigest()==PIN,'FULL_PIN_REQUIRED'
 with p.open('rb')as f:assert hashlib.sha256(f.read(prefix)).hexdigest()==prefixSha
 with zipfile.ZipFile(p)as z:
  uncompressed=sum(i.file_size for i in z.infolist());assert gate()>=20*2**30+uncompressed+8*2**30
  for i in z.infolist():
   q=(SDK/i.filename).resolve();assert q.is_relative_to(SDK.resolve())and not i.filename.startswith('/');mode=i.external_attr>>16;assert not stat.S_ISLNK(mode);gate()
   if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
   q.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i)as src,q.open('xb')as dst:
    while b:=src.read(1048576):gate();dst.write(b)
   if mode&0o111:os.chmod(q,0o755)
 at=SDK/'system-images/android-33/default';at.mkdir(parents=True);(SDK/'arm64-v8a').rename(at/'arm64-v8a');(SDK/'platform-tools').symlink_to('/opt/homebrew/share/android-commandlinetools/platform-tools',target_is_directory=True)
 (E/'provision03.json').open('x').write(json.dumps({'status':'PASS_PINNED_RUNTIME','systemBytes':TOTAL,'systemSha256':PIN,'retainedPrefixBytes':prefix,'retainedPrefixSha256':prefixSha,'parts':receipts,'uncompressedBytes':uncompressed,'elapsedSeconds':time.monotonic()-began},indent=2)+'\n');print('PASS_PINNED_RUNTIME',flush=True)
except Exception as ex:(E/'provision03-failure.json').open('x').write(json.dumps({'error':str(ex),'partialPartsRetained':True},indent=2)+'\n');raise
finally:(E/'provision03-resources.json').open('x').write(json.dumps({'minFreeBytes':min(samples)if samples else None,'finalFreeBytes':shutil.disk_usage(R).free,'elapsedSeconds':time.monotonic()-began},indent=2)+'\n')
