from pathlib import Path
import ast,datetime,hashlib,json,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control02.transport import PassiveStartup
out=R/'evidence/betaintegrated01-m1control01/qa/startup02';out.mkdir();cases=[]
def check(name,f):
 try:f();cases.append({'id':name,'pass':True})
 except Exception as e:cases.append({'id':name,'pass':False,'error':repr(e)})
def require(x):
 if not x:raise AssertionError('independent assertion')
def denied(f):
 try:f()
 except RuntimeError:return
 raise AssertionError('expected refusal')
def initial():
 p=PassiveStartup();p.begin(100);a=p.eof(200);b=p.eof(300)
 require(a['beforeAnyAPByte']is True and b['initialEOFNumber']==2 and p.bytes_seen==0)
 require(a['applicationTXBytes']==0)
def partial():
 p=PassiveStartup();p.begin(100);p.eof(200);p.receive(b'\xfd');denied(lambda:p.eof(300));require(p.bytes_seen==1)
def foreign():
 p=PassiveStartup();p.begin(100);p.receive(b'foreign-invalid');denied(lambda:p.eof(200))
def timeout():
 p=PassiveStartup();p.begin(100);p.check(20_000_000_100);denied(lambda:p.check(20_000_000_101));denied(lambda:p.eof(20_000_000_101))
def regression():
 p=PassiveStartup();denied(lambda:p.check(0));p.begin(100);denied(lambda:p.eof(99))
def fixedbudget():require(PassiveStartup.maximum_wait_ns==20_000_000_000 and PassiveStartup.maximum_attempts==200)
check('PRE_BYTE_INITIAL_EOFS_RETAINED_RETRY_ONLY',initial);check('PARTIAL_FIRST_BYTE_LATCHES_EOF_FATAL',partial);check('FOREIGN_INVALID_FIRST_BYTES_LATCH_FATAL',foreign);check('REAL_WINDOW_BOUND_NO_UNLIMITED_RETRY',timeout);check('UNSTARTED_CLOCK_REGRESSION_REFUSED',regression);check('FINITE_DECLARED_ATTEMPT_WINDOW',fixedbudget)
pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (R/'pilot/betaintegrated01/control02').glob('*.py')}
for p in (R/'pilot/betaintegrated01/control02').glob('*.py'):ast.parse(p.read_bytes())
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(c['pass']for c in cases)else'FAIL','cases':cases,'sourceSHA256':pins,'sourceReview':'Minimal delta: onlyPassiveStartup + bound prebyteEOF branch; any byteslatchbeforeparse; oldsourceunchanged; backendalgorithmunchangedapartfrom source labelandrelativepackage import','scope':'Pure bootstrapstate tests+source review, no sockets/thread/services/AP/Android; actualstartupnotchecked'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(cases)}))
