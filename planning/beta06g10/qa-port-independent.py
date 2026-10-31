"""Independent bounded ephemeral-socket and pure injected-error checks. No campaign ports."""
from pathlib import Path
import ast,ctypes,datetime,errno,hashlib,importlib.util,io,json,os,socket,subprocess,sys,types
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation10'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
p=load('qa_independent_portguard',R/'planning/beta06g10/qa-port-guard.py');H=lambda b:hashlib.sha256(b).hexdigest();checks=[]
sourcePaths=['planning/beta06g10/qa-port-guard.py','planning/beta06g10/qa-root-controller.py','planning/beta06g9/qa-root-controller.py'];sourceHashes={n:H((R/n).read_bytes())for n in sourcePaths}
def freeport():
 with socket.socket()as s:s.bind(('127.0.0.1',0));n=s.getsockname()[1]
 assert n not in [8872,8873,5972,5582,5583];return n
def twoports():
 a,b=freeport(),freeport()
 assert a!=b;return a,b
def refused(ports,**kwargs):
 try:p.probe_host_ports(ports,**kwargs)
 except p.PortProbeError as e:return e.report
 raise AssertionError('EXPECTED_PORT_REFUSAL')
# Extract the actual old source loop, replacing ONLY its fixed port list with fixture ports.
old=(R/'planning/beta06g9/qa-root-controller.py').read_text();tree=ast.parse(old);ctl=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller');fn=next(n for n in ctl.body if isinstance(n,ast.FunctionDef)and n.name=='start_host');loop=next(n for n in fn.body if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='port');loop.iter=ast.Name(id='ports',ctx=ast.Load());f=ast.FunctionDef(name='old_probe',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='ports')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[loop],decorator_list=[]);mod=ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[]));scope={'socket':socket};exec(compile(mod,'actual_G9_loop_ephemeral_iterator_only','exec'),scope)
listener=socket.socket();listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind(('127.0.0.1',0));port=listener.getsockname()[1];assert port not in [8872,8873,5972,5582,5583];listener.listen(1);client=socket.socket();client.settimeout(2);client.connect(('127.0.0.1',port));accepted,peer=listener.accept();identity={'server':accepted.getsockname(),'peer':accepted.getpeername()};accepted.shutdown(socket.SHUT_WR);accepted.close();assert client.recv(1)==b'';client.close();listener.close();assert all(s.fileno()==-1 for s in [listener,client,accepted]);other=freeport();assert other!=port
oldError=None
try:scope['old_probe']((port,other))
except OSError as e:oldError={'errno':e.errno,'message':str(e)}
assert oldError and oldError['errno']==errno.EADDRINUSE,'OLD_REFUSAL_NOT_REPRODUCED_DO_NOT_INVENT_STATE'
witness=p.probe_host_ports((port,other));assert witness['heldTogetherUntilCleanup']and witness['status']=='PASS_HOST_PORT_PROBE_NOT_STARTUP_GUARANTEE'
node="import net from'node:net';const s=net.createServer();s.on('error',e=>{console.error(e.code);process.exitCode=1});s.listen(Number(process.argv[1]),'127.0.0.1',()=>s.close(()=>console.log('NODE_EPHEMERAL_LISTEN_PASS')));"
nodeResult=subprocess.run(['node','--input-type=module','-e',node,str(port)],capture_output=True,text=True,timeout=5);assert nodeResult.returncode==0 and 'NODE_EPHEMERAL_LISTEN_PASS'in nodeResult.stdout
checks.append({'case':'actual_old_closed_accepted_connection_refuses_new_reuse_bindlisten_and_Node_listen_pass','status':'PASS','socketIdentity':identity,'allOriginalHandlesClosed':True,'oldError':oldError,'newProof':witness,'nodeResult':nodeResult.stdout.strip(),'kernelTIME_WAITState':'NOT_OBSERVED_NOT_ATTRIBUTED_TO_HISTORICAL_G9'})
for index in [0,1]:
 for reuse in [False,True]:
  foreign=socket.socket();foreign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,int(reuse));foreign.bind(('0.0.0.0',0));blocked=foreign.getsockname()[1];foreign.listen(1);assert blocked not in [8872,8873,5972,5582,5583];available=freeport();assert available!=blocked;ports=(blocked,available)if index==0 else(available,blocked)
  try:
   report=refused(ports);assert report['failure']['port']==blocked and report['failure']['operation']in ['bind','listen'];assert report['failure']['errno']==errno.EADDRINUSE
   with socket.socket()as freed:freed.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);freed.bind(('127.0.0.1',available));freed.listen(1)
  finally:foreign.close()
  checks.append({'case':'active_foreign_listener_refused','portIndex':index,'foreignReuseAddress':reuse,'proof':report,'partialAvailableHandleReleased':True})
class FakeSocket:
 def __init__(self,i,events,fail=None,closefail=False):self.i=i;self.events=events;self.fail=fail;self.closefail=closefail;self.closed=False
 def setsockopt(self,level,option,value):assert(level,option,value)==(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);self.events.append((self.i,'reuseaddr'))
 def bind(self,addr):
  self.events.append((self.i,'bind'))
  if self.fail=='bind':raise PermissionError(errno.EACCES,'INJECTED_BIND_DENIED')
 def listen(self,n):
  assert n==1;self.events.append((self.i,'listen'))
  if self.fail=='listen':raise OSError(errno.EIO,'INJECTED_LISTEN_FAILED')
 def close(self):
  self.closed=True;self.events.append((self.i,'close'))
  if self.closefail:raise OSError(errno.EIO,'INJECTED_CLOSE_FAILED')
for failure,closefail in [('bind',False),('listen',False),(None,True)]:
 events=[];handles=[]
 def factory(*args):
  s=FakeSocket(len(handles),events,fail=failure if len(handles)==1 else None,closefail=closefail and len(handles)==0);handles.append(s);return s
 report=refused((31001,31002),socket_factory=factory);assert all(s.closed for s in handles);assert report['failure']['operation']==failure if failure else bool(report['closeFailures']);assert len(json.dumps(report))<16384
 checks.append({'case':'injected_socket_or_cleanup_error_refuses_and_closes_all','failure':failure,'closeError':closefail,'proof':report})
def brokenfactory(*a):raise RuntimeError('INJECTED_FACTORY_FAILURE')
report=refused((31001,31002),socket_factory=brokenfactory);assert report['failure']['operation']=='socket'and report['failure']['port']==31001;checks.append({'case':'unexpected_socket_factory_failure_diagnostic','proof':report})
# Integration seams are isolated: no real Controller Popen, writer, UI, campaign-port probes or sleep.
c=load('qa_independent_G10_controller',R/'planning/beta06g10/qa-root-controller.py');events=[];writes=[];ctl=c.Controller('20',boot_reader=lambda:'QA_BOOT',clock=lambda:100);ctl.emit=lambda event,**v:events.append({'event':event,**v});ctl.quota_admission=lambda *a:None
failed={'failure':{'port':8873,'operation':'listen','errno':errno.EADDRINUSE},'closeFailures':[],'status':'REFUSED'}
realmodule=c.module
def modules(name,file):
 if file=='qa-runtime.py':return types.SimpleNamespace(budget_decision=lambda samples:None)
 if file=='qa-port-guard.py':return types.SimpleNamespace(probe_host_ports=lambda *a,**k:(_ for _ in()).throw(p.PortProbeError(failed)))
 return realmodule(name,file)
with patch.object(c,'module',side_effect=modules),patch.object(c.time,'sleep'),patch.object(c.b,'write_json',side_effect=lambda *a,**k:writes.append(str(a[0]))),patch.object(c.subprocess,'Popen')as popen:
 for name in ['qa-port-refusal','qa-no-second-start']:
  try:ctl.command({'op':'start-host','rootApproved':True,'commandId':name,'sourceAndViewerStoppedAndInspected':True})
  except BaseException:pass
  else:raise AssertionError('FAILED_START_MUST_REFUSE')
 assert ctl.campaign_failed and ctl.host_instances==0 and ctl.connect_count==0;popen.assert_not_called()
checks.append({'case':'focused_port_refusal_latches_no_later_host_Popen_or_AP','events':events,'diagnosticPaths':writes,'actualCampaignPortsBound':False})
ctl=c.Controller('20',boot_reader=lambda:'QA_BOOT',clock=lambda:100);events=[];ctl.emit=lambda event,**v:events.append({'event':event,**v});ctl.host_instances=1;ctl.host_process=types.SimpleNamespace(pid=424242,returncode=98,poll=lambda:98);retainedConsole=b'INJECTED_POST_PROBE_NODE_STARTUP_EADDRINUSE\n'
try:ctl.quota_admission('before-connect','qa-owned-startup-exit')
except RuntimeError as e:assert str(e)=='OWNED_HOST_EXITED_NO_CONNECT_OR_RETRY'
else:raise AssertionError('DEAD_CHILD_NO_CONNECT')
assert ctl.campaign_failed and ctl.connect_count==0;checks.append({'case':'post_probe_observed_child_exit_blocks_Connect_without_retry','mockExit':98,'retainedMockConsoleSha256':H(retainedConsole),'events':events,'seam':'Observed owned-child state injected; no actual product child launched.'})
assert all(H((R/n).read_bytes())==h for n,h in sourceHashes.items()),'SOURCE_CHANGED_DURING_TEST'
report={'status':'PASS_INDEPENDENT_FOCUSED_REAL_EPHEMERAL_PORT_GUARD_SOURCE_MOCK_ONLY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceHashes':sourceHashes,'checks':checks,'productionPortProbes':0,'actualProductRuntimeLaunches':0,'testSocketsClosed':True,'historicalG9Cause':'UNKNOWN; controlled fixture reproduces old availability refusal, not historical socket state.','TOCTOUGuarantee':False,'noSO_REUSEPORT':True,'newOutsideProjectCopies':0}
b=json.dumps(report,separators=(',',':')).encode()+b'\n';assert len(b)<65536
with(E/'qa-port-independent01.json').open('xb')as out:out.write(b);out.flush();os.fsync(out.fileno())
print(json.dumps({'path':str(E/'qa-port-independent01.json'),'sha256':H(b),'bytes':len(b),'checks':len(checks),'status':report['status']}))
