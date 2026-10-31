"""Python dispatch-age proof with injected clock/admit and inert thread, no effects."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation17';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();s=importlib.util.spec_from_file_location('g17_quota_age_current',P/'qa-native-budget.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
class Thread:
 def __init__(self,**kw):self.target=kw['target']
 def start(self):pass
 def join(self,timeout):pass
 def is_alive(self):return False
cases=[]
def expect(fn,reason):
 try:fn();raise AssertionError('EXPECTED_REFUSAL')
 except AssertionError as e:assert str(e)==reason,(str(e),reason)
with patch.object(m.threading,'Thread',Thread),patch.object(m,'load',return_value={'scanner':{'staleMs':15000}}):
 now=[0.0]
 def nine(*a,**kw):now[0]+=9;return {'policySha256':'mock-policy'}
 with patch.object(m,'admit',nine):w=m.QuotaWatch(clock=lambda:now[0])
 assert w.check()['auditAgeS']==9 and w.last==0;now[0]+=6;assert w.check()['auditAgeS']==15;now[0]+=.001;expect(w.check,'SHARED_QUOTA_AUDIT_STALE');w.close();expect(w.check,'SHARED_QUOTA_AUDIT_CLOSED');cases.append({'case':'DELAY9_FOLLOW6_ORIGINAL_DISPATCH_AGE','ages':[9,15],'over15':'REFUSED','afterClose':'REFUSED'})
 for elapsed in [15.001,-.001]:
  now=[100.0]
  def bad(*a,**kw):now[0]+=elapsed;return {'policySha256':'must-not-be-published'}
  with patch.object(m,'admit',bad):expect(lambda:m.QuotaWatch(clock=lambda:now[0]),'SHARED_QUOTA_AUDIT_STALE_OR_CLOSED_AT_COMPLETION')
  cases.append({'case':'COMPLETION_OUTSIDE_EXISTING_0_TO15','elapsedS':elapsed,'status':'REFUSED_BEFORE_SAMPLE_PUBLISH'})
 now=[0.0];count=[0];watch=[None]
 def close_during(*a,**kw):
  count[0]+=1
  if count[0]>1:now[0]+=9;watch[0].close()
  return {'policySha256':'original'if count[0]==1 else'late-must-not-be-published'}
 with patch.object(m,'admit',close_during):
  w=m.QuotaWatch(clock=lambda:now[0]);watch[0]=w;original=(w.proof.copy(),w.last);realwait=w.stopped.wait;calls=[0]
  def wait(timeout):calls[0]+=1;return False if calls[0]==1 else True
  with patch.object(w.stopped,'wait',wait):w.thread.target()
  assert (w.proof,w.last)==original;expect(w.check,'SHARED_QUOTA_AUDIT_CLOSED')
 cases.append({'case':'CLOSE_DURING_PENDING_ADMIT','status':'NO_LATE_PROOF_OR_ANCHOR_RENEWAL','admitCalls':count[0]})
report={'status':'PASS_CONSERVATIVE_PYTHON_DISPATCH_AGE_AND_CLOSE','cases':cases,'source':{'path':str((P/'qa-native-budget.py').relative_to(R)),'sha256':H(P/'qa-native-budget.py')},'beforeSource':{'path':str((P/'nativebuilder-budget-before-dispatch-age.py').relative_to(R)),'sha256':H(P/'nativebuilder-budget-before-dispatch-age.py')},'beforeProofSha256':H(E/'nativebuilder-quota-age-before01.json'),'testSha256':H(Path(__file__)),'clockRule':'Only one injected Python clock before/after admission. No Node/Python subtraction, duration/deadline/counter reset, retry or actual thread.','thresholdMs':15000,'runtimePerformed':False};out=E/'nativebuilder-quota-age01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'cases':len(cases),'sourceSha256':H(P/'qa-native-budget.py')}))
