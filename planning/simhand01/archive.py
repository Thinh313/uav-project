"""Bounded engineering dependency tar. Explicit files only, no staging copy."""
from pathlib import Path
import io,json,os,sys,tarfile,stat,hashlib,datetime
from support import ROOT,E,sha,put,disk
LIMIT=512*2**20

def assemble():
 disk(True);depPath=ROOT/'planning/simhand01/dependencies.json';d=json.loads(depPath.read_text());files=dict(d['files']);files[str(depPath.relative_to(ROOT))]={'bytes':depPath.stat().st_size,'sha256':sha(depPath),'mode':0o644}
 for n in ['planning/simhand01/README.md','planning/simhand01/recipient-policy.json','planning/simhand01/source-ids.json']:
  p=ROOT/n
  if p.is_file():files[n]={'bytes':p.stat().st_size,'sha256':sha(p),'mode':stat.S_IMODE(p.stat().st_mode)}
 total=sum(v['bytes']for v in files.values());free=disk()
 if total>LIMIT or free-total-LIMIT<10*2**30+256*2**20:raise RuntimeError('BUNDLE_512MIB_OR_STAGING_RESERVE')
 manifest={'format':'aeris-simhand01-bundle','version':1,'files':files,'uncompressedBytes':total,'engineeringOnly':True,'productionSignature':False,'sourceIDs':d['sourceIDs'],'externalPrerequisites':d['externalPrerequisites'],'recipientPolicy':'planning/simhand01/recipient-policy.json','originalAgentBudgetEmbedded':False};mb=(json.dumps(manifest,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();out=ROOT/'delivery/sim-handoff01';out.mkdir(parents=True,exist_ok=True);target=out/'aeris-sim-handoff01-engineering.tar.gz';partial=out/'aeris-sim-handoff01-engineering.partial.tar.gz'
 if target.exists()or partial.exists():raise RuntimeError('ASSEMBLY_EXISTS_NO_AUTOMATIC_RETRY_OR_DELETE')
 try:
  with partial.open('xb')as raw:
   with tarfile.open(fileobj=raw,mode='w:gz',format=tarfile.PAX_FORMAT)as tf:
    for n,v in sorted(files.items()):
     p=ROOT/n
     if not p.is_file()or p.is_symlink()or p.stat().st_size!=v['bytes']or sha(p)!=v['sha256']:raise RuntimeError('DEPENDENCY_DRIFT_DURING_ASSEMBLY:'+n)
     item=tarfile.TarInfo(n);item.size=v['bytes'];item.mode=v['mode']&0o777;item.mtime=0
     with p.open('rb')as f:tf.addfile(item,f)
     if raw.tell()>LIMIT:raise RuntimeError('COMPRESSED_ARCHIVE512MIB')
    for n,b in [('bundle-manifest.json',mb),('bundle-manifest.sha256',(mh+'\n').encode())]:
     item=tarfile.TarInfo(n);item.size=len(b);item.mode=0o644;item.mtime=0;tf.addfile(item,io.BytesIO(b))
   raw.flush();os.fsync(raw.fileno())
  if partial.stat().st_size>LIMIT:raise RuntimeError('ARCHIVE512MIB')
  os.link(partial,target);partial.unlink();put(out/'assembly.json',{'status':'ASSEMBLED_NOT_RUNTIME_ACCEPTANCE','archive':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':sha(target),'manifestSHA256':mh,'fileCount':len(files),'uncompressedBytes':total,'maxCompressedBytes':LIMIT,'keysIncluded':False,'oldRawEvidenceIncluded':False});print(str(target))
 except Exception as e:put(out/'assembly-failure.json',{'status':'FAILED_RETAIN_PARTIAL','error':repr(e),'partial':str(partial.relative_to(ROOT))});raise

def inspect_unpack(archive,dest=None):
 archive=Path(archive)
 if archive.stat().st_size>LIMIT:raise RuntimeError('ARCHIVE512MIB')
 with tarfile.open(archive,'r:gz')as tf:
  members=tf.getmembers();names=[m.name for m in members]
  if len(members)>2002 or len(names)!=len(set(names)):raise RuntimeError('ARCHIVE_DUPLICATES_OR_MEMBER_BOUND')
  for m in members:
   p=Path(m.name)
   if p.is_absolute()or'..'in p.parts or not m.isfile()or m.issym()or m.islnk()or m.size>LIMIT or'\n'in m.name:raise RuntimeError('ARCHIVE_UNSAFE_MEMBER')
  mb=tf.extractfile('bundle-manifest.json').read();mh=hashlib.sha256(mb).hexdigest();expected=tf.extractfile('bundle-manifest.sha256').read().decode().strip();m=json.loads(mb)
  if mh!=expected or m['format']!='aeris-simhand01-bundle'or m['version']!=1:raise RuntimeError('MANIFEST_SHA_OR_FORMAT')
  if set(names)!=set(m['files'])|{'bundle-manifest.json','bundle-manifest.sha256'}:raise RuntimeError('ARCHIVE_EXACT_MEMBER_SET')
  if sum(v['bytes']for v in m['files'].values())>LIMIT:raise RuntimeError('UNCOMPRESSED512MIB')
  for n,v in m['files'].items():
   b=tf.extractfile(n).read()
   if len(b)!=v['bytes']or hashlib.sha256(b).hexdigest()!=v['sha256']:raise RuntimeError('MEMBER_SHA:'+n)
  if dest:
   disk(True);dest=Path(dest).resolve()
   if dest.exists():raise RuntimeError('EXCLUSIVE_RECEIVER_DESTINATION')
   dest.mkdir(parents=True)
   for member in members:
    p=dest/member.name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb')as f:f.write(tf.extractfile(member).read())
    p.chmod(member.mode&0o777)
  return{'status':'VERIFIED_ARCHIVE_BYTES_NOT_SOURCE_AUTHENTICATED','manifestSHA256':mh,'files':len(m['files']),'bytes':archive.stat().st_size,'unpacked':str(dest)if dest else None,'runtimeAcceptance':'NOT_CHECKED','sourceAuthentication':'NOT_PRODUCTION_SIGNED'}
if __name__=='__main__':
 if len(sys.argv)==2 and sys.argv[1]=='assemble':assemble()
 elif len(sys.argv)>=3 and sys.argv[1]=='verify':print(json.dumps(inspect_unpack(sys.argv[2],sys.argv[3]if len(sys.argv)>3 else None),indent=2))
 else:raise SystemExit('archive.py assemble | verify archive.tar.gz [new-destination]')
