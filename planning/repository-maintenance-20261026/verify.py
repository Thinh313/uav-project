"""Read-only staged-source checks; writes a fresh host-local QA receipt only."""
from pathlib import Path
import ast,concurrent.futures,datetime,hashlib,json,os,re,stat,subprocess,time,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/repository-maintenance-20261026'
sha=lambda b:hashlib.sha256(b).hexdigest()
def run(*a):return subprocess.check_output(a,cwd=R)
names=[n.decode()for n in run('git','diff','--cached','--name-only','--diff-filter=AM','-z').split(b'\0')if n]
assert not run('git','diff','--cached','--name-only','--diff-filter=D','-z'),'UNEXPECTED_STAGED_DELETION'
missing=[n.decode()for n in run('git','diff','--name-only','--diff-filter=D','-z').split(b'\0')if n];assert len(missing)==97
blocked=[];secrets=[];pyErrors=[];safeLinks=[]
patterns={'private-key':rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----','github-token':rb'(?<![A-Za-z0-9_-])gh[pousr]_[A-Za-z0-9]{30,}','github-pat':rb'(?<![A-Za-z0-9_-])github_pat_[A-Za-z0-9_]{40,}','aws-access-id':rb'(?<![A-Za-z0-9_-])AKIA[0-9A-Z]{16}','openai-key':rb'(?<![A-Za-z0-9_-])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}'}
for n in names:
 p=R/n
 if p.is_symlink():
  target=os.readlink(p);resolved=p.resolve()
  if Path(target).is_absolute()or not resolved.is_relative_to(R)or not resolved.is_file()or str(resolved.relative_to(R))not in names:blocked.append(n)
  else:safeLinks.append({'path':n,'target':target,'resolvedSource':str(resolved.relative_to(R))})
 if any(v in p.parts for v in ['.stage','.build','__pycache__','node_modules','.local'])or n.startswith(('runtime/','evidence/endure'))or p.suffix in ['.apk','.keystore','.jks','.pem','.key','.zip','.gz','.pyc','.class']:blocked.append(n)
 b=p.read_bytes()
 if b'\x00'not in b:
  for k,pattern in patterns.items():
   if re.search(pattern,b):secrets.append({'path':n,'kind':k})
 if p.suffix=='.py':
  try:ast.parse(b,filename=n)
  except SyntaxError as e:pyErrors.append({'path':n,'line':e.lineno,'message':e.msg})
js=[n for n in names if Path(n).suffix in ['.mjs','.js']]
def check(n):
 q=subprocess.run(['node','--check',n],cwd=R,capture_output=True,text=True,timeout=20)
 return None if q.returncode==0 else {'path':n,'returncode':q.returncode,'diagnostic':q.stderr[-600:]}
start=time.monotonic();jsErrors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:
 for i,result in enumerate(ex.map(check,js),1):
  if result:jsErrors.append(result)
  if i%400==0:print(json.dumps({'checkedJS':i,'of':len(js),'errors':len(jsErrors)}),flush=True)
overlay=R/'snapshots/simstability03';o=json.loads((overlay/'overlay.json').read_text());overlayDrift=[]
for v in o['changes']:
 b=(overlay/v['path']).read_bytes();base=(R/v['path']).read_bytes()
 if sha(b)!=v['sha256']or len(b)!=v['bytes']or sha(base)!=v['baseCheckoutSHA256']:overlayDrift.append(v['path'])
assert sha((overlay/'source-bundle-manifest.json').read_bytes())==o['sourceManifestSHA256']
legacyPath=R/'evidence/coach01/preservation-missionbeta01-after.json';legacy=json.loads(legacyPath.read_text());legacyDrift=[]
def identity(p):
 if not p.exists()and not p.is_symlink():return {'kind':'MISSING'}
 s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';v={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind=='REGULAR_FILE':v.update(bytes=s.st_size,sha256=sha(p.read_bytes()),mtimeNs=str(s.st_mtime_ns))
 if kind=='SYMLINK':
  v['linkTarget']=os.readlink(p)
  if p.is_file():v.update(targetBytes=p.stat().st_size,sha256=sha(p.read_bytes()))
 return v
for n,v in legacy['observed'].items():
 if identity(R/n)!=v:legacyDrift.append(n)
sealPath=R/'evidence/simstability03/handoff-final01.json';seal=json.loads(sealPath.read_text());sealDrift=[]
for n,v in seal['inventory'].items():
 p=R/n
 if not p.is_file()or p.is_symlink()or p.stat().st_size!=v['bytes']or sha(p.read_bytes())!=v['sha256']:sealDrift.append(n)
q={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if not(blocked or secrets or pyErrors or jsErrors or overlayDrift or legacyDrift or sealDrift)else'FAIL','stagedSourceDocuments':len(names),'stagedBytes':sum((R/n).stat().st_size for n in names),'jsSyntaxChecked':len(js),'pythonASTChecked':sum(Path(n).suffix=='.py'for n in names),'jsSyntaxErrors':jsErrors,'pythonASTErrors':pyErrors,'excludedArtifactViolations':blocked,'secretPatternFindings':secrets,'secretScanLimit':'Heuristic named patterns only; not an exhaustive security audit','overlayFilesChecked':len(o['changes']),'overlayDrift':overlayDrift,'protectedLegacyIdentities':len(legacy['observed']),'preexistingMissingOverall':len(legacy['entryMissing']),'legacyDrift':legacyDrift,'priorTaskSealEntries':len(seal['inventory']),'priorTaskSealSHA256':sha(sealPath.read_bytes()),'priorTaskSealDrift':sealDrift,'trackedMissingUnstaged':missing,'stagedDeletions':0,'runtimeTestsRun':False,'productReadiness':'NOT_INFERRED_FROM_STATIC_OR_GIT_CHECKS','elapsedSeconds':time.monotonic()-start}
tag=sys.argv[1]if len(sys.argv)>1 else'01';assert re.fullmatch('[0-9]{2}',tag);q['safeRelativeSourceLinks']=safeLinks
(E/('verification'+tag+'.json')).open('x').write(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items()if k not in ['trackedMissingUnstaged']},indent=2));assert q['status']=='PASS','QA_FINDINGS_RETAINED'
