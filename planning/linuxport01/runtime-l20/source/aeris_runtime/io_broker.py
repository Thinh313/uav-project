"""TRANSPORT14: single owned, typed, non-authoritative persistent ADB shell.

Four STATUS commands remain four counted, original command receipts. Only their
host process transport is shared. Output regular files are nonce-owned transient
scratch, capped before capture. No flight, input, navigation or BOOTSTRAP op.
"""
import base64,hashlib,json,os,re,secrets,selectors,shlex,subprocess,threading,time
from .cleanup import cleanup
from pilot.betaintegrated01.runtime.ap_stage import canonical
PACKAGE='vn.rtr.aeris.mission'
FRAME_LIMIT=16385+65+512

def operation(args):
 args=list(args)
 if len(args)==7 and args[:6]==['shell','log','-p','i','-t','AERIS_MISSION']and re.fullmatch('AERIS_OBSERVER_READY_[a-f0-9]{32}',args[6]):return 'MARKER',64
 if len(args)==13 and args[:12]==['shell','am','broadcast','-n',PACKAGE+'/.CockpitActivity$StatusReceiver','-a',PACKAGE+'.STATUS','--es','missionAction','STATUS','--es','missionRequestBase64']:
  from .once_reader import unique
  try:
   raw=base64.b64decode(args[12],altchars=b'-_',validate=True);v=json.loads(raw,object_pairs_hook=unique)
   if not 0<len(raw)<=512 or base64.urlsafe_b64encode(raw).decode()!=args[12]or type(v)is not dict or set(v)!={'version','requestNonce'}or type(v['version'])is not int or v['version']!=1 or not isinstance(v['requestNonce'],str)or re.fullmatch('[a-f0-9]{32}',v['requestNonce'])is None or json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()!=raw:raise ValueError()
  except (ValueError,UnicodeError,TypeError,KeyError):raise ValueError('BROKER_TYPED_STATUS_REQUEST')
  return 'STATUS',2048
 if args==['shell','pidof',PACKAGE]:return 'PID',64
 if args==['shell','run-as',PACKAGE,'cat','files/runtime/response.json']:return 'SNAPSHOT',16384
 raise ValueError('BROKER_TYPED_FOUR_OPERATIONS_ONLY')

def scratch_path(token):
 if type(token)is not str or re.fullmatch('[a-f0-9]{32}',token)is None:raise ValueError('BROKER_TOKEN')
 return '/data/local/tmp/aeris-transport14-'+token

def startup_script(token):
 d=scratch_path(token)
 return ('umask 077\nmkdir '+d+' || exit 71\n'+''.join(': >'+d+'/'+name+' || exit 72\n'for name in('out','err','rc','h1','h2'))+'printf '+shlex.quote('T14_READY '+token+'\n')+'\n').encode()

def _anonymous_capture(command,directory,maximum_stdout):
 """Private fixed-source renderer, never a public arbitrary-command API.

 FD3 carries original stdout to the outer capped sink. The inner pipe carries
 only stderr. Three sidecars are fresh and bounded to at most4 bytes each.
 """
 if type(command)is not str or not command or len(command.encode())>2048 or type(maximum_stdout)is not int or not 0<maximum_stdout<=16384 or re.fullmatch('/data/local/tmp/aeris-transport14-[a-f0-9]{32}',directory)is None:raise ValueError('ANONYMOUS_CAPTURE_FIXED_SOURCE_SHAPE')
 d=directory
 prefix=''.join(': >'+d+'/'+name+' || exit 72\n'for name in('rc','h1','h2'))
 pipeline=('{ { '+command+"; t14rc=$?; printf '%s\\n' \"$t14rc\" >"+d+'/rc; } 2>&1 1>&3 | { head -c 65 >'+d+"/err; printf '%s\\n' \"$?\" >"+d+'/h2; }; } 3>&1 | { head -c '+str(maximum_stdout+1)+' >'+d+"/out; printf '%s\\n' \"$?\" >"+d+'/h1; }\n')
 status=('t14d='+d+'\nfor t14status in rc h1 h2; do\n t14value=$(head -c 4 "$t14d/$t14status")\n t14size=$(wc -c <"$t14d/$t14status")\n t14size=$((t14size + 0))\n case "$t14value:$t14size" in [0-9]:2|[1-9][0-9]:3|1[0-9][0-9]:4|2[0-4][0-9]:4|25[0-5]:4) ;; *) printf \'T14_STATUS_FAILED %s\\n\' "$t14status"; cat '+d+'/out; cat '+d+'/err; exit 73 ;; esac\n case "$t14status" in rc) rc=$t14value ;; h1) h1=$t14value ;; h2) h2=$t14value ;; esac\ndone\nolen=$(wc -c <'+d+'/out)\nelen=$(wc -c <'+d+'/err)\nolen=$((olen + 0))\nelen=$((elen + 0))\n')
 return (prefix+pipeline+status).encode()

def operation_script(args,token,seq,nonce):
 kind,limit=operation(args);d=scratch_path(token)
 if type(seq)is not int or not 0<seq<=3700 or type(nonce)is not str or re.fullmatch('[a-f0-9]{32}',nonce)is None:raise ValueError('BROKER_OPERATION_SEQUENCE_NONCE')
 capture=_anonymous_capture(shlex.join(args[1:]),d,limit)
 return capture+('printf '+shlex.quote(f'T13 {seq} {nonce} {kind} %s %s %s %s %s\n')+' "$rc" "$h1" "$h2" "$olen" "$elen"\ncat '+d+'/out\ncat '+d+'/err\nprintf '+shlex.quote(f'\nT13_END {seq} {nonce}\n')+'\n').encode()

def stop_script(token):
 d=scratch_path(token)
 return ('rm -- '+ ' '.join(d+'/'+name for name in('out','err','rc','h1','h2'))+' && rmdir -- '+d+' && printf '+shlex.quote('T14_CLOSED '+token+'\n')+'\nexit\n').encode()

class FrameParser:
 """One original frame, exact canonical header/body/footer, bounded prefix."""
 def __init__(self,seq,nonce,kind,limit):self.seq=seq;self.nonce=nonce;self.kind=kind;self.limit=limit;self.raw=bytearray();self.result=None
 def feed(self,raw):
  if type(raw)is not bytes:raise TypeError('BROKER_FRAME_BYTES')
  self.raw.extend(raw)
  if self.result is not None and raw:raise ValueError('BROKER_UNSOLICITED_TRAILING_FRAME')
  if len(self.raw)>FRAME_LIMIT:raise ValueError('BROKER_FRAME_BOUND_PREFIX')
  if b'\n'not in self.raw:
   if len(self.raw)>192:raise ValueError('BROKER_HEADER192')
   return None
  end=self.raw.index(10)+1;header=bytes(self.raw[:end])
  match=re.fullmatch(rb'T13 ([1-9][0-9]{0,3}) ([a-f0-9]{32}) (MARKER|STATUS|PID|SNAPSHOT) (0|[1-9][0-9]{0,2}) (0|[1-9][0-9]{0,2}) (0|[1-9][0-9]{0,2}) (0|[1-9][0-9]{0,4}) (0|[1-9][0-9]{0,2})\n',header)
  if match is None:raise ValueError('BROKER_HEADER_SCHEMA')
  seq=int(match[1]);nonce=match[2].decode();kind=match[3].decode();code,h1,h2,n,e=map(int,match.groups()[3:])
  if (seq,nonce,kind)!=(self.seq,self.nonce,self.kind):raise ValueError('BROKER_FRAME_BINDING')
  if code>255 or h1>255 or h2>255 or n>self.limit+1 or e>65:raise ValueError('BROKER_HEADER_SOURCE_BOUNDS')
  footer=f'\nT13_END {seq} {nonce}\n'.encode();total=end+n+e+len(footer)
  if len(self.raw)<total:return None
  if len(self.raw)!=total or bytes(self.raw[-len(footer):])!=footer:raise ValueError('BROKER_FOOTER_OR_TRAILING')
  self.result={'header':header,'stdout':bytes(self.raw[end:end+n]),'stderr':bytes(self.raw[end+n:end+n+e]),'footer':footer,'exit':code,'headExit':[h1,h2],'oversize':n>self.limit or e>64}
  return self.result
 def eof(self):
  if self.result is None:raise ValueError('BROKER_PARTIAL_EOF_PREFIX')
  return self.result

class DeviceIOBroker:
 def __init__(self,device):
  self.device=device;self.budget=device.budget;self.original_store=device.store;self.original_root=device.root;self.token=secrets.token_hex(16);self.seq=0;self.process=None;self.selector=None;self.lease=None;self.failure=None;self.closed=False;self.busy=threading.Lock();self.last_frame=None;self.launch_ref=None;self.close_result=None;self.stderr_persisted=0;self.stderr_refs=[];self.capture_persistence_failed=False;self.failed_capture_durable=False;self.failed_capture_refs=[]
 def _read(self,deadline,*,maximum_stdout=FRAME_LIMIT+1):
  while True:
   if self.device.now()>=deadline:raise TimeoutError('BROKER_DEADLINE')
   for key,_ in self.selector.select(min(.01,max(0,(deadline-self.device.now())/1e9))):
    raw=os.read(key.fileobj.fileno(),4097 if key.data=='stderr'else maximum_stdout)
    if not raw:raise RuntimeError('BROKER_EOF_OR_DEATH')
    if key.data=='stderr':
     self.stderr_prefix.extend(raw[:4097-len(self.stderr_prefix)])
     raise RuntimeError('BROKER_TRANSPORT_STDERR_PREFIX')
    return raw
   if self.process.poll()is not None:raise RuntimeError('BROKER_PROCESS_EXIT')
 def _write(self,raw,deadline):
  if self.device.now()>=deadline:raise TimeoutError('BROKER_WRITE_DEADLINE')
  # Bounded write to a live shell with a single small operation, never a queue.
  view=memoryview(raw)
  while view:
   if self.device.now()>=deadline:raise TimeoutError('BROKER_WRITE_DEADLINE')
   try:n=os.write(self.process.stdin.fileno(),view)
   except BlockingIOError:
    import select
    select.select([], [self.process.stdin.fileno()], [], min(.01,max(0,(deadline-self.device.now())/1e9)));continue
   if type(n)is not int or not 0<n<=len(view):raise OSError('BROKER_SHORT_PIPE_WRITE')
   view=view[n:]
 def start(self,deadline):
  self.device._check_budget_actor()
  if self.process is not None:raise ValueError('BROKER_ONE_START')
  self.budget.tick('diagnosticChildren');self.lease=self.budget.reserve_lease({'commands':65536,'command_receipts':16384})
  argv=[self.device.adb,'-s',self.device.serial,'shell','-T','sh'];script=startup_script(self.token);self.stderr_prefix=bytearray();prefix=bytearray();started=self.device.now()
  try:
   self.process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
   os.set_blocking(self.process.stdin.fileno(),False)
   self.budget.bind_lease_child(self.lease,self.process.pid)
   self.selector=selectors.DefaultSelector()
   for name,stream in [('stdout',self.process.stdout),('stderr',self.process.stderr)]:os.set_blocking(stream.fileno(),False);self.selector.register(stream,selectors.EVENT_READ,name)
   self._write(script,deadline);expected=('T14_READY '+self.token+'\n').encode()
   while len(prefix)<len(expected):
    prefix.extend(self._read(deadline,maximum_stdout=len(expected)+1-len(prefix)))
    if len(prefix)>len(expected)or not expected.startswith(prefix):raise ValueError('BROKER_START_EXACT_READY')
  except BaseException as error:self.failure=error
  with self.budget.use_lease(self.lease):
   proof={'format':'aeris-device-io-broker-launch','version':2,'captureVersion':2,'argv':argv,'pid':None if self.process is None else self.process.pid,'token':self.token,'scriptBase64':base64.b64encode(script).decode(),'scriptSHA256':hashlib.sha256(script).hexdigest(),'startedHostNs':started,'readyHostNs':self.device.now(),'readyRef':self.original_store.command_bytes(prefix),'stderrRef':self.retain_transport_stderr(self.original_store),'ready':self.failure is None,'failure':None if self.failure is None else str(self.failure)[:256],'scratchPayloadMaximumBytes':16462,'scratchFilesystemForecastBytes':49152,'noAuthority':True}
   self.launch_ref=self.original_store.receipt('broker-launch.json',proof)
  if self.failure is not None:raise self.failure
  return {'pid':self.process.pid,'launchRef':self.launch_ref,'noAuthority':True}
 def accepts(self,args):
  args=list(args)
  owned=args[:2]==['shell','log']or args[:3]==['shell','am','broadcast']or args[:2]==['shell','pidof']or args[:4]==['shell','run-as',PACKAGE,'cat']
  if not owned:return False
  operation(args);return True
 def execute(self,args,deadline):
  if self.closed or self.failure is not None or self.process is None:raise RuntimeError('BROKER_NOT_LIVE')
  if not self.busy.acquire(blocking=False):raise ValueError('BROKER_ONE_INFLIGHT')
  self.last_frame=None;nonce=secrets.token_hex(16);self.seq+=1;kind,limit=operation(args);parser=FrameParser(self.seq,nonce,kind,limit);script=operation_script(args,self.token,self.seq,nonce);started=self.device.now()
  try:
   self._write(script,deadline)
   while parser.result is None:parser.feed(self._read(deadline,maximum_stdout=FRAME_LIMIT+1-len(parser.raw)))
   # No unclaimed trailing stdout or diagnostic stderr can be accepted.
   if self.selector.select(0):raise RuntimeError('BROKER_UNSOLICITED_READY_BYTES')
   frame=parser.eof();self.last_frame=frame
   if frame['headExit']!=[0,0]or frame['oversize']:raise ValueError('BROKER_BOUNDED_READER_OR_OVERSIZE')
   return frame
  except BaseException as error:self.failure=error;raise
  finally:
   self.last_prefix=bytes(parser.raw);self.last_operation={'seq':self.seq,'nonce':nonce,'kind':kind,'scriptSHA256':hashlib.sha256(script).hexdigest(),'startedHostNs':started};self.busy.release()
 def command_proof(self,store,frame):
  value={'format':'aeris-device-io-broker-command','version':1,'launchStore':self.original_root.name,'launchRef':self.launch_ref,'pid':self.process.pid,'operation':self.last_operation,'headerBase64':base64.b64encode(frame['header']).decode(),'footerBase64':base64.b64encode(frame['footer']).decode(),'headExit':frame['headExit'],'oversize':frame['oversize'],'transportFailure':None if self.failure is None else str(self.failure)[:256]}
  return store.broker_proof(value)
 def retain_transport_stderr(self,store,*,closing=False):
  raw=bytes(self.stderr_prefix[self.stderr_persisted:]);ref=store.command_bytes(raw,closing=closing)
  if raw:self.stderr_refs.append({'store':store.root.name,'ref':ref});self.stderr_persisted=len(self.stderr_prefix)
  return ref
 def transfer(self,new):
  old=self.device
  if self.busy.locked()or self.failure is not None or self.closed or new.budget is not self.budget or new.serial!=old.serial or new.adb!=old.adb or old.root.parent!=new.root.parent or old.root.name!='android-api'or new.root.name!='android-api-restart-01'or getattr(new,'io_broker',None)is not None:raise ValueError('BROKER_EXACT_CASE_RESTART_TRANSFER')
  proof={'format':'aeris-device-io-broker-transfer','version':1,'launchStore':self.original_root.name,'launchRef':self.launch_ref,'pid':self.process.pid,'oldStore':old.root.name,'newStore':new.root.name,'afterSequence':self.seq,'hostNs':old.now(),'authorityRestored':False,'processIdentityRestored':False}
  new.store.receipt('broker-transfer.json',proof);old.io_broker=None;new.io_broker=self;self.device=new
 def _drain(self,deadline):
  self.close_tail={'stdout':bytearray(),'stderr':bytearray()};self.eof_drained=False;seen=set()
  if self.process is None:self.eof_drained=True;return
  # Rebuild both pipe registrations even when startup's selector setup failed.
  # A missing registration is never treated as observed EOF.
  selector=selectors.DefaultSelector()
  try:
   for name in('stdout','stderr'):
    stream=getattr(self.process,name)
    if stream is None or stream.closed:raise RuntimeError('BROKER_ORIGINAL_PIPE_UNAVAILABLE_FOR_EOF')
    os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,name)
   while selector.get_map():
    if self.device.now()>=deadline:raise TimeoutError('BROKER_CLOSE_EOF_DEADLINE')
    for key,_ in selector.select(min(.01,max(0,(deadline-self.device.now())/1e9))):
     name=key.data;cap=16962 if name=='stdout'else 4096;raw=os.read(key.fileobj.fileno(),min(4096,cap+1-len(self.close_tail[name])))
     if not raw:selector.unregister(key.fileobj);seen.add(name);continue
     self.close_tail[name].extend(raw)
     if len(self.close_tail[name])>cap:raise ValueError('BROKER_CLOSE_TAIL_BOUND_PREFIX')
   self.eof_drained=seen=={'stdout','stderr'}
  finally:selector.close()
 def close(self,deadline):
  if self.close_result is not None:return self.close_result
  if self.busy.locked():raise ValueError('BROKER_INFLIGHT_CLOSE')
  if self.process is None and self.lease is None:
   self.closed=True;self.close_result={'receipt':{'format':'aeris-device-io-broker-close','version':1,'pid':None,'exit':None,'operations':self.seq,'noActorCreated':True,'scratchCleanupAcknowledged':True,'captureComplete':True,'drainComplete':True,'failure':None if self.failure is None else str(self.failure)[:256],'authorityRestored':False,'flightAcceptance':False},'receiptRef':None};return self.close_result
  prefix=bytearray();clean=False;primary=self.failure;self.closed=True
  try:
   if primary is None and self.process is not None and self.process.poll()is None:
    self._write(stop_script(self.token),deadline);expected=('T14_CLOSED '+self.token+'\n').encode()
    while len(prefix)<len(expected):
     prefix.extend(self._read(deadline,maximum_stdout=len(expected)+1-len(prefix)))
     if len(prefix)>len(expected)or not expected.startswith(prefix):raise ValueError('BROKER_CLOSE_EXACT_READY')
    self.process.stdin.close();self.process.wait(timeout=max(.001,(deadline-self.device.now())/1e9));clean=self.process.returncode==0
  except BaseException as error:
   if primary is None:primary=error
   else:primary.add_note('BROKER_CLOSE_SECONDARY:'+str(error)[:256])
  def stop():
   if self.process is not None:
    if self.process.poll()is None:self.process.terminate()
    try:self.process.wait(timeout=2)
    except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=2)
  operations=[('broker-stop-wait',stop),('broker-original-eof-drain',lambda:self._drain(max(deadline,self.device.now()+1_000_000_000)))]
  if self.selector is not None:operations.append(('broker-selector-close',self.selector.close))
  if self.process is not None:
   for name in('stdin','stdout','stderr'):operations.append(('broker-'+name+'-close',getattr(self.process,name).close))
  close_errors=[]
  def tracked(label,op):
   def run():
    try:return op()
    except BaseException as error:close_errors.append({'operation':label,'error':str(error)[:128]});raise
   return run
  primary=cleanup(primary,[(label,tracked(label,op))for label,op in operations])
  drained=(self.process is None or self.process.poll()is not None)and not close_errors and getattr(self,'eof_drained',False)and(not self.capture_persistence_failed or self.failed_capture_durable)
  value={'format':'aeris-device-io-broker-close','version':1,'pid':None if self.process is None else self.process.pid,'exit':None if self.process is None else self.process.poll(),'operations':self.seq,'scratchCleanupAcknowledged':clean or self.process is None,'drainComplete':drained,'closeErrors':close_errors,'operationalFailure':None if self.failure is None else str(self.failure)[:256],'closePrefixRef':None,'stdoutTailRef':None,'stderrTailRef':None,'originalEOFDrained':getattr(self,'eof_drained',False),'transportStderrRefs':list(self.stderr_refs),'transportStderrCapturedBytes':len(self.stderr_prefix),'failedCaptureRefs':list(self.failed_capture_refs),'failedCaptureDurable':not self.capture_persistence_failed or self.failed_capture_durable,'captureComplete':primary is None and clean,'failure':None if primary is None else str(primary)[:256],'authorityRestored':False,'flightAcceptance':False}
  try:
   with self.budget.use_lease(self.lease):
    closing=self.budget.snapshot().get('failed')is not None
    value['closePrefixRef']=self.original_store.command_bytes(prefix,closing=closing)
    for name in('stdout','stderr'):value[name+'TailRef']=self.original_store.command_bytes(getattr(self,'close_tail',{}).get(name,b''),closing=closing)
    self.retain_transport_stderr(self.original_store,closing=closing);value['transportStderrRefs']=list(self.stderr_refs)
    tail_extra=any(getattr(self,'close_tail',{}).values())
    if tail_extra:value['captureComplete']=False;value['failure']=(value['failure']or'BROKER_UNEXPECTED_CLOSE_TAIL')
    ref=self.original_store.receipt('broker-close.json',value,closing=closing)
   if drained:self.budget.release_lease(self.lease);self.lease=None
  except BaseException as error:
   if primary is not None:error.add_note('BROKER_PRIMARY:'+str(primary));raise
  self.close_result={'receipt':value,'receiptRef':ref}
  if not drained:
   if primary is not None:raise primary
   raise RuntimeError('BROKER_DRAIN_UNKNOWN')
  if self.failure is None and(primary is not None or not value['captureComplete']):
   if primary is not None:raise primary
   raise RuntimeError('BROKER_UNEXPECTED_CLOSE_TAIL')
  return self.close_result
