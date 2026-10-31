"""M0 bounded static source inventory. Does not import or execute product code.

Direct relative ESM imports and new URL literals are resolved. Rooted literal
file paths are conservative reference edges, not proof of runtime reachability.
Dynamic projections, Python execution and asset routers are classified explicitly.
"""
from pathlib import Path
from collections import deque,Counter
import ast,datetime,hashlib,json,os,re,stat,subprocess,time
R=Path(__file__).resolve().parents[4];P=R/'planning/betaintegrated01/m0/dependencies';E=R/'evidence/betaintegrated01-m0/dependencies'
HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
tracked={p.decode()for p in subprocess.check_output(['git','ls-files','-z'],cwd=R).split(b'\0')if p}
missing={p.decode()for p in subprocess.check_output(['git','diff','--name-only','--diff-filter=D','-z'],cwd=R).split(b'\0')if p}
roots=['native/native98/src','native/native98/assets','pilot/workbench01','pilot/workbench02','pilot/missionbeta01','pilot/betavideo03']
sourceExt={'.mjs','.js','.py','.java','.html','.css','.json','.xml','.txt','.md','.parm','.yaml','.yml','.c','.h','.ttf','.webm','.png','.jpg','.glb','.hdr'}
seeds=['native/native98/build.py','native/native98/AndroidManifest.xml','native/native98/runtime98.py','native/native98/peers98.mjs']
for root in roots:
 seeds.extend(str(p.relative_to(R))for p in sorted((R/root).rglob('*'))if p.is_file()and p.suffix in sourceExt and not any(v in p.parts for v in ['.build','dist','__pycache__','.stage']))
overlay=json.loads((R/'snapshots/simstability03/overlay.json').read_text())
seeds.extend('snapshots/simstability03/'+v['path']for v in overlay['changes'])
queue=deque(dict.fromkeys(seeds));queued=set(queue);files={};edges=[];unresolved=[];dynamic=[];intake=[];external=[];started=time.monotonic();copyBytes=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def recordEdge(src,line,kind,raw,target=None):edges.append({'from':src,'line':line,'kind':kind,'literal':raw,'target':target})
def get(n,required=False):
 global copyBytes
 p=R/n
 if p.is_file():
  resolved=p.resolve()
  if not resolved.is_relative_to(R):raise RuntimeError('EXTERNAL_SYMLINK:'+n)
  return p.read_bytes(),'WORKING_CHECKOUT'
 if n in missing and n in tracked:
  body=subprocess.check_output(['git','show',HEAD+':'+n],cwd=R);blob=subprocess.check_output(['git','rev-parse',HEAD+':'+n],cwd=R).decode().strip()
  assert copyBytes+len(body)<=8*2**20,'INTAKE8MIB'
  dest=P/'intake'/n;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.open('xb').write(body);copyBytes+=len(body);intake.append({'originalMissingPath':n,'intakePath':str(dest.relative_to(R)),'bytes':len(body),'sha256':sha(body),'gitCommit':HEAD,'gitBlob':blob,'operation':'EXACT_BYTES_TO_NEW_ISOLATED_INTAKE_ONLY','originalPathRestored':False})
  return body,'GIT_HEAD_EXACT_INTAKE'
 if required:unresolved.append({'path':n,'status':'MISSING_SOURCE_NOT_RECONSTRUCTED'})
 return None,None
def add(src,line,kind,raw,path,required=True):
 p=Path(path)
 try:n=str(p.resolve().relative_to(R))
 except ValueError:external.append({'from':src,'line':line,'kind':kind,'literal':raw,'status':'OUTSIDE_CHECKOUT_REFERENCE_NOT_READ'});return
 recordEdge(src,line,kind,raw,n)
 if n in queued:return
 if (R/n).is_file()or n in tracked:
  queued.add(n);queue.append(n)
 elif (R/n).is_dir():unresolved.append({'from':src,'line':line,'path':n,'status':'DIRECTORY_SELECTION_REQUIRES_MANIFEST_NOT_EXPANDED'})
 elif required:unresolved.append({'from':src,'line':line,'path':n,'status':'MISSING_LITERAL_OR_GENERATED_ROUTE_REQUIRES_ADAPTATION'})
literalRoots='(?:app|native|pilot|services|tools|media|payload|reference|hardware|geodata|runtime|evidence|deployment|sot)'
rootPattern=re.compile(r"(['\"])("+literalRoots+r"/[A-Za-z0-9_./-]+\.[A-Za-z0-9_-]+)\1")
relativePattern=re.compile(r"\b(?:import|export)\s+(?:[^;\n]*?\bfrom\s*)?(['\"])(\.[^'\"]+)\1")
urlPattern=re.compile(r"new\s+URL\(\s*(['\"])(\.[^'\"]+)\1\s*,\s*import\.meta\.url")
while queue:
 assert time.monotonic()-started<300,'ANALYSIS300S';assert len(files)<5000,'SOURCE5000_BOUND'
 n=queue.popleft();b,origin=get(n,True)
 if b is None:continue
 p=R/n;files[n]={'bytes':len(b),'sha256':sha(b),'origin':origin,'kind':'BINARY_ASSET'if b'\0'in b else'SOURCE_OR_TEXT_REFERENCE','selectedForExecution':False,'inventoryMeaning':'CONSERVATIVE_SOURCE_REFERENCE_UNION_NOT_EXECUTABLE_RELEASE_CLOSURE'}
 if b'\0'in b or p.suffix not in {'.mjs','.js','.py','.java','.html','.css','.json','.xml'}:continue
 text=b.decode('utf-8',errors='replace');lines=text.splitlines()
 if p.suffix in {'.mjs','.js'}:
  for pattern,kind in [(relativePattern,'STATIC_RELATIVE_ESM'),(urlPattern,'RELATIVE_IMPORT_META_URL')]:
   for m in pattern.finditer(text):add(n,text.count('\n',0,m.start())+1,kind,m[2],p.parent/m[2])
  for m in re.finditer(r"\bimport\(\s*(['\"])([^'\"]+)\1",text):
   if m[2].startswith('.'):add(n,text.count('\n',0,m.start())+1,'LITERAL_DYNAMIC_IMPORT',m[2],p.parent/m[2])
   else:dynamic.append({'path':n,'line':text.count('\n',0,m.start())+1,'kind':'NON_RELATIVE_DYNAMIC_IMPORT','literal':m[2][:180],'executableSelection':'NOT_SELECTED_NEEDS_ADAPTER_REVIEW'})
 for m in rootPattern.finditer(text):
  path=m[2]
  if path.startswith('evidence/'):
   recordEdge(n,text.count('\n',0,m.start())+1,'EVIDENCE_RECEIPT_OR_OUTPUT_REFERENCE',path,path);continue
  if path.startswith('runtime/'):
   recordEdge(n,text.count('\n',0,m.start())+1,'EXTERNAL_RUNTIME_ARTIFACT_OR_OUTPUT_REFERENCE',path,path);continue
  add(n,text.count('\n',0,m.start())+1,'ROOTED_LITERAL_CONSERVATIVE_REFERENCE',path,R/path,False)
 for lineNo,line in enumerate(lines,1):
  kinds=[]
  if re.search(r'\bexec\(|\bcompile\(|types\.ModuleType',line):kinds.append('PYTHON_DYNAMIC_EXEC_OR_COMPILE')
  if 'data:text/javascript' in line:kinds.append('RUNTIME_JS_PROJECTION_IMPORT')
  if any(x in line for x in ['source.replace','s.replace(','s.replaceAll(','source=source.replace','source.replaceAll']):kinds.append('TEXT_PROJECTION_REQUIRES_PIN_AND_INVERSE_REVIEW')
  if any(x in line for x in ['.rglob(','.copytree(',"copytree("]):kinds.append('DIRECTORY_BUILD_SELECTION_OR_COPY_NOT_EXECUTED')
  if any(x in line for x in ['development.p12','--ks-pass','K/\'password\'']):kinds.append('PRIVATE_SIGNING_MATERIAL_REFERENCE_NOT_READ')
  for k in kinds:dynamic.append({'path':n,'line':lineNo,'kind':k,'executableSelection':'NOT_SELECTED_NEEDS_EXPLICIT_NEW_BUILD_OR_ADAPTER'})
 # AST imports resolve only existing sibling Python files. stdlib/third-party left external.
 if p.suffix=='.py':
  try:tree=ast.parse(text,filename=n)
  except SyntaxError as ex:unresolved.append({'path':n,'line':ex.lineno,'status':'PYTHON_SYNTAX_ERROR','message':ex.msg});continue
  for a in ast.walk(tree):
   if isinstance(a,(ast.Import,ast.ImportFrom)):
    names=[v.name for v in a.names]if isinstance(a,ast.Import)else[a.module or'']
    for name in names:
     candidate=p.parent/(name.replace('.','/')+'.py')
     if candidate.is_file():add(n,a.lineno,'PYTHON_SIBLING_IMPORT',name,candidate)
     else:external.append({'from':n,'line':a.lineno,'kind':'PYTHON_IMPORT_STDLIB_THIRDPARTY_OR_SYSPATH','literal':name,'status':'NOT_IMPORTED_OR_EXECUTED'})
counts=Counter(d['kind']for d in dynamic)
requiredMissing=[v for v in intake]
missingClassification=[]
for n in sorted(missing):
 role='SELECTED_REFERENCE_DEPENDENCY_INTAKE'if any(v['originalMissingPath']==n for v in intake)else'HISTORICAL_EVIDENCE_OR_ASSET_NOT_SELECTED_BY_STATIC_REFERENCE_UNION'
 if n.startswith('sot/source_canonical/'):role='CANONICAL_SOURCE_NOT_RESTORED_NOT_EXECUTABLE_DEPENDENCY'
 missingClassification.append({'path':n,'classification':role,'originalPathRestored':False})
q={'format':'aeris-beta-m0-static-dependency-audit','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceCommit':HEAD,'status':'SOURCE_REFERENCE_UNION_PINNED_NOT_EXECUTABLE_CLOSURE','method':'Bounded static direct ESM/newURL + conservative rooted literals + sibling Python imports. All Java src/assets inventoried. Dynamic exec/text projection/route-generated imports explicitly unproven. Product code never imported/executed.','sourceRoots':roots,'seeds':sorted(set(seeds)),'files':files,'sourceFiles':len(files),'sourceBytes':sum(v['bytes']for v in files.values()),'edges':edges,'edgeCount':len(edges),'dynamicReferences':dynamic,'dynamicCounts':dict(counts),'unresolvedOrGeneratedSelections':unresolved,'externalReferences':external,'intake':intake,'intakeBytes':copyBytes,'missingTrackedPaths':missingClassification,'missingTrackedCount':len(missing),'allOriginalMissingRemainMissing':all(not(R/n).exists()for n in missing),'rootedLiteralEdgesProveRuntimeReachability':False,'selectedReleaseExecutableCount':0,'runtimeLaunches':0,'builds':0,'installations':0,'signatures':0,'privateKeyRead':False,'planningDisposition':'Native98-derived source is selected for adaptation, not existing binary reuse. Do not call complete live closure until runtime projections/ABI/provider/routing contracts are explicitly materialized and audited in isolated M1 build.'}
for target in [E/'source-reference-union01.json',P/'source-reference-union.json']:
 target.open('x').write(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:q[k]for k in ['status','sourceFiles','sourceBytes','edgeCount','dynamicCounts','intakeBytes','missingTrackedCount','allOriginalMissingRemainMissing']},indent=2));print('intake',q['intake']);print('unresolved',len(unresolved))
