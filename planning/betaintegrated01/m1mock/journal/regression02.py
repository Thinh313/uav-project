"""Targeted follow-up on bounded ingress and cold commit classification.

Old full-suite receipts remain unchanged; this is not a re-label of their SHA.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.journal import SegmentedJournal,Policy,FileIO,verify_journal
E=R/'evidence/betaintegrated01-m1mock/journal/regression02';E.mkdir(exist_ok=False)
P=Policy(segment_bytes=12288,max_record_bytes=2048,quota_bytes=262144,max_segments=32)
results=[]
def fail(fn):
 try:fn()
 except Exception as e:return type(e).__name__+':'+str(e)
 raise AssertionError('EXPECTED_REJECTION')
def case(name,fn):
 try:results.append({'name':name,'status':'PASS','detail':fn()})
 except Exception as e:results.append({'name':name,'status':'FAIL','error':repr(e)})
def make(name,io=None):return SegmentedJournal(E/name,'run01','epoch01',P,io)
def read(name,anchor=None):return verify_journal(E/name,'run01','epoch01',anchor)
def nominal():
 j=make('nominal')
 for i in range(12):
  j.record_frame(i,b'rx',b'sensor',len);j.append_stage(i,{'computeNs':i,'fsyncNs':3*i})
 receipt=j.close();v=read('nominal');assert v['state']=='COMPLETE_BYTES_UNATTESTED'and v['byteSequenceComplete']and not v['writerCommitAttested']and not v['publicationAllowed']
 a=read('nominal',receipt['commitAnchor']);assert a['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'and a['writerCommitAttested']and not a['publicationAllowed']and not a['APExecutionAccepted']
 bad=dict(receipt['commitAnchor']);bad['head']='f'*64;fail(lambda:read('nominal',bad))
 assert a['stageSummary']['fsyncNs']=={'count':12,'sum':198,'max':33}
 return {'frames':a['frames'],'segments':a['segments'],'defaultState':v['state'],'anchoredState':a['state']}
case('normal_close_external_anchor_and_stage_replay',nominal)
def bounded_inputs():
 for mode in ['rx','intent','computed','string','cycle','deep','items']:
  j=make('bound-'+mode);sent=[];computed=[]
  if mode in ['rx','intent','computed']:
   def compute(b):computed.append(True);return b'x'*1537
   rx=b'x'*1537 if mode=='rx'else b'rx';intent=compute if mode=='computed'else b'x'*1537 if mode=='intent'else b's'
   err=fail(lambda:j.record_frame(0,rx,intent,lambda b:sent.append(True)or len(b)))
   assert not sent
   if mode in ['rx','intent']:assert not computed and read('bound-'+mode)['receivedFrames']==0
   else:assert computed and read('bound-'+mode)['receivedFrames']==1
  else:
   if mode=='string':payload={'x':'x'*2049}
   elif mode=='cycle':payload={};payload['x']=payload
   elif mode=='items':payload=list(range(65))
   else:
    payload={};v=payload
    for i in range(9):v['x']={};v=v['x']
   err=fail(lambda:j.append_event('EVENT',payload))
  assert read('bound-'+mode)['state']=='INCOMPLETE_RECORDING';assert j.failed
 return {'refusedModes':7,'sendCalls':0,'encodingBeforeInputBound':False}
case('pre_encoding_ingress_tree_and_bytes_bounds',bounded_inputs)
def final_double():
 class Persistent(FileIO):
  def dirsync(self,p):
   if (Path(p)/'session.json').exists():raise OSError('INJECTED_FINAL_DIRECTORY_SYNC')
   return super().dirsync(p)
  def open_exclusive(self,p):
   if Path(p).name=='failure.json':raise OSError('INJECTED_FAILURE_MARKER_OPEN')
   return super().open_exclusive(p)
 j=make('finaldouble',Persistent());j.record_frame(0,b'r',b's',len);err=fail(j.close);v=read('finaldouble')
 assert v['state']=='COMPLETE_BYTES_UNATTESTED'and v['byteSequenceComplete']and not v['writerCommitAttested']and not v['publicationAllowed']and not j.closed
 return {'closeError':err,'state':v['state'],'externalAnchorReturned':False}
case('final_dirsync_plus_failure_marker_fault_never_committed',final_double)
def oldcold():
 vals={}
 for name in ['nominal','short-progress','send-return','send-raise','io-sync','io-dir','io-next','quota','crash-intent','crash-sent','crash-successor','crash-close','crash-session','crash-committed']:
  p=R/'evidence/betaintegrated01-m1mock/journal/tests01'/name
  if not p.exists():continue
  v=verify_journal(p,'run01','epoch01');vals[name]=v['state'];assert not v['publicationAllowed']and not v['writerCommitAttested']
 assert vals['nominal']=='COMPLETE_BYTES_UNATTESTED'and vals['io-sync']=='INCOMPLETE_RECORDING'
 return vals
case('existing_failure_prefix_and_rotation_cold_replay',oldcold)
src={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'pilot/betaintegrated01/journal').glob('*.py')}
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(x['status']=='PASS'for x in results)else'FAIL','sourceSHA256':src,'groups':results,'scope':'Targeted mock/filesystem regression, no AP/Android/flight/native wiring/performance/powerloss proof','oldFullSuiteReceiptPreserved':True}
(E/'report.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(0 if report['status']=='PASS'else 1)
