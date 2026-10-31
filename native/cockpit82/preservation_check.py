from pathlib import Path
import hashlib,json,datetime,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82'
base=json.loads((E/'preservation-before.json').read_text());files={}
for f in base['manifestSha256']:
 raw=(R/f).read_bytes();assert hashlib.sha256(raw).hexdigest()==base['manifestSha256'][f]
 for k,v in json.loads(raw)['files'].items():
  sha=v if isinstance(v,str)else v['sha256']
  assert k not in files or files[k]==sha
  files[k]=sha
bad=[]
for name,expected in files.items():
 p=R/name
 if not p.is_file():bad.append({'path':name,'reason':'missing'});continue
 h=hashlib.sha256()
 with p.open('rb')as s:
  while b:=s.read(1024*1024):h.update(b)
 if h.hexdigest()!=expected:bad.append({'path':name,'reason':'sha'})
r={'at':datetime.datetime.now().astimezone().isoformat(),'checked':len(files),'failures':bad,'status':'PASS'if not bad else 'FAIL','scope':'Current bytes match protected manifests; no historical continuous-path-presence claim','manifestSha256':base['manifestSha256']}
assert not(E/'preservation-after.json').exists()
(E/'preservation-after.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k]for k in ['status','checked','failures']}));sys.exit(bool(bad))
