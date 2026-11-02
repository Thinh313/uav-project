"""Mock/fault injection. No pmset, Android, SITL or real child starts."""
from pathlib import Path
import hashlib,io,json,os,struct,subprocess,sys,tempfile,threading,time,types,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent/'source';sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import power_worker as P
from aeris_runtime.metadata_budget import MetadataBudget
OUT=b"Now drawing from 'AC Power'\n -InternalBattery-0\t65%; charging; present: true\n"
class MockProcess:
 def __init__(self,mode='valid'):
  self.pid=987654;self.returncode=None;self.mode=mode;self.stopped=False;self.requests=[];self.errors=[]
  a,b=os.pipe();self.child_in=os.fdopen(a,'rb',buffering=0);self.stdin=os.fdopen(b,'wb',buffering=0)
  a,b=os.pipe();self.stdout=os.fdopen(a,'rb',buffering=0);self.child_out=os.fdopen(b,'wb',buffering=0)
  a,b=os.pipe();self.stderr=os.fdopen(a,'rb',buffering=0);self.child_err=os.fdopen(b,'wb',buffering=0)
  self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def poll(self):return self.returncode
 def wait(self,timeout=None):
  self.thread.join(timeout)
  if self.thread.is_alive():raise subprocess.TimeoutExpired('mock',timeout)
  return self.returncode
 def terminate(self):self.stopped=True
 def kill(self):self.stopped=True
 def run(self):
  try:
   while not self.stopped:
    raw=P._read_exact(self.child_in,P.REQUEST.size)
    if raw is None:break
    self.requests.append(raw);magic,seq,pid,ppid,instance,nonce,request=P.REQUEST.unpack(raw);qs=time.monotonic_ns();qe=qs+10
    fields=[P.MAGIC,seq,pid,ppid,777777,instance,nonce,qs,qe,0,1,len(OUT),0,0,qs,1,0];body=OUT
    if self.mode=='pid':fields[2]+=1
    if self.mode=='parent':fields[3]+=1
    if self.mode=='sequence':fields[1]+=1
    if self.mode=='instance':fields[5]=b'x'*16
    if self.mode=='nonce':fields[6]=b'y'*16
    if self.mode=='stale':fields[7]=request-1;fields[8]=qs
    if self.mode=='future':fields[8]=qs+P.FRESH_NS
    if self.mode=='cpu':fields[-1]=2
    if self.mode=='stdoutbound':fields[11]=194
    if self.mode=='stderrbound':fields[12]=130
    if self.mode=='errorbound':fields[13]=513
    if self.mode=='incomplete':fields[10]=0
    if self.mode=='exit':fields[9]=3
    if self.mode=='stderr':self.child_err.write(b'injected stderr');continue
    if self.mode=='partial':self.child_out.write(P.RESPONSE.pack(*fields)[:8]);break
    if self.mode=='zero':break
    if self.mode=='error':fields[13]=3;body+=b'EIO'
    self.child_out.write(P.RESPONSE.pack(*fields)+body)
  except BaseException as e:self.errors.append(str(e))
  finally:
   for f in(self.child_in,self.child_out,self.child_err):
    try:f.close()
    except OSError:pass
   self.returncode=0
class WorkerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='mock-power-',dir=R/'evidence/hostisolate14');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.b=MetadataBudget(self.root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);self.b.admit();self.b.require_real_actor=lambda:None;self.workers=[];self.addCleanup(self.close_workers)
 def close_workers(self):
  for w in self.workers:
   try:w.close()
   except BaseException:pass
 def make(self,mode='valid'):
  if self.workers:
   self.root=self.root/'next';self.root.mkdir();self.b=MetadataBudget(self.root/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:100*2**30,mock=True);self.b.admit();self.b.require_real_actor=lambda:None
  calls=[]
  def spawn(*a,**kw):calls.append((a,kw));return MockProcess(mode)
  w=P.PowerWorker(self.b,'guardian',self.root/'guardian',spawn=spawn);self.workers.append(w);w.start();return w,calls
 def test_repeated_queries_no_parent_spawn_and_preserve_raw_bound_times(self):
  w,calls=self.make();first=w.query();second=w.query();self.assertEqual(len(calls),1);self.assertEqual(first['stdout'],OUT);self.assertEqual(len(first['binding']),92);self.assertLessEqual(first['ended'],P.BINDING.unpack(first['binding'])[2]);self.assertNotEqual(first['binding'],second['binding']);self.assertIsNone(second['failure']);c=w.close();self.assertEqual(c['queriesDispatched'],2);self.assertTrue(c['physicalClosed']);self.assertTrue(c['stdoutEOF']);self.assertTrue(c['stderrEOF']);self.assertFalse(c['flightAcceptance']);self.assertIsNone(w.lease)
 def test_foreign_replayed_or_bad_clock_response_fails_closed(self):
  for mode in('pid','parent','sequence','instance','nonce','stale','future','cpu','stdoutbound','stderrbound','errorbound','stderr','partial','zero'):
   with self.subTest(mode=mode):
    w,_=self.make(mode)
    with self.assertRaises((RuntimeError,TimeoutError)):w.query()
    first=w.failure
    with self.assertRaises(type(first)):w.query()
    self.assertIs(w.failure,first)
    try:w.close()
    except RuntimeError:pass
 def test_failed_capture_retains_response_not_healthy(self):
  for mode in('incomplete','exit','error'):
   with self.subTest(mode=mode):
    w,_=self.make(mode);r=w.query();self.assertIsNotNone(r['failure']);self.assertEqual(r['stdout'],OUT);self.assertIn(w.last_response['sequence'],(1,));self.assertIs(w.failure,r['failure'])
    try:w.close()
    except RuntimeError:pass
 def test_no_automatic_restart_or_second_start(self):
  w,c=self.make();w.query();w.close()
  with self.assertRaisesRegex(RuntimeError,'ONE_START'):w.start()
  with self.assertRaisesRegex(RuntimeError,'CLOSED'):w.query()
  self.assertEqual(len(c),1)
 def test_actual_helper_death_veto_without_next_query(self):
  w,_=self.make();w.process.returncode=12
  with self.assertRaisesRegex(RuntimeError,'DEAD'):w.check_alive()
  self.assertEqual(w.seq,0)
  w.process.returncode=None
 def test_query_cap_no_extra_request(self):
  w,_=self.make();w.seq=P.MAX_QUERIES
  with self.assertRaisesRegex(RuntimeError,'QUERY_CAP'):w.query()
  self.assertEqual(w.process.requests,[])
 def test_counter_exhaustion_blocks_spawn_before_actor(self):
  [self.b.tick('diagnosticChildren')for _ in range(4)];calls=[];w=P.PowerWorker(self.b,'guardian',self.root/'guardian',spawn=lambda*a,**k:calls.append(1));self.workers.append(w)
  with self.assertRaises(Exception):w.start()
  self.assertEqual(calls,[]);self.assertIsNone(w.process)
 def test_partial_start_bind_failure_reaps_child_no_new_spawn(self):
  calls=[]
  def spawn(*a,**k):p=MockProcess();calls.append(p);return p
  w=P.PowerWorker(self.b,'guardian',self.root/'guardian',spawn=spawn);self.workers.append(w)
  with patch.object(self.b,'bind_lease_child',side_effect=OSError('injected bind EIO')):
   with self.assertRaisesRegex(OSError,'bind EIO'):w.start()
  self.assertIsNotNone(calls[0].poll());self.assertEqual(len(calls),1);self.assertIsNone(w.lease)
 def test_launch_receipt_EIO_preserves_failure_and_reaps(self):
  w=P.PowerWorker(self.b,'guardian',self.root/'guardian',spawn=lambda*a,**k:MockProcess());self.workers.append(w)
  real=w._put
  def put(name,v):
   if name=='power-helper-launch.json':raise OSError('injected launch fsync')
   return real(name,v)
  with patch.object(w,'_put',side_effect=put):
   with self.assertRaisesRegex(OSError,'launch fsync'):w.start()
  self.assertIsNotNone(w.process.poll());self.assertEqual(str(w.failure),'injected launch fsync')
 def test_close_receipt_EIO_is_not_drained_or_retry_success(self):
  w,_=self.make();w.query()
  with patch.object(w,'_put',side_effect=OSError('injected close fsync')):
   with self.assertRaisesRegex(RuntimeError,'CLOSE_FAILED'):w.close()
  self.assertIsNotNone(w.lease);self.assertIsNone(w.closure)
  with self.assertRaises(RuntimeError):w.close()
 def test_original_two_second_deadline_refuses_no_reply(self):
  w,_=self.make();clock=iter([0,P.FRESH_NS+1]);w.now=lambda:next(clock,P.FRESH_NS+1)
  with self.assertRaisesRegex(TimeoutError,'2S_DEADLINE'):w.query()
 def test_drain_closed_outputs_and_idempotence(self):
  w,_=self.make();w.query();a=w.close();b=w.close();self.assertEqual(a,b);self.assertEqual(self.b.snapshot()['counters']['diagnosticChildren'],1)
if __name__=='__main__':unittest.main(verbosity=2)
