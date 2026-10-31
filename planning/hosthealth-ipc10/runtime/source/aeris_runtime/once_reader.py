"""Strict cold v2 evidence reader, independent of writer/Android process state."""
from pathlib import Path,PurePosixPath
import hashlib,json,re,os,stat

def unique(items):
 result={}
 for k,v in items:
  if k in result:raise ValueError('COLD_DUPLICATE_JSON_KEY')
  result[k]=v
 return result

def read_ref(root,ref):
 if type(ref)is not dict or set(ref)!={'format','version','path','offset','bytes','sha256'} or ref['format']!='aeris-original-byte-ref' or type(ref['version'])is not int or ref['version']not in(1,3):raise ValueError('COLD_REF_SCHEMA')
 name=ref['path']
 if type(name)is not str or not name or '\\'in name or PurePosixPath(name).is_absolute() or any(p in ('','..','.')for p in name.split('/')):raise ValueError('COLD_REF_PATH')
 if name not in(('ack-stream.raw','command-stream.raw','broker-wire.jsonl','status15-wire.jsonl')if ref['version']==3 else('ack-stream.raw',)) and re.fullmatch(r'objects/[a-f0-9]{64}',name)is None and not(ref['version']==3 and re.fullmatch(r'receipts/(request|command|barrier|close|diagnostic)\.jsonl',name)):raise ValueError('COLD_REF_OBJECT_KIND')
 if any(type(ref[k])is not int or ref[k]<0 for k in ('offset','bytes')) or ref['bytes']>(131073 if ref['version']==3 else 131072) or re.fullmatch('[a-f0-9]{64}',str(ref['sha256']))is None:raise ValueError('COLD_REF_BOUNDS')
 root=Path(root).absolute()
 if any(p.is_symlink()for p in[root,*root.parents]):raise ValueError('COLD_REF_ROOT_SYMLINK')
 path=root/name;fds=[os.open(root,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0))]
 try:
  for part in PurePosixPath(name).parts[:-1]:fds.append(os.open(part,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0),dir_fd=fds[-1]))
  fd=os.open(PurePosixPath(name).name,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0),dir_fd=fds[-1]);fds.append(fd);st=os.fstat(fd);size=st.st_size
  if not stat.S_ISREG(st.st_mode)or ref['version']==3 and st.st_nlink!=1:raise ValueError('COLD_REF_REGULAR_SINGLE_LINK')
  if ref['offset']+ref['bytes']>size:raise ValueError('COLD_REF_TRUNCATED')
  if name.startswith('objects/')and(ref['offset']!=0 or ref['bytes']!=size or name.split('/')[1]!=ref['sha256']or ref['version']==3 and size>16384):raise ValueError('COLD_OBJECT_EXACT')
  os.lseek(fd,ref['offset'],os.SEEK_SET);raw=os.read(fd,ref['bytes'])
  if hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('COLD_REF_SHA')
  if name in('ack-stream.raw','broker-wire.jsonl','status15-wire.jsonl')or name.startswith('receipts/'):
   if ref['offset']:os.lseek(fd,ref['offset']-1,os.SEEK_SET);before=os.read(fd,1)
   else:before=b'\n'
   if before!=b'\n'or not raw.endswith(b'\n')or b'\n'in raw[:-1]:raise ValueError('COLD_ACK_WHOLE_ORIGINAL_ROW')
 finally:
  for fd in reversed(fds):os.close(fd)
 return raw

def _reconstruct_requests(root,receipts,*,source,expected_context=None,expected_apk=None,version=2,maximum=32):
 """Receipts must be complete contiguous request sequence, in original order.

 v1 historical records deliberately fail here; legacy callers may still inspect
 them with their original reader, without claiming v2 reconstruction.
 """
 from .proofs import validate_native_ack
 if type(receipts)is not list or not 0<len(receipts)<=maximum:raise ValueError('COLD_DECLARED32_REQUEST_ENVELOPE')
 result=[];nonces=set();markers=set();nav_tickets=set();offset=-1;epoch=None;last_received=-1;bound=False;socket_cache={};socket_seq={}
 for sequence,receipt in enumerate(receipts,1):
  if type(receipt)is not dict or receipt.get('format')!='aeris-public-request' or type(receipt.get('version'))is not int or receipt.get('version')not in((3,4)if version==4 else(version,))or type(receipt.get('sequence'))is not int or receipt['sequence']!=sequence:raise ValueError('COLD_REQUEST_SEQUENCE_V2')
  fields={'format','version','sequence','request','action','hostSentNs','hostReceivedNs','sourceSHA256','context','expectedContext','intentHostNs','actualPID','barrierRef','barrierObservedHostNs','ackRef','snapshotRef','snapshotSHA256','snapshotBytes','rawSnapshotSHA256'}
  actual_version=receipt['version']
  if actual_version==4:fields=(fields-{'intentHostNs'})|{'socketRef'}
  if set(receipt)!=fields:raise ValueError('COLD_REQUEST_EXACT_SCHEMA')
  expected_ref_version=3 if version in(3,4)else 1
  if any(type(receipt.get(k))is not dict or receipt[k].get('version')!=expected_ref_version for k in('ackRef','snapshotRef','barrierRef')):raise ValueError('COLD_RECEIPT_REFERENCE_VERSION')
  request=receipt['request']
  if type(request)is not dict or type(request.get('version'))is not int or request['version']!=1 or type(request.get('requestNonce'))is not str or re.fullmatch('[a-f0-9]{32}',request['requestNonce'])is None:raise ValueError('COLD_ORIGINAL_REQUEST_SCHEMA')
  if receipt['action']=='STATUS' and set(request)!={'version','requestNonce'}:raise ValueError('COLD_STATUS_EXACT_SCHEMA')
  if receipt['action']=='BOOTSTRAP' and (set(request)!={'version','requestNonce','processEpoch','viewEpoch','baseRevision','sourceSHA256','context','provider','survey','expectedDraftSHA256'} or request.get('sourceSHA256')!=source or request.get('context')!=expected_context):raise ValueError('COLD_BOOTSTRAP_EXACT_SCHEMA')
  nonce=request['requestNonce']
  if nonce in nonces:raise ValueError('COLD_DUPLICATE_REQUEST_NONCE')
  nonces.add(nonce);ack_raw=read_ref(root,receipt['ackRef']);ack=json.loads(ack_raw,object_pairs_hook=unique);snapshot=read_ref(root,receipt['snapshotRef'])
  if version in(3,4)and(len(snapshot)>16384 or len(ack_raw)>2048):raise ValueError('COLD_SOURCE_DTO_ACK_BOUNDS')
  if receipt['ackRef']['path']!='ack-stream.raw' or receipt['ackRef']['offset']<=offset:raise ValueError('COLD_ACK_REF_ORDER')
  previous_offset=offset;offset=receipt['ackRef']['offset'];sent=receipt['hostSentNs'];received=receipt['hostReceivedNs']
  if type(sent)is not int or type(received)is not int or sent<last_received or received<sent or received-sent>10_000_000_000:raise ValueError('COLD_ORIGINAL10S_TIMES')
  last_received=received
  context=receipt.get('context');requested_context=receipt.get('expectedContext')
  if context!=ack.get('context') or context is not None and context!=expected_context or requested_context is not None and requested_context!=expected_context or bound and context!=expected_context:raise ValueError('COLD_SELECTED_CONTEXT')
  if context is not None:bound=True
  if receipt.get('action') not in ('STATUS','BOOTSTRAP') or receipt['action']!=('BOOTSTRAP' if 'baseRevision'in request else 'STATUS'):raise ValueError('COLD_REQUEST_ACTION')
  if type(receipt.get('snapshotBytes'))is not int or receipt['snapshotBytes']!=len(snapshot) or receipt.get('rawSnapshotSHA256')!=hashlib.sha256(snapshot).hexdigest() or receipt.get('sourceSHA256')!=source or receipt.get('snapshotSHA256')!=hashlib.sha256(snapshot).hexdigest():raise ValueError('COLD_SOURCE_CONTEXT_SNAPSHOT')
  barrier=read_ref(root,receipt['barrierRef']);barrier_time=receipt.get('barrierObservedHostNs')
  intent_time=receipt.get('intentHostNs')if actual_version!=4 else received
  if receipt['barrierRef']['path']!='ack-stream.raw' or not previous_offset<receipt['barrierRef']['offset']<offset or barrier in markers or re.fullmatch(rb'AERIS_OBSERVER_READY_[a-f0-9]{32}\n',barrier)is None or type(barrier_time)is not int or type(intent_time)is not int or not sent<=barrier_time<=intent_time<=received:raise ValueError('COLD_SUBSCRIBE_BEFORE_ACK')
  markers.add(barrier)
  if actual_version==4:
   if receipt['action']!='STATUS':raise ValueError('COLD_SOCKET_STATUS_ONLY')
   from .status15_reader import verify_request
   proof=verify_request(root,receipt,ack_raw,snapshot,source,receipts,socket_cache,expected_apk=expected_apk)
   expected=socket_seq.get(proof['channel'],0)+1
   if proof['sequence']!=expected:raise ValueError('COLD_STATUS15_CONTIGUOUS_CHANNEL_SEQUENCE')
   socket_seq[proof['channel']]=expected
  if type(receipt.get('actualPID'))is not int or receipt['actualPID']<=0:raise ValueError('COLD_ACTUAL_PID')
  value=validate_native_ack(request,ack,snapshot,pid=receipt['actualPID'],source=source,expected_context=requested_context,host_sent_ns=sent,host_received_ns=received)
  if epoch is not None and value['processEpoch']!=epoch:raise ValueError('COLD_PROCESS_RESTART')
  if 'navigation'in value['layout']:
   nav=value['layout']['navigation']
   if receipt['action']!='STATUS'or nav['ticket']in nav_tickets:raise ValueError('COLD_NAVIGATION_ORIGINAL_STATUS_UNIQUE_TICKET')
   nav_tickets.add(nav['ticket'])
  epoch=value['processEpoch'];result.append(value)
 return result


def reconstruct_requests(root,receipts,*,source,expected_context=None,expected_apk=None):
 if type(receipts)is not list or not receipts:raise ValueError('COLD_REQUESTS_NONEMPTY')
 version=receipts[0].get('version')
 if any(r.get('version')==4 for r in receipts):version=4
 if version not in(2,3,4):raise ValueError('COLD_REQUEST_VERSION')
 return _reconstruct_requests(root,receipts,source=source,expected_context=expected_context,expected_apk=expected_apk,version=version,maximum=900 if version in(3,4)else 32)

def read_receipts(root,kind):
 if kind not in('request','command','barrier','close','diagnostic'):raise ValueError('COLD_RECEIPT_KIND')
 path=Path(root)/'receipts'/(kind+'.jsonl')
 if not path.exists():return []
 if path.is_symlink()or not path.is_file()or path.stat().st_nlink!=1:raise ValueError('COLD_RECEIPT_REGULAR_SINGLE_LINK')
 result=[]
 with path.open('rb')as f:
  while True:
   raw=f.readline(16385)
   if not raw:break
   if len(raw)>16384 or not raw.endswith(b'\n'):raise ValueError('COLD_RECEIPT_TRUNCATED_OR_BOUND')
   result.append(json.loads(raw,object_pairs_hook=unique))
   if len(result)>5700:raise ValueError('COLD_RECEIPT_COUNT')
 return result

def _command_limit(remote):
 package='vn.rtr.aeris.mission'
 if remote==['forward','--no-rebind','tcp:0','localabstract:vn.rtr.aeris.mission.observe15']:return 64
 if remote==['forward','--list']:return 4096
 if len(remote)==3 and remote[:2]==['forward','--remove']and re.fullmatch('tcp:[1-9][0-9]{0,4}',remote[2])and int(remote[2][4:])<=65535:return 64
 if remote[:3]==['run-as',package,'cat']and len(remote)==4 and remote[3]in('files/runtime/response.json','files/runtime/current.json'):return 16384
 if remote==['am','start','-n',package+'/.ProductActivity']:return 2048
 if len(remote)==9 and remote[:8]==['am','broadcast','-a',package+'.PRODUCT_STATUS','-n',package+'/.ProductStatusReceiver','--es','requestNonce']and re.fullmatch('[a-f0-9]{32}',remote[8]):return 2048
 if len(remote)==4 and remote[:3]==['run-as',package,'cat']and re.fullmatch(r'files/product-observations01/status-[a-f0-9]{32}\.json',remote[3]):return 16384
 if remote in(['reverse','--list'],['reverse','--no-rebind','tcp:8895','tcp:8895'],['reverse','--no-rebind','tcp:8896','tcp:8896'],['reverse','--remove','tcp:8895'],['reverse','--remove','tcp:8896']):return 4096
 if remote==['pidof',package]:return 64
 if len(remote)==6 and remote[:4]==['log','-p','i','-t']and remote[4]in('AERIS_MISSION','AERIS_PRODUCT_STATUS')and re.fullmatch('AERIS_OBSERVER_READY_[a-f0-9]{32}',remote[-1]):return 64
 if remote==['am','start','-n',package+'/.CockpitActivity']:return 2048
 if len(remote)==10 and remote[:9]==['am','start','-n',package+'/.CockpitActivity','--es','missionAction','BOOTSTRAP','--es','missionRequestBase64']:return 2048
 if len(remote)==12 and remote[:11]==['am','broadcast','-n',package+'/.CockpitActivity$StatusReceiver','-a',package+'.STATUS','--es','missionAction','STATUS','--es','missionRequestBase64']:return 2048
 if remote==['am','force-stop',package]:return 64
 if remote==['pm','path',package]:return 4096
 if remote==['sh','-c','if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi']:return 64
 if len(remote)==2 and remote[0]=='sha256sum'and remote[1].startswith('/'):return 512
 if remote in(['dumpsys','activity','activities'],['exec-out','uiautomator','dump','/dev/tty']):return 131072
 if len(remote)==3 and remote[:2]==['input','text']and re.fullmatch('[a-f0-9]{64}',remote[2]):return 64
 if len(remote)==4 and remote[:2]==['input','tap']and all(re.fullmatch('[0-9]{1,4}',v)for v in remote[2:]):return 64
 if len(remote)==6 and remote[:3]==['input','touchscreen','motionevent']and remote[3]in('DOWN','MOVE','UP')and all(re.fullmatch('[0-9]{1,4}',v)for v in remote[4:]):return 64
 if len(remote)==3 and remote[:2]==['sh','-c']and re.fullmatch(r'if pidof vn\.rtr\.aeris\.mission >/dev/null \|\| kill -0 [1-9][0-9]* 2>/dev/null; then echo RUNNING; else echo ABSENT; fi',remote[2]):return 64
 raise ValueError('COLD_COMMAND_NOT_SOURCE_ALLOWLIST')

def _cold_predecessor_proof():
 # Independent immutable predecessor derivation, never the producer classifier.
 from .candidate import load,sha,CERT
 from .paths import repository
 digest='986bfabbbb2fc08043918a68e7ff211b9208826bd138f68a1e1fe123490447b5';source='3186db6e531b6bcb987dc82d2e7489a105a9d7b170c3d69a3b3667a275f00a3c';apk='3564fb8aa9e9006477b59b4f1e4954c3239ec20d5619b12f28b50b49d80de9c3'
 path=repository()/'evidence/runtime-nativeprepare10/candidates'/digest
 if any(v.is_symlink()for v in[path,*path.parents]):raise ValueError('COLD_PREDECESSOR_IMMUTABLE_PATH')
 manifest=load(path,digest);build=json.loads((path/'native-build-receipt.json').read_bytes(),object_pairs_hook=unique)
 if manifest['native']['sourceSHA256']!=source or manifest['native']['APK_SHA256']!=apk or build.get('certificateSHA256')!=CERT or build.get('productionSigning')is not False or build.get('sourceCount')!=51:raise ValueError('COLD_PREDECESSOR_SOURCE_APK_CERT')
 return {'format':'aeris-immutable-upgrade-predecessor','version':1,'candidateDir':str(path),'candidateSHA256':digest,'nativeSourceSHA256':source,'APKSHA256':apk,'certificateSHA256':CERT,'nativeBuildReceiptSHA256':sha(path/'native-build-receipt.json')}

def _verify_predecessor_backup_post(root,ref,commands,expected):
 import shlex
 proof=json.loads(read_ref(root,ref),object_pairs_hook=unique);capture=json.loads(read_ref(root,proof['exportCaptureReceiptRef']),object_pairs_hook=unique);rows=[]
 for key in('installedAfterPathCommandRef','installedAfterSHACommandRef','coldAfterCommandRef'):
  if proof[key].get('path')!='receipts/command.jsonl':raise ValueError('COLD_BACKUP_POST_ORIGINAL_COMMAND_JOURNAL')
  row=json.loads(read_ref(root,proof[key]),object_pairs_hook=unique);argv=json.loads(read_ref(root,row['argvRef']),object_pairs_hook=unique)
  if row not in commands or row.get('version')!=3 or row.get('captureComplete')is not True or type(row.get('exit'))is not int or row['exit']!=0 or row.get('failure')is not None or read_ref(root,row['stderrRef'])or len(argv)!=5 or argv[1:4]!=['-s',proof['serial'],'shell']:raise ValueError('COLD_BACKUP_POST_CAPTURE')
  rows.append((row,shlex.split(argv[4]),read_ref(root,row['stdoutRef'])))
 location=rows[0][2].decode().strip()
 if rows[0][1]!=['pm','path','vn.rtr.aeris.mission']or not location.startswith('package:/')or'\n'in location or rows[1][1]!=['sha256sum',location[8:]]or rows[1][2].decode().split()[0]!=expected or rows[2][1]!=['sh','-c','if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi']or rows[2][2]!=b'ABSENT\n':raise ValueError('COLD_BACKUP_POST_EXACT_APK_PID')
 if not capture['finishedHostNs']<=rows[0][0]['startedHostNs']<=rows[0][0]['endedHostNs']<=rows[1][0]['startedHostNs']<=rows[1][0]['endedHostNs']<=rows[2][0]['startedHostNs']<=rows[2][0]['endedHostNs']<=proof['verifiedHostNs']:raise ValueError('COLD_BACKUP_POST_EXPORT_APK_ORDER')

def _verify_install_result_v2(root,install,auth,commands,*,allow_failed):
 import shlex
 rows=[v for v in read_receipts(root,'diagnostic')if v.get('format')=='aeris-recovery08-development-install'and v.get('version')==auth['version']and v.get('authorizationRef')==install['authorizationRef']]
 if not rows and allow_failed:return
 if len(rows)!=1:raise ValueError('COLD_INSTALL_V2_ONE_ORIGINAL_RESULT')
 result=rows[0];fields={'format','version','authorizationRef','installCommandRef','installedPathCommandRef','installedSHACommandRef','coldAfterCommandRef','oldOriginalBackupReceiptRef','newAPKSHA256','noClearOrWipe','ACKObserverStarted','flightAcceptance'}
 if set(result)!=fields or result['installCommandRef'].get('path')!='receipts/command.jsonl'or type(result['version'])is not int or result['noClearOrWipe']is not True or result['ACKObserverStarted']is not False or result['flightAcceptance']is not False or result['newAPKSHA256']!=auth['APKSHA256']or result['oldOriginalBackupReceiptRef']!=auth['originalBackupReceiptRef']or json.loads(read_ref(root,result['installCommandRef']),object_pairs_hook=unique)!=install:raise ValueError('COLD_INSTALL_V2_EXACT_RESULT')
 identity=json.loads(read_ref(root,install['argvRef']),object_pairs_hook=unique)[:3];post=[]
 for key in('installedPathCommandRef','installedSHACommandRef','coldAfterCommandRef'):
  ref=result[key]
  if ref.get('path')!='receipts/command.jsonl':raise ValueError('COLD_INSTALL_POST_ORIGINAL_COMMAND_JOURNAL')
  command=json.loads(read_ref(root,ref),object_pairs_hook=unique);argv=json.loads(read_ref(root,command['argvRef']),object_pairs_hook=unique)
  if command not in commands or command.get('version')!=3 or command.get('captureComplete')is not True or type(command.get('exit'))is not int or command['exit']!=0 or command.get('failure')is not None or read_ref(root,command['stderrRef'])or len(argv)!=5 or argv[:3]!=identity or argv[3]!='shell':raise ValueError('COLD_INSTALL_V2_POST_ORIGINAL_CAPTURE')
  post.append((command,shlex.split(argv[4]),read_ref(root,command['stdoutRef'])))
 if [v[0]['sequence']for v in post]!=list(range(install['sequence']+1,install['sequence']+4)):raise ValueError('COLD_INSTALL_V2_IMMEDIATELY_FOLLOWING_POSTCHECKS')
 location=post[0][2].decode().strip()
 if post[0][1]!=['pm','path','vn.rtr.aeris.mission']or not location.startswith('package:/')or'\n'in location or post[1][1]!=['sha256sum',location[8:]]or post[1][2].decode().split()[0]!=auth['APKSHA256']or post[2][1]!=['sh','-c','if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi']or post[2][2]!=b'ABSENT\n':raise ValueError('COLD_INSTALL_V2_NEW_APK_AND_COLD_AFTER')
 if not install['endedHostNs']<=post[0][0]['startedHostNs']<=post[0][0]['endedHostNs']<=post[1][0]['startedHostNs']<=post[1][0]['endedHostNs']<=post[2][0]['startedHostNs']<=post[2][0]['endedHostNs']:raise ValueError('COLD_INSTALL_V2_POSTCHECK_CLOCKS')

def _verify_install_authorization(root,row,remote,out,source,*,allow_failed=False):
 from .android import verify_cold_original_backup
 from .candidate import load,sha,CERT
 auth=json.loads(read_ref(root,row['authorizationRef']),object_pairs_hook=unique)
 fields={'format','version','candidateDir','candidateSHA256','APKPath','APKSHA256','nativeSourceSHA256','certificateSHA256','expectedOldAPKSHA256','originalBackupReceiptRef','package','preparedHostNs','coldBeforeCommandRef','installedPathCommandRef','installedSHACommandRef'}
 expected_version=3 if row['version']==8 else 2 if row['version']==6 else 1
 if expected_version in(2,3):fields.add('predecessor')
 if type(auth)is not dict or set(auth)!=fields or auth['format']!='aeris-recovery08-development-install-authorization'or type(auth['version'])is not int or auth['version']!=expected_version or auth['package']!='vn.rtr.aeris.mission':raise ValueError('COLD_INSTALL_EXACT_AUTHORIZATION_SCHEMA')
 if type(auth['preparedHostNs'])is not int or not 0<=auth['preparedHostNs']<=row['startedHostNs']:raise ValueError('COLD_INSTALL_AUTHORIZATION_CLOCK')
 expected_old='47208ec07a0c5bc5e70ea28fee87bcbc3267e44c039a75c5e9d95cfd96b4a189'
 if expected_version in(2,3):
  if expected_version==3:
   from .predecessor15 import proof as current_predecessor
   predecessor=current_predecessor()
  else:predecessor=_cold_predecessor_proof()
  expected_old=predecessor['APKSHA256']
  if row['authorizationRef'].get('path')!='receipts/diagnostic.jsonl'or auth not in read_receipts(root,'diagnostic'):raise ValueError('COLD_INSTALL_V2_ORIGINAL_AUTHORIZATION_JOURNAL')
  if auth['predecessor']!=predecessor or auth['nativeSourceSHA256']==predecessor['nativeSourceSHA256']or auth['APKSHA256']==expected_old:raise ValueError('COLD_INSTALL_FIXED_NEW_SOURCE_PREDECESSOR')
 if auth['expectedOldAPKSHA256']!=expected_old:raise ValueError('COLD_INSTALL_EXACT_ORIGINAL_APK')
 candidate=Path(auth['candidateDir']);apk=Path(auth['APKPath'])
 if not candidate.is_absolute()or not apk.is_absolute()or candidate.is_symlink()or apk.is_symlink()or apk.resolve()!=candidate.resolve()/'native.apk':raise ValueError('COLD_INSTALL_FROZEN_APK_PATH')
 manifest=load(candidate,auth['candidateSHA256'])
 if auth['APKSHA256']!=manifest['native']['APK_SHA256']or sha(apk)!=auth['APKSHA256']or auth['nativeSourceSHA256']!=manifest['native']['sourceSHA256']or auth['nativeSourceSHA256']!=source or auth['certificateSHA256']!=CERT or remote!=['install','-r',str(apk)]:raise ValueError('COLD_INSTALL_CANDIDATE_APK_SOURCE_CERT')
 backup=verify_cold_original_backup(root,auth['originalBackupReceiptRef']);original_commands=read_receipts(root,'command')
 if expected_version in(2,3)and(backup.get('backupVersion')!=expected_version or backup.get('predecessor')!=predecessor or backup.get('oldAPKSHA256')!=expected_old):raise ValueError('COLD_INSTALL_PREDECESSOR_BACKUP_UNION')
 if expected_version in(2,3):_verify_predecessor_backup_post(root,auth['originalBackupReceiptRef'],original_commands,expected_old)
 commands=[]
 import shlex
 for key in('coldBeforeCommandRef','installedPathCommandRef','installedSHACommandRef'):
  command=json.loads(read_ref(root,auth[key]),object_pairs_hook=unique)
  command_fields={'format','version','sequence','argvRef','startedHostNs','endedHostNs','exit','stdoutRef','stderrRef','captureComplete','failure'}
  if type(command)is not dict or set(command)!=command_fields or command not in original_commands or command.get('format')!='aeris-command'or type(command.get('version'))is not int or command['version']!=3 or type(command.get('exit'))is not int or command['exit']!=0 or command.get('captureComplete')is not True or command.get('failure')is not None or any(type(command.get(k))is not int for k in('startedHostNs','endedHostNs','sequence'))or not 0<=command['startedHostNs']<=command['endedHostNs']<=auth['preparedHostNs']:raise ValueError('COLD_INSTALL_ORIGINAL_PRECHECK_COMMAND')
  argv=json.loads(read_ref(root,command['argvRef']),object_pairs_hook=unique);original=read_ref(root,command['stdoutRef']);stderr=read_ref(root,command['stderrRef'])
  if stderr or type(argv)is not list or len(argv)!=5 or argv[3]!='shell':raise ValueError('COLD_INSTALL_PRECHECK_ORIGINAL_ARGV')
  commands.append((argv,shlex.split(argv[4]),original))
 if [json.loads(read_ref(root,auth[k]),object_pairs_hook=unique)['sequence']for k in('coldBeforeCommandRef','installedPathCommandRef','installedSHACommandRef')]!=list(range(row['sequence']-3,row['sequence'])):raise ValueError('COLD_INSTALL_IMMEDIATELY_PRECEDING_PRECHECKS')
 identity=commands[0][0][:3]
 if backup.get('serial')!=identity[2]or any(v[0][:3]!=identity for v in commands)or json.loads(read_ref(root,row['argvRef']),object_pairs_hook=unique)!=identity+['install','-r',str(apk)]:raise ValueError('COLD_INSTALL_PRECHECK_DEVICE_AND_DIRECT_INSTALL_ARGV')
 if commands[0][1]!=['sh','-c','if pidof vn.rtr.aeris.mission >/dev/null; then echo RUNNING; else echo ABSENT; fi']or commands[0][2]!=b'ABSENT\n'or commands[1][1]!=['pm','path','vn.rtr.aeris.mission']:raise ValueError('COLD_INSTALL_COLD_ORIGINAL_PACKAGE')
 location=commands[1][2].decode().strip()
 if not location.startswith('package:/')or '\n'in location:raise ValueError('COLD_INSTALL_SINGLE_ORIGINAL_PACKAGE_PATH')
 if commands[2][1]!=['sha256sum',location[len('package:'):]]or commands[2][2].decode().split()[0]!=auth['expectedOldAPKSHA256']:raise ValueError('COLD_INSTALL_ORIGINAL_APK_BYTES')
 if not allow_failed and(not out or out.rstrip().splitlines()[-1]!=b'Success'):raise ValueError('COLD_INSTALL_ACTUAL_SUCCESS_REQUIRED')
 if expected_version in(2,3):_verify_install_result_v2(root,row,auth,original_commands,allow_failed=allow_failed)
 return 2048

def _verify_am_delivery_notice(row,argv,remote,out,err,source):
 # Independent cold derivation. Do not call the live Android classifier.
 import base64,shlex
 if row.get('androidDeliveryNotice')!='BOOTSTRAP_SINGLE_TOP_DELIVERED_NON_AUTHORITY'or row.get('captureComplete')is not True or type(row.get('exit'))is not int or row['exit']!=0 or row.get('failure')is not None:raise ValueError('COLD_AM_DELIVERY_EXACT_OUTCOME')
 if out!=b'Starting: Intent { cmp=vn.rtr.aeris.mission/.CockpitActivity (has extras) }\n'or err!=b'Warning: Activity not started, intent has been delivered to currently running top-most instance.\n':raise ValueError('COLD_AM_DELIVERY_EXACT_ORIGINAL_OUTPUTS')
 if len(argv)!=5 or argv[3]!='shell'or argv[4]!=shlex.join(remote)or len(remote)!=10 or remote[:9]!=['am','start','-n','vn.rtr.aeris.mission/.CockpitActivity','--es','missionAction','BOOTSTRAP','--es','missionRequestBase64']:raise ValueError('COLD_AM_DELIVERY_EXACT_CANONICAL_BOOTSTRAP_ARGV')
 raw=base64.b64decode(remote[-1],altchars=b'-_',validate=True)
 if not 0<len(raw)<=32768 or base64.urlsafe_b64encode(raw).decode()!=remote[-1]:raise ValueError('COLD_AM_DELIVERY_CANONICAL_BODY_BASE64')
 body=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in()).throw(ValueError('COLD_NONFINITE_BOOTSTRAP')))
 if type(body)is not dict or set(body)!={'version','requestNonce','processEpoch','viewEpoch','baseRevision','sourceSHA256','context','provider','survey','expectedDraftSHA256'}or json.dumps(body,separators=(',',':'),ensure_ascii=False).encode()!=raw:raise ValueError('COLD_AM_DELIVERY_EXACT_BODY')
 if type(body['version'])is not int or body['version']!=1 or type(body['viewEpoch'])is not int or body['viewEpoch']<=0 or type(body['baseRevision'])is not int or body['baseRevision']<0 or body['sourceSHA256']!=source or any(type(body[k])is not str or re.fullmatch('[a-f0-9]{%d}'%n,body[k])is None for k,n in[('requestNonce',32),('processEpoch',32),('sourceSHA256',64)]):raise ValueError('COLD_AM_DELIVERY_TYPED_SOURCE_NONCE_EPOCH')
 if type(body['context'])is not dict or set(body['context'])!={'run','epoch','boot','operator','generation','profileId'}or len(json.dumps(body['context'],sort_keys=True,separators=(',',':')).encode())>256 or any(type(v)is not str or not v for v in body['context'].values())or type(body['provider'])is not dict or not body['provider']:raise ValueError('COLD_AM_DELIVERY_CONTEXT_PROVIDER')
 if not(type(body['survey'])is dict and body['expectedDraftSHA256']is None or body['survey']is None and type(body['expectedDraftSHA256'])is str and re.fullmatch('[a-f0-9]{64}',body['expectedDraftSHA256'])):raise ValueError('COLD_AM_DELIVERY_SURVEY_OR_DRAFT')
 return body


def verify_navigation_taps(root,requests,snapshots,commands,*,allow_failed=False):
 """Reconstruct each UI input from original STATUS/argv/post-STATUS byte refs."""
 import shlex
 from .proofs import navigation_measurement
 views=[];seen=set();last_source=0
 def original(ref,kind,rows):
  if type(ref)is not dict or ref.get('path')!='receipts/'+kind+'.jsonl':raise ValueError('COLD_NAVIGATION_ORIGINAL_JOURNAL')
  row=json.loads(read_ref(root,ref),object_pairs_hook=unique)
  if row not in rows:raise ValueError('COLD_NAVIGATION_ORIGINAL_ROW_MEMBERSHIP')
  return row
 for proof in read_receipts(root,'diagnostic'):
  if proof.get('format')!='aeris-navigation-tap':continue
  fields={'format','version','view','ticket','sourceRequestRef','tapCommandRef','afterRequestRef','beforeTapHostNs','afterTapHostNs','completed','failure'}
  if set(proof)!=fields or type(proof['version'])is not int or proof['version']!=1 or proof['view']not in('survey','preflight','fly','review')or type(proof['completed'])is not bool:raise ValueError('COLD_NAVIGATION_PROOF_SCHEMA')
  if len(json.dumps(proof,sort_keys=True,separators=(',',':')).encode())+1>1280:raise ValueError('COLD_NAVIGATION_PROOF1280')
  request=original(proof['sourceRequestRef'],'request',requests);tap=original(proof['tapCommandRef'],'command',commands);index=request['sequence']-1;snapshot=snapshots[index]
  if request['action']!='STATUS'or request['sequence']<=last_source or tap['sequence']in seen:raise ValueError('COLD_NAVIGATION_ORIGINAL_ORDER_NO_REUSE')
  last_source=request['sequence'];seen.add(tap['sequence']);name='nav-'+proof['view'];n=navigation_measurement(snapshot,action=name,receipt=request,before_tap_ns=proof['beforeTapHostNs'])
  if proof['ticket']!=n['ticket']:raise ValueError('COLD_NAVIGATION_TICKET_JOIN')
  b=n['targets'][name]['bounds'];argv=json.loads(read_ref(root,tap['argvRef']),object_pairs_hook=unique)
  expected=['input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2)]
  if tap['version']!=3 or len(argv)!=5 or argv[3]!='shell'or argv[4]!=shlex.join(expected):raise ValueError('COLD_NAVIGATION_ORIGINAL_ACTUAL_INPUT')
  if not proof['completed']:
   if not allow_failed or type(proof['failure'])is not str or not proof['failure']:raise ValueError('COLD_NAVIGATION_INCOMPLETE')
   # Failed/unknown dispatch remains an original prefix, never an accepted tap.
   continue
  if not proof['beforeTapHostNs']<=tap['startedHostNs']<=request['hostSentNs']+200_000_000 or tap['startedHostNs']>request['hostReceivedNs']+200_000_000:raise ValueError('COLD_NAVIGATION_ACTUAL_DISPATCH200MS')
  if proof['failure']is not None or tap['captureComplete']is not True or tap['exit']!=0 or tap['failure']is not None or read_ref(root,tap['stderrRef'])!=b'':raise ValueError('COLD_NAVIGATION_SUCCESS_ORIGINAL_CAPTURE')
  after=original(proof['afterRequestRef'],'request',requests);post=snapshots[after['sequence']-1];state=post['state']
  if after['action']!='STATUS'or after['sequence']<=request['sequence']or type(proof['afterTapHostNs'])is not int or not tap['endedHostNs']<=proof['afterTapHostNs']<=after['hostSentNs']:raise ValueError('COLD_NAVIGATION_POST_STATUS_ORDER')
  if any(post[k]!=snapshot[k]for k in('pid','sourceSHA256','processEpoch','viewEpoch','context'))or state['chosenView']!=proof['view']or state['presentedView']!=proof['view']or state['viewReady']is not True or state['renderedWorkspaceVersion']!=state['workspaceProjection']['version']:raise ValueError('COLD_NAVIGATION_ACTUAL_PRESENTED_TARGET')
  views.append(proof['view'])
 return views

def verify_store(store,*,source,expected_context=None,expected_apk=None,allow_failed=False):
 """Cold verify every original command row plus matched original request chain."""
 import base64,shlex
 root=Path(store.root)if hasattr(store,'root')else Path(store)
 commands=read_receipts(root,'command');requests=read_receipts(root,'request')
 if any(type(r)is not dict or r.get('version')not in(3,4)for r in requests):raise ValueError('COLD_V3_STORE_REQUEST_VERSION')
 if not 0<len(commands)<=3700:raise ValueError('COLD_COMMAND_COUNT')
 parsed=[];last=-1;device_identity=None;delivery_notices={};matched_notices=set();broker_sequence=0;broker_nonces=set();broker_identity=None
 for sequence,row in enumerate(commands,1):
  required={'format','version','sequence','argvRef','startedHostNs','endedHostNs','exit','stdoutRef','stderrRef','captureComplete','failure'}
  version=row.get('version');required=required|({'authorizationRef'}if type(version)is int and version in(4,6,8) else{'androidDeliveryNotice'}if type(version)is int and version==5 else{'brokerRef'}if type(version)is int and version==7 else set())
  if set(row)!=required or row['format']!='aeris-command'or type(row['version'])is not int or row['version']not in(3,4,5,6,7,8) or type(row['sequence'])is not int or row['sequence']!=sequence:raise ValueError('COLD_COMMAND_SCHEMA_ORDER')
  if any(type(row[k])is not dict or row[k].get('version')!=3 for k in('argvRef','stdoutRef','stderrRef')):raise ValueError('COLD_V3_COMMAND_REFERENCE_VERSION')
  start=row['startedHostNs'];end=row['endedHostNs']
  if type(start)is not int or type(end)is not int or not last<=start<=end or end-start>70_000_000_000:raise ValueError('COLD_COMMAND_CLOCK')
  last=end
  no_exit_prefix=allow_failed and row['exit']is None and row['captureComplete']is False and type(row['failure'])is str and bool(row['failure'])
  if type(row['captureComplete'])is not bool or(type(row['exit'])is not int and not no_exit_prefix)or(not allow_failed and(not row['captureComplete']or row['exit']or row['failure']is not None)):raise ValueError('COLD_COMMAND_INCOMPLETE_OR_FAILED')
  argv=json.loads(read_ref(root,row['argvRef']),object_pairs_hook=unique);out=read_ref(root,row['stdoutRef']);err=read_ref(root,row['stderrRef'])
  if type(argv)is not list or not all(type(x)is str for x in argv)or len(argv)<4 or argv[1]!='-s'or re.fullmatch('emulator-[0-9]+',argv[2])is None:raise ValueError('COLD_COMMAND_ARGV')
  identity=(argv[0],argv[2])
  if device_identity is not None and identity!=device_identity:raise ValueError('COLD_COMMAND_DEVICE_IDENTITY')
  device_identity=identity
  if err and row['failure']is None and row['version']!=5:raise ValueError('COLD_SUCCESS_WITH_ORIGINAL_STDERR')
  remote=shlex.split(argv[4])if len(argv)==5 and argv[3]=='shell'else argv[3:]
  if row['version']==7:
   from .broker_reader import verify_command
   bp=verify_command(root,row,argv,remote,out,err,allow_failed=allow_failed)
   if bp['sequence']!=(broker_sequence if broker_sequence else bp['precedingSequence'])+1 or bp['nonce']in broker_nonces or broker_identity is not None and broker_identity!=(bp['pid'],bp['launchRef']):raise ValueError('COLD_BROKER_SEQUENCE_NONCE_OR_IDENTITY')
   broker_sequence=bp['sequence'];broker_nonces.add(bp['nonce']);broker_identity=(bp['pid'],bp['launchRef'])
  if row['version']==5:delivery_notices[row['sequence']]=_verify_am_delivery_notice(row,argv,remote,out,err,source)
  if row['version']in(4,6,8):
   if type(row['authorizationRef'])is not dict or row['authorizationRef'].get('version')!=3:raise ValueError('COLD_INSTALL_ORIGINAL_AUTHORIZATION_REFERENCE')
   limit=_verify_install_authorization(root,row,remote,out,source,allow_failed=allow_failed)
  else:limit=_command_limit(remote)
  if not allow_failed and len(out)>limit:raise ValueError('COLD_COMMAND_SOURCE_OUTPUT_BOUND')
  parsed.append((row,remote,out,err))
 result=reconstruct_requests(root,requests,source=source,expected_context=expected_context,expected_apk=expected_apk)
 for request in requests:
  if request['version']==4:continue
  nonce=request['request']['requestNonce'];marker=read_ref(root,request['barrierRef']).rstrip(b'\n').decode('ascii');matches=[]
  for row,remote,out,err in parsed:
   if len(remote)>3 and remote[:2]in(['am','broadcast'],['am','start'])and 'missionRequestBase64'in remote:
    pos=remote.index('missionRequestBase64')
    if pos+1<len(remote):
     body=json.loads(base64.urlsafe_b64decode(remote[pos+1]),object_pairs_hook=unique)
     if body.get('requestNonce')==nonce:matches.append((row,body))
  if len(matches)!=1 or matches[0][1]!=request['request']:raise ValueError('COLD_ORIGINAL_INTENT_REQUEST')
  matched_remote=next(remote for row,remote,out,err in parsed if row is matches[0][0]);encoded=matched_remote[matched_remote.index('missionRequestBase64')+1]
  expected_remote=(['am','broadcast','-n','vn.rtr.aeris.mission/.CockpitActivity$StatusReceiver','-a','vn.rtr.aeris.mission.STATUS','--es','missionAction','STATUS','--es','missionRequestBase64',encoded]if request['action']=='STATUS'else['am','start','-n','vn.rtr.aeris.mission/.CockpitActivity','--es','missionAction','BOOTSTRAP','--es','missionRequestBase64',encoded])
  if matched_remote!=expected_remote:raise ValueError('COLD_ORIGINAL_PUBLIC_INTENT_COMPONENT_ACTION')
  intent=matches[0][0]
  if intent['version']==5:
   if request['action']!='BOOTSTRAP'or delivery_notices[intent['sequence']]!=request['request']:raise ValueError('COLD_AM_DELIVERY_ORIGINAL_BOOTSTRAP_REQUEST')
   matched_notices.add(intent['sequence'])
  if not request['intentHostNs']<=intent['startedHostNs']<=intent['endedHostNs']<=request['hostReceivedNs']:raise ValueError('COLD_INTENT_DISPATCH_CLOCK')
  markers=[row for row,remote,out,err in parsed if remote==['log','-p','i','-t','AERIS_MISSION',marker]and request['hostSentNs']<=row['startedHostNs']<=row['endedHostNs']<=request['intentHostNs']]
  snapshots=[row for row,remote,out,err in parsed if remote==['run-as','vn.rtr.aeris.mission','cat','files/runtime/response.json']and row['stdoutRef']==request['snapshotRef']and intent['startedHostNs']<=row['startedHostNs']<=row['endedHostNs']<=request['hostReceivedNs']]
  pids=[out for row,remote,out,err in parsed if remote==['pidof','vn.rtr.aeris.mission']and intent['startedHostNs']<=row['startedHostNs']<=row['endedHostNs']<=request['hostReceivedNs']]
  if len(markers)!=1 or len(snapshots)!=1 or len(pids)!=1 or pids[0].strip()!=str(request['actualPID']).encode():raise ValueError('COLD_ORIGINAL_MARKER_PID_SNAPSHOT_COMMANDS')
 if not allow_failed and set(delivery_notices)!=matched_notices:raise ValueError('COLD_AM_DELIVERY_WITHOUT_GENUINE_MATCHED_NATIVE_ACK')
 from .broker_reader import verify_wire_coverage
 verify_wire_coverage(root,[r['brokerRef']for r in commands if r['version']==7],allow_failed=allow_failed)
 from .status15_reader import verify_exchange_coverage
 verify_exchange_coverage(root,[r['socketRef']for r in requests if r['version']==4],allow_failed=allow_failed)
 navigation_views=verify_navigation_taps(root,requests,result,commands,allow_failed=allow_failed)
 return {'navigationViews':navigation_views,'navigationTaps':len(navigation_views),'format':'aeris-v3-cold-store-proof','version':3,'requests':len(result),'socketRequests':sum(r['version']==4 for r in requests),'commands':len(commands),'androidDeliveryNotices':len(delivery_notices),'unmatchedAndroidDeliveryNotices':len(set(delivery_notices)-matched_notices),'missionAcceptanceClaimed':False,'failedPrefixOnly':allow_failed,'allOriginalCommandBytesVerified':True,'allOriginalRequestAndSnapshotBytesVerified':True,'processEpoch':result[-1]['processEpoch'],'lastSnapshotSHA256':requests[-1]['snapshotSHA256']}
