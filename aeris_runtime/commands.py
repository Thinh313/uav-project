"""Bounded retained host read/inspection commands for the fixed product launcher."""
from pathlib import Path
import subprocess,time,re
from .candidate import put
from pilot.betaintegrated01.runtime.ap_stage import canonical
class HostCommands:
 def __init__(self,root,campaign):self.root=Path(root);self.campaign=campaign;self.n=0
 def __call__(self,argv):
  self.campaign.check();self.n+=1;start=time.monotonic_ns();remaining=min(10,(self.campaign.deadline_ns-start)/1e9)
  permitted=(len(argv)==6 and argv[:3]==['docker','image','inspect'] and re.fullmatch('sha256:[a-f0-9]{64}',argv[3]) is not None and argv[4:]==['--format','{{.Id}}']) or (len(argv)==5 and argv[:3]==['docker','ps','-aq'] and argv[3]=='--filter' and argv[4].startswith('name=^/aeris-')) or (len(argv)==3 and argv[:2]==['docker','inspect'] and argv[2].startswith('aeris-'))
  # Actual dockerexec SHA command has five arguments; no arbitrary executable.
  permitted=permitted or (len(argv)==5 and argv[:2]==['docker','exec'] and argv[2].startswith('aeris-') and argv[3]=='sha256sum' and re.fullmatch('/proc/[1-9][0-9]*/exe',argv[4]) is not None)
  if not permitted:raise ValueError('READ_ONLY_HOST_QUERY_ALLOWLIST')
  try:p=subprocess.run(argv,capture_output=True,timeout=remaining)
  except subprocess.TimeoutExpired as e:
   put(self.root/('query-%04d.json'%self.n),canonical({'argv':argv,'startedHostNs':start,'finishedHostNs':time.monotonic_ns(),'timeout':True,'stdoutHex':(e.stdout or b'')[:131072].hex(),'stderrHex':(e.stderr or b'')[:131072].hex()})+b'\n');raise
  row={'argv':argv,'startedHostNs':start,'finishedHostNs':time.monotonic_ns(),'exit':p.returncode,'stdoutHex':p.stdout[:131072].hex(),'stderrHex':p.stderr[:131072].hex(),'truncated':len(p.stdout)>131072 or len(p.stderr)>131072};put(self.root/('query-%04d.json'%self.n),canonical(row)+b'\n')
  if p.returncode or row['truncated']:raise RuntimeError('RETAINED_HOST_QUERY_FAILED:'+str(self.n))
  return p.stdout.decode()
