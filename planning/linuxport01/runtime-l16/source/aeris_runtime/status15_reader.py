"""Cold STATUS15 original bytes and enrollment, independent of live channel."""
import hashlib,json,os,re,shlex,stat,struct
from pathlib import Path
from .once_reader import read_ref,read_receipts,unique
from .candidate import CERT
NAME='vn.rtr.aeris.mission.observe15'

def need(ok,name):
 if not ok:raise ValueError('COLD_STATUS15_'+name)

def journal(root,ref,kind):
 need(type(ref)is dict and ref.get('path')=='receipts/'+kind+'.jsonl'and ref.get('version')==3,'ORIGINAL_'+kind.upper()+'_JOURNAL')
 row=json.loads(read_ref(root,ref),object_pairs_hook=unique);need(sum(r==row for r in read_receipts(root,kind))==1,'ORIGINAL_ROW_MEMBERSHIP');return row

def command(root,ref):
 row=journal(root,ref,'command');need(row.get('version')==3 and row.get('captureComplete')is True and row.get('failure')is None and type(row.get('exit'))is int and row['exit']==0 and read_ref(root,row['stderrRef'])==b'','ACTUAL_COMMAND_SUCCESS')
 argv=json.loads(read_ref(root,row['argvRef']),object_pairs_hook=unique);need(type(argv)is list and len(argv)>=4 and argv[1]=='-s'and argv[2]=='emulator-5582','OWNED_ACTUAL_ADB_ARGV')
 remote=shlex.split(argv[4])if len(argv)==5 and argv[3]=='shell'else argv[3:]
 return row,argv,remote,read_ref(root,row['stdoutRef'])

def host_query(root,ref,port):
 path=Path(root).parent/'host-queries/queries.jsonl';need(type(ref)is dict and set(ref)=={'path','offset','bytes','sha256'}and ref['path']==str(path)and type(ref['offset'])is int and ref['offset']>=0 and type(ref['bytes'])is int and 0<ref['bytes']<=2048,'LISTENER_QUERY_REF')
 def original(path,offset,n,sha,cap):
  path=Path(path);need(not any(p.is_symlink()for p in[path,*path.parents])and path.parent==Path(root).parent/'host-queries','QUERY_ORIGINAL_PATH')
  fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
  try:
   st=os.fstat(fd);need(stat.S_ISREG(st.st_mode)and st.st_nlink==1 and 0<=offset<=st.st_size and 0<=n<=cap and offset+n<=st.st_size,'QUERY_ORIGINAL_BOUND')
   os.lseek(fd,offset,os.SEEK_SET);raw=os.read(fd,n);need(len(raw)==n and hashlib.sha256(raw).hexdigest()==sha,'QUERY_ORIGINAL_SHA');return raw
  finally:os.close(fd)
 raw=original(path,ref['offset'],ref['bytes'],ref['sha256'],2048);need(raw.endswith(b'\n')and b'\n'not in raw[:-1],'QUERY_WHOLE_JSON_ROW');q=json.loads(raw,object_pairs_hook=unique)
 expected=['/usr/sbin/lsof','-nP','-a','-iTCP:'+str(port),'-sTCP:LISTEN','-Fpcfn']
 need(q.get('format')=='aeris-host-query'and q.get('version')==3 and q.get('argv')==expected and q.get('exit')==0 and q.get('captureComplete')is True and q.get('failure')is None,'LISTENER_ACTUAL_QUERY')
 outputs={}
 for key,cap in [('stdoutRef',16384),('stderrRef',4096)]:
  r=q[key];need(type(r)is dict and set(r)=={'path','offset','bytes','sha256'}and r['path']==str(path.parent/'query-output.raw'),'QUERY_CAPTURE_REF');outputs[key]=original(r['path'],r['offset'],r['bytes'],r['sha256'],cap)
 need(outputs['stderrRef']==b'','LISTENER_QUERY_NO_STDERR');lines=outputs['stdoutRef'].decode('ascii').splitlines();names=[s[1:]for s in lines if s.startswith('n')];commands=[s[1:]for s in lines if s.startswith('c')];pids=[s[1:]for s in lines if s.startswith('p')]
 need(names and commands and all(s=='adb'for s in commands)and pids and all(re.fullmatch('[1-9][0-9]*',s)for s in pids),'LISTENER_ADB_PROCESS')
 need(all(s in('127.0.0.1:'+str(port),'[::1]:'+str(port),'localhost:'+str(port))for s in names),'LISTENER_LOOPBACK_ONLY')
 return {'row':q,'listenerNames':names,'ADBListenerPIDs':[int(v)for v in pids],'loopbackVerifiedFromOriginalQuery':True}

def channel(root,ref,source,requests,cache,expected_apk):
 need(type(expected_apk)is str and re.fullmatch('[a-f0-9]{64}',expected_apk)is not None,'EXPECTED_SELECTED_APK_REQUIRED')
 key=(ref['sha256'],expected_apk)
 if key in cache:return cache[key]
 p=journal(root,ref,'diagnostic');fields={'format','version','sourceSHA256','APKSHA256','serial','port','socketName','baselineRequestRef','PIDBeforeCommandRef','PIDAfterCommandRef','forwardCommandRef','mappingCommandRef','listenerQueryRef','installedPathCommandRef','installedSHACommandRef','helloRef','startedHostNs','readyHostNs','localPeer','hostLocalEndpoint','listener','authorityRestored','trust'}
 need(set(p)==(fields|{'plannedTransitionRef'}if p.get('version')==2 else fields)and p['format']=='aeris-status15-channel-open'and type(p['version'])is int and p['version']in(1,2) and p['sourceSHA256']==source and p['serial']=='emulator-5582'and p['socketName']==NAME and p['authorityRestored']is False and p['trust']=='LOCAL_ENGINEERING_ADB_ENROLLMENT_NOT_REMOTE_ATTESTATION','CHANNEL_SCHEMA')
 need(p['APKSHA256']==expected_apk,'EXACT_SELECTED_SIGNED_APK')
 port=p['port'];need(type(port)is int and 0<port<=65535 and p['localPeer']==['127.0.0.1',port]and type(p['hostLocalEndpoint'])is list and len(p['hostLocalEndpoint'])==2 and p['hostLocalEndpoint'][0]=='127.0.0.1','CHANNEL_LOOPBACK')
 baseline=journal(root,p['baselineRequestRef'],'request');need(baseline['version']==3 and baseline['action']=='STATUS'and baseline in requests,'ORIGINAL_LEGACY_ENROLLMENT')
 from .once_reader import _reconstruct_requests
 prefix=requests[:baseline['sequence']]
 if p['version']==1:
  need(baseline['context']is None and baseline['expectedContext']is None and all(x['version']==3 for x in prefix),'UNSELECTED_LEGACY_PREFIX_BEFORE_CHANNEL')
  b=_reconstruct_requests(root,prefix,source=source,version=3,maximum=900)[-1]
 else:
  need(type(baseline['context'])is dict and baseline['expectedContext']==baseline['context'],'PLANNED_SELECTED_BASELINE')
  b=_reconstruct_requests(root,prefix,source=source,expected_context=baseline['context'],expected_apk=expected_apk,version=4,maximum=900)[-1]
  transition=journal(root,p['plannedTransitionRef'],'diagnostic')
  fields={'format','version','oldChannelOpenRef','oldChannelCloseRef','beforeIdentity','oldBaselineRequestRef','bootstrapRequestRef','bootstrapRequestNonce','bootstrapSHA256','baselineRequestRef','context','sourceSHA256','authorityRestored','unexpectedEOFReconnect'}
  need(set(transition)==fields and transition['format']=='aeris-planned-bootstrap-status-transition'and type(transition['version'])is int and transition['version']==1 and transition['sourceSHA256']==source and transition['context']==baseline['context']and transition['baselineRequestRef']==p['baselineRequestRef']and transition['authorityRestored']is False and transition['unexpectedEOFReconnect']is False,'PLANNED_EXACT_TRANSACTION_SCHEMA')
  oldopen=journal(root,transition['oldChannelOpenRef'],'diagnostic');oldclose=journal(root,transition['oldChannelCloseRef'],'diagnostic');bootstrap=journal(root,transition['bootstrapRequestRef'],'request');oldbaseline=journal(root,transition['oldBaselineRequestRef'],'request')
  need(oldopen.get('version')==1 and oldclose.get('format')=='aeris-status15-channel-close'and oldclose.get('channelOpenRef')==transition['oldChannelOpenRef']and oldclose.get('captureComplete')is True and oldclose.get('drainComplete')is True and oldclose.get('failure')is None,'PLANNED_HEALTHY_PREVIOUS_CLOSE_NOT_EOF_RECOVERY')
  need(bootstrap in requests and oldbaseline in requests and bootstrap['action']=='BOOTSTRAP'and bootstrap['version']==3 and oldbaseline['action']=='STATUS'and oldbaseline.get('version')==4 and oldbaseline['context']is None and oldbaseline['sequence']+1==bootstrap['sequence']and bootstrap['sequence']+1==baseline['sequence']and bootstrap['request']['requestNonce']==transition['bootstrapRequestNonce'],'PLANNED_CONTIGUOUS_BOOTSTRAP_ORIGINAL_REQUESTS')
  ready=json.loads(read_ref(root,bootstrap['snapshotRef']),object_pairs_hook=unique)
  need(ready.get('context')==transition['context']and ready.get('lifecycle',{}).get('phase')=='READY'and ready.get('bootstrapSHA256')==transition['bootstrapSHA256']==b.get('bootstrapSHA256')and re.fullmatch('[a-f0-9]{64}',transition['bootstrapSHA256'])is not None,'PLANNED_ORIGINAL_READY_HASH_CONTEXT')
  identity={k:b[k]for k in('sourceSHA256','pid','processEpoch','viewEpoch')}
  need(identity==transition['beforeIdentity']and all(ready.get(k)==v for k,v in identity.items()),'PLANNED_SAME_ORIGINAL_PROCESS_SOURCE_VIEW')
  old_snapshot=json.loads(read_ref(root,oldbaseline['snapshotRef']),object_pairs_hook=unique)
  need(all(old_snapshot.get(k)==v for k,v in identity.items())and bootstrap['request']['processEpoch']==identity['processEpoch']and bootstrap['request']['viewEpoch']==identity['viewEpoch']and bootstrap['request']['baseRevision']==old_snapshot['revision'],'PLANNED_OLD_ORIGINAL_BASELINE_IDENTITY_AND_REVISION')
  for snapshot in(ready,b):
   state=snapshot['state'];native=state.get('native',{});inp=native.get('input',{})
   need(state.get('connectPending')is False and state.get('ownerActive')is False and state.get('authorityRestorable')is False and native.get('phase')=='NO_SESSION'and native.get('authorityRestorable')is False and native.get('flight',{}).get('armed')is not True and inp.get('consent')is not True and inp.get('leaseId')is None and native.get('rcOverrideActiveLocally')is not True,'PLANNED_NO_OWNER_ARM_INPUT')
  # The original old mapping removal must precede public BOOTSTRAP dispatch.
  removed,_,_,_=command(root,oldclose['mappingAfterRef']);need(removed['endedHostNs']<=bootstrap['hostSentNs']<=bootstrap['hostReceivedNs']<=baseline['hostSentNs'],'PLANNED_CLOSE_BOOTSTRAP_BASELINE_ORDER')
  _verify_channel_closure(root,oldopen,oldclose,expected_apk=expected_apk,source=source,allow_failed=False)
 need(b['state'].get('ownerActive')is False and b['state'].get('authorityRestorable')is False and b['state'].get('native',{}).get('flight',{}).get('armed')is not True,'UNARMED_NO_AUTHORITY_ENROLLMENT')
 before,argv,remote,out=command(root,p['PIDBeforeCommandRef']);need(remote==['pidof','vn.rtr.aeris.mission']and out.strip()==str(b['pid']).encode(),'ACTUAL_PID_BEFORE')
 after,argv2,remote,out=command(root,p['PIDAfterCommandRef']);need(argv2[:3]==argv[:3]and remote==['pidof','vn.rtr.aeris.mission']and out.strip()==str(b['pid']).encode(),'ACTUAL_PID_AFTER')
 forward,fargv,remote,out=command(root,p['forwardCommandRef']);need(fargv[:3]==argv[:3]and remote==['forward','--no-rebind','tcp:0','localabstract:'+NAME]and re.fullmatch(rb'[1-9][0-9]{0,4}\n?',out)is not None and int(out)==port,'ACTUAL_FORWARD_CREATE')
 mapping,margv,remote,out=command(root,p['mappingCommandRef']);expected='emulator-5582 tcp:'+str(port)+' localabstract:'+NAME;need(margv[:3]==argv[:3]and remote==['forward','--list']and [s for s in out.decode('ascii').splitlines()if s.split()[:2]==['emulator-5582','tcp:'+str(port)]]==[expected],'ACTUAL_FORWARD_MAPPING')
 installed,_,remote,out=command(root,p['installedPathCommandRef']);path=out.decode().strip();need(remote==['pm','path','vn.rtr.aeris.mission']and path.startswith('package:/')and '\n'not in path,'ACTUAL_INSTALLED_PACKAGE_PATH')
 digest,_,remote,out=command(root,p['installedSHACommandRef']);need(remote==['sha256sum',path[8:]]and out.decode().split()[0]==p['APKSHA256'],'ACTUAL_INSTALLED_APK_SHA')
 observed=host_query(root,p['listenerQueryRef'],port);q=observed.pop('row');need(p['listener']==observed,'LISTENER_PROJECTION_FROM_ORIGINAL')
 raw=read_ref(root,p['helloRef']);need(4<len(raw)<=2052 and struct.unpack('!I',raw[:4])[0]==len(raw)-4,'HELLO_ORIGINAL_FRAMING');h=json.loads(raw[4:],object_pairs_hook=unique)
 fields={'format','version','socketName','pid','sourceSHA256','processEpoch','viewEpoch','apkSHA256','certificateSHA256','appUid','peerUid','peerPid','debuggable','capabilities','authorityRestorable','localOnly'}
 need(type(h)is dict and set(h)==fields and h['format']=='aeris-observer15-hello'and type(h['version'])is int and h['version']==1 and h['socketName']==NAME and h['sourceSHA256']==source and h['apkSHA256']==p['APKSHA256']and h['certificateSHA256']==CERT,'HELLO_STRICT_APPLICATION_ASSERTIONS')
 need(type(h['pid'])is int and h['pid']==b['pid']and h['processEpoch']==b['processEpoch']and type(h['viewEpoch'])is int and h['viewEpoch']==b['viewEpoch']and type(h['appUid'])is int and h['appUid']>=10000 and type(h['peerUid'])is int and h['peerUid']in(0,2000)and type(h['peerPid'])is int and h['peerPid']>0,'HELLO_LEGACY_ENROLLMENT_AND_ENGINEERING_PEER')
 need(h['debuggable']is True and h['capabilities']==['STATUS']and h['authorityRestorable']is False and h['localOnly']is True,'HELLO_NO_OPERATIONAL_CAPABILITY')
 need(all(type(p[k])is int for k in('startedHostNs','readyHostNs'))and 0<=p['startedHostNs']<=before['startedHostNs']<=before['endedHostNs']<=forward['startedHostNs']<=forward['endedHostNs']<=mapping['startedHostNs']<=mapping['endedHostNs']<=q['startedHostNs']<=q['finishedHostNs']<=after['startedHostNs']<=after['endedHostNs']<=p['readyHostNs'],'CHANNEL_CAUSAL_ORIGINAL_ORDER')
 need(digest['endedHostNs']<=p['startedHostNs']and baseline['hostReceivedNs']<=p['startedHostNs']<=baseline['hostReceivedNs']+10_000_000_000,'INSTALLED_APK_AND_FRESH_LEGACY_ENROLLMENT')
 cache[key]=(p,h);return p,h

def verify_request(root,r,ack_raw,snapshot,source,requests,cache,*,expected_apk=None):
 ref=r['socketRef'];need(type(ref)is dict and ref.get('path')=='status15-wire.jsonl'and ref.get('version')==3 and 0<ref.get('bytes',0)<=4096,'ORIGINAL_EXCHANGE_JOURNAL');raw=read_ref(root,ref);p=json.loads(raw,object_pairs_hook=unique)
 fields={'format','version','channelOpenRef','sequence','requestWireRef','ackHeaderRef','socketACKRef','DTOHeaderRef','snapshotRef','timing','frameCompleteBeforeOwnPersistence','socketExchangeNotADBCommand'}
 need(set(p)==fields and p['format']=='aeris-status15-exchange'and type(p['version'])is int and p['version']==1 and type(p['sequence'])is int and 0<p['sequence']<=900 and p['snapshotRef']==r['snapshotRef']and p['frameCompleteBeforeOwnPersistence']is True and p['socketExchangeNotADBCommand']is True,'EXCHANGE_SCHEMA')
 c,h=channel(root,p['channelOpenRef'],source,requests,cache,expected_apk)
 request=read_ref(root,p['requestWireRef']);body=json.dumps({'version':1,'requestNonce':r['request']['requestNonce']},separators=(',',':')).encode();need(request==struct.pack('!I',len(body))+body,'ORIGINAL_TYPED_REQUEST_WIRE')
 wireack=read_ref(root,p['socketACKRef']);need(wireack==ack_raw and read_ref(root,p['ackHeaderRef'])==struct.pack('!I',len(ack_raw))and read_ref(root,p['DTOHeaderRef'])==struct.pack('!I',len(snapshot)),'SOCKET_ACK_EQUALS_ORIGINAL_LOG_AND_LENGTHS')
 need(r['actualPID']==h['pid']and r['sourceSHA256']==h['sourceSHA256']and json.loads(snapshot,object_pairs_hook=unique)['processEpoch']==h['processEpoch']and json.loads(snapshot,object_pairs_hook=unique)['viewEpoch']==h['viewEpoch'],'CURRENT_CHANNEL_PROCESS_VIEW')
 timing=p['timing'];codes=('entry','validated','reserved','sendStart','bytesSent','firstByte','frameComplete','ackJoined','validateStart','validateEnd','persistStart','payloadPersisted','requestPersisted','returnReady')
 need(type(timing)is dict and timing.get('codes')==list(codes)and timing.get('diagnosticNotSafetyProof')is True and timing.get('clockDomain')=='HOST_MONOTONIC_AND_CALLING_THREAD_CPU','SAME_HOST_DIAGNOSTIC_CLOCK')
 need(set(timing)=={'codes','points','fsync','clockDomain','nestedAndConcurrentWorkMayOverlap','ACKWorkerNotIncludedInThreadCPU','proofAndRequestReceiptSelfFsyncExcluded','measuredCut','diagnosticNotSafetyProof'}and timing['nestedAndConcurrentWorkMayOverlap']is True and timing['ACKWorkerNotIncludedInThreadCPU']is True and timing['proofAndRequestReceiptSelfFsyncExcluded']is True and timing['measuredCut']=='RESPONSE_BYTES_DURABLE_BEFORE_PROOF_AND_REQUEST_RECEIPT','DIAGNOSTIC_EXACT_PROJECTION_CUT')
 need(type(timing['fsync'])is dict and set(timing['fsync']).issubset({'payload_fsync','ledger_fsync'}),'FSYNC_CODES')
 for values in timing['fsync'].values():
  need(type(values)is list and len(values)==5 and all(type(v)is int and 0<=v<2**63 for v in values)and 0<values[0]<=1024 and values[2]<=values[1]and values[4]<=values[3],'FSYNC_TYPED_BOUNDED_AGGREGATE')
 points={};last=-1;last_cpu=-1
 for row in timing['points']:
  need(type(row)is list and len(row)==3 and all(type(v)is int and v>=0 for v in row)and row[0]<len(codes)and row[0]not in points and row[1]>=last and row[2]>=last_cpu,'TIMING_TYPED_MONOTONIC');points[row[0]]=row;last=row[1];last_cpu=row[2]
 need(set(points)==set(range(12))and c['readyHostNs']<=r['hostSentNs']<=points[3][1]<=points[4][1]<=points[5][1]<=points[6][1]<=points[7][1]<=r['hostReceivedNs']<=points[8][1]<=points[9][1]<=points[10][1]<=points[11][1],'FRAME_BEFORE_RESPONSE_PERSISTENCE')
 need(read_ref(root,r['barrierRef'])==('AERIS_OBSERVER_READY_'+r['request']['requestNonce']+'\n').encode(),'NATIVE_NONCE_MARKER_EXACT')
 return {'channel':p['channelOpenRef']['sha256'],'sequence':p['sequence']}

def verify_exchange_coverage(root,refs,*,allow_failed=False):
 path=Path(root)/'status15-wire.jsonl'
 if not path.exists():need(not refs,'WIRE_JOURNAL_MISSING');return
 fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));rows=[];failure_rows=[]
 try:
  before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_size<=900*4096,'WIRE_JOURNAL_SIZE_LINK')
  with os.fdopen(fd,'rb',closefd=False)as f:
   offset=0
   while True:
    raw=f.readline(4097)
    if not raw:break
    need(len(raw)<=4096 and raw.endswith(b'\n')and b'\n'not in raw[:-1],'WIRE_JOURNAL_WHOLE_ROW');value=json.loads(raw,object_pairs_hook=unique);key=(offset,len(raw),hashlib.sha256(raw).hexdigest())
    if value.get('format')=='aeris-status15-exchange':rows.append(key)
    elif value.get('format')=='aeris-status15-failed-prefix':failure_rows.append(key)
    else:raise ValueError('COLD_STATUS15_UNKNOWN_WIRE_PROOF')
    offset+=len(raw);need(len(rows)+len(failure_rows)<=900,'WIRE_JOURNAL900_ROWS')
  after=os.fstat(fd);need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'WIRE_CHANGED_DURING_COLD_READ')
 finally:os.close(fd)
 declared=[(r['offset'],r['bytes'],r['sha256'])for r in refs];need(len(set(declared))==len(declared),'WIRE_REFERENCE_REUSED')
 if allow_failed:need(rows[:len(declared)]==declared and len(rows)-len(declared)<=1 and len(failure_rows)<=1,'WIRE_FAILED_LAST_PREFIX_ONLY')
 else:need(rows==declared and not failure_rows,'WIRE_ORPHAN_MISSING_OR_FAILED_PROOF')

def _verify_channel_closure(root,c,p,*,expected_apk,source,allow_failed=False):
 """One original channel closure, independent of live object flags."""
 root=Path(root);diagnostics=read_receipts(root,'diagnostic')
 fields={'format','version','channelOpenRef','port','requests','EOFObserved','socketClosed','mappingBeforeRef','removeCommandRef','mappingAfterRef','forwardRemoved','tailRef','drainComplete','captureComplete','failure','authorityRestored','flightAcceptance'}
 need(set(p)==fields and type(p['version'])is int and p['version']==1 and type(p['port'])is int and type(p['requests'])is int and 0<=p['requests']<=900 and all(type(p[k])is bool for k in('EOFObserved','socketClosed','forwardRemoved','drainComplete','captureComplete','authorityRestored','flightAcceptance'))and(p['failure']is None or type(p['failure'])is str),'CLOSE_EXACT_TYPED_SCHEMA')
 wirepath=root/'status15-wire.jsonl';wire=[]
 if wirepath.exists():
  with wirepath.open('rb')as f:
   for line in f:
    need(len(line)<=4096 and line.endswith(b'\n'),'CLOSE_ORIGINAL_WIRE_ROW');wire.append(json.loads(line,object_pairs_hook=unique));need(len(wire)<=900,'CLOSE_WIRE900')
 successful=[r for r in wire if r.get('format')=='aeris-status15-exchange'and r.get('channelOpenRef')==p['channelOpenRef']]
 failures=[r for r in [*wire,*diagnostics]if r.get('format')=='aeris-status15-failed-prefix'and r.get('channelOpenRef')==p['channelOpenRef']]
 need([r['sequence']for r in successful]==list(range(1,len(successful)+1))and len(failures)<=1,'CLOSE_CONTIGUOUS_EXCHANGE_COUNTS')
 expected_requests=len(successful)
 if failures:
  need(allow_failed,'CLOSE_FAILED_EXCHANGE_NOT_ACCEPTED');failed=failures[0];failed_wire=read_ref(root,failed['requestWireRef'])
  nonce=failed['requestNonce'];need(type(nonce)is str and re.fullmatch('[a-f0-9]{32}',nonce)is not None and type(failed.get('intendedRequestBytes'))is int and 0<failed['intendedRequestBytes']<=516 and type(failed.get('requestWasFullySent'))is bool and failed.get('sendEvidence')=='KERNEL_ACCEPTED_BYTES_NOT_REMOTE_RECEIPT','CLOSE_FAILED_SEND_PROVENANCE')
  intended=json.dumps({'version':1,'requestNonce':nonce},separators=(',',':')).encode();intended=struct.pack('!I',len(intended))+intended
  need(len(intended)==failed['intendedRequestBytes']and intended.startswith(failed_wire)and failed['requestWasFullySent']==(failed_wire==intended),'CLOSE_ACTUAL_SENT_PREFIX_ONLY')
  need(type(failed.get('exchangeAttempted'))is bool and type(failed.get('channelSequence'))is int and failed['channelSequence']in(len(successful),len(successful)+1),'CLOSE_FAILED_SEQUENCE_TYPED')
  if not failed['exchangeAttempted']:need(failed_wire==b''and failed['channelSequence']==len(successful),'CLOSE_PREEXCHANGE_REFUSAL_ZERO_SENT')
  expected_requests=failed['channelSequence']
 need(p['requests']==expected_requests,'CLOSE_EXACT_ORIGINAL_REQUEST_COUNT')
 need(c['APKSHA256']==expected_apk and c['sourceSHA256']==source and p['port']==c['port']and p['authorityRestored']is False and p['flightAcceptance']is False,'CLOSE_SELECTED_CHANNEL_IDENTITY')
 original=json.loads(read_ref(root,p['channelOpenRef']),object_pairs_hook=unique);need(original==c,'CLOSE_ORIGINAL_OPEN_REFERENCE')
 need(p['EOFObserved']is True and p['socketClosed']is True and p['forwardRemoved']is True and p['drainComplete']is True,'CLOSE_EOF_FD_AND_FORWARD_DRAIN')
 port=c['port'];before,identity,remote,out=command(root,p['mappingBeforeRef']);expected='emulator-5582 tcp:'+str(port)+' localabstract:'+NAME
 need(remote==['forward','--list']and [x for x in out.decode('ascii').splitlines()if x.split()[:2]==['emulator-5582','tcp:'+str(port)]]==[expected],'CLOSE_BEFORE_OWNED_MAPPING')
 remove,argv,remote,out=command(root,p['removeCommandRef']);need(argv[:3]==identity[:3]and remote==['forward','--remove','tcp:'+str(port)]and out==b'','CLOSE_EXACT_OWNED_FORWARD_REMOVAL')
 after,argv,remote,out=command(root,p['mappingAfterRef']);need(argv[:3]==identity[:3]and remote==['forward','--list']and not[x for x in out.decode('ascii').splitlines()if x.split()[:2]==['emulator-5582','tcp:'+str(port)]],'CLOSE_NO_MAPPING_AFTER')
 need(before['endedHostNs']<=remove['startedHostNs']<=remove['endedHostNs']<=after['startedHostNs'],'CLOSE_ORIGINAL_COMMAND_ORDER')
 tail=read_ref(root,p['tailRef']);need(len(tail)<=2049,'CLOSE_TAIL_BOUND')
 if not allow_failed:need(p['captureComplete']is True and p['failure']is None and tail==b'','CLOSE_COMPLETE_CAPTURE_FOR_ACCEPTANCE')
 return {'format':'aeris-status15-cold-channel-closure','version':1,'drainComplete':True,'port':port,'captureComplete':p['captureComplete'],'flightAcceptance':False}


def verify_closure(root,*,expected_apk,source,allow_failed=False):
 """Every opened generation must close; max2 only via planned BOOTSTRAP."""
 root=Path(root);diagnostics=read_receipts(root,'diagnostic');opens=[r for r in diagnostics if r.get('format')=='aeris-status15-channel-open'];closes=[r for r in diagnostics if r.get('format')=='aeris-status15-channel-close']
 need(1<=len(opens)<=2 and len(opens)==len(closes),'EVERY_ORIGINAL_CHANNEL_OPEN_CLOSE')
 requests=read_receipts(root,'request');cache={};results=[]
 for opened in opens:
  matched=[]
  for closed in closes:
   original=json.loads(read_ref(root,closed['channelOpenRef']),object_pairs_hook=unique)
   if original==opened:matched.append(closed)
  need(len(matched)==1,'EXACT_ONE_CLOSE_PER_CHANNEL')
  closed=matched[0];channel(root,closed['channelOpenRef'],source,requests,cache,expected_apk)
  results.append(_verify_channel_closure(root,opened,closed,expected_apk=expected_apk,source=source,allow_failed=allow_failed))
 need(opens[0]['version']==1 and(len(opens)==1 or opens[1]['version']==2),'ONLY_DECLARED_BOOTSTRAP_GENERATION')
 return {'format':'aeris-status-cold-generational-closure','version':1,'channels':results,'drainComplete':True,'flightAcceptance':False}
