"""Owned engineering ADB-forward channel. STATUS only, no authority or reconnect."""
import errno,json,os,re,select,socket,time,struct
from .status15_wire import HelloParser,ResponseParser,MAX_RESPONSE,unique,request_bytes
from .candidate import CERT
NAME='vn.rtr.aeris.mission.observe15'
_REAL_SOCKET=socket.socket
HELLO_FIELDS={'format','version','socketName','pid','sourceSHA256','processEpoch','viewEpoch','apkSHA256','certificateSHA256','appUid','peerUid','peerPid','debuggable','capabilities','authorityRestorable','localOnly'}

def need(ok,name):
 if not ok:raise ValueError('STATUS15_'+name)

def listener(argv,raw,port):
 need(argv==['/usr/sbin/lsof','-nP','-a','-iTCP:'+str(port),'-sTCP:LISTEN','-Fpcfn'],'FIXED_LISTENER_QUERY')
 names=[];commands=[];pids=[]
 for line in raw.splitlines():
  if line.startswith('n'):names.append(line[1:])
  elif line.startswith('c'):commands.append(line[1:])
  elif line.startswith('p'):pids.append(line[1:])
 need(names and commands and all(v=='adb'for v in commands)and pids and all(re.fullmatch('[1-9][0-9]*',v)for v in pids),'ACTUAL_ADB_LISTENER_RECORD')
 need(all(v in('127.0.0.1:'+str(port),'[::1]:'+str(port),'localhost:'+str(port))for v in names),'LOOPBACK_LISTENER_ONLY')
 return {'listenerNames':names,'ADBListenerPIDs':[int(v)for v in pids],'loopbackVerifiedFromOriginalQuery':True}

def hello(raw,baseline,source,apk):
 need(type(raw)is bytes and 4<len(raw)<=2052 and struct.unpack('!I',raw[:4])[0]==len(raw)-4,'HELLO_ORIGINAL_LENGTH')
 v=json.loads(raw[4:],object_pairs_hook=unique)
 need(type(v)is dict and set(v)==HELLO_FIELDS and v['format']=='aeris-observer15-hello'and type(v['version'])is int and v['version']==1,'HELLO_SCHEMA')
 need(v['socketName']==NAME and v['sourceSHA256']==source and v['apkSHA256']==apk and v['certificateSHA256']==CERT,'HELLO_INSTALLED_SOURCE_APK_CERT_ASSERTIONS')
 need(type(v['pid'])is int and v['pid']==baseline['pid']and v['processEpoch']==baseline['processEpoch']and type(v['viewEpoch'])is int and v['viewEpoch']==baseline['viewEpoch'],'HELLO_LEGACY_PROCESS_ENROLLMENT')
 need(type(v['appUid'])is int and v['appUid']>=10000 and type(v['peerUid'])is int and v['peerUid']in(0,2000)and type(v['peerPid'])is int and v['peerPid']>0,'HELLO_ENGINEERING_PEER_ASSERTIONS_NOT_HOST_KERNEL_ATTESTATION')
 need(v['debuggable']is True and v['capabilities']==['STATUS']and v['authorityRestorable']is False and v['localOnly']is True,'HELLO_READ_ONLY_DEVELOPMENT_CAPABILITIES')
 return v

class StatusSocket:
 def __init__(self,device,baseline,baseline_ref,source,apk,*,connect_factory=socket.socket,planned_transition=None):
  self.device=device;self.store=device.store;self.budget=device.budget;self.baseline=baseline;self.baseline_ref=baseline_ref;self.source=source;self.apk=apk;self.connect_factory=connect_factory;self.sock=None;self.port=None;self.forward_set=False;self.active=False;self.closed=False;self.failure=None;self.open_ref=None;self.lease=None;self.last_prefix=b'';self.sequence=0;self.close_result=None;self.forward_attempted=False;self.prefix_undurable=False;self.sent_prefix=bytearray();self.planned_transition=planned_transition
 def _deadline(self,end):
  if self.device.now()>=end:raise TimeoutError('STATUS15_CHANNEL_DEADLINE')
 def _recv_frame(self,parser,end,*,timing=None):
  first=False
  while parser.result is None:
   self._deadline(end)
   ready,_,_=select.select([self.sock],[],[],min(.01,max(0,(end-self.device.now())/1e9)))
   if not ready:continue
   cap=(2053 if isinstance(parser,HelloParser)else MAX_RESPONSE+1)-len(parser.raw);raw=self.sock.recv(max(1,cap))
   if raw and timing is not None and not first:timing.point('firstByte');first=True
   if not raw:raise RuntimeError('STATUS15_PEER_EOF_BEFORE_FRAME')
   parser.feed(raw)
  if timing is not None:timing.point('frameComplete')
  # Detect immediately available trailing bytes/EOF; a later unsolicited byte
  # is rejected by the next pre-send check. No stale fallback or reconnect.
  ready,_,_=select.select([self.sock],[],[],0)
  if ready:
   extra=self.sock.recv(1)
   if extra:parser.feed(extra)
   raise RuntimeError('STATUS15_UNEXPECTED_PEER_EOF')
  return parser.eof()
 def _mapping(self,end,*,present):
  raw=self.device.command(['forward','--list'],deadline_ns=end,maximum_bytes=4096).decode('ascii');ref=self.device.last_command_ref
  expected=self.device.serial+' tcp:'+str(self.port)+' localabstract:'+NAME
  own=[line for line in raw.splitlines()if line.split()[0:2]==[self.device.serial,'tcp:'+str(self.port)]]
  need(own==([expected]if present else[]),'OWNED_EXACT_FORWARD_MAPPING')
  return ref
 def open(self,end):
  self.device._check_budget_actor()
  if self.budget.mock and self.connect_factory is _REAL_SOCKET:raise ValueError('STATUS15_MOCK_FORBIDS_REAL_SOCKET')
  need(self.sock is None and not self.closed,'ONE_CHANNEL_START')
  self.lease=self.budget.reserve_lease({'commands':65536,'command_receipts':16384});started=self.device.now();prefix=b'';self.open_details={}
  try:
   before=self.device.pid('vn.rtr.aeris.mission',deadline_ns=end);before_ref=self.device.last_command_ref;need(before==self.baseline['pid'],'ACTUAL_PID_BEFORE_OPEN')
   self.forward_attempted=True
   value=self.device.command(['forward','--no-rebind','tcp:0','localabstract:'+NAME],deadline_ns=end,maximum_bytes=64)
   need(re.fullmatch(rb'[1-9][0-9]{0,4}\n?',value)is not None and 0<int(value)<=65535,'ALLOCATED_FORWARD_PORT');self.port=int(value);self.forward_set=True;forward_ref=self.device.last_command_ref;mapping_ref=self._mapping(end,present=True)
   from .commands import HostCommands
   query=getattr(self.device,'host_query',None);need(type(query)is HostCommands and query.budget is self.budget and query.root==self.device.root.parent/'host-queries','ORIGINAL_CASE_HOST_QUERY_OWNER')
   argv=['/usr/sbin/lsof','-nP','-a','-iTCP:'+str(self.port),'-sTCP:LISTEN','-Fpcfn'];observed=listener(argv,query(argv),self.port);listener_ref=query.last_ref
   self.sock=self.connect_factory(socket.AF_INET,socket.SOCK_STREAM);self.sock.setblocking(False);code=self.sock.connect_ex(('127.0.0.1',self.port))
   if code not in(0,errno.EINPROGRESS,errno.EWOULDBLOCK):raise OSError(code,'STATUS15_CONNECT')
   while code:
    self._deadline(end);_,ready,_=select.select([],[self.sock],[],min(.01,max(0,(end-self.device.now())/1e9)))
    if ready:code=self.sock.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR);break
   need(code==0,'CONNECT_LOOPBACK');need(self.sock.getpeername()==('127.0.0.1',self.port),'ACTUAL_LOOPBACK_CHANNEL')
   parser=HelloParser()
   try:prefix=self._recv_frame(parser,end)
   finally:prefix=bytes(parser.raw)
   self.enrollment=hello(prefix,self.baseline,self.source,self.apk)
   prepared=getattr(self.device,'_native_prepared_apk_refs',None);need(type(prepared)is tuple and len(prepared)==3 and prepared[2]==self.apk,'ORIGINAL_PREPARED_INSTALLED_APK_REFS')
   after=self.device.pid('vn.rtr.aeris.mission',deadline_ns=end);after_ref=self.device.last_command_ref;need(after==before,'ACTUAL_PID_AFTER_OPEN')
   with self.budget.use_lease(self.lease):
    proof={'format':'aeris-status15-channel-open','version':1,'sourceSHA256':self.source,'APKSHA256':self.apk,'serial':self.device.serial,'port':self.port,'socketName':NAME,'baselineRequestRef':self.baseline_ref,'PIDBeforeCommandRef':before_ref,'PIDAfterCommandRef':after_ref,'forwardCommandRef':forward_ref,'mappingCommandRef':mapping_ref,'listenerQueryRef':listener_ref,'installedPathCommandRef':prepared[0],'installedSHACommandRef':prepared[1],'helloRef':self.store.command_bytes(prefix),'startedHostNs':started,'readyHostNs':self.device.now(),'localPeer':list(self.sock.getpeername()),'hostLocalEndpoint':list(self.sock.getsockname()),'listener':observed,'authorityRestored':False,'trust':'LOCAL_ENGINEERING_ADB_ENROLLMENT_NOT_REMOTE_ATTESTATION'}
    if self.planned_transition is not None:proof.update(version=2,plannedTransitionRef=self.planned_transition['receiptRef'])
    self.open_ref=self.store.receipt('status15-channel-open.json',proof)
   self.open_details=proof;self.active=True;return proof
  except BaseException as error:
   self.failure=error;self.last_prefix=prefix
   try:
    if self.lease is not None:
     with self.budget.use_lease(self.lease):self.store.receipt('status15-channel-open-failure.json',{'format':'aeris-status15-channel-open-failure','version':1,'port':self.port,'forwardSet':self.forward_set,'prefixRef':self.store.command_bytes(prefix),'failure':str(error)[:256],'flightAcceptance':False})
   except BaseException as preserve:self.prefix_undurable=True;error.add_note('STATUS15_OPEN_PREFIX_UNDURABLE:'+str(preserve)[:256])
   raise
 def exchange(self,request,end,timing):
  need(self.active and not self.closed and self.failure is None,'ACTIVE_CHANNEL_NO_RECONNECT');self.sequence+=1;need(self.sequence<=900,'CHANNEL900_REQUESTS')
  wire=request_bytes(request);parser=ResponseParser();self.last_request_wire=wire;self.sent_prefix=bytearray();self.last_prefix=b''
  try:
   ready,_,_=select.select([self.sock],[],[],0)
   if ready:
    extra=self.sock.recv(1);self.last_prefix=extra;raise RuntimeError('STATUS15_UNSOLICITED_BEFORE_SEND')
   timing.point('sendStart');view=memoryview(wire)
   while view:
    self._deadline(end)
    _,ready,_=select.select([],[self.sock],[],min(.01,max(0,(end-self.device.now())/1e9)))
    if not ready:continue
    n=self.sock.send(view)
    if type(n)is not int or not 0<n<=len(view):raise RuntimeError('STATUS15_INVALID_SEND_COUNT')
    self.sent_prefix.extend(view[:n]);view=view[n:]
   timing.point('bytesSent');return self._recv_frame(parser,end,timing=timing)
  except BaseException as error:self.failure=error;raise
  finally:
   if parser.raw:self.last_prefix=bytes(parser.raw)
 def close(self,end):
  if self.close_result is not None:return self.close_result
  primary=self.failure;tail=bytearray();eof=self.sock is None;socket_closed=self.sock is None;mapping_before=None;remove=None;mapping_after=None
  if self.sock is not None:
   try:
    try:self.sock.shutdown(socket.SHUT_WR)
    except OSError:pass
    while not eof:
     self._deadline(end);ready,_,_=select.select([self.sock],[],[],min(.01,max(0,(end-self.device.now())/1e9)))
     if not ready:continue
     raw=self.sock.recv(min(2049-len(tail),2049))
     if not raw:eof=True;break
     tail.extend(raw)
     if len(tail)>2048:raise ValueError('STATUS15_CLOSE_TAIL2048_PREFIX')
   except BaseException as error:
    if primary is None:primary=error
    else:primary.add_note('STATUS15_CLOSE_SECONDARY:'+str(error)[:256])
   finally:
    try:self.sock.close();socket_closed=True
    except BaseException as error:
     if primary is None:primary=error
  if self.forward_set:
   try:
    mapping_before=self._mapping(end,present=True)
    self.device.command(['forward','--remove','tcp:'+str(self.port)],deadline_ns=end,maximum_bytes=64);remove=self.device.last_command_ref;mapping_after=self._mapping(end,present=False);self.forward_set=False
   except BaseException as error:
    if primary is None:primary=error
    else:primary.add_note('STATUS15_FORWARD_REMOVE_SECONDARY:'+str(error)[:256])
  drained=eof and socket_closed and not self.forward_set and not(self.forward_attempted and self.port is None)and not self.prefix_undurable
  proof={'format':'aeris-status15-channel-close','version':1,'channelOpenRef':self.open_ref,'port':self.port,'requests':self.sequence,'EOFObserved':eof,'socketClosed':socket_closed,'mappingBeforeRef':mapping_before,'removeCommandRef':remove,'mappingAfterRef':mapping_after,'forwardRemoved':not self.forward_set and not(self.forward_attempted and self.port is None),'tailRef':None,'drainComplete':drained,'captureComplete':drained and primary is None and not tail,'failure':None if primary is None else str(primary)[:256],'authorityRestored':False,'flightAcceptance':False}
  if self.lease is not None:
   with self.budget.use_lease(self.lease):
    closing=self.budget.snapshot().get('failed')is not None;proof['tailRef']=self.store.command_bytes(tail,closing=closing);ref=self.store.receipt('status15-channel-close.json',proof,closing=closing)
   if drained:self.budget.release_lease(self.lease);self.lease=None
  else:ref=None
  self.closed=True;self.active=False;self.close_result={'receipt':proof,'receiptRef':ref}
  if not drained:raise primary or RuntimeError('STATUS15_CHANNEL_DRAIN_UNKNOWN')
  if self.failure is None and(primary is not None or tail):raise primary or RuntimeError('STATUS15_UNEXPECTED_CLOSE_BYTES')
  return self.close_result
