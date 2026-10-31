from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,os,stat,concurrent.futures,time,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/native86';W=R/'.local/native86-android';SDK=W/'sdk';OLD=W/'download02';D=W/'download03';D.mkdir();assert shutil.disk_usage(R).free>=32*2**30 and(SDK/'emulator/emulator').is_file()and not(SDK/'system-images').exists();receipts=[];events=[];samples=[]
def gate():
 f=shutil.disk_usage(R).free;samples.append(f);assert f>=21*2**30;return f
url='https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip';total=672331372;pin='55ba9a20d473dd5351c77342016956342c40375f3e073b65a43dc9db13ccc5c6';chunk=8*1024*1024;count=(total+chunk-1)//chunk

def part(i):
 start=i*chunk;end=min(total-1,(i+1)*chunk-1);old=OLD/('system-chunk%03d'%i)
 if old.is_file()and old.stat().st_size==end-start+1:return{'path':str(old.relative_to(R)),'start':start,'end':end,'sha256':hashlib.file_digest(old.open('rb'),'sha256').hexdigest(),'reusedUnverifiedUntilFinalSHA':True}
 for attempt in range(1,5):
  p=D/('system-chunk%03d-try%d'%(i,attempt));n=0
  try:
   req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
   with urllib.request.urlopen(req,timeout=45)as res,p.open('xb')as f:
    assert res.status==206 and res.headers['Content-Range']==f'bytes {start}-{end}/{total}'
    while b:=res.read(131072):gate();f.write(b);n+=len(b);assert n<=end-start+1
   assert n==end-start+1;h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();print('system '+str(i+1)+'/'+str(count),flush=True);return{'path':str(p.relative_to(R)),'start':start,'end':end,'sha256':h,'bytes':n}
  except Exception as ex:
   events.append({'chunk':i,'attempt':attempt,'bytes':n,'error':str(ex),'pathRetained':str(p.relative_to(R))});print('download transient chunk '+str(i)+' attempt '+str(attempt),flush=True)
   if attempt==4:raise
   time.sleep(2)
try:
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:parts=list(pool.map(part,range(count)))
 (E/'download03-chunks.json').open('x').write(json.dumps(parts,indent=2)+'\n');archive=D/'system.zip';h=hashlib.sha256()
 with archive.open('xb')as out:
  for q in parts:
   with(R/q['path']).open('rb')as src:
    while b:=src.read(1048576):gate();out.write(b);h.update(b)
 assert archive.stat().st_size==total and h.hexdigest()==pin,'FULL_OFFICIAL_ARCHIVE_SHA'
 with zipfile.ZipFile(archive)as z:
  expanded=sum(i.file_size for i in z.infolist());assert gate()>=20*2**30+expanded+8*2**30
  for i in z.infolist():
   q=(SDK/i.filename).resolve();assert q.is_relative_to(SDK.resolve())and not i.filename.startswith('/')and not stat.S_ISLNK(i.external_attr>>16);gate()
   if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
   q.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i)as src,q.open('xb')as dst:
    while b:=src.read(1048576):gate();dst.write(b)
   if(i.external_attr>>16)&0o111:os.chmod(q,0o755)
 dest=SDK/'system-images/android-33/default';dest.mkdir(parents=True);(SDK/'arm64-v8a').rename(dest/'arm64-v8a');(SDK/'platform-tools').symlink_to('/opt/homebrew/share/android-commandlinetools/platform-tools',target_is_directory=True)
 emulator=OLD/'emulator.zip';epin='f4c4a142bda54fcec064bdb32b51f19e25bae0a45ad019197ef968bf7a48979b';assert hashlib.file_digest(emulator.open('rb'),'sha256').hexdigest()==epin
 out={'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS_OFFICIAL_ARCHIVE_SHA','emulator':{'archive':str(emulator.relative_to(R)),'bytes':416112708,'sha256':epin},'system':{'archive':str(archive.relative_to(R)),'bytes':total,'sha256':pin,'expandedBytes':expanded},'downloadFailuresRetained':events};(E/'provision03.json').open('x').write(json.dumps(out,indent=2)+'\n');print('READY_EXACT_OFFICIAL_SHA',flush=True)
except BaseException as ex:(E/'provision03-failure.json').open('x').write(json.dumps({'error':str(ex),'events':events},indent=2));raise
finally:(E/'provision03-resources.json').open('x').write(json.dumps({'minFreeBytes':min(samples)if samples else None,'finalFreeBytes':shutil.disk_usage(R).free,'transientEvents':events},indent=2))
