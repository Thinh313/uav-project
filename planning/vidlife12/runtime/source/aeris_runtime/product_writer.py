"""Bounded product data RPC; Root owns every physical write and fsync.
No command, input authority, deletion, replacement, or arbitrary owner/path verb.
"""
from pathlib import Path
import base64,hashlib,json,os,re,secrets,socket,struct,threading,time
from .metadata_budget import MetadataBudget,encoded
MAX_PAYLOAD=65536;MAX_REQUEST=98304;MAX_REPLY=2048;RPC_NS=200_000_000;MAX_WRITES=32768
LANES={'journal':'lifecycle','state':'lifecycle','media':'dto','reports':'external_task'}
CAPS={'journal':8*2**20,'state':8*2**20,'media':15*2**20,'reports':2**20}
def need(v,name):
 if not v:raise ValueError('PRODUCT_WRITER_'+name)
def unique(items):
 value={}
 for k,v in items:
  need(k not in value,'DUPLICATE_JSON_FIELD');value[k]=v
 return value
class ProductWriter:
 def __init__(self,budget,context):
  need(type(budget)is MetadataBudget,'EXACT_SHARED_BUDGET')
  need(type(context)is dict and set(context)=={'run','epoch','boot','operator','generation','profileId'}and len(encoded(context))<=256,'EXACT_SELECTED_CONTEXT')
  need(all(type(v)is str and 0<len(v)<=64 for v in context.values())and re.fullmatch('[A-Za-z0-9_-]{1,64}',context['run'])is not None,'CONTEXT_VALUES')
  self.budget=budget;self.context=dict(context);self.root=budget.evidence/'sessions'/context['run']/'product';self.token=secrets.token_hex(32);self.sequence=0;self.lock=threading.Lock();self.failure=None;self.closed=False;self.server=None;self.thread=None;self.stop=threading.Event();self.inflight=None;self.requests=0;self.last_commit_state=False;self.native_registration=None;self.native_registrations=[];self.native_closed_inputs=None;self.raw_export=None;self.raw_export_attempted=False;self.scene_source=None;self.flight_interval_source=None;self.delivery_check=None;self.committed_files={};self.observer_sequence=0;self.observer_failure=None;self.ending=False;self.connections=set();self.workers=[];self.roles={};self.role_lock=threading.Lock()
  case_index=budget.snapshot()['counters']['cases'];need(type(case_index)is int and case_index in(1,2),'EXISTING_CASE_ORDINAL')
  self.case_index=case_index;self.socket_path=budget.evidence/'reports'/('pw%02d.sock'%case_index)
 def descriptor(self):return {'format':'aeris-product-writer','version':1,'socketPath':str(self.socket_path),'token':self.token,'context':dict(self.context),'maximumPayloadBytes':MAX_PAYLOAD,'maximumRequestBytes':MAX_REQUEST,'deadlineNs':RPC_NS,'operations':['append','exclusive','clock-proof','native-registration','raw-export','flight-interval','native-closed-inputs'],'observerOperations':['scene-frame'],'maximumConnections':2,'replacementOrDeletion':False}
 def dispatch(self,request,*,received_ns=None):
  """Called by the one server worker. Unit mocks call this same gate directly."""
  with self.lock:
   need(not self.closed and self.failure is None,'CLOSED_OR_FAILED_NO_RETRY')
   need(type(request)is dict and set(request)=={'version','token','sequence','context','op','path','payloadBase64','expectedOffset'},'EXACT_REQUEST_FIELDS')
   need(type(request['version'])is int and request['version']==1 and type(request['token'])is str and secrets.compare_digest(request['token'],self.token),'VERSION_TOKEN')
   need(request['context']==self.context and type(request['context'])is dict,'CONTEXT')
   need(type(request['sequence'])is int and request['sequence']==self.sequence+1 and request['sequence']<=MAX_WRITES,'CONTIGUOUS_SEQUENCE')
   name=request['path'];need(type(name)is str and len(name)<=160 and re.fullmatch(r'(journal|state|media|reports)/[A-Za-z0-9_.-]{1,96}',name)is not None and '..'not in Path(name).parts,'DECLARED_PATH')
   if request['op']in('clock-proof','native-registration','raw-export','flight-interval','native-closed-inputs'):
    return self._readonly_proof(request,received_ns=received_ns)
   lane=name.split('/')[0];need(request['op']in('append','exclusive')and type(request['expectedOffset'])is int and 0<=request['expectedOffset']<=CAPS[lane],'OP_OFFSET')
   raw=request['payloadBase64'];need(type(raw)is str and len(raw)<=4*((MAX_PAYLOAD+2)//3),'BASE64_BOUND')
   payload=base64.b64decode(raw,validate=True);need(base64.b64encode(payload).decode()==raw and 0<len(payload)<=MAX_PAYLOAD,'CANONICAL_PAYLOAD_BOUND')
   target=self.root/name;need(not target.is_symlink(),'SYMLINK')
   offset=target.stat().st_size if target.exists()else 0
   need(offset==request['expectedOffset']and offset+len(payload)<=CAPS[lane],'EXPECTED_OFFSET_OR_FILE_CAP')
   need(request['op']=='append'or offset==0 and not target.exists(),'EXCLUSIVE_NO_OVERWRITE')
   # Product file writes are not Android STATUS or ADB command requests.
   # Existing owner byte/high-water/global caps govern this finite write stream.
   self.sequence=request['sequence'];self.last_commit_state=None;started=time.monotonic_ns();self.inflight={'sequence':self.sequence,'path':name,'offset':offset,'bytes':len(payload),'startedHostNs':started}
   try:
    result=self.budget.write(LANES[lane],target,payload,append=request['op']=='append')
    self.last_commit_state=True;self.committed_files[name]={'bytes':offset+len(payload),'writeSequence':result['writeSequence']}
    ref={'path':str(target.relative_to(self.budget.evidence)),'offset':offset,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'writeSequence':result['writeSequence']}
    # Late committed writes remain committed and must never be replayed.
    late=time.monotonic_ns()-started>RPC_NS
    if late:self.failure=TimeoutError('PRODUCT_WRITER_COMMITTED_AFTER200MS_NO_RETRY')
    return {'version':1,'sequence':self.sequence,'ok':not late,'committed':True,'ref':ref,'error':None if not late else str(self.failure)}
   except BaseException as error:
    self.failure=error
    try:self.budget.failure(error,detail={'productWriter':dict(self.inflight),'commitUnknown':True,'retryAllowed':False})
    except BaseException as storage:error.add_note('PRODUCT_WRITER_FAILURE_RECORD_UNDURABLE:'+str(storage)[:128])
    raise
   finally:self.inflight=None
 def committed_prefix(self,name):
  need(name=='journal/workspace.jsonl','ONLY_DECLARED_READONLY_WORKSPACE_PREFIX')
  if not self.lock.acquire(blocking=False):return None
  try:
   row=self.committed_files.get(name)
   if row is None:return None
   need(row['bytes']<=8*2**20,'WORKSPACE_PREFIX8M')
   with(self.root/name).open('rb')as f:raw=f.read(row['bytes'])
   need(len(raw)==row['bytes'],'WORKSPACE_COMMITTED_PREFIX_PRESENT');return(raw,dict(row))
  finally:self.lock.release()
 def register_native_probe(self,probe):
  from .product_types import is_product_probe
  need(is_product_probe(probe) and probe.latest is not None and probe.last_ref is not None and len(self.native_registrations)<2,'BOUNDED_GENUINE_PRIVILEGED_NATIVE_REGISTRATION')
  from .once_reader import read_ref
  if self.native_registration is not None:need(probe.probe_generation==2 and probe.rollover is not None and self.native_registration['processEpoch']==probe.rollover['previousProcessEpoch']and self.native_registration['keyId']==probe.rollover['previousKeyId']and probe.rollover['previousObservationRef']is not None,'EXACT_SOURCE_PLANNED_ROLLOVER_NOT_RECONNECT')
  else:need(probe.probe_generation==1,'FIRST_REGISTRATION_GENERATION1')
  snapshot=probe.latest;need(type(probe._latest_validated_raw)is bytes and encoded(snapshot).strip()==encoded(json.loads(probe._latest_validated_raw)).strip(),'IMMUTABLE_NATIVE_REGISTRATION_DTO')
  request_ref=probe.last_ref;original=json.loads(read_ref(probe.device.store.root,request_ref),object_pairs_hook=unique)
  need(original['requestNonce']==snapshot['requestNonce']and original['sourceSHA256']==probe.source and original['actualPID']==snapshot['pid']and original['APKSHA256']==probe.apk,'ORIGINAL_NATIVE_REGISTRATION_RECEIPT')
  inp=snapshot['input'];der=base64.b64decode(inp['producerPublicKeyX509Base64'],validate=True)
  if self.native_registration is not None:need(snapshot['processEpoch']!=self.native_registration['processEpoch']and inp['producerKeyId']!=self.native_registration['keyId']and inp.get('configured')is False and inp.get('pending')is False,'ROLLOVER_DISTINCT_EPHEMERAL_KEY_AND_NO_AUTHORITY_RESTORE')
  need(len(der)==91 and der.startswith(bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d03010703420004'))and hashlib.sha256(der).hexdigest()==inp['producerKeyId']and inp['producerSignatureAlgorithm']=='SHA256withECDSA','NATIVE_P256_SPKI_ORIGINAL')
  value={'format':'aeris-root-native-producer-registration','version':1,'context':dict(self.context),'sourceSHA256':probe.source,'APKSHA256':probe.apk,'pid':snapshot['pid'],'processEpoch':snapshot['processEpoch'],'publicKeyX509Base64':inp['producerPublicKeyX509Base64'],'keyId':inp['producerKeyId'],'signatureAlgorithm':'SHA256withECDSA','identityScope':'EPHEMERAL_SIM_PROCESS_NOT_PHYSICAL_HID_ATTESTATION','originalStoreRoot':str(probe.device.store.root),'originalObservationRef':request_ref,'authorityGranted':False,'generation':probe.probe_generation,'priorRegistrationRef':self.native_registration['rootRegistrationRef']if self.native_registration else None,'rolloverSourceRef':probe.rollover['sourceReceiptRef']if probe.rollover else None}
  if probe.manifest['native'].get('package')=='vn.rtr.aeris.betasim09':
   from .product_native09 import verify_application_original
   application=verify_application_original(probe.device.store.root,probe.application_domain_ref,probe.manifest);value['applicationId']=application['applicationId'];value['applicationDomainRef']=probe.application_domain_ref
  raw=encoded(value);path=self.budget.evidence/'reports'/('native-producer-%02d-registration.json'%self.case_index if probe.probe_generation==1 else'native-producer-%02d-registration-g02.json'%self.case_index);receipt=self.budget.write('external_task',path,raw)
  self.native_registration={**value,'rootRegistrationRef':{'path':str(path.relative_to(self.budget.evidence)),'offset':0,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'writeSequence':receipt['writeSequence']}};self.native_registrations.append(dict(self.native_registration));return self.native_registration
 def register_closed_native(self,probe):
  from .product_types import is_product_probe
  from .once_reader import read_ref
  need(is_product_probe(probe) and probe.closed_export is not None and probe.closed_snapshot is not None and self.native_closed_inputs is None,'ONE_GENUINE_CLOSED_NATIVE_INPUT_DESCRIPTOR');generations=[]
  sources=[*probe.archived_lifecycles,{'snapshot':probe.closed_snapshot,'lastObservationRef':probe.closed_snapshot_ref}]
  for ordinal,item in enumerate(sources,1):
   snapshot=item['snapshot'];observation=json.loads(read_ref(probe.device.store.root,item['lastObservationRef']),object_pairs_hook=unique);raw=read_ref(probe.device.store.root,observation['snapshotRef']);original=json.loads(raw,object_pairs_hook=unique);need(original==snapshot,'CLOSED_NATIVE_EXACT_ORIGINAL_SNAPSHOT');hits=[r for r in self.native_registrations if r['processEpoch']==snapshot['processEpoch']and r['keyId']==snapshot['input']['producerKeyId']];need(len(hits)==1,'CLOSED_NATIVE_ONE_PRIVILEGED_REGISTRATION');r=hits[0];generations.append({'probeGeneration':ordinal,'processEpoch':snapshot['processEpoch'],'pid':snapshot['pid'],'journalGeneration':snapshot['input']['journal']['generation'],'keyId':r['keyId'],'publicKeyX509Base64':r['publicKeyX509Base64'],'signatureAlgorithm':r['signatureAlgorithm'],'sourceSHA256':r['sourceSHA256'],'APKSHA256':r['APKSHA256'],'originalStoreRoot':str(probe.device.store.root),'originalObservationRef':item['lastObservationRef'],'snapshotOriginalRef':observation['snapshotRef'],'registrationRootRef':r['rootRegistrationRef'],'journalStatus':snapshot['input']['journal']})
  tar=probe.closed_export['export'];need(Path(tar['path']).is_file()and Path(tar['path']).stat().st_size==tar['bytes'],'CLOSED_NATIVE_ORIGINAL_TAR_PRESENT');value={'format':'aeris-root-closed-native-inputs','version':1,'context':dict(self.context),'candidateSHA256':hashlib.sha256(__import__('aeris_runtime.candidate',fromlist=['canonical']).canonical(probe.manifest)).hexdigest(),'tar':{'path':tar['path'],'bytes':tar['bytes'],'sha256':tar['sha256']},'generations':generations,'allSelectedGenerationsRequired':True,'unselectedHistoricalScope':'ORIGINAL_BYTES_PRESERVED_NO_CURRENT_AUTHORITY_CREDIT','authorityRestorable':False};raw=encoded(value);need(len(raw)<=16384,'CLOSED_NATIVE_DESCRIPTOR16K');path=self.budget.evidence/'reports'/('native-closed-inputs-%02d.json'%self.case_index);receipt=self.budget.write('external_task',path,raw);self.native_closed_inputs={'descriptorPath':str(path),'descriptorSHA256':hashlib.sha256(raw).hexdigest(),'descriptorBytes':len(raw),'context':dict(self.context),'originalWriteSequence':receipt['writeSequence'],'authorityRestorable':False};return dict(self.native_closed_inputs)
 def register_closed_raw(self,resources,native_probe):
  need(not self.raw_export_attempted and self.raw_export is None and not self.closed and not self.ending,'ONE_CLOSED_RAW_EXPORT_NO_RETRY');self.raw_export_attempted=True
  from .raw_export import prepare_export
  try:self.raw_export=prepare_export(self.budget,resources,self.context,native_probe,check_live=self.delivery_check);return dict(self.raw_export)
  except BaseException as error:self.failure=error;raise
 def _readonly_proof(self,request,*,received_ns):
  need(request['expectedOffset']==0 and type(request['expectedOffset'])is int,'PROOF_ZERO_OFFSET')
  data=base64.b64decode(request['payloadBase64'],validate=True);need(len(data)<=1024 and base64.b64encode(data).decode()==request['payloadBase64'],'PROOF_PAYLOAD')
  body=json.loads(data,object_pairs_hook=unique);need(type(body)is dict and type(body.get('challenge'))is str and re.fullmatch('[a-f0-9]{32}',body['challenge'])is not None,'PROOF_CHALLENGE')
  op=request['op'];need(request['path']==('reports/clock-proof'if op=='clock-proof'else'reports/native-registration'if op=='native-registration'else'reports/raw-export'if op=='raw-export'else'reports/flight-interval'if op=='flight-interval'else'reports/native-closed-inputs'),'PROOF_FIXED_PATH')
  if op=='clock-proof':need(set(body)=={'challenge','nodeSentNs'}and type(body['nodeSentNs'])is str and re.fullmatch('[0-9]{1,19}',body['nodeSentNs'])is not None and int(body['nodeSentNs'])<2**63,'NODE_CLOCK_INTEGER_STRING')
  elif op=='native-registration':need(set(body)=={'challenge'}and self.native_registration is not None,'SOURCE_NATIVE_REGISTRATION_READY')
  elif op=='raw-export':need(set(body)=={'challenge'}and self.raw_export is not None,'GENUINE_SOURCE_CLOSED_RAW_EXPORT_READY')
  elif op=='native-closed-inputs':need(set(body)=={'challenge'}and self.native_closed_inputs is not None,'SOURCE_CLOSED_NATIVE_INPUTS_READY')
  else:need(set(body)=={'challenge','missionSHA256','run','boot'}and body['run']==self.context['run']and body['boot']==self.context['boot']and callable(self.flight_interval_source),'SOURCE_FLIGHT_INTERVAL_CONTEXT_READY')
  interval=self.flight_interval_source(body['missionSHA256'])if op=='flight-interval'else None
  self.sequence=request['sequence'];self.last_commit_state=None;entry=time.monotonic_ns()if received_ns is None else received_ns
  value={'format':'aeris-root-product-clock-proof','version':1,'sequence':self.sequence,'challenge':body['challenge'],'nodeSentNs':body.get('nodeSentNs'),'proofKind':op,'rootReceivedHostNs':entry,'rootPreparedHostNs':time.monotonic_ns(),'context':dict(self.context),'authorityGranted':False}
  if interval is not None:value['flightInterval']=interval
  path=self.budget.evidence/'reports/product-clock-proofs.jsonl';raw=encoded(value);offset=path.stat().st_size if path.exists()else 0
  try:committed=self.budget.write('external_task',path,raw,append=True);self.last_commit_state=True
  except BaseException as error:self.failure=error;raise
  ref={'path':str(path.relative_to(self.budget.evidence)),'offset':offset,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'writeSequence':committed['writeSequence']}
  result={'version':1,'sequence':self.sequence,'ok':True,'committed':True,'ref':ref,'error':None}
  if op=='clock-proof':result['clock']=value
  elif op=='native-registration':
   inline=('format','version','context','sourceSHA256','pid','processEpoch','publicKeyX509Base64','keyId','authorityGranted','generation','priorRegistrationRef','rolloverSourceRef','rootRegistrationRef','originalObservationRef');result['nativeRegistration']={**{k:self.native_registration[k]for k in inline},'challenge':body['challenge']}
  elif op=='raw-export':result['rawExport']={**self.raw_export,'challenge':body['challenge']}
  elif op=='native-closed-inputs':result['nativeClosedInputs']={**self.native_closed_inputs,'challenge':body['challenge']}
  else:result['flightInterval']={**interval,'challenge':body['challenge'],'context':dict(self.context)}
  return result
 def start(self):
  need(self.server is None and self.thread is None and not self.closed,'ONE_START')
  if not self.budget.mock:self.budget.require_real_actor()
  # Unit mocks may dispatch directly; socket tests use only this owned Unix
  # namespace. No network-facing listener or operating aircraft is reachable.
  path=self.socket_path;self.budget.prepare_directory('external_task',path.parent);self.budget.charge_ephemeral_socket('external_task',path)
  self.server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.server.bind(str(path));os.chmod(path,0o600);self.server.listen(2);self.server.settimeout(.05)
  self.thread=threading.Thread(target=self._serve,name='aeris-product-writer',daemon=False);self.thread.start();return self.descriptor()
 def _exact(self,conn,n,end):
  out=bytearray()
  while len(out)<n:
   need(time.monotonic_ns()<end,'RPC200MS');part=conn.recv(n-len(out));need(bool(part),'PARTIAL_FRAME_EOF');out.extend(part)
  return bytes(out)
 def _scene(self,request):
  need(type(request)is dict and set(request)=={'version','token','sequence','context','op','path','payloadBase64','expectedOffset'}and type(request['version'])is int and request['version']==1 and request['token']==self.token and request['context']==self.context,'SCENE_PRIVATE_CONTEXT')
  need(request['op']=='scene-frame'and request['path']=='reports/scene-frame'and type(request['expectedOffset'])is int and request['expectedOffset']==0 and type(request['sequence'])is int and request['sequence']==self.observer_sequence+1 and request['sequence']<=MAX_WRITES,'SCENE_READONLY_SEQUENCE')
  raw=base64.b64decode(request['payloadBase64'],validate=True);body=json.loads(raw,object_pairs_hook=unique);need(len(raw)<=128 and type(body)is dict and set(body)=={'challenge'}and type(body['challenge'])is str and re.fullmatch('[a-f0-9]{32}',body['challenge'])is not None,'SCENE_READONLY_CHALLENGE')
  self.observer_sequence=request['sequence']
  value=self.scene_source.snapshot()if self.scene_source is not None else{'available':False,'failure':'SCENE_NOT_ATTACHED','flightAuthority':False,'rootNowNs':str(time.monotonic_ns())}
  return {'version':1,'sequence':self.observer_sequence,'ok':True,'committed':False,'readonly':True,'ref':None,'scene':value,'challenge':body['challenge'],'error':None}
 def _serve(self):
  try:
   while not self.stop.is_set():
    try:conn,_=self.server.accept()
    except socket.timeout:continue
    except OSError:
     if self.stop.is_set():return
     raise
    with self.role_lock:
     self.workers=[w for w in self.workers if w.is_alive()]
     if len(self.workers)>=2:conn.close();continue
     self.connections.add(conn);worker=threading.Thread(target=self._serve_connection,args=(conn,),name='aeris-product-rpc-peer',daemon=False);self.workers.append(worker);worker.start()
  except BaseException as error:self.failure=self.failure or error
 def _serve_connection(self,conn):
  role=None
  try:
   with conn:
    conn.settimeout(.05)
    while not self.stop.is_set():
     attempted_data=False
     try:
      try:first=conn.recv(1)
      except socket.timeout:continue
      if not first:
       if not self.stop.is_set()and not self.ending:
        if role=='scene':self.observer_failure='SCENE_OBSERVER_CLIENT_EOF'
        else:self.failure=RuntimeError('PRODUCT_WRITER_UNEXPECTED_CLIENT_EOF')
       return
      end=time.monotonic_ns()+RPC_NS;header=first+self._exact(conn,3,end);length=struct.unpack('!I',header)[0];need(0<length<=MAX_REQUEST,'FRAME_BOUND');raw=self._exact(conn,length,end);received_ns=time.monotonic_ns();request=json.loads(raw,object_pairs_hook=unique)
      if role is None:
       need(type(request)is dict and request.get('token')==self.token and request.get('context')==self.context,'PRIVATE_ROLE_ENROLLMENT')
       proposed='scene'if request.get('op')=='scene-frame'else'data'
       with self.role_lock:
        need(proposed not in self.roles,'ONE_CONNECTION_PER_ROLE');self.roles[proposed]=conn;role=proposed
      if role=='scene':response=self._scene(request)
      else:
       need(request.get('op')!='scene-frame'and not self.ending,'DATA_ROLE_ADMISSION');self.requests+=1;need(self.requests<=MAX_WRITES,'SOURCE_WRITE_STREAM_BOUND');attempted_data=True;self.last_commit_state=False;response=self.dispatch(request,received_ns=received_ns)
     except BaseException as error:
      if role=='scene':self.observer_failure=type(error).__name__+':'+str(error)[:256]
      else:self.failure=self.failure or error
      response={'version':1,'sequence':self.observer_sequence if role=='scene'else self.sequence,'ok':False,'committed':self.last_commit_state if attempted_data else False,'retryAllowed':False,'ref':None,'error':type(error).__name__+':'+str(error)[:256]}
     body=encoded(response);need(len(body)<=MAX_REPLY,'REPLY_BOUND')
     try:conn.sendall(struct.pack('!I',len(body))+body)
     except BaseException as error:
      if role=='scene':self.observer_failure=type(error).__name__+':'+str(error)[:256]
      elif not self.ending:self.failure=self.failure or error
      return
     if role=='scene'and self.observer_failure is not None or role!='scene'and self.failure is not None:return
  except BaseException as error:
   if role=='scene':self.observer_failure=type(error).__name__+':'+str(error)[:256]
   elif not self.ending:self.failure=self.failure or error
  finally:
   with self.role_lock:
    self.connections.discard(conn)
    if role is not None and self.roles.get(role)is conn:del self.roles[role]
 def begin_close(self):
  self.ending=True
  return {'commandAdmissionClosed':True,'lastDataSequence':self.sequence,'inflight':None if self.inflight is None else dict(self.inflight),'flightAcceptance':False}
 def check(self):
  need(not self.closed and self.server is not None and self.thread is not None,'NOT_STARTED_OR_CLOSED')
  if self.failure is not None:raise self.failure
  need(self.thread.is_alive(),'WORKER_DEAD')
  if self.inflight is not None:need(0<=time.monotonic_ns()-self.inflight['startedHostNs']<=RPC_NS,'INFLIGHT200MS')
  return {'alive':True,'sequence':self.sequence,'authorityGranted':False}
 def close(self):
  if self.closed:return {'closed':True,'failure':None if self.failure is None else str(self.failure),'sequence':self.sequence,'flightAcceptance':False}
  self.begin_close();self.stop.set()
  if self.server is not None:self.server.close()
  if self.thread is not None:self.thread.join(timeout=.6)
  for worker in list(self.workers):worker.join(timeout=.6)
  need((self.thread is None or not self.thread.is_alive())and all(not w.is_alive()for w in self.workers),'THREAD_STILL_ALIVE')
  need(self.inflight is None,'INFLIGHT_WRITE_UNKNOWN')
  path=self.socket_path
  if path.exists():path.unlink()
  self.closed=True
  return {'closed':True,'failure':None if self.failure is None else str(self.failure),'sequence':self.sequence,'observerSequence':self.observer_sequence,'observerFailure':self.observer_failure,'allRoleThreadsStopped':True,'threadStopped':True,'flightAcceptance':False,'authorityRestored':False}
