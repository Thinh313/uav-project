"""Independent RAM transport faults; source guards/reader, no actors or sockets."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack
import ast,hashlib,json,os,stat,sys,time,traceback
R=Path(__file__).resolve().parents[3]; S=R/'planning/hosthealth-ipc10/runtime/source'
sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import host_health as hh,ipc_trace10 as tr
H=lambda b:hashlib.sha256(b).hexdigest()
old=R/'evidence/runtime-hostguard07/qa/protocol_checks01.py'
fn=next(n for n in ast.parse(old.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='snapshot')
ns={'time':time,'H':H};exec(compile(ast.Module(body=[fn],type_ignores=[]),'explicit_old_synthetic_fixture','exec'),ns)
class Clock:
 def __init__(self):self.now=1_000_000_000_000
 def monotonic_ns(self):return self.now
class FakePath:
 parents=()
 def __init__(self,socket=False):self.socket=socket
 def resolve(self):return self
 def is_symlink(self):return False
 def lstat(self):return SimpleNamespace(st_dev=7,st_ino=11,st_uid=os.geteuid(),st_mode=(stat.S_IFSOCK|0o600)if self.socket else(stat.S_IFDIR|0o700))
 def __str__(self):return '/EXPLICIT_QA/health.sock'if self.socket else'/EXPLICIT_QA'
def binding():
 return {'version':1,'instance':'a'*32,'pid':os.getpid(),'processStart':'EXPLICIT_SYNTHETIC_QA','guardianSourceSHA256':'b'*64,'healthSourceSHA256':H((S/'aeris_runtime/host_health.py').read_bytes()),'budgetSourceIdentity':'c'*64,'budgetRoot':'/EXPLICIT_QA/budget','evidenceRoot':'/EXPLICIT_QA'}
class Wire:
 def __init__(self,b,clock,elapsed,change,raw,partial_timeout,send_error):
  self.b=b;self.clock=clock;self.elapsed=elapsed;self.change=change;self.raw=raw;self.partial_timeout=partial_timeout;self.send_error=send_error;self.sent=None;self.pos=0;self.data=None;self.calls=0
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def settimeout(self,v):assert v==.1
 def connect(self,p):self.clock.now+=1_000_000
 def sendall(self,b):
  self.sent=b;self.clock.now+=1_000_000
  if self.send_error:raise BrokenPipeError('UNKNOWN_PARTIAL_SEND')
 def recv(self,n):
  self.calls+=1
  if self.data is None:
   self.clock.now+=self.elapsed-2_000_000
   if self.raw is not None:self.data=self.raw
   else:
    q=json.loads(self.sent);v=ns['snapshot']();v['inventory']['counters'].update(metadataAccountingUpperBoundAtScan=0,metadataAccountingWriteSequenceAtScan=0)
    v={**self.b,**v,'challenge':q['challenge'],'responseHostNs':self.clock.now}
    if self.change:self.change(v)
    self.data=hh._json(v).replace(b'"owner":"guardian"',b' "owner" : "guardian" ')
  if self.partial_timeout and self.pos:raise TimeoutError('PARTIAL_TIMEOUT')
  b=self.data[self.pos:self.pos+n];self.pos+=len(b);return b
def exchange(*,elapsed=10_000_000,change=None,raw=None,peer_bad=False,partial_timeout=False,send_error=False,recorder=None,parse_delay=0,schema_delay=0,forbid_trace_work=False,nonce=None):
 c=Clock();b=binding();client=hh.GuardianClient.__new__(hh.GuardianClient);client.root=FakePath();client.path=FakePath(True);client.binding=b;client.socket_identity=(7,11);client.allow_mock=True
 client.trace=tr.TraceRing('client',b,client.path,(7,11),candidate='d'*64)
 if recorder:
  for slot in client.trace.slots:setattr(slot,recorder,lambda *a,**k:(_ for _ in()).throw(OSError('INJECTED_RECORDER_'+recorder)))
 wire=Wire(b,c,elapsed,change,raw,partial_timeout,send_error);error=None;result=None;strict=hh._strict;schema=hh._health_schema
 def delayed_parse(v):c.now+=parse_delay;return strict(v)
 def delayed_schema(v):
  try:return schema(v)
  finally:c.now+=schema_delay
 with ExitStack()as stack:
  for ctx in [patch.object(hh.os,'kill',return_value=None),patch.object(hh.socket,'socket',return_value=wire),patch.object(hh,'peer_pid',return_value=b['pid']+int(peer_bad)),patch.object(time,'monotonic_ns',c.monotonic_ns),patch.object(hh,'_strict',side_effect=delayed_parse),patch.object(hh,'_health_schema',side_effect=delayed_schema)]:stack.enter_context(ctx)
  if nonce is not None:stack.enter_context(patch.object(hh.secrets,'token_hex',return_value=nonce))
  if forbid_trace_work:
   for ctx in [patch.object(tr,'canonical',side_effect=AssertionError('TRACE_HOT_SERIALIZATION')),patch.object(tr.hashlib,'sha256',side_effect=AssertionError('TRACE_HOT_SHA')),patch.object(tr.TraceRing,'flush',side_effect=AssertionError('TRACE_HOT_FLUSH'))]:stack.enter_context(ctx)
  try:result=client()
  except BaseException as e:error=e
 original=client.trace.export();decoded=tr.verify_original(original,candidate='d'*64,binding=b,endpoint=str(client.path),endpoint_identity=(7,11),trace_pid=os.getpid(),role='client')
 return SimpleNamespace(error=error,result=result,trace=decoded,raw=original,wire=wire,ring=client.trace,binding=b)
def row(x):return x.trace['rows'][0]
def require_error(x,kind,text=None):
 assert isinstance(x.error,kind),(type(x.error).__name__,str(x.error))
 if text is not None:assert str(x.error)==text,(str(x.error),text)
 assert x.result is None
def tests():
 x=exchange(elapsed=97_000_000,parse_delay=3_000_000,schema_delay=5_000_000);assert x.error is None and row(x)['elapsedNs']==100_000_000
 assert row(x)['times']['schema_end']-row(x)['times']['schema_begin']==5_000_000
 assert row(x)['responseOriginal']==x.wire.data and b' "owner" : 'in row(x)['responseOriginal']
 yield 'exact_raw_whitespace_and_original_parse_inside_schema_outside_100ms'
 x=exchange();n=row(x)['metadata']['n'];x=exchange(raw=x.wire.data,nonce=n,forbid_trace_work=True);assert x.error is None
 yield 'no_trace_serialization_sha_or_flush_during_actual_source_guard'
 x=exchange(elapsed=100_000_001);require_error(x,RuntimeError,'HOST_HEALTH_FRESH_RESPONSE_BINDING');assert row(x)['subpredicates']['elapsedExceeds100ms']
 x=exchange(change=lambda v:v.update(challenge='e'*32));require_error(x,RuntimeError,'HOST_HEALTH_FRESH_RESPONSE_BINDING');assert row(x)['subpredicates']['challengeMismatch']
 x=exchange(change=lambda v:v.update(processStart='DIFFERENT'));require_error(x,RuntimeError,'HOST_HEALTH_FRESH_RESPONSE_BINDING');assert row(x)['subpredicates']['bindingMismatches']==['processStart']
 yield 'late_nonce_and_binding_preserve_exact_combined_primary'
 x=exchange(peer_bad=True);require_error(x,RuntimeError,'HOST_HEALTH_KERNEL_PID_BINDING');assert x.wire.sent is None and row(x)['metadata']['p']==x.binding['pid']+1
 yield 'actual_peer_refusal_precedes_any_send'
 for raw in [b'{"x":',b'\xff\n',b'{"x":1,"x":2}\n',b'{"x":NaN}\n']:
  x=exchange(raw=raw);require_error(x,Exception);assert row(x)['responseOriginal']==raw and not row(x)['flags']['accepted']
 x=exchange(raw=b'x'*4097+b'UNOBSERVED');require_error(x,ValueError,'HOST_HEALTH_IPC_BOUND');assert row(x)['responseOriginal']==b'x'*4097 and row(x)['flags']['overbound']
 x=exchange(raw=b'partial',partial_timeout=True);require_error(x,TimeoutError);assert row(x)['responseOriginal']==b'partial'and row(x)['flags']['timeout']
 yield 'malformed_partial_eof_timeout_and_exact4097_observed_prefix'
 x=exchange(raw=b'not-json\n',elapsed=200_000_000);require_error(x,json.JSONDecodeError)
 x=exchange(elapsed=200_000_000,change=lambda v:v.update(owner='FOREIGN'));require_error(x,ValueError,'HOST_HEALTH_EXACT_RESPONSE_SCHEMA')
 yield 'original_parse_and_schema_primary_win_even_when_late'
 x=exchange(send_error=True);require_error(x,BrokenPipeError);assert row(x)['flags']['request_intended']and not row(x)['flags']['send_success']and row(x)['responseOriginal']==b''
 yield 'partial_sendall_keeps_intended_buffer_and_unknown_send_completion'
 for method in ['capture','receive','mark','finish']:
  x=exchange(recorder=method);require_error(x,RuntimeError);assert not row(x)['flags']['accepted']
  x=exchange(recorder=method,raw=b'not-json\n');require_error(x,json.JSONDecodeError);assert row(x)['responseOriginal']==b'not-json\n'
 yield 'all_hot_recorder_faults_deny_valid_path_preserve_original_invalid_path'
 r=tr.TraceRing('client',binding(),'/EXPLICIT_QA',(7,11),candidate='d'*64);a=r.begin('A','QA');b=r.begin('B','QA');r.finish(a,RuntimeError('FIRST_PRIMARY'))
 b.slot.finish=lambda *a:(_ for _ in()).throw(OSError('SECOND_FINALIZER'))
 try:r.finish(b);raise AssertionError('retired in-flight health escaped after finalizer fault')
 except RuntimeError:pass
 assert r.first_failed_sequence==1
 yield 'concurrent_first_failure_and_second_finalizer_cannot_restore_acceptance_or_replace_first'
 x=exchange();raw=bytearray(x.raw);raw[-1]^=1
 try:tr.verify_original(bytes(raw),candidate='d'*64,binding=x.binding,endpoint=str(FakePath(True)),endpoint_identity=(7,11),trace_pid=os.getpid(),role='client');raise AssertionError('tamper accepted')
 except ValueError:pass
 for changes in [{'candidate':'e'*64},{'trace_pid':os.getpid()+1},{'endpoint_identity':(7,12)},{'endpoint':'/FOREIGN'}]:
  args=dict(candidate='d'*64,binding=x.binding,endpoint=str(FakePath(True)),endpoint_identity=(7,11),trace_pid=os.getpid(),role='client');args.update(changes)
  try:tr.verify_original(x.raw,**args);raise AssertionError('foreign provenance accepted')
  except ValueError:pass
 yield 'cold_original_bytes_and_external_candidate_process_endpoint_identity_bound'
def main():
 out=R/sys.argv[1];paths=[S/'aeris_runtime/host_health.py',S/'aeris_runtime/ipc_trace10.py'];pins={str(p.relative_to(R)):H(p.read_bytes())for p in paths};passed=[];failure=None
 try:
  for item in tests():passed.append(item)
 except BaseException:failure=traceback.format_exc()
 end={str(p.relative_to(R)):H(p.read_bytes())for p in paths};status='PASS_SCOPED_RAM_SOURCE_FAULTS_NOT_ACTUAL_HEALTH'if failure is None and pins==end else'FAIL_OR_SOURCE_DRIFT'
 v={'format':'aeris-independent-hosthealth-ipc10-causal-qa','status':status,'passed':passed,'failure':failure,'sourceSHA256':pins,'sourceUnchangedDuringChecks':pins==end,'qaSourceSHA256':H(Path(__file__).read_bytes()),'fixtureSource':str(old.relative_to(R)),'fixtureSourceSHA256':H(old.read_bytes()),'fixtureHealth':'EXPLICIT_SYNTHETIC_TYPED_HEALTH','transport':'RAM_FAKE_SOCKET_AND_MONOTONIC_CLOCK','QAActorsStarted':False,'actualPeerOrAndroidClaim':False,'scratchCreated':False}
 with out.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({'status':status,'passedGroups':len(passed),'failure':failure,'path':str(out),'sha256':H(out.read_bytes())}))
 if failure is not None:raise SystemExit(1)
if __name__=='__main__':main()
