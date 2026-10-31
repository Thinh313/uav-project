"""Curated phone overlay. Frozen dependencies are read, pinned and never edited."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def source():
 pins=json.loads((N/'dependencies.json').read_text())['files']
 for p,s in pins.items():
  if sha((R/p).read_bytes())!=s:raise RuntimeError('FROZEN_DEPENDENCY_DRIFT:'+p)
 own={str(p.relative_to(R)):sha(p.read_bytes())for p in N.rglob('*')if p.is_file()and not any(x.startswith('.')or x in ['dist','__pycache__']for x in p.relative_to(N).parts)}
 return {**pins,**own}
def replace_once(text,a,b):
 if text.count(a)!=1:raise RuntimeError('DERIVATION_CONTEXT:'+a[:90])
 return text.replace(a,b)
def stage(target):
 source();mapping=json.loads((N/'dependencies.json').read_text())['targets']
 for logical,p in mapping.items():
  b=(R/p).read_bytes();dest=target/logical
  if logical.startswith('src/'):
   b=b.replace(b'vn.rtr.aeris.crew02',b'vn.rtr.aeris.phone06').replace(b'vn.rtr.aeris.integration03',b'vn.rtr.aeris.phone06').replace(b'crew02.aeris.invalid',b'phone06.aeris.invalid').replace(b'integration03.aeris.invalid',b'phone06.aeris.invalid')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 from derive import derive
 derive(target)
 for folder in ['src','assets']:
  for p in (N/folder).rglob('*'):
   if p.is_file():
    dest=target/folder/(p.name if folder=='src'else p.relative_to(N/'assets'));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 return source()
