from pathlib import Path
import urllib.request,zipfile,hashlib,json,shutil,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82';W=R/'.local/cockpit82-android';SDK=W/'sdk';p=W/'system.zip';total=672331372;expected='55ba9a20d473dd5351c77342016956342c40375f3e073b65a43dc9db13ccc5c6'
assert not(E/'provision02.json').exists()and not(SDK/'system-images').exists()
observations=[]
def gate():
 free=shutil.disk_usage(R).free;observations.append(free);assert free>=21*2**30;return free
prefix=p.stat().st_size;prefixSha=hashlib.sha256(p.read_bytes()).hexdigest();assert 0<prefix<total
(E/'download-resume02-before.json').write_text(json.dumps({'partialBytes':prefix,'partialSha256':prefixSha,'prefixRetained':'append only, verify prior prefix SHA and full pinned archive before extraction'},indent=2)+'\n')
try:
 req=urllib.request.Request('https://dl.google.com/android/repository/sys-img/android/arm64-v8a-33_r02.zip',headers={'Range':'bytes='+str(prefix)+'-','Accept-Encoding':'identity'})
 with urllib.request.urlopen(req,timeout=60)as response:
  assert response.status==206 and response.headers.get('Content-Range')=='bytes '+str(prefix)+'-'+str(total-1)+'/'+str(total),'EXACT_RANGE_REQUIRED'
  with p.open('ab')as f:
   while b:=response.read(1048576):gate();f.write(b);assert f.tell()<=total
 with p.open('rb')as f:assert hashlib.sha256(f.read(prefix)).hexdigest()==prefixSha
 actual=hashlib.sha256(p.read_bytes()).hexdigest();assert p.stat().st_size==total and actual==expected,'FULL_ARCHIVE_PIN'
 with zipfile.ZipFile(p)as z:
  size=sum(i.file_size for i in z.infolist());assert gate()>=20*2**30+size+8*2**30
  for i in z.infolist():
   q=(SDK/i.filename).resolve();assert q.is_relative_to(SDK.resolve())and not i.filename.startswith('/');mode=i.external_attr>>16;assert not stat.S_ISLNK(mode);gate()
   if i.is_dir():q.mkdir(parents=True,exist_ok=True);continue
   q.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i)as src,q.open('xb')as dst:
    while b:=src.read(1048576):gate();dst.write(b)
   if mode&0o111:os.chmod(q,0o755)
 at=SDK/'system-images/android-33/default';at.mkdir(parents=True);(SDK/'arm64-v8a').rename(at/'arm64-v8a');(SDK/'platform-tools').symlink_to('/opt/homebrew/share/android-commandlinetools/platform-tools',target_is_directory=True)
 (E/'provision02.json').write_text(json.dumps({'systemBytes':total,'systemSha256':actual,'resumedPrefixBytes':prefix,'resumedPrefixSha256':prefixSha,'emulatorReceipt':'provision-failure.json completed[0], original pinned SHA unchanged','uncompressedBytes':size},indent=2)+'\n');print('PASS_PINNED_RUNTIME_RESUMED')
except Exception as ex:(E/'provision02-failure.json').write_text(json.dumps({'error':str(ex)},indent=2)+'\n');raise
finally:(E/'provision02-observations.json').write_text(json.dumps({'samples':len(observations),'minFreeBytes':min(observations)if observations else None,'finalFreeBytes':shutil.disk_usage(R).free},indent=2)+'\n')
