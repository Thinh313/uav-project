"""Final clock recvmsg/capacity policy probes on a fake socket seam."""
from pathlib import Path
import datetime,hashlib,json,struct,sys,types
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime import clock_socket as m
out=R/('evidence/betaintegrated01-m1runtime/qa/clock-final'+sys.argv[1]);out.mkdir()
source=R/'pilot/betaintegrated01/runtime/clock_socket.py';before=hashlib.sha256(source.read_bytes()).hexdigest();results=[]
class Fake:
 def __init__(self,now):self.q=[];self.sent=[];self.closed=False;self.now=now
 def bind(self,p):assert p==('127.0.0.1',0)
 def setblocking(self,b):assert b is False
 def recvmsg(self,n):
  if not self.q:raise BlockingIOError()
  return self.q.pop(0)
 def sendto(self,b,p):self.sent.append((b,p,self.now[0]));return len(b)
 def close(self):self.closed=True
def test(name,f):
 try:results.append({'id':name,'pass':True,'detail':f()})
 except Exception as e:results.append({'id':name,'pass':False,'error':type(e).__name__+':'+str(e)})
def setup(fn):
 now=[1000000000];sock=Fake(now);old_socket,old_time=m.socket,m.time
 try:
  m.socket=types.SimpleNamespace(AF_INET=2,SOCK_DGRAM=2,MSG_TRUNC=32,socket=lambda*a:sock)
  m.time=types.SimpleNamespace(monotonic_ns=lambda:now[0])
  return fn(now,sock)
 finally:m.socket,m.time=old_socket,old_time
def roundtrip(now,sock):
 rows=[];c=m.ClockSocket('run01','epoch01','boot01',rows.append);c.poll()
 for i in range(32):
  raw,peer,sent=sock.sent[-1];rid=struct.unpack('<Q',raw)[0];assert rid==i+1
  sock.q.append((struct.pack('<7Q',rid,sent-99999500,sent-99999400,0,0,0,0),[],0,('127.0.0.1',9014)))
  now[0]+=100000000;c.poll();assert c.calibration()['id']==rid
 snapshot=c.close();assert sock.closed and snapshot['recent']<=64 and snapshot['pending']<=8
 return {'roundTrips':32,'retainedEvents':len(rows),'snapshot':snapshot,'clockType':'FAKE_NO_NETWORK'}
test('F01_FINAL_RECVMSG_32_ROUNDTRIPS',lambda:setup(roundtrip))
def truncated(now,sock):
 diag=[];rows=[];c=m.ClockSocket('run02','epoch02','boot02',rows.append,diagnostic=diag.append);c.poll();sock.q.append((b'prefix',[],32,('127.0.0.1',9014)));now[0]+=100000000
 try:c.poll();raise AssertionError('truncation accepted')
 except RuntimeError:pass
 assert len(diag)==1 and diag[0]['socketTruncated'] is True and diag[0]['exactReceivedBytesRetained'] is False and diag[0]['rawHex']==b'prefix'.hex();assert c.calibration() is None;c.close();return diag
test('F02_TRUNCATION_EXACTNESS_DIAGNOSTIC',lambda:setup(truncated))
def eventcap(now,sock):
 diag=[];rows=[];c=m.ClockSocket('run03','epoch03','boot03',rows.append,maximum_seconds=1,diagnostic=diag.append)
 # Fault-injection seam: emulate the final remaining retained-event slot.
 c.events=c.max_events-1
 try:c.poll();raise AssertionError('capacity accepted')
 except RuntimeError:pass
 snap=c.close();assert len(rows)==1 and c.events==c.max_events and len(diag)==1 and diag[0]['reason']=='CLOCK_TOTAL_EVENT_CAPACITY' and snap['failed'] is not None
 return {'counterNearCapInjected':True,'retainedThisFixture':len(rows),'maxEvents':c.max_events,'snapshot':snap,'diagnostic':diag}
test('F03_HARD_EVENT_CAPACITY_FAIL_CLOSED',lambda:setup(eventcap))
manifest=R/'evidence/betaintegrated01-m1runtime/host/runtime-manifest01.json';d=json.loads(manifest.read_text());drift=[]
for name,pin in d['files'].items():
 p=R/name
 if p.stat().st_size!=pin['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=pin['sha256']:drift.append(name)
results.append({'id':'F04_FROZEN_HOST_MANIFEST_INPUTS','pass':not drift,'files':len(d['files']),'drift':drift})
after=hashlib.sha256(source.read_bytes()).hexdigest();report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'results':results,'status':'PASS'if all(r['pass']for r in results)and before==after else'FAIL','APAndroidSocketRuntimeLaunches':0,'hostManifestSHA256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'scope':'Final recvmsg/diagnostic/eventcap policy and source closure; prior1100exchange evidence remains separately versioned, no actualnetwork or physicalclock attestation'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':before!=after}))
