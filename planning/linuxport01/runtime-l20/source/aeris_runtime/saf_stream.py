"""Bounded actual recipient stream, only a source-enrolled immutable SAF URI.
No archive copy or full-stdout-blob claim: callback sees original ADB pipe bytes;
receipt retains SHA/prefix/count/EOF and the genuine native-success reference.
"""
import contextlib,hashlib,json,os,re,selectors,subprocess,time
from .metadata_budget import encoded
_TOKEN=object();MIB=2**20

def need(v,n):
 if not v:raise ValueError('SAF_STREAM_'+n)
class SafDocument:
 def __init__(self,token,device,receipt,original_ref):
  need(token is _TOKEN,'PRIVATE_NATIVE_CAPABILITY');self.device=device;self.receipt=dict(receipt);self.original_ref=original_ref;self.token=token

def capability(probe,stream,index):
 from .product_types import is_product_probe
 need(is_product_probe(probe) and getattr(probe,'raw_export_reference',None)is not None,'GENUINE_SOURCE_ROOT_EXPORT_REFERENCE');d=probe.device;need(d.serial=='emulator-5582'and probe.latest is not None,'OWNED_EMULATOR_ONLY');rawref=probe.raw_export_reference;manifest=json.loads(__import__('pathlib').Path(rawref['manifestPath']).read_bytes());need(hashlib.sha256(__import__('pathlib').Path(rawref['manifestPath']).read_bytes()).hexdigest()==rawref['manifestSHA256'],'ORIGINAL_ROOT_MANIFEST_SHA');rows=probe.latest['exportBudget'].get('successReceipts');need(type(rows)is list and len(rows)<=8,'GENUINE_LAST8_NATIVE_RECEIPTS');hits=[r for r in rows if r.get('stream')==stream and r.get('index')==index and r.get('manifestSHA256')==rawref['manifestSHA256']];need(len(hits)==1,'ONE_NATIVE_SUCCESS_FOR_CURRENT_PART');advertised=hits[0];path=advertised.get('immutableReceiptPath');need(type(path)is str and re.fullmatch(r'files/product-exports01/success-[a-f0-9]{64}\.json',path)is not None,'IMMUTABLE_NATIVE_SUCCESS_PATH');raw=d.command(['shell','run-as',d.APPLICATION_PACKAGE,'cat',path],deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=4096);original_ref=d.last_command['stdoutRef'];need(len(raw)==advertised['immutableReceiptBytes']and hashlib.sha256(raw).hexdigest()==advertised['immutableReceiptSHA256'],'NATIVE_SUCCESS_ORIGINAL_SHA');q=json.loads(raw);need(q.get('format')=='aeris-native-saf-success'and q.get('version')==1 and q.get('status')=='SAF_READBACK_VERIFIED'and q.get('authorityRestorable')is False and q.get('processEpoch')==probe.latest['processEpoch'],'NATIVE_SUCCESS_SOURCE_CONTEXT');need(q['stream']==stream and q['index']==index and q['manifestSHA256']==rawref['manifestSHA256']and path.endswith(hashlib.sha256(q['originalRequestId'].encode()).hexdigest()+'.json'),'NATIVE_SUCCESS_EXACT_PART');uri=q.get('documentUri');need(type(uri)is str and len(uri)<=2048 and re.fullmatch(r'content://(?:com\.android\.externalstorage\.documents|com\.android\.providers\.downloads\.documents|com\.android\.providers\.media\.documents)/[A-Za-z0-9%._~:/@+\-]+',uri)is not None,'LOCAL_GENUINE_SAF_URI_NO_SHELL_SYNTAX')
 if stream=='manifest':need(index==-1 and q['bytes']==rawref['manifestBytes']and q['sha256']==rawref['manifestSHA256']and 0<q['bytes']<=256*1024,'EXACT_ORIGINAL_BARE_ROOT_MANIFEST_DOCUMENT')
 else:
  need(stream in('bundle','native-closed-files')and type(index)is int,'STREAM_DOMAIN');selected=manifest['bundle'if stream=='bundle'else'nativeStream'];need(0<=index<len(selected['parts']),'PART_INDEX');p=selected['parts'][index];need(q['bytes']==p['bytes']and q['sha256']==p['sha256']and q['bytes']<=28*MIB,'PART_ACTUAL_NATIVE_BYTES_SHA')
 return SafDocument(_TOKEN,d,q,original_ref)

class Reader:
 def __init__(self,device,cap,deadline,check):
  need(type(cap)is SafDocument and cap.token is _TOKEN and cap.device is device and device.serial=='emulator-5582','PRIVATE_PART_DEVICE');self.d=device;self.cap=cap;self.deadline=deadline;self.check=check;self.buffer=bytearray();self.prefix=bytearray();self.error_prefix=bytearray();self.count=0;self.delivered=0;self.hash=hashlib.sha256();self.eof=set();self.failure=None;self.closed=False;self.process=None;self.sel=selectors.DefaultSelector();self.started=device.now();self.argv=[device.adb,'-s',device.serial,'exec-out','content','read','--uri',cap.receipt['documentUri']]
  try:
   device._check_budget_actor();device.budget.tick('commands');device.sequence+=1;need(device.sequence<=3700,'ORIGINAL_COMMAND3700');device.budget.ensure('commands',32768);device.budget.ensure('command_receipts',8192);self.argv_ref=device.store.command_bytes(encoded(self.argv));self.process=subprocess.Popen(self.argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   for name,f in(('stdout',self.process.stdout),('stderr',self.process.stderr)):os.set_blocking(f.fileno(),False);self.sel.register(f,selectors.EVENT_READ,name)
  except BaseException as primary:
   from .android import _stop_capture_process,_capture_cleanup
   errors=[];operations=[('constructor-selector-close',self.sel.close)]
   if self.process is not None:
    operations=[('constructor-child-stop',lambda:_stop_capture_process(self.process)),*operations]
    for label,f in(('stdout',self.process.stdout),('stderr',self.process.stderr)):
     if f is not None:operations.append(('constructor-'+label+'-close',f.close))
   primary=_capture_cleanup(primary,operations,errors);raise primary

 def read(self,n):
  need(type(n)is int and 0<=n<=65536 and not self.closed,'READ64K');
  if not n:return b''
  while not self.buffer and self.sel.get_map():
   need(self.d.now()<self.deadline,'RECIPIENT_STREAM_DEADLINE');self.check()
   for key,_ in self.sel.select(.05):
    raw=os.read(key.fileobj.fileno(),65536 if key.data=='stdout'else min(65536,16385-len(self.error_prefix)))
    if not raw:self.eof.add(key.data);self.sel.unregister(key.fileobj);continue
    if key.data=='stderr':self.error_prefix.extend(raw);need(len(self.error_prefix)<=16384,'STDERR16K');continue
    self.count+=len(raw);need(self.count<=self.cap.receipt['bytes'],'EXTRA_ORIGINAL_RECIPIENT_BYTES');self.hash.update(raw);self.prefix.extend(raw[:max(0,256-len(self.prefix))]);self.buffer.extend(raw);need(len(self.buffer)<=65536,'IN_MEMORY64K')
  if self.buffer:
   out=bytes(self.buffer[:n]);del self.buffer[:n];self.delivered+=len(out);return out
  return b''
 def finish(self,primary=None):
  if self.closed:return
  self.closed=True;errors=[];complete=False
  try:
   if primary is None:need(not self.buffer and self.eof=={'stdout','stderr'}and self.count==self.delivered==self.cap.receipt['bytes']and self.hash.hexdigest()==self.cap.receipt['sha256'],'COMPLETE_CONSUMPTION_SHA_AND_BOTH_EOF');need(self.process.wait(timeout=max(.01,(self.deadline-self.d.now())/1e9))==0 and not self.error_prefix,'EXACT_SUCCESS_STDERR_EMPTY');complete=True
  except BaseException as e:primary=e
  finally:
   from .android import _stop_capture_process,_capture_cleanup
   operations=[('saf-content-child-stop',lambda:_stop_capture_process(self.process)),('saf-content-selector-close',self.sel.close),('saf-content-stdout-close',self.process.stdout.close),('saf-content-stderr-close',self.process.stderr.close)];primary=_capture_cleanup(primary,operations,errors)
   receipt={'format':'aeris-native-saf-recipient-stream','version':1,'argvRef':self.argv_ref,'sourceNativeReceiptRef':self.cap.original_ref,'nativeManifestSHA256':self.cap.receipt['manifestSHA256'],'stream':self.cap.receipt['stream'],'index':self.cap.receipt['index'],'originalObservedBytes':self.count,'deliveredBytes':self.delivered,'stdoutSHA256':self.hash.hexdigest(),'stdoutPrefixRef':self.d.store.command_bytes(self.prefix,closing=primary is not None),'stderrRef':self.d.store.command_bytes(self.error_prefix,closing=primary is not None),'startedHostNs':self.started,'finishedHostNs':self.d.now(),'PID':self.process.pid,'exit':self.process.poll(),'bothOriginalPipeEOF':self.eof=={'stdout','stderr'},'completeOriginalStream':complete and primary is None,'fullStdoutBlobRetained':False,'failure':None if primary is None else type(primary).__name__+':'+str(primary)[:512],'cleanupErrors':errors,'noHostArchiveCopy':True,'flightAcceptance':False};self.d.store.receipt('saf-recipient-stream.json',receipt,closing=primary is not None)
  if primary is not None:raise primary

@contextlib.contextmanager
def open_document(device,cap,*,deadline_ns,check=lambda:None):
 with device.budget.operation({'commands':32768,'command_receipts':8192}):
  reader=Reader(device,cap,deadline_ns,check)
  try:yield reader
  except BaseException as e:reader.finish(e);raise
  else:reader.finish()
