import json,hashlib,datetime,urllib.request,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/visual56'
d=json.loads((E/'outdoor-files.json').read_text());url=d['tonemapped']['url'];p=H/'assets/outdoor-background.jpg'
if p.exists():raise SystemExit('NO_OVERWRITE')
fs=os.statvfs(R)
if fs.f_bavail*fs.f_frsize<20*1024**3+100*1024**2:raise SystemExit('FLOOR')
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS-VISUAL56'}),timeout=40) as r:b=r.read(15000001)
if len(b)>15000000:raise SystemExit('BUDGET')
p.write_bytes(b);(E/'sky-background-source.json').write_text(json.dumps({'url':url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'purpose':'8K photographed background; HDRI lighting remains2K'},indent=2)+'\n');print(len(b))
