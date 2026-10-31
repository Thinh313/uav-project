import datetime,hashlib,json,sys,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'evidence/visual56';E.mkdir(exist_ok=True);pins={}
for name in ['evidence/simtrain53/preservation-before.json','evidence/simtrain53/artifact-fingerprints.json','research/ragas54/artifact-fingerprints.json','evidence/mission55/artifact-fingerprints.json']:
 p=R/name;pins.update(json.loads(p.read_text())['files']);pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
bad=[]
for name,h in pins.items():
 try:
  x=hashlib.sha256()
  with (R/name).open('rb') as f:
   for b in iter(lambda:f.read(1024**2),b''):x.update(b)
  if x.hexdigest()!=h:bad.append(name)
 except OSError:bad.append(name)
fs=os.statvfs(R);d={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked':len(pins),'failures':bad,'freeBytes':fs.f_bavail*fs.f_frsize,'scope':'Point-in-time SHA; not ENDURE acceptance or continuous presence'}
p=E/('preservation-'+sys.argv[1]+'.json')
if p.exists():raise SystemExit('No receipt overwrite')
p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d));sys.exit(bool(bad))
