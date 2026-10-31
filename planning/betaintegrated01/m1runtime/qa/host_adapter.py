"""Independent host integration probes. Fake clock datagrams; no real sockets/AP."""
from pathlib import Path
import hashlib,json,os,struct,sys,time,types,datetime
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.runtime.physics import Model,profile
from pilot.betaintegrated01.runtime.physics_reference import Model as Reference
from pilot.betaintegrated01.runtime import clock_socket
from pilot.betaintegrated01.journal import FileIO,verify_journal
out=R/('evidence/betaintegrated01-m1runtime/qa/host-adapter'+sys.argv[1]);out.mkdir()
paths=[R/'pilot/betaintegrated01/runtime'/n for n in ['frame_adapter.py','clock_socket.py','ap_stage.py','backend.py','physics.py','physics_reference.py','_sim32_kernel.cpython-314-darwin.so']]
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
before=pins();results=[]
def test(name,f):
 try:detail=f();results.append({'id':name,'pass':True,'detail':detail})
 except Exception as e:results.append({'id':name,'pass':False,'error':type(e).__name__+':'+str(e)})
def check(b,why):
 if not b:raise AssertionError(why)
fresh=lambda:{'id':1,'hostReceiveNs':time.monotonic_ns(),'offsetLowNs':0,'offsetHighNs':1}
packet=lambda frame,rate=1200:SERVO.pack(18458,rate,frame,*[1730+((frame*13+j*17)%101) if j<4 else 1000 for j in range(16)])
def normal():
 operations=[];io=FileIO(hook=lambda op,p,n:operations.append(op));config=profile('offset','gust',57)
 ref=Reference(config);m=Model(config);a=FrameAdapter(out/'normal','normal','epoch01',m,max_frames=128,io=io)
 count=0
 for i in range(96):
  raw=packet(i);pwm=SERVO.unpack(raw)[3:];want=('\n'+json.dumps(ref.step(pwm,1/1200),separators=(',',':'),allow_nan=False)+'\n').encode()
  def send(body):
   nonlocal count
   check(body==want,'sensor bytes differ at '+str(i));check('fsync'in operations,'missing file sync');operations.clear();count+=1;return len(body)
  a.receive(raw,('127.0.0.1',45100),send,clock_read=fresh)
 receipt=a.close();cold=verify_journal(out/'normal','normal','epoch01',expected_commit=receipt['commitAnchor'])
 check(cold['frames']==96 and cold['stageRows']==96 and count==96,'frame/stage count');check(cold['publicationAllowed'] is False,'publication')
 return {'frames':count,'stageRows':cold['stageRows'],'exactReferenceBytes':True,'state':cold['state']}
test('H01_EXACT_MODEL_FRAME_ORDER_AND_SYNC',normal)
def invalid(kind):
 root=out/kind;a=FrameAdapter(root,kind,'epoch01',Model(profile()),max_frames=16);sent=[]
 a.receive(packet(0),('127.0.0.1',45100),lambda b:(sent.append(b)or len(b)),clock_read=fresh)
 bad=packet(2)if kind=='gap'else packet(1,1199)if kind=='rate'else packet(1)
 peer=('127.0.0.1',45101)if kind=='peer'else('127.0.0.1',45100)
 try:a.receive(bad,peer,lambda b:(sent.append(b)or len(b)),clock_read=fresh);raise AssertionError('unexpected accepted')
 except (ValueError,RuntimeError):pass
 check(len(sent)==1 and a.failed,'unexpected dispatch/revival')
 reject=json.loads(root.with_name(root.name+'-rejected.json').read_bytes());check(reject['rawHex']==bad.hex() and reject['exactReceivedBytesRetained'] is True,'rejection lost bytes')
 return {'sendCount':len(sent),'retainedRejectedBytes':reject['inputBytes']}
for name in ['gap','rate','peer']:test('H02_REJECT_'+name.upper(),lambda name=name:invalid(name))
def stale_after_intent():
 a=FrameAdapter(out/'stale-intent','stale-intent','epoch01',Model(profile()),max_frames=16);reads=0;sends=[]
 def clock():
  nonlocal reads
  reads+=1;return fresh()if reads==1 else None
 try:a.receive(packet(0),('127.0.0.1',45100),lambda b:(sends.append(b)or len(b)),clock_read=clock);raise AssertionError('accepted expired clock')
 except (ValueError,RuntimeError):pass
 v=verify_journal(out/'stale-intent','stale-intent','epoch01');check(not sends and v['state']=='INCOMPLETE_RECORDING','false complete/send')
 return {'clockReads':reads,'sends':len(sends),'state':v['state']}
test('H03_CLOCK_EXPIRY_AFTER_INTENT_ZERO_SEND',stale_after_intent)
def shortsend():
 a=FrameAdapter(out/'shortsend','shortsend','epoch01',Model(profile()),max_frames=16)
 try:a.receive(packet(0),('127.0.0.1',45100),lambda b:len(b)-1,clock_read=fresh);raise AssertionError('shortsend accepted')
 except RuntimeError:pass
 v=verify_journal(out/'shortsend','shortsend','epoch01');check(v['state']=='INCOMPLETE_RECORDING','false complete');check(a.failed,'not fenced');return v
test('H04_SHORT_SEND_UNKNOWN',shortsend)
def clock_wire():
 class FakeSocket:
  def __init__(self):self.q=[];self.sent=[];self.closed=False
  def bind(self,peer):check(peer==('127.0.0.1',0),'bind')
  def setblocking(self,b):check(b is False,'blocking')
  def recvfrom(self,n):
   if not self.q:raise BlockingIOError()
   return self.q.pop(0)
  def sendto(self,b,peer):self.sent.append((b,peer,now[0]));return len(b)
  def close(self):self.closed=True
 fs=FakeSocket();now=[1000000000];old_socket,old_time=clock_socket.socket,clock_socket.time;rows=0
 try:
  clock_socket.socket=types.SimpleNamespace(AF_INET=2,SOCK_DGRAM=2,socket=lambda*a:fs)
  clock_socket.time=types.SimpleNamespace(monotonic_ns=lambda:now[0])
  with(out/'clock-events.jsonl').open('x')as log:
   def sink(row):
    nonlocal rows
    log.write(json.dumps(row,separators=(',',':'))+'\n');log.flush();os.fsync(log.fileno());rows+=1
   c=clock_socket.ClockSocket('clockrun','clockepoch','clockboot',sink)
   check(c.calibration()is None,'bootstrap accepted')
   c.poll()
   for i in range(1100):
    rid=struct.unpack('<Q',fs.sent[-1][0])[0];sent_at=fs.sent[-1][2];check(rid==i+1,'nonce reused')
    fs.q.append((struct.pack('<7Q',rid,sent_at-99999500,sent_at-99999400,0,0,0,0),('127.0.0.1',9014)))
    now[0]+=100000000;c.poll();check(c.calibration()is not None,'matched calibration absent')
   now[0]+=251000000;check(c.calibration()is None,'stale calibration returned')
   snap=c.close();check(fs.closed,'socket not closed');check(snap['pending']<=8 and snap['recent']<=64,'unbounded state')
  return {'exchanges':1100,'durableRows':rows,'wireRequests':len(fs.sent),'snapshot':snap,'socketType':'FAKE_NO_NETWORK'}
 finally:clock_socket.socket,clock_socket.time=old_socket,old_time
test('H05_CLOCK_SOCKET_OVER1024_EXCHANGES',clock_wire)
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'sourceChanged':before!=pins(),'results':results,'APAndroidSocketLaunches':0,'scope':'Independent current adapter mock/filesystem checks. Clock uses monkeypatched fake datagram seam, not real network; physical flight/timing not inferred'}
report['status']='PASS'if all(r['pass']for r in results)and not report['sourceChanged']else'FAIL'
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':report['sourceChanged']}))
