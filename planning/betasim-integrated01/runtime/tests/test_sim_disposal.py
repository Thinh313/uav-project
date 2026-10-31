"""No AP/Android processes: fake Popen state + real output pipes/budget EOF."""
from pathlib import Path
import json,os,shutil,subprocess,sys,time,types
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=ROOT.parents[2];sys.path[:0]=[str(ROOT/'source'),str(REPO)]
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.resources import OwnedChild
from aeris_runtime.owned_output import OwnedOutput
from aeris_runtime.disposal import dispose_resources,stop_owned
LAB=REPO/'evidence/betasim-integrated01/runtime/.dispose'
class P:
 def __init__(self,pid,argv,delayed=False):self.pid=pid;self.args=argv;self.code=None;self.signals=[];self.delayed=delayed
 def poll(self):return self.code
 def terminate(self):self.signals.append('TERM');self.code=None if self.delayed else -15
 def kill(self):self.signals.append('KILL');self.code=-9
 def wait(self,timeout):
  if self.code is None:raise subprocess.TimeoutExpired(self.args,timeout)
  return self.code

def make(name):
 e=LAB/name;e.mkdir(parents=True);b=MetadataBudget(e/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();root=e/'sessions/mock/processes';children={};outputs={};raw={}
 for i,n in enumerate(('ap','backend'),801):
  p=P(i,['owned-'+n]);paths={};raw[n]=b'original\x00'+n.encode()
  for channel,value in [('stdout',raw[n]),('stderr',b'')]:
   r,w=os.pipe();os.write(w,value);os.close(w);setattr(p,channel,os.fdopen(r,'rb',buffering=0));paths[channel]=root/(n+'.'+channel+'.log')
  lease=b.reserve_lease({'child_output':16384});b.bind_lease_child(lease,i);outputs[n]=OwnedOutput(b,'child_output',p,paths,maximum_each=4096,lease=lease);children[n]=OwnedChild(n,p,p.args,time.monotonic_ns(),str(paths['stdout']),str(paths['stderr']))
 return types.SimpleNamespace(manifest={'simulationOnly':True},children=children,outputs=outputs,budget=b,closure=None,_completed_closure=None),raw

def deny(fn):
 try:fn()
 except RuntimeError:return
 raise AssertionError('missing refusal')

def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  r,raw=make('positive');result=dispose_resources(r,primary_failure='FAILED_INPUT',admission_revoked=True,deadline_ns=time.monotonic_ns()+1_000_000_000);assert result['status']=='SIMULATOR_PHYSICALLY_DISPOSED_MISSION_FAILED'and result['APGroundProven']is False and result['sourceManagedDrainAccepted']is False and r.closure is None and r._completed_closure is None
  for name in r.children:assert r.children[name].process.signals==['TERM']and Path(r.children[name].stdout_path).read_bytes()==raw[name]and not r.outputs[name].thread.is_alive()
  assert not r.budget.snapshot()['inFlight'];checks.append('real-pipe-lossless-EOF-lease-release-no-ground-or-normal-closure')
  p=P(901,['owned-stuck'],delayed=True);c=OwnedChild('ap',p,p.args,time.monotonic_ns(),'out','err');s=stop_owned(c,deadline_ns=time.monotonic_ns()+1_000_000_000,mock=True);assert s['signals']==['TERM','KILL']and s['exit']==-9 and s['APGroundProven']is False;checks.append('bounded-terminal-escalation-simulator-only')
  r,_=make('noadmission');deny(lambda:dispose_resources(r,primary_failure='FAILED',admission_revoked=False,deadline_ns=time.monotonic_ns()+1_000_000_000));assert all(not c.process.signals for c in r.children.values());dispose_resources(r,primary_failure='FAILED',admission_revoked=True,deadline_ns=time.monotonic_ns()+1_000_000_000);checks.append('admission-not-revoked-denies-before-any-signal')
  r,_=make('wrongidentity');r.children['ap'].argv=['other'];result=dispose_resources(r,primary_failure='FAILED',admission_revoked=True,deadline_ns=time.monotonic_ns()+1_000_000_000);assert result['status']=='SIMULATOR_DISPOSAL_INCOMPLETE_OWNERS_RETAINED'and not r.children['ap'].process.signals and r.closure is None;checks.append('wrong-owner-identity-retained-never-normal-PASS')
  report={'status':'PASS_HOST_DISPOSAL_MOCK_NOT_ACTUAL_SHUTDOWN','groups':checks,'actualAPAndroid':False,'parentDeathActual':'NOT_RUN','guardianActual':'NOT_RUN','scratchRemoved':str(LAB)}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/disposal-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(checks)}))
if __name__=='__main__':main()
