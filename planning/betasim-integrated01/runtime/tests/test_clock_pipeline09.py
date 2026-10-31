"""CLOCKPIPE09 causal source tests: real threads/file fsync, fake time/UDP only."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,os,shutil,struct,sys,threading,time,zlib
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.owner import ClockOwner,Publication
from aeris_runtime.foundation.clock_pipeline09 import OrderedClockQueue,TentativeCorrelator
from aeris_runtime.foundation.clock_socket import ClockSocket
from aeris_runtime.foundation.frame_adapter import FrameAdapter,SERVO
from aeris_runtime.metadata_budget import encoded
from pilot.betaintegrated01.clock.correlation import Context
LAB=R/'evidence/betasim-integrated01/runtime/.clockpipe09'
HOST=100904000000000;CTX=('betasim-clock09','e'*32,'b'*32)
class UDP:
 def __init__(self):self.responses=[];self.sent=[];self.closed=False
 def bind(self,*a):pass
 def setblocking(self,*a):pass
 def recvmsg(self,*a):
  if not self.responses:raise BlockingIOError
  return self.responses.pop(0),[],0,('127.0.0.1',9014)
 def sendto(self,raw,peer):self.sent.append((bytes(raw),peer));return len(raw)
 def close(self):self.closed=True
class Journal:
 """Real append/fsync bytes; synthetic manifest omitted, no actual-flight claim."""
 def __init__(self,root,io):self.root=root;root.mkdir();self.fd=os.open(root/'rows.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);self.io=io;self.seq=0;self.head='0'*64;self.rows=[];self.guard=SimpleNamespace(check=lambda *a:None);self.closed=False
 def append_event(self,kind,data):
  body={'v':2,'run':CTX[0],'epoch':CTX[1],'segment':0,'seq':self.seq,'previous':self.head,'kind':'EVENT','frame':None,'payload':{'eventKind':kind,'data':data}};b=encoded(body).rstrip(b'\n');head=hashlib.sha256(bytes.fromhex(self.head)+b).hexdigest();raw=encoded({'body':body,'crc32':format(zlib.crc32(b),'08x'),'sha256':head});self.io.write(self.fd,raw);self.io.fsync(self.fd);self.rows.append(body);self.head=head;self.seq+=1;return self.seq-1
 def close(self):
  if not self.closed:os.close(self.fd);self.closed=True
  return {'commitAnchor':{'mockOnlyJournal':True,'head':self.head}}
 def abort(self,*a):self.close()
def fixture(name,now):
 out=LAB/name;out.mkdir();o=ClockOwner(out,*CTX,180,'a'*64,origin_ns=HOST);o.thread=SimpleNamespace(is_alive=lambda:True);o.journal=Journal(out/'clock-journal',o.diagnostic_io);return o
def response(rid,receive):
 # Positive RTT, stable Root-minus-guest offset; exact original receive kept.
 return struct.pack('<7Q',rid,receive-437330000000-1_000_000,receive-437330000000,0,1,0,0)
def drain(o):
 while True:
  row=o.pipeline.take()
  if row is None:return
  o._commit(row)
def deny(fn,part):
 try:fn()
 except Exception as e:assert part in str(e),str(e);return
 raise AssertionError('expected '+part)
def adapter(o):
 a=FrameAdapter.__new__(FrameAdapter);a.clock_owner=o;a.failed=a.closed=False;a.frames=a.stage_rows=0;a.max_frames=10;a.peer=None;a.origin_ns=HOST;a.first_rx=a.last_rx=None;a.last_sensor_send_ns=HOST+619853708;a.scene=None;a.current=None;a.latest_diagnostic=None;a.model=SimpleNamespace(t=0);a.sensor=[];a.capture_failure=lambda e,c,r:None
 def step(pwm,dt):a.model.t+=dt;return {'timestamp':a.model.t,'position':[0,0,0]}
 a.model.step=step
 def record_frame(frame,raw,compute,send):assert o.publication.id==939;body=compute(raw);a.sensor.append({'intentFsyncBeforeSend':True,'body':body});send(body)
 a.journal=SimpleNamespace(record_frame=record_frame,append_stage=lambda *a:None,reject=lambda *a:None)
 return a
def cold_rows(j):
 head='0'*64;out=[]
 for i,line in enumerate((j.root/'rows.jsonl').read_bytes().splitlines()):
  q=json.loads(line);b=q['body'];raw=encoded(b).rstrip(b'\n');assert b['seq']==i and b['previous']==head and q['crc32']==format(zlib.crc32(raw),'08x')and q['sha256']==hashlib.sha256(bytes.fromhex(head)+raw).hexdigest();head=q['sha256'];out.append(b['payload'])
 return out
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);groups=[];owners=[];now=[HOST+546770583]
 try:
  with patch('aeris_runtime.foundation.owner.time.monotonic_ns',side_effect=lambda:now[0]):
   o=fixture('r06-replay',now);owners.append(o);udp=UDP();sock=ClockSocket(*CTX,o.sink,maximum_seconds=180,on_matched_response=o.stage_publication,socket_factory=lambda *a:udp,now_ns=lambda:now[0],correlator_factory=TentativeCorrelator);sock.request_id=937
   sock.poll();drain(o);now[0]=HOST+559742041;udp.responses.append(response(938,now[0]));sock.poll();drain(o);assert o.calibration()['id']==938;prior=o.calibration();paused=threading.Event();release=threading.Event();errors=[]
   def hook(kind,path,size):
    if kind=='fsync'and not paused.is_set():paused.set();assert release.wait(2)
   o.diagnostic_io.hook=hook;now[0]=HOST+733294666;sock.poll();assert int.from_bytes(udp.sent[-1][0],'little')==939
   def consume():
    try:drain(o)
    except BaseException as e:errors.append(repr(e))
   worker=threading.Thread(target=consume);worker.start();assert paused.wait(1);assert o.publication.id==938
   now[0]=HOST+746294666;udp.responses.append(response(939,now[0]));sock.poll();assert o.publication.id==938 and o.pipeline.pending();groups.append('R06-TICK-fsync-blocked-socket939-query-and-original-response-progress-without-authority')
   now[0]=HOST+845214833;a=adapter(o);entered=threading.Event();original_wait=o.wait_for_frame
   def wait(*args):entered.set();return original_wait(*args)
   o.wait_for_frame=wait
   def unblock():assert entered.wait(1);now[0]=HOST+851975250;release.set()
   unblocker=threading.Thread(target=unblock);unblocker.start();clock_calls=[0]
   def read():clock_calls[0]+=1;return prior if clock_calls[0]==1 else o.calibration()
   sent=[];wire=SERVO.pack(18458,1200,0,*([1000]*16));a.receive(wire,('127.0.0.1',9000),lambda b:sent.append(b)or len(b),clock_read=read,admission_deadline_ns=HOST+945214833);worker.join(2);unblocker.join(2);assert not errors and not worker.is_alive()and not unblocker.is_alive();assert o.publication.id==939 and len(sent)==1 and a.frames==a.stage_rows==1 and a.current['unadmittedClockWait']['priorID']==938 and a.current['lastAcceptedClock']['id']==939 and a.sensor[0]['intentFsyncBeforeSend'];groups.append('R06-postread-stale938-one-unadmitted-servo-waits-new-durable939-only-no-model-before-commit')
   rows=cold_rows(o.journal);events=[r['data']for r in rows if r['eventKind']=='CLOCK'];assert [r['sequence']for r in events]==list(range(1,len(events)+1));assert [r['kind']for r in events]==['TICK','REGISTERED','RESPONSE','TICK','REGISTERED','RESPONSE'];pubs=[r['data']for r in rows if r['eventKind']=='CLOCK_PUBLICATION'];assert [r['id']for r in pubs]==[938,939]and pubs[-1]['hostReceiveNs']==HOST+746294666;assert o.pipeline.snapshot()['highWaterEvents']<=64;groups.append('all-original-CLOCK-event-order-sequence-CRC-SHA-coldjoin-and-unmodified-receive-timestamps')
   # Current pending writer is the only legal reason for a bounded wait.
   now[0]=HOST+1_200_000_000;o.pipeline.stage('CLOCK',{'run':CTX[0],'epoch':CTX[1],'boot':CTX[2],'kind':'TICK','hostNs':now[0]});row=o.pipeline.take();assert row is not None
   with patch.object(o.pipeline.condition,'wait',side_effect=lambda s:now.__setitem__(0,now[0]+6_000_000)):deny(lambda:o.wait_for_frame(now[0]+100_000_000,939),'WAIT100MS_DEADLINE')
   assert o.publication.id==939 and len(sent)==1;groups.append('no-response-pending-writer100ms-timeout-zero-additional-sensor')
   o.latch_failure(OSError('EIO_INFLIGHT'));deny(lambda:o.wait_for_frame(now[0]+100_000_000,939),'CLOCK_OWNER_FAILED');assert o.failed.endswith('EIO_INFLIGHT');groups.append('true-EIO-failure-latch-never-cleared-by-clock-pending-wait')
   # Exactly64 TOTAL entries, including a popped/inflight row.
   q=OrderedClockQueue()
   for i in range(64):q.stage('CLOCK',{'i':i})
   q.take();deny(lambda:q.stage('CLOCK',{'i':64}),'QUEUE64_OVERFLOW');assert q.snapshot()['highWaterEvents']==64 and q.snapshot()['inflightOrQueuedUnknown'];groups.append('queue64-total-including-inflight-overflow-retained-unknown-no-64plus1')
   q=OrderedClockQueue();q.close_ingress();deny(lambda:q.stage('CLOCK',{}),'INGRESS_CLOSED');groups.append('closed-source-ingress-never-stages-or-restores-authority')
   o2=fixture('foreign',now);owners.append(o2);deny(lambda:o2.sink({'run':'foreign','epoch':CTX[1],'boot':CTX[2]}),'FOREIGN_EVENT');assert not o2.pipeline.pending();groups.append('foreign-context-before-queue-zero-durablewrites')
   c=TentativeCorrelator(Context(*CTX),('127.0.0.1',9014),lambda row:None,max_pending=8,recent_limit=64)
   for i in range(8):c.register(i,1_000_000+i,Context(*CTX))
   deny(lambda:c.register(8,1_000_008,Context(*CTX)),'PENDING');assert c.snapshot()['pendingPeak']==8;groups.append('unchanged-original-correlator8-pending-requests-limit')
   # Diagnostic normal-close publication includes bounded real write/fsync IO.
   o2.done.set();o2._write_delivery();d=json.loads((o2.out/'clock-delivery-diagnostic.json').read_bytes());assert d['clockOriginalIO']['maximumRetainedOperations']==8 and d['clockOriginalIO']['threadCPUDoesNotIdentifyOSWaitReason']and len((o2.out/'clock-delivery-diagnostic.json').read_bytes())<=32768;groups.append('normal-close-diagnostic-bounded-original-write-fsync-offCPU-subspans-no-fs-only-attribution')
  report={'format':'aeris-clockpipe09-source-causal-mock','status':'PASS_SOURCE_PIPELINE_REAL_FILE_FSYNC_FAKE_TIME_UDP_NOT_ANDROID_SITL','groups':groups,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[T/'source/aeris_runtime/foundation'/n for n in('owner.py','clock_socket.py','clock_pipeline09.py','frame_adapter.py')]},'actorsStarted':False,'requestPeriodNsUnchanged':100000000,'maximumPendingRequestsUnchanged':8,'maximumQueuedAndInflight':64,'maximumUnadmittedWaitNs':100000000,'freshnessNsUnchanged':250000000,'allSensorIntentsFsyncBeforeSend':True,'noSourceTimestampRefresh':True,'scratchRemoved':str(LAB.relative_to(R))}
 finally:
  for owner in owners:owner.journal.close()
  shutil.rmtree(LAB)
 out=R/'evidence/betasim-integrated01/runtime/clockpipe09-causal-mock03.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
