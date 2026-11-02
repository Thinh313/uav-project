"""Bounded auxiliary IPC evidence. No serialization/hash/IO on exchange paths.

The socket protocol and authority guards do not use this evidence as authority.
One shared client ring retains the first failed exchange and its bounded context.
The server retains its final eight exchanges; absence is NOT_RETAINED, not proof.
"""
import hashlib,json,os,struct,threading,time,zlib

MAGIC=b'AHIPC10\0'; FILE=struct.Struct('>8sI'); RECORD=struct.Struct('>HHHI')
SLOTS=8; REQUEST=257; RESPONSE=4097; META=1024; HEADER=4096; MAX_FILE=49152
TIMES=('begin','connect_begin','connect_end','peer_begin','peer_end','send_begin','send_end','first_recv','last_recv','recv_end','parse_begin','parse_end','exchange_end','schema_begin','schema_end','validate_begin','validate_end','finish')
FLAGS=('request_complete','response_complete','send_success','request_intended','response_intended','eof','timeout','overbound','parsed','schema','accepted','exception','recorder_failed','send_partial_unknown','multiple_send_buffers')
_rings={};_registry_lock=threading.RLock()

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def strict(raw):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('IPC10_DUPLICATE_KEY')
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError('IPC10_NONFINITE')))

class Exchange:
 def __init__(self,ring):
  self.ring=ring;self.request=bytearray(REQUEST);self.response=bytearray(RESPONSE);self.times=[None]*len(TIMES);self.active=False
 def reset(self,sequence,nonce,caller):
  self.sequence=sequence;self.nonce=nonce;self.caller=caller;self.request_bytes=0;self.response_bytes=0;self.flags=0;self.outbound_lengths=[];self.peer=None;self.error=None;self.times[:]=[None]*len(TIMES);self.active=True;return self
 def mark(self,name,at=None):self.times[TIMES.index(name)]=time.monotonic_ns()if at is None else at
 def flag(self,name):self.flags|=1<<FLAGS.index(name)
 def capture(self,which,raw,*,intended=False):
  data=self.request if which=='request'else self.response;key=which+'_bytes';at=getattr(self,key);take=min(len(raw),len(data)-at)
  if take:data[at:at+take]=raw[:take]
  setattr(self,key,at+take)
  if intended:self.flag(which+'_intended')
  if len(raw)>take:self.flag('overbound')
 def receive(self,which,raw,at):
  if self.times[TIMES.index('first_recv')]is None:self.mark('first_recv',at)
  self.mark('last_recv',at);self.capture(which,raw)
  if not raw:self.flag('eof')
 def finish(self,error=None):
  if error is not None:
   self.flag('exception');self.error=(type(error).__name__+':'+str(error))[:192]
   if isinstance(error,TimeoutError):self.flag('timeout')
  self.mark('finish');self.active=False

class RecorderView:
 """Recorder faults cannot preempt the original transport/parse/guard error."""
 def __init__(self,slot):self.slot=slot
 def __getattr__(self,name):return getattr(self.slot,name)
 @property
 def peer(self):return self.slot.peer
 @peer.setter
 def peer(self,value):self.slot.peer=value
 @property
 def nonce(self):return self.slot.nonce
 @nonce.setter
 def nonce(self,value):self.slot.nonce=value
 def fault(self,method):
  with self.slot.ring.lock:self.slot.flags|=1<<FLAGS.index('recorder_failed');self.slot.ring.recorder_error='IPC10_RECORDER_'+method
 def mark(self,*args):
  try:self.slot.mark(*args)
  except BaseException:self.fault('mark')
 def flag(self,name):
  try:self.slot.flag(name)
  except BaseException:self.fault('flag');self.slot.flags|=1<<FLAGS.index(name)
 def capture(self,which,raw,*,intended=False):
  before=getattr(self.slot,which+'_bytes')
  try:self.slot.capture(which,raw,intended=intended)
  except BaseException:
   self.fault('capture');self.original_prefix(which,raw,before)
   if intended:self.slot.flags|=1<<FLAGS.index(which+'_intended')
 def original_prefix(self,which,raw,before):
  data=self.slot.request if which=='request'else self.slot.response;take=min(len(raw),len(data)-before)
  data[before:before+take]=raw[:take];setattr(self.slot,which+'_bytes',before+take)
 def receive(self,which,raw,at):
  before=getattr(self.slot,which+'_bytes')
  try:self.slot.receive(which,raw,at)
  except BaseException:
   self.fault('receive');self.original_prefix(which,raw,before)
   if self.slot.times[TIMES.index('first_recv')]is None:self.slot.times[TIMES.index('first_recv')]=at
   self.slot.times[TIMES.index('last_recv')]=at
   if not raw:self.slot.flags|=1<<FLAGS.index('eof')

class TraceRing:
 def __init__(self,role,binding,endpoint,identity,*,candidate=None):
  if role not in('client','server'):raise ValueError('IPC10_ROLE')
  self.role=role;self.binding=dict(binding);self.endpoint=str(endpoint);self.identity=tuple(identity);self.candidate=candidate or os.environ.get('AERIS_CANDIDATE_SHA256');self.pid=os.getpid();self.lock=threading.RLock();self.slots=[Exchange(self)for _ in range(SLOTS)];self.total=0;self.overwritten=0;self.after_frozen=0;self.frozen=False;self.recorder_error=None;self.flushed=False;self.first_failed_sequence=None
 def begin(self,nonce,caller):
  with self.lock:
   if self.frozen:self.after_frozen+=1;raise RuntimeError('IPC10_FROZEN_NO_NEW_ACCEPTANCE')
   free=[s for s in self.slots if not s.active]
   if not free:
    self.recorder_error='IPC10_ALL_EIGHT_INFLIGHT';self.frozen=True;raise RuntimeError(self.recorder_error)
   slot=min(free,key=lambda s:getattr(s,'sequence',0));self.total+=1
   if self.total>=2**63:raise RuntimeError('IPC10_SEQUENCE_BOUND')
   if getattr(slot,'sequence',0):self.overwritten+=1
   return RecorderView(slot.reset(self.total,nonce,caller))
 def finish(self,slot,error=None):
  # Memory-only final acceptance/fault linearization. Never holds the lock
  # over a socket operation, serialization, file write or metadata transaction.
  with self.lock:return self._finish(slot,error)
 def _finish(self,slot,error=None):
  if slot is None:return
  if isinstance(slot,RecorderView):slot=slot.slot
  original_error=error
  retired=error is None and(self.recorder_error is not None or self.frozen)
  if retired:
   error=RuntimeError('HOST_HEALTH_IPC_RECORDER_FAILED'if self.recorder_error is not None else'IPC10_FROZEN_NO_NEW_ACCEPTANCE');slot.flags&=~(1<<FLAGS.index('accepted'))
  # Raw buffers are populated before this finalization. Even an injected
  # finalizer failure cannot erase the triggering exchange.
  try:slot.finish(error)
  except BaseException as diagnostic:
   slot.flags|=1<<FLAGS.index('recorder_failed');slot.flags&=~(1<<FLAGS.index('accepted'));slot.active=False;self.recorder_error=(type(diagnostic).__name__+':'+str(diagnostic))[:192]
   with self.lock:
    self.frozen=True
    if self.first_failed_sequence is None:self.first_failed_sequence=slot.sequence
   if original_error is not None:
    error.add_note('IPC10_RECORDER_SECONDARY:'+self.recorder_error);return
   if retired:raise error from diagnostic
   raise RuntimeError('HOST_HEALTH_IPC_RECORDER_FAILED')from diagnostic
  if error is not None and self.role=='client':
   with self.lock:
    self.frozen=True
    if self.first_failed_sequence is None:self.first_failed_sequence=slot.sequence
  if retired:raise error
 def export(self):
  """Called only after ingress retirement/endpoint join, never on a guard path."""
  with self.lock:
   selected=sorted((s for s in self.slots if getattr(s,'sequence',0)),key=lambda s:s.sequence)
   if any(s.active for s in selected):raise RuntimeError('IPC10_EXPORT_INFLIGHT_UNKNOWN')
   header={'format':'aeris-hosthealth-ipc-trace','version':1,'role':self.role,'pid':self.pid,'candidateSHA256':self.candidate,'expectedBinding':self.binding,'endpoint':self.endpoint,'endpointIdentity':list(self.identity),'times':list(TIMES),'flags':list(FLAGS),'total':self.total,'overwritten':self.overwritten,'afterFrozenNotCaptured':self.after_frozen,'firstFailedSequence':self.first_failed_sequence,'frozen':self.frozen,'recorderFailure':self.recorder_error,'coverage':'FIRST_CLIENT_FAILURE_VIEW'if self.role=='client'and self.frozen else'BOUNDED_FINAL_EIGHT_NOT_FULL_HISTORY','sendSemantics':'INTENDED_BUFFER_NOT_BYTES_SENT_UNLESS_SEND_SUCCESS','actualValues':'EXACT_ORIGINAL_JSON_BYTES_WHEN_PARSEABLE','captureOverhead':'INCLUDED_IN_ORIGINAL_TIMER_NO_SUBTRACTION','errorMeaning':'UTF8_PREFIX16_ONLY_FULL_PRIMARY_IN_OWNER_ERROR','sendTimesMeaning':'LAST_ATTEMPT_IF_MULTIPLE_SEND_BUFFERS;UNKNOWN_PARTIAL_NEVER_BYTES_SENT','rows':len(selected)}
   rawheader=canonical(header)
   if len(rawheader)>HEADER:raise ValueError('IPC10_HEADER4096')
   chunks=[FILE.pack(MAGIC,len(rawheader)),rawheader]
   for s in selected:
    request=bytes(s.request[:s.request_bytes]);response=bytes(s.response[:s.response_bytes]);error=None if s.error is None else s.error.encode('utf8',errors='replace')[:16].decode('utf8',errors='ignore');meta=canonical({'s':s.sequence,'n':s.nonce,'c':s.caller,'p':s.peer,'t':s.times,'f':s.flags,'e':error,'a':s.outbound_lengths,'q':hashlib.sha256(request).hexdigest(),'r':hashlib.sha256(response).hexdigest()})
    if len(meta)>META:raise ValueError('IPC10_METADATA1024')
    payload=meta+request+response;chunks.extend([RECORD.pack(len(meta),len(request),len(response),zlib.crc32(payload)&0xffffffff),payload])
   raw=b''.join(chunks)
   if len(raw)>MAX_FILE:raise ValueError('IPC10_FILE48KiB')
   return raw
 def flush(self,budget,path):
  if self.flushed:raise RuntimeError('IPC10_NO_SECOND_FLUSH')
  raw=self.export();result=budget.write('closure',path,raw,closing=True);self.flushed=True;return result

def client_ring(binding,endpoint,identity):
 key=(str(endpoint),tuple(identity),binding['instance'],binding['pid'])
 with _registry_lock:
  if key not in _rings:
   if len(_rings)>=1:raise RuntimeError('IPC10_ONE_SOURCE_BOUND_CLIENT_ENDPOINT')
   _rings[key]=TraceRing('client',binding,endpoint,identity)
  existing=_rings[key]
  if existing.binding!=binding or existing.candidate!=os.environ.get('AERIS_CANDIDATE_SHA256')or existing.identity!=tuple(identity):raise RuntimeError('IPC10_EXISTING_RING_SOURCE_MISMATCH')
  return _rings[key]

def flush_clients(budget,path):
 with _registry_lock:rings=list(_rings.values())
 if not rings:return None
 if len(rings)!=1:raise RuntimeError('IPC10_CLIENT_ENDPOINT_BOUND')
 return rings[0].flush(budget,path)

def decode(raw,*,expected_candidate=None,expected_binding=None):
 """Strict cold decoding of original byte buffers; never a health grant."""
 if type(raw)is not bytes or len(raw)>MAX_FILE or len(raw)<FILE.size:raise ValueError('IPC10_FILE_BOUND')
 magic,hn=FILE.unpack_from(raw);at=FILE.size
 if magic!=MAGIC or not 0<hn<=HEADER or at+hn>len(raw):raise ValueError('IPC10_HEADER')
 h=strict(raw[at:at+hn]);at+=hn
 if h.get('format')!='aeris-hosthealth-ipc-trace'or h.get('version')!=1 or h.get('times')!=list(TIMES)or h.get('flags')!=list(FLAGS)or h.get('role')not in('client','server')or type(h.get('rows'))is not int or not 0<=h['rows']<=SLOTS:raise ValueError('IPC10_SCHEMA')
 if expected_candidate is not None and h['candidateSHA256']!=expected_candidate:raise ValueError('IPC10_CANDIDATE')
 if expected_binding is not None and h['expectedBinding']!=expected_binding:raise ValueError('IPC10_BINDING')
 rows=[];previous=0
 for _ in range(h['rows']):
  if at+RECORD.size>len(raw):raise ValueError('IPC10_PARTIAL_RECORD')
  mn,qn,rn,crc=RECORD.unpack_from(raw,at);at+=RECORD.size
  if not 0<mn<=META or qn>REQUEST or rn>RESPONSE or at+mn+qn+rn>len(raw):raise ValueError('IPC10_RECORD_BOUND')
  payload=raw[at:at+mn+qn+rn];at+=len(payload)
  if zlib.crc32(payload)&0xffffffff!=crc:raise ValueError('IPC10_RECORD_CRC')
  m=strict(payload[:mn]);q=payload[mn:mn+qn];r=payload[mn+qn:]
  if set(m)!={'s','n','c','p','t','f','e','a','q','r'}or type(m['s'])is not int or not previous<m['s']<=h['total']or len(m['t'])!=len(TIMES)or any(v is not None and(type(v)is not int or not 0<=v<2**63)for v in m['t'])or type(m['a'])is not list or len(m['a'])>2 or any(type(n)is not int or not 0<=n<=8192 for n in m['a'])or type(m['f'])is not int or m['f']>>len(FLAGS)or hashlib.sha256(q).hexdigest()!=m['q']or hashlib.sha256(r).hexdigest()!=m['r']:raise ValueError('IPC10_RECORD_SCHEMA_SHA')
  previous=m['s'];times=dict(zip(TIMES,m['t']));flags={name:bool(m['f']&(1<<i))for i,name in enumerate(FLAGS)}
  for a,b in [('connect_begin','connect_end'),('peer_begin','peer_end'),('send_begin','send_end'),('first_recv','last_recv'),('parse_begin','parse_end'),('schema_begin','schema_end'),('validate_begin','validate_end')]:
   if times[a]is not None and times[b]is not None and times[b]<times[a]:raise ValueError('IPC10_TIME_ORDER')
  chain=('begin','connect_begin','connect_end','peer_begin','peer_end','send_begin','send_end','first_recv','last_recv','recv_end','parse_begin','parse_end','exchange_end','schema_begin','schema_end','validate_begin','validate_end','finish')if h['role']=='client'else('begin','peer_begin','peer_end','first_recv','last_recv','recv_end','parse_begin','parse_end','send_begin','send_end','exchange_end','finish')
  previous_time=None
  for name in chain:
   value=times[name]
   if value is not None:
    if previous_time is not None and value<previous_time:raise ValueError('IPC10_CROSS_PHASE_ORDER')
    previous_time=value
  def parsed(b):
   try:return strict(b)
   except (ValueError,UnicodeError):return None
  request=parsed(q);response=parsed(r);elapsed=None
  if times['begin']is not None and times['exchange_end']is not None:
   elapsed=times['exchange_end']-times['begin']
   if elapsed<0:raise ValueError('IPC10_EXCHANGE_ORDER')
  predicates={'elapsedExceeds100ms':None if elapsed is None else elapsed>100000000,'challengeMismatch':None if not isinstance(response,dict)else response.get('challenge')!=m['n'],'bindingMismatches':None if not isinstance(response,dict)else[k for k,v in h['expectedBinding'].items()if response.get(k)!=v]}
  if flags['schema']and(not flags['parsed']or not flags['response_complete']):raise ValueError('IPC10_SCHEMA_WITHOUT_PARSE')
  if flags['accepted']and h['role']=='client':
   if any(predicates[k]for k in predicates)or any(flags[k]for k in('exception','recorder_failed','eof','timeout','overbound','send_partial_unknown'))or not all(flags[k]for k in('schema','parsed','request_complete','response_complete','send_success'))or m['p']!=h['expectedBinding']['pid']or not isinstance(request,dict)or request!={'challenge':m['n'],'instance':h['expectedBinding']['instance']}or any(times[k]is None for k in('begin','exchange_end','schema_begin','schema_end','validate_begin','validate_end')):raise ValueError('IPC10_ACCEPTED_CONTRADICTION')
  rows.append({'metadata':m,'times':times,'flags':flags,'requestOriginal':q,'responseOriginal':r,'requestParsed':request,'responseParsed':response,'elapsedNs':elapsed,'subpredicates':predicates})
 if at!=len(raw):raise ValueError('IPC10_TRAILING_BYTES')
 return {'header':h,'rows':rows,'healthAuthority':False}

def verify_original(raw,*,candidate,binding,endpoint,endpoint_identity,trace_pid,role):
 """Caller supplies independently joined launch/endpoint/owner originals.

Unit decode is intentionally untrusted. This gate never accepts self-reported
header identity as an external launch fact, and grants no flight authority.
 """
 result=decode(raw,expected_candidate=candidate,expected_binding=binding);h=result['header']
 if h['endpoint']!=str(endpoint)or h['endpointIdentity']!=list(endpoint_identity)or h['pid']!=trace_pid or h['role']!=role:raise ValueError('IPC10_ORIGINAL_LAUNCH_ENDPOINT_BINDING')
 return result

def correlate(client,server):
 """An absent server counterpart is NOT_RETAINED, not a fabricated match."""
 joined=[]
 for c in client['rows']:
  matches=[s for s in server['rows']if s['metadata']['n']==c['metadata']['n']and s['requestOriginal']==c['requestOriginal']and s['responseOriginal']==c['responseOriginal']]
  if len(matches)>1:raise ValueError('IPC10_DUPLICATE_COUNTERPART')
  joined.append({'clientSequence':c['metadata']['s'],'serverSequence':None if not matches else matches[0]['metadata']['s'],'status':'EXACT_NONCE_AND_RAW_BYTES_JOINED'if matches else'NOT_RETAINED_OR_BYTES_DIFFER_NOT_AUTHORITY'})
 return joined
