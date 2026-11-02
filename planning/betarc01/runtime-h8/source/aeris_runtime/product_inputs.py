"""Finite read-only product input graph, separate from native APK/Python closure.
No copies, installs or actors. Asset reads must be explicitly declared; runtime
Node loader checks every file module before load against this held graph.
"""
from pathlib import Path
import hashlib,json,re
from .paths import repository,PACKAGE_ROOT
ALIASES={'planning/betasim-integrated01/product/raw-receiver.mjs':'planning/betarc01/tar_profile_h7/raw-receiver-h7.mjs','planning/nativejournal17/native-tar17.mjs':'planning/betarc01/tar_profile_h7/native-tar.mjs','planning/betasim-integrated01/product/native-tar.mjs':'planning/betarc01/tar_profile_h7/native-tar.mjs','planning/nativejournal17/native-cold17.mjs':'planning/betarc01/tar_profile_h7/native-cold-h7.mjs','pilot/apstream40/definitions.mjs':'pilot/field02/flight/vendor/apstream40-definitions.mjs','native/integration03/assets/mission-fixtures92.mjs':'native/crew02/assets/mission-fixtures92.mjs',**{'native/integration03/assets/offline94/'+n+'.mjs':'native/crew02/assets/offline94/'+n+'.mjs'for n in('auto','common','qgc','kml')}}
CONTRACT=PACKAGE_ROOT/'assets/product-input-closure.json'
PATTERN=re.compile(r'''(?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s*)(["'])([^"']+)\1''')
def need(v,name):
 if not v:raise ValueError('PRODUCT_INPUT_'+name)
def safe(name):
 need(type(name)is str and not Path(name).is_absolute()and'..'not in Path(name).parts and'\\'not in name,'RELATIVE_PATH');return name
def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def code_positions(source):
 # Only keyword starts outside comments/quoted projection strings count. The
 # runtime module loader still rejects every actually loaded unheld module.
 out=bytearray(len(source));state=None;i=0
 while i<len(source):
  c=source[i];n=source[i:i+2]
  if state in("'",'"','`'):
   if c=='\\':i+=2;continue
   if c==state:state=None
  elif state=='line':
   if c=='\n':state=None
  elif state=='block':
   if n=='*/':state=None;i+=2;continue
  elif n=='//':state='line';i+=2;continue
  elif n=='/*':state='block';i+=2;continue
  elif c in("'",'"','`'):state=c
  else:out[i]=1
  i+=1
 return out
def discover(entrypoints,read_inputs):
 repo=repository();todo=list(entrypoints);seen={};modules=[];reads=sorted(set(map(safe,read_inputs)));need(0<len(todo)<=8 and len(reads)<=512,'FINITE_ENTRY_ASSET_SET')
 while todo:
  name=safe(todo.pop());name=ALIASES.get(name,name)
  if name in seen:continue
  need(len(seen)<1024,'MODULE1024_BOUND');path=repo/name;need(not any(p.is_symlink()for p in(path,*path.parents))and path.is_file(),'MISSING_OR_SYMLINK:'+name);seen[name]=digest(path);modules.append(name)
  if path.suffix not in('.mjs','.js'):continue
  need(path.stat().st_size<=2**20,'MODULE1MIB');source=path.read_text();positions=code_positions(source)
  for match in PATTERN.finditer(source):
   if not positions[match.start()]:continue
   spec=match[2]
   if spec.startswith('node:'):continue
   if spec.startswith('.'):
    actual=(path.parent/spec).resolve();need(actual.is_relative_to(repo),'IMPORT_OUTSIDE_REPO');todo.append(str(actual.relative_to(repo)))
   elif spec.startswith('file:'):raise ValueError('PRODUCT_INPUT_DYNAMIC_FILE_URL_REQUIRES_DECLARATION:'+name)
   elif spec.startswith('data:'):raise ValueError('PRODUCT_INPUT_DATA_MODULE_NOT_ALLOWED:'+name)
   else:raise ValueError('PRODUCT_INPUT_EXTERNAL_IMPORT_NOT_DECLARED:'+name+':'+spec)
 for name in reads:
  path=repo/name;need(not any(p.is_symlink()for p in(path,*path.parents))and path.is_file(),'ASSET_MISSING_OR_SYMLINK:'+name);seen[name]=digest(path)
 return {'format':'aeris-betasim-product-readonly-closure','version':1,'entrypoints':sorted(set(entrypoints)),'readInputs':reads,'aliases':dict(ALIASES),'moduleInputs':sorted(modules),'pins':dict(sorted(seen.items())),'outsideArtifactReadOnly':True,'dynamicDataModulesAllowed':False,'claimsActualAcceptance':False}
def validate(value=None):
 value=json.loads(CONTRACT.read_bytes())if value is None else value
 need(type(value)is dict and value.get('format')=='aeris-betasim-product-readonly-closure'and value.get('version')==1,'SCHEMA');actual=discover(value['entrypoints'],value['readInputs']);need(value==actual,'EXACT_TRANSITIVE_GRAPH_OR_ASSET_DRIFT');return actual
