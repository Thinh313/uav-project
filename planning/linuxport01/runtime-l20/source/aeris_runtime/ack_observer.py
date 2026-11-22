"""One lifecycle log subscription. Readiness is a durable same-stream marker."""
import json,os,secrets,selectors,subprocess,threading,time
from .once_reader import unique
from .cleanup import cleanup
class AckObserver:
 def __init__(self,device,store,*,popen=subprocess.Popen,tag='AERIS_MISSION'):
  if tag not in('AERIS_MISSION','AERIS_PRODUCT_STATUS'):raise ValueError('SOURCE_ACK_TAG')
  self.tag=tag
  self.device=device;self.store=store;self.popen=popen;self.cv=threading.Condition();self.rows=[];self.markers={};self.expected=set();self.failure=None;self.closed=False;self.stop=threading.Event();self.pending=b'';self.pending_offset=0;self.process=None;self.thread=None;self.last_ref=None;self.cursor=0;self.busy=threading.Lock();self.closing=False;self.drained=threading.Event();self.first_barrier_seen=False
 def start(self):
  if self.process is not None:raise ValueError('ACK_ONE_LIFECYCLE_SUBSCRIPTION')
  self.device._check_budget_actor(popen=self.popen)
  budget=self.store.budget;budget.tick('observerEpochs');budget.prepare_directory('command_receipts',self.store.root/'receipts');available=budget.available('stream')
  if available<131072:raise ValueError('ACK_STREAM_START_RESERVATION')
  self.stream_lease=budget.reserve_lease({'stream':available})
  argv=[self.device.adb,'-s',self.device.serial,'logcat','-v','raw',self.tag+':I',*(['AERIS_JOURNAL17:I']if self.device.__class__.__name__=='AndroidDomain17'else[]),'*:S']
  try:self.process=self.popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  except BaseException:
   budget.release_lease(self.stream_lease);self.stream_lease=None;raise
  budget.bind_lease_child(self.stream_lease,self.process.pid)
  self.thread=threading.Thread(target=self._pump,name='aeris-persistent-ack',daemon=True);self.thread.start()
 def _pump(self):
  with self.store.budget.use_lease(self.stream_lease):return self._pump_reserved()
 def _pump_reserved(self):
  selector=None;p=self.process;pending_chunk=None
  try:
   selector=selectors.DefaultSelector()
   for name,stream in [('stdout',p.stdout),('stderr',p.stderr)]:os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,name)
   while not self.stop.is_set():
    for key,_ in selector.select(.05):
     raw=os.read(key.fileobj.fileno(),4097 if key.data=='stderr'else 65536)
     if not raw:
      if not self.closing:raise RuntimeError('ACK_STREAM_EOF_OR_ROTATION')
      selector.unregister(key.fileobj)
      if not selector.get_map():self.drained.set();return
      continue
     if key.data=='stderr':
      primary=RuntimeError('ACK_STREAM_STDERR_FAILED_PREFIX_INCOMPLETE')
      try:self.store.receipt('stream-stderr-%07d.json'%self.store.stream_offset,{'stderrRef':self.store.command_bytes(raw,closing=True),'observerFailure':True,'captureComplete':False},closing=True)
      except BaseException as storage:primary.add_note('ACK_STDERR_STORAGE_SECONDARY:'+str(storage));raise primary from storage
      raise primary
     pending_chunk=(raw,self.store.stream_offset)
     if not self.first_barrier_seen and self.store.stream_offset+len(raw)>2*2**20:raise ValueError('ACK_HISTORICAL_PREFIX2MiB')
     ref=self.store.stream(raw);pending_chunk=None
     with self.cv:
      self.pending+=raw
      if len(self.pending)>262144:raise ValueError('ACK_PENDING_BOUND')
      while b'\n'in self.pending:
       line,self.pending=self.pending.split(b'\n',1);line_raw=line+b'\n';line_ref=self.store.ref('ack-stream.raw',self.pending_offset,line_raw);self.pending_offset+=len(line_raw)
       marker=line.decode('ascii') if line.isascii() else ''
       if marker in self.expected:self.first_barrier_seen=True;self.markers[marker]=(len(self.rows),line_ref);self.cv.notify_all();continue
       if not line.startswith(b'{'):
        if self.first_barrier_seen:raise ValueError('ACK_UNEXPECTED_NONJSON_AFTER_READY')
        continue
       if len(line)>2048:raise ValueError('ACK_LINE2KiB_BOUND')
       row=json.loads(line,object_pairs_hook=unique)
       if type(row)is not dict:raise ValueError('ACK_OBJECT')
       if len(self.rows)>=8192:raise ValueError('ACK_ROWS_BOUND')
       self.rows.append((row,line_ref));self.cv.notify_all()
    if p.poll() is not None and not self.closing:raise RuntimeError('ACK_PROCESS_EXIT')
  except BaseException as error:
   if pending_chunk is not None:
    try:self.store.retain_failed_stream_chunk(*pending_chunk)
    except BaseException as storage:error.add_note('FAILED_STREAM_PREFIX_UNDURABLE:'+str(storage))
   with self.cv:self.failure=error;self.cv.notify_all()
   try:self.store.budget.failure(error)
   except BaseException as storage:error.add_note('ACK_FAILURE_DIAGNOSTIC_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:256])
  finally:
   try:
    if selector is not None:selector.close()
   except BaseException as cleanup:
    secondary=type(cleanup).__name__+':'+str(cleanup)[:512]
    with self.cv:
     if self.failure is None:self.failure=cleanup
     else:self.failure.add_note('ACK_SELECTOR_CLOSE_SECONDARY:'+secondary)
     self.cv.notify_all()
    try:self.store.budget.failure(self.failure,detail={'operation':'AckObserver.selector.close','cleanupFailure':secondary})
    except BaseException as storage:self.failure.add_note('ACK_SELECTOR_CLOSE_DIAGNOSTIC_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:256])
 def check(self):
  if self.failure is not None:raise RuntimeError('ACK_STREAM_FAILED:'+str(self.failure))from self.failure
  if self.closed:raise RuntimeError('ACK_STREAM_CLOSED')
 def barrier(self,deadline_ns):
  self.check()
  if self.process is None:self.start()
  with self.store.budget.use_lease(self.stream_lease):self.store.budget.ensure('stream',65536+2049)
  marker='AERIS_OBSERVER_READY_'+secrets.token_hex(16)
  with self.cv:self.expected.add(marker)
  self.device.command(['shell','log','-p','i','-t',self.tag,marker],deadline_ns=deadline_ns,maximum_bytes=131072)
  with self.cv:
   while marker not in self.markers:
    self.check();remaining=(deadline_ns-self.device.now())/1e9
    if remaining<=0:raise TimeoutError('ACK_SUBSCRIBE_MARKER_DEADLINE')
    self.cv.wait(min(.05,remaining))
   self.cursor,ref=self.markers.pop(marker);self.expected.remove(marker)
  self.store.receipt('barrier-%05d.json'%self.device.sequence,{'format':'aeris-ack-barrier','version':1,'marker':marker,'markerRef':ref,'observedHostNs':self.device.now(),'samePersistentStream':True,'intentDispatched':False},owner='barriers')
  self.check();return ref
 def expect_native_marker(self,nonce):
  import re
  if type(nonce)is not str or re.fullmatch('[a-f0-9]{32}',nonce)is None:raise ValueError('STATUS15_NATIVE_MARKER_NONCE')
  self.check()
  if self.process is None:self.start()
  with self.store.budget.use_lease(self.stream_lease):self.store.budget.ensure('stream',65536+2049)
  marker='AERIS_OBSERVER_READY_'+nonce
  with self.cv:
   if self.expected:raise ValueError('STATUS15_ONE_EXPECTED_NATIVE_MARKER')
   self.expected.add(marker)
  return marker
 def join_native_marker(self,marker,deadline_ns):
  with self.cv:
   if marker not in self.expected:raise ValueError('STATUS15_ORIGINAL_EXPECTED_MARKER')
   while marker not in self.markers:
    self.check();remaining=(deadline_ns-self.device.now())/1e9
    if remaining<=0:raise TimeoutError('STATUS15_NATIVE_MARKER_DEADLINE')
    self.cv.wait(min(.01,remaining))
   self.cursor,ref=self.markers.pop(marker);self.expected.remove(marker)
  observed=self.device.now();self.store.receipt('barrier-%05d.json'%self.device.sequence,{'format':'aeris-ack-barrier','version':2,'marker':marker,'markerRef':ref,'observedHostNs':observed,'samePersistentStream':True,'nativeEmittedBeforeCollector':True},owner='barriers');self.check();return ref,observed
 def rows_until(self,deadline_ns):
  while True:
   with self.cv:
    self.check()
    if self.device.now()>deadline_ns:raise TimeoutError('ANDROID_PUBLIC_LIVE_ACK10S')
    if self.cursor<len(self.rows):row,self.last_ref=self.rows[self.cursor];self.cursor+=1
    else:self.cv.wait(.05);continue
   yield row
 def close(self):
  if self.closed:
   if getattr(self,'close_receipt',{}).get('captureComplete')is True and hasattr(self,'close_ref'):return {'receipt':self.close_receipt,'receiptRef':self.close_ref}
   if self.failure is not None:raise self.failure
   if hasattr(self,'close_failure'):raise self.close_failure
   raise RuntimeError('ACK_PREVIOUS_CLOSE_INCOMPLETE_OR_UNDURABLE')
  self.closed=True;self.closing=True;p=self.process;errors=[]
  if p is not None:
   def stop_owned():
    if p.poll()is None:p.terminate()
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
   self.failure=cleanup(self.failure,[('ack-stop-wait',stop_owned)])
   if self.thread:self.thread.join(timeout=2)
   if self.thread and self.thread.is_alive():
    errors.append('ACK_INCOMPLETE_CLOSE_DRAIN2S');self.stop.set();self.thread.join(timeout=.1)
   if not self.drained.is_set():errors.append('ACK_CLOSE_EOF_NOT_PROVEN')
   prior=self.failure;notes=len(getattr(prior,'__notes__',()))
   self.failure=cleanup(self.failure,[('ack-stdout-close',p.stdout.close),('ack-stderr-close',p.stderr.close)])
   if self.failure is not prior or len(getattr(self.failure,'__notes__',()))>notes:
    try:self.store.budget.failure(self.failure,detail={'operation':'AckObserver.close','captureComplete':False})
    except BaseException as storage:self.failure.add_note('ACK_PIPE_CLOSE_DIAGNOSTIC_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:256])
  if getattr(self,'stream_lease',None)is not None and(self.thread is None or not self.thread.is_alive()):
   self.store.budget.release_lease(self.stream_lease);self.stream_lease=None
  if self.pending:errors.append('ACK_TRAILING_PARTIAL_ROW')
  receipt={'format':'aeris-ack-stream-close','version':1,'originalBytes':self.store.stream_offset,'exit':None if p is None else p.poll(),'error':None if self.failure is None else str(self.failure),'closeErrors':errors,'captureComplete':(p is None or self.drained.is_set()) and not errors and self.failure is None,'flightAcceptance':False,'authorityRestored':False}
  self.close_receipt=receipt;self.close_ref=self.store.receipt('stream-close.json',receipt,closing=True)
  if self.failure is not None:
   if errors:self.failure.add_note('ACK_CLOSE_ERRORS:'+':'.join(errors)[:512])
   raise self.failure
  if errors:self.close_failure=RuntimeError(':'.join(errors));raise self.close_failure
  return {'receipt':receipt,'receiptRef':self.close_ref}
