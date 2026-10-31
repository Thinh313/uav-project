from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,time,os,stat
R=Path(__file__).resolve().parents[2];N=R/'native/runtime79';E=R/'evidence/native79';W=N/'.runtime';FLOOR=20*2**30;STOP=FLOOR+768*2**20
assert shutil.disk_usage(R).free>=32*2**30,'RUNTIME_ADMISSION_32GIB'
assert not W.exists(),'EXISTING_RUNTIME_NO_OVERWRITE'
W.mkdir();observations=[]
sources=[('emulator','https://dl.google.com/android/repository/emulator-darwin_aarch64-16428233.zip',416112708,'3af4fe44ce82b3d88ae5678a53735f27ad729c15'),('system','https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip',672331372,'69883e92b77f8705af135ee86e1d87589f8f113e')]
def gate():
 free=shutil.disk_usage(R).free;observations.append({'mono':time.monotonic(),'freeBytes':free});assert free>=STOP,'RESOURCE_STOP_HEADROOM';return free
receipts=[]
try:
 for name,url,size,expected in sources:
  gate();p=W/(name+'.zip');h=hashlib.sha1();h256=hashlib.sha256();count=0
  with urllib.request.urlopen(url,timeout=45)as response,p.open('xb')as f:
   while b:=response.read(2**20):gate();f.write(b);h.update(b);h256.update(b);count+=len(b);assert count<=size
  assert count==size and h.hexdigest()==expected,'OFFICIAL_ARCHIVE_CHECKSUM'
  with zipfile.ZipFile(p)as z:
   total=sum(i.file_size for i in z.infolist());assert total<8*2**30,'UNCOMPRESSED_BOUND';assert gate()>=FLOOR+total+2*2**30,'FULL_EXTRACTION_PLUS_AVD_MARGIN'
   for i in z.infolist():
    q=(W/i.filename).resolve();assert q.is_relative_to(W.resolve()) and not i.filename.startswith('/');mode=i.external_attr>>16;assert not stat.S_ISLNK(mode),'NO_ARCHIVE_SYMLINK'
    gate()
    if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
    q.parent.mkdir(parents=True,exist_ok=True)
    with z.open(i)as src,q.open('xb')as dst:
     while b:=src.read(2**20):gate();dst.write(b)
    if mode&0o111:os.chmod(q,0o755)
  receipts.append({'name':name,'url':url,'bytes':count,'sha1':h.hexdigest(),'sha256':h256.hexdigest(),'uncompressedBytes':total,'license':'Previously accepted android-sdk-license; no new agreement','allocation':'full extraction, no sparse assumption'})
  print(json.dumps(receipts[-1]),flush=True)
except Exception as ex:
 with(E/'provision-final-failure.json').open('x')as f:json.dump({'error':str(ex),'completed':receipts,'minimumObservedFreeBytes':min(x['freeBytes']for x in observations)},f,indent=2)
 raise
finally:
 with(E/'provision-final-observations.json').open('x')as f:json.dump({'samples':len(observations),'minimumObservedFreeBytes':min(x['freeBytes']for x in observations),'finalFreeBytes':shutil.disk_usage(R).free},f,indent=2)
with(E/'provision-final.json').open('x')as f:json.dump(receipts,f,indent=2)
