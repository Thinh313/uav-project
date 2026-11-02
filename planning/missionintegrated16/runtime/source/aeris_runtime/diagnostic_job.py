"""Explicit bounded Root companion stdout/stderr; never owns flight authority."""
from pathlib import Path
import subprocess,time
from .metadata_budget import MetadataBudget,encoded
from .owned_output import OwnedOutput
_REAL_POPEN=subprocess.Popen
class DiagnosticJob:
 def __init__(self,budget,prefix,*,spawn=subprocess.Popen):
  if type(budget)is not MetadataBudget:raise ValueError('DIAGNOSTIC_EXACT_BUDGET')
  self.budget=budget;self.prefix=Path(prefix);self.spawn=spawn;self.process=None;self.output=None;self.lease=None;self.result=None
 def start(self,argv):
  if self.process is not None:raise ValueError('DIAGNOSTIC_ONE_START')
  if self.spawn is _REAL_POPEN:self.budget.require_real_actor()
  if type(argv)is not list or not all(type(v)is str for v in argv)or len(encoded(argv))>4096:raise ValueError('DIAGNOSTIC_ARGV4KiB')
  self.budget.tick('diagnosticChildren');self.lease=self.budget.reserve_lease({'external_task':2*16384+16384});self.started=time.monotonic_ns()
  try:self.process=self.spawn(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  except BaseException:
   self.budget.release_lease(self.lease);self.lease=None;raise
  # Object is constructed before start: ownership survives capture setup errors.
  self.budget.bind_lease_child(self.lease,self.process.pid)
  self.output=OwnedOutput(self.budget,'external_task',self.process,{'stdout':self.prefix/'stdout','stderr':self.prefix/'stderr'},maximum_each=16384,lease=self.lease)
  with self.budget.use_lease(self.lease):self.budget.append_json('external_task',self.prefix/'launch.json',{'format':'aeris-diagnostic-child','version':3,'pid':self.process.pid,'argv':argv,'startedHostNs':self.started,'noAuthorityDischarge':True},maximum=8192)
  return self.process.pid
 def wait(self,deadline_ns):
  if self.result is not None:return self.result
  if self.process is None:raise ValueError('DIAGNOSTIC_NOT_STARTED')
  seconds=(deadline_ns-time.monotonic_ns())/1e9
  if seconds<=0:raise TimeoutError('DIAGNOSTIC_OWNER_RETAINED_DEADLINE')
  # No timeout/overflow shortcut terminates a runtime owner or asserts ground.
  code=self.process.wait(timeout=seconds);capture=self.output.close();self.lease=None
  self.result={'format':'aeris-diagnostic-child-close','version':3,'pid':self.process.pid,'exit':code,'startedHostNs':self.started,'finishedHostNs':time.monotonic_ns(),'capture':capture,'noAuthorityDischarge':True}
  self.budget.append_json('external_task',self.prefix/'close.json',self.result,maximum=4096)
  return self.result
