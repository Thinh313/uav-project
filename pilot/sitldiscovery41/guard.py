from pathlib import Path
import importlib.util,json,os,sys
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/sitldiscovery41'
spec=importlib.util.spec_from_file_location('readonly_apstream_guard',R/'pilot/apstream40/guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=g.sha;free=g.free;FLOOR=20*2**30;BUDGET=32*2**20;HEADROOM=1536*2**20
def append(stem,obj):
 assert free()>=FLOOR+65536,'disk floor';E.mkdir(exist_ok=True);n=1
 while (E/f'{stem}{n}.json').exists():n+=1
 with (E/f'{stem}{n}.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 return E/f'{stem}{n}.json'
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='before':
  assert not (E/'preservation-before1.json').exists();old=json.loads((R/'evidence/apstream40/preservation-before1.json').read_text());files=old['files'].copy();files.update(json.loads((R/'evidence/apstream40/artifact-fingerprints.json').read_text())['files']);files['evidence/apstream40/artifact-fingerprints.json']=sha(R/'evidence/apstream40/artifact-fingerprints.json')
  bad=g.bad(files);assert g.endure()==old['endureGuardPaths'];p=append('preservation-before',{'at':datetime.now(timezone.utc).isoformat(),'files':dict(sorted(files.items())),'failures':bad,'endureGuardPaths':g.endure(),'freeBytes':free(),'headroomBytes':HEADROOM});print(json.dumps({'protectedCount':len(files),'failures':len(bad),'freeGiB':free()/2**30}));assert not bad and free()>=FLOOR+HEADROOM+BUDGET
 elif mode=='after':
  old=json.loads((E/'preservation-before1.json').read_text());bad=g.bad(old['files']);same=g.endure()==old['endureGuardPaths'];size=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file());o={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS' if not bad and same and free()>=FLOOR and size<BUDGET else 'FAIL','protectedCount':len(old['files']),'failures':bad,'endureGuardCount':len(g.endure()),'endureUnchanged':same,'allocatedBytes':size,'freeBytes':free()};append('preservation-after',o);print(json.dumps({k:v for k,v in o.items() if k!='failures'}));assert o['status']=='PASS'
 else:raise ValueError('before/after')
