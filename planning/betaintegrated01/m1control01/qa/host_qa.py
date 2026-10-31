from pathlib import Path
import copy,datetime,hashlib,json,struct,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control01.mavlink import Framer,DEFINITIONS
from pilot.betaintegrated01.control01.transport import PassiveObservation,FaultState,Context
attempt=sys.argv[1]if len(sys.argv)>1 else'01';out=R/('evidence/betaintegrated01-m1control01/qa/host'+attempt);out.mkdir()
paths=[R/'pilot/betaintegrated01/control01'/s for s in ('mavlink.py','transport.py','dialect.json')]
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
before=pins();rows=[]
def test(name,f):
 try:f();rows.append({'id':name,'pass':True})
 except Exception as e:rows.append({'id':name,'pass':False,'error':repr(e)})
def require(x):
 if not x:raise AssertionError('independent assertion')
def denied(f):
 try:f()
 except Exception:return
 raise AssertionError('expected refusal')
def packet(i,payload,seq=1,system=42,component=1):
 # Independent bitwise X25 implementation, not the product crc().
 h=bytes([len(payload),0,0,seq,system,component])+i.to_bytes(3,'little')
 c=65535
 for b in h+payload+bytes([DEFINITIONS[i][2]]):
  c^=b
  for _ in range(8):c=(c>>1)^0x8408 if c&1 else c>>1
 return b'\xfd'+h+payload+struct.pack('<H',c)
hb=struct.pack('<IBBBBB',5,2,3,128,4,3)
def fragments():
 f=Framer();b=packet(0,hb)
 require(f.feed(b[:4],1)==[]);r=f.feed(b[4:],2)
 require(len(r)==1 and r[0]['system']==42 and r[0]['wireSequence']==1)
def badcrc():
 f=Framer();b=bytearray(packet(0,hb));b[-1]^=1
 denied(lambda:f.feed(bytes(b),1));require(f.failed=='CRC');denied(lambda:f.feed(packet(0,hb),2))
def stale():
 f=Framer();f.feed(packet(0,hb)[:4],1);denied(lambda:f.tick(1_500_000_002))
def bounds():
 denied(lambda:Framer().feed(b'x'*4097,1));denied(lambda:Framer().feed(b'garbage',1))
def sequence():
 events=[];p=PassiveObservation(lambda k,v:events.append((k,copy.deepcopy(v))))
 p.receive(packet(0,hb,10),100);require(p.latest['HEARTBEAT']['observedHostNs']==100)
 p.receive(packet(0,hb,10),200);p.receive(packet(0,hb,9),300)
 require(p.latest['HEARTBEAT']['observedHostNs']==100 and p.duplicate_frames==1 and p.older_frames==1)
 p.receive(packet(0,hb,11,43),400);require(p.latest['HEARTBEAT']['observedHostNs']==100)
 p.receive(packet(0,hb,11),500);require(p.latest['HEARTBEAT']['observedHostNs']==500)
 require(events[0][0]=='PASSIVE_RX' and events[1][0]=='PASSIVE_FRAME')
 require(p.snapshot()['applicationTXBytes']==0 and not hasattr(p,'send'))
def reboot():
 p=PassiveObservation(lambda k,v:None)
 b=bytearray(28);struct.pack_into('<I',b,0,1000);p.receive(packet(30,bytes(b),1),100)
 struct.pack_into('<I',b,0,50);denied(lambda:p.receive(packet(30,bytes(b),2),200))
 require(p.boot_regression is not None)
def cut():
 c=Context('run','epoch','boot');request={'run':'run','epoch':'epoch','boot':'boot','action':'CUT_NATIVE_LINK','nonce':'nonce01','hostNs':100}
 s=FaultState(c);r=s.cut(request,101);require(s.cut_latched and r['restoredAuthority']is False and r['nativeReconnectAllowed']is False);denied(lambda:s.cut(request,102))
 for key,value in [('boot','wrong'),('hostNs',True),('hostNs',200),('hostNs',-3_000_000_000),('action','RESTORE'),('nonce','')]:
  q={**request,key:value};s=FaultState(c);denied(lambda:s.cut(q,101));require(not s.cut_latched)
test('H01_FRAGMENTED_VALID_CRC',fragments);test('H02_CRC_POISON_NO_REUSE',badcrc);test('H03_STALE_PARTIAL',stale);test('H04_BOUNDS_AND_GARBAGE',bounds);test('H05_PASSIVE_DUPLICATE_FOREIGN_ZERO_TX',sequence);test('H06_PASSIVE_BOOT_REGRESSION',reboot);test('H07_CONTEXTUAL_ONE_SHOT_CUT',cut)
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'sourceChanged':before!=pins(),'results':rows,'status':'PASS'if all(r['pass']for r in rows)and before==pins()else'FAIL','scope':'Independent pure parser/passive observer/fault state only; no sockets, AP, Android, or live transport thread','actualTransportZeroTX':'NOT_CHECKED'}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'failed':[r for r in rows if not r['pass']]}))
