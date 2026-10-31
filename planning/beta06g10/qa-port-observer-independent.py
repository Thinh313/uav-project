"""Independent authorized ephemeral-only listener-observer falsification. Never campaign ports."""
from pathlib import Path
import ast,datetime,errno,hashlib,importlib.util,json,os,socket,subprocess,sys,types
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation10';H=lambda b:hashlib.sha256(b).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
p=load('qa_independent_portguard',R/'planning/beta06g10/qa-port-guard.py');checks=[]
paths=['planning/beta06g10/qa-port-guard.py','planning/beta06g10/qa-root-controller.py','planning/beta06g9/qa-root-controller.py','planning/beta06g10/qa-root-live20.py','planning/beta06g10/qa-deadline-guard.py'];sourceHashes={n:H((R/n).read_bytes())for n in paths}
HEADER=b'Active Internet connections (including servers)\nProto Recv-Q Send-Q Local Address Foreign Address (state)\n'
def freeport():
 with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 assert port not in [8872,8873,5972,5582,5583];return port
def refused(ports,**kw):
 try:p.probe_host_ports(ports,**kw)
 except p.PortProbeError as e:return e.report
 raise AssertionError('EXPECTED_REFUSAL')
# Reuse the exact retained independent old-source witness only; it binds random ports, never product ports.
recipe=(R/'planning/beta06g10/qa-port-independent.py').read_text();part=recipe.split('# Extract the actual old source loop')[1].split('for index in [0,1]:')[0];exec('# Extract the actual old source loop'+part,globals())
for address in ['127.0.0.1','0.0.0.0']:
 for reuse in [False,True]:
  for index in [0,1]:
   foreign=socket.socket()
   try:
    foreign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,int(reuse));foreign.bind((address,0));blocked=foreign.getsockname()[1];foreign.listen(1);assert blocked not in [8872,8873,5972,5582,5583];available=freeport();assert blocked!=available;ports=(blocked,available)if index==0 else(available,blocked)
    proof=refused(ports);assert proof['failure']['operation']=='kernel_LISTEN_before'and proof['failure']['port']==blocked;assert proof['events']==[]
    checks.append({'case':'real_active_foreign_refused_before_socket_allocation','address':address,'reuse':reuse,'portIndex':index,'proof':proof})
   finally:foreign.close()
ports=(freeport(),freeport());assert ports[0]!=ports[1]
for name,body,stderr,code in [('empty',b'',b'',0),('malformed',HEADER+b'tcp4 garbage\n',b'',0),('stderr_even_exit0',HEADER,b'EPERM',0),('nonzero',HEADER,b'',1),('oversize',HEADER+b' '*(1024*1024),b'',0),('nonascii',HEADER+b'\xff',b'',0)]:
 proof=refused(ports,kernel_observer=lambda q,body=body,stderr=stderr,code=code:p.parse_kernel_table(body,stderr,code,q));assert proof['events']==[]
 checks.append({'case':'observer_'+name+'_refuses','proof':proof})
for name,observer in [('header_only',lambda q:p.parse_kernel_table(HEADER,b'',0,q)),('fabricated_incomplete_snapshot',lambda q:{'status':'COMPLETE','targetPorts':list(q),'listeners':[]})]:
 proof=refused(ports,kernel_observer=observer);checks.append({'case':name+'_cannot_grant_PASS','proof':proof})
for family,address in [('tcp6','::1'),('tcp46','*')]:
 raw=HEADER+f'{family} 0 0 {address}.{ports[0]} *.* LISTEN\n'.encode();proof=refused(ports,kernel_observer=lambda q,raw=raw:p.parse_kernel_table(raw,b'',0,q));assert proof['failure']['operation']=='kernel_LISTEN_before';checks.append({'case':'other_family_target_listener_refused','family':family,'proof':proof})
calls=[]
def missingrow(q):
 result=p.observe_kernel_listeners(q);calls.append(result)
 if len(calls)==2:result={**result,'listeners':result['listeners'][1:]}
 return result
proof=refused(ports,kernel_observer=missingrow);assert proof['failure']['operation']=='kernel_LISTEN_while_held';assert len(calls)==2;checks.append({'case':'missing_held_owned_row_refuses_all_handles_closed','proof':proof})
foreign=socket.socket();calls=[]
def race(q):
 result=p.observe_kernel_listeners(q);calls.append(result)
 if len(calls)==1:foreign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);foreign.bind(('0.0.0.0',q[0]));foreign.listen(1)
 return result
try:
 proof=refused(ports,kernel_observer=race);assert proof['failure']['operation']=='kernel_LISTEN_while_held';assert len(proof['kernelWhileHeld']['listeners'])==3;checks.append({'case':'foreign_wildcard_arrives_after_pre_observation_post_observation_refuses','proof':proof})
finally:foreign.close()
# Inject only raw observer snapshots and fake sockets for socket/close errors; no actual ports bound.
for failure in ['bind','listen','close']:
 handles=[];calls=[]
 class Sock:
  def __init__(self):self.i=len(handles);self.closed=False;handles.append(self)
  def setsockopt(self,*a):assert a==(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
  def bind(self,*a):
   if failure=='bind'and self.i==1:raise PermissionError(errno.EACCES,'INJECTED')
  def listen(self,*a):
   if failure=='listen'and self.i==1:raise OSError(errno.EIO,'INJECTED')
  def close(self):
   self.closed=True
   if failure=='close'and self.i==0:raise OSError(errno.EIO,'INJECTED')
 def observer(q):
  calls.append(1);raw=HEADER+(b''.join(f'tcp4 0 0 127.0.0.1.{n} *.* LISTEN\n'.encode()for n in q)if len(calls)>1 else b'');return p.parse_kernel_table(raw,b'',0,q)
 proof=refused(ports,socket_factory=lambda *a:Sock(),kernel_observer=observer);assert all(s.closed for s in handles);assert(proof['failure']or proof['closeFailures'][0])['operation']==failure;checks.append({'case':'injected_'+failure+'_refuses_closes_all','proof':proof})
# Execute only the original independent pure Controller integration seams, with Popen/writers/UI fully patched.
part=recipe.split('# Integration seams are isolated:')[1].split("assert all(H((R/n).read_bytes())")[0];exec('# Integration seams are isolated:'+part,globals())
assert all(H((R/n).read_bytes())==h for n,h in sourceHashes.items()),'SOURCE_DRIFT'
report={'status':'PASS_INDEPENDENT_PORT_OBSERVER_SOURCE_MOCK_ONLY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'version':sys.version,'executable':sys.executable,'executableSha256':H(Path(sys.executable).read_bytes())},'retainedPriorAttempt':'First exact Apple3.9 targeted run reached Controller import after socket/parser cases, then TypeError evaluating three union annotations; no PASS receipt or runtime effects. Corrected by authorized G10 future-annotations import only.','sourceHashes':sourceHashes,'checks':checks,'checksCount':len(checks),'allOwnSocketHandlesClosed':True,'noSO_REUSEPORT':True,'actualCampaignPortsBound':0,'actualProductRuntimeLaunches':0,'historicalG9Cause':'UNKNOWN; controlled old-failure/new-pass does not reconstruct historical kernel state','noToctouGuarantee':True,'retainedOriginalFailure':'qa-port-active-listener-failure01.json'}
b=json.dumps(report,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(b)<128*2**10
out=E/'qa-port-observer-independent01.json'
with out.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out),'sha256':H(b),'bytes':len(b),'checks':len(checks)}))
