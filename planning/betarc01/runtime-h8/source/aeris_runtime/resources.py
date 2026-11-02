"""Owned bounded process DAG. Only a caller with verified ground/seal may drain AP."""
from dataclasses import dataclass
from pathlib import Path
import os,signal,subprocess,time,json
from .candidate import load
from .cleanup import finish_cleanup
from .paths import repository
_REAL_POPEN=subprocess.Popen
@dataclass
class OwnedChild:
 name:str;process:object;argv:list;started_ns:int;stdout_path:str;stderr_path:str
class OwnedResources:
 def __init__(self,candidate_dir,digest,root,*,spawn=subprocess.Popen,now=time.monotonic_ns,budget=None):
  self.candidate=Path(candidate_dir).resolve();self.manifest=load(self.candidate,digest);self.digest=digest;self.root=Path(root);self.spawn=spawn;self.now=now;self.children={};self.files=[];self.outputs={};self.output_leases={};self.budget=budget;self.closure=None;self._completed_closure=None;self.scene_pipe=None
 def enable_scene(self,context,raw_root,source_binding):
  if self.scene_pipe is not None or self.children:raise ValueError('SCENE_BEFORE_ANY_CHILD_ONLY')
  from .scene_channel import ScenePipeReader
  readfd,writefd=os.pipe();reader=ScenePipeReader(readfd,context,raw_root,source_binding);reader.start();self.scene_pipe={'reader':reader,'writeFD':writefd,'backendDispatched':False};return reader
 def start(self,name,argv,*,deadline_ns,candidate_python=False,env=None):
  from .metadata_budget import MetadataBudget
  if name not in('ap','backend')or type(self.budget)is not MetadataBudget:raise ValueError('SOURCE_OWNED_PROCESS_AND_BUDGET_REQUIRED')
  if self.spawn is _REAL_POPEN:self.budget.require_real_actor()
  if name in self.children or self.closure is not None or self.now()>deadline_ns:raise RuntimeError('RESOURCE_OWNERSHIP_START')
  out=self.root/(name+'.stdout.log');err=self.root/(name+'.stderr.log');values=dict(os.environ);values.update(env or {});values.update(AERIS_METADATA_BUDGET=str(self.budget.root),AERIS_REPOSITORY_ROOT=str(repository()),AERIS_CANDIDATE_DIR=str(self.candidate),AERIS_CANDIDATE_SHA256=self.digest,AERIS_RUNTIME_OWNER_PID=str(os.getpid()),PYTHONDONTWRITEBYTECODE='1')
  if candidate_python:values['PYTHONPATH']=str(repository())
  self.budget.tick('children')
  lease=self.budget.reserve_lease({'child_output':2*500*1024+16384});self.output_leases[name]=lease
  pass_fds=()
  if name=='backend'and self.scene_pipe is not None:
   if self.scene_pipe['backendDispatched']:raise ValueError('SCENE_ONE_BACKEND_FD_OWNER')
   values['AERIS_SCENE_SOURCE_BINDING']=json.dumps(self.scene_pipe['reader'].source_binding,separators=(',',':'));values['AERIS_SCENE_FD']=str(self.scene_pipe['writeFD']);values['AERIS_SCENE_CONTEXT']=json.dumps(self.scene_pipe['reader'].context,separators=(',',':'));pass_fds=(self.scene_pipe['writeFD'],);self.scene_pipe['backendDispatched']=True
  spawn_args={'cwd':str(self.candidate/'source')if candidate_python else str(repository()),'env':values,'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'start_new_session':True}
  if pass_fds:spawn_args['pass_fds']=pass_fds
  try:p=self.spawn(argv,**spawn_args)
  except BaseException as error:
   try:self.budget.release_lease(lease)
   except BaseException:pass
   try:self.budget.failure(error)
   except BaseException:error.add_note('OWNED_SPAWN_FAILURE_DIAGNOSTIC_UNDURABLE')
   raise
  if pass_fds:os.close(self.scene_pipe['writeFD']);self.scene_pipe['writeFD']=None
  self.children[name]=OwnedChild(name,p,list(argv),self.now(),str(out),str(err))
  self.budget.bind_lease_child(lease,p.pid)
  try:
   from .owned_output import OwnedOutput
   self.outputs[name]=OwnedOutput(self.budget,'child_output',p,{'stdout':out,'stderr':err},maximum_each=500*1024,lease=lease)
  except BaseException as primary:
   try:self.budget.failure(primary,detail={'childTracked':True,'pid':p.pid,'captureSetupFailed':True})
   except BaseException:primary.add_note('OWNED_CAPTURE_SETUP_DIAGNOSTIC_UNDURABLE')
   raise
  return p.pid
 def close_scene(self):
  if self.scene_pipe is None:return None
  if self.scene_pipe['writeFD']is not None:os.close(self.scene_pipe['writeFD']);self.scene_pipe['writeFD']=None
  return self.scene_pipe['reader'].close()
 def require_alive(self,name):
  if name not in self.outputs:raise RuntimeError('OWNED_OUTPUT_SETUP_FAILED_OWNERSHIP_RETAINED')
  self.outputs[name].check();child=self.children[name];code=child.process.poll()
  if code is not None:raise RuntimeError('OWNED_CHILD_EXIT:'+name+':'+str(code)+':'+child.stderr_path)
 def drain(self,ground_proof,seal_proof,*,deadline_ns):
  if not ground_proof.get('groups') or not seal_proof.get('nativeJournalAnchor'):raise RuntimeError('DRAIN_REQUIRES_ORIGINAL_GROUND_AND_NATIVE_SEAL')
  return self._drain_proven(ground_proof,seal_proof,deadline_ns=deadline_ns,seal_kind='nativeSealProof')
 def drain_workbench(self,ground_proof,seal_proof,*,deadline_ns):
  if seal_proof.get('format')!='aeris-root-verified-workbench-seal'or seal_proof.get('authorityRevoked')is not True or seal_proof.get('providerClosed')is not True or seal_proof.get('journalClosed')is not True or seal_proof.get('runtimeContext',{}).get('run')!=self.root.parent.name or not __import__('re').fullmatch('[a-f0-9]{64}',str(seal_proof.get('productJournalSHA256'))):raise RuntimeError('WORKBENCH_DRAIN_REQUIRES_ORIGINAL_PROVIDER_SEAL')
  if not ground_proof.get('groups'):raise RuntimeError('WORKBENCH_DRAIN_REQUIRES_ORIGINAL_GROUND')
  return self._drain_proven(ground_proof,seal_proof,deadline_ns=deadline_ns,seal_kind='workbenchSealProof')
 def _drain_proven(self,ground_proof,seal_proof,*,deadline_ns,seal_kind):
  # AP parent closes original stage pipe and obtains EOF before backend termination.
  receipt={'startedNs':self.now(),'groundProof':ground_proof,seal_kind:seal_proof,'children':{},'heartbeatActorAdded':False}
  for name in ('ap','backend'):
   if name not in self.children:raise RuntimeError('OWNED_RESOURCE_MISSING:'+name)
   c=self.children[name];dispatch=self.now()
   if type(dispatch)is not int or dispatch>=deadline_ns:raise TimeoutError('OWNED_DRAIN_DEADLINE_BEFORE_STOP')
   if name=='ap':self._fresh_ground_at_dispatch(ground_proof,dispatch)
   if c.process.poll() is None:os.killpg(c.process.pid,signal.SIGTERM)
   remaining=(deadline_ns-self.now())/1e9
   if remaining<=0:raise TimeoutError('OWNED_DRAIN_DEADLINE')
   code=c.process.wait(timeout=remaining);receipt['children'][name]={'pid':c.process.pid,'exit':code,'argv':c.argv,'stdout':c.stdout_path,'stderr':c.stderr_path}
  finish_cleanup([item for f in self.files for item in[('legacy-flush',f.flush),('legacy-fsync',lambda f=f:os.fsync(f.fileno())),('legacy-close',f.close)]])
  if set(self.outputs)!=set(self.children):raise RuntimeError('OWNED_OUTPUT_SETUP_FAILED_OWNERSHIP_RETAINED')
  receipt['outputCapture']={name:output.close()for name,output in self.outputs.items()}
  if self.scene_pipe is not None:receipt['sceneObserver']=self.close_scene()
  receipt['finishedNs']=self.now();self.closure=receipt;self._completed_closure=receipt;return receipt
 def _fresh_ground_at_dispatch(self,proof,dispatch):
  groups=proof.get('groups');clock=proof.get('currentProofHostNs');context=proof.get('context')
  if type(groups)is not list or len(groups)!=2 or type(clock)is not int or not 0<=dispatch-clock<=1_500_000_000 or type(context)is not dict or context.get('run')!=self.root.parent.name:raise RuntimeError('DRAIN_FRESH_ORIGINAL_GROUND_CONTEXT')
  for group in groups:
   if type(group)is not dict or set(group)!={'heartbeat','landed','position'}or any(type(v)is not dict or type(v.get('hostNs'))is not int or not 0<=v['hostNs']<=dispatch for v in group.values()):raise RuntimeError('DRAIN_GROUND_GROUP_SCHEMA')
  latest=groups[-1];h=latest['heartbeat'];l=latest['landed'];p=latest['position']
  if any(dispatch-v['hostNs']>1_500_000_000 for v in latest.values())or h.get('armed')is not False or type(l.get('landedState'))is not int or l['landedState']!=1 or type(p.get('relativeAltitudeMm'))is not int or abs(p['relativeAltitudeMm'])>400:raise RuntimeError('DRAIN_STALE_ARMED_OR_NOT_GROUNDED_KEEP_OWNERSHIP')
 def completed_closure(self):
  """Only this owner's completed managed receipt may discharge live ownership."""
  receipt=self.closure
  if receipt is None or receipt is not getattr(self,'_completed_closure',None) or type(receipt)is not dict:raise RuntimeError('NO_ORIGINAL_COMPLETED_OWNED_DRAIN')
  start=receipt.get('startedNs');finish=receipt.get('finishedNs');now=self.now();children=receipt.get('children')
  if any(type(v)is not int for v in(start,finish,now))or not 0<=start<=finish<=now or type(children)is not dict or set(children)!=set(self.children):raise RuntimeError('OWNED_DRAIN_RECEIPT_CONTEXT_OR_CLOCK')
  for name,child in self.children.items():
   row=children[name];code=child.process.poll()
   if type(row)is not dict or type(row.get('pid'))is not int or row['pid']!=child.process.pid or type(row.get('exit'))is not int or type(code)is not int or row['exit']!=code or child.started_ns>start:raise RuntimeError('OWNED_DRAIN_RECEIPT_PID_EXIT_OR_LIVENESS')
  return receipt
 def abort_preparation(self,proof,*,deadline_ns):
  """Failed startup closes owned resources; never promotes exit to ground/pass."""
  if self.closure is not None:return self.completed_closure()
  if 'ap' in self.children:
   fence=proof.get('ingressFence',{});ground=proof.get('ground',{});closed=fence.get('closedRef',{})
   if proof.get('noNativeSessionSourceBound')is not True or proof.get('noNativeConnectionInOriginalCommittedRaw')is not True or len(ground.get('groups',[]))!=2 or fence.get('format')!='aeris-failed-preowner-ingress-fence' or type(fence.get('version'))is not int or fence['version']!=1 or fence.get('nativeConnectionEverSeen')is not False or fence.get('nativeBytesEverSeen')is not False or fence.get('pendingForwardEverSeen')is not False or fence.get('nativeReconnectAllowed')is not False or fence.get('FDMClockUntouched')is not True or type(closed.get('closedHostNs'))is not int or ground.get('afterHostNs')!=closed['closedHostNs'] or ground.get('committedPrefix')!=fence.get('committedPrefix'):raise RuntimeError('PREPARE_AP_CLEANUP_REQUIRES_FENCED_INITIAL_NOAUTHORITY_RAW_GROUND')
  elif proof.get('APNeverDispatched') is not True:raise RuntimeError('PREPARE_NO_AP_OWNER_PROOF')
  receipt={'status':'FAILED_STARTUP_OWNED_DRAIN_NOT_ACCEPTANCE','proof':proof,'children':{},'startedNs':self.now()}
  for name in ('ap','backend'):
   if name not in self.children:continue
   c=self.children[name];dispatch=self.now()
   if type(dispatch)is not int or dispatch>=deadline_ns:raise TimeoutError('STARTUP_DRAIN_DEADLINE_BEFORE_STOP')
   if name=='ap':
    proof_clock=ground.get('currentProofHostNs');groups=ground['groups']
    if any(type(group)is not dict or set(group)!={'heartbeat','landed','position'} or any(type(v)is not dict for v in group.values())for group in groups):raise RuntimeError('PREOWNER_GROUND_GROUP_SCHEMA_AT_AP_STOP')
    if ground.get('context')!=fence.get('context') or type(proof_clock)is not int or not 0<=dispatch-proof_clock<=1_500_000_000 or any(type(v.get('hostNs'))is not int or not closed['closedHostNs']<=v['hostNs']<=dispatch for group in groups for v in group.values()) or any(dispatch-v['hostNs']>1_500_000_000 for v in groups[-1].values()):raise RuntimeError('PREOWNER_GROUND_STALE_OR_CONTEXT_AT_AP_STOP')
   if c.process.poll() is None:os.killpg(c.process.pid,signal.SIGTERM)
   remaining=(deadline_ns-self.now())/1e9
   if remaining<=0:raise TimeoutError('STARTUP_DRAIN_DEADLINE')
   receipt['children'][name]={'pid':c.process.pid,'exit':c.process.wait(timeout=remaining),'stdout':c.stdout_path,'stderr':c.stderr_path}
  finish_cleanup([item for f in self.files if not f.closed for item in[('legacy-flush',f.flush),('legacy-fsync',lambda f=f:os.fsync(f.fileno())),('legacy-close',f.close)]])
  if set(self.outputs)!=set(self.children):raise RuntimeError('OWNED_OUTPUT_SETUP_FAILED_OWNERSHIP_RETAINED')
  receipt['outputCapture']={name:output.close()for name,output in self.outputs.items()}
  if self.scene_pipe is not None:receipt['sceneObserver']=self.close_scene()
  receipt['finishedNs']=self.now();self.closure=receipt;self._completed_closure=receipt;return receipt
