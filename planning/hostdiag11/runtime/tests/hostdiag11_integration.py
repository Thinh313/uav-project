from pathlib import Path
import contextlib,hashlib,json,os,shutil,socket,sys,tempfile,threading,time,types
from unittest.mock import patch
from hostdiag11_mock import R,S,observer
from aeris_runtime import host_health as hh,ipc_trace10 as ipc,guardian_cause11 as cause,darwin_disk11 as disk,product_runtime as runtime
from aeris_runtime.metadata_budget import MetadataBudget,_bound

def run():
 root=Path(tempfile.mkdtemp(prefix='k',dir=R/'evidence/hostdiag11'));groups=[]
 try:
  endpoint=root/'h';endpoint.mkdir();os.chmod(endpoint,0o700);bind={'version':1,'instance':'a'*32,'pid':os.getpid(),'processStart':'EXPLICIT_SYNTHETIC_START','guardianSourceSHA256':'b'*64,'healthSourceSHA256':hh.source_sha(),'budgetSourceIdentity':'c'*64,'budgetRoot':str(root/'metadata-budget'),'evidenceRoot':str(root)}
  class DiskGuardError(RuntimeError):pass
  primary=DiskGuardError('EXPLICIT_MOCK_DISK_FORECAST')
  def reject():raise primary
  health=types.SimpleNamespace(budget=types.SimpleNamespace(publication=contextlib.nullcontext),check=reject,snapshot=lambda:(_ for _ in()).throw(AssertionError('FAULT_MUST_NOT_RETURN_HEALTH')),latch=lambda e:None)
  server=hh.HealthServer(endpoint,health,bind);server.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.socket.bind(str(server.path));os.chmod(server.path,0o600);server.inode=server.path.stat().st_ino;identity=(server.path.stat().st_dev,server.inode);server.socket.listen(1);server.socket.settimeout(.1);server.trace=ipc.TraceRing('server',bind,server.path,identity,candidate='d'*64);server.thread=threading.Thread(target=server._run,name='hostdiag11-explicit-synthetic-socket',daemon=True)
  client=hh.GuardianClient.__new__(hh.GuardianClient);client.root=endpoint;client.path=server.path;client.socket_identity=identity;client.binding=bind;client.allow_mock=True;client.trace=ipc.TraceRing('client',bind,server.path,identity,candidate='d'*64)
  error=None
  try:
   server.thread.start()
   try:client()
   except BaseException as e:error=e
  finally:server.close()
  assert type(error)is ValueError and str(error)=='HOST_HEALTH_TYPED_RESPONSE';annotation=cause.diagnostic(error);assert annotation['status']=='SOURCE_BOUND_DIAGNOSTIC_ONLY'and annotation['failure']=='DiskGuardError:EXPLICIT_MOCK_DISK_FORECAST'and annotation['authority']is False
  a=ipc.verify_original(client.trace.export(),candidate='d'*64,binding=bind,endpoint=server.path,endpoint_identity=identity,trace_pid=os.getpid(),role='client');b=ipc.verify_original(server.trace.export(),candidate='d'*64,binding=bind,endpoint=server.path,endpoint_identity=identity,trace_pid=os.getpid(),role='server');assert ipc.correlate(a,b)[0]['status']=='EXACT_NONCE_AND_RAW_BYTES_JOINED';assert a['rows'][0]['flags']['accepted']is False and a['rows'][0]['flags']['schema']is False;groups.append('real_unix_kernel_peer_authenticated_fault_exact_primary_schema_rejection_and_raw_nonce_join')
  fixture=root/'budget';fixture.mkdir();(fixture/'diagnostics').mkdir();(fixture/'guardian').mkdir();budget=MetadataBudget(fixture/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:20*2**30,mock=True);budget.admit();budget.write('external_task',fixture/'diagnostics/exhaust.bin',b'x'*(1024*1024));assert budget.snapshot()['remaining']['external_task']==0
  # Reports absent is the true worst source lifecycle: guardian must exist
  # before an IPC trace exists; owner-error creates the one missing directory.
  assert not(fixture/'reports').exists();assert _bound(fixture/'reports/owner-error.txt',16384,False)==20480
  for name,n in [('reports/owner-error.txt',16384),('reports/ui-failure-final.json',32768),('reports/owner-terminal.json',4096),('reports/hosthealth-ipc-client.bin',49152),('guardian/hosthealth-ipc-server.bin',49152),('reports/host-disk-attribution.bin',65536)]:budget.write('closure',fixture/name,b'x'*n,closing=True)
  state=budget.snapshot();assert state['closingOwners']['closure']==8192;groups.append('all_original_closure_maxima_plus64KiB_with_directory_rounding_221184_of229376_no_new_owner')
  for name,raw,append in [('reports/other-disk.bin',b'x',False),('reports/host-disk-attribution.bin',b'x'*65537,False),('reports/host-disk-attribution.bin',b'x',True)]:
   try:budget.write('closure',fixture/name,raw,append=append,closing=True);raise AssertionError('invalid path/bound accepted')
   except ValueError:pass
  groups.append('exact_single_hostdisk_path64KiB_no_append_or_unknown_path')
  second=root/'eio';second.mkdir();(second/'reports').mkdir();budget2=MetadataBudget(second/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:20*2**30,mock=True);budget2.admit();o,p,c=observer(1);o.sample();o.retire();o.stop();real_write=os.write
  def eio(fd,raw):
   target=second/'reports/host-disk-attribution.bin'
   if target.exists()and os.fstat(fd).st_ino==target.stat().st_ino:raise OSError('EXPLICIT_HOSTDISK_EIO')
   return real_write(fd,raw)
  with patch.object(os,'write',side_effect=eio):
   try:o.flush(budget2,second/'reports/host-disk-attribution.bin');raise AssertionError('EIO hidden')
   except OSError:pass
  assert o.flushed is False;groups.append('hostdisk_EIO_not_claimed_flushed_or_complete')
  events=[];owner=runtime.WorkbenchRuntime.__new__(runtime.WorkbenchRuntime);owner.root=fixture;owner.digest='d'*64
  fakeobserver=types.SimpleNamespace(retire=lambda:events.append('retire'),stop=lambda:events.append('observer-stop'),flush=lambda *a:events.append('disk-flush'))
  owner.disk_observer=fakeobserver;owner.case={'admissionRevoked':False,'phase':'ACTIVE','writer':types.SimpleNamespace(begin_close=lambda:events.append('revoke'),close=lambda:events.append('writer-close')),'companion':None,'resources':object(),'native':types.SimpleNamespace(close=lambda:events.append('native-close')),'monitor':types.SimpleNamespace(close=lambda:events.append('monitor-close')),'APStarted':True,'device':types.SimpleNamespace(last_command_ref=None,root=fixture)};owner.close_interval=lambda:events.append('interval-close');owner.close_guardian=lambda **kw:events.append('guardian-close');owner.budget=types.SimpleNamespace(failure=lambda *a,**kw:events.append('failure-summary'));owner.write=lambda n,v,**kw:events.append(('terminal',v))
  with patch.object(runtime,'dispose_resources',side_effect=lambda *a,**kw:events.append('dispose')),patch.object(ipc,'flush_clients',side_effect=lambda *a:events.append('ipc-flush')):result=owner.fail_case(error)
  assert events.index('retire')<events.index('dispose')<events.index('disk-flush')and events.index('observer-stop')<events.index('disk-flush');terminal=next(v[1]for v in events if type(v)is tuple and v[0]=='terminal');assert terminal['guardianCause']['failure']==annotation['failure']and terminal['primaryFailure']=='HOST_HEALTH_TYPED_RESPONSE';groups.append('actual_failure_fsm_firstretire_before_disposal_flush_after_physical_cleanup_and_primary_plus_authentic_cause_terminal')
  def failure_flush(*a):events.append('disk-EIO');raise OSError('EXPLICIT_CLOSURE_CAPTURE_FAILURE')
  fakeobserver.flush=failure_flush
  with patch.object(runtime,'dispose_resources',side_effect=lambda *a,**kw:events.append('dispose')),patch.object(ipc,'flush_clients',side_effect=lambda *a:None):second_result=owner.fail_case(error)
  assert second_result['primaryFailure']=='HOST_HEALTH_TYPED_RESPONSE'and any(v['step']=='preserve-host-disk-attribution'for v in second_result['secondaryErrors']);groups.append('required_capture_EIO_stays_secondary_and_does_not_replace_primary_or_block_disposal')
 finally:shutil.rmtree(root)
 return groups,not root.exists()
if __name__=='__main__':
 out=R/sys.argv[1];groups,removed=run();files=[S/'aeris_runtime'/n for n in('host_health.py','guardian_cause11.py','darwin_disk11.py','product_runtime.py','metadata_budget.py')];v={'format':'aeris-hostdiag11-builder-integration-mock','status':'PASS','groups':groups,'passed':len(groups),'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},'scope':'REAL_LOCAL_UNIX_AND_METADATA_IO_WITH_SYNTHETIC_HEALTH_NO_ANDROID_AP','AndroidOrAPStarted':False,'scratchRemoved':removed}
 with out.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS','groups':len(groups),'path':str(out)}))
