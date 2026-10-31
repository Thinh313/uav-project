from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,time,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82';W=R/'.local/cockpit82-android';SDK=W/'sdk';STOP=21*2**30
assert shutil.disk_usage(R).free>=32*2**30 and not W.exists(),'ADMISSION_OR_EXISTING_RUNTIME'
SDK.mkdir(parents=True);observations=[];receipts=[]
sources=[('emulator','https://dl.google.com/android/repository/emulator-darwin_aarch64-16428233.zip',416112708,'f4c4a142bda54fcec064bdb32b51f19e25bae0a45ad019197ef968bf7a48979b'),('system','https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip',672331372,'55ba9a20d473dd5351c77342016956342c40375f3e073b65a43dc9db13ccc5c6')]
def gate():
 free=shutil.disk_usage(R).free;observations.append(free);assert free>=STOP,'DISK_HEADROOM_STOP';return free
try:
 for name,url,size,expected in sources:
  p=W/(name+'.zip');h=hashlib.sha256();count=0
  with urllib.request.urlopen(url,timeout=45)as response,p.open('xb')as f:
   while b:=response.read(1048576):gate();f.write(b);h.update(b);count+=len(b);assert count<=size
  assert count==size and h.hexdigest()==expected,'PINNED_OFFICIAL_ARCHIVE'
  with zipfile.ZipFile(p)as z:
   total=sum(i.file_size for i in z.infolist());assert total<8*2**30 and gate()>=20*2**30+total+8*2**30,'EXTRACT_AND_AVD_BUDGET'
   for i in z.infolist():
    q=(SDK/i.filename).resolve();assert q.is_relative_to(SDK.resolve())and not i.filename.startswith('/');mode=i.external_attr>>16;assert not stat.S_ISLNK(mode)
    gate()
    if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
    q.parent.mkdir(parents=True,exist_ok=True)
    with z.open(i)as src,q.open('xb')as dst:
     while b:=src.read(1048576):gate();dst.write(b)
    if mode&0o111:os.chmod(q,0o755)
  if name=='system':
   at=SDK/'system-images/android-33/default';at.mkdir(parents=True);(SDK/'arm64-v8a').rename(at/'arm64-v8a')
  receipts.append({'name':name,'url':url,'bytes':count,'sha256':h.hexdigest(),'uncompressedBytes':total,'previouslyAcceptedLicense':True});print(json.dumps(receipts[-1]),flush=True)
except Exception as ex:
 (E/'provision-failure.json').write_text(json.dumps({'error':str(ex),'completed':receipts},indent=2));raise
finally:
 (E/'provision-observations.json').write_text(json.dumps({'samples':len(observations),'minimumFreeBytes':min(observations)if observations else None,'finalFreeBytes':shutil.disk_usage(R).free},indent=2))
(SDK/'platform-tools').symlink_to('/opt/homebrew/share/android-commandlinetools/platform-tools',target_is_directory=True)
(E/'provision.json').write_text(json.dumps(receipts,indent=2)+'\n')
