"""One original campaign clock across at most three immutable integration attempts."""
from pathlib import Path
import json,time
from .candidate import put,load
from pilot.betaintegrated01.runtime.ap_stage import canonical
class Campaign:
 def __init__(self,path,*,now=time.monotonic_ns):
  self.path=Path(path);self.now=now;self.receipt=json.loads(self.path.read_bytes())
  if set(self.receipt)!={'format','version','startedHostNs','maximumSeconds','maximumAttempts'} or self.receipt['format']!='aeris-mission-campaign' or type(self.receipt['version']) is not int or self.receipt['version']!=1 or type(self.receipt['startedHostNs']) is not int or self.receipt['startedHostNs']<0 or type(self.receipt['maximumSeconds']) is not int or self.receipt['maximumSeconds']!=5400 or type(self.receipt['maximumAttempts']) is not int or self.receipt['maximumAttempts']!=3:raise ValueError('ORIGINAL_CAMPAIGN_CLOCK')
  self.deadline_ns=self.receipt['startedHostNs']+5400_000_000_000
 def check(self):
  n=self.now()
  if not self.receipt['startedHostNs']<=n<=self.deadline_ns:raise TimeoutError('ORIGINAL_5400S_CAMPAIGN_DEADLINE')
 def attempt(self,candidate,digest):
  self.check();m=load(candidate,digest);root=self.path.parent/'attempts';root.mkdir(exist_ok=True)
  present=list(root.glob('attempt-*.json'))
  if len(present)>=3:raise RuntimeError('MAXIMUM3_IMMUTABLE_ATTEMPTS')
  if any(json.loads(p.read_bytes()).get('candidateSHA256')==digest for p in present):raise ValueError('SAME_CANDIDATE_ALREADY_DISPATCHED_NO_RETRY_ATTEMPT')
  n=len(present)+1;receipt={'format':'aeris-mission-attempt','version':1,'candidateSHA256':digest,'candidatePath':str(Path(candidate).resolve()),'ordinal':n,'startedHostNs':self.now(),'originalCampaignStartedNs':self.receipt['startedHostNs'],'originalDeadlineNs':self.deadline_ns,'oldIntervalsCredited':False};path=root/('attempt-%02d.json'%n);put(path,canonical(receipt)+b'\n');return {**receipt,'path':str(path)}

 def case(self,attempt_path,candidate_digest,context):
  self.check();path=Path(attempt_path).resolve();root=(self.path.parent/'attempts').resolve()
  if path.parent!=root or not path.is_file():raise ValueError('ACTUAL_CANDIDATE_ATTEMPT_RECEIPT')
  attempt=json.loads(path.read_bytes())
  if attempt.get('candidateSHA256')!=candidate_digest or attempt.get('originalCampaignStartedNs')!=self.receipt['startedHostNs'] or attempt.get('originalDeadlineNs')!=self.deadline_ns:raise ValueError('CASE_ORIGINAL_CANDIDATE_ATTEMPT_CLOCK')
  cases=root/(path.stem+'-cases');cases.mkdir(exist_ok=True);existing=list(cases.glob('case-*.json'))
  if len(existing)>=4:raise RuntimeError('NOMINAL_SHORT_LONG_AND_TWO_SEPARATE_FAULT_CASES_BOUND')
  if any(json.loads(p.read_bytes()).get('context')==context for p in existing):raise ValueError('EXACT_CASE_NO_AUTOMATIC_RESTART')
  value={'format':'aeris-product-case','version':1,'context':context,'candidateSHA256':candidate_digest,'attemptOrdinal':attempt['ordinal'],'startedHostNs':self.now(),'originalDeadlineNs':self.deadline_ns,'repairAttemptIncremented':False};put(cases/('case-%02d.json'%(len(existing)+1)),canonical(value)+b'\n');return value
