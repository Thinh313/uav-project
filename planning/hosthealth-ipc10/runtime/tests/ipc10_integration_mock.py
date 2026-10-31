from pathlib import Path
import argparse,contextlib,hashlib,json,os,shutil,socket,sys,tempfile,threading,types
from unittest.mock import patch
from ipc10_mock import ROOT,SOURCE,binding,snapshot,hh,trace
from aeris_runtime.metadata_budget import MetadataBudget,CLOSING_OWNERS,_bound
from aeris_runtime import product_runtime as runtime

def run(out):
 root=Path(tempfile.mkdtemp(prefix='k',dir=ROOT/'evidence/hosthealth-ipc10'));groups=[]
 try:
  endpoint=root/'h';endpoint.mkdir();os.chmod(endpoint,0o700);bind=binding();health=types.SimpleNamespace(check=lambda:None,snapshot=snapshot,latch=lambda e:None,budget=types.SimpleNamespace(publication=contextlib.nullcontext))
  server=hh.HealthServer(endpoint,health,bind);server.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.socket.bind(str(server.path));os.chmod(server.path,0o600);server.inode=server.path.stat().st_ino;identity=(server.path.stat().st_dev,server.inode);server.socket.listen(1);server.socket.settimeout(.1);server.trace=trace.TraceRing('server',bind,server.path,identity,candidate='d'*64);server.thread=threading.Thread(target=server._run,name='ipc10-explicit-mock-only',daemon=True)
  client=hh.GuardianClient.__new__(hh.GuardianClient);client.root=endpoint;client.path=server.path;client.socket_identity=identity;client.binding=bind;client.allow_mock=True;client.trace=trace.TraceRing('client',bind,server.path,identity,candidate='d'*64)
  try:
   server.thread.start();result=client();assert result['sourceVerified']is True
  finally:server.close()
  a=trace.verify_original(client.trace.export(),candidate='d'*64,binding=bind,endpoint=server.path,endpoint_identity=identity,trace_pid=os.getpid(),role='client');b=trace.verify_original(server.trace.export(),candidate='d'*64,binding=bind,endpoint=server.path,endpoint_identity=identity,trace_pid=os.getpid(),role='server');joined=trace.correlate(a,b);assert joined[0]['status']=='EXACT_NONCE_AND_RAW_BYTES_JOINED';assert a['rows'][0]['metadata']['p']==b['header']['pid']and b['rows'][0]['metadata']['p']==a['header']['pid'];groups.append('real_local_unix_kernel_pid_source_client_server_nonce_raw_join')
  fixture=root/'budget';fixture.mkdir();(fixture/'reports').mkdir();(fixture/'guardian').mkdir();budget=MetadataBudget(fixture/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:20*2**30,mock=True);budget.admit();budget.write('external_task',fixture/'reports/exhaust.bin',b'x'*(1024*1024));assert budget.snapshot()['remaining']['external_task']==0
  for name in('reports/hosthealth-ipc-client.bin','guardian/hosthealth-ipc-server.bin'):
   p=fixture/name;assert _bound(p,49152,False)==49152;budget.write('closure',p,b'x'*49152,closing=True)
  budget.write('closure',fixture/'reports/owner-terminal.json',b'x'*4096,closing=True);budget.write('closure',fixture/'reports/owner-error.txt',b'x'*16384,closing=True);budget.write('closure',fixture/'reports/ui-failure-final.json',b'x'*32768,closing=True);assert budget.snapshot()['closingOwners']['closure']==77824;groups.append('real_budget_148KiB_rounding_original224KiB_external_exhaustion')
  for path,data in [('reports/not-allowed-ipc.bin',b'x'),('reports/hosthealth-ipc-client.bin',b'x'*49153)]:
   try:budget.write('closure',fixture/path,data,closing=True);assert False
   except ValueError:pass
  groups.append('exact_two_paths_no_append_no48KiB_overrun')
  fixture2=root/'eio';fixture2.mkdir();(fixture2/'reports').mkdir();budget2=MetadataBudget(fixture2/'metadata-budget',lambda:{'metadataBytes':0},free=lambda:20*2**30,mock=True);budget2.admit();ring=trace.TraceRing('client',bind,'/mock',(1,2));s=ring.begin('n','mock');ring.finish(s,RuntimeError('ORIGINAL_PRIMARY'))
  original_write=os.write
  def injected_write(fd,data):
   target=fixture2/'reports/hosthealth-ipc-client.bin'
   if target.exists()and os.fstat(fd).st_ino==target.stat().st_ino:raise OSError('EXPLICIT_TRACE_EIO')
   return original_write(fd,data)
  with patch.object(os,'write',side_effect=injected_write):
   try:ring.flush(budget2,fixture2/'reports/hosthealth-ipc-client.bin');assert False
   except OSError:pass
  assert ring.flushed is False;groups.append('real_write_eio_not_marked_flushed_or_complete')
  events=[];owner=runtime.WorkbenchRuntime.__new__(runtime.WorkbenchRuntime);owner.root=fixture;owner.digest='d'*64;owner.case={'admissionRevoked':False,'phase':'ACTIVE','writer':types.SimpleNamespace(begin_close=lambda:events.append('revoke'),close=lambda:events.append('writer-close')),'companion':None,'resources':object(),'native':types.SimpleNamespace(close=lambda:events.append('native-close')),'monitor':types.SimpleNamespace(close=lambda:events.append('monitor-close')),'APStarted':True,'device':types.SimpleNamespace(last_command_ref=None,root=fixture)};owner.close_interval=lambda:events.append('interval-close');owner.close_guardian=lambda **kw:events.append('guardian-close');owner.budget=types.SimpleNamespace(failure=lambda *a,**k:events.append('failure-summary'));owner.write=lambda n,v,**kw:events.append(('terminal',v['primaryFailure']))
  def flush(*a):events.append('trace-flush');raise OSError('EXPLICIT_DIAGNOSTIC_EIO')
  with patch.object(runtime,'dispose_resources',side_effect=lambda *a,**k:events.append('dispose')),patch.object(trace,'flush_clients',side_effect=flush):result=owner.fail_case(RuntimeError('ORIGINAL_PRIMARY'))
  assert events.index('revoke')<events.index('dispose')<events.index('trace-flush');assert result['primaryFailure']=='ORIGINAL_PRIMARY'and any(z['step']=='preserve-hosthealth-ipc-client'for z in result['secondaryErrors']);assert ('terminal','ORIGINAL_PRIMARY')in events;groups.append('actual_failure_fsm_revoke_dispose_then_trace_eio_secondary')
 finally:shutil.rmtree(root)
 report={'format':'aeris-ipc10-builder-integration-mock','scope':'REAL_LOCAL_SYNTHETIC_UNIX_AND_METADATA_FILES_NO_ANDROID_AP_QEMU_OR_PRODUCT_ACTORS','groups':groups,'passed':len(groups),'sdkActorsStarted':False,'scratchRemoved':not root.exists(),'sourceSHA256':{str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [SOURCE/'aeris_runtime/host_health.py',SOURCE/'aeris_runtime/ipc_trace10.py',SOURCE/'aeris_runtime/metadata_budget.py',SOURCE/'aeris_runtime/product_runtime.py']},'status':'PASS'}
 with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS','groups':len(groups),'report':str(out)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
