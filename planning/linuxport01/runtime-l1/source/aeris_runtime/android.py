"""Bounded public Android bridge and explicitly authorized recovery08 development update."""
from pathlib import Path
import base64,contextlib,json,os,re,selectors,shlex,subprocess,time,hashlib,tarfile
from .candidate import put
_REAL_POPEN=subprocess.Popen
from pilot.betaintegrated01.runtime.ap_stage import canonical
def _capture_cleanup(primary,operations,errors):
 from .cleanup import cleanup
 def tracked(label,operation):
  def run():
   try:operation()
   except BaseException as error:
    errors.append({'operation':label,'type':type(error).__name__,'error':str(error)[:256]});raise
  return run
 return cleanup(primary,[(label,tracked(label,operation))for label,operation in operations])
def _stop_capture_process(process):
 if process.poll()is None:process.terminate()
 try:process.wait(timeout=2)
 except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
ANDROID_READY_SCRIPT='i=0; while [ "$i" -lt 120 ]; do v=$(getprop sys.boot_completed); printf "BOOT:%s\\n" "$v"; [ "$v" = 1 ] && break; i=$((i+1)); sleep 0.25; done; [ "$v" = 1 ] || exit 21; p=$(pm path android); printf "PM:%s\\n" "$p"; case "$p" in package:/*) echo ANDROID_READY;; *) exit 22;; esac'
BOOTSTRAP_AM_STDOUT=b'Starting: Intent { cmp=vn.rtr.aeris.mission/.CockpitActivity (has extras) }\n'
BOOTSTRAP_AM_STDERR=b'Warning: Activity not started, intent has been delivered to currently running top-most instance.\n'
BOOTSTRAP_AM_NOTICE='BOOTSTRAP_SINGLE_TOP_DELIVERED_NON_AUTHORITY'
def _bootstrap_am_notice(args,out,err):
 # This is a transport classification derived from original bytes, never a
 # caller permission. Only the existing canonical public BOOTSTRAP shape.
 if len(args)!=11 or args[:10]!=['shell','am','start','-n','vn.rtr.aeris.mission/.CockpitActivity','--es','missionAction','BOOTSTRAP','--es','missionRequestBase64']or out!=BOOTSTRAP_AM_STDOUT or err!=BOOTSTRAP_AM_STDERR:return None
 try:
  raw=base64.b64decode(args[10],altchars=b'-_',validate=True)
  if not 0<len(raw)<=32768 or base64.urlsafe_b64encode(raw).decode()!=args[10]:return None
  def pairs(items):
   d={}
   for k,v in items:
    if k in d:raise ValueError('DUPLICATE_BOOTSTRAP_FIELD')
    d[k]=v
   return d
  body=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda value:(_ for _ in()).throw(ValueError('NONFINITE_BOOTSTRAP')))
  fields={'version','requestNonce','processEpoch','viewEpoch','baseRevision','sourceSHA256','context','provider','survey','expectedDraftSHA256'}
  if type(body)is not dict or set(body)!=fields or json.dumps(body,separators=(',',':'),ensure_ascii=False).encode()!=raw:return None
  if type(body['version'])is not int or body['version']!=1 or type(body['viewEpoch'])is not int or body['viewEpoch']<=0 or type(body['baseRevision'])is not int or body['baseRevision']<0:return None
  if any(type(body[k])is not str or re.fullmatch('[a-f0-9]{%d}'%n,body[k])is None for k,n in[('requestNonce',32),('processEpoch',32),('sourceSHA256',64)]):return None
  if type(body['context'])is not dict or set(body['context'])!={'run','epoch','boot','operator','generation','profileId'}or len(canonical(body['context']))>256 or any(type(v)is not str or not v for v in body['context'].values())or type(body['provider'])is not dict or not body['provider']:return None
  if not(type(body['survey'])is dict and body['expectedDraftSHA256']is None or body['survey']is None and type(body['expectedDraftSHA256'])is str and re.fullmatch('[a-f0-9]{64}',body['expectedDraftSHA256'])):return None
  return BOOTSTRAP_AM_NOTICE
 except(ValueError,TypeError,UnicodeError):return None

class AndroidDevice:
 APPLICATION_PACKAGE="vn.rtr.aeris.mission"
 PRODUCT_ACTIVITY_COMPONENT="vn.rtr.aeris.mission/.ProductActivity"
 PRODUCT_STATUS_COMPONENT="vn.rtr.aeris.mission/.ProductStatusReceiver"
 PRODUCT_STATUS_ACTION="vn.rtr.aeris.mission.PRODUCT_STATUS"
 COLD_ABSENCE_PREDICATE="if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi"
 def __init__(self,adb,serial,evidence,*,now=time.monotonic_ns,budget=None,observer_tag='AERIS_MISSION'):
  self.adb=str(Path(adb).resolve());self.serial=serial;self.root=Path(evidence);self.now=now;self.sequence=0
  if len(self.adb.encode())>256:raise ValueError('FIXED_ADB_PATH256_BOUND')
  if not re.fullmatch('emulator-[0-9]+',serial):raise ValueError('EXPLICIT_OWNED_EMULATOR_ONLY')
  self.budget=budget;self.store=None;self.observer=None;self.last_snapshot_ref=None;self.last_command_ref=None;self.preparation_commands=0;self._install_authorization=None;self.include_quarantine=False;self.io_broker=None;self.status_socket=None;self.status_sockets=[];self.host_query=None;self.live_check=None;self._android_ready=None;self._content_reader_preparation_attempted=False
  if budget is not None:
   from .metadata_budget import MetadataBudget
   if type(budget)is not MetadataBudget:raise ValueError('ANDROID_EXACT_METADATA_BUDGET_REQUIRED')
   from .once_store import OnceStore
   from .ack_observer import AckObserver
   self.store=OnceStore(self.root,budget=budget);self.observer=AckObserver(self,self.store,tag=observer_tag)
 def _check_budget_actor(self,*,popen=None):
  from .metadata_budget import MetadataBudget
  if type(self.budget)is not MetadataBudget:raise ValueError('ANDROID_EXACT_METADATA_BUDGET_REQUIRED')
  if self.budget.mock:
   if (subprocess.Popen if popen is None else popen)is _REAL_POPEN:raise ValueError('MOCK_LEDGER_FORBIDS_REAL_ANDROID_ACTOR')
   state=self.budget.check()
   if state.get('mockOnly')is not True:raise ValueError('ANDROID_MOCK_LEDGER_PROVENANCE_REQUIRED')
   return state
  return self.budget.require_real_actor()
 def command(self,args,*,deadline_ns,maximum_bytes=131072,dispatch_deadline_ns=None):
  self._check_budget_actor()
  if self.live_check is not None:self.live_check()
  if self.store is None:raise ValueError('EXPLICIT_ONCE_STORE_AND_BUDGET_REQUIRED')
  if type(maximum_bytes)is not int or not 0<maximum_bytes<=131072:raise ValueError('ANDROID_COMMAND131072_BOUND')
  args=list(args);maximum_bytes=min(maximum_bytes,self._command_bound(args));dto=args[:4]==['shell','run-as',self.APPLICATION_PACKAGE,'cat']
  argv_bound=8192 if (args[:3]==['shell','am','start']and len(args)==11)or(self.__class__.__name__=='AndroidDomain17'and len(args)==16 and args[:5]==['shell','am','broadcast','-a','vn.rtr.aeris.mission.JOURNAL_LIFECYCLE17'])else 1024 if args[:3]==['shell','am','broadcast']else 512
  claims={'commands':2*(maximum_bytes+1)+argv_bound+32768,'command_receipts':1280+8192+(4096 if self.io_broker is not None and self.io_broker.accepts(args)else 0)}
  if dto:claims['dto']=maximum_bytes+1+8192
  with self.budget.operation(claims):return self._command(args,deadline_ns=deadline_ns,maximum_bytes=maximum_bytes,dispatch_deadline_ns=dispatch_deadline_ns)
 def _command(self,args,*,deadline_ns,maximum_bytes,dispatch_deadline_ns=None):
  install17_context=None
  if self.__class__.__name__=='AndroidDomain17'and args[:2]==['install','-r']:
   from .install17 import install_context17
   install17_context=install_context17(self,args,consume=True)
  self.budget.tick('commands');self.sequence+=1
  if self.sequence>3700:raise ValueError('DECLARED_CAMPAIGN3700_COMMAND_ENVELOPE')
  start=self.now()
  if start>=deadline_ns:raise TimeoutError('ANDROID_COMMAND_DEADLINE')
  if self.io_broker is not None and self.io_broker.accepts(args):return self._broker_command(args,deadline_ns=deadline_ns,maximum_bytes=maximum_bytes,start=start)
  remote_args=['shell',shlex.join(args[1:])] if args and args[0]=='shell' else args
  argv=[self.adb,'-s',self.serial,*remote_args]
  argv_bound=8192 if (args[:3]==['shell','am','start']and len(args)==11)or(self.__class__.__name__=='AndroidDomain17'and len(args)==16 and args[:5]==['shell','am','broadcast','-a','vn.rtr.aeris.mission.JOURNAL_LIFECYCLE17'])else 1024 if args[:3]==['shell','am','broadcast']else 512
  if len(canonical(argv))>argv_bound:raise ValueError('ANDROID_SOURCE_ARGV_BOUND:'+str(argv_bound))
  # Reserve is already durable at entry, and every captured write is guarded.
  self.budget.ensure('command_receipts',1280+8192)
  self.budget.ensure('dto'if args[:4]==['shell','run-as',self.APPLICATION_PACKAGE,'cat']else'commands',maximum_bytes+1+8192)
  sel=selectors.DefaultSelector();p=None;chunks={'stdout':bytearray(),'stderr':bytearray()};failure=None;complete=False;cleanup_errors=[];delivery_notice=None
  try:
   if self.live_check is not None:self.live_check()
   if self.now()>=deadline_ns:raise TimeoutError('ANDROID_COMMAND_DEADLINE')
   if dispatch_deadline_ns is not None:
    tap=len(args)==5 and args[:3]==['shell','input','tap']and all(re.fullmatch('[0-9]{1,4}',v)for v in args[3:])
    swipe=self.serial=='emulator-5582'and self.observer.tag=='AERIS_PRODUCT_STATUS'and len(args)==8 and args[:3]==['shell','input','swipe']and args[-1]=='250'and all(re.fullmatch('[0-9]{1,4}',v)for v in args[3:7])
    if type(dispatch_deadline_ns)is not int or not(tap or swipe):raise ValueError('NAVIGATION_DISPATCH_DEADLINE_EXACT_TAP_OR_OWNED250MS_SWIPE')
    start=self.now()
    if start>=deadline_ns or start>dispatch_deadline_ns:raise TimeoutError('NAVIGATION_ACTUAL_DISPATCH200MS')
   p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   for name,stream in [('stdout',p.stdout),('stderr',p.stderr)]:os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
   while sel.get_map():
    if self.live_check is not None:self.live_check()
    if self.now()>=deadline_ns:raise TimeoutError('ANDROID_COMMAND_DEADLINE')
    for key,_ in sel.select(min(.05,max(0,(deadline_ns-self.now())/1e9))):
     name=key.data;raw=os.read(key.fileobj.fileno(),min(65536,maximum_bytes+1-len(chunks[name])))
     if not raw:sel.unregister(key.fileobj);continue
     chunks[name].extend(raw)
     if len(chunks[name])>maximum_bytes:raise ValueError('ANDROID_COMMAND_OVERSIZED_PREFIX_RETAINED_INCOMPLETE')
   p.wait(timeout=max(.001,(deadline_ns-self.now())/1e9));complete=True
   if p.returncode:raise RuntimeError('ANDROID_COMMAND_EXIT:'+str(p.returncode))
   if install17_context is not None:
    from .install17 import install_success17
    if not install_success17(bytes(chunks['stdout'])):raise RuntimeError('INSTALL17_EXACT_INSTALL_RESULT_UNCONFIRMED')
   if chunks['stderr']:
    delivery_notice=_bootstrap_am_notice(args,bytes(chunks['stdout']),bytes(chunks['stderr']))
    if delivery_notice is None:raise RuntimeError('ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE')
  except BaseException as error:failure=error
  finally:
   operations=[]
   if p is not None:operations.append(('command-process-stop',lambda:_stop_capture_process(p)))
   operations.append(('command-selector-close',sel.close))
   if p is not None:operations.extend([('command-stdout-close',p.stdout.close),('command-stderr-close',p.stderr.close)])
   failure=_capture_cleanup(failure,operations,cleanup_errors)
   if cleanup_errors:complete=False
   if delivery_notice is not None and self.now()>=deadline_ns and failure is None:failure=TimeoutError('ANDROID_BOOTSTRAP_DELIVERY_FINAL_DEADLINE')
   if not complete or failure is not None:delivery_notice=None
   # Oversize has one detection byte beyond the accepted bound. Retain it as a
   # failed prefix blob; never label a partial command capture lossless/accepted.
   try:
    dto=args[:4]==['shell','run-as',self.APPLICATION_PACKAGE,'cat'] and complete and failure is None
    out=self.store.blob(chunks['stdout'],owner='dto')if dto else self.store.command_bytes(chunks['stdout']);err=self.store.command_bytes(chunks['stderr']);argv_ref=self.store.command_bytes(canonical(argv))
    self.last_command={'format':'aeris-command','version':3,'sequence':self.sequence,'argvRef':argv_ref,'startedHostNs':start,'endedHostNs':self.now(),'exit':None if p is None else p.returncode,'stdoutRef':out,'stderrRef':err,'captureComplete':complete,'failure':None if failure is None else type(failure).__name__+':'+str(failure)[:256]}
    if delivery_notice is not None:self.last_command.update(version=5,androidDeliveryNotice=delivery_notice)
    if args[:2]==['install','-r']:
     install_context=install17_context if install17_context is not None else self._install_authorization
     self.last_command['version']=install_context.get('commandVersion',4);self.last_command['authorizationRef']=install_context['ref']
    self.last_command_ref=self.store.receipt('command-%05d.json'%self.sequence,self.last_command,owner='command_receipts')
   except BaseException as storage:
    primary=failure if failure is not None else storage
    detail=RuntimeError('COMMAND_PRIMARY='+type(primary).__name__+':'+str(primary)+'; PERSISTENCE_SECONDARY='+type(storage).__name__+':'+str(storage))
    for note in getattr(primary,'__notes__',())[:8]:detail.add_note(note)
    try:self.budget.failure(detail)
    except BaseException as closure:
     primary.add_note('UNDURABLE_FAILURE_DIAGNOSTIC:'+type(closure).__name__+':'+str(closure))
    primary.add_note('PERSISTENCE_SECONDARY:'+type(storage).__name__+':'+str(storage))
    raise primary from storage
   if cleanup_errors:
    try:self.budget.failure(failure,detail={'capture':'ANDROID_COMMAND','commandReceiptRef':self.last_command_ref,'cleanupErrors':cleanup_errors,'captureComplete':False})
    except BaseException as diagnostic:failure.add_note('COMMAND_CLEANUP_DIAGNOSTIC_SECONDARY:'+type(diagnostic).__name__+':'+str(diagnostic)[:256])
  if failure is not None:raise failure
  return bytes(chunks['stdout'])
 def start_io_broker(self,*,deadline_ns):
  from .io_broker import DeviceIOBroker
  if self.io_broker is not None:raise ValueError('ANDROID_BROKER_ONE_OWNER')
  self.io_broker=DeviceIOBroker(self)
  try:return self.io_broker.start(deadline_ns)
  except BaseException as error:self.io_broker.failure=error;raise
 def transfer_io_broker_to(self,new_device):
  if self.io_broker is not None:self.io_broker.transfer(new_device)
 def stop_io_broker(self,*,deadline_ns):
  if self.io_broker is None:return None
  return self.io_broker.close(deadline_ns)
 def _broker_command(self,args,*,deadline_ns,maximum_bytes,start):
  broker=self.io_broker;frame=None;failure=None;complete=False;code=None
  self.budget.ensure('command_receipts',4096+1280+8192)
  self.budget.ensure('dto'if args[:4]==['shell','run-as',self.APPLICATION_PACKAGE,'cat']else'commands',maximum_bytes+1+8192)
  try:
   frame=broker.execute(args,deadline_ns);code=frame['exit'];complete=True
   if code:raise RuntimeError('ANDROID_COMMAND_EXIT:'+str(code))
   if frame['stderr']:raise RuntimeError('ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE')
  except BaseException as error:
   failure=error;frame=broker.last_frame
   if frame is not None:code=frame['exit']
  try:
   if frame is not None:
    out=self.store.blob(frame['stdout'],owner='dto')if args[:4]==['shell','run-as',self.APPLICATION_PACKAGE,'cat']and complete and failure is None else self.store.command_bytes(frame['stdout'])
    err=self.store.command_bytes(frame['stderr']);proof=broker.command_proof(self.store,frame)
   else:
    out=self.store.command_bytes(getattr(broker,'last_prefix',b''));err=broker.retain_transport_stderr(self.store)
    proof=self.store.broker_proof({'format':'aeris-device-io-broker-command-failure','version':1,'launchStore':broker.original_root.name,'launchRef':broker.launch_ref,'pid':broker.process.pid,'operation':broker.last_operation,'prefixIsStdoutRef':True,'failure':str(failure)[:256]})
   logical_argv=[self.adb,'-s',self.serial,'shell',shlex.join(args[1:])]
   self.last_command={'format':'aeris-command','version':7,'sequence':self.sequence,'argvRef':self.store.command_bytes(canonical(logical_argv)),'startedHostNs':start,'endedHostNs':self.now(),'exit':code,'stdoutRef':out,'stderrRef':err,'captureComplete':complete,'failure':None if failure is None else type(failure).__name__+':'+str(failure)[:256],'brokerRef':proof}
   self.last_command_ref=self.store.receipt('command-%05d.json'%self.sequence,self.last_command,owner='command_receipts')
  except BaseException as storage:
   primary=failure if failure is not None else storage;broker.failure=primary;broker.capture_persistence_failed=True
   # One bounded nonaccepting preservation attempt, never an operation retry.
   # Prior partial output may already exist after an uncertain fsync failure;
   # this fallback explicitly does not claim physical deduplication/acceptance.
   try:
    fallback=self.store.command_bytes(getattr(broker,'last_prefix',b''),closing=True)
    broker.failed_capture_refs.append({'store':self.store.root.name,'ref':fallback,'uncertainPhysicalDuplicate':True,'acceptanceEvidence':False});broker.failed_capture_durable=True
   except BaseException as preserve:primary.add_note('BROKER_CAPTURE_PREFIX_UNDURABLE:'+str(preserve)[:256]);broker.failed_capture_durable=False
   try:self.budget.failure(primary,detail={'operation':'BROKER_COMMAND_PERSISTENCE','persistenceSecondary':str(storage)[:256]})
   except BaseException as closure:primary.add_note('BROKER_FAILURE_UNDURABLE:'+str(closure)[:256])
   if failure is not None:failure.add_note('BROKER_PERSISTENCE_SECONDARY:'+str(storage)[:256]);raise failure from storage
   raise
  if failure is not None:raise failure
  return frame['stdout']
 def open_status_socket(self,baseline,baseline_ref,source,apk,*,deadline_ns,planned_transition=None):
  from .status_socket import StatusSocket
  previous=self.status_socket
  if previous is not None:
   proof=planned_transition.get('proof',{})if type(planned_transition)is dict else{}
   if len(self.status_sockets)!=1 or previous.failure is not None or not previous.closed or previous.active or previous.lease is not None or previous.close_result is None:raise ValueError('STATUS_TRANSITION_CLOSED_HEALTHY_PREVIOUS_CHANNEL_REQUIRED')
   if proof.get('format')!='aeris-planned-bootstrap-status-transition'or proof.get('oldChannelOpenRef')!=previous.open_ref or proof.get('oldChannelCloseRef')!=previous.close_result['receiptRef']or proof.get('baselineRequestRef')!=baseline_ref or proof.get('sourceSHA256')!=source or proof.get('authorityRestored')is not False or proof.get('unexpectedEOFReconnect')is not False:raise ValueError('STATUS_TRANSITION_EXACT_SOURCE_TRANSACTION')
  elif planned_transition is not None:raise ValueError('STATUS_TRANSITION_REQUIRES_PREVIOUS_CHANNEL')
  self.status_socket=StatusSocket(self,baseline,baseline_ref,source,apk,planned_transition=planned_transition)
  self.status_sockets.append(self.status_socket)
  return self.status_socket.open(deadline_ns)
 def close_status_socket(self,*,deadline_ns):
  if self.status_socket is None:return None
  return self.status_socket.close(deadline_ns)
 def _command_bound(self,args):
  """Source-owned output envelopes, applied before spawning or pipe capture."""
  package=self.APPLICATION_PACKAGE
  from .status_socket import NAME
  if args==['forward','--no-rebind','tcp:0','localabstract:'+NAME]and self.status_socket is not None and self.status_socket.port is None:return 64
  if args==['forward','--list']and self.status_socket is not None:return 4096
  if self.status_socket is not None and self.status_socket.forward_set and self.status_socket.port is not None and args==['forward','--remove','tcp:'+str(self.status_socket.port)]:return 64
  if args==['shell','sh','-c',self.COLD_ABSENCE_PREDICATE]:return 16
  if len(args)==3 and args[:2]==['install','-r']and self._install_authorization is not None and args[2]==self._install_authorization['APKPath']:return 2048
  if len(args)==4 and args[:3]==['shell','input','text']and re.fullmatch('[a-f0-9]{64}',args[3]):return 64
  if args[:4]==['shell','run-as',package,'cat'] and len(args)==5 and args[4]in('files/runtime/response.json','files/runtime/current.json'):return 16384
  if self.observer is not None and self.observer.tag=='AERIS_PRODUCT_STATUS':
   if args==['shell','run-as',package,'du','-k','-s','files']:return 256
   if args==['shell','am','start','-n',self.PRODUCT_ACTIVITY_COMPONENT]:return 2048
   if self.serial=='emulator-5582'and args==['shell','sh','-c',ANDROID_READY_SCRIPT]:return 2048
   if self.serial=='emulator-5582'and args in(['root'],['wait-for-device'],['shell','id','-u'],['shell','cat','/proc/sys/kernel/random/boot_id']):return 2048
   if len(args)==5 and args[:4]==['shell','run-as',package,'cat']and re.fullmatch(r'files/product-exports01/success-[a-f0-9]{64}\.json',args[4]):return 4096
   if len(args)==8 and args[:3]==['shell','input','swipe']and args[-1]=='250'and all(re.fullmatch('[0-9]{1,4}',v)for v in args[3:7]):return 64
   if len(args)==10 and args[:9]==['shell','am','broadcast','-a',self.PRODUCT_STATUS_ACTION,'-n',self.PRODUCT_STATUS_COMPONENT,'--es','requestNonce']and re.fullmatch('[a-f0-9]{32}',args[9]):return 2048
   if len(args)==5 and args[:4]==['shell','run-as',package,'cat']and re.fullmatch(r'files/product-observations01/status-[a-f0-9]{32}\.json',args[4]):return 16384
   if args in(['reverse','--list'],['reverse','--no-rebind','tcp:8895','tcp:8895'],['reverse','--no-rebind','tcp:8896','tcp:8896'],['reverse','--remove','tcp:8895'],['reverse','--remove','tcp:8896']):return 4096
  if args==['shell','pidof',package]:return 64
  if len(args)==7 and args[:5]==['shell','log','-p','i','-t']and args[5]in('AERIS_MISSION','AERIS_PRODUCT_STATUS') and re.fullmatch('AERIS_OBSERVER_READY_[a-f0-9]{32}',args[-1]):return 64
  if args==['shell','am','start','-n',package+'/.CockpitActivity']:return 2048
  if len(args)==11 and args[:10]==['shell','am','start','-n',package+'/.CockpitActivity','--es','missionAction','BOOTSTRAP','--es','missionRequestBase64'] and re.fullmatch(r'[A-Za-z0-9_=\-]{1,43692}',args[10]):return 2048
  if len(args)==13 and args[:12]==['shell','am','broadcast','-n',package+'/.CockpitActivity$StatusReceiver','-a',package+'.STATUS','--es','missionAction','STATUS','--es','missionRequestBase64'] and re.fullmatch(r'[A-Za-z0-9_=\-]{1,684}',args[12]):return 2048
  if args==['shell','am','force-stop',package]:return 64
  if args==['shell','pm','path',package]:return 4096
  if args[:2]==['shell','sha256sum'] and len(args)==3 and args[2].startswith('/'):return 512
  if args==['shell','dumpsys','activity','activities'] or args==['exec-out','uiautomator','dump','/dev/tty']:
   self.preparation_commands+=1
   if self.preparation_commands>24:raise ValueError('ANDROID24_PREPARATION_OUTPUT_ENVELOPE')
   self.budget.tick('preparationCommands');return 131072
  if args[:3]==['shell','input','tap'] and len(args)==5 and all(re.fullmatch('[0-9]{1,4}',v)for v in args[3:]):return 64
  if args[:4]==['shell','input','touchscreen','motionevent'] and len(args)==7 and args[4]in('DOWN','MOVE','UP') and all(re.fullmatch('[0-9]{1,4}',v)for v in args[5:]):return 64
  if args[:3]==['shell','sh','-c'] and len(args)==4 and re.fullmatch(r'if pidof vn\.rtr\.aeris\.mission >/dev/null \|\| kill -0 [1-9][0-9]* 2>/dev/null; then echo RUNNING; else echo ABSENT; fi',args[3]):return 64
  raise ValueError('UNDECLARED_ANDROID_COMMAND_WRITER')
 def intent(self,component,extras,*,deadline_ns):
  if component!='vn.rtr.aeris.mission/.CockpitActivity' or set(extras)!={'missionAction','missionRequestBase64'} or extras['missionAction'] not in ('STATUS','BOOTSTRAP') or not re.fullmatch(r'[A-Za-z0-9_=\-]{1,43692}',extras['missionRequestBase64']):raise ValueError('PUBLIC_INTENT_ALLOWLIST')
  if extras['missionAction']=='STATUS':
   encoded=extras['missionRequestBase64']
   if len(encoded)>684:raise ValueError('PUBLIC_STATUS_REQUEST_BOUND')
   try:
    raw=base64.b64decode(encoded,altchars=b'-_',validate=True)
    if not 0<len(raw)<=512:raise ValueError('PUBLIC_STATUS_REQUEST_BOUND')
    if base64.urlsafe_b64encode(raw).decode('ascii')!=encoded:raise ValueError('PUBLIC_STATUS_CANONICAL_BASE64URL')
    def unique_pairs(items):
     result={}
     for key,value in items:
      if key in result:raise ValueError('PUBLIC_STATUS_DUPLICATE_KEY')
      result[key]=value
     return result
    request=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_pairs)
    if type(request)is not dict or set(request)!={'version','requestNonce'}or type(request.get('version'))is not int or request['version']!=1 or type(request.get('requestNonce'))is not str or re.fullmatch('[a-f0-9]{32}',request['requestNonce'])is None:raise ValueError('PUBLIC_STATUS_REQUEST_SCHEMA')
   except (ValueError,UnicodeError)as error:raise ValueError('PUBLIC_STATUS_REQUEST_SCHEMA_OR_ENCODING')from error
   return self.command(['shell','am','broadcast','-n','vn.rtr.aeris.mission/.CockpitActivity$StatusReceiver','-a','vn.rtr.aeris.mission.STATUS','--es','missionAction','STATUS','--es','missionRequestBase64',encoded],deadline_ns=deadline_ns)
  return self.command(['shell','am','start','-n',component,'--es','missionAction',extras['missionAction'],'--es','missionRequestBase64',extras['missionRequestBase64']],deadline_ns=deadline_ns)
 def pid(self,package,*,deadline_ns):
  if package!=self.APPLICATION_PACKAGE:raise ValueError('PACKAGE_ALLOWLIST')
  raw=self.command(['shell','pidof',package],deadline_ns=deadline_ns).decode().strip()
  if re.fullmatch('[1-9][0-9]*',raw)is None:raise ValueError('EXACT_ACTUAL_PROCESS_REQUIRED')
  return int(raw)
 def read_private(self,package,path,*,maximum_bytes,deadline_ns):
  if package!='vn.rtr.aeris.mission' or path not in ('files/runtime/response.json','files/runtime/current.json') or maximum_bytes!=131072:raise ValueError('COHERENT_READ_ONLY_ALLOWLIST')
  raw=self.command(['shell','run-as',package,'cat',path],deadline_ns=deadline_ns,maximum_bytes=16384);self.last_snapshot_ref=self.last_command['stdoutRef'];return raw
 @contextlib.contextmanager
 def live_log(self,tag,*,deadline_ns):
  if self.observer is None or tag!=self.observer.tag:raise ValueError('LIVE_LOG_TAG_AND_EXPLICIT_BUDGET')
  if not self.observer.busy.acquire(blocking=False):raise ValueError('ONE_ACK_REQUEST_AT_A_TIME')
  try:
   self.last_barrier_ref=self.observer.barrier(deadline_ns);self.last_barrier_ns=self.now()
   yield self.observer.rows_until(deadline_ns)
  except BaseException as primary:
   try:self.budget.failure(primary)
   except BaseException as closure:primary.add_note('UNDURABLE_FAILURE_DIAGNOSTIC:'+str(closure))
   try:self.observer.close()
   except BaseException as closure:primary.add_note('ACK_CLOSE_SECONDARY:'+str(closure))
   raise
  finally:self.observer.busy.release()
 def wait_owned_ready(self,*,deadline_ns):
  """One transport wait, finite boot observation, one PM probe. No failed retry."""
  if self.serial!='emulator-5582'or self.observer.tag!='AERIS_PRODUCT_STATUS'or self.observer.process is not None or self._android_ready is not None or self.sequence:raise ValueError('OWNED_ANDROID_READINESS_FIRST_ONCE')
  started=self.now();end=min(deadline_ns,started+60_000_000_000)
  self.command(['wait-for-device'],deadline_ns=end,maximum_bytes=2048);transport=self.last_command_ref
  output=self.command(['shell','sh','-c',ANDROID_READY_SCRIPT],deadline_ns=end,maximum_bytes=2048);boot=self.last_command_ref
  lines=output.splitlines();pm=[v for v in lines if v.startswith(b'PM:')]
  if self.now()>=end or not 3<=len(lines)<=122 or lines[-1]!=b'ANDROID_READY'or len(pm)!=1 or pm[0]!=lines[-2]or re.fullmatch(rb'PM:package:/[A-Za-z0-9_./+-]+',pm[0])is None or lines[-3]!=b'BOOT:1'or any(v not in(b'BOOT:',b'BOOT:0',b'BOOT:1')for v in lines[:-2])or any(v==b'BOOT:1'for v in lines[:-3]):raise ValueError('ORIGINAL_ANDROID_BOOT_AND_PM_READINESS_REQUIRED')
  value={'format':'aeris-owned-android-ready','version':1,'serial':self.serial,'startedHostNs':started,'finishedHostNs':self.now(),'deadlineHostNs':end,'transportCommandRef':transport,'bootAndPackageManagerCommandRef':boot,'readinessScriptSHA256':hashlib.sha256(ANDROID_READY_SCRIPT.encode()).hexdigest(),'packageManagerPath':pm[0][3:].decode(),'bootObservations':len(lines)-2,'APKInstalled':False,'APStarted':False,'flightAcceptance':False}
  self._android_ready=self.store.receipt('product-android-ready.json',value);return self._android_ready
 def _content_reader_capture(self,ref,args,*,deadline_ns,expected_exit=0,expected_failure=None):
  """Verify originaldurable command bytes, not in-memorysummary or stderrhint."""
  from .once_reader import read_ref,read_receipts,unique
  if type(ref)is not dict or ref.get('version')!=3 or ref.get('path')!='receipts/command.jsonl':raise ValueError('CONTENT_READER_ORIGINAL_COMMAND_REF')
  raw=read_ref(self.store.root,ref);row=json.loads(raw,object_pairs_hook=unique)
  fields={'format','version','sequence','argvRef','startedHostNs','endedHostNs','exit','stdoutRef','stderrRef','captureComplete','failure'}
  if type(row)is not dict or set(row)!=fields or row['format']!='aeris-command'or type(row['version'])is not int or row['version']!=3 or any(type(row[k])is not int for k in('sequence','startedHostNs','endedHostNs','exit'))or row['sequence']!=self.sequence or row['captureComplete']is not True or row['exit']!=expected_exit or row['failure']!=expected_failure or not 0<=row['startedHostNs']<=row['endedHostNs']<deadline_ns:raise ValueError('CONTENT_READER_ORIGINAL_COMMAND_SCHEMA')
  commands=read_receipts(self.store.root,'command')
  if len(commands)!=self.sequence or commands[-1]!=row or any(type(v.get('sequence'))is not int or v['sequence']!=i for i,v in enumerate(commands,1)):raise ValueError('CONTENT_READER_ORIGINAL_COMMAND_MEMBERSHIP')
  expected=[self.adb,'-s',self.serial,*(['shell',shlex.join(args[1:])]if args and args[0]=='shell'else args)]
  if any(type(row[k])is not dict or row[k].get('version')!=3 for k in('argvRef','stdoutRef','stderrRef'))or read_ref(self.store.root,row['argvRef'])!=canonical(expected):raise ValueError('CONTENT_READER_EXACT_ADB_SERIAL_ARGV')
  out=read_ref(self.store.root,row['stdoutRef']);err=read_ref(self.store.root,row['stderrRef'])
  if self.now()>=deadline_ns:raise TimeoutError('CONTENT_READER_SAME30S_DEADLINE')
  return row,out,err
 def prepare_content_reader(self,*,deadline_ns):
  if self.serial!='emulator-5582'or self.observer.tag!='AERIS_PRODUCT_STATUS'or self.observer.process is not None:raise ValueError('ROOT_ONLY_OWNED_PRODUCT_EMULATOR_BEFORE_OBSERVER')
  if self._android_ready is None:raise ValueError('GENUINE_ANDROID_READY_BEFORE_CONTENT_PREPARATION')
  if getattr(self,'_content_reader_preparation_attempted',False):raise ValueError('CONTENT_READER_NO_RETRY_AFTER_ATTEMPT')
  started=self.now()
  if type(deadline_ns)is not int:raise ValueError('CONTENT_READER_TYPED_DEADLINE')
  end=min(deadline_ns,started+30_000_000_000)
  if started>=end:raise TimeoutError('CONTENT_READER_SAME30S_DEADLINE')
  self._content_reader_preparation_attempted=True
  boot_args=['shell','cat','/proc/sys/kernel/random/boot_id'];boot=self.command(boot_args,deadline_ns=end,maximum_bytes=2048);boot_before_ref=self.last_command_ref
  boot_row,boot_original,boot_err=self._content_reader_capture(boot_before_ref,boot_args,deadline_ns=end)
  if boot!=boot_original or boot_err or re.fullmatch(rb'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\n',boot)is None:raise ValueError('CONTENT_READER_ORIGINAL_KERNEL_BOOT_UUID')
  before=self.command(['shell','id','-u'],deadline_ns=end,maximum_bytes=2048);before_ref=self.last_command_ref
  before_row,before_original,before_err=self._content_reader_capture(before_ref,['shell','id','-u'],deadline_ns=end)
  if before!=before_original or before_err or before not in(b'0\n',b'2000\n')or before_row['startedHostNs']<boot_row['endedHostNs']:raise ValueError('CONTENT_READER_ORIGINAL_BEFORE_UID')
  root_ref=wait_ref=None;root_outcome='NOT_REQUESTED_UID_ALREADY0';root_command_failed=False
  if before!=b'0\n':
   try:
    self.command(['root'],deadline_ns=end,maximum_bytes=2048);root_ref=self.last_command_ref
   except RuntimeError as original:
    if type(original)is not RuntimeError or str(original)!='ANDROID_COMMAND_EXIT:1'or getattr(original,'__notes__',())or original.__cause__ is not None:raise
    root_ref=self.last_command_ref
    try:
     root_row,root_out,root_err=self._content_reader_capture(root_ref,['root'],deadline_ns=end,expected_exit=1,expected_failure='RuntimeError:ANDROID_COMMAND_EXIT:1')
     if root_out!=b''or root_err!=b'adb: unable to connect for root: closed\n'or root_row['sequence']!=before_row['sequence']+1 or root_row['startedHostNs']<before_row['endedHostNs']:raise ValueError('CONTENT_READER_EXACT_UNCERTAIN_ROOT_DISPATCH')
    except BaseException as verification:
     original.add_note('ROOT_FAILURE_RECEIPT_NOT_VERIFIED:'+type(verification).__name__+':'+str(verification)[:160]);raise original from verification
    root_command_failed=True;root_outcome='COMMAND_FAILED_DISPATCH_UNKNOWN_CLOSED_TRANSPORT'
   else:
    root_row,root_out,root_err=self._content_reader_capture(root_ref,['root'],deadline_ns=end)
    if root_err or root_row['sequence']!=before_row['sequence']+1 or root_row['startedHostNs']<before_row['endedHostNs']:raise ValueError('CONTENT_READER_ORIGINAL_ROOT_COMMAND')
    root_outcome='COMMAND_EXIT0_OBSERVED_NOT_UID_PROOF'
   # Neverresend root after uncertain dispatch. These are readonly confirmations
   # within the SAME30sdeadline, not a retry or an extension of any guard.
   self.command(['wait-for-device'],deadline_ns=end,maximum_bytes=2048);wait_ref=self.last_command_ref
   wait_row,wait_out,wait_err=self._content_reader_capture(wait_ref,['wait-for-device'],deadline_ns=end)
   if wait_out or wait_err or wait_row['startedHostNs']<root_row['endedHostNs']:raise ValueError('CONTENT_READER_ORIGINAL_READONLY_WAIT')
  after=self.command(['shell','id','-u'],deadline_ns=end,maximum_bytes=2048);after_ref=self.last_command_ref
  after_row,after_original,after_err=self._content_reader_capture(after_ref,['shell','id','-u'],deadline_ns=end)
  prior_row=wait_row if wait_ref is not None else before_row
  if after!=after_original or after!=b'0\n'or after_err or after_row['sequence']!=prior_row['sequence']+1 or after_row['startedHostNs']<prior_row['endedHostNs']:raise ValueError('ACTUAL_EMULATOR_ROOT_UID_REQUIRED')
  after_boot=self.command(boot_args,deadline_ns=end,maximum_bytes=2048);boot_after_ref=self.last_command_ref
  boot_after_row,after_boot_original,after_boot_err=self._content_reader_capture(boot_after_ref,boot_args,deadline_ns=end)
  if after_boot!=after_boot_original or after_boot_err or after_boot!=boot or boot_after_row['startedHostNs']<after_row['endedHostNs']:raise ValueError('CONTENT_READER_SAME_KERNEL_BOOT_REQUIRED')
  if self.now()>=end:raise TimeoutError('CONTENT_READER_SAME30S_DEADLINE')
  value={'format':'aeris-owned-emulator-content-reader-preparation','version':2,'serial':self.serial,'beforeRef':before_ref,'rootRef':root_ref,'afterRef':after_ref,'waitRef':wait_ref,'bootBeforeRef':boot_before_ref,'bootAfterRef':boot_after_ref,'kernelBootUUID':boot.decode('ascii').strip(),'rootCommandOutcome':root_outcome,'originalRootCommandFailed':root_command_failed,'originalRootCommandAcceptedAsSuccess':False,'confirmation':'READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','startedHostNs':started,'finishedHostNs':self.now(),'deadlineHostNs':end,'actualUID0':True,'noPhysicalDevice':True,'rootResent':False}
  preparation_ref=self.store.receipt('product-content-reader-preparation.json',value)
  if self.now()>=end:raise TimeoutError('CONTENT_READER_PREPARATION_DURABILITY_DEADLINE')
  self.content_reader_preparation=preparation_ref;return preparation_ref
 def open_saf_document(self,cap,*,deadline_ns,check=lambda:None):
  if not getattr(self,'content_reader_preparation',None):raise ValueError('SOURCE_ACTUAL_ROOT_PREPARATION_REQUIRED')
  from .saf_stream import open_document
  return open_document(self,cap,deadline_ns=deadline_ns,check=check)
 def close_observer(self):
  closed=self.close_status_socket(deadline_ns=self.now()+5_000_000_000)
  if closed is not None and closed.get('receipt',{}).get('drainComplete')is not True:raise RuntimeError('STATUS15_SOCKET_DRAIN_BEFORE_ACK_CLOSE')
  if self.observer is not None:return self.observer.close()
 def export_private(self,run,target,*,deadline_ns,metadata_only=False,maximum_bytes=168*2**20):
  self._check_budget_actor()
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):return self._export_private(run,target,deadline_ns=deadline_ns,metadata_only=metadata_only,maximum_bytes=maximum_bytes)
 def _export_private(self,run,target,*,deadline_ns,metadata_only=False,maximum_bytes=168*2**20,full_original=False,product_full_closed=False,native17_stage=None):
  if re.fullmatch('[A-Za-z0-9_-]{1,64}',run)is None:raise ValueError('EXPORT_RUN')
  target=Path(target);paths=['files/checkpoint14','files/latest-state.json','files/workspace03','files/review-links','files/runtime']
  if self.include_quarantine:paths.append('files/recovery08')
  if full_original or product_full_closed:paths=['files']
  elif not metadata_only:paths.insert(0,'files/control-runs/'+run)
  if type(maximum_bytes)is not int or not 0<maximum_bytes<=(64*2**20 if metadata_only else 168*2**20):raise ValueError('EXPORT_ORIGINAL_CAP')
  expected='native-original-before-quarantine.tar'if full_original else('native-restart-metadata.tar'if metadata_only else'native-closed.tar')
  if product_full_closed:expected='native-restart-metadata.tar'if metadata_only and self.APPLICATION_PACKAGE=='vn.rtr.aeris.betasim09'else'native-closed.tar'
  if native17_stage is not None:
   from .native17 import NATIVE17_EXPORTS
   if self.__class__.__name__!='AndroidDomain17' or native17_stage not in NATIVE17_EXPORTS or target.name!=NATIVE17_EXPORTS[native17_stage]or not product_full_closed or full_original:raise ValueError('NATIVE17_FIXED_STAGE_EXPORT')
   expected=NATIVE17_EXPORTS[native17_stage]
  if target.name!=expected or target.parent.resolve()!=self.root.parent.resolve() or any(p.is_symlink()for p in [target,*target.parents]):raise ValueError('EXACT_ORIGINAL_EXPORT_DOMAIN')
  prior=sum(p.stat().st_size for p in target.parent.glob('native-*.tar')if p.is_file());maximum_bytes=min(maximum_bytes,192*2**20-prior)
  if maximum_bytes<=0:raise ValueError('EXPORT_ORIGINAL192MiB_AGGREGATE')
  self.budget.ensure('commands',16385+8192);self.budget.reserve_export(target,maximum_bytes);argv=[self.adb,'-s',self.serial,'exec-out','run-as',self.APPLICATION_PACKAGE,'tar','-cf','-',*paths];argv_ref=self.store.command_bytes(canonical(argv));started=self.now();p=None;sel=selectors.DefaultSelector();count=0;seen=0;stderr=bytearray();failure=None;complete=False;result=None;file=None;cleanup_errors=[];retained=0
  try:
   file=target.open('xb');p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   for name,stream in [('stdout',p.stdout),('stderr',p.stderr)]:os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
   while sel.get_map():
    if self.now()>deadline_ns:raise TimeoutError('NATIVE_EXPORT_DEADLINE')
    for key,_ in sel.select(.05):
     name=key.data;limit=min(65536,maximum_bytes+1-seen)if name=='stdout'else min(65536,16385-len(stderr));raw=os.read(key.fileobj.fileno(),limit)
     if not raw:sel.unregister(key.fileobj);continue
     if name=='stderr':
      stderr.extend(raw)
      if len(stderr)>16384:raise ValueError('NATIVE_EXPORT_STDERR16KiB_PREFIX_INCOMPLETE')
     else:
      accepted=raw[:max(0,maximum_bytes-count)]
      if accepted:
       wrote=file.write(accepted)
       if wrote!=len(accepted):raise OSError('NATIVE_EXPORT_SHORT_WRITE')
       count+=wrote
      seen+=len(raw)
      if seen>maximum_bytes:raise RuntimeError('NATIVE_EXPORT_CAP_PREFIX_INCOMPLETE')
   code=p.wait(timeout=max(.01,(deadline_ns-self.now())/1e9))
   if code:raise RuntimeError('NATIVE_EXPORT_FAILED:'+str(code))
   file.flush();os.fsync(file.fileno());complete=True
   from .candidate import sha
   result={'path':str(target),'sha256':sha(target),'bytes':count,'startedHostNs':started,'finishedHostNs':self.now(),'argv':argv,'exit':code,'selectedRun':run,'readOnlyExport':True,'captureComplete':True}
  except BaseException as primary:failure=primary
  finally:
   operations=[]
   if p is not None:operations.append(('export-process-stop',lambda:_stop_capture_process(p)))
   operations.append(('export-selector-close',sel.close))
   if p is not None:operations.extend([('export-stdout-close',p.stdout.close),('export-stderr-close',p.stderr.close)])
   if file is not None:operations.extend([('export-file-flush',file.flush),('export-file-fsync',lambda:os.fsync(file.fileno())),('export-file-close',file.close)])
   failure=_capture_cleanup(failure,operations,cleanup_errors)
   if cleanup_errors:complete=False
   reservation_retained=file is None or bool(cleanup_errors)
   try:
    if file is not None:retained=target.stat().st_size
    if file is not None and not cleanup_errors:self.budget.finish_export(target)
    err_ref=self.store.command_bytes(stderr);receipt={'format':'aeris-native-export','version':1,'argvRef':argv_ref,'fullOriginalFiles':full_original or product_full_closed,'path':str(target),'bytesRetained':retained,'bytesAcceptedByWriter':count,'bytesObservedLowerBound':seen,'stderrRef':err_ref,'startedHostNs':started,'finishedHostNs':self.now(),'exit':None if p is None else p.poll(),'captureComplete':complete and failure is None,'failure':None if failure is None else type(failure).__name__+':'+str(failure)[:512],'cleanupErrors':cleanup_errors,'exportReservationRetained':reservation_retained,'flightAcceptance':False}
    ref=self.store.receipt('export-metadata.json'if metadata_only else'export-full.json',receipt,closing=failure is not None)
    if result is not None:result.update(stderrRef=err_ref,captureReceiptRef=ref,captureComplete=complete and failure is None)
   except BaseException as secondary:
    if failure is None:failure=secondary
    else:failure.add_note('EXPORT_PERSISTENCE_SECONDARY:'+str(secondary)[:256])
  if failure is not None:raise failure
  return result
 def _cold_absence(self,deadline_ns):
  raw=self.command(['shell','sh','-c',self.COLD_ABSENCE_PREDICATE],deadline_ns=deadline_ns)
  if raw!=b'ABSENT\n':raise RuntimeError('ORIGINAL_APP_MUST_BE_COLD_PID0')
  return self.last_command_ref
 def _installed_sha(self,expected,deadline_ns):
  raw=self.command(['shell','pm','path',self.APPLICATION_PACKAGE],deadline_ns=deadline_ns).decode().strip();path_ref=self.last_command_ref
  if not raw.startswith('package:/')or'\n'in raw:raise ValueError('ONE_INSTALLED_PACKAGE_FOR_PRESERVATION')
  digest=self.command(['shell','sha256sum',raw[8:]],deadline_ns=deadline_ns).decode().split()[0];sha_ref=self.last_command_ref
  if digest!=expected:raise ValueError('COLD_INSTALLED_APK_EXPECTATION')
  return path_ref,sha_ref
 def cold_original_backup(self,run,target,*,deadline_ns):
  self._check_budget_actor()
  if self.observer.process is not None:raise ValueError('COLD_BACKUP_BEFORE_ANY_ACK_OBSERVER')
  before=self._cold_absence(deadline_ns);path_ref,sha_ref=self._installed_sha(ORIGINAL_APK_SHA,deadline_ns)
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):export=self._export_private(run,target,deadline_ns=deadline_ns,full_original=True)
  after=self._cold_absence(deadline_ns);table=verify_full_files_tar(export['path'],export['sha256'],export['bytes'])
  proof={'format':'aeris-cold-original-app-backup','version':1,'package':'vn.rtr.aeris.mission','oldAPKSHA256':ORIGINAL_APK_SHA,'serial':self.serial,'exportPath':str(Path(target).absolute()),'exportBytes':export['bytes'],'exportSHA256':export['sha256'],'exportCaptureReceiptRef':export['captureReceiptRef'],'coldBeforeCommandRef':before,'installedPathCommandRef':path_ref,'installedSHACommandRef':sha_ref,'coldAfterCommandRef':after,'verifiedHostNs':self.now(),**table}
  ref=self.store.receipt('cold-original-backup.json',proof);verified=verify_cold_original_backup(self.store.root,ref);return {'backupReceiptRef':ref,**verified}
 def install_development(self,candidate_dir,candidate_sha,backup_receipt_ref,*,deadline_ns):
  self._check_budget_actor()
  if self.observer.process is not None:raise ValueError('INSTALL_BEFORE_ANY_ACK_OBSERVER')
  backup=verify_cold_original_backup(self.store.root,backup_receipt_ref)
  if backup.get('backupVersion')in(2,3):return self._install_predecessor_development(candidate_dir,candidate_sha,backup_receipt_ref,backup,deadline_ns=deadline_ns)
  if backup['serial']!=self.serial:raise ValueError('COLD_ORIGINAL_SAME_OWNED_DEVICE')
  from .candidate import load,sha
  candidate=Path(candidate_dir).resolve();manifest=load(candidate,candidate_sha);apk=candidate/'native.apk';build=json.loads((candidate/'native-build-receipt.json').read_bytes());native=manifest['native']
  if build.get('sourceCount')!=51 or build.get('productionSigning')is not False or build.get('certificateSHA256')!=DEVELOPMENT_CERT_SHA or sha(apk)!=build.get('sha256')or native.get('APK_SHA256')!=sha(apk):raise ValueError('FIXED51_DEVELOPMENT_INSTALL_CANDIDATE')
  before=self._cold_absence(deadline_ns);path_ref,sha_ref=self._installed_sha(ORIGINAL_APK_SHA,deadline_ns)
  auth={'format':'aeris-recovery08-development-install-authorization','version':1,'candidateDir':str(candidate),'candidateSHA256':candidate_sha,'APKPath':str(apk),'APKSHA256':sha(apk),'nativeSourceSHA256':native['sourceSHA256'],'certificateSHA256':DEVELOPMENT_CERT_SHA,'expectedOldAPKSHA256':ORIGINAL_APK_SHA,'originalBackupReceiptRef':backup_receipt_ref,'package':'vn.rtr.aeris.mission','preparedHostNs':self.now(),'coldBeforeCommandRef':before,'installedPathCommandRef':path_ref,'installedSHACommandRef':sha_ref}
  ref=self.store.receipt('development-install-authorization.json',auth);self._install_authorization={'ref':ref,'APKPath':str(apk)}
  try:
   output=self.command(['install','-r',str(apk)],deadline_ns=deadline_ns);install_ref=self.last_command_ref
   if not output.splitlines()or output.splitlines()[-1]!=b'Success':raise RuntimeError('DEVELOPMENT_INSTALL_NO_EXACT_SUCCESS')
  finally:self._install_authorization=None
  new_path,new_sha=self._installed_sha(sha(apk),deadline_ns);after=self._cold_absence(deadline_ns)
  result={'format':'aeris-recovery08-development-install','version':1,'authorizationRef':ref,'installCommandRef':install_ref,'installedPathCommandRef':new_path,'installedSHACommandRef':new_sha,'coldAfterCommandRef':after,'oldOriginalBackupReceiptRef':backup_receipt_ref,'newAPKSHA256':sha(apk),'noClearOrWipe':True,'ACKObserverStarted':False,'flightAcceptance':False};result_ref=self.store.receipt('development-install-result.json',result);return {**result,'receiptRef':result_ref}
 def cold_predecessor_backup(self,run,target,*,deadline_ns):
  """Only the immutable selected R10 predecessor; no caller expected-hash seam."""
  self._check_budget_actor();predecessor=predecessor_candidate_proof()
  if self.observer.process is not None:raise ValueError('COLD_BACKUP_BEFORE_ANY_ACK_OBSERVER')
  before=self._cold_absence(deadline_ns);path_ref,sha_ref=self._installed_sha(predecessor['APKSHA256'],deadline_ns)
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):export=self._export_private(run,target,deadline_ns=deadline_ns,full_original=True)
  after_path,after_sha=self._installed_sha(predecessor['APKSHA256'],deadline_ns);after=self._cold_absence(deadline_ns);table=verify_full_files_tar(export['path'],export['sha256'],export['bytes']);retained=verify_predecessor_retained_files(export['path'])
  proof={'format':'aeris-cold-original-app-backup','version':2,'package':'vn.rtr.aeris.mission','oldAPKSHA256':predecessor['APKSHA256'],'predecessor':predecessor,'installedAfterPathCommandRef':after_path,'installedAfterSHACommandRef':after_sha,'serial':self.serial,'exportPath':str(Path(target).absolute()),'exportBytes':export['bytes'],'exportSHA256':export['sha256'],'exportCaptureReceiptRef':export['captureReceiptRef'],'coldBeforeCommandRef':before,'installedPathCommandRef':path_ref,'installedSHACommandRef':sha_ref,'coldAfterCommandRef':after,'verifiedHostNs':self.now(),**table,**retained}
  ref=self.store.receipt('cold-predecessor-backup.json',proof);verified=verify_cold_original_backup(self.store.root,ref);return {'backupReceiptRef':ref,**verified}
 def cold_transport14_backup(self,run,target,*,deadline_ns):
  """Only the immutable selected e552/eb83 predecessor; no caller hash seam."""
  self._check_budget_actor()
  from .predecessor15 import proof as current_predecessor
  predecessor=current_predecessor()
  if self.observer.process is not None:raise ValueError('COLD_BACKUP_BEFORE_ANY_ACK_OBSERVER')
  before=self._cold_absence(deadline_ns);path_ref,sha_ref=self._installed_sha(predecessor['APKSHA256'],deadline_ns)
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):export=self._export_private(run,target,deadline_ns=deadline_ns,full_original=True)
  after_path,after_sha=self._installed_sha(predecessor['APKSHA256'],deadline_ns);after=self._cold_absence(deadline_ns);table=verify_full_files_tar(export['path'],export['sha256'],export['bytes']);retained=verify_predecessor_retained_files(export['path'])
  proof={'format':'aeris-cold-original-app-backup','version':3,'package':'vn.rtr.aeris.mission','oldAPKSHA256':predecessor['APKSHA256'],'predecessor':predecessor,'installedAfterPathCommandRef':after_path,'installedAfterSHACommandRef':after_sha,'serial':self.serial,'exportPath':str(Path(target).absolute()),'exportBytes':export['bytes'],'exportSHA256':export['sha256'],'exportCaptureReceiptRef':export['captureReceiptRef'],'coldBeforeCommandRef':before,'installedPathCommandRef':path_ref,'installedSHACommandRef':sha_ref,'coldAfterCommandRef':after,'verifiedHostNs':self.now(),**table,**retained}
  ref=self.store.receipt('cold-predecessor-backup.json',proof);verified=verify_cold_original_backup(self.store.root,ref);return {'backupReceiptRef':ref,**verified}
 def _install_predecessor_development(self,candidate_dir,candidate_sha,backup_ref,backup,*,deadline_ns):
  from .candidate import load,sha
  version=backup.get('backupVersion')
  if version==3:
   from .predecessor15 import proof as current_predecessor
   predecessor=current_predecessor()
  else:predecessor=predecessor_candidate_proof()
  if backup['serial']!=self.serial or backup['predecessor']!=predecessor:raise ValueError('PREDECESSOR_BACKUP_EXACT_DEVICE_SOURCE')
  candidate=Path(candidate_dir).resolve();manifest=load(candidate,candidate_sha);apk=candidate/'native.apk';native=manifest['native'];build=json.loads((candidate/'native-build-receipt.json').read_bytes())
  if build.get('sourceCount')!=51 or build.get('productionSigning')is not False or build.get('certificateSHA256')!=DEVELOPMENT_CERT_SHA or sha(apk)!=build.get('sha256')or native.get('APK_SHA256')!=sha(apk)or native.get('sourceSHA256')==predecessor['nativeSourceSHA256']or sha(apk)==predecessor['APKSHA256']:raise ValueError('FIXED51_NEW_SOURCE_DEVELOPMENT_UPGRADE')
  before=self._cold_absence(deadline_ns);path_ref,sha_ref=self._installed_sha(predecessor['APKSHA256'],deadline_ns)
  auth={'format':'aeris-recovery08-development-install-authorization','version':version,'candidateDir':str(candidate),'candidateSHA256':candidate_sha,'APKPath':str(apk),'APKSHA256':sha(apk),'nativeSourceSHA256':native['sourceSHA256'],'certificateSHA256':DEVELOPMENT_CERT_SHA,'expectedOldAPKSHA256':predecessor['APKSHA256'],'predecessor':predecessor,'originalBackupReceiptRef':backup_ref,'package':'vn.rtr.aeris.mission','preparedHostNs':self.now(),'coldBeforeCommandRef':before,'installedPathCommandRef':path_ref,'installedSHACommandRef':sha_ref}
  ref=self.store.receipt('development-install-authorization.json',auth);self._install_authorization={'ref':ref,'APKPath':str(apk),'commandVersion':8 if version==3 else 6}
  try:
   output=self.command(['install','-r',str(apk)],deadline_ns=deadline_ns);install_ref=self.last_command_ref
   if not output.splitlines()or output.splitlines()[-1]!=b'Success':raise RuntimeError('DEVELOPMENT_INSTALL_NO_EXACT_SUCCESS')
  finally:self._install_authorization=None
  new_path,new_sha=self._installed_sha(sha(apk),deadline_ns);after=self._cold_absence(deadline_ns)
  result={'format':'aeris-recovery08-development-install','version':version,'authorizationRef':ref,'installCommandRef':install_ref,'installedPathCommandRef':new_path,'installedSHACommandRef':new_sha,'coldAfterCommandRef':after,'oldOriginalBackupReceiptRef':backup_ref,'newAPKSHA256':sha(apk),'noClearOrWipe':True,'ACKObserverStarted':False,'flightAcceptance':False};result_ref=self.store.receipt('development-install-result.json',result);return {**result,'receiptRef':result_ref}
 def prepare_normal(self,expected_apk_sha,*,deadline_ns):
  """Fresh cold/warm resources only. Public native READY remains mandatory."""
  import xml.etree.ElementTree as ET
  started=self.now();first_sequence=self.sequence+1;package='vn.rtr.aeris.mission';prior_pid=getattr(self,'_native_resource_prepared_pid',None)
  raw=self.command(['shell','pm','path',package],deadline_ns=deadline_ns).decode().strip();prepared_path_ref=self.last_command_ref
  if not raw.startswith('package:/') or '\n' in raw:raise ValueError('ONE_INSTALLED_DEVELOPMENT_PACKAGE')
  actual=self.command(['shell','sha256sum',raw[8:]],deadline_ns=deadline_ns).decode().split()[0];prepared_sha_ref=self.last_command_ref
  if actual!=expected_apk_sha:raise ValueError('ACTUAL_INSTALLED_APK_SHA')
  availability=self.command(['shell','sh','-c',COLD_ABSENCE_SCRIPT],deadline_ns=deadline_ns)
  if availability not in(b'ABSENT\n',b'RUNNING\n'):raise ValueError('NATIVE_PREPARATION_EXACT_PROCESS_AVAILABILITY')
  cold=availability==b'ABSENT\n';pid=None
  if cold:
   if prior_pid is not None:raise RuntimeError('PREPARED_PROCESS_ABSENT_REQUIRES_NEW_DEVICE_LIFECYCLE')
   self.command(['shell','am','start','-n',package+'/.CockpitActivity'],deadline_ns=deadline_ns)
  else:
   pid=self.pid(package,deadline_ns=deadline_ns)
   if prior_pid is not None and pid!=prior_pid:raise RuntimeError('PREPARED_PROCESS_CHANGED_REQUIRES_NEW_DEVICE_LIFECYCLE')
  component=r'(?<![A-Za-z0-9_.])vn\.rtr\.aeris\.mission/(?:\.CockpitActivity|vn\.rtr\.aeris\.mission\.CockpitActivity)(?=[\s}])'
  while self.now()<=deadline_ns:
   if pid is None:
    probe=self.command(['shell','sh','-c',COLD_ABSENCE_SCRIPT],deadline_ns=deadline_ns)
    if probe==b'ABSENT\n':time.sleep(.1);continue
    if probe!=b'RUNNING\n':raise ValueError('NATIVE_PREPARATION_EXACT_PROCESS_AVAILABILITY')
    pid=self.pid(package,deadline_ns=deadline_ns)
   before=self.pid(package,deadline_ns=deadline_ns)
   if before!=pid:raise RuntimeError('NATIVE_PREPARATION_PID_CHANGED')
   xml=self.command(['exec-out','uiautomator','dump','/dev/tty'],deadline_ns=deadline_ns).decode();start=xml.find('<?xml');end=xml.rfind('</hierarchy>')
   activity=self.command(['shell','dumpsys','activity','activities'],deadline_ns=deadline_ns,maximum_bytes=131072).decode()
   focused=any(re.search(component,line)and('mResumedActivity'in line or'topResumedActivity'in line)for line in activity.splitlines())
   after=self.pid(package,deadline_ns=deadline_ns)
   if after!=pid:raise RuntimeError('NATIVE_PREPARATION_PID_CHANGED')
   if not cold and not focused:raise RuntimeError('WARM_NATIVE_ACTIVITY_NOT_FOREGROUND_NO_RELAUNCH')
   if start>=0 and end>=start:
    tree=ET.fromstring(xml[start:end+12]);nodes=list(tree.iter('node'));web=any(n.get('class')=='android.webkit.WebView'and n.get('package')==package for n in nodes);controls=any(n.get('package')==package and(n.get('content-desc')in('AERIS khảo sát và huấn luyện SITL','Real-time Robotics AERIS')or n.get('text')=='Khảo sát')for n in nodes)
    if focused and web and controls:
     if self.now()>deadline_ns:raise TimeoutError('NATIVE_RESOURCE_PREPARATION60S')
     self._native_resource_prepared_pid=pid;self._native_prepared_apk_refs=(prepared_path_ref,prepared_sha_ref,actual)
     return {'status':'NATIVE_RESOURCES_PREPARED_NOT_PROTOCOL_READY','preparationMode':'COLD_ABSENT_PLAIN_LAUNCH'if cold else'WARM_FOREGROUND_NO_LAUNCH','startedHostNs':started,'observedHostNs':self.now(),'installedAPKSHA256':actual,'actualPID':pid,'PIDStableAcrossFreshUIProbe':True,'launchDispatched':cold,'cachedReadinessUsed':False,'plainLaunchNoMissionExtras':True,'focusedVisibleUIObserved':True,'protocolREADYClaimed':False,'originalCommandSequenceRange':[first_sequence,self.sequence]}
   time.sleep(.1)
  raise TimeoutError('NATIVE_RESOURCE_PREPARATION60S')

 def restart_normal(self,expected_apk_sha,*,old_pid,deadline_ns):
  if type(old_pid)is not int or old_pid<=0:raise ValueError('ORIGINAL_OLD_PID_REQUIRED')
  started=self.now();self.command(['shell','am','force-stop','vn.rtr.aeris.mission'],deadline_ns=deadline_ns);stop_ref=self.last_command_ref
  predicate='if pidof vn.rtr.aeris.mission >/dev/null || kill -0 '+str(old_pid)+' 2>/dev/null; then echo RUNNING; else echo ABSENT; fi'
  gone=self.command(['shell','sh','-c',predicate],deadline_ns=deadline_ns).decode().strip();absence=self.last_command_ref
  if gone!='ABSENT':raise RuntimeError('RESTART_OLD_PROCESS_NOT_GONE')
  proof={'oldPID':old_pid,'oldPIDAbsent':True,'absenceReceiptRef':absence,'stopReceiptRef':stop_ref,'startedHostNs':started,'absentObservedHostNs':self.now(),'forceStopNeverUsedAsGround':True}
  try:proof['newPreparation']=self.prepare_normal(expected_apk_sha,deadline_ns=deadline_ns)
  except BaseException as primary:
   self.store.receipt('restart-operation-failed.json',{'proof':proof,'failure':type(primary).__name__+':'+str(primary)[:512],'flightAcceptance':False},closing=True);raise
  return proof

ORIGINAL_APK_SHA='47208ec07a0c5bc5e70ea28fee87bcbc3267e44c039a75c5e9d95cfd96b4a189'
DEVELOPMENT_CERT_SHA='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
COLD_ABSENCE_SCRIPT='if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi'
QUARANTINE_TOPS=('checkpoint14','latest-state.json','review-links','workspace03')
def verify_full_files_tar(path,expected_sha,expected_bytes):
 path=Path(path).absolute()
 if path.name!='native-original-before-quarantine.tar'or any(p.is_symlink()for p in[path,*path.parents])or type(expected_bytes)is not int or not 0<expected_bytes<=168*2**20 or path.stat().st_size!=expected_bytes:raise ValueError('ORIGINAL_BACKUP_EXACT_EXPORT_PATH_SIZE')
 digest=hashlib.sha256()
 with path.open('rb')as f:
  for raw in iter(lambda:f.read(65536),b''):digest.update(raw)
  f.seek(max(0,expected_bytes-1024));tail=f.read()
 if digest.hexdigest()!=expected_sha or expected_bytes%512 or tail!=b'\0'*1024:raise ValueError('ORIGINAL_BACKUP_SHA_OR_COMPLETE_TAR_END')
 table=[];targets=[];seen=set();logical=0
 with tarfile.open(path,'r:')as t:
  for count,m in enumerate(t,1):
   name=m.name.rstrip('/')
   if count>2048 or name in seen or not(name=='files'or name.startswith('files/'))or any(x in('','..','.')for x in name.split('/'))or '\\'in name or m.pax_headers or not(m.isfile()or m.isdir())or m.issym()or m.islnk():raise ValueError('ORIGINAL_BACKUP_SAFE_COMPLETE_MEMBER_SET')
   seen.add(name)
   if m.isdir():size=0;sha='-';kind='D'
   else:
    if not 0<=m.size<=168*2**20:raise ValueError('ORIGINAL_BACKUP_MEMBER_BOUND')
    size=m.size;logical+=size
    if logical>168*2**20:raise ValueError('ORIGINAL_BACKUP_LOGICAL_CAP')
    h=hashlib.sha256();f=t.extractfile(m);n=0
    for raw in iter(lambda:f.read(65536),b''):n+=len(raw);h.update(raw)
    if n!=size:raise ValueError('ORIGINAL_BACKUP_MEMBER_TRUNCATED')
    sha=h.hexdigest();kind='F'
   rel=name[6:]if name.startswith('files/')else'';row=(name,kind,size,sha);table.append(row)
   if rel and any(rel==top or rel.startswith(top+'/')for top in QUARANTINE_TOPS):targets.append((rel,kind,size,sha))
  eof=t.offset
 with path.open('rb')as f:
  f.seek(eof)
  for raw in iter(lambda:f.read(65536),b''):
   if any(raw):raise ValueError('ORIGINAL_BACKUP_UNPARSED_TRAILING_MEMBER')
 if 'files'not in seen or not targets:raise ValueError('ORIGINAL_BACKUP_FULL_FILES_ROOT_AND_TARGETS')
 def table_digest(rows):return hashlib.sha256(b''.join((kind+'\t'+name+'\t'+str(size)+'\t'+sha+'\n').encode()for name,kind,size,sha in sorted(rows))).hexdigest()
 return {'allOriginalTableSHA256':table_digest(table),'targetTableSHA256':table_digest(targets),'memberCount':len(table),'originalLogicalBytes':logical,'targetEntryCount':len(targets),'targetLogicalBytes':sum(r[2]for r in targets),'fullOriginalFilesPreserved':True,'targetScope':list(QUARANTINE_TOPS),'protocolTransientScope':'runtime bytes INCLUDED in cold original export; only four exact mission-data tops are moved later'}

def verify_cold_original_backup(store_root,backup_receipt_ref):
 from .once_reader import read_ref,unique,read_receipts
 root=Path(store_root).absolute();proof=json.loads(read_ref(root,backup_receipt_ref),object_pairs_hook=unique)
 version=proof.get('version');expected_old=ORIGINAL_APK_SHA
 if type(version)is int and version in(2,3):
  if version==3:
   from .predecessor15 import proof as current_predecessor
   predecessor=current_predecessor()
  else:predecessor=predecessor_candidate_proof()
  expected_old=predecessor['APKSHA256']
  if backup_receipt_ref.get('path')!='receipts/diagnostic.jsonl'or proof not in read_receipts(root,'diagnostic'):raise ValueError('BACKUP_V2_ORIGINAL_DIAGNOSTIC_JOURNAL')
  if proof.get('predecessor')!=predecessor:raise ValueError('BACKUP_EXACT_IMMUTABLE_PREDECESSOR')
 if proof.get('format')!='aeris-cold-original-app-backup'or type(version)is not int or version not in(1,2,3)or proof.get('oldAPKSHA256')!=expected_old or proof.get('package')!='vn.rtr.aeris.mission':raise ValueError('ORIGINAL_BACKUP_RECEIPT_SCHEMA')
 identity=None
 def command(ref,args,output=None):
  nonlocal identity
  row=json.loads(read_ref(root,ref),object_pairs_hook=unique);argv=json.loads(read_ref(root,row['argvRef']));out=read_ref(root,row['stdoutRef']);err=read_ref(root,row['stderrRef'])
  expected=args if args[0]!='shell'else['shell',shlex.join(args[1:])]
  if version in(2,3):
   fields={'format','version','sequence','argvRef','startedHostNs','endedHostNs','exit','stdoutRef','stderrRef','captureComplete','failure'}
   if ref.get('path')!='receipts/command.jsonl'or ref.get('version')!=3 or set(row)!=fields or row not in read_receipts(root,'command')or any(type(row.get(k))is not int for k in('version','sequence','exit','startedHostNs','endedHostNs'))or row['sequence']<=0 or not 0<=row['startedHostNs']<=row['endedHostNs']or type(argv)is not list or len(argv)!=5 or any(type(v)is not str for v in argv):raise ValueError('PREDECESSOR_BACKUP_ORIGINAL_TYPED_COMMAND')
   if identity is None:identity=argv[:3]
   if argv[:3]!=identity:raise ValueError('PREDECESSOR_BACKUP_SAME_ADB_DEVICE')
  if row.get('format')!='aeris-command'or row.get('version')!=3 or row.get('captureComplete')is not True or row.get('failure')is not None or row.get('exit')!=0 or argv[1:4]!=['-s',proof['serial'],expected[0]]or argv[3:]!=expected or err or output is not None and out!=output:raise ValueError('ORIGINAL_BACKUP_SOURCE_COMMAND_LINK')
  return row,out
 before,_=command(proof['coldBeforeCommandRef'],['shell','sh','-c',COLD_ABSENCE_SCRIPT],b'ABSENT\n');pathrow,praw=command(proof['installedPathCommandRef'],['shell','pm','path','vn.rtr.aeris.mission']);installed=praw.decode().strip()
 if not installed.startswith('package:/')or'\n'in installed:raise ValueError('ORIGINAL_BACKUP_INSTALLED_PATH')
 sharow,sraw=command(proof['installedSHACommandRef'],['shell','sha256sum',installed[8:]])
 if sraw.decode().split()[0]!=expected_old:raise ValueError('ORIGINAL_BACKUP_INSTALLED_SHA')
 after,_=command(proof['coldAfterCommandRef'],['shell','sh','-c',COLD_ABSENCE_SCRIPT],b'ABSENT\n');capture=json.loads(read_ref(root,proof['exportCaptureReceiptRef']),object_pairs_hook=unique);argv=json.loads(read_ref(root,capture['argvRef']))
 if capture.get('format')!='aeris-native-export'or capture.get('fullOriginalFiles')is not True or capture.get('captureComplete')is not True or capture.get('failure')is not None or capture.get('exit')!=0 or read_ref(root,capture['stderrRef'])!=b''or argv[1:]!=['-s',proof['serial'],'exec-out','run-as','vn.rtr.aeris.mission','tar','-cf','-','files']:raise ValueError('ORIGINAL_BACKUP_COMPLETE_CAPTURE_ARGV')
 path=Path(proof['exportPath'])
 if path!=root.parent/'native-original-before-quarantine.tar'or capture.get('path')!=str(path)or capture.get('bytesRetained')!=proof['exportBytes']or not before['endedHostNs']<=pathrow['startedHostNs']<=pathrow['endedHostNs']<=sharow['startedHostNs']<=sharow['endedHostNs']<=capture['startedHostNs']<=capture['finishedHostNs']<=after['startedHostNs']<=after['endedHostNs']<=proof['verifiedHostNs']:raise ValueError('ORIGINAL_BACKUP_COLD_WINDOW_AND_OWNED_PATH')
 if version in(2,3):
  capture_fields={'format','version','argvRef','fullOriginalFiles','path','bytesRetained','bytesAcceptedByWriter','bytesObservedLowerBound','stderrRef','startedHostNs','finishedHostNs','exit','captureComplete','failure','cleanupErrors','exportReservationRetained','flightAcceptance'}
  if proof['exportCaptureReceiptRef'].get('path')!='receipts/diagnostic.jsonl'or capture not in read_receipts(root,'diagnostic')or set(capture)!=capture_fields or any(type(capture.get(k))is not int for k in('version','bytesRetained','bytesAcceptedByWriter','bytesObservedLowerBound','startedHostNs','finishedHostNs','exit'))or capture['version']!=1 or capture['bytesAcceptedByWriter']!=proof['exportBytes']or capture['bytesObservedLowerBound']!=proof['exportBytes']or capture['cleanupErrors']!=[]or capture['exportReservationRetained']is not False or capture['flightAcceptance']is not False or argv[:3]!=identity or type(proof['verifiedHostNs'])is not int:raise ValueError('PREDECESSOR_BACKUP_EXACT_COMPLETE_EXPORT')
  post_path,post_raw=command(proof['installedAfterPathCommandRef'],['shell','pm','path','vn.rtr.aeris.mission']);post_location=post_raw.decode().strip()
  if not post_location.startswith('package:/')or'\n'in post_location:raise ValueError('PREDECESSOR_AFTER_EXPORT_PACKAGE_PATH')
  post_sha,post_digest=command(proof['installedAfterSHACommandRef'],['shell','sha256sum',post_location[8:]])
  if post_digest.decode().split()[0]!=expected_old or not capture['finishedHostNs']<=post_path['startedHostNs']<=post_path['endedHostNs']<=post_sha['startedHostNs']<=post_sha['endedHostNs']<=after['startedHostNs']:raise ValueError('PREDECESSOR_AFTER_EXPORT_ORIGINAL_APK_CLOCK')
 table=verify_full_files_tar(path,proof['exportSHA256'],proof['exportBytes'])
 if any(proof.get(k)!=v for k,v in table.items()):raise ValueError('ORIGINAL_BACKUP_RECOMPUTED_MANIFEST')
 result={'exportPath':str(path),'exportSHA256':proof['exportSHA256'],'exportBytes':proof['exportBytes'],'oldAPKSHA256':expected_old,'serial':proof['serial'],'coldOriginalVerified':True,**table}
 if version in(2,3):
  retained=verify_predecessor_retained_files(path)
  if any(type(proof.get(k))is not type(v)or proof.get(k)!=v for k,v in {**table,**retained}.items()):raise ValueError('BACKUP_RETAINED_PREDECESSOR_BYTES')
  fields={'format','version','package','oldAPKSHA256','predecessor','serial','exportPath','exportBytes','exportSHA256','exportCaptureReceiptRef','coldBeforeCommandRef','installedPathCommandRef','installedSHACommandRef','coldAfterCommandRef','verifiedHostNs','installedAfterPathCommandRef','installedAfterSHACommandRef'}|set(table)|set(retained)
  if set(proof)!=fields:raise ValueError('BACKUP_V2_EXACT_SCHEMA')
  result.update(backupVersion=version,predecessor=predecessor,**retained)
 return result


PREDECESSOR_CANDIDATE_SHA='986bfabbbb2fc08043918a68e7ff211b9208826bd138f68a1e1fe123490447b5'
PREDECESSOR_NATIVE_SOURCE='3186db6e531b6bcb987dc82d2e7489a105a9d7b170c3d69a3b3667a275f00a3c'
PREDECESSOR_APK_SHA='3564fb8aa9e9006477b59b4f1e4954c3239ec20d5619b12f28b50b49d80de9c3'
RETAINED_DRAFT_SHA='2176fc9b9af0827943be02e5a98361b637306000969d711860506f04987c04cd'
RETAINED_QUARANTINE_ID='904c2c14555e4ffe8bc6da01021e4ee1'
RETAINED_QUARANTINE_SHA='386d135010e208eb577505e577f09a202dda3d62b020ac650ec30a953d69b7fc'
def predecessor_candidate_proof():
 from .candidate import load,sha
 from .paths import repository
 p=repository()/'evidence/runtime-nativeprepare10/candidates'/PREDECESSOR_CANDIDATE_SHA
 if any(v.is_symlink()for v in[p,*p.parents]):raise ValueError('PREDECESSOR_IMMUTABLE_PATH')
 m=load(p,PREDECESSOR_CANDIDATE_SHA);b=json.loads((p/'native-build-receipt.json').read_bytes())
 if m['native']['sourceSHA256']!=PREDECESSOR_NATIVE_SOURCE or m['native']['APK_SHA256']!=PREDECESSOR_APK_SHA or b.get('certificateSHA256')!=DEVELOPMENT_CERT_SHA or b.get('productionSigning')is not False or b.get('sourceCount')!=51:raise ValueError('PREDECESSOR_SOURCE_APK_CERT_FIXED51')
 return {'format':'aeris-immutable-upgrade-predecessor','version':1,'candidateDir':str(p),'candidateSHA256':PREDECESSOR_CANDIDATE_SHA,'nativeSourceSHA256':PREDECESSOR_NATIVE_SOURCE,'APKSHA256':PREDECESSOR_APK_SHA,'certificateSHA256':DEVELOPMENT_CERT_SHA,'nativeBuildReceiptSHA256':sha(p/'native-build-receipt.json')}
def verify_predecessor_retained_files(path):
 """Current root draft and nested ORIGINAL quarantine table are distinct."""
 prefix='files/recovery08/'+RETAINED_QUARANTINE_ID+'/original/';rows=[];draft='files/workspace03/draft-000001-'+RETAINED_DRAFT_SHA+'.json';draft_found=False
 with tarfile.open(path,'r:')as t:
  for m in t:
   name=m.name.rstrip('/')
   if not name.startswith(prefix)and name!=draft:continue
   if m.isdir():row=(name[len(prefix):],'D',0,'-')
   else:
    h=hashlib.sha256();f=t.extractfile(m)
    for block in iter(lambda:f.read(65536),b''):h.update(block)
    if name==draft:
     if h.hexdigest()!=RETAINED_DRAFT_SHA:raise ValueError('PREDECESSOR_RETAINED_DRAFT_BYTES')
     draft_found=True;continue
    row=(name[len(prefix):],'F',m.size,h.hexdigest())
   if not any(row[0]==top or row[0].startswith(top+'/')for top in QUARANTINE_TOPS):raise ValueError('PREDECESSOR_FOREIGN_ORIGINAL_TARGET')
   rows.append(row)
 digest=hashlib.sha256(b''.join((kind+'\t'+name+'\t'+str(size)+'\t'+h+'\n').encode()for name,kind,size,h in sorted(rows))).hexdigest()
 if not draft_found or digest!=RETAINED_QUARANTINE_SHA or len(rows)!=8 or sum(v[2]for v in rows)!=6043:raise ValueError('PREDECESSOR_RETAINED_ORIGINAL_TARGET_TABLE')
 return {'retainedDraftSHA256':RETAINED_DRAFT_SHA,'retainedDraftPath':draft,'retainedQuarantineIdentity':RETAINED_QUARANTINE_ID,'retainedQuarantineTableSHA256':digest}
