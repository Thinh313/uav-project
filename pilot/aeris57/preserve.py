import hashlib,json,datetime,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'evidence/aeris57';pins={}
for name in ['evidence/simtrain53/preservation-before.json','evidence/simtrain53/artifact-fingerprints.json','research/ragas54/artifact-fingerprints.json','evidence/mission55/artifact-fingerprints.json','evidence/visual56/artifact-fingerprints.json','evidence/visual56/compact-ui-fingerprints.json','evidence/visual56/type-fingerprints.json']:
 p=R/name;pins.update(json.loads(p.read_text())['files']);pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
fail=[]
for p,h in pins.items():
 try:
  actual=sha(R/p)
  if actual!=h:fail.append({'path':p,'expected':h,'actual':actual})
 except OSError as e:fail.append({'path':p,'error':str(e)})
s=os.statvfs(R);receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked':len(pins),'failures':fail,'freeBytes':s.f_bavail*s.f_frsize,'scope':'Point-in-time hashes only; prior mutable visual56 hashes superseded by ordered retained type/compact manifests; not ENDURE acceptance'}
p=E/('preservation-'+sys.argv[1]+'.json')
with p.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt));raise SystemExit(bool(fail))
