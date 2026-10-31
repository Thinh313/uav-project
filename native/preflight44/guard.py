from pathlib import Path
import importlib.util,json,sys
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/native44'
spec=importlib.util.spec_from_file_location('old40guard',R/'pilot/apstream40/guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=g.sha;free=g.free;FLOOR=20*2**30;BUDGET=32*2**20;HEADROOM=1536*2**20

def put(stem,obj):
 assert free()>FLOOR+65536;E.mkdir(exist_ok=True);n=1
 while (E/f'{stem}{n}.json').exists():n+=1
 with (E/f'{stem}{n}.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 return E/f'{stem}{n}.json'
def check():
 old=json.loads((E/'preservation-before1.json').read_text());bad=g.bad(old['files']);same=g.endure()==old['endureGuardPaths'];allocated=sum(p.stat().st_blocks*512 for d in [H,E,R/'.local/native44'] if d.exists() for p in d.rglob('*') if p.is_file());assert not bad and same and free()>=FLOOR and allocated<BUDGET
 return {'protectedCount':len(old['files']),'failures':bad,'endureUnchanged':same,'endureCount':len(g.endure()),'allocatedBytes':allocated,'freeBytes':free()}
if __name__=='__main__':
 if sys.argv[1]=='before':
  assert not (E/'preservation-before1.json').exists();prior=json.loads((R/'evidence/preflight43/preservation-before1.json').read_text());files=prior['files'].copy();files.update(json.loads((R/'evidence/preflight43/artifact-fingerprints.json').read_text())['files']);files['evidence/preflight43/artifact-fingerprints.json']=sha(R/'evidence/preflight43/artifact-fingerprints.json');bad=g.bad(files);assert not bad and g.endure()==prior['endureGuardPaths'] and free()>=FLOOR+BUDGET+64*2**20
  put('preservation-before',{'at':datetime.now(timezone.utc).isoformat(),'files':dict(sorted(files.items())),'endureGuardPaths':g.endure(),'freeBytes':free()});print(json.dumps({'protectedCount':len(files),'failures':len(bad),'freeGiB':free()/2**30}))
 elif sys.argv[1]=='after':
  obj=check();put('preservation-after',obj);print(json.dumps(obj))
