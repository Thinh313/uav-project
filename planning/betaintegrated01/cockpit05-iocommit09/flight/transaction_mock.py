"""Synthetic raw-payload semantic fixtures, not a framed durability or Android proof."""
from .transactions import resolve_rows
from pathlib import Path
import base64,copy,hashlib,json
C=dict(run='run',epoch='epoch',boot='boot',operator='operator',generation='generation',profileId='profile')
def row(n,k,v,t):
 raw=json.dumps(v,separators=(',',':')).encode();return dict(n=n,kind=k,base64=base64.b64encode(raw).decode(),monotonicNs=t,sha256=hashlib.sha256(b'row'+raw).hexdigest())
def inp(seq,t):return dict(**C,source='touch-source',clockDomain='ANDROID_UPTIME_NS_SAMPLER',provenance='ROOT_INJECTED_ANDROID_TOUCH',sequence=seq,elapsedNs=t,uptimeNs=t,lastMotionUptimeNs=0,axes=[0,0,0,0],pointers=0,motionAction=-1,release=False,inputObservation=dict(kind='IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT',uiHeartbeatElapsedNs=t,touchRevision=0,samplerThreadId=2,uiThreadId=1,viewEpoch=1,releaseFence=0))
def tx(n,i,prior=None,lease=None,expiry=-1):
 p=dict(kind='OBSERVE'if lease is None else'RENEW',priorLeaseId=lease,priorExpiryNs=expiry,proposedLeaseId=lease,proposedExpiryNs=-1 if lease is None else i['elapsedNs']+200000000,inputSequence=i['sequence'])
 return row(n,'CONTROL_INPUT_TX',dict(format='aeris-authority-transaction',version=1,context=C,operation='INPUT',preWriteNs=i['elapsedNs']+1,input=i,proposal=p,priorCommitReceipt=prior),i['elapsedNs']+2)
def receipt(r,decision=None,disposition='ACCEPTED'):
 v=json.loads(base64.b64decode(r['base64']));return dict(format='aeris-authority-commit-receipt',version=1,context=C,operation=v['operation'],txRecordN=r['n'],txPayloadSHA256=hashlib.sha256(base64.b64decode(r['base64'])).hexdigest(),groupDurableNs=r['monotonicNs']+1,decisionNs=r['monotonicNs']+2 if decision is None else decision,disposition=disposition,proposal=v['proposal'],reason=None if disposition=='ACCEPTED'else'EXPIRED',authorityRestorable=False)
def fixture():
 a=tx(1,inp(0,100000000));ar=receipt(a);av=json.loads(base64.b64decode(a['base64']));i=av['input'];p=dict(kind='CONSENT',priorLeaseId=None,priorExpiryNs=-1,proposedLeaseId='lease-1-consent-1',proposedExpiryNs=300000000,inputSequence=0,actionId='consent-1')
 b=row(2,'CONTROL_CONSENT_TX',dict(format='aeris-authority-transaction',version=1,context=C,operation='CONSENT',preWriteNs=110000000,neutralInput=i,proposal=p,priorCommitReceipt=ar),110000001);br=receipt(b)
 c=tx(3,inp(1,200000000),br,'lease-1-consent-1',300000000);cr=receipt(c)
 d=row(4,'CONTROL_COMMIT_RECEIPT',dict(atNs=210000000,reason='BEFORE_DISCRETE_ACTION_OR_CLOSE',commitReceipt=cr),210000000)
 return [a,b,c,d,row(5,'SESSION_CLOSE',{},220000000)]
def main():
 out=Path(__file__).resolve().parents[4]/'evidence/betaintegrated01-cockpit05-iocommit09/host/transactions-mock04';out.mkdir(parents=True,exist_ok=False);results=[]
 def test(name,mutate=None,negative=False):
  f=fixture()
  if mutate:mutate(f)
  try:
   summary={};events=list(resolve_rows(f,C,summary))
   if negative:raise AssertionError('counterfeit accepted')
   assert [r['kind']for r in events]==['CONTROL_INPUT','CONTROL_CONSENT','CONTROL_INPUT','CONTROL_LEASE_RENEWED','CONTROL_COMMIT_RECEIPT','SESSION_CLOSE'];assert events[0]['monotonicNs']==100000004 and events[0]['commitEvidence']['candidateRecordN']==1;assert summary['candidates']==3
   results.append(dict(case=name,pass_=True))
  except ValueError as e:
   results.append(dict(case=name,pass_=negative,reason=str(e)))
 def change(f,index,key,value,receiptKey=False):
  v=json.loads(base64.b64decode(f[index]['base64']));(v['commitReceipt']if receiptKey else v)[key]=value;f[index]=row(f[index]['n'],f[index]['kind'],v,f[index]['monotonicNs'])
 test('resolved actual decision clocks and no altered native bytes')
 def expired(f):
  change(f,3,'decisionNs',300000001,True);f[3]['monotonicNs']=310000000;f[4]['monotonicNs']=320000000
 test('accepted renewal after old expiry refuses',expired,True)
 test('typed false version refuses',lambda f:change(f,0,'version',True),True)
 test('unknown pending tail refuses',lambda f:f.__delitem__(slice(3,None)),True)
 test('orphan repeated receipt refuses',lambda f:f.append(copy.deepcopy(f[3])),True)
 test('changed original input SHA refuses',lambda f:change(f,3,'txPayloadSHA256','0'*64,True),True)
 test('unrecognized carrier refuses',lambda f:f[3].update(kind='CONTROL_ARBITRARY'),True)
 test('future actual durability refuses',lambda f:change(f,3,'groupDurableNs',999999999,True),True)
 test('accepted attached UI stale refuses',lambda f:change(f,3,'decisionNs',450000000,True),True)
 v=dict(status='PASS'if all(x['pass_']for x in results)else'FAIL',cases=results,syntheticPayloadsOnly=True,framedDurabilityProof=False,actualAndroid=False)
 (out/'results.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));assert v['status']=='PASS'
if __name__=='__main__':main()
