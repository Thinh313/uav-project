"""Causal boundary unit tests, no Android/network/process or acceptance claim."""
from pathlib import Path
import copy,importlib,json,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'source'),str(ROOT.parents[2])]
from aeris_runtime.native import NativeBridge
IDENTITY={'sourceSHA256':'a'*64,'pid':123,'processEpoch':'b'*32,'viewEpoch':7}
CONTEXT={'run':'case','epoch':'c'*32,'boot':'d'*32,'operator':'pilot','generation':'e'*32,'profileId':'manual'}
def snapshot(selected=False):
 return {**IDENTITY,'context':CONTEXT if selected else None,'bootstrapSHA256':'f'*64 if selected else None,'lifecycle':{'phase':'READY'if selected else'IDLE'},'state':{'ownerActive':False,'connectPending':False,'authorityRestorable':False,'native':{'phase':'NO_SESSION','authorityRestorable':False,'flight':{'armed':False},'input':{'consent':False,'leaseId':None},'rcOverrideActiveLocally':False}}}
class Store:
 def __init__(self):self.rows=[]
 def receipt(self,name,value):self.rows.append((name,copy.deepcopy(value)));return {'original':len(self.rows)}
class Channel:
 def __init__(self):self.active=True;self.closed=False;self.failure=None;self.open_ref={'original':'old-open'};self.lease='owned';self.close_result=None
class Device:
 def __init__(self):self.status_socket=Channel();self.store=Store();self.events=[]
 def close_status_socket(self,deadline_ns):
  self.events.append('old-close');c=self.status_socket;c.active=False;c.closed=True;c.lease=None;c.close_result={'receipt':{'captureComplete':True,'drainComplete':True,'failure':None},'receiptRef':{'original':'old-close'}};return c.close_result
 def open_status_socket(self,baseline,baseline_ref,source,apk,**kw):self.events.append('new-open');self.opened=(copy.deepcopy(baseline),baseline_ref,kw)
class Bridge(NativeBridge):
 def _request(self,action,body=None,context=None,deadline_ns=None):
  assert action=='STATUS'and self.device.status_socket.closed
  self.device.events.append('fresh-legacy-selected-status');self.latest=copy.deepcopy(self.next_status);self.trace.append({'action':'STATUS','hostReceivedNs':100,'version':3});self.last_receipt_ref={'original':'fresh-baseline'};return self.latest

def case():
 d=Device();n=Bridge(d,IDENTITY['sourceSHA256'],now=lambda:101,apk_sha='1'*64);n._stage_deadline=1000;n.latest=snapshot();n.trace.append({'action':'STATUS','version':4});n._latest_validated_raw=json.dumps(n.latest).encode();n.last_receipt_ref={'original':'before'};n.next_status=snapshot(True);return n,d

def blocked(fn,word):
 try:fn()
 except(ValueError,RuntimeError)as e:assert word in str(e),(word,str(e));return
 raise AssertionError('expected refusal:'+word)

def main():
 checks=[]
 n,d=case();boundary=n._begin_bootstrap_transport(n.latest);assert d.events==['old-close'];ready=snapshot(True);n.trace.append({'action':'BOOTSTRAP','request':{'requestNonce':'2'*32}});n.last_receipt_ref={'original':'bootstrap'}
 result=n._finish_bootstrap_transport(boundary,ready,CONTEXT,1000);assert d.events==['old-close','fresh-legacy-selected-status','new-open']and result==snapshot(True);proof=d.store.rows[-1][1];assert proof['oldChannelCloseRef']=={'original':'old-close'}and proof['bootstrapRequestNonce']=='2'*32 and proof['baselineRequestRef']=={'original':'fresh-baseline'}and proof['authorityRestored']is False;checks.append('positive-close-READY-freshbaseline-open-original-order')
 n,d=case();d.status_socket.failure=RuntimeError('unexpectedEOF');blocked(lambda:n._begin_bootstrap_transport(n.latest),'HEALTHY_OLD_CHANNEL');assert d.events==[];checks.append('unexpectedEOF-terminal-zero-reconnect')
 n,d=case();b=n._begin_bootstrap_transport(n.latest);blocked(lambda:n._begin_bootstrap_transport(n.latest),'ONE_BOOTSTRAP_ATTEMPT');checks.append('one-transition-no-retry')
 for key,value in [('pid',124),('sourceSHA256','9'*64),('processEpoch','9'*32),('viewEpoch',8),('context',{**CONTEXT,'boot':'9'*32})]:
  n,d=case();b=n._begin_bootstrap_transport(n.latest);n.trace.append({'action':'BOOTSTRAP','request':{'requestNonce':'2'*32}});bad=snapshot(True);bad[key]=value;blocked(lambda:n._finish_bootstrap_transport(b,bad,CONTEXT,1000),'SAME_ORIGINAL_CONTEXT_IDENTITY');assert 'new-open'not in d.events
 checks.append('wrong-PID-source-process-view-selectedcontext-denied')
 for branch,key,value in [('state','ownerActive',True),('state','connectPending',True),('state','authorityRestorable',True),('native','phase','CONNECTED'),('flight','armed',True),('input','consent',True),('input','leaseId','oldlease')]:
  n,d=case();b=n._begin_bootstrap_transport(n.latest);n.trace.append({'action':'BOOTSTRAP','request':{'requestNonce':'2'*32}});bad=snapshot(True);target=bad['state'] if branch=='state'else bad['state']['native']if branch=='native'else bad['state']['native'][branch];target[key]=value;blocked(lambda:n._finish_bootstrap_transport(b,bad,CONTEXT,1000),'STATUS_TRANSITION_NO_');assert 'new-open'not in d.events
 checks.append('owner-pending-authority-arm-consent-lease-denied')
 n,d=case();b=n._begin_bootstrap_transport(n.latest);n.trace.append({'action':'BOOTSTRAP','request':{'requestNonce':'2'*32}});n.next_status['bootstrapSHA256']='9'*64;blocked(lambda:n._finish_bootstrap_transport(b,snapshot(True),CONTEXT,1000),'SAME_READY_BOOTSTRAP');assert 'new-open'not in d.events;checks.append('freshbaseline-wrong-bootstrap-hash-denied')
 n,d=case();b=n._begin_bootstrap_transport(n.latest);n.trace.append({'action':'BOOTSTRAP','request':{'requestNonce':'2'*32}});n.next_status['state']['native']['input']['consent']=True;blocked(lambda:n._finish_bootstrap_transport(b,snapshot(True),CONTEXT,1000),'NO_ARM_OR_INPUT');assert 'new-open'not in d.events;checks.append('freshbaseline-rechecks-authority')
 print(json.dumps({'status':'PASS_UNIT_MOCK_NOT_ANDROID','groups':checks,'actualActors':0}))
if __name__=='__main__':main()
