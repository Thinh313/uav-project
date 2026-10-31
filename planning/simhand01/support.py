from pathlib import Path
import datetime,hashlib,json,os,platform,shutil,subprocess,stat,time,uuid
ROOT=Path(__file__).resolve().parents[2];E=ROOT/'evidence/simhand01';CONTROL=ROOT/'.local/simhand01';LOCK=CONTROL/'active';PKG='vn.rtr.aeris.simhand01';ADB=Path('/opt/homebrew/share/android-commandlinetools/platform-tools/adb')
UTC=datetime.timezone.utc
def now():return datetime.datetime.now(UTC)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def put(p,value):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def command(argv,timeout=15):
 p=subprocess.run(list(map(str,argv)),cwd=ROOT,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError('COMMAND_FAILED:'+str(argv[0])+':'+p.stderr[-1000:])
 return p.stdout.strip()
def stamp(pid):
 p=subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','args='],capture_output=True,text=True)
 return p.stdout.strip()if p.returncode==0 else None
def disk(entry=False):
 free=shutil.disk_usage(ROOT).free;minimum=20*2**30 if entry else 10*2**30+256*2**20
 if free<minimum:raise RuntimeError('DISK_ENTRY20_OR_FLOOR10_RESERVE256')
 return free
def usage():
 n=0;b=0
 if not E.exists():return{'files':0,'bytes':0}
 for root,dirs,files in os.walk(E,followlinks=False):
  for name in dirs+files:
   p=Path(root)/name
   if p.is_symlink():raise RuntimeError('OWN_OUTPUT_SYMLINK_REJECTED')
  for name in files:n+=1;b+=(Path(root)/name).stat().st_size
 if n>12000 or b>=2*2**30:raise RuntimeError('EVIDENCE12000_OR2GIB')
 return{'files':n,'bytes':b}
def verify_manifest(root=ROOT):
 p=root/'bundle-manifest.json';b=p.read_bytes();digest=hashlib.sha256(b).hexdigest();expected=(root/'bundle-manifest.sha256').read_text().strip()
 if expected!=digest:raise RuntimeError('BUNDLE_MANIFEST_SHA')
 m=json.loads(b)
 if m.get('format')!='aeris-simhand01-bundle'or m.get('version')!=1 or len(m.get('files',{}))>2000:raise RuntimeError('BUNDLE_MANIFEST_SCOPE')
 for name,v in m['files'].items():
  rel=Path(name)
  if rel.is_absolute()or'..'in rel.parts:raise RuntimeError('BUNDLE_PATH')
  f=root/rel
  if not f.is_file()or f.is_symlink()or f.stat().st_size!=v['bytes']or sha(f)!=v['sha256']:raise RuntimeError('BUNDLE_FILE_SHA:'+name)
 return digest

def budget(explicit_start=False):
 original=E/'budget.json'
 if original.is_file():
  b=json.loads(original.read_text());stop=datetime.datetime.fromisoformat(b['runtimeStopUTC']);deadline=datetime.datetime.fromisoformat(b['deadlineUTC'])
  if stop>deadline or now()>=stop:raise RuntimeError('AGENT_RUNTIME_DEADLINE_EXPIRED_NO_OVERRIDE')
  if (stop-now()).total_seconds()<60:raise RuntimeError('INSUFFICIENT_RUNTIME_CLOSURE_RESERVE')
  return original,b,False
 if not explicit_start:raise RuntimeError('RECIPIENT_EXPLICIT_SIMULATION_START_REQUIRED')
 digest=verify_manifest();policy=json.loads((ROOT/'planning/simhand01/recipient-policy.json').read_text())
 if policy['format']!='aeris-simhand01-recipient-policy'or policy['version']!=1 or not(1<=policy['hostSeconds']<=5400)or policy['apSeconds']>300:raise RuntimeError('RECIPIENT_POLICY')
 start=now();end=start+datetime.timedelta(seconds=policy['hostSeconds']);b={**policy,'task':'SIM-HANDOFF01-RECIPIENT','anchorUTC':start.isoformat(),'runtimeStopUTC':end.isoformat(),'deadlineUTC':(end+datetime.timedelta(minutes=15)).isoformat(),'sourceManifestSHA':digest,'recipientManualInvocation':True,'automaticRenewal':False}
 p=E/'session-budgets'/('budget-'+uuid.uuid4().hex+'.json');put(p,b);return p,b,True

def doctor():
 result={'format':'aeris-simhand01-doctor','version':1,'platform':platform.system()+'-'+platform.machine(),'checks':[],'downloads':False,'simulationOnly':True}
 def check(name,fn):
  try:result['checks'].append({'name':name,'status':'PASS','value':fn()})
  except Exception as e:result['checks'].append({'name':name,'status':'FAIL','error':str(e)})
 check('supportedHostDarwinArm64',lambda:result['platform']in['Darwin-arm64','Darwin-aarch64']or(_ for _ in()).throw(RuntimeError('SUPPORTED_MACOS_ARM_ONLY')))
 check('entry20GiB',lambda:disk(True));check('Node',lambda:command(['node','--version']));check('Python3.14.6',lambda:command([os.environ.get('AERIS_SIMHAND_PYTHON','python3'),'--version'])=='Python 3.14.6'or(_ for _ in()).throw(RuntimeError('CACHED_PYTHON3.14.6_NATIVE_ABI_REQUIRED')))
 check('cachedDockerImage',lambda:command(['/usr/local/bin/docker','image','inspect','rtr-aeris-sim32-trace-builder:local','--format','{{.Id}} {{.Architecture}} {{.Os}}'])=='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84 arm64 linux'or(_ for _ in()).throw(RuntimeError('EXACT_CACHED_DOCKER_IMAGE_REQUIRED')))
 check('cachedADB',lambda:ADB.is_file()or(_ for _ in()).throw(RuntimeError('ADB_NOT_CACHED')))
 deps=ROOT/'planning/simhand01/dependencies.json'
 def closure():
  d=json.loads(deps.read_text());bad=[n for n,v in d['files'].items()if not(ROOT/n).is_file()or(ROOT/n).is_symlink()or sha(ROOT/n)!=v['sha256']]
  if bad:raise RuntimeError('DEPENDENCY_DRIFT:'+str(bad[:3]))
  return{'verifiedFiles':len(d['files']),'sha256':sha(deps)}
 check('offlineDependencyClosure',closure);check('ownQuota',usage)
 if (E/'budget.json').exists():check('agentDeadline',lambda:budget()[1]['runtimeStopUTC'])
 else:check('verifiedRecipientBundle',verify_manifest)
 result['status']='PASS'if all(c['status']=='PASS'for c in result['checks'])else'FAIL';return result
