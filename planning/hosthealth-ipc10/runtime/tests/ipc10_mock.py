from pathlib import Path
import ast,hashlib,json,os,shutil,socket,sys,tempfile,time,threading,argparse
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4];SOURCE=Path(__file__).resolve().parents[1]/'source';sys.path[:0]=[str(SOURCE),str(ROOT)];os.environ['AERIS_REPOSITORY_ROOT']=str(ROOT)
from aeris_runtime import host_health as hh,ipc_trace10 as trace

H=lambda b:hashlib.sha256(b).hexdigest()
node=ast.parse((ROOT/'evidence/runtime-hostguard07/qa/protocol_checks01.py').read_text());fn=next(x for x in node.body if isinstance(x,ast.FunctionDef)and x.name=='snapshot');ns={'time':time,'H':H};exec(compile(ast.Module(body=[fn],type_ignores=[]),'explicit_old_synthetic_snapshot','exec'),ns)
def snapshot():
 v=ns['snapshot']();v['inventory']['counters'].update(metadataAccountingUpperBoundAtScan=0,metadataAccountingWriteSequenceAtScan=0);return v
def binding():return {'version':1,'instance':'a'*32,'pid':os.getpid(),'processStart':'EXPLICIT_MOCK_ONLY','guardianSourceSHA256':'b'*64,'healthSourceSHA256':hh.source_sha(),'budgetSourceIdentity':'c'*64,'budgetRoot':str(ROOT/'evidence/hosthealth-ipc10/mock-budget'),'evidenceRoot':str(ROOT/'evidence/hosthealth-ipc10/mock')}
class Clock:
 def __init__(self):self.n=1000000000000
 def monotonic_ns(self):return self.n
class Wire:
 def __init__(self,b,clock,duration,change=None,raw=None,send_error=False,recv_error=False):self.b=b;self.clock=clock;self.duration=duration;self.change=change;self.raw=raw;self.send_error=send_error;self.recv_error=recv_error;self.sent=None;self.offset=0;self.first=True
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def settimeout(self,x):pass
 def connect(self,p):pass
 def sendall(self,raw):
  self.sent=raw
  if self.send_error:raise BrokenPipeError('explicit unknown partial send')
 def recv(self,n):
  if self.first:
   self.first=False;self.clock.n+=self.duration
   if self.recv_error:self.data=b'partial'
   elif self.raw is not None:self.data=self.raw
   else:
    q=json.loads(self.sent);v={**self.b,**snapshot(),'challenge':q['challenge'],'responseHostNs':self.clock.n}
    if self.change:self.change(v)
    self.data=hh._json(v)
  if self.recv_error and self.offset:raise socket.timeout('explicit partial timeout')
  result=self.data[self.offset:self.offset+n];self.offset+=len(result);return result

def fixture(root,clock):
 root.mkdir();os.chmod(root,0o700);path=root/'health.sock';actual=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);actual.bind(str(path));os.chmod(path,0o600);b=binding();client=hh.GuardianClient.__new__(hh.GuardianClient);client.root=root;client.binding=b;client.path=path;client.socket_identity=(path.stat().st_dev,path.stat().st_ino);client.allow_mock=True;client.trace=trace.TraceRing('client',b,path,client.socket_identity,candidate='d'*64);return client,actual
def exchange(root,*,duration=10000000,change=None,raw=None,peer=None,send_error=False,recv_error=False,finish_error=False):
 root=root.parent/H(root.name.encode())[:5];clock=Clock();client,actual=fixture(root,clock);wire=Wire(client.binding,clock,duration,change,raw,send_error,recv_error);error=None;result=None
 try:
  if finish_error:
   for s in client.trace.slots:s.finish=lambda e=None:(_ for _ in()).throw(OSError('injected finalizer fault'))
  with patch.object(hh.socket,'socket',return_value=wire),patch.object(hh,'peer_pid',return_value=os.getpid()if peer is None else peer),patch.object(time,'monotonic_ns',clock.monotonic_ns):
   try:result=client()
   except BaseException as e:error=e
  decoded=trace.decode(client.trace.export(),expected_candidate='d'*64,expected_binding=client.binding)
  return error,result,decoded,client,wire
 finally:actual.close();(root/'health.sock').unlink();root.rmdir()

def run(out):
 scratch=Path(tempfile.mkdtemp(prefix='m',dir=ROOT/'evidence/hosthealth-ipc10'));groups=[]
 try:
  a=exchange(scratch/'boundary',duration=100000000);assert a[0]is None and a[2]['rows'][0]['elapsedNs']==100000000
  b=exchange(scratch/'late',duration=100000001);assert str(b[0])=='HOST_HEALTH_FRESH_RESPONSE_BINDING'and b[2]['rows'][0]['subpredicates']['elapsedExceeds100ms'];groups.append('original100ms_exact_boundary_and_late_combined_primary')
  c=exchange(scratch/'nonce',change=lambda v:v.update(challenge='e'*32));assert str(c[0])=='HOST_HEALTH_FRESH_RESPONSE_BINDING'and c[2]['rows'][0]['subpredicates']['challengeMismatch']
  d=exchange(scratch/'binding',change=lambda v:v.update(processStart='FOREIGN'));assert str(d[0])=='HOST_HEALTH_FRESH_RESPONSE_BINDING'and d[2]['rows'][0]['subpredicates']['bindingMismatches']==['processStart']
  e=exchange(scratch/'peer',peer=os.getpid()+1);assert str(e[0])=='HOST_HEALTH_KERNEL_PID_BINDING'and e[4].sent is None;groups.append('nonce_binding_and_actual_peer_source_order')
  for name,raw in [('partial',b'{"x":'),('invalidutf8',b'\xff\n'),('duplicate',b'{"x":1,"x":2}\n'),('overflow',b'x'*4097)]:
   x=exchange(scratch/name,raw=raw);assert x[0]is not None and x[2]['rows'][0]['responseOriginal']==raw
   if name=='overflow':assert x[2]['rows'][0]['flags']['overbound']
  x=exchange(scratch/'timeout',recv_error=True);assert isinstance(x[0],TimeoutError)and x[2]['rows'][0]['responseOriginal']==b'partial'and x[2]['rows'][0]['flags']['timeout'];groups.append('exact_partial_eof_timeout_utf8_duplicate_and4097_prefix')
  x=exchange(scratch/'parse_late',duration=200000000,raw=b'not-json\n');assert isinstance(x[0],json.JSONDecodeError)and x[2]['rows'][0]['elapsedNs']is None
  x=exchange(scratch/'schema_late',duration=200000000,change=lambda v:v.update(owner='FOREIGN'));assert str(x[0])=='HOST_HEALTH_EXACT_RESPONSE_SCHEMA'and x[2]['rows'][0]['elapsedNs']==200000000;groups.append('original_parse_schema_precede_latency_rejection')
  x=exchange(scratch/'send_unknown',send_error=True);assert isinstance(x[0],BrokenPipeError)and x[2]['rows'][0]['flags']['request_intended']and not x[2]['rows'][0]['flags']['send_success']
  x=exchange(scratch/'recorder_good',finish_error=True);assert str(x[0])=='HOST_HEALTH_IPC_RECORDER_FAILED'and not x[2]['rows'][0]['flags']['accepted']
  x=exchange(scratch/'recorder_primary',duration=100000001,finish_error=True);assert str(x[0])=='HOST_HEALTH_FRESH_RESPONSE_BINDING'and x[2]['rows'][0]['responseOriginal'];groups.append('unknown_partial_send_and_recorder_failure_never_masks_primary')
  ring=trace.TraceRing('client',binding(),'/explicit/mock', (1,2),candidate='d'*64)
  for n in range(17):s=ring.begin(str(n),'mock');s.capture('request',b'x'*257);s.capture('response',b'y'*4097);ring.finish(s)
  v=trace.decode(ring.export());assert [z['metadata']['s']for z in v['rows']]==list(range(10,18))and v['header']['overwritten']==9 and len(ring.export())<=49152
  s=ring.begin('FAIL','mock');ring.finish(s,ValueError('primary'));saved=ring.export()
  try:ring.begin('later','mock');assert False
  except RuntimeError as e:assert str(e)=='IPC10_FROZEN_NO_NEW_ACCEPTANCE'
  assert trace.decode(ring.export())['rows'][-1]['metadata']['n']=='FAIL'
  inflight=trace.TraceRing('server',binding(),'/mock',(1,2))
  for n in range(8):inflight.begin(str(n),'mock')
  try:inflight.begin('overflow','mock');assert False
  except RuntimeError:pass
  groups.append('ring8_wrap_inflight_bound_failure_freeze_and48KiB')
  raw=bytearray(saved);raw[-1]^=1
  try:trace.decode(bytes(raw));assert False
  except ValueError:pass
  try:trace.verify_original(saved,candidate='e'*64,binding=binding(),endpoint='/explicit/mock',endpoint_identity=(1,2),trace_pid=os.getpid(),role='client');assert False
  except ValueError:pass
  groups.append('cold_exact_crc_sha_and_external_candidate_binding')
  for label,malformed in [('guard-valid',False),('parse-bad',True)]:
   with patch.object(trace.Exchange,'capture',side_effect=OSError('injected capture failure')):
    x=exchange(scratch/label,raw=b'bad-json\n'if malformed else None)
   if malformed:assert isinstance(x[0],json.JSONDecodeError)and x[2]['rows'][0]['responseOriginal']==b'bad-json\n'
   else:assert str(x[0])=='HOST_HEALTH_IPC_RECORDER_FAILED'and not x[2]['rows'][0]['flags']['accepted']
  groups.append('capture_fault_retains_raw_and_original_parse_primary')
  concurrent=trace.TraceRing('client',binding(),'/mock',(1,2));a=concurrent.begin('A','mock');b=concurrent.begin('B','mock');concurrent.finish(a,ValueError('first-primary'));b.flag('accepted')
  try:concurrent.finish(b);assert False
  except RuntimeError as e:assert str(e)=='IPC10_FROZEN_NO_NEW_ACCEPTANCE'
  v=trace.decode(concurrent.export());assert v['header']['firstFailedSequence']==1 and not v['rows'][1]['flags']['accepted'];groups.append('already_inflight_acceptance_retired_after_first_failure')

 finally:shutil.rmtree(scratch)
 report={'format':'aeris-ipc10-builder-mock','scope':'EXPLICIT_SYNTHETIC_SOCKET_TRANSPORT_REAL_SOURCE_GUARDS_NOT_ANDROID_OR_ACTUAL_HEALTH','groups':groups,'passed':len(groups),'sourceSHA256':{p.name:H(p.read_bytes())for p in [SOURCE/'aeris_runtime/host_health.py',SOURCE/'aeris_runtime/ipc_trace10.py']},'scratchRemoved':not scratch.exists(),'actorsStarted':False,'status':'PASS'}
 with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS','groups':len(groups),'report':str(out)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
