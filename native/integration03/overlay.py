from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def source():
 pins=json.loads((N/'dependencies.json').read_text())['files']
 for p,s in pins.items():
  if sha((R/p).read_bytes())!=s:raise RuntimeError('READ_ONLY_DEPENDENCY_DRIFT:'+p)
 own={str(p.relative_to(R)):sha(p.read_bytes())for p in N.rglob('*')if p.is_file()and not any(x.startswith('.')or x in ['dist','__pycache__'] for x in p.relative_to(N).parts)}
 return {**pins,**own}
def stage(target):
 pins=json.loads((N/'dependencies.json').read_text())['files'];source()
 for p in pins:
  src=R/p;rel=Path(p).relative_to('native/crew02');dest=target/rel
  if rel.parts[0]=='src':dest=target/'src'/src.name
  dest.parent.mkdir(parents=True,exist_ok=True);b=src.read_bytes()
  if src.suffix=='.java':b=b.replace(b'vn.rtr.aeris.crew02',b'vn.rtr.aeris.integration03').replace(b'crew02.aeris.invalid',b'integration03.aeris.invalid')
  dest.write_bytes(b)
 for directory in ['src','assets']:
  for p in(N/directory).rglob('*'):
   if p.is_file():
    dest=target/directory/(p.name if directory=='src'else p.relative_to(N/'assets'));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 return source()
