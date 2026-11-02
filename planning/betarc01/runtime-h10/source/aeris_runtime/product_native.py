"""Source-bound read-only Android product observation; never grants authority."""
import hashlib,json,re,secrets,time
from .android import AndroidDevice
from .once_reader import read_ref,unique
PACKAGE='vn.rtr.aeris.mission';TAG='AERIS_PRODUCT_STATUS'
def need(value,name):
 if not value:raise ValueError('PRODUCT_NATIVE_'+name)
class ProductNativeProbe:
 def __init__(self,device,manifest,*,now=time.monotonic_ns):
  need(type(device)is AndroidDevice and device.observer.tag==TAG,'EXACT_PRODUCT_DEVICE')
  self.device=device;self.manifest=manifest;self.source=manifest['native']['sourceSHA256'];self.apk=manifest['native']['APK_SHA256'];self.now=now;self.latest=None;self.requests=0;self.process_epoch=None;self.pid=None;self.last_ref=None;self._latest_validated_raw=None;self.closed_export=None;self.closed_snapshot=None;self.closed_snapshot_ref=None;self.probe_generation=1;self.rollover=None;self.archived_lifecycles=[]
 def prepare_rollover(self,*,deadline_ns):
  """Root-only planned transition AFTER public force-stop; never EOF recovery."""
  need(self.probe_generation==1 and self.rollover is None and self.latest is not None and self.last_ref is not None and self.closed_export is None,'ONE_PLANNED_RESTART_NO_EXPORT_OR_RETRY');self.device._check_budget_actor();absence=self.device._cold_absence(deadline_ns);path_ref,sha_ref=self.device._installed_sha(self.apk,deadline_ns);old={'processEpoch':self.process_epoch,'pid':self.pid,'keyId':self.latest['input']['producerKeyId'],'lastObservationRef':self.last_ref,'snapshot':self.latest,'originalSnapshotSHA256':hashlib.sha256(self._latest_validated_raw).hexdigest()};value={'format':'aeris-product-native-planned-rollover','version':1,'previousProbeGeneration':1,'nextProbeGeneration':2,'previousProcessEpoch':self.process_epoch,'previousPID':self.pid,'previousKeyId':old['keyId'],'previousObservationRef':self.last_ref,'previousSnapshotSHA256':old['originalSnapshotSHA256'],'coldAbsenceCommandRef':absence,'installedPathRef':path_ref,'installedSHARef':sha_ref,'sourceSHA256':self.source,'APKSHA256':self.apk,'oldInputOutcome':'UNKNOWN_UNTIL_COLD_AJ02_REPLAY','authorityRestorable':False};ref=self.device.store.receipt('product-planned-rollover.json',value);self.rollover={**value,'sourceReceiptRef':ref};self.archived_lifecycles.append(old);self.probe_generation=2;self.process_epoch=None;self.pid=None;self.latest=None;self.last_ref=None;self._latest_validated_raw=None;return dict(self.rollover)
 def install_selected(self,candidate,digest,*,deadline_ns):
  from .candidate import load,sha
  from pathlib import Path
  import tarfile
  d=self.device;d._check_budget_actor();need(d._android_ready is not None,'GENUINE_ANDROID_READY_BEFORE_INSTALL');need(d.observer.process is None,'INSTALL_BEFORE_OBSERVER');m=load(candidate,digest);need(m['native'].get('productKind')=='BETASIM_INTEGRATED','NEW_SOURCE_DEVELOPMENT_PRODUCT');apk=Path(candidate)/'native.apk'
  d.command(['shell','am','force-stop',PACKAGE],deadline_ns=deadline_ns);before=d._cold_absence(deadline_ns);loc=d.command(['shell','pm','path',PACKAGE],deadline_ns=deadline_ns).decode().strip();pathref=d.last_command_ref;need(loc.startswith('package:/')and'\n'not in loc,'EXISTING_ONE_PACKAGE_REQUIRED');old=d.command(['shell','sha256sum',loc[8:]],deadline_ns=deadline_ns).decode().split()[0];oldref=d.last_command_ref;need(old in('f459c7a90d714afc653985607df0c29587ae1cdc57a97359787b131ad6e31425',m['native']['APK_SHA256']),'ONLY_SOURCE_HELD_F459_OR_SAME_PRODUCT_PREDECESSOR')
  target=d.root.parent/'native-original-before-quarantine.tar'
  with d.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):backup=d._export_private(d.root.parent.name,target,deadline_ns=deadline_ns,full_original=True)
  need(backup['captureComplete']is True,'COLD_BACKUP_CAPTURE');names=set();logical=0
  with tarfile.open(target,'r:')as tar:
   for member in tar:
    need(len(names)<8192 and member.name not in names and(member.name=='files'or member.name.startswith('files/'))and'..'not in member.name.split('/')and not member.islnk()and not member.issym()and(member.isfile()or member.isdir())and not member.pax_headers,'COLD_BACKUP_SAFE_MEMBER_SET');names.add(member.name);logical+=member.size;need(logical<=512*2**20,'COLD_BACKUP_NATIVE512M')
  need('files'in names,'COLD_BACKUP_FULL_FILES');after=d._cold_absence(deadline_ns);d._installed_sha(old,deadline_ns);authorization={'format':'aeris-betasim-development-install-authorization','version':1,'candidateSHA256':digest,'APKSHA256':m['native']['APK_SHA256'],'APKPath':str(apk),'expectedOldAPKSHA256':old,'oldInstalledPathRef':pathref,'oldInstalledSHARef':oldref,'coldBeforeRef':before,'coldAfterBackupRef':after,'backup':backup,'allOriginalFilesRetained':True,'nativeFileMembers':len(names),'nativeLogicalBytes':logical,'noClearOrWipe':True};ref=d.store.receipt('product-install-authorization.json',authorization)
  if old!=m['native']['APK_SHA256']:
   d._install_authorization={'ref':ref,'APKPath':str(apk)}
   try:
    output=d.command(['install','-r',str(apk)],deadline_ns=deadline_ns);need(output.splitlines()and output.splitlines()[-1]==b'Success','EXACT_INSTALL_SUCCESS');install_ref=d.last_command_ref
   finally:d._install_authorization=None
  else:install_ref=None
  new_path,new_sha=d._installed_sha(m['native']['APK_SHA256'],deadline_ns);d._cold_absence(deadline_ns);return d.store.receipt('product-install-result.json',{'format':'aeris-betasim-development-install-result','version':1,'authorizationRef':ref,'installRef':install_ref,'newInstalledPathRef':new_path,'newInstalledSHARef':new_sha,'alreadySelected':old==m['native']['APK_SHA256'],'noClearOrWipe':True,'flightAcceptance':False})
 def start(self,*,deadline_ns):
  d=self.device;d._check_budget_actor()
  path=d.command(['shell','pm','path',PACKAGE],deadline_ns=deadline_ns,maximum_bytes=4096).decode().strip();path_ref=d.last_command_ref;need(path.startswith('package:/')and '\n'not in path,'ACTUAL_PACKAGE_PATH')
  digest=d.command(['shell','sha256sum',path[8:]],deadline_ns=deadline_ns,maximum_bytes=512).decode().split();sha_ref=d.last_command_ref;need(digest and digest[0]==self.apk,'INSTALLED_SELECTED_APK')
  d.command(['shell','am','start','-n',PACKAGE+'/.ProductActivity'],deadline_ns=deadline_ns,maximum_bytes=2048)
  d.store.receipt('product-start.json',{'format':'aeris-product-native-start','version':1,'sourceSHA256':self.source,'APKSHA256':self.apk,'installedPathRef':path_ref,'installedSHARef':sha_ref,'startCommandRef':d.last_command_ref,'readonlyStartupNotFlight':True,'probeGeneration':self.probe_generation,'rolloverSourceRef':self.rollover['sourceReceiptRef']if self.rollover else None})
  return self.status(deadline_ns=deadline_ns)
 def status(self,*,deadline_ns=None):
  d=self.device;d._check_budget_actor();need(self.requests<900,'STATUS900_COUNT');need(self.requests<240 and d.budget.snapshot()['counters']['requests']<240,'SELECTED_TASK_STATUS240_SOURCE_RESERVATION');global_status_ordinal=d.budget.tick('requests');self.requests+=1
  nonce=secrets.token_hex(16);sent=self.now();deadline=min(deadline_ns or sent+10_000_000_000,sent+10_000_000_000)
  with d.budget.operation({'requests':2048+8192}):
   with d.live_log(TAG,deadline_ns=deadline)as stream:
    d.command(['shell','am','broadcast','-a',PACKAGE+'.PRODUCT_STATUS','-n',PACKAGE+'/.ProductStatusReceiver','--es','requestNonce',nonce],deadline_ns=deadline,maximum_bytes=2048)
    broadcast_ref=d.last_command_ref
    ack=None
    for row in stream:
     if row.get('requestNonce')==nonce:ack=row;break
    need(type(ack)is dict,'ORIGINAL_NONCE_ACK');ack_ref=d.observer.last_ref
    expected='files/product-observations01/status-'+nonce+'.json';need(set(ack)=={'version','requestNonce','path','sha256','bytes','processEpoch','pid'}and type(ack['version'])is int and ack['version']==1 and ack['path']==expected and type(ack['bytes'])is int and 0<ack['bytes']<=16384,'EXACT_ACK_SCHEMA_PATH')
    actual_pid=d.pid(PACKAGE,deadline_ns=deadline);pid_ref=d.last_command_ref;raw=d.command(['shell','run-as',PACKAGE,'cat',expected],deadline_ns=deadline,maximum_bytes=16384);snapshot_ref=d.last_command['stdoutRef'];received=self.now()
    need(received<=deadline and len(raw)==ack['bytes']and hashlib.sha256(raw).hexdigest()==ack['sha256'],'ORIGINAL_ACK_DTO_SHA_AND10S')
    snapshot=json.loads(raw,object_pairs_hook=unique);validate(snapshot,ack,source=self.source,pid=actual_pid,nonce=nonce,protocol_sha=self.manifest['native'].get('productProtocolSHA256'))
    need(self.process_epoch is None or self.process_epoch==snapshot['processEpoch'],'RESTART_NEEDS_NEW_PROBE_LIFECYCLE')
    if self.probe_generation==2 and self.process_epoch is None:need(snapshot['processEpoch']!=self.rollover['previousProcessEpoch']and snapshot['input']['producerKeyId']!=self.rollover['previousKeyId']and snapshot['input']['configured']is False and snapshot['input']['pending']is False,'ROLLOVER_NEW_KEY_NO_AUTHORITY_RESTORE')
    if self.latest is not None:need(self.latest['input']['producerKeyId']==snapshot['input']['producerKeyId']and self.latest['input']['journal']['generation']==snapshot['input']['journal']['generation'],'NO_UNPLANNED_INPUT_ACTOR_OR_KEY_CHANGE')
    self.process_epoch=snapshot['processEpoch'];self.pid=actual_pid
    proof={'format':'aeris-product-native-observation','version':1,'sequence':self.requests,'requestNonce':nonce,'hostSentNs':sent,'hostReceivedNs':received,'barrierRef':d.last_barrier_ref,'barrierObservedHostNs':d.last_barrier_ns,'ACKRef':ack_ref,'snapshotRef':snapshot_ref,'actualPID':actual_pid,'actualPIDCommandRef':pid_ref,'broadcastCommandRef':broadcast_ref,'snapshotCommandRef':d.last_command_ref,'sourceSHA256':self.source,'APKSHA256':self.apk,'readonly':True,'authorityGranted':False,'probeGeneration':self.probe_generation,'globalStatusOrdinal':global_status_ordinal}
    self.last_ref=d.store.receipt('request-product-%05d.json'%self.requests,proof,owner='requests');self._latest_validated_raw=bytes(raw);self.latest=snapshot;return snapshot
 def saf_document(self,stream,index):
  from .saf_stream import capability
  return capability(self,stream,index)
 def export_closed(self,resources,*,deadline_ns):
  from .resources import OwnedResources
  need(type(resources)is OwnedResources and self.closed_export is None,'ONE_EXACT_SOURCE_CLOSED_EXPORT')
  need(resources.root.parent==self.device.root.parent,'SAME_SOURCE_CASE_NATIVE_EXPORT');snapshot=self.latest;need(snapshot is not None and snapshot['input'].get('closed')is True and snapshot['input'].get('pending')is False and snapshot['input'].get('configured')is False and snapshot['input'].get('failed')is False and snapshot['input'].get('journal',{}).get('durablyDrained')is True,'GENUINE_NATIVE_INPUT_CLOSED_AND_NO_PENDING_AUTHORITY')
  d=self.device;d._check_budget_actor()
  with d.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):export=d._export_private(self.device.root.parent.name,self.device.root.parent/'native-closed.tar',deadline_ns=deadline_ns,product_full_closed=True)
  need(export.get('captureComplete')is True,'FULL_NATIVE_FILES_CAPTURE_COMPLETE');proof=verify_input_tar(export,snapshot,[r['snapshot']for r in self.archived_lifecycles]);self.closed_export={'format':'aeris-product-native-closed-files','version':1,'export':export,'nativeObservationRef':self.last_ref,'processEpoch':self.process_epoch,'pid':self.pid,'sourceSHA256':self.source,'APKSHA256':self.apk,'journal':proof,'authorityRestorable':False};self.closed_snapshot=json.loads(json.dumps(snapshot));self.closed_snapshot_ref=self.last_ref;self.closed_export_ref=d.store.receipt('product-native-closed-export.json',{'format':'aeris-product-native-closed-files-capture','version':1,'tarPath':export['path'],'tarBytes':export['bytes'],'tarSHA256':export['sha256'],'captureReceiptRef':export.get('captureReceiptRef'),'nativeObservationRef':self.last_ref,'selectedGenerations':len(proof['generations']),'selectedJournalProofSHA256':hashlib.sha256(encoded(proof)).hexdigest(),'fullProofInOriginalRawManifest':True,'authorityRestorable':False});return dict(self.closed_export)
 def close(self):return self.device.close_observer()

def validate(snapshot,ack,*,source,pid,nonce,protocol_sha=None):
 need(type(ack)is dict and set(ack)=={'version','requestNonce','path','sha256','bytes','processEpoch','pid'}and type(ack.get('version'))is int and ack['version']==1 and type(ack.get('pid'))is int and type(ack.get('bytes'))is int and 0<ack['bytes']<=16384,'EXACT_ORIGINAL_ACK_TYPES')
 need(type(snapshot)is dict and set(snapshot)=={'format','version','requestNonce','observedElapsedNs','processEpoch','pid','package','sourceSHA256','sourceIdentity','input','authorityRestorable','actualImages','inventory','workspaceNamespace','exportBudget','webGeometry'}and snapshot.get('format')=='aeris-betasim-native-status'and type(snapshot.get('version'))is int and snapshot['version']==1,'DTO_FORMAT')
 need(snapshot.get('requestNonce')==nonce and snapshot.get('sourceSHA256')==source and snapshot.get('package')==PACKAGE and type(snapshot.get('pid'))is int and snapshot['pid']==pid==ack['pid'],'DTO_SOURCE_PID_NONCE')
 need(type(snapshot.get('processEpoch'))is str and re.fullmatch('[a-f0-9]{32}',snapshot['processEpoch'])is not None and snapshot['processEpoch']==ack['processEpoch'],'DTO_PROCESS_EPOCH')
 need(type(snapshot.get('observedElapsedNs'))is int and snapshot['observedElapsedNs']>=0 and snapshot.get('authorityRestorable')is False and snapshot.get('actualImages')==0 and type(snapshot.get('actualImages'))is int,'DTO_CLOCK_NO_REAL_MEDIA_AUTHORITY')
 identity=snapshot.get('sourceIdentity');need(type(identity)is dict and identity.get('sourceSHA256')==source and identity.get('package')==PACKAGE and identity.get('production')is False and identity.get('format')=='aeris-betasim-product-source-identity','DTO_PACKAGED_IDENTITY')
 if protocol_sha is not None:need(identity.get('productProtocolSHA256')==protocol_sha,'DTO_SELECTED_PRODUCT_PROTOCOL')
 inv=snapshot.get('inventory');need(type(inv)is dict and inv.get('scope')in('PRIVATE_FILES_ONLY_NOT_WHOLE_APP_DATA_DIR','WHOLE_APP_DATA_DIR')and all(type(inv.get(k))is int and inv[k]>=0 for k in('logicalBytes','allocatedBytes','entries'))and inv.get('measuredBeforeOwnSnapshotWrite')is True,'DTO_INVENTORY_SCOPE_NUMBERS')
 # Partial files observations are never promoted into whole-app quota facts.
 export=snapshot.get('exportBudget');need(type(export)is dict and type(export.get('reservedBytes'))is int and 0<=export['reservedBytes']<=192*2**20 and export.get('capBytes')==192*2**20 and export.get('unknownWriteRefunded')is False,'DTO_EXPORT_CAP_RESERVATIONS')
 inp=snapshot.get('input');need(type(inp)is dict and inp.get('authorityRestorable')is False and inp.get('processEpoch')==snapshot['processEpoch']and all(type(inp.get(k))is bool for k in('foreground','configured','closed','failed','pending'))and type(inp.get('sequence'))is int and inp['sequence']>=0,'DTO_READONLY_INPUT_STATE')
 public=inp.get('producerPublicKeyX509Base64');need(type(public)is str and len(public)<=256 and inp.get('producerSignatureAlgorithm')=='SHA256withECDSA'and inp.get('producerIdentityScope')=='EPHEMERAL_SIM_PROCESS_NOT_PHYSICAL_HID_ATTESTATION','DTO_SIGNED_NATIVE_PRODUCER_SCOPE')
 import base64
 der=base64.b64decode(public,validate=True);need(len(der)==91 and der.startswith(bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d03010703420004'))and hashlib.sha256(der).hexdigest()==inp.get('producerKeyId'),'DTO_ORIGINAL_P256_KEY_FINGERPRINT')
 return snapshot


def verify_originals(root,manifest):
 """Independent cold byte joins; no live probe or cached summary is an oracle."""
 from .once_reader import read_receipts
 from .status15_reader import command,journal
 rows=read_receipts(root,'request');need(bool(rows),'ORIGINAL_OBSERVATIONS_REQUIRED');nonces=set();last_received=-1;epoch=None;result=[];last_global=0
 diagnostics=read_receipts(root,'diagnostic');starts=[r for r in diagnostics if r.get('format')=='aeris-product-native-start'];need(1<=len(starts)<=2,'BOUNDED_ORIGINAL_STARTS');start_by_generation={};source=manifest['native']['sourceSHA256'];apk=manifest['native']['APK_SHA256'];rollover=None
 for start in starts:
  generation=start.get('probeGeneration',1);need(generation in(1,2)and generation not in start_by_generation,'EXACT_START_GENERATION');start_by_generation[generation]=start;need(start['sourceSHA256']==source and start['APKSHA256']==apk,'SELECTED_START_IDENTITY')
  _,_,remote,path=command(root,start['installedPathRef']);need(remote==['pm','path',PACKAGE]and path.decode().strip().startswith('package:/'),'INSTALLED_PATH_ORIGINAL')
  _,_,remote,digest=command(root,start['installedSHARef']);need(remote==['sha256sum',path.decode().strip()[8:]]and digest.decode().split()[0]==apk,'INSTALLED_SHA_ORIGINAL')
  startcmd,_,remote,_=command(root,start['startCommandRef']);need(remote==['am','start','-n',PACKAGE+'/.ProductActivity'],'EXACT_PRODUCT_START')
  if generation==2:
   from .android import COLD_ABSENCE_SCRIPT
   rollover=json.loads(read_ref(root,start['rolloverSourceRef']),object_pairs_hook=unique);need(rollover.get('format')=='aeris-product-native-planned-rollover'and rollover.get('previousProbeGeneration')==1 and rollover.get('nextProbeGeneration')==2 and rollover.get('authorityRestorable')is False and rollover.get('sourceSHA256')==source and rollover.get('APKSHA256')==apk,'ORIGINAL_PLANNED_ROLLOVER_SOURCE')
   cold,_,remote,raw=command(root,rollover['coldAbsenceCommandRef']);need(remote==['sh','-c',COLD_ABSENCE_SCRIPT]and raw==b'ABSENT\n'and cold['endedHostNs']<=startcmd['startedHostNs'],'ORIGINAL_APP_COLD_BEFORE_PLANNED_RESTART')
 need(1 in start_by_generation,'FIRST_SOURCE_START_REQUIRED');last_snapshot=None;last_row=None;last_generation=1
 for i,row in enumerate(rows,1):
  need(row.get('format')=='aeris-product-native-observation'and row.get('version')==1 and row.get('sequence')==i and i<=900 and i<=240 and row.get('readonly')is True and row.get('authorityGranted')is False,'ORIGINAL_READONLY_OBSERVATION_SEQUENCE')
  need(type(row.get('globalStatusOrdinal'))is int and last_global<row['globalStatusOrdinal']<=240,'SHARED_TASK_STATUS240_ORIGINAL_ORDINAL');last_global=row['globalStatusOrdinal']
  nonce=row['requestNonce'];need(nonce not in nonces and re.fullmatch('[a-f0-9]{32}',nonce)is not None,'UNIQUE_ORIGINAL_NONCE');nonces.add(nonce)
  sent=row['hostSentNs'];received=row['hostReceivedNs'];need(type(sent)is int and type(received)is int and last_received<=sent<=row['barrierObservedHostNs']<=received and received-sent<=10_000_000_000,'ORIGINAL_STATUS10S_CLOCK');last_received=received
  need(row['sourceSHA256']==source and row['APKSHA256']==apk,'ORIGINAL_SELECTED_RELEASE')
  marker=read_ref(root,row['barrierRef']);need(re.fullmatch(rb'AERIS_OBSERVER_READY_[a-f0-9]{32}\n',marker)is not None,'ORIGINAL_SUBSCRIPTION_MARKER')
  broadcast,_,remote,_=command(root,row['broadcastCommandRef']);need(remote==['am','broadcast','-a',PACKAGE+'.PRODUCT_STATUS','-n',PACKAGE+'/.ProductStatusReceiver','--es','requestNonce',nonce]and sent<=broadcast['startedHostNs']<=broadcast['endedHostNs']<=received,'ORIGINAL_BROADCAST_NONCE')
  pidrow,_,remote,pidraw=command(root,row['actualPIDCommandRef']);need(remote==['pidof',PACKAGE]and pidraw.strip()==str(row['actualPID']).encode(),'ORIGINAL_ACTUAL_PID')
  snapshotrow,_,remote,raw=command(root,row['snapshotCommandRef']);need(remote==['run-as',PACKAGE,'cat','files/product-observations01/status-'+nonce+'.json']and snapshotrow['stdoutRef']==row['snapshotRef']and pidrow['endedHostNs']<=snapshotrow['startedHostNs']<=snapshotrow['endedHostNs']<=received,'ORIGINAL_IMMUTABLE_SNAPSHOT_READ')
  ackraw=read_ref(root,row['ACKRef']);ack=json.loads(ackraw,object_pairs_hook=unique);need(ack['requestNonce']==nonce and ack['sha256']==hashlib.sha256(raw).hexdigest()and ack['bytes']==len(raw),'ORIGINAL_LOG_ACK_SNAPSHOT_SHA')
  need(row['barrierRef']['path']==row['ACKRef']['path']=='ack-stream.raw'and row['barrierRef']['offset']<row['ACKRef']['offset'],'SAME_ORIGINAL_STREAM_CAUSALITY')
  snapshot=json.loads(raw,object_pairs_hook=unique);validate(snapshot,ack,source=source,pid=row['actualPID'],nonce=nonce,protocol_sha=manifest['native'].get('productProtocolSHA256'))
  generation=row.get('probeGeneration',1);need(generation in start_by_generation and generation in(last_generation,last_generation+1),'SOURCE_ORDERED_PROBE_GENERATIONS')
  if epoch is not None and epoch!=snapshot['processEpoch']:
   need(last_generation==1 and generation==2 and rollover is not None,'NO_UNPLANNED_PROCESS_CHANGE');previous=json.loads(read_ref(root,rollover['previousObservationRef']),object_pairs_hook=unique);need(previous==last_row and rollover['previousProcessEpoch']==epoch and rollover['previousKeyId']==last_snapshot['input']['producerKeyId']and snapshot['input']['producerKeyId']!=rollover['previousKeyId']and snapshot['input']['configured']is False and snapshot['input']['pending']is False,'ORIGINAL_PRIOR_PROCESS_AND_NEW_KEY_NO_AUTHORITY_RESTORE');need(hashlib.sha256(read_ref(root,last_row['snapshotRef'])).hexdigest()==rollover['previousSnapshotSHA256'],'ORIGINAL_PREDEATH_SNAPSHOT_SHA');cold,_,_,_=command(root,rollover['coldAbsenceCommandRef']);need(last_row['hostReceivedNs']<=cold['startedHostNs'],'PREDEATH_OBSERVATION_BEFORE_COLD_ABSENCE')
  else:
   need(generation==last_generation,'NO_GENERATION_CHANGE_WITH_SAME_PROCESS')
   if last_snapshot is not None:need(last_snapshot['input']['producerKeyId']==snapshot['input']['producerKeyId']and last_snapshot['input']['journal']['generation']==snapshot['input']['journal']['generation'],'NO_UNPLANNED_ORIGINAL_INPUT_ACTOR_CHANGE')
  epoch=snapshot['processEpoch'];last_generation=generation;last_snapshot=snapshot;last_row=row;result.append({'requestNonce':nonce,'pid':snapshot['pid'],'processEpoch':epoch,'probeGeneration':generation,'scope':snapshot['inventory']['scope'],'authorityGranted':False})
 return {'status':'ORIGINAL_PRODUCT_NATIVE_OBSERVATIONS_VERIFIED_NOT_FLIGHT_ACCEPTANCE','count':len(result),'observations':result,'flightAcceptance':False}

def decode_aj02(found,key_id,*,snapshot_journal=None,require_closed=True):
 import struct
 magic=b'AERIS_INPUT_JOURNAL_V2\n';need(found.startswith(magic)and len(found)<=32*2**20,'COMPLETE_AJ02_NATIVE_INPUT_FILE');head='0'*64;seq=0;last=-1;offset=len(magic);pending=None;envelopes=0;prefix=None
 if snapshot_journal is not None and snapshot_journal.get('sequence')==0:prefix={'sequence':0,'bytes':len(magic),'head':head}
 while offset<len(found):
  need(offset+4<=len(found),'AJ02_TORN_PREFIX');n=struct.unpack_from('!I',found,offset)[0];need(82<=n<=2581 and offset+4+n<=len(found),'AJ02_RECORD_BOUND_OR_TORN');body=found[offset+4:offset+4+n-32];h=found[offset+4+n-32:offset+4+n].hex();number,elapsed=struct.unpack_from('!QQ',body);kind=body[16];previous=body[17:49].hex();payload=body[49:];seq+=1
  need(seq<=24576 and number==seq and elapsed>=last and previous==head and hashlib.sha256(body).hexdigest()==h,'AJ02_SEQUENCE_CLOCK_OR_CHAIN');need(kind==1 and pending is None and len(payload)<=2500 or kind==2 and pending is not None and len(payload)<=16,'AJ02_INTENT_OUTCOME_PAIR_ORDER')
  if kind==1:
   q=json.loads(payload,object_pairs_hook=unique);need(q.get('format')=='aeris-native-input-signed-envelope'and q.get('version')==1 and q.get('keyId')==key_id,'AJ02_SIGNED_ENVELOPE_KEY_SCOPE');pending=seq;envelopes+=1
  else:need(re.fullmatch(rb'[1-5][0-9]{2}',payload)is not None,'AJ02_HTTP_OUTCOME_BYTES');pending=None
  head=h;last=elapsed;offset+=4+n
  if snapshot_journal is not None and snapshot_journal.get('sequence')==seq:prefix={'sequence':seq,'bytes':offset,'head':head}
 if snapshot_journal is not None:
  j=snapshot_journal;need(j.get('format')=='AERIS_INPUT_JOURNAL_AJ02'and prefix is not None and j.get('bytes')==prefix['bytes']and j.get('head')==prefix['head'],'SOURCE_STATUS_TO_COLD_AJ02_PREFIX')
  if require_closed:need(j.get('closed')is True and j.get('failed')is False and j.get('durablyDrained')is True and j.get('sequence')==seq and j.get('pendingOutcome')is(pending is not None),'NATIVE_STATUS_TO_COLD_ORIGINAL_AJ02_JOURNAL')
 return {'bytes':len(found),'sha256':hashlib.sha256(found).hexdigest(),'sequence':seq,'head':head,'sourceClosedStatusBound':require_closed,'unresolvedIntentSequence':pending,'signedEnvelopeCount':envelopes,'signedPayloadSemanticsNotYetIndependentlyVerified':True,'sourceObservedPrefix':prefix}

def verify_input_tar(export,snapshot,historical_snapshots=()):
 import tarfile
 path=__import__('pathlib').Path(export['path']);need(path.stat().st_size==export['bytes']and __import__('aeris_runtime.candidate',fromlist=['sha']).sha(path)==export['sha256'],'FULL_NATIVE_TAR_SHA');registered={}
 for q in[*historical_snapshots,snapshot]:
  generation=q['input']['journal'].get('generation');need(type(generation)is str and re.fullmatch('[a-f0-9]{32}',generation)is not None and generation not in registered,'ORIGINAL_UNIQUE_AJ02_GENERATION');registered[generation]=q
 need(len(registered)<=2,'SELECTED_SOURCE_GENERATIONS2');found={};count=0;logical=0;names=set();historical=[];journal_count=0;journal_bytes=0
 with tarfile.open(path,'r:')as tar:
  for member in tar:
   count+=1;need(count<=8192 and member.name not in names and not member.issym()and not member.islnk()and not member.pax_headers and not member.name.startswith('/')and'..'not in member.name.split('/')and(member.isdir()or member.isfile()),'TAR_MEMBER_DOMAIN');names.add(member.name);logical+=member.size;need(logical<=512*2**20,'TAR_NATIVE512M_LOGICAL')
   match=re.fullmatch(r'files/product-input01/([a-f0-9]{32})\.aj02',member.name)
   if match:
    need(member.isfile()and member.size<=32*2**20,'INPUT_JOURNAL32M');journal_count+=1;journal_bytes+=member.size;need(journal_count<=8 and journal_bytes<=64*2**20,'ALL_NATIVE_AJ02_GENERATIONS8_TOTAL64M');generation=match[1];raw=tar.extractfile(member).read()
    if generation in registered:
     q=registered[generation];closed=q['input']['journal'].get('closed')is True and q['input']['journal'].get('durablyDrained')is True;r=decode_aj02(raw,q['input']['producerKeyId'],snapshot_journal=q['input']['journal'],require_closed=closed);found[generation]={'path':member.name,'generation':generation,'processEpoch':q['processEpoch'],'keyId':q['input']['producerKeyId'],**r}
    else:historical.append({'path':member.name,'bytes':member.size,'sha256':hashlib.sha256(raw).hexdigest(),'scope':'UNSELECTED_HISTORICAL_BYTES_PRESERVED_NO_CURRENT_AUTHORITY_OR_SIGNATURE_CREDIT'})
 need(set(found)==set(registered),'ALL_SELECTED_AJ02_GENERATIONS_PRESENT');current=found[snapshot['input']['journal']['generation']];need(current['sourceClosedStatusBound'],'CURRENT_SOURCE_NATIVE_INPUT_MUST_BE_CLOSED');return{**current,'generations':[found[g]for g in registered],'allSelectedGenerationsClosed':all(r['sourceClosedStatusBound']for r in found.values()),'anyUnresolvedIntent':any(r['unresolvedIntentSequence']is not None for r in found.values()),'unselectedHistoricalJournals':historical,'sourceTaskJournalGenerationScope':'EXACT_CURRENT_CASE_PRIVILEGED_REGISTRATIONS_NOT_ALL_PRIOR_APP_HISTORY'}
