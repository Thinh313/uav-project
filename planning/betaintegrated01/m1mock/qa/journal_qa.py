"""Independent small filesystem adversarial checks against the actual public API."""
from pathlib import Path
import os,sys,json,hashlib,shutil,datetime,math,copy
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.journal import SegmentedJournal,Policy,FileIO,verify_journal,estimate_admission

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(p):return {str(x.relative_to(p)):sha(x)for x in p.rglob('*')if x.is_file()and not x.is_symlink()}
def failcall(fn):
 try:fn()
 except Exception as e:return type(e).__name__+':'+str(e)
 raise AssertionError('EXPECTED_REFUSAL')
tag=sys.argv[1]if len(sys.argv)>1 else'01';assert tag.isdigit()
E=R/'evidence/betaintegrated01-m1mock/qa'/('journal-qa'+tag);E.mkdir(exist_ok=False)
assert shutil.disk_usage(E).free>=10*2**30+256*2**20
src=[R/'pilot/betaintegrated01/journal'/n for n in ['writer.py','receiver.py','admission.py']];before={str(p.relative_to(R)):sha(p)for p in src};results=[]
policy=Policy(segment_bytes=8192,quota_bytes=524288,max_record_bytes=1024,max_segments=128,termination_reserve_bytes=16384)
def make(name,frames=18,io=None):
 p=E/name;j=SegmentedJournal(p,'qarun','qaepoch',policy,io=io)
 for i in range(frames):j.record_frame(i,bytes([i%256]),b'sensor-'+bytes([i%256]),lambda b:len(b));j.append_stage(i,{'a':i,'b':2*i})
 j.close();return p,j
def case(i,fn):
 try:value=fn();results.append({'id':i,'status':'PASS','detail':value})
 except Exception as e:results.append({'id':i,'status':'FAIL','error':type(e).__name__+':'+str(e)})
baseline,j0=make('baseline');v=verify_journal(baseline,'qarun','qaepoch');assert v['state']=='COMPLETE_RECORDING'and v['frames']==18 and v['segments']>1
def clone(n):p=E/n;shutil.copytree(baseline,p);return p
def reject_mutation(name,mutate):
 p=clone(name);mutate(p);return failcall(lambda:verify_journal(p,'qarun','qaepoch'))
case('J01_rotated_full_capture',lambda:{'segments':v['segments'],'frames':v['frames'],'stageRows':v['stageRows'],'scope':v['scope']})
def immutable():
 b=tree(baseline);failcall(lambda:j0.append_event('LATE',{}));assert tree(baseline)==b;assert verify_journal(baseline,'qarun','qaepoch')['state']=='COMPLETE_RECORDING';return 'sealed bytes unchanged after rejected append'
case('J02_no_append_after_seal',immutable)
case('J03_tamper_rejected',lambda:reject_mutation('tamper',lambda p:(p/'segment-000000.jsonl').write_bytes((p/'segment-000000.jsonl').read_bytes().replace(b'sensor',b'SENSOR',1)+b'garbage')))
case('J04_missing_segment',lambda:reject_mutation('missing',lambda p:(p/'segment-000001.jsonl').rename(p/'saved-missing.bin')))
case('J05_unlisted_member',lambda:reject_mutation('extra',lambda p:(p/'unexpected.json').write_text('{}')))
case('J06_forged_status',lambda:reject_mutation('forgedstatus',lambda p:(p/'session.json').write_text((p/'session.json').read_text().replace('COMPLETE_RECORDING','FLIGHT_SUCCESS'))))
def symlink():
 p=E/'alias';p.symlink_to(baseline.resolve(),target_is_directory=True);return failcall(lambda:verify_journal(p,'qarun','qaepoch'))
case('J07_symlink_root',symlink)
case('J08_foreign_expected_context',lambda:failcall(lambda:verify_journal(baseline,'foreign','qaepoch')))
def order():
 class Trace(FileIO):
  def __init__(self):super().__init__();self.log=[]
  def write(self,fd,b):n=super().write(fd,b);self.log.append('write-return');return n
  def fsync(self,fd):super().fsync(fd);self.log.append('fsync-return')
 io=Trace();p=E/'order';j=SegmentedJournal(p,'qarun','qaepoch',policy,io=io)
 def send(b):
  assert io.log[-1]=='fsync-return';row=json.loads((p/'segment-000000.jsonl').read_bytes().splitlines()[-1]);assert row['body']['kind']=='INTENT';io.log.append('send-return');return len(b)
 j.record_frame(0,b'rx',b'sensor',send);j.close();return {'state':verify_journal(p,'qarun','qaepoch')['state'],'sendCount':io.log.count('send-return')}
case('J09_fsync_before_actual_send_callback',order)
def partial():
 p=E/'partial';j=SegmentedJournal(p,'qarun','qaepoch',policy);err=failcall(lambda:j.record_frame(0,b'rx',b'sensor',lambda b:len(b)-1));v=verify_journal(p,'qarun','qaepoch');assert v['state']=='INCOMPLETE_RECORDING'and v['unknownSends']==1 and v['localSends']==0;return {'error':err,'state':v['state'],'unknown':v['unknownSends']}
case('J10_partial_send_unknown',partial)
def sync_fail():
 class Once(FileIO):
  armed=False
  def fsync(self,fd):
   if self.armed:self.armed=False;raise OSError('QA_FSYNC_FAILURE')
   return super().fsync(fd)
 p=E/'syncfail';io=Once();j=SegmentedJournal(p,'qarun','qaepoch',policy,io=io);io.armed=True;called=[];failcall(lambda:j.record_frame(0,b'rx',b'sensor',lambda b:called.append(True)or len(b)));assert not called;v=verify_journal(p,'qarun','qaepoch');assert v['state']=='INCOMPLETE_RECORDING';return v['pendingPhase']
case('J11_failed_intent_barrier_no_send',sync_fail)
def stage_overflow():
 p=E/'stageoverflow';j=SegmentedJournal(p,'qarun','qaepoch',policy);j.record_frame(0,b'r',b's',lambda b:len(b));j.append_stage(0,{'ns':2**63-1})
 err=None
 try:j.append_stage(0,{'ns':1})
 except Exception as e:err=type(e).__name__+':'+str(e)
 if err:
  j.abort('QA_EXPECTED_REJECTION');return {'rejected':err}
 j.close();v=verify_journal(p,'qarun','qaepoch');assert v['state']=='COMPLETE_RECORDING','writer accepted overflow but verifier cannot read it';return 'writer/receiver agree'
case('J12_stage_aggregate_integer_bound',stage_overflow)
def final_double_fault():
 class Persistent(FileIO):
  def dirsync(self,p):
   if (Path(p)/'session.json').exists():raise OSError('QA_SESSION_DIRECTORY_SYNC_FAILED')
   return super().dirsync(p)
  def open_exclusive(self,p):
   if Path(p).name=='failure.json':raise OSError('QA_FAILURE_MARKER_UNWRITABLE')
   return super().open_exclusive(p)
 p=E/'finaldouble';j=SegmentedJournal(p,'qarun','qaepoch',policy,io=Persistent());j.record_frame(0,b'r',b's',lambda b:len(b));err=failcall(j.close)
 try:v=verify_journal(p,'qarun','qaepoch')
 except Exception as e:return {'closeError':err,'coldRejected':str(e)}
 assert v['state']!='COMPLETE_RECORDING','close failed and failure marker unavailable, yet cold receiver declares COMPLETE_RECORDING without commit anchor';return {'closeError':err,'state':v['state']}
case('J13_final_sync_and_failure_marker_fault',final_double_fault)
def shortwrite():
 class Short(FileIO):
  def write(self,fd,b):return super().write(fd,b[:min(3,len(b))])
 p,j=make('shortwrites',frames=2,io=Short());v=verify_journal(p,'qarun','qaepoch');assert v['frames']==2 and v['state']=='COMPLETE_RECORDING';return 'POSIX short writes fully retried without dropping bytes'
case('J14_valid_shortwrite_loop',shortwrite)
args={'free_bytes':100*2**30,'duration_seconds':30,'rate_hz':1200,'max_wal_bytes_per_frame':3000,'max_trace_events_per_frame':10,'trace_event_bytes':64,'max_stage_bytes_per_frame':100,'max_video_bytes_per_second':1000000,'metadata_bytes':1024,'copies':3,'export_peak_bytes':1024,'capacity_frames':36000}
def admission():
 assert estimate_admission(**args)['admitted'];n=0
 for key,val in [('duration_seconds',False),('rate_hz',float('nan')),('metadata_bytes',-1),('copies',2**63),('max_wal_bytes_per_frame',float('inf')),('rate_hz',0)]:
  a=dict(args);a[key]=val;failcall(lambda:estimate_admission(**a));n+=1
 a=dict(args);a['rate_hz']=2**62;a['duration_seconds']=4;failcall(lambda:estimate_admission(**a));n+=1
 a=dict(args);a['free_bytes']=20*2**30-1;assert not estimate_admission(**a)['admitted'];a=dict(args);a['capacity_frames']=35999;assert not estimate_admission(**a)['admitted'];return {'invalidArithmeticCases':n,'entryAndCapacityRefused':True}
case('J15_admission_strict_numeric_bounds',admission)
after={str(p.relative_to(R)):sha(p)for p in src};q={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SCOPED'if all(x['status']=='PASS'for x in results)else'FINDINGS','sourceBefore':before,'sourceAfter':after,'sourceChangedDuringRun':before!=after,'results':results,'scope':'Independent small-filesystem/public-API mock tests; no actual AP/Android/flight/hardware or source-authenticity certification','outputsBytes':sum(p.stat().st_size for p in E.rglob('*')if p.is_file()),'runtimeLaunches':0}
if before!=after:q['status']='SOURCE_CHANGED_REVIEW_RESULTS_AGAIN'
(E/'results.json').open('x').write(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2));sys.exit(0 if q['status']=='PASS_SCOPED'else 2)
