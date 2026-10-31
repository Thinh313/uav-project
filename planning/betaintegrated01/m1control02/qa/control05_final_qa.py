from pathlib import Path
import copy,datetime,hashlib,json,struct,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control05.bootstrap import StartupEnvelope
from pilot.betaintegrated01.control05.transport import PassiveStartup
from pilot.betaintegrated01.control05.geocollect import collect
from pilot.betaintegrated01.control05.audit import audit_transport
from pilot.betaintegrated01.control05.native_release import release_witness,wire_release_observations
from pilot.betaintegrated01.control01.mavlink import Framer,DEFINITIONS
O=R/'evidence/betaintegrated01-m1control02/qa/control05-final01';O.mkdir();paths=list((R/'pilot/betaintegrated01/control05').glob('*.py'));before={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths};cases=[]
def require(x,s='assertion'):
 if not x:raise AssertionError(s)
def denied(f):
 try:f()
 except(Exception):return
 raise AssertionError('expectedrefusal')
def test(label,f):
 try:f();cases.append({'id':label,'pass':True})
 except Exception as e:cases.append({'id':label,'pass':False,'error':repr(e)})
def hb():
 p=struct.pack('<IBBBBB',5,2,3,129,4,3);h=bytes([len(p),0,0,1,42,1,0,0,0]);c=65535
 for b in h+p+bytes([DEFINITIONS[0][2]]):
  c^=b
  for _ in range(8):c=(c>>1)^0x8408 if c&1 else c>>1
 return b'\xfd'+h+p+struct.pack('<H',c)
def fragmented():
 for pairs in range(4):
  e=StartupEnvelope();f=Framer();classified=[];frames=[]
  for n,b in enumerate(b'0 '*pairs+hb()):
   raw,p=e.feed(bytes([b]),n*1_000_000);classified+=p;frames+=f.feed(raw,n*1_000_000)
  require(len(classified)==pairs and len(frames)==1 and frames[0]['id']==0)
def strict():
 for raw in (b'0 '*4,b'garbage',b' ',b'0!',b'0\xfd'):denied(lambda:StartupEnvelope().feed(raw,1))
def timeout():
 e=StartupEnvelope();e.feed(b'0',1);require(e.feed(b' ',200000001)[1][0]['pair']==1)
 e=StartupEnvelope();e.feed(b'0',1);denied(lambda:e.feed(b' ',200000002))
def late():
 e=StartupEnvelope();f=Framer();b,p=e.feed(hb(),1);f.feed(b,1);b,p=e.feed(b'0 ',2);require(b==b'0 'and not p);denied(lambda:f.feed(b,2))
def eof():
 s=PassiveStartup();s.begin(0);s.receive(b'0 ');denied(lambda:s.eof(1));denied(lambda:s.check(20000000001))
def wiring():
 b=R/'evidence/betaintegrated01-m1control02/host/startup05-mock01/initial-eof-then-valid';r=json.loads((b/'transport-result.json').read_bytes());a=audit_transport(b,'run-initial-eof-then-valid','epoch-initial-eof-then-valid','boot-initial-eof-then-valid',expected_anchor=r['commitAnchor']);require(a['startupResetPairsClassified']==3 and a['startupRawBytesRetained']==6);rows=collect(b,'run-initial-eof-then-valid','epoch-initial-eof-then-valid','boot-initial-eof-then-valid');require(len(rows)==1 and rows[0]['kind']=='heartbeat')
test('P01_ALL_ZERO_TO_THREE_FRAGMENTED_SOURCE_PAIRS_PLUS_REAL_CRC_HB',fragmented);test('P02_STRICT_NOT_GENERIC_RESYNC',strict);test('P03_FRAGMENT_200MS_BOUNDARY',timeout);test('P04_PERMANENT_MAV_LATCH_LATE_PREFIX_REJECTED',late);test('P05_ANY_PREFIXBYTE_EOF_FATAL_FIRSTMAV20S_BOUND',eof);test('P06_COLD_RAW_CLASSIFICATION_AND_GEOCOLLECT_FULL_WIRING',wiring)
saved=json.loads((R/'evidence/betaintegrated01-m1control02/qa/release01/results.json').read_bytes());wire=saved['wire']
for c in saved['cases']:
 def f(c=c):
  d=c['descriptor'];r=release_witness(d,c['descriptorAnchor'],'nominal','epoch01','boot01',wire);require(r['status']==('HOST_NATIVE_RELEASE_WITNESS_PASS'if c['id']=='baseline'else'HOST_NATIVE_RELEASE_NOT_READY'));return r
 test('R_'+c['id'],f)
base=saved['cases'][0];D=base['descriptor'];A=base['descriptorAnchor']
def extra_rc():
 w=copy.deepcopy(wire);w['nativeForwardedTimeline'].insert(-1,dict(hostNs=5300000000,kind='RC_OVERRIDE',channels=[1550,1500,1500,1500]+[65535]*14,forwardPitchHeld=False,wireSHA256='f'*64));require(release_witness(D,A,'nominal','epoch01','boot01',w)['status']=='HOST_NATIVE_RELEASE_NOT_READY')
def coalesced():
 w=copy.deepcopy(wire)
 for x in w['nativeForwardedTimeline']:
  if x['kind']=='RC_OVERRIDE'and x['hostNs']>5000000000:x['hostNs']=5100000000
 require(release_witness(D,A,'nominal','epoch01','boot01',w)['status']=='HOST_NATIVE_RELEASE_WITNESS_PASS')
def ack_only():
 w=copy.deepcopy(wire);w['passiveTimeline']=[dict(hostNs=5400000000,kind='COMMAND_ACK',command=176,result=0)];require(release_witness(D,A,'nominal','epoch01','boot01',w)['status']=='HOST_NATIVE_RELEASE_NOT_READY')
test('R_EXTRA_ROLL_RC_AFTER_BRAKE_REFUSED',extra_rc);test('R_COALESCED_HOST_NEUTRAL_RELEASE_TIMESTAMP_ORDER_FROM_BYTES',coalesced);test('R_ACK_NEVER_EXECUTION',ack_only)
after={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths};r={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(x['pass']for x in cases)and before==after else'FAIL','cases':cases,'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'scope':'Independent startupgrammar/coldwiring plus integrity-valid nativephasefixtures; noAPAndroidservices orproductedits. NativeUP/newlease authority needs separateactual audit.','oldReproProofSourcePreserved':'qa/native_release_pre01.py','newRawCopies':0};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'groups':len(cases),'failed':[x['id']for x in cases if not x['pass']]}))
