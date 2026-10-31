"""Owned bounded process DAG. Only a caller with verified ground/seal may drain AP."""
from dataclasses import dataclass
from pathlib import Path
import os,signal,subprocess,time,json
from .candidate import load
from .paths import repository
@dataclass
class OwnedChild:
 name:str;process:object;argv:list;started_ns:int;stdout_path:str;stderr_path:str
class OwnedResources:
 def __init__(self,candidate_dir,digest,root,*,spawn=subprocess.Popen,now=time.monotonic_ns):
  self.candidate=Path(candidate_dir).resolve();self.manifest=load(self.candidate,digest);self.digest=digest;self.root=Path(root);self.spawn=spawn;self.now=now;self.children={};self.files=[];self.closure=None
 def start(self,name,argv,*,deadline_ns,candidate_python=False,env=None):
  if name in self.children or self.closure is not None or self.now()>deadline_ns:raise RuntimeError('RESOURCE_OWNERSHIP_START')
  self.root.mkdir(parents=True,exist_ok=True);out=self.root/(name+'.stdout.log');err=self.root/(name+'.stderr.log');a=out.open('xb');b=err.open('xb');self.files.extend([a,b]);values=dict(os.environ);values.update(env or {});values.update(AERIS_REPOSITORY_ROOT=str(repository()),AERIS_CANDIDATE_DIR=str(self.candidate),AERIS_CANDIDATE_SHA256=self.digest,PYTHONDONTWRITEBYTECODE='1')
  if candidate_python:values['PYTHONPATH']=str(repository())
  try:p=self.spawn(argv,cwd=str(self.candidate/'source') if candidate_python else str(repository()),env=values,stdout=a,stderr=b,start_new_session=True)
  except BaseException:a.close();b.close();raise
  self.children[name]=OwnedChild(name,p,list(argv),self.now(),str(out),str(err));return p.pid
 def require_alive(self,name):
  child=self.children[name];code=child.process.poll()
  if code is not None:raise RuntimeError('OWNED_CHILD_EXIT:'+name+':'+str(code)+':'+child.stderr_path)
 def drain(self,ground_proof,seal_proof,*,deadline_ns):
  if not ground_proof.get('groups') or not seal_proof.get('nativeJournalAnchor'):raise RuntimeError('DRAIN_REQUIRES_ORIGINAL_GROUND_AND_NATIVE_SEAL')
  # AP parent closes original stage pipe and obtains EOF before backend termination.
  receipt={'startedNs':self.now(),'groundProof':ground_proof,'nativeSealProof':seal_proof,'children':{},'heartbeatActorAdded':False}
  for name in ('ap','backend'):
   if name not in self.children:raise RuntimeError('OWNED_RESOURCE_MISSING:'+name)
   c=self.children[name]
   if c.process.poll() is None:os.killpg(c.process.pid,signal.SIGTERM)
   remaining=(deadline_ns-self.now())/1e9
   if remaining<=0:raise TimeoutError('OWNED_DRAIN_DEADLINE')
   code=c.process.wait(timeout=remaining);receipt['children'][name]={'pid':c.process.pid,'exit':code,'argv':c.argv,'stdout':c.stdout_path,'stderr':c.stderr_path}
  for f in self.files:f.flush();os.fsync(f.fileno());f.close()
  receipt['finishedNs']=self.now();self.closure=receipt;return receipt
 def abort_preparation(self,proof,*,deadline_ns):
  """Failed startup closes owned resources; never promotes exit to ground/pass."""
  if 'ap' in self.children:
   if proof.get('noNativeSessionSourceBound') is not True or proof.get('noNativeConnectionInOriginalCommittedRaw') is not True or len(proof.get('ground',{}).get('groups',[]))!=2:raise RuntimeError('PREPARE_AP_CLEANUP_REQUIRES_INITIAL_NOAUTHORITY_AND_RAW_GROUND')
  elif proof.get('APNeverDispatched') is not True:raise RuntimeError('PREPARE_NO_AP_OWNER_PROOF')
  receipt={'status':'FAILED_STARTUP_OWNED_DRAIN_NOT_ACCEPTANCE','proof':proof,'children':{},'startedNs':self.now()}
  for name in ('ap','backend'):
   if name not in self.children:continue
   c=self.children[name]
   if c.process.poll() is None:os.killpg(c.process.pid,signal.SIGTERM)
   remaining=(deadline_ns-self.now())/1e9
   if remaining<=0:raise TimeoutError('STARTUP_DRAIN_DEADLINE')
   receipt['children'][name]={'pid':c.process.pid,'exit':c.process.wait(timeout=remaining),'stdout':c.stdout_path,'stderr':c.stderr_path}
  for f in self.files:
   if not f.closed:f.flush();os.fsync(f.fileno());f.close()
  receipt['finishedNs']=self.now();self.closure=receipt;return receipt
