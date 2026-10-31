"""Frozen/current real-model differential and preadmission-only clock waiting."""
from pathlib import Path
from types import SimpleNamespace,ModuleType
from unittest.mock import patch
import hashlib,json,os,shutil,sys,time
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.frame_adapter import FrameAdapter,SERVO
from aeris_runtime.metadata_budget import encoded
from pilot.betaintegrated01.runtime.physics import Model,profile
LAB=R/'evidence/betasim-integrated01/runtime/.clockframe09';OLD=R/'evidence/betasim-integrated01/candidates/c9d43b1768b89614701d0dfd9334f5e7fd940eda4aa6c49c386c975607553ef4/source/aeris_runtime/foundation/frame_adapter.py'
class Capture:
 def __init__(self,path):self.fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);self.frames=0;self.phase='BETWEEN';self.rows=[];self.sensors=[];self.synced=False;self.closed=False
 def record_frame(self,frame,raw,compute,send):
  self.phase='RX';body=compute(raw);self.phase='INTENT';self.synced=False;os.write(self.fd,body);os.fsync(self.fd);self.synced=True;self.sensors.append(body);send(body);self.frames+=1;self.phase='BETWEEN'
 def append_stage(self,frame,row):self.rows.append(dict(row));assert len(row)<=32
 def abort(self,reason):
  if not self.closed:os.close(self.fd);self.closed=True
class Clock:
 def dispatch(self,bracket,fn):return fn(time.monotonic_ns())
def create(cls,name,clock):
 out=LAB/name;out.mkdir();a=cls.__new__(cls);a.clock_owner=clock;a.failed=a.closed=False;a.frames=a.stage_rows=0;a.max_frames=200;a.peer=None;a.origin_ns=time.monotonic_ns();a.first_rx=a.last_rx=None;a.last_sensor_send_ns=None;a.scene=None;a.current=None;a.latest_diagnostic=None;a.root=out/'journal';a.capture_failure=lambda *a:None;a.model=Model(profile('offset','gust',32));a.journal=Capture(out/'original-sensors.bin');return a
def fresh():
 t=time.monotonic_ns();return{'id':939,'hostReceiveNs':t,'offsetLowNs':0,'offsetHighNs':0,'clockPublicationSequence':2,'publicationCompleteHostNs':t}
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);captures=[];groups=[]
 try:
  module=ModuleType('_readonly_frozen_r06_frame');module.__file__=str(OLD);exec(compile(OLD.read_bytes(),str(OLD),'exec'),module.__dict__);variants=[]
  for cls,name in((module.FrameAdapter,'frozen-r06'),(FrameAdapter,'new-clockpipe09')):
   a=create(cls,name,Clock());captures.append(a.journal);sent=[]
   for frame in range(120):
    pwm=[1460+frame%15,1480-frame%13,1440+frame%9,1470-frame%11]+[1000]*12;packet=SERVO.pack(18458,1200,frame,*pwm);original=time.monotonic_ns();kwargs={}if cls is module.FrameAdapter else{'original_receive_ns':original,'admission_deadline_ns':original+100_000_000}
    def send(body):assert a.journal.synced;sent.append(body);return len(body)
    a.receive(packet,('127.0.0.1',9000),send,clock_read=fresh,**kwargs)
   variants.append((sent,a.model.snapshot(),a.frames,a.stage_rows));assert len(sent)==120
   if cls is FrameAdapter:
    assert all(row['originalReceiveKind']==1 and row['clockAtOriginalReceiptStatus']==0 and row['originalReceiveSinceOriginNs']==row['receiveSinceOriginNs']<=row['clockAdmissionSinceOriginNs']for row in a.journal.rows)
  assert variants[0]==variants[1];groups.append('frozen-R06-vs-current-unchanged-realModel120frames-identical-sensorbytes-finalmodel-and-frame-stagecounts')
  # Case, original receipt+500ms and previous sensor+500ms each constrain wait.
  for label,receive_age,last_send_age,case_left,expected_left in [('case',0,0,2_000_000,2_000_000),('original500',499_000_000,0,1_000_000_000,1_000_000),('lastsensor500',0,497_000_000,1_000_000_000,3_000_000)]:
   now=[2_000_000_000];deadlines=[];c=Clock();c.pipeline=SimpleNamespace(pending=lambda:True);c.pending_prior_id=lambda:938
   def wait(end,prior):assert prior==938;deadlines.append(end);raise TimeoutError('MOCK_ORIGINAL_BOUND_NO_PERMISSION')
   c.wait_for_frame=wait
   with patch('aeris_runtime.foundation.frame_adapter.time.monotonic_ns',side_effect=lambda:now[0]):
    a=create(FrameAdapter,label,c);a.origin_ns=0;a.last_sensor_send_ns=now[0]-last_send_age;captures.append(a.journal)
    try:a.receive(SERVO.pack(18458,1200,0,*([1000]*16)),('127.0.0.1',9000),lambda b:(_ for _ in()).throw(AssertionError('SENSOR')),clock_read=lambda:None,admission_deadline_ns=now[0]+case_left,original_receive_ns=now[0]-receive_age)
    except TimeoutError as e:assert 'ORIGINAL_BOUND'in str(e)
    else:raise AssertionError('expected refusal')
   assert deadlines==[now[0]+expected_left]and not a.journal.sensors and a.model.t==0 and a.frames==0 and a.current['journalAdmissionAttempted']is False
  groups.append('sourcecase-originalrecv500ms-lastsensor500ms-bound-oneunadmittedwait-zero-model-intent-sensor-on-refusal')
  now=[3_000_000_000];waited=[];c=Clock();c.pipeline=SimpleNamespace(pending=lambda:True);c.wait_for_frame=lambda *a:waited.append(a);c.pending_prior_id=lambda:938
  with patch('aeris_runtime.foundation.frame_adapter.time.monotonic_ns',side_effect=lambda:now[0]):
   a=create(FrameAdapter,'postintent',c);a.origin_ns=0;captures.append(a.journal);step=a.model.step
   def delayed(*args):v=step(*args);now[0]+=300_000_000;return v
   a.model.step=delayed;ref={**fresh(),'hostReceiveNs':now[0]};sent=[]
   try:a.receive(SERVO.pack(18458,1200,0,*([1000]*16)),('127.0.0.1',9000),lambda b:sent.append(b),clock_read=lambda:ref,original_receive_ns=now[0])
   except ValueError as e:assert 'CLOCK_BRACKET_NOT_FRESH_250MS'in str(e)
   else:raise AssertionError('late sensor was accepted')
   assert not waited and not sent and a.current['journalAdmissionAttempted']is True and a.current['localCallbackInvoked']is False
  groups.append('after-model-or-INTENT-no-wait-or-clock-retry-stale250ms-refusal-before-socketcallback')
  report={'format':'aeris-clockpipe09-frame-source-differential','status':'PASS_REAL_MODEL_AND_FSYNC_MOCK_CLOCK_NOT_SITL','groups':groups,'oldSourceSHA256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'newSourceSHA256':hashlib.sha256((T/'source/aeris_runtime/foundation/frame_adapter.py').read_bytes()).hexdigest(),'oldCandidateSourceUnchanged':True,'actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))}
 finally:
  for c in captures:c.abort('MOCK_TERMINAL')
  shutil.rmtree(LAB)
 out=R/'evidence/betasim-integrated01/runtime/clockpipe09-frame-mock02.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
