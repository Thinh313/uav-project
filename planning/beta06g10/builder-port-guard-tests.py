"""Focused authorized ephemeral-only host probe fixtures; no campaign runtime."""
from pathlib import Path
import errno,hashlib,importlib.util,json,os,select,socket,subprocess,sys,tempfile,time,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation10'
def mod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
g=mod('g10_focused_port_guard',P/'qa-port-guard.py');c=mod('g10_focused_controller',P/'qa-root-controller.py');observed={}
class FakeQuota:
 def reserve_write(self,**kw):return kw
 def check_native_future(self,**kw):return {'status':'CAPACITY_AVAILABLE',**kw}
 def load_policy(self):return {'scanner':{'staleMs':15000},'categories':{'screenshots':{'perFileBytes':5*2**20}}}
c.b._quota=FakeQuota()
def spare_port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def collect_line(proc):
 assert select.select([proc.stdout],[],[],5)[0],'BOUNDED_FIXTURE_NODE_STDOUT_TIMEOUT'
 line=proc.stdout.readline(2049);assert len(line)<=2048 and line.endswith('\n'),'BOUNDED_FIXTURE_NODE_LINE';return json.loads(line)
def node_failed_listener(port):
 return ['node','-e',"const net=require('node:net');const s=net.createServer();s.on('error',e=>{console.error(JSON.stringify({code:e.code,errno:e.errno,syscall:e.syscall,address:e.address,port:e.port}));process.exitCode=1;});s.listen(Number(process.argv[1]),'127.0.0.1',()=>{s.close();});",str(port)]
class Tracked:
 def __init__(self,sock,all_sockets):self.sock=sock;self.all=all_sockets;self.closed=False;self.all.append(self)
 def setsockopt(self,*a):return self.sock.setsockopt(*a)
 def bind(self,*a):return self.sock.bind(*a)
 def listen(self,*a):return self.sock.listen(*a)
 def close(self):self.closed=True;return self.sock.close()
HEADER=b'Active Internet connections (including servers)\nProto Recv-Q Send-Q Local Address Foreign Address (state)\n'
def fake_observer():
 count=[0]
 def read(ports):
  raw=HEADER
  if count[0]:raw+=b''.join(('tcp4 0 0 127.0.0.1.'+str(port)+' *.* LISTEN\n').encode()for port in ports)
  count[0]+=1;return g.parse_kernel_table(raw,b'',0,ports)
 return read
class Tests(unittest.TestCase):
 def test_real_Node_closed_accepted_connection_old_plainbind_fails_new_reuse_and_Node_pass(self):
  js=r"""const net=require('node:net');const timer=setTimeout(()=>{console.error('FIXTURE_TIMEOUT');process.exit(2)},4000);const server=net.createServer(s=>{console.log(JSON.stringify({phase:'ACCEPTED',localPort:s.localPort,remotePort:s.remotePort}));s.on('close',()=>server.close(()=>{clearTimeout(timer);console.log(JSON.stringify({phase:'CLOSED_LISTENER_AND_ACCEPTED'}))}));s.end('x')});server.listen(0,'127.0.0.1',()=>console.log(JSON.stringify({phase:'LISTENING',port:server.address().port,node:process.version,uv:process.versions.uv})));"""
  proc=subprocess.Popen(['node','-e',js],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);rows=[]
  try:
   first=collect_line(proc);rows.append(first);port=first['port'];self.assertNotIn(port,[8872,8873,5582,5583])
   with socket.create_connection(('127.0.0.1',port),timeout=2)as client:
    self.assertEqual(client.recv(8),b'x');self.assertEqual(client.recv(8),b'')
   rest,err=proc.communicate(timeout=5);rows.extend(json.loads(line)for line in rest.splitlines());self.assertEqual(proc.returncode,0,err);self.assertTrue(any(x['phase']=='ACCEPTED'for x in rows));self.assertEqual(rows[-1]['phase'],'CLOSED_LISTENER_AND_ACCEPTED')
   old_error=None
   with socket.socket()as old:
    try:old.bind(('127.0.0.1',port))
    except OSError as exc:old_error={'errno':exc.errno,'class':type(exc).__name__,'message':str(exc)}
   self.assertIsNotNone(old_error,'OLD_PLAINBIND_DEFECT_NOT_REPRODUCED_ON_THIS_OS');self.assertEqual(old_error['errno'],errno.EADDRINUSE)
   node=subprocess.run(node_failed_listener(port),capture_output=True,text=True,timeout=5);self.assertEqual(node.returncode,0,node.stderr)
   proof=g.probe_host_ports((port,spare_port()));self.assertTrue(proof['heldTogetherUntilCleanup']);self.assertTrue(all(e['ok']for e in proof['events']))
   observed['nodeClosedAcceptedWitness']={'rows':rows,'oldPlainBind':old_error,'defaultNodeImmediateRestart':{'exit':node.returncode,'stderr':node.stderr},'newProbe':proof,'historicalG9Cause':'UNKNOWN; this controlled socket-state witness is separate evidence, not retrospective diagnosis.'}
  finally:
   if proc.poll()is None:proc.kill();proc.wait(timeout=2)
   proc.stdout.close();proc.stderr.close()
 def host_command(self,guard,tmp,*,popen=None):
  ctl=c.Controller('20',boot_reader=lambda:'MOCK_BOOT',clock=lambda:100);ctl.host_anchor=100;ctl.quota_admission=lambda *a:None;ctl.workspace_before_first_writer=lambda:None
  (tmp/'workspace01').mkdir();runtime=types.SimpleNamespace(budget_decision=lambda samples:None)
  def module(name,file):return guard if file=='qa-port-guard.py'else runtime
  settings=[patch.object(c,'E',tmp),patch.object(c,'module',side_effect=module),patch.object(c.time,'sleep',return_value=None),patch.object(c.shutil,'disk_usage',return_value=types.SimpleNamespace(free=37*2**30))]
  if popen is not None:settings.append(patch.object(c.subprocess,'Popen',side_effect=popen))
  from contextlib import ExitStack
  stack=ExitStack()
  for setting in settings:stack.enter_context(setting)
  return ctl,stack,{'op':'start-host','rootApproved':True,'commandId':'g10-port-test','sourceAndViewerStoppedAndInspected':True}
 def test_active_each_port_reuse_and_wildcard_refuses_before_Popen_and_latches(self):
  results=[]
  for address in ['127.0.0.1','0.0.0.0']:
   for reuse in [False,True]:
    for occupied_index in [0,1]:
     with socket.socket()as active:
      if reuse:active.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
      active.bind((address,0));active.listen(1);occupied=active.getsockname()[1];ports=[spare_port(),spare_port()];ports[occupied_index]=occupied;tracked=[]
      factory=lambda *a:Tracked(socket.socket(*a),tracked)
      def probe(requested,**kw):self.assertEqual(requested,(8872,8873));return g.probe_host_ports(ports,socket_factory=factory,clock=time.monotonic)
      guard=types.SimpleNamespace(probe_host_ports=probe)
      with tempfile.TemporaryDirectory(prefix='builder-g10-port-active-',dir=E)as name:
       ctl,stack,command=self.host_command(guard,Path(name))
       with stack,patch.object(c.subprocess,'Popen')as popen:
        with self.assertRaises(g.PortProbeError,msg=str((address,reuse,occupied_index)))as caught:ctl.command(command)
        self.assertTrue(ctl.campaign_failed);self.assertEqual(ctl.connect_count,0);self.assertEqual(ctl.dispatched,set());popen.assert_not_called()
        with self.assertRaisesRegex(AssertionError,'FAILED_CAMPAIGN'):ctl.command({**command,'commandId':'g10-no-retry'})
        # No UI/reference read or Connect anchor is permitted after this failure.
        with self.assertRaisesRegex(AssertionError,'FAILED_OR_UNCERTAIN'):ctl.command({'op':'action','rootApproved':True,'commandId':'g10-no-connect','target':'field-connect'})
        self.assertEqual(ctl.guard.snapshot()['connectBeforeTapPythonMonoS'],None)if 'connectBeforeTapPythonMonoS'in ctl.guard.snapshot()else self.assertEqual(ctl.connect_count,0)
        proof=json.loads((Path(name)/'host-admission-g10-port-test-ports.json').read_text());self.assertEqual(proof,caught.exception.report);self.assertEqual(proof['failure']['port'],occupied);self.assertEqual(proof['failure']['operation'],'kernel_LISTEN_before');self.assertIsNone(proof['failure']['errno'])
        self.assertEqual(tracked,[]);self.assertTrue(proof['kernelBefore']['listeners'])
        results.append({'address':address,'foreignReuse':reuse,'occupiedPosition':occupied_index,'proof':proof,'PopenCalls':popen.call_count,'campaignFailed':ctl.campaign_failed})
  observed['activeForeignListeners']=results
 def test_both_success_handles_are_retained_until_second_listen_and_no_REUSEPORT(self):
  events=[];handles=[]
  class Sock:
   def __init__(self):self.closed=False;handles.append(self)
   def setsockopt(self,level,opt,val):events.append(('option',level,opt,val));self_opt=(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);self.assertion=self_opt;assert(level,opt,val)==self_opt
   def bind(self,addr):events.append(('bind',addr));assert not any(s.closed for s in handles)
   def listen(self,n):events.append(('listen',n));assert not any(s.closed for s in handles)
   def close(self):self.closed=True;events.append(('close',len(handles)))
  proof=g.probe_host_ports((12345,12346),socket_factory=lambda *args:Sock(),clock=lambda:100,kernel_observer=fake_observer())
  self.assertTrue(proof['heldTogetherUntilCleanup']);self.assertEqual([e[0]for e in events],['option','bind','listen','option','bind','listen','close','close']);self.assertTrue(all(s.closed for s in handles));observed['twoHandlesHeld']=proof
 def test_permission_unexpected_socket_and_cleanup_failures_preserve_port_operation_errno(self):
  cases=[('socket',0,errno.EMFILE),('setsockopt_SO_REUSEADDR',0,errno.EPERM),('bind',0,errno.EACCES),('listen',1,errno.EIO),('close',0,errno.EIO)];results=[]
  for operation,index,number in cases:
   handles=[]
   class Sock:
    def __init__(self,i):self.i=i;self.closed=False
    def fail(self,op):
     if op==operation and self.i==index:raise OSError(number,'CONTROLLED_SOCKET_FAILURE')
    def setsockopt(self,*a):self.fail('setsockopt_SO_REUSEADDR')
    def bind(self,*a):self.fail('bind')
    def listen(self,*a):self.fail('listen')
    def close(self):self.closed=True;self.fail('close')
   def factory(*a):
    i=len(handles)
    if operation=='socket'and i==index:raise OSError(number,'CONTROLLED_SOCKET_CREATE_FAILURE')
    sock=Sock(i);handles.append(sock);return sock
   with self.assertRaises(g.PortProbeError)as caught:g.probe_host_ports((12345,12346),socket_factory=factory,clock=lambda:100,kernel_observer=fake_observer())
   proof=caught.exception.report;failure=proof['failure']or proof['closeFailures'][0];self.assertEqual(failure['operation'],operation);self.assertEqual(failure['port'],[12345,12346][index]);self.assertEqual(failure['errno'],number);self.assertTrue(all(s.closed for s in handles));self.assertLessEqual(len(json.dumps(proof).encode()),16*2**10);results.append(proof)
  observed['injectedSocketFailures']=results
 def test_kernel_parser_and_held_observation_unknowns_refuse(self):
  cases=[(b'',b'',0),(HEADER,b'EPERM',0),(HEADER,b'',1),(b'unknown\n',b'',0),(HEADER+b'tcp4 0 0 malformed *.* LISTEN\n',b'',0),(HEADER+b'tcp4 0 0 127.0.0.1.12345 *.* UNKNOWN\n',b'',0),(b'x'*(1024*1024+1),b'',0),(HEADER+b'\xff',b'',0)]
  for raw,err,exit_code in cases:
   with self.assertRaises(g.KernelObservationError):g.parse_kernel_table(raw,err,exit_code,(12345,12346))
  # A complete header-only table can be a valid pre-observation, never positive held coverage.
  for target_rows in [b'',b'tcp4 0 0 127.0.0.1.12345 *.* LISTEN\n',b'tcp46 0 0 *.12345 *.* LISTEN\ntcp4 0 0 127.0.0.1.12346 *.* LISTEN\n']:
   count=[0];closed=[]
   def observer(ports):
    raw=HEADER+(target_rows if count[0]else b'');count[0]+=1;return g.parse_kernel_table(raw,b'',0,ports)
   class Sock:
    def setsockopt(self,*a):pass
    def bind(self,*a):pass
    def listen(self,*a):pass
    def close(self):closed.append(True)
   with self.assertRaises(g.PortProbeError)as caught:g.probe_host_ports((12345,12346),socket_factory=lambda *a:Sock(),kernel_observer=observer,clock=lambda:100)
   self.assertEqual(caught.exception.report['failure']['operation'],'kernel_LISTEN_while_held');self.assertEqual(len(closed),2)
  observed['kernelNegatives']={'rawRefusals':len(cases),'heldMissingOrWildcardRefusals':3,'emptyNeverPositive':True}
 def test_partial_second_bind_failure_closes_first_real_handle(self):
  tracked=[]
  with socket.socket()as foreign:
   foreign.bind(('127.0.0.1',0));foreign.listen(1);ports=(spare_port(),foreign.getsockname()[1])
   # Inject only the pre-kernel observation to isolate actual second-bind cleanup.
   with self.assertRaises(g.PortProbeError)as caught:g.probe_host_ports(ports,socket_factory=lambda *a:Tracked(socket.socket(*a),tracked),kernel_observer=fake_observer())
   self.assertIn(caught.exception.report['failure']['operation'],['bind','listen']);self.assertEqual(caught.exception.report['failure']['port'],ports[1]);self.assertTrue(all(s.closed and s.sock.fileno()==-1 for s in tracked));self.assertEqual(len(tracked),2)
   observed['partialSecondCleanup']=caught.exception.report
 def test_Popen_failure_latches_without_retries_or_AP(self):
  with tempfile.TemporaryDirectory(prefix='builder-g10-popen-fail-',dir=E)as name:
   tmp=Path(name);guard=types.SimpleNamespace(probe_host_ports=lambda *a,**kw:{'status':'PASS_MOCK_PROBE'})
   ctl,stack,command=self.host_command(guard,tmp,popen=lambda *a,**kw:(_ for _ in()).throw(OSError(errno.ENOENT,'MOCK_EXEC_FAILURE')))
   with stack:
    with self.assertRaises(OSError):ctl.command(command)
    self.assertTrue(ctl.campaign_failed);self.assertEqual(ctl.connect_count,0);self.assertEqual(ctl.host_instances,1)
    with self.assertRaisesRegex(AssertionError,'FAILED_CAMPAIGN'):ctl.command({**command,'commandId':'g10-popen-no-retry'})
    ctl.close()
  observed['PopenFailure']={'campaignFailed':True,'AP':0,'automaticRetry':False}
 def test_post_probe_race_real_failed_Node_child_log_and_observed_exit_blocks_Connect(self):
  ports=(spare_port(),spare_port());foreign=socket.socket();real_popen=subprocess.Popen;spawned=[]
  def probe(*args,**kwargs):
   result=g.probe_host_ports(ports);foreign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);foreign.bind(('127.0.0.1',ports[0]));foreign.listen(1);return result
  def popen(*args,**kwargs):
   child=real_popen(node_failed_listener(ports[0]),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=R);spawned.append(child);child.wait(timeout=5);return child
  try:
   with tempfile.TemporaryDirectory(prefix='builder-g10-startup-race-',dir=E)as name:
    tmp=Path(name);ctl,stack,command=self.host_command(types.SimpleNamespace(probe_host_ports=probe),tmp,popen=popen)
    with stack:
     result=ctl.command(command);self.assertEqual(result['hostPid'],spawned[0].pid);self.assertNotEqual(spawned[0].returncode,0);ctl.host_capture.finish();log=(tmp/'host-console1.txt').read_bytes();self.assertIn(b'EADDRINUSE',log)
     # Restore real original quota method; exit is refused before quota/UI/Connect input.
     ctl.quota_admission=types.MethodType(c.Controller.quota_admission,ctl)
     with patch.object(c.b,'admit')as admit:
      with self.assertRaisesRegex(RuntimeError,'OWNED_HOST_EXITED_NO_CONNECT'):ctl.command({'op':'action','rootApproved':True,'commandId':'g10-race-no-connect','target':'field-connect'})
      admit.assert_not_called()
     self.assertTrue(ctl.campaign_failed);self.assertEqual(ctl.connect_count,0);self.assertEqual(ctl.dispatched,set())
     with self.assertRaisesRegex(AssertionError,'FAILED_CAMPAIGN'):ctl.command({**command,'commandId':'g10-race-no-retry'})
     observed['postProbeRace']={'childPid':spawned[0].pid,'exit':spawned[0].returncode,'logUtf8':log.decode(),'logSha256':hashlib.sha256(log).hexdigest(),'campaignFailed':True,'Connects':0,'scope':'Probe succeeded, then controlled foreign listener won the race before actual Node child. No TOCTOU guarantee; later observed exit blocked before UI. No automatic retry.'};ctl.close()
  finally:
   foreign.close()
   for child in spawned:
    if child.poll()is None:child.kill();child.wait(timeout=2)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'classification':'FOCUSED_EPHEMERAL_SOCKET_AND_NODE_FIXTURES_NOT_CAMPAIGN_RUNTIME','status':'PASS_G10_PORT_GUARD_SOURCE_MOCK'if result.wasSuccessful()else'FAIL','groups':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors],'observed':observed,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'qa-port-guard.py',P/'qa-root-controller.py',Path(__file__)]},'historicalG9PortAndSocketState':'UNKNOWN','scope':'Only ephemeral IPv4 fixture sockets/Node children. No host-app10/listener on actual campaign ports, emulator, AP, ADB, browser or runtime launch; temporary small fixture bodies removed.'};out=E/(sys.argv[1]if len(sys.argv)>1 else'builder-port-guard01.json')
 with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 sys.exit(0 if result.wasSuccessful()else 1)
