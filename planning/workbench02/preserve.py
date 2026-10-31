from pathlib import Path
import json,hashlib,os,stat,sys,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/workbench02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30+1048576
ref='evidence/workbench01/preservation-before.json';rows=read(ref)['snapshot'];matched=0
for n,v in rows.items():
 p=R/n;s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';a={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind!='DIRECTORY':a.update(bytes=len(p.read_bytes()),sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
 if kind=='SYMLINK':a['linkTarget']=os.readlink(p)
 assert a==v,n;matched+=1
manifest='evidence/workbench01/handoff-manifest.json';m=read(manifest)
for n,v in m['files'].items():assert (R/n).stat().st_size==v['bytes']and sha(R/n)==v['sha256'],n
for n,h in {**m['frozenReferences'],**m['reusePins'],**m['fontPins']}.items():assert sha(R/n)==h,n
refs={n:sha(R/n)for n in [ref,manifest]};native={}
for prefix in ['native/native94/assets/offline94','native/native94/assets/mission92.mjs','native/native94/assets/mission-fixtures92.mjs','native/field02/src/Integrity02.java']:
 p=R/prefix
 for f in ([p]if p.is_file()else p.rglob('*')):
  if f.is_file():native[str(f.relative_to(R))]=sha(f)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','protectedIdentities':matched,'workbench01Files':len(m['files']),'references':refs,'nativeReuse':native,'freeBytes':free,'provenance':'Prior missing95 and restoration incidents remain; no whole repo/continuous presence claim.'}
if sys.argv[1]!='before':
 b=read('evidence/workbench02/preservation-before.json');assert b['references']==refs and b['nativeReuse']==native
with (E/('preservation-'+sys.argv[1]+'.json')).open('x')as f:json.dump(result,f,indent=2)
print(json.dumps(result))
