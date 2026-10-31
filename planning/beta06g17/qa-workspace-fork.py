"""Exact20-file original closed G5 data fork only; no project/authority restoration."""
from pathlib import Path
import datetime,hashlib,json,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation17';H=lambda b:hashlib.sha256(b).hexdigest();free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30
prior=json.loads((R/'evidence/beta06/generation15/workspace-copy01.json').read_bytes());rows=[]
for r in prior['files']:
 src=R/r['source'];assert src.is_file()and not src.is_symlink();data=src.read_bytes();assert len(data)==r['bytes']and H(data)==r['sha256'];rel=src.relative_to(R/'evidence/beta06/generation05/workspace01');dst=E/'workspace01'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 for p in [dst.parent,*dst.parents]:
  assert not p.is_symlink()
  if p==E:break
 fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,stat.S_IMODE(src.lstat().st_mode))
 with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert H(dst.read_bytes())==r['sha256'];rows.append({'source':r['source'],'copy':str(dst.relative_to(R)),'bytes':len(data),'sha256':H(data)})
assert len(rows)==20 and sum(r['bytes']for r in rows)==870221
for p in sorted([E/'workspace01',*(q for q in(E/'workspace01').rglob('*')if q.is_dir())],key=lambda p:len(p.parts),reverse=True):
 fd=os.open(p,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
base=E/'qa-preservation-before17.json';report={'schema':'G17_EXACT_CLOSED_WORKSPACE_COPY_V1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'EXACT_CLOSED_DATA_FORK_NOT_PROJECT_COPY','source':'evidence/beta06/generation05/workspace01','destination':'evidence/beta06/generation17/workspace01','fileCount':20,'bytes':870221,'files':rows,'baseline':{'path':str(base.relative_to(R)),'sha256':H(base.read_bytes()),'bytes':base.stat().st_size},'firstWriterRequired':{'writerLockAbsent':not(E/'workspace01/writer.lock').exists(),'exclusiveRootPermitRequired':True},'actualG17Execution':False,'noAuthorityRestoration':True,'freeBytesBeforeFork':free}
out=E/'workspace-copy01.json';b=json.dumps(report,separators=(',',':')).encode()+b'\n'
with out.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
fd=os.open(E,os.O_RDONLY)
try:os.fsync(fd)
finally:os.close(fd)
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(b),'bytes':len(b),'files':20,'dataBytes':870221,'oldWrites':0}))
