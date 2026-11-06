"""Source-bounded read-only host queries, retained once behind campaign IO."""
from pathlib import Path
import hashlib,time,re
from .metadata_budget import capture_command
class HostCommands:
 def __init__(self,root,campaign,*,budget=None):self.root=Path(root);self.campaign=campaign;self.budget=budget;self.n=0;self.last_ref=None;self.last_row=None
 def __call__(self,argv):
  from .metadata_budget import MetadataBudget
  if type(self.budget)is not MetadataBudget:raise ValueError('HOST_QUERY_EXACT_BUDGET_REQUIRED')
  with self.budget.operation({'host_queries':32768}):return self._call(argv)
 def _call(self,argv):
  self.campaign.check();start=time.monotonic_ns();remaining=min(10,(self.campaign.deadline_ns-start)/1e9)
  permitted=(len(argv)==6 and argv[:3]==['docker','image','inspect']and re.fullmatch('sha256:[a-f0-9]{64}',argv[3])is not None and argv[4:]==['--format','{{.Id}}'])or(len(argv)==5 and argv[:3]==['docker','ps','-aq']and argv[3]=='--filter'and argv[4].startswith('name=^/aeris-'))or(len(argv)==3 and argv[:2]==['docker','inspect']and argv[2].startswith('aeris-'))
  permitted=permitted or(len(argv)==5 and argv[:2]==['docker','exec']and argv[2].startswith('aeris-')and argv[3]=='sha256sum'and re.fullmatch('/proc/[1-9][0-9]*/exe',argv[4])is not None)
  permitted=permitted or(len(argv)==6 and argv[:3]==['/usr/sbin/lsof','-nP','-a']and re.fullmatch(r'-iTCP:[1-9][0-9]{0,4}',argv[3])is not None and 0<int(argv[3][6:])<=65535 and argv[4:]==['-sTCP:LISTEN','-Fpcfn'])
  if not permitted or len(str(argv))>1024:raise ValueError('READ_ONLY_HOST_QUERY_ALLOWLIST')
  if self.budget is None:raise ValueError('HOST_QUERY_EXPLICIT_BUDGET_REQUIRED')
  self.budget.tick('queries');self.n+=1;result=capture_command(self.budget,'host_queries',argv,deadline_ns=start+int(remaining*1e9),stdout_limit=16384,stderr_limit=4096);failure=result['failure']
  try:
   path=self.root/'query-output.raw';refs={}
   for name in('stdout','stderr'):
    raw=result[name];offset=path.stat().st_size if path.exists()else 0;self.budget.write('host_queries',path,raw,append=True);refs[name+'Ref']={'path':str(path),'offset':offset,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
   row={'format':'aeris-host-query','version':3,'sequence':self.n,'argv':argv,'startedHostNs':start,'finishedHostNs':time.monotonic_ns(),'exit':result['exit'],'captureComplete':result['captureComplete'],'failure':None if failure is None else type(failure).__name__+':'+str(failure),**refs}
   from .metadata_budget import encoded
   target=self.root/'queries.jsonl';offset=target.stat().st_size if target.exists()else 0;raw=encoded(row)
   self.budget.append_json('host_queries',target,row,maximum=2048);self.last_row=row;self.last_ref={'path':str(target),'offset':offset,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
  except BaseException as storage:
   primary=failure or storage
   try:self.budget.failure(primary,detail={'secondaryStorageFailure':str(storage)[:512]})
   except BaseException:primary.add_note('HOST_QUERY_FAILURE_DIAGNOSTIC_UNDURABLE')
   raise primary from storage
  if failure is not None:raise failure
  return result['stdout'].decode()
