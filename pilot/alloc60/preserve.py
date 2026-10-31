"""Point-in-time cumulative preservation; no restoration or old evidence writes."""
from pathlib import Path
import datetime,hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]; E=R/'evidence/alloc60'
MANIFESTS=['evidence/simtrain53/preservation-before.json','evidence/simtrain53/artifact-fingerprints.json','research/ragas54/artifact-fingerprints.json','evidence/mission55/artifact-fingerprints.json','evidence/visual56/artifact-fingerprints.json','evidence/visual56/compact-ui-fingerprints.json','evidence/visual56/type-fingerprints.json','evidence/aeris57/artifact-fingerprints.json','evidence/pace58/artifact-fingerprints.json','evidence/io59/artifact-fingerprints.json']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main(label):
 E.mkdir(exist_ok=True);pins={}
 for name in MANIFESTS:
  p=R/name;pins.update(json.loads(p.read_text())['files']);pins[name]=sha(p)
 failures=[]
 for p,h in pins.items():
  try:
   actual=sha(R/p)
   if actual!=h:failures.append({'path':p,'expected':h,'actual':actual})
  except OSError as e:failures.append({'path':p,'error':str(e)})
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked':len(pins),'failures':failures,'freeBytes':shutil.disk_usage(R).free,'files':pins,'scope':'Point-in-time exact hashes; no ENDURE acceptance or continuous-path-presence claim'}
 with(E/f'preservation-{label}.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result[k]for k in ['at','checked','failures','freeBytes']}));return bool(failures)
if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
