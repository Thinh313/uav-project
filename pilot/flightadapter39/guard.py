"""Readonly historical fingerprint checking; writes only append receipts in new scope."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys
R=Path(__file__).resolve().parents[2]; H=Path(__file__).resolve().parent; E=R/'evidence/flightadapter39'
FLOOR=20*2**30; BUDGET=16*2**20; RESERVE=64*2**20
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def free():
 v=os.statvfs(R);return v.f_bavail*v.f_frsize
def append(stem,obj):
 E.mkdir(exist_ok=True);n=1
 while (E/f'{stem}{n}.json').exists():n+=1
 with (E/f'{stem}{n}.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 return E/f'{stem}{n}.json'
def endure_paths():
 s=set()
 for parent in ['evidence','pilot','.local','delivery/releases']:
  for d in (R/parent).glob('*endure*'):
   if d.is_dir():s.update(str(p.relative_to(R)) for p in d.rglob('*') if p.is_file())
 for parent in ['docs','delivery']:s.update(str(p.relative_to(R)) for p in (R/parent).glob('*ENDURE*') if p.is_file())
 return sorted(s)
def check_files(files):
 bad=[]
 for p,s in files.items():
  q=R/p;actual=sha(q) if q.is_file() else None
  if actual!=s:bad.append({'path':p,'expected':s,'actual':actual})
 return bad
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='before':
  assert not (E/'preservation-before1.json').exists(),'baseline exists; never replace'
  b=json.loads((R/'evidence/firmware38/preservation-before.json').read_text()); files=b['files'].copy()
  newer=json.loads((R/'evidence/firmware38/artifact-fingerprints.json').read_text())['files']; files.update(newer)
  for n in ['evidence/firmware38/artifact-fingerprints.json','evidence/firmware38/preservation-before.json']:files[n]=sha(R/n)
  bad=check_files(files);paths=endure_paths();assert paths==b['endureGuardPaths'],'ENDURE inventory drift'
  obj={'at':datetime.now(timezone.utc).isoformat(),'files':dict(sorted(files.items())),'failures':bad,'endureGuardPaths':paths,'freeBytes':free(),'floorBytes':FLOOR,'budgetBytes':BUDGET,'reserveBytes':RESERVE}
  p=append('preservation-before',obj);print(json.dumps({'receipt':str(p),'protectedCount':len(files),'failures':len(bad),'freeGiB':free()/2**30}));assert not bad and free()>=FLOOR+BUDGET+RESERVE
 elif mode=='after':
  b=json.loads((E/'preservation-before1.json').read_text());bad=check_files(b['files']);paths=endure_paths();allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file())
  obj={'at':datetime.now(timezone.utc).isoformat(),'protectedCount':len(b['files']),'failures':bad,'endureGuardCount':len(paths),'endureInventoryUnchanged':paths==b['endureGuardPaths'],'allocatedBytes':allocated,'freeBytes':free(),'status':'PASS' if not bad and paths==b['endureGuardPaths'] and free()>=FLOOR and allocated<BUDGET else 'FAIL'}
  p=append('preservation-after',obj);print(json.dumps({'receipt':str(p),'status':obj['status'],'protectedCount':len(b['files']),'failures':len(bad),'allocatedMiB':allocated/2**20,'freeGiB':free()/2**30}));assert obj['status']=='PASS'
 else:raise ValueError('before/after')
