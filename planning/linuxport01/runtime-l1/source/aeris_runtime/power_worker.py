"""One supervised power-acquisition process per health lifetime.

The helper has no filesystem writer. The parent owns durable original power rows
and the finite lifetime receipt. A response is an observation, never authority.
"""
from pathlib import Path
import hashlib,json,os,secrets,selectors,signal,struct,subprocess,sys,threading,time
if not __package__:
 sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
 from aeris_runtime.metadata_budget import capture_command,MetadataBudget
 from aeris_runtime.stage_trace import StageTrace,CODES
 from aeris_runtime.host_power_platform import power_argv
else:
 from .metadata_budget import capture_command,MetadataBudget
 from .stage_trace import StageTrace,CODES
 from .host_power_platform import power_argv
REQUEST=struct.Struct('<4sIII16s16sQ')
RESPONSE=struct.Struct('<4sIIII16s16sQQiBHHHQQQ')
BINDING=struct.Struct('<4sQQIIII16s16sQQQ')
MAGIC=b'PW14';BINDING_MAGIC=b'PB14';FRESH_NS=2_000_000_000
STDOUT_MAX=192;STDERR_MAX=128;ERROR_MAX=512;HELPER_STDERR_MAX=128
RESPONSE_MAX=RESPONSE.size+STDOUT_MAX+1+STDERR_MAX+1+ERROR_MAX
LIFETIME_LEASE=16*1024;MAX_QUERIES=4200

def _error(e):return (type(e).__name__+':'+str(e))[:256]
def _capture_error(e):
 if e is None:return b''
 notes=list(getattr(e,'__notes__',[]));full=json.dumps(notes,ensure_ascii=True,separators=(',',':')).encode();reason=str(e)
 v={'typePrefix':type(e).__name__[:32],'reasonPrefix':reason[:120],'reasonSHA256':hashlib.sha256(reason.encode()).hexdigest(),'notesCount':len(notes),'notesSHA256':hashlib.sha256(full).hexdigest(),'notesPrefix':full[:100].decode('ascii'),'diagnosticIsBoundedPrefix':len(full)>100 or len(reason)>120 or len(type(e).__name__)>32}
 while True:
  raw=json.dumps(v,sort_keys=True,separators=(',',':')).encode()
  if len(raw)<=ERROR_MAX:return raw
  v['diagnosticIsBoundedPrefix']=True
  key=max(('reasonPrefix','notesPrefix','typePrefix'),key=lambda k:len(json.dumps(v[k]).encode()))
  if not v[key]:raise RuntimeError('POWER_ERROR_FIXED_SCHEMA_BOUND')
  v[key]=v[key][:-1]

def _integer(v):return type(v)is int and 0<=v<2**63

def _read_exact(stream,n):
 raw=bytearray()
 while len(raw)<n:
  part=stream.read(n-len(raw))
  if not part:
   if not raw:return None
   raise RuntimeError('POWER_CHILD_PARTIAL_REQUEST')
  raw.extend(part)
 return bytes(raw)

def child_main(instance_hex,parent,source_sha):
 def stopping(sig,frame):raise RuntimeError('POWER_CHILD_TERMINATION_REQUESTED')
 signal.signal(signal.SIGTERM,stopping)
 instance=bytes.fromhex(instance_hex)
 if len(instance)!=16 or parent!=os.getppid()or hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=source_sha:raise RuntimeError('POWER_CHILD_SOURCE_PARENT_INSTANCE')
 seq=0
 while True:
  raw=_read_exact(sys.stdin.buffer,REQUEST.size)
  if raw is None:return
  magic,request_seq,pid,ppid,inst,nonce,request_ns=REQUEST.unpack(raw)
  if magic!=MAGIC or inst!=instance or request_seq!=seq+1 or request_seq>MAX_QUERIES or pid!=os.getpid()or ppid!=parent or os.getppid()!=parent:raise RuntimeError('POWER_CHILD_REQUEST_BINDING')
  seq=request_seq;started=time.monotonic_ns();trace=StageTrace()
  if not 0<=started-request_ns<FRESH_NS:raise RuntimeError('POWER_CHILD_REQUEST_CLOCK')
  commands=[]
  def spawn_power(*a,**kw):
   command=subprocess.Popen(*a,**kw);commands.append(command);return command
  r=capture_command(None,'guardian',power_argv(),deadline_ns=request_ns+FRESH_NS,stdout_limit=STDOUT_MAX,stderr_limit=STDERR_MAX,trace=trace,spawn=spawn_power)
  ended=time.monotonic_ns();out=r['stdout'];err=r['stderr'];failure=_capture_error(r['failure'])
  popen=next((row for row in trace.snapshot().get('rows',[])if row[1]==CODES.index('popen')),None)
  if popen is None:raise RuntimeError('POWER_CHILD_POPEN_TIMING_ABSENT')
  if len(out)>STDOUT_MAX+1 or len(err)>STDERR_MAX+1:raise RuntimeError('POWER_CHILD_CAPTURE_BOUND')
  response=RESPONSE.pack(MAGIC,seq,os.getpid(),parent,commands[0].pid if len(commands)==1 else 0,instance,nonce,started,ended,r['exit']if type(r['exit'])is int else -999,int(r['captureComplete']),len(out),len(err),len(failure),popen[3],popen[4],popen[5])+out+err+failure
  sys.stdout.buffer.write(response);sys.stdout.buffer.flush()
  if failure or not r['captureComplete']:return

class PowerWorker:
 def __init__(self,budget,owner,root,*,spawn=subprocess.Popen,now=time.monotonic_ns):
  if type(budget)is not MetadataBudget or owner not in('guardian','monitor'):raise ValueError('POWER_WORKER_EXACT_BUDGET_OWNER')
  self.budget=budget;self.owner=owner;self.root=Path(root);self.spawn=spawn;self.real_spawn=spawn is subprocess.Popen;self.now=now;self.parent=os.getpid();self.instance=secrets.token_bytes(16);self.process=None;self.lease=None;self.attempted=False;self.seq=0;self.failure=None;self.closure=None;self.close_failure=None;self.stderr=bytearray();self.last_wire=b'';self.last_request=None;self.last_response=None;self.selector=None;self.stderr_eof=False;self.stdout_eof=False;self.lock=threading.RLock();self.accepted_digest=hashlib.sha256();self.started=None;self.source_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 def _put(self,name,value):
  raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
  if len(raw)>8192:raise ValueError('POWER_LIFETIME_RECEIPT8KiB')
  with self.budget.use_lease(self.lease):return self.budget.write(self.owner,self.root/name,raw,closing=name=='power-helper-close.json')
 def start(self):
  if self.attempted:raise RuntimeError('POWER_WORKER_ONE_START')
  self.attempted=True;self.budget.require_real_actor();self.budget.tick('diagnosticChildren');self.lease=self.budget.reserve_lease({self.owner:LIFETIME_LEASE});self.started=self.now()
  argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--power-child',self.instance.hex(),str(self.parent),self.source_sha]
  try:
   self.process=self.spawn(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
   self.budget.bind_lease_child(self.lease,self.process.pid)
   self.selector=selectors.DefaultSelector()
   for name in('stdout','stderr'):
    stream=getattr(self.process,name);os.set_blocking(stream.fileno(),False);self.selector.register(stream,selectors.EVENT_READ,name)
   os.set_blocking(self.process.stdin.fileno(),False)
   self._put('power-helper-launch.json',{'format':'aeris-power-helper-launch','version':1,'pid':self.process.pid,'parentPID':self.parent,'instance':self.instance.hex(),'argv':argv,'sourceSHA256':self.source_sha,'startedHostNs':self.started,'queryDeadlineNs':FRESH_NS,'maximumQueries':MAX_QUERIES,'diagnosticChildCharged':True,'predispatchLeaseBytes':LIFETIME_LEASE,'periodicPopenInParent':False,'flightAcceptance':False})
   return self.process.pid
  except BaseException as e:
   self.failure=e
   # close retains PID ownership even when bind/selector/launch write fails.
   try:self.close()
   except BaseException as secondary:e.add_note('POWER_START_CLOSE_SECONDARY:'+_error(secondary))
   raise
 def _alive(self):
  if self.parent!=os.getpid()or self.process is None:raise RuntimeError('POWER_PARENT_PROCESS_EPOCH')
  if self.process.poll()is not None:raise RuntimeError('POWER_HELPER_DEAD:'+str(self.process.returncode))
 def _read(self,needed,deadline):
  raw=bytearray()
  while len(raw)<needed:
   if self.now()>=deadline:raise TimeoutError('POWER_HELPER_ORIGINAL2S_DEADLINE')
   if self.selector is None:raise RuntimeError('POWER_HELPER_NO_SELECTOR')
   for key,_ in self.selector.select(min(.05,max(0,(deadline-self.now())/1e9))):
    name=key.data
    if name=='stderr':
     part=os.read(key.fileobj.fileno(),HELPER_STDERR_MAX+1-len(self.stderr))
     if not part:self.stderr_eof=True;self.selector.unregister(key.fileobj)
     else:
      self.stderr.extend(part)
      if len(self.stderr)>HELPER_STDERR_MAX:raise RuntimeError('POWER_HELPER_STDERR_OVERFLOW')
      raise RuntimeError('POWER_HELPER_STDERR_NOT_EMPTY')
    else:
     part=os.read(key.fileobj.fileno(),needed-len(raw))
     if not part:self.stdout_eof=True;self.selector.unregister(key.fileobj);raise RuntimeError('POWER_HELPER_PARTIAL_RESPONSE')
     raw.extend(part);self.last_wire+=part
     if len(self.last_wire)>RESPONSE_MAX:raise RuntimeError('POWER_HELPER_RESPONSE_TOTAL_BOUND')
   if self.process.poll()is not None and len(raw)<needed:raise RuntimeError('POWER_HELPER_DEAD_PARTIAL_RESPONSE')
  return bytes(raw)
 def query(self):
  with self.lock:
   if self.failure is not None:raise self.failure
   if self.closure is not None or self.close_failure is not None:raise RuntimeError('POWER_HELPER_CLOSED')
   try:
    self._alive()
    if self.seq>=MAX_QUERIES:raise RuntimeError('POWER_HELPER_QUERY_CAP')
    self.seq+=1;nonce=secrets.token_bytes(16);started=self.now();deadline=started+FRESH_NS
    request=REQUEST.pack(MAGIC,self.seq,self.process.pid,self.parent,self.instance,nonce,started);self.last_request=request;self.last_wire=b''
    n=os.write(self.process.stdin.fileno(),request)
    if n!=len(request):raise RuntimeError('POWER_HELPER_REQUEST_SHORT_WRITE_NO_RETRY')
    header=self._read(RESPONSE.size,deadline);fields=RESPONSE.unpack(header)
    magic,seq,pid,ppid,command_pid,instance,actual_nonce,qs,qe,exit_code,complete,on,en,fn,ps,pw,pc=fields
    if magic!=MAGIC or seq!=self.seq or pid!=self.process.pid or ppid!=self.parent or instance!=self.instance or actual_nonce!=nonce or command_pid<=0 or command_pid in(pid,ppid) or complete not in(0,1)or on>STDOUT_MAX+1 or en>STDERR_MAX+1 or fn>ERROR_MAX:raise RuntimeError('POWER_HELPER_EXACT_RESPONSE_BINDING_OR_BOUND')
    body=self._read(on+en+fn,deadline)if on+en+fn else b'';received=self.now();wire=header+body;self.last_wire=wire
    if not(started<=qs<=ps<=ps+pw<=qe<=received<deadline)or pc>pw:raise RuntimeError('POWER_HELPER_ORIGINAL_CLOCK_OR_FRESHNESS')
    out=body[:on];err=body[on:on+en];error=body[on+en:]
    self.last_response={'sequence':seq,'pid':pid,'parentPID':ppid,'commandPID':command_pid,'instance':instance.hex(),'challenge':nonce.hex(),'requestHostNs':started,'queryStartedHostNs':qs,'queryCompletedHostNs':qe,'receivedHostNs':received,'popenStartedHostNs':ps,'popenWallNs':pw,'popenThreadCPUNs':pc,'exit':exit_code,'captureComplete':bool(complete),'error':error.decode('utf-8','strict')}
    binding=BINDING.pack(BINDING_MAGIC,started,received,pid,ppid,command_pid,seq,instance,nonce,ps,pw,pc)
    failure=None
    if exit_code!=0 or not complete or error:failure=RuntimeError('POWER_HELPER_COMMAND_FAILED:'+error.decode('utf-8','strict'))
    self.accepted_digest.update(request+wire)
    result={'stdout':out,'stderr':err,'failure':failure,'captureComplete':bool(complete),'started':qs,'ended':qe,'binding':binding}
    if failure is not None:self.failure=failure
    return result
   except BaseException as e:
    if self.failure is None:self.failure=e
    raise
 def check_alive(self):
  if self.failure is not None:raise self.failure
  self._alive()
 def close(self):
  with self.lock:
   if self.closure is not None:return dict(self.closure)
   if self.close_failure is not None:raise self.close_failure
   errors=[];forced=False;p=self.process;stdout_tail=b'';tail_complete=True
   def attempt(name,fn):
    try:fn()
    except BaseException as e:errors.append({'step':name,'error':_error(e)})
   if p is not None:
    attempt('stdin-close',p.stdin.close)
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:
     forced=True;attempt('terminate',p.terminate)
     try:p.wait(timeout=2)
     except subprocess.TimeoutExpired:attempt('kill',p.kill);attempt('reap',lambda:p.wait(timeout=2))
    except BaseException as e:errors.append({'step':'wait','error':_error(e)})
    # Only fixed bounded trailing prefixes, never an unbounded communicate.
    for name,maximum in(('stdout',RESPONSE_MAX),('stderr',HELPER_STDERR_MAX)):
     stream=getattr(p,name)
     if stream is None:continue
     try:
      os.set_blocking(stream.fileno(),False);tail=bytearray()
      while len(tail)<=maximum:
       try:b=os.read(stream.fileno(),maximum+1-len(tail))
       except BlockingIOError:break
       if not b:
        if name=='stdout':self.stdout_eof=True
        else:self.stderr_eof=True
        break
       tail.extend(b)
      if name=='stderr':self.stderr.extend(tail)
      elif tail:
       stdout_tail=bytes(tail);errors.append({'step':'unexpected-stdout-tail','error':'UNCONSUMED_PROTOCOL_BYTES_RETAINED_IN_RECEIPT'})
      if len(tail)>maximum:
       tail_complete=False;errors.append({'step':name+'-overflow','error':'BOUNDED_FAILED_PREFIX'})
     except BaseException as e:errors.append({'step':name+'-drain','error':_error(e)})
     attempt(name+'-close',stream.close)
   if self.selector is not None:attempt('selector-close',self.selector.close)
   group_gone=None
   if p is not None and self.real_spawn:
    def group_alive():
     try:os.killpg(p.pid,0);return True
     except ProcessLookupError:return False
    try:
     group_gone=not group_alive()
     if not group_gone:
      errors.append({'step':'command-process-group','error':'DESCENDANT_SURVIVED_HELPER_CLOSE'})
      os.killpg(p.pid,signal.SIGTERM);end=time.monotonic()+2
      while group_alive()and time.monotonic()<end:time.sleep(.01)
      if group_alive():os.killpg(p.pid,signal.SIGKILL)
      end=time.monotonic()+2
      while group_alive()and time.monotonic()<end:time.sleep(.01)
      group_gone=not group_alive()
      if not group_gone:errors.append({'step':'command-process-group','error':'DESCENDANT_CLOSURE_UNPROVEN'})
    except BaseException as e:errors.append({'step':'command-process-group','error':_error(e)})
   if p is not None and p.poll()is None:errors.append({'step':'process','error':'POWER_HELPER_STILL_ALIVE'})
   if forced:errors.append({'step':'process','error':'POWER_HELPER_FORCED_TERMINATION'})
   if p is not None and p.returncode!=0:errors.append({'step':'process','error':'POWER_HELPER_NONZERO:'+str(p.returncode)})
   if p is not None and(not self.stdout_eof or not self.stderr_eof):errors.append({'step':'capture','error':'POWER_HELPER_EOF_UNPROVEN'})
   if self.stderr:errors.append({'step':'stderr','error':'POWER_HELPER_STDERR_NOT_EMPTY'})
   value={'format':'aeris-power-helper-close','version':1,'pid':None if p is None else p.pid,'parentPID':self.parent,'instance':self.instance.hex(),'sourceSHA256':self.source_sha,'startedHostNs':self.started,'closedHostNs':self.now(),'exit':None if p is None else p.returncode,'queriesDispatched':self.seq,'acceptedWireSHA256':self.accepted_digest.hexdigest(),'lastRequestHex':None if self.last_request is None else self.last_request.hex(),'lastResponse':self.last_response,'failedProtocolPrefixHex':self.last_wire.hex()[:2*RESPONSE_MAX] if self.failure else None,'unexpectedStdoutTailHex':stdout_tail.hex(),'protocolTailCaptureComplete':tail_complete and self.stdout_eof,'helperStderrHex':bytes(self.stderr[:HELPER_STDERR_MAX+1]).hex(),'helperStderrCapturedBytes':len(self.stderr),'helperStderrCapturedSHA256':hashlib.sha256(self.stderr).hexdigest(),'helperStderrCaptureComplete':len(self.stderr)<=HELPER_STDERR_MAX and self.stderr_eof,'stdoutEOF':self.stdout_eof,'stderrEOF':self.stderr_eof,'primaryFailure':None if self.failure is None else _error(self.failure),'closeErrors':errors,'commandProcessGroupGone':group_gone,'groupProofScope':'ACTUAL_OWNED_PROCESS_GROUP'if self.real_spawn else'MOCK_NOT_KERNEL_PROOF','physicalClosed':p is None or p.poll()is not None,'flightAcceptance':False,'authorityRestored':False}
   if self.lease is not None:
    try:self._put('power-helper-close.json',value)
    except BaseException as e:errors.append({'step':'receipt-write','error':_error(e)})
    if not errors:
     try:self.budget.release_lease(self.lease);self.lease=None
     except BaseException as e:errors.append({'step':'lease-release','error':_error(e)})
   if errors:
    self.close_failure=RuntimeError('POWER_HELPER_CLOSE_FAILED:'+json.dumps(errors,separators=(',',':'))[:1024]);raise self.close_failure
   self.closure=value;return dict(value)

if __name__=='__main__':
 if len(sys.argv)!=5 or sys.argv[1]!='--power-child':raise RuntimeError('POWER_CHILD_FIXED_ENTRY')
 child_main(sys.argv[2],int(sys.argv[3]),sys.argv[4])
