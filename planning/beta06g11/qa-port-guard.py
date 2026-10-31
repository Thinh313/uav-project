"""Bounded IPv4 host availability probe. No listener or process runs on import.
SO_REUSEADDR + bind/listen matches the verified immediate Node restart case;
this proves availability only while handles are held, never a TOCTOU guarantee.
"""
import hashlib,ipaddress,json,os,selectors,socket,subprocess,time
from subprocess import Popen as kernel_popen
from pathlib import Path
import importlib.util,sys
_clock_path=Path(__file__).resolve().parents[2]/'pilot/beta06g11/clock_basis.py'
if 'aeris_g11_clock'in sys.modules:
 host_clock=sys.modules['aeris_g11_clock'];assert Path(host_clock.__file__).resolve()==_clock_path.resolve(),'CANONICAL_CLOCK_PATH_REQUIRED'
else:
 _clock_spec=importlib.util.spec_from_file_location('aeris_g11_clock',_clock_path);host_clock=importlib.util.module_from_spec(_clock_spec);sys.modules[_clock_spec.name]=host_clock;_clock_spec.loader.exec_module(host_clock)

class PortProbeError(RuntimeError):
 def __init__(self,report):
  self.report=report;failure=report['failure']or report['closeFailures'][0]
  super().__init__('HOST_PORT_PROBE_REFUSED:'+str(failure['port'])+':'+failure['operation']+':errno='+str(failure['errno']))
def detail(exc,port,operation,at):
 return {'port':port,'operation':operation,'errno':exc.errno if isinstance(exc,OSError)and type(exc.errno)is int else None,'errorClass':type(exc).__name__[:80],'message':str(exc)[:256],'pythonMonoS':at}
class KernelObservationError(RuntimeError):
 def __init__(self,reason,evidence):self.evidence=evidence;super().__init__(reason)
def parse_kernel_table(stdout,stderr,exit_code,ports):
 evidence={'format':'aeris-kernel-tcp-listen/1','status':'REFUSED_INCOMPLETE','command':['/usr/sbin/netstat','-an','-p','tcp'],'targetPorts':list(ports),'exitCode':exit_code,'stdoutBytes':len(stdout),'stdoutSha256':hashlib.sha256(stdout).hexdigest(),'stderrBytes':len(stderr),'stderrSha256':hashlib.sha256(stderr).hexdigest(),'headerVerified':False,'rowCount':0,'listeners':[]}
 def refuse(reason):raise KernelObservationError(reason,evidence)
 if exit_code!=0 or stderr:refuse('KERNEL_OBSERVER_EXIT_OR_STDERR_AMBIGUITY')
 if len(stdout)>1024*1024:refuse('KERNEL_OBSERVER_STDOUT1MIB_BOUND')
 try:lines=[line for line in stdout.decode('ascii').splitlines()if line.strip()]
 except UnicodeError:refuse('KERNEL_OBSERVER_ASCII_GRAMMAR_REQUIRED')
 if len(lines)<2 or lines[0]!='Active Internet connections (including servers)'or lines[1].split()!=['Proto','Recv-Q','Send-Q','Local','Address','Foreign','Address','(state)']:refuse('KERNEL_OBSERVER_KNOWN_COMPLETE_HEADER_REQUIRED')
 evidence['headerVerified']=True
 states={'LISTEN','ESTABLISHED','CLOSE_WAIT','FIN_WAIT_1','FIN_WAIT_2','LAST_ACK','CLOSING','SYN_SENT','SYN_RCVD','TIME_WAIT','CLOSED'}
 def address(value):
  if value=='*.*':return '*',None
  try:
   host,port=value.rsplit('.',1);assert port.isascii()and port.isdigit()and 0<=int(port)<=65535
   if host!='*':ipaddress.ip_address(host)
   return host,int(port)
  except (AssertionError,ValueError):refuse('KERNEL_OBSERVER_ADDRESS_GRAMMAR_REQUIRED')
 for line in lines[2:]:
  fields=line.split()
  if len(fields)!=6 or fields[0]not in {'tcp4','tcp6','tcp46'}or not fields[1].isascii()or not fields[1].isdigit()or not fields[2].isascii()or not fields[2].isdigit()or fields[5]not in states:refuse('KERNEL_OBSERVER_COMPLETE_TCP_ROW_GRAMMAR_REQUIRED')
  host,port=address(fields[3]);address(fields[4]);evidence['rowCount']+=1
  if fields[5]=='LISTEN'and port is None:refuse('KERNEL_OBSERVER_AMBIGUOUS_LISTEN_PORT')
  if fields[5]=='LISTEN'and port in ports:
   evidence['listeners'].append({'family':fields[0],'address':host,'port':port,'state':'LISTEN'})
   if len(evidence['listeners'])>32:refuse('KERNEL_OBSERVER_TARGET_ROW32_BOUND')
 evidence['status']='COMPLETE';return evidence
def checked_kernel_snapshot(value,ports):
 assert isinstance(value,dict)and value.get('format')=='aeris-kernel-tcp-listen/1'and value.get('status')=='COMPLETE'and value.get('headerVerified')is True and value.get('targetPorts')==list(ports),'KERNEL_OBSERVER_VALIDATED_COMPLETE_SNAPSHOT_REQUIRED'
 assert value.get('exitCode')==0 and type(value.get('exitCode'))is int and value.get('stderrBytes')==0 and type(value.get('stderrBytes'))is int,'KERNEL_OBSERVER_ZERO_EXIT_STDERR_REQUIRED'
 assert type(value.get('stdoutBytes'))is int and 100<=value['stdoutBytes']<=1024*1024 and isinstance(value.get('stdoutSha256'),str)and len(value['stdoutSha256'])==64 and all(ch in '0123456789abcdef'for ch in value['stdoutSha256']),'KERNEL_OBSERVER_BOUNDED_RAW_IDENTITY_REQUIRED'
 assert type(value.get('rowCount'))is int and value['rowCount']>=0 and isinstance(value.get('listeners'),list)and len(value['listeners'])<=32 and value['rowCount']>=len(value['listeners']),'KERNEL_OBSERVER_COMPLETE_ROW_COUNT_REQUIRED'
 for row in value['listeners']:
  assert isinstance(row,dict)and set(row)=={'family','address','port','state'}and row['family']in {'tcp4','tcp6','tcp46'}and row['state']=='LISTEN'and type(row['port'])is int and row['port']in ports,'KERNEL_OBSERVER_TARGET_LISTEN_ROWS_REQUIRED'
  if row['address']!='*':ipaddress.ip_address(row['address'])
 return value
def observe_kernel_listeners(ports):
 started=host_clock.now_s();proc=None;selector=selectors.DefaultSelector();output=bytearray();errors=bytearray();capture_error=None
 try:
  proc=kernel_popen(['/usr/sbin/netstat','-an','-p','tcp'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  for stream,target in [(proc.stdout,output),(proc.stderr,errors)]:os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,target)
  while selector.get_map():
   remaining=3-(host_clock.now_s()-started)
   if remaining<=0:raise TimeoutError('KERNEL_OBSERVER3S_TIMEOUT')
   for key,_ in selector.select(min(.1,remaining)):
    data=os.read(key.fileobj.fileno(),65536)
    if not data:selector.unregister(key.fileobj);continue
    target=key.data
    if len(output)+len(errors)+len(data)>1024*1024:raise RuntimeError('KERNEL_OBSERVER_COMBINED1MIB_BOUND')
    target.extend(data)
  exit_code=proc.wait(timeout=max(.001,3-(host_clock.now_s()-started)))
 except BaseException as exc:capture_error=exc
 finally:
  selector.close()
  if proc is not None:
   if proc.poll()is None:
    proc.terminate()
    try:proc.wait(timeout=.5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=.5)
   if proc.stdout:proc.stdout.close()
   if proc.stderr:proc.stderr.close()
 if capture_error is not None:raise KernelObservationError(type(capture_error).__name__+':'+str(capture_error)[:128],{'clockBasis':host_clock.BASIS,'hostBootId':os.environ.get('BETA06_HOST_BOOT_UUID'),'status':'REFUSED_CAPTURE_INCOMPLETE','targetPorts':list(ports),'stdoutBytes':len(output),'stdoutSha256':hashlib.sha256(output).hexdigest(),'stderrBytes':len(errors),'stderrSha256':hashlib.sha256(errors).hexdigest(),'startedPythonMonoS':started,'finishedPythonMonoS':host_clock.now_s()})from capture_error
 result=parse_kernel_table(bytes(output),bytes(errors),exit_code,ports);result.update(clockBasis=host_clock.BASIS,hostBootId=os.environ.get('BETA06_HOST_BOOT_UUID'),startedPythonMonoS=started,finishedPythonMonoS=host_clock.now_s());return result
def probe_host_ports(ports,*,socket_factory=socket.socket,clock=host_clock.now_s,kernel_observer=None):
 ports=tuple(ports);assert len(ports)==2 and len(set(ports))==2 and all(type(p)is int and 0<p<65536 for p in ports),'EXACT_TWO_DISTINCT_HOST_PORTS'
 report={'format':'aeris-host-port-probe/1','clockBasis':host_clock.BASIS,'hostBootId':os.environ.get('BETA06_HOST_BOOT_UUID'),'status':'PROBING','address':'127.0.0.1','ports':list(ports),'reuseAddress':True,'reusePort':False,'startedPythonMonoS':clock(),'finishedPythonMonoS':None,'heldTogetherUntilCleanup':False,'events':[],'failure':None,'closeFailures':[],'noToctouGuarantee':True,'kernelBefore':None,'kernelWhileHeld':None};handles=[];cause=None;port=None;operation=None;observer=kernel_observer or observe_kernel_listeners
 try:
  operation='kernel_LISTEN_before';before=checked_kernel_snapshot(observer(ports),ports);report['kernelBefore']=before
  if before.get('status')!='COMPLETE'or before.get('targetPorts')!=list(ports):raise RuntimeError('KERNEL_OBSERVER_INCOMPLETE_BEFORE')
  if before['listeners']:port=before['listeners'][0]['port'];raise RuntimeError('FOREIGN_KERNEL_LISTENER_BEFORE_PROBE')
  for port in ports:
   operation='socket';sock=socket_factory(socket.AF_INET,socket.SOCK_STREAM);handles.append((port,sock));report['events'].append({'port':port,'operation':operation,'ok':True})
   operation='setsockopt_SO_REUSEADDR';sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);report['events'].append({'port':port,'operation':operation,'ok':True})
   operation='bind';sock.bind(('127.0.0.1',port));report['events'].append({'port':port,'operation':operation,'ok':True})
   operation='listen';sock.listen(1);report['events'].append({'port':port,'operation':operation,'ok':True})
  report['heldTogetherUntilCleanup']=True;operation='kernel_LISTEN_while_held';held=checked_kernel_snapshot(observer(ports),ports);report['kernelWhileHeld']=held
  expected=sorted([('tcp4','127.0.0.1',p)for p in ports]);actual=sorted((row['family'],row['address'],row['port'])for row in held.get('listeners',[]))
  if held.get('status')!='COMPLETE'or held.get('targetPorts')!=list(ports)or actual!=expected:
   port=next((p for p in ports if actual.count(('tcp4','127.0.0.1',p))!=1),ports[0]);raise RuntimeError('KERNEL_OBSERVER_MUST_SEE_EXACT_OWNED_TWO_AND_NO_FOREIGN_LISTENERS')
 except BaseException as exc:
  cause=exc;report['failure']=detail(exc,port,operation,clock())
  if isinstance(exc,KernelObservationError):report['kernelObservationError']=exc.evidence
 finally:
  for owned_port,sock in reversed(handles):
   try:sock.close();report['events'].append({'port':owned_port,'operation':'close','ok':True})
   except BaseException as exc:report['closeFailures'].append(detail(exc,owned_port,'close',clock()))
  report['finishedPythonMonoS']=clock();report['status']='REFUSED'if cause is not None or report['closeFailures']else'PASS_HOST_PORT_PROBE_NOT_STARTUP_GUARANTEE'
  assert len(json.dumps(report,separators=(',',':'),allow_nan=False).encode())<=16*2**10,'BOUNDED_PORT_PROBE_DIAGNOSTIC16KIB'
 if cause is not None or report['closeFailures']:raise PortProbeError(report)from cause
 return report
