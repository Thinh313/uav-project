from pathlib import Path
import json,hashlib,time,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/native79';before=json.loads((E/'preservation-before.json').read_text());failures=[];started=time.monotonic()
for name,pin in before['files'].items():
 expected=pin['sha256']if isinstance(pin,dict)else pin;p=R/name
 if not p.is_file():failures.append({'path':name,'issue':'MISSING'});continue
 h=hashlib.sha256()
 with p.open('rb')as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 if h.hexdigest()!=expected:failures.append({'path':name,'issue':'SHA_MISMATCH','actual':h.hexdigest(),'expected':expected})
result={'status':'PASS'if not failures else'FAIL','checked':len(before['files']),'failures':failures,'seconds':time.monotonic()-started,'freeBytes':shutil.disk_usage(R).free,'basisSha256':hashlib.sha256((E/'preservation-before.json').read_bytes()).hexdigest()}
with(E/'preservation-final-after.json').open('x')as f:json.dump(result,f,indent=2)
print(json.dumps({k:result[k]for k in ['status','checked','failures','freeBytes']}));assert not failures
