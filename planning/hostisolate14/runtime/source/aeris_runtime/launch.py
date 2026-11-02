"""Product-owned simulation process boot. No task-specific baseline or operator actions."""
from pathlib import Path
import json,os,re,shutil,socket,time
from . import identity,policy
from .candidate import put
from .state_binding import prepare_fresh_case_state
from .paths import repository
from pilot.betaintegrated01.runtime.ap_stage import canonical
class SimulationLauncher:
 def __init__(self,config,root,*,image,query,check_live,now=time.monotonic_ns,sleep=time.sleep,budget=None):
  self.budget=budget;self.config=config;self.root=Path(root).resolve();self.image=image;self.query=query;self.check=check_live;self.now=now;self.sleep=sleep;self.receipt=None
 def _wait(self,resources,child,file,seconds,campaign_deadline):
  start=self.now();deadline=min(start+int(seconds*1e9),campaign_deadline)
  while not file.exists():
   self.check();resources.require_alive(child)
   if self.now()>deadline:raise TimeoutError('OWNED_'+child.upper()+'_START_DEADLINE')
   self.sleep(.05)
  raw=file.read_bytes()
  if len(raw)>262144:raise ValueError('BOOT_RECEIPT_BOUND')
  value=json.loads(raw)
  if any(value.get(k)!=self.config[k] for k in ('run','epoch','boot')):raise ValueError('BOOT_CONTEXT_MISMATCH')
  return value,{'startHostNs':start,'readyHostNs':self.now(),'gateSeconds':seconds}
 def __call__(self,resources,campaign_deadline):
  from .metadata_budget import MetadataBudget
  if type(self.budget)is not MetadataBudget:raise ValueError('LAUNCH_EXACT_GLOBAL_METADATA_BUDGET')
  self.budget.require_real_actor()
  cfg=self.config;repo=repository();identity.validate_native_selection(cfg,resources.candidate)
  if re.fullmatch('sha256:[a-f0-9]{64}',self.image)is None or self.query(['docker','image','inspect',self.image,'--format','{{.Id}}']).strip()!=self.image:raise ValueError('EXACT_CACHED_LINUX_IMAGE')
  name='aeris-'+cfg['run']
  if self.query(['docker','ps','-aq','--filter','name=^/'+name+'$']).strip():raise ValueError('OWNED_CONTAINER_ALREADY_EXISTS')
  for port,kind in [(5961,socket.SOCK_STREAM),(5962,socket.SOCK_STREAM),(5963,socket.SOCK_STREAM),(9012,socket.SOCK_DGRAM),(9014,socket.SOCK_DGRAM)]:
   with socket.socket(socket.AF_INET,kind) as s:s.bind(('127.0.0.1',port))
  self.root.mkdir(parents=True,exist_ok=True);state=self.root/'AP-state';prepare_fresh_case_state(state,cfg['caseID']);out=Path(cfg['evidence']);out.mkdir(parents=True,exist_ok=True);put(out/'run-config.json',canonical(cfg)+b'\n')
  relative=resources.candidate.relative_to(repo);container_candidate='/src/'+str(relative)
  argv=['python3','-B','-m','aeris_runtime.entry','backend','--config',str(out/'run-config.json')]
  self.check();need_budget(cfg);resources.start('backend',argv,deadline_ns=campaign_deadline,candidate_python=True)
  backend,backend_timing=self._wait(resources,'backend',out/'backend-identity.json',40,campaign_deadline)
  if backend.get('guardPrimed') is not True or backend.get('transportReady') is not True or backend.get('clockOwnerReady') is not True or any(type(backend.get(k,{}).get('elapsedRealMonotonicNs'))is not int or backend[k]['elapsedRealMonotonicNs']<15_000_000_000 for k in ('guardPriming','transportGuardPriming','clockGuardPriming')):raise ValueError('ORIGINAL3_GUARDS_REAL15S_PRIME')
  controls=(resources.candidate/'source/aeris_runtime/assets/workbench-profiles')if cfg.get('providerKind')=='WORKBENCH_SIM_V1'else(repo/'pilot/betaintegrated01/cockpit04/profiles')
  if cfg.get('providerKind')=='WORKBENCH_SIM_V1'and __import__('hashlib').sha256((controls/'nominal/control.parm').read_bytes()).hexdigest()!=cfg['parameterSHA256']['control.parm']:raise ValueError('WORKBENCH_EXACT_ORIGINAL_FAILSAFE_PARAMETERS')
  docker=['docker','run','--rm','--name',name,'--label','aeris.product=mission-runtime','--label','aeris.run='+cfg['run'],'--cpus','4','--memory','2g','--pids-limit','128','--read-only','--tmpfs','/tmp:size=16m','-p','127.0.0.1:5963:5760/tcp','-p','127.0.0.1:5962:5762/tcp','-p','127.0.0.1:9014:9004/udp','-v',str(repo)+':/src:ro','-v',str(repo/'runtime/betaintegrated01/dist')+':/candidate:ro','-v',str(controls)+':/control:ro','-v',str(out)+':/evidence:rw','-v',str(state)+':/state:rw','-w',container_candidate+'/source','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/src','-e','AERIS_REPOSITORY_ROOT=/src','-e','AERIS_CANDIDATE_DIR='+container_candidate,'-e','AERIS_CANDIDATE_SHA256='+resources.digest,self.image,'python3','-B','-m','aeris_runtime.entry','ap_supervisor','--config','/evidence/run-config.json']
  self.check();need_budget(cfg);resources.start('ap',docker,deadline_ns=campaign_deadline)
  ap,ap_timing=self._wait(resources,'ap',out/'ap-supervisor-launch.json',12,campaign_deadline)
  info=json.loads(self.query(['docker','inspect',name]))[0]
  if info['State']['Running']is not True or info['Image']!=self.image or info['Config']['Labels'].get('aeris.run')!=cfg['run']:raise ValueError('ACTUAL_OWNED_AP_CONTAINER')
  exe=self.query(['docker','exec',name,'sha256sum','/proc/'+str(ap['APPID'])+'/exe']).split()[0]
  if exe!=cfg['APSHA256']:raise ValueError('ACTUAL_AP_EXECUTABLE')
  self.receipt={'backendReady':True,'APReady':True,'backend':backend,'AP':ap,'containerImage':info['Image'],'containerID':info['Id'],'actualAPExecutableSHA256':exe,'backendTiming':backend_timing,'APTiming':ap_timing,'wholeColdStartClaimed10s':False};return self.receipt

def need_budget(config):
 budget=policy.case_budget(shutil.disk_usage(repository()).free,config['maximumSeconds'])
 if budget['admitted']is not True:raise ValueError('ORIGINAL_WHOLE_CASE_BUDGET_ENTRY_REFUSED')
 return budget
