"""Bounded real-filesystem mock/fault tests. No AP/Android/socket/build/old writes."""
from pathlib import Path
import sys,json,hashlib,shutil,os,datetime,subprocess,time,threading
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from pilot.betaintegrated01.journal import SegmentedJournal,Policy,FileIO,verify_journal,estimate_admission,JournalError
from pilot.betaintegrated01.journal.receiver import VerificationError
TAG=sys.argv[1]if len(sys.argv)>1 else'01'
assert TAG.isdigit()and len(TAG)==2
E=R/'evidence/betaintegrated01-m1mock/journal'/('tests'+TAG);E.mkdir(exist_ok=False)
P=Policy(segment_bytes=12288,max_record_bytes=2048,quota_bytes=262144,max_segments=32)
# Policy minimum is4records+4KiB, exactly12288.
results=[]
def check(name,fn):
 try:fn();results.append({'name':name,'status':'PASS'})
 except Exception as e:results.append({'name':name,'status':'FAIL','errorType':type(e).__name__,'error':str(e)[:300]})
def fail(fn):
 try:fn()
 except(Exception,):return
 raise AssertionError('EXPECTED_REJECTION')
def make(name,io=None,policy=P):return SegmentedJournal(E/name,'run01','epoch01',policy,io)
def read(name):return verify_journal(E/name,'run01','epoch01')
def frame(j,i):return j.record_frame(i,b'PWM0123',lambda rx:b'SENSOR'+rx,lambda data:len(data))
def beforeafter(p):return {v.name:hashlib.sha256(v.read_bytes()).hexdigest()for v in p.iterdir()if v.is_file()}

class TraceIO(FileIO):
 def __init__(self):super().__init__();self.ops=[];self.kind=None
 def write(self,fd,b):
  try:self.kind=json.loads(bytes(b)).get('body',{}).get('kind')
  except Exception:self.kind=None
  self.ops.append(('WRITE',self.kind));return super().write(fd,b)
 def fsync(self,fd):self.ops.append(('SYNC',self.kind));super().fsync(fd)

def nominal():
 io=TraceIO();j=make('nominal',io)
 for i in range(40):
  def compute(rx):io.ops.append(('COMPUTE',i));return b'sensor:'+rx
  def send(b):io.ops.append(('SEND',i));return len(b)
  j.record_frame(i,b'rx',compute,send);j.append_stage(i,{'computeNs':i,'syncNs':2*i})
 s=j.close();v=read('nominal');assert v['state']=='COMPLETE_BYTES_UNATTESTED'and v['frames']==40 and v['segments']>1 and v['stageRows']==40
 assert v['stageSummary']['syncNs']=={'count':40,'sum':1560,'max':78}
 for n,(op,k)in enumerate(io.ops):
  if op=='SEND':assert io.ops[n-1]==('SYNC','INTENT')and any(x==('WRITE','RX')for x in io.ops[:n])
 assert s['APExecutionAccepted']is False and not v['APExecutionAccepted']
 b=beforeafter(j.root);fail(lambda:frame(j,40));fail(lambda:j.append_event('AFTER',{}));fail(lambda:j.abort('after'));assert beforeafter(j.root)==b
 (E/'nominal-io-order.json').open('x').write(json.dumps(io.ops))
check('rotation_global_chain_streamed_stage_and_fsync_before_send',nominal)

class OnceFault(FileIO):
 def __init__(self,kind):super().__init__();self.kind=kind;self.armed=False;self.hit=False;self.current=None
 def open_exclusive(self,p):
  if self.armed and not self.hit and self.kind=='next'and p.name=='segment-000001.jsonl':self.hit=True;raise OSError('INJECTED_ENOSPC_NEXT')
  return super().open_exclusive(p)
 def write(self,fd,b):
  try:self.current=json.loads(bytes(b)).get('body',{}).get('kind')
  except Exception:self.current=None
  if self.armed and not self.hit and self.kind in ['write','zero']and self.current=='INTENT':
   self.hit=True
   if self.kind=='zero':return 0
   raise OSError('INJECTED_EIO')
  return super().write(fd,b)
 def fsync(self,fd):
  if self.armed and not self.hit and self.kind=='sync'and self.current=='INTENT':self.hit=True;raise OSError('INJECTED_FSYNC')
  return super().fsync(fd)
 def dirsync(self,p):
  if self.armed and not self.hit and self.kind=='dir':self.hit=True;raise OSError('INJECTED_DIRSYNC')
  return super().dirsync(p)

def io_fault(kind):
 io=OnceFault(kind);j=make('io-'+kind,io);io.armed=True;sent=[]
 if kind=='dir':fail(j.close)
 elif kind=='next':
  for i in range(100):
   try:j.record_frame(i,b'rx',b'sensor',lambda b:sent.append(i)or len(b))
   except Exception:break
  assert io.hit
 else:fail(lambda:j.record_frame(0,b'rx',b'sensor',lambda b:sent.append(0)or len(b)));assert not sent
 assert j.failed and io.hit and read('io-'+kind)['state']=='INCOMPLETE_RECORDING';fail(j.close)
for k in ['write','zero','sync','dir','next']:check('fault_'+k+'_never_complete',lambda k=k:io_fault(k))

class SmallWrites(FileIO):
 def write(self,fd,b):return super().write(fd,b[:7])
def short_success():
 j=make('short-progress',SmallWrites());frame(j,0);j.close();assert read('short-progress')['frames']==1
check('progressing_short_writes_complete_all_bytes',short_success)

def partial_send():
 for kind in ['return','raise']:
  j=make('send-'+kind);calls=[]
  def send(b):
   calls.append(True)
   if kind=='raise':raise OSError('send could have occurred')
   return len(b)-1
  fail(lambda:j.record_frame(0,b'rx',b'sensor',send));v=read('send-'+kind);assert len(calls)==1 and v['unknownSends']==1 and v['state']=='INCOMPLETE_RECORDING'and v['frames']==0;fail(j.close)
check('partial_or_raised_send_is_unknown_not_retried_or_sent',partial_send)

def quota():
 j=make('quota',policy=Policy(segment_bytes=12288,max_record_bytes=2048,quota_bytes=40960,max_segments=32));calls=[]
 for i in range(100):
  try:j.record_frame(i,b'rx',b'x'*100,lambda b:calls.append(i)or len(b))
  except Exception:break
 assert j.failed and len(calls)<100;v=read('quota');assert v['state']=='INCOMPLETE_RECORDING'and v['frames']==len(calls)
check('quota_refusal_preserves_prefix_and_no_future_send',quota)

def event_order():
 j=make('order');fail(lambda:j.record_frame(1,b'rx',b'sensor',len));assert read('order')['state']=='INCOMPLETE_RECORDING'
 j=make('stage-order');fail(lambda:j.append_stage(0,{'cost':1}));assert read('stage-order')['state']=='INCOMPLETE_RECORDING'
 j=make('event-NaN');fail(lambda:j.append_event('COST',{'value':float('nan')}));assert read('event-NaN')['state']=='INCOMPLETE_RECORDING'
check('frame_stage_and_nonfinite_order_rejected',event_order)

def concurrent_writer():
 j=make('concurrent');entered=threading.Event();release=threading.Event();err=[]
 def compute(rx):entered.set();assert release.wait(2);return b'sensor'
 def work():
  try:j.record_frame(0,b'rx',compute,len)
  except Exception as e:err.append(str(e))
 t=threading.Thread(target=work);t.start();assert entered.wait(2);fail(lambda:j.append_event('CONCURRENT',{}));release.set();t.join(2);assert not t.is_alive()and not err;j.close();assert read('concurrent')['frames']==1
check('single_writer_enforced_under_concurrent_callback',concurrent_writer)

def copy_case(name):
 p=E/name;shutil.copytree(E/'nominal',p);return p
def tamper():
 p=copy_case('tamper');f=p/'segment-000000.jsonl';b=f.read_bytes().replace(b'RX',b'RY',1);f.write_bytes(b);fail(lambda:verify_journal(p,'run01','epoch01'))
check('receiver_crc_tamper_rejected',tamper)
def missing():
 p=copy_case('missing');(p/'segment-000001.jsonl').rename(p/'displaced.jsonl');fail(lambda:verify_journal(p,'run01','epoch01'))
check('receiver_missing_or_renamed_segment_rejected',missing)
def append_sealed():
 p=copy_case('sealed-append');f=p/'segment-000000.jsonl';f.open('ab').write(b'junk\n');fail(lambda:verify_journal(p,'run01','epoch01'))
check('receiver_append_after_seal_rejected',append_sealed)
def wrong_context():fail(lambda:verify_journal(E/'nominal','different','epoch01'))
check('receiver_foreign_context_rejected',wrong_context)
def unlisted():
 p=copy_case('unlisted');(p/'unexpected.json').write_text('{}');fail(lambda:verify_journal(p,'run01','epoch01'))
check('receiver_unlisted_file_rejected',unlisted)
def link():
 p=E/'root-link';p.symlink_to(E/'nominal',target_is_directory=True);fail(lambda:verify_journal(p,'run01','epoch01'))
 p=copy_case('file-link');f=p/'segment-000000.jsonl';f.rename(p/'moved');f.symlink_to(p/'moved');fail(lambda:verify_journal(p,'run01','epoch01'))
check('receiver_root_and_file_symlink_rejected',link)
def fake_success():
 j=make('fake-success');frame(j,0);j.abort('failure');p=j.root;(p/'session.json').write_text(json.dumps({'state':'COMPLETE_RECORDING','frames':1,'segments':1}));fail(lambda:read('fake-success'))
check('receiver_forged_complete_metadata_rejected',fake_success)

def admission():
 d=dict(free_bytes=40*2**30,duration_seconds=30,rate_hz=1200,max_wal_bytes_per_frame=3000,max_trace_events_per_frame=10,trace_event_bytes=64,max_stage_bytes_per_frame=128,max_video_bytes_per_second=2_000_000,metadata_bytes=1048576,copies=3,export_peak_bytes=2**20,capacity_frames=36000)
 assert estimate_admission(**d)['admitted']
 for updates in [{'free_bytes':19*2**30},{'capacity_frames':35999},{'free_bytes':20*2**30,'duration_seconds':86400,'capacity_frames':103680000}]:assert not estimate_admission(**{**d,**updates})['admitted']
 for updates in [{'copies':True},{'rate_hz':None},{'duration_seconds':2**63-1},{'max_wal_bytes_per_frame':-1}]:fail(lambda updates=updates:estimate_admission(**{**d,**updates}))
 for secs in [1800,7200,28800,86400]:assert not estimate_admission(**{**d,'free_bytes':20*2**30,'duration_seconds':secs,'capacity_frames':103680000})['admitted']
check('admission_undefined_overflow_capacity_and_long_run_budgets',admission)

# Separate child processes simulate abrupt interpreter death, not an AP/runtime.
script=R/'planning/betaintegrated01/m1mock/journal/crash_fixture.py'
for point in ['after-intent','after-sent','before-next','after-close','before-session','committed']:
 def crash(point=point):
  p=E/('crash-'+point);q=subprocess.run([sys.executable,'-B',str(script),str(p),point],cwd=R,capture_output=True,text=True,timeout=10);assert q.returncode==75,(point,q.returncode,q.stderr);v=verify_journal(p,'run01','epoch01');assert v['state']==('COMPLETE_BYTES_UNATTESTED'if point=='committed'else'INCOMPLETE_RECORDING');assert not v['APExecutionAccepted']
 check('abrupt_process_death_'+point,crash)

files=[p for p in E.rglob('*')if p.is_file()and not p.is_symlink()];bytecount=sum(p.stat().st_size for p in files);assert bytecount<64*2**20 and len(files)<500
report={'format':'aeris-beta-m1-journal-builder-fault-suite','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(r['status']=='PASS'for r in results)else'FAIL','results':results,'groups':len(results),'fileCount':len(files),'bytes':bytecount,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'pilot/betaintegrated01/journal').glob('*.py')},'sourceWiredToFlight':False,'oldWALCompatibilityClaim':False,'APAndroidNetworkRuntimeBuildSigning':False,'actualHostDiskGuardUsed':True,'independentQA':'NOT_CLAIMED_BY_BUILDER','scope':'Realfilesystem/injectedfailures/processdeath plus pure admission; not physicalpowerloss or flight/performance proof'}
(E/'report.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(0 if report['status']=='PASS' else 1)
