from pathlib import Path
import json,hashlib,datetime,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/native90';files={};bases=json.loads((E/'protected-manifests.json').read_text())
for f,h in bases.items():
 raw=(R/f).read_bytes();assert hashlib.sha256(raw).hexdigest()==h
 for name,v in json.loads(raw)['files'].items():
  expected=v if isinstance(v,str)else v['sha256'];assert name not in files or files[name]==expected;files[name]=expected
bad=[]
for name,expected in files.items():
 p=R/name
 if not p.is_file():bad.append({'path':name,'reason':'missing'});continue
 h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 if h.hexdigest()!=expected:bad.append({'path':name,'reason':'sha'})
r={'at':datetime.datetime.now().astimezone().isoformat(),'count':len(files),'failures':bad,'status':'PASS'if not bad else 'FAIL','scope':'Protected source/candidate/ENDURE and prior immutable receipts through NATIVE88; current bytes, no continuous-presence claim'}
(E/('preservation-'+sys.argv[1]+'.json')).open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(bool(bad))
