from pathlib import Path
from datetime import datetime,timezone
import json,os,hashlib,sys
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/apstream40'
FLOOR=20*2**30;BUDGET=32*2**20
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def free():
 v=os.statvfs(R);return v.f_bavail*v.f_frsize
def append(stem,obj):
 assert free()>=FLOOR+65536,'20GiB floor'
 E.mkdir(exist_ok=True);n=1
 while (E/f'{stem}{n}.json').exists():n+=1
 with (E/f'{stem}{n}.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 return E/f'{stem}{n}.json'
def endure():
 s=set()
 for parent in ['evidence','pilot','.local','delivery/releases']:
  for d in (R/parent).glob('*endure*'):
   if d.is_dir():s.update(str(p.relative_to(R)) for p in d.rglob('*') if p.is_file())
 for parent in ['docs','delivery']:s.update(str(p.relative_to(R)) for p in (R/parent).glob('*ENDURE*') if p.is_file())
 return sorted(s)
def bad(files):
 return [{'path':p,'expected':s,'actual':sha(R/p) if (R/p).is_file() else None} for p,s in files.items() if not (R/p).is_file() or sha(R/p)!=s]
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='before':
  assert not (E/'preservation-before1.json').exists()
  prior=json.loads((R/'evidence/flightadapter39/preservation-before1.json').read_text());files=prior['files'].copy();files.update(json.loads((R/'evidence/flightadapter39/artifact-fingerprints.json').read_text())['files'])
  files['evidence/flightadapter39/artifact-fingerprints.json']=sha(R/'evidence/flightadapter39/artifact-fingerprints.json')
  failures=bad(files);assert endure()==prior['endureGuardPaths']
  p=append('preservation-before',{'at':datetime.now(timezone.utc).isoformat(),'files':dict(sorted(files.items())),'failures':failures,'endureGuardPaths':endure(),'freeBytes':free(),'budgetBytes':BUDGET})
  print(json.dumps({'receipt':str(p),'protectedCount':len(files),'failures':len(failures),'freeGiB':free()/2**30}));assert not failures and free()>=FLOOR+BUDGET+64*2**20
 elif mode=='after':
  before=json.loads((E/'preservation-before1.json').read_text());failures=bad(before['files']);allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file());same=endure()==before['endureGuardPaths']
  obj={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS' if not failures and same and free()>=FLOOR and allocated<BUDGET else 'FAIL','protectedCount':len(before['files']),'failures':failures,'endureGuardCount':len(endure()),'endureUnchanged':same,'allocatedBytes':allocated,'freeBytes':free()}
  p=append('preservation-after',obj);print(json.dumps({k:v for k,v in obj.items() if k!='failures'}));assert obj['status']=='PASS'
 else:raise ValueError('before/after')
