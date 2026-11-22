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
 def _wait_forwarder(self,resources,campaign_deadline):
  """runtime-l18 (team): wait for the JSON forwarder's ready line, read from its own captured stdout."""
  from .json_forwarder import ready_line
  start=self.now();deadline=min(start+5_000_000_000,campaign_deadline);log=Path(resources.children['forwarder'].stdout_path)
  while True:
   self.check();resources.require_alive('forwarder')
   value=ready_line(log.read_bytes()if log.exists()else b'',self.config)
   if value is not None:return value,{'startHostNs':start,'readyHostNs':self.now(),'gateSeconds':5}
   if self.now()>deadline:raise TimeoutError('OWNED_FORWARDER_START_DEADLINE')
   self.sleep(.05)
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
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:s.bind(FORWARDER_LISTEN_L18)
  self.root.mkdir(parents=True,exist_ok=True);state=self.root/'AP-state'
  if cfg.get('readOnlyBootProbeRC01')is not None:
   from .state_binding import prepare_readonly_probe_state
   prepare_readonly_probe_state(state,cfg)
  else:prepare_fresh_case_state(state,cfg['caseID'])
  out=Path(cfg['evidence']);out.mkdir(parents=True,exist_ok=True);put(out/'run-config.json',canonical(cfg)+b'\n')
  relative=resources.candidate.relative_to(repo);container_candidate='/src/'+str(relative)
  argv=['python3','-B','-m','aeris_runtime.entry','backend','--config',str(out/'run-config.json')]
  self.check();need_budget(cfg);resources.start('backend',argv,deadline_ns=campaign_deadline,candidate_python=True)
  backend,backend_timing=self._wait(resources,'backend',out/'backend-identity.json',40,campaign_deadline)
  if backend.get('guardPrimed') is not True or backend.get('transportReady') is not True or backend.get('clockOwnerReady') is not True or any(type(backend.get(k,{}).get('elapsedRealMonotonicNs'))is not int or backend[k]['elapsedRealMonotonicNs']<15_000_000_000 for k in ('guardPriming','transportGuardPriming','clockGuardPriming')):raise ValueError('ORIGINAL3_GUARDS_REAL15S_PRIME')
  controls=(resources.candidate/'source/aeris_runtime/assets/workbench-profiles')if cfg.get('providerKind')=='WORKBENCH_SIM_V1'else(repo/'pilot/betaintegrated01/cockpit04/profiles')
  if cfg.get('providerKind')=='WORKBENCH_SIM_V1'and __import__('hashlib').sha256((controls/'nominal/control.parm').read_bytes()).hexdigest()!=cfg['parameterSHA256']['control.parm']:raise ValueError('WORKBENCH_EXACT_ORIGINAL_FAILSAFE_PARAMETERS')
  forwarder_argv=['python3','-B','-m','aeris_runtime.entry','json_forwarder','--config',str(out/'run-config.json')]
  self.check();need_budget(cfg);resources.start('forwarder',forwarder_argv,deadline_ns=campaign_deadline,candidate_python=True)
  forwarder,forwarder_timing=self._wait_forwarder(resources,campaign_deadline)
  docker=['docker','run','--rm','--name',name,'--label','aeris.product=mission-runtime','--label','aeris.run='+cfg['run'],'--cpus','4','--memory','2g','--pids-limit','128','--read-only','--tmpfs','/tmp:size=16m','-p','127.0.0.1:5963:5760/tcp','-p','127.0.0.1:5962:5762/tcp','-p','127.0.0.1:9014:9004/udp','-v',str(repo)+':/src:ro','-v',str(repo/'runtime/betaintegrated01/dist')+':/candidate:ro','-v',str(controls)+':/control:ro','-v',str(out)+':/evidence:rw','-v',str(state)+':/state:rw','-w',container_candidate+'/source','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/src','-e','AERIS_REPOSITORY_ROOT=/src','-e','AERIS_CANDIDATE_DIR='+container_candidate,'-e','AERIS_CANDIDATE_SHA256='+resources.digest,self.image,'python3','-B','-m','aeris_runtime.entry','ap_supervisor','--config','/evidence/run-config.json']
  self.check();need_budget(cfg);resources.start('ap',docker,deadline_ns=campaign_deadline)
  ap,ap_timing=self._wait(resources,'ap',out/'ap-supervisor-launch.json',12,campaign_deadline)
  info=json.loads(self.query(['docker','inspect',name]))[0]
  if info['State']['Running']is not True or info['Image']!=self.image or info['Config']['Labels'].get('aeris.run')!=cfg['run']:raise ValueError('ACTUAL_OWNED_AP_CONTAINER')
  proof_l18=ap_identity_l18(self.query,name,ap,cfg)
  self.receipt={'backendReady':True,'APReady':True,'backend':backend,'AP':ap,'containerImage':info['Image'],'containerID':info['Id'],**proof_l18,'forwarder':forwarder,'forwarderTiming':forwarder_timing,'backendTiming':backend_timing,'APTiming':ap_timing,'wholeColdStartClaimed10s':False};return self.receipt

AP_ARTIFACT_L18='/candidate/arducopter-m1-stagepipe-03';BINFMT_INTERPRETER_L18='/usr/libexec/qemu-binfmt/aarch64-binfmt-P'
EMULATOR_SHA256_L18='e4f8d99e9ff69c3cefffab71cee358ce2af1ecba1282d04c3eeb44ef76f5a71e';FORWARDER_LISTEN_L18=('172.17.0.1',9012)
def ap_identity_l18(query,name,ap,cfg):
 """runtime-l18 (team decisions "Option (a): keep key" and "Yes, pin qemu", not the owner's). Under ARM user
 emulation /proc/<pid>/exe is the emulator, so the AP is identified by the artifact the process has mapped. Returns
 the receipt fields only if the executable is the pinned emulator, cmdline is the binfmt interpreter plus the AP
 path plus the recorded AP command, the AP file has the pinned SHA-256 and every maps line naming the AP file has
 exactly that path (one at offset 0). The harness's own exe query comes first and the maps query last."""
 def refuse(reason):raise ValueError('ACTUAL_AP_MAPPED_ARTIFACT_L18:'+reason)
 pid=ap.get('APPID');command=ap.get('command')
 if type(pid)is not int or pid<=0 or type(command)is not list or not command or any(type(v)is not str for v in command)or command[0]!=AP_ARTIFACT_L18:refuse('LAUNCH_RECORD')
 proc='/proc/'+str(pid)
 emulator=query(['docker','exec',name,'sha256sum',proc+'/exe']).split()[:1]
 if emulator!=[EMULATOR_SHA256_L18]:refuse('PINNED_EMULATOR_SHA256')
 path=query(['docker','exec',name,'readlink',proc+'/exe']).rstrip('\n')
 if query(['docker','exec',name,'sha256sum',AP_ARTIFACT_L18]).split()[:1]!=[cfg['APSHA256']]:refuse('ARTIFACT_SHA256')
 raw=query(['docker','exec',name,'cat',proc+'/cmdline'])
 if not raw.endswith('\0')or raw[:-1].split('\0')!=[BINFMT_INTERPRETER_L18,AP_ARTIFACT_L18,*command]:refuse('CMDLINE')
 lines=query(['docker','exec',name,'grep','-F',AP_ARTIFACT_L18,proc+'/maps']).splitlines();rows=[line.split(None,5)for line in lines]
 if not 0<len(rows)<=16 or any(len(row)!=6 or row[5]!=AP_ARTIFACT_L18 for row in rows)or not any(row[2]=='00000000'for row in rows):refuse('MAPS')
 return {'actualAPExecutableSHA256':cfg['APSHA256'],'APIdentityMethod':'ARM_USER_EMULATION_MAPPED_ARTIFACT_L18','emulatorExecutablePath':path,'emulatorExecutableSHA256':emulator[0],'APCmdline':raw[:-1].split('\0'),'APMappedArtifactLines':lines}

def need_budget(config):
 budget=policy.case_budget(shutil.disk_usage(repository()).free,config['maximumSeconds'])
 if budget['admitted']is not True:raise ValueError('ORIGINAL_WHOLE_CASE_BUDGET_ENTRY_REFUSED')
 return budget
