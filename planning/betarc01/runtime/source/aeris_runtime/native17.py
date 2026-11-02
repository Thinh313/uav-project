"""Native-only17 bounded administrative adapters. No AP or flight transport.

Receiver runs in a fresh process selected by the OLD candidate. Actual commands
are original OnceStore operations; unknown outcomes stop, never resend.
"""
from pathlib import Path
import base64,hashlib,json,os,re,secrets,sys,time,tarfile
from .application09 import AndroidDomain09,PACKAGE,ACTIVITY
from .metadata_budget import encoded,capture_command
from .paths import repository
from planning.nativejournal17.receiver17 import validate_tar_shape

ADMIN_ACTION='vn.rtr.aeris.mission.JOURNAL_LIFECYCLE17'
ADMIN_COMPONENT=PACKAGE+'/vn.rtr.aeris.mission.JournalLifecycleReceiver17'
NATIVE17_EXPORTS={'after-migration':'native-journal17-after-migration.tar','after-first-close':'native-journal17-after-first-close.tar'}
OLD_CANDIDATE='9e01e2dc55f4c1545388204674b236bb1babf1a6da97fcbc57d383ffaac0190c'
OLD_APK='8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1'
def need(v,n):
 if not v:raise ValueError('NATIVE17_'+n)
def sha(b):return hashlib.sha256(b).hexdigest()
def unique(xs):
 d={}
 for k,v in xs:need(k not in d,'DUPLICATE_JSON');d[k]=v
 return d
def decode(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in()).throw(ValueError('NONFINITE')))

class AndroidDomain17(AndroidDomain09):
 def _command_bound(self,args):
  need(self.serial=='emulator-5582'and self.observer is not None and self.observer.tag=='AERIS_PRODUCT_STATUS','EXACT_OWNED_NATIVE17_DEVICE')
  if len(args)==3 and args[:2]==['install','-r']:
   from .install17 import install_context17
   install_context17(self,args);return 2048
  if args==['shell','am','start','-W','-n',ACTIVITY]:
   need(getattr(self,'migration17_verified',False),'ARCHIVE_VERIFIED_BEFORE_ACTIVITY');return 2048
  if len(args)==16 and args[:7]==['shell','am','broadcast','-a',ADMIN_ACTION,'-n',ADMIN_COMPONENT]:
   need(args[7:9]==['--es','requestNonce']and re.fullmatch('[a-f0-9]{32}',args[9])and args[10:12]==['--es','operation']and args[12]in('PREVIEW','APPLY')and args[13:15]==['--es','planBase64'],'EXACT_ADMIN_ARGUMENTS')
   raw=base64.b64decode(args[15],validate=True);need(len(raw)<=4096 and base64.b64encode(raw).decode()==args[15],'BOUNDED_CANONICAL_PLAN');return 2048
  return super()._command_bound(args)
 def export17(self,stage,*,deadline_ns):
  need(stage in NATIVE17_EXPORTS,'FIXED_EXPORT_STAGE');self._check_budget_actor()
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):return self._export_private(self.root.parent.name,self.root.parent/NATIVE17_EXPORTS[stage],deadline_ns=deadline_ns,metadata_only=True,maximum_bytes=64*2**20,product_full_closed=True,native17_stage=stage)

def preserve_legacy(owner,case,*,deadline_ns):
 """Original09 retained old app inventory, no credit or package mutation."""
 from .android import AndroidDevice
 d=case['device'];probe=case['native'];legacy=AndroidDevice(d.adb,d.serial,d.root.parent/'android-api-retained',budget=d.budget,observer_tag='AERIS_PRODUCT_STATUS');legacy.live_check=d.live_check
 legacy.command(['shell','am','force-stop','vn.rtr.aeris.mission'],deadline_ns=deadline_ns);cold=legacy._cold_absence(deadline_ns);path,apk=legacy._installed_sha('77c65876eecb6d4fbc68a113bf682fa416c4272b3ed1de71f803c63df58d1b21',deadline_ns)
 with d.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):export=legacy._export_private(case['context']['run'],case['root']/'native-original-before-quarantine.tar',deadline_ns=deadline_ns,full_original=True)
 need(export['captureComplete']is True,'RETAINED_LEGACY_FULL_CAPTURE');legacy._cold_absence(deadline_ns)
 du=legacy.command(['shell','run-as','vn.rtr.aeris.mission','du','-k','-s','files'],deadline_ns=deadline_ns,maximum_bytes=256);match=re.fullmatch(rb'([0-9]+)[\t ]+files\n',du);need(match is not None,'RETAINED_LEGACY_ALLOCATED_KIB');logical=0;entries=0;seen=set()
 with tarfile.open(export['path'],'r:')as tar:
  for m in tar:
   need(m.name not in seen and entries<8192 and not m.pax_headers and not m.issym()and not m.islnk()and(m.isdir()or m.isfile())and(m.name=='files'or m.name.startswith('files/'))and'..'not in m.name.split('/'),'RETAINED_LEGACY_TAR');seen.add(m.name);entries+=1
   if m.isfile():logical+=m.size;need(logical<=512*2**20,'RETAINED_LEGACY_LOGICAL')
 probe.retained_inventory={'format':'aeris-retained-old-application-private-inventory','version':1,'package':'vn.rtr.aeris.mission','allocatedBytes':int(match[1])*1024,'plaintextFileLengthBytes':logical,'entries':entries,'sourceDUCommandRef':legacy.last_command_ref,'sourceDUStdoutRef':legacy.last_command['stdoutRef'],'sourceDUArgvRef':legacy.last_command['argvRef'],'sourceOriginalTAR':export,'historicalCompact10DecodedLogical':'NOT_REMEASURED_OR_CREDITED','sourceStopped':True,'notNewDeviceGrowthCredit':True}
 probe.retained_inventory_ref=d.store.receipt('retained-old-application-inventory.json',probe.retained_inventory);case['legacy17']={'coldRef':cold,'pathRef':path,'APKRef':apk};return probe.retained_inventory

def cold_backup(owner,case,*,deadline_ns):
 """Stop target once; complete cold backup before any package installation."""
 d=case['device'];need(type(d)is AndroidDomain17 and not hasattr(d,'_backup17'),'ONE_ORIGINAL_COLD_BACKUP')
 d.command(['shell','am','force-stop',PACKAGE],deadline_ns=deadline_ns);before=d._cold_absence(deadline_ns)
 path_ref,sha_ref=d._installed_sha(OLD_APK,deadline_ns)
 with d.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):backup=d._export_private(case['context']['run'],case['root']/'native-restart-metadata.tar',deadline_ns=deadline_ns,metadata_only=True,maximum_bytes=64*2**20,product_full_closed=True)
 after=d._cold_absence(deadline_ns);need(backup['captureComplete']is True and backup['exit']==0,'COMPLETE_BACKUP_REQUIRED');workspace=workspace17(backup['path']);need(workspace['sequence']<16,'NO_PUBLIC_WORKSPACE_SAVE_GENERATION_BUDGET');case['workspaceBefore17']=workspace
 old=repository()/'evidence/missionintegrated16/candidates'/OLD_CANDIDATE
 proof={'format':'aeris-journal17-original-cold-backup','version':1,'candidatePath':str(old),'candidateSHA256':OLD_CANDIDATE,'androidEvidenceRoot':str(d.root),'coldBeforeRef':before,'coldAfterRef':after,'installedPathRef':path_ref,'installedSHARef':sha_ref,'backupCaptureRef':backup['captureReceiptRef'],'backupSHA256':backup['sha256'],'backupBytes':backup['bytes']}
 original=encoded(proof);ref=owner.write('native17-cold-backup-proof.json',proof);case['coldProof17']={'path':owner.root/'reports/native17-cold-backup-proof.json','sha256':sha(original),'ref':ref};case['backup17']=backup;d._backup17=True;return proof

def independent_receiver(owner,case,node,*,deadline_ns):
 """Fresh OLD-source child; full stdout/stderr/capture preserved, no fallback."""
 need(case.get('backup17')is not None and 'receiver17'not in case,'ONE_FRESH_RECEIVER_BEFORE_INSTALL')
 repo=repository();p=case['coldProof17'];argv=[sys.executable,'-B',str(repo/'planning/nativejournal17/receiver17.py'),'--backup',case['backup17']['path'],'--cold-proof',str(p['path']),'--cold-proof-sha',p['sha256'],'--new-source',owner.manifest['native']['sourceSHA256'],'--expected-head','ROOT','--node',str(node)]
 started=time.monotonic_ns()
 owner.budget.tick('commands')
 with owner.budget.operation({'commands':32768+4096+8192,'external_task':32768+4096+8192}):result=capture_command(owner.budget,'external_task',argv,deadline_ns=deadline_ns,stdout_limit=32768,stderr_limit=4096)
 stdout=result['stdout'];stderr=result['stderr'];record={'format':'aeris-native17-receiver-original-capture','version':1,'argv':argv,'startedHostNs':started,'finishedHostNs':time.monotonic_ns(),'exit':result['exit'],'captureComplete':result['captureComplete'],'failure':None if result['failure']is None else str(result['failure']),'pid':result['pid'],'stdoutBytes':len(stdout),'stderrBytes':len(stderr),'stdoutSHA256':sha(stdout),'stderrSHA256':sha(stderr),'authorityGranted':False}
 owner.budget.write('external_task',owner.root/'reports/native17-receiver-stdout.bin',stdout)
 owner.budget.write('external_task',owner.root/'reports/native17-receiver-stderr.bin',stderr)
 owner.write('native17-receiver-capture.json',record)
 need(result['failure']is None and result['captureComplete']and result['exit']==0 and not stderr,'RECEIVER_COMPLETE_POSITIVE_EXIT')
 q=decode(stdout);need(q.get('format')=='aeris-journal17-fresh-cold-receiver-result'and q.get('readOnly')is True and q.get('actorsStarted')is False,'RECEIVER_SCOPE')
 report=base64.b64decode(q['reportBase64'],validate=True);plan=base64.b64decode(q['planBase64'],validate=True);need(sha(report)==q['reportSHA256']and sha(plan)==q['planSHA256']and len(report)<=16384 and len(plan)<=4096,'RECEIVER_ORIGINAL_DIGEST_AND_BOUND')
 r=decode(report);need(r.get('status')=='COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT'and r.get('package')==PACKAGE and r.get('oldAPKSHA256')==OLD_APK and r['backupSHA256']==case['backup17']['sha256']and r['newSourceSHA256']==owner.manifest['native']['sourceSHA256']and r.get('coldProofSHA256')==p['sha256']and r.get('expectedHostRegistryHead')=='ROOT'and len(r['originals'])==8 and len({x['generation']for x in r['originals']})==8 and all(re.fullmatch('[a-f0-9]{32}',x['generation'])and x['disposition']=='UNUSED'and x['sourceClosedStatusBound']is False and x['bytes']==23 and x['sha256']==sha(b'AERIS_INPUT_JOURNAL_V2\n')for x in r['originals']),'EXACT_INITIAL8_UNUSED_NO_CLOSURE_CREDIT')
 # Preserve exact returned bytes, not a host-generated replacement manifest.
 owner.budget.write('external_task',owner.root/'reports/native17-receiver-original.json',report)
 owner.budget.write('external_task',owner.root/'reports/native17-plan-original.txt',plan)
 case['receiver17']={'raw':report,'value':r,'plan':plan,'planSHA256':sha(plan),'reportSHA256':sha(report)};return r

def install_upgrade(owner,case,*,deadline_ns):
 from .candidate import load
 d=case['device'];need(case.get('receiver17')is not None and not getattr(d,'_install17_attempted',False),'POSITIVE_RECEIVER_BEFORE_ONE_UPGRADE')
 cold_ref=d._cold_absence(deadline_ns);path_ref,sha_ref=d._installed_sha(OLD_APK,deadline_ns);m=load(owner.candidate,owner.digest);apk=owner.candidate/'native.apk';need(sha(apk.read_bytes())==m['native']['APK_SHA256'],'SELECTED_UPGRADE_APK')
 d._install17_attempted=True
 from .install17 import authorize_install17,install_success17
 authorize_install17(d,owner.candidate,owner.digest,m,case,cold_ref=cold_ref,path_ref=path_ref,sha_ref=sha_ref)
 try:out=d.command(['install','-r',str(apk)],deadline_ns=deadline_ns,maximum_bytes=2048)
 finally:d._install_authorization=None
 need(install_success17(out),'INSTALL_R_ORIGINAL_SUCCESS');install_ref=d.last_command_ref
 path_ref,sha_ref=d._installed_sha(m['native']['APK_SHA256'],deadline_ns);cold=d._cold_absence(deadline_ns)
 proof={'format':'aeris-native17-same-package-upgrade','version':1,'package':PACKAGE,'oldAPKSHA256':OLD_APK,'newAPKSHA256':m['native']['APK_SHA256'],'sourceSHA256':m['native']['sourceSHA256'],'candidateSHA256':owner.digest,'receiverSHA256':case['receiver17']['reportSHA256'],'installCommandRef':install_ref,'installedPathRef':path_ref,'installedSHARef':sha_ref,'coldAfterRef':cold,'noClearWipeUninstall':True,'counterResetOrRefund':False,'authorityRestorable':False}
 case['upgrade17']=proof;owner.write('native17-upgrade.json',proof)
 authorization=d.store.receipt('native17-upgrade-original.json',proof)
 private=d.command(['shell','run-as',PACKAGE,'pwd','-P'],deadline_ns=deadline_ns,maximum_bytes=256);need(private==('/data/user/0/'+PACKAGE+'\n').encode(),'SAME_PRIVATE_DIRECTORY')
 domain={'format':'aeris-root-observed-development-application-domain','version':1,'nativeLifecycleMigration17':True,'applicationId':PACKAGE,'privateFilesDirectory':'/data/user/0/'+PACKAGE+'/files','serial':d.serial,'sourceSHA256':m['native']['sourceSHA256'],'APKSHA256':m['native']['APK_SHA256'],'candidateSHA256':owner.digest,'authorizationRef':authorization,'installedPathRef':path_ref,'installedSHARef':sha_ref,'actualPrivateDirectoryCommandRef':d.last_command_ref,'nativeReportedApplicationId':False,'retainedInventoryRef':case['native'].retained_inventory_ref,'oldApplicationOriginalsRetained':True,'noAuthorityRestore':True}
 probe=case['native'];probe.application_domain=domain;probe.application_domain_ref=d.store.receipt('application-domain17-observation.json',domain);return proof

def admin(owner,case,operation,*,deadline_ns):
 """Each operation at most once. Receipt uncertainty cannot authorize resend."""
 d=case['device'];need((case.get('upgrade17')is not None or case.get('adoption17')is not None)and operation in('PREVIEW','APPLY'),'UPGRADE_BEFORE_ADMIN')
 attempted=case.setdefault('adminAttempts17',set());need(operation not in attempted,'NO_ADMIN_RETRY');attempted.add(operation)
 nonce=secrets.token_hex(16);plan=case['receiver17']['plan'];args=['shell','am','broadcast','-a',ADMIN_ACTION,'-n',ADMIN_COMPONENT,'--es','requestNonce',nonce,'--es','operation',operation,'--es','planBase64',base64.b64encode(plan).decode()]
 with d.live_log('AERIS_PRODUCT_STATUS',deadline_ns=deadline_ns)as stream:
  d.command(args,deadline_ns=deadline_ns,maximum_bytes=2048);command_ref=d.last_command_ref;ack=None
  for row in stream:
   if row.get('requestNonce')==nonce:ack=row;break
  need(type(ack)is dict,'ADMIN_ORIGINAL_NONCE_ACK');ack_ref=d.observer.last_ref
  if operation=='PREVIEW':
   need(ack.get('status')=='NON_DURABLE_REFUSED_REGISTRY_ENROLLMENT_REQUIRED'and ack.get('durableReceipt')is False and ack.get('authorityRestorable')is False,'PREVIEW_UNENROLLED_NON_DURABLE_ONLY')
   owner.write('native17-preview.json',{'originalACK':ack,'ACKRef':ack_ref,'commandRef':command_ref,'scope':'EXTERNALLY_CAPTURED_NOT_APP_DURABLE'});return ack
  expected='files/product-input-lifecycle17/request-'+nonce+'.json';need(ack.get('path')==expected and ack.get('durableReceipt')is True and type(ack.get('bytes'))is int and 0<ack['bytes']<=4096 and re.fullmatch('[a-f0-9]{64}',ack.get('registryHead','')),'APPLY_DURABLE_RECEIPT_SCOPE')
  raw=d.command(['shell','run-as',PACKAGE,'cat',expected],deadline_ns=deadline_ns,maximum_bytes=4096);raw_ref=d.last_command['stdoutRef'];need(len(raw)==ack['bytes']and sha(raw)==ack['sha256'],'ORIGINAL_ADMIN_ACK_RECEIPT_SHA')
  value=decode(raw);need(value.get('status')=='ARCHIVED_VERIFIED_NO_AUTHORITY'and value.get('planSHA256')==case['receiver17']['planSHA256']and value.get('independentReceiverSHA256')==case['receiver17']['reportSHA256']and value.get('backupTARSHA256')==case['backup17']['sha256']and value.get('sourceSHA256')==owner.manifest['native']['sourceSHA256']and value.get('authorityRestorable')is False,'APPLY_EXACT_RECEIVER_PLAN_RESULT')
  case['admin17']={'ACK':ack,'ACKRef':ack_ref,'commandRef':command_ref,'receiptRef':raw_ref,'receipt':value,'registryHead':ack['registryHead']};owner.write('native17-apply.json',case['admin17']);return value

def table(path):
 """Rehash full original TARs; bytes are never replaced by these summaries."""
 try:validate_tar_shape(path)
 except ValueError as error:raise ValueError('NATIVE17_COMPLETE_TAR_SHAPE:'+str(error))from error
 rows={};logical=0;seen=set()
 with tarfile.open(path,'r:')as tar:
  for m in tar:
   need(m.name not in seen and len(seen)<8192 and not m.pax_headers and not m.issym()and not m.islnk()and(m.isdir()or m.isfile())and(m.name=='files'or m.name.startswith('files/'))and not any(x in('','..','.')for x in m.name.split('/')),'COMPLETE_TAR_SHAPE');seen.add(m.name)
   if m.isdir():continue
   logical+=m.size;need(logical<=512*2**20,'COMPLETE_TAR_LOGICAL512M');h=hashlib.sha256();n=0
   with tar.extractfile(m)as stream:
    for b in iter(lambda:stream.read(65536),b''):n+=len(b);h.update(b)
   need(n==m.size,'COMPLETE_TAR_MEMBER');rows[m.name]={'bytes':n,'sha256':h.hexdigest()}
 return rows

def workspace17(path):
 """Cold immutable body/head consistency. No deletion, repair or inferred save."""
 prefix='files/betasim-workspace01/';rows=table(path);selected={n:r for n,r in rows.items()if n.startswith(prefix)}
 if not selected:return {'sequence':0,'head':'ROOT','bodySHA256':None,'rows':{}}
 need(sum(r['bytes']for r in selected.values())<=8*2**20,'WORKSPACE8M');head_path=prefix+'HEAD';need(head_path in selected and selected[head_path]['bytes']<=512,'WORKSPACE_HEAD_REQUIRED')
 with tarfile.open(path,'r:')as t:raw=t.extractfile(head_path).read(513)
 m=re.fullmatch(rb'([1-9][0-9]?) ([a-f0-9]{64})\n',raw);need(m is not None,'WORKSPACE_HEAD_SHAPE');sequence=int(m[1]);digest=m[2].decode();need(sequence<=16,'WORKSPACE16_GENERATIONS')
 bodies={}
 for name,row in selected.items():
  if name==head_path:continue
  b=re.fullmatch(re.escape(prefix)+r'([0-9]{4})-([a-f0-9]{64})[.]json',name);need(b is not None and row['bytes']<=2*2**20 and row['sha256']==b[2]and int(b[1])not in bodies,'WORKSPACE_IMMUTABLE_BODY_SHA');bodies[int(b[1])]=b[2]
 need(set(bodies)==set(range(1,sequence+1))and bodies[sequence]==digest,'WORKSPACE_HISTORY_AND_HEAD');return {'sequence':sequence,'head':sha(raw),'bodySHA256':digest,'rows':selected}

def conserved_workspace17(before_path,after_path,saved):
 before=workspace17(before_path);after=workspace17(after_path);r=saved['observation'].get('workspaceSaveReceipt')or{}
 need(r.get('format')=='aeris-verified-native-workspace-save'and r.get('status')=='COMMITTED'and r.get('platform')=='ANDROID'and r.get('verification')=='ORIGINAL_NATIVE_REPLY_ID_SESSION_ACTION_AND_BODY_SHA_VERIFIED'and r.get('authorityRestorable')is False and type(r.get('completionSequence'))is int and r['completionSequence']>0,'GENUINE_PUBLIC_NATIVE_SAVE_RECEIPT')
 need(r.get('previousHead')==before['head']and r.get('head')==saved['head']==after['head']and r.get('bodySha256')==after['bodySHA256']and after['sequence']in(before['sequence'],before['sequence']+1),'EXACT_ONE_AUTHORIZED_WORKSPACE_ADVANCE')
 for name,row in before['rows'].items():
  if name!='files/betasim-workspace01/HEAD':need(after['rows'].get(name)==row,'OLD_IMMUTABLE_WORKSPACE_BODY_PRESERVED')
 return {'oldSequence':before['sequence'],'newSequence':after['sequence'],'oldHead':before['head'],'newHead':after['head'],'newBodySHA256':after['bodySHA256'],'originalHeadPreservedInBeforeTAR':True,'publicSaveCompletionSequence':r['completionSequence']}

def archive_check(owner,case,export,stage,*,deadline_ns,selected_closed=()):
 """Fresh read-only cold registry replay, full old/private byte conservation."""
 checks=case.setdefault('archiveChecks17',set());need(stage in('migration','first-close','final-close')and stage not in checks and case.get('admin17')is not None,'ONE_COLD_CHECK_PER_STAGE');checks.add(stage)
 source=repository()/'planning/nativejournal17/archive_verifier17.py';receiver=owner.root/'reports/native17-receiver-original.json';previous=case.get('lastRegistryProof17');head=case['admin17']['registryHead']if stage=='migration'else previous['registryHead']
 argv=[sys.executable,'-B',str(source),'--backup',export['path'],'--backup-sha',export['sha256'],'--expected-head',head,'--candidate-sha',owner.digest,'--receiver',str(receiver)]
 for generation in selected_closed:argv.extend(['--selected-closed',generation])
 owner.budget.tick('commands');started=time.monotonic_ns()
 with owner.budget.operation({'commands':65536+4096+8192,'external_task':65536+4096+8192}):r=capture_command(owner.budget,'external_task',argv,deadline_ns=deadline_ns,stdout_limit=65536,stderr_limit=4096)
 stdout=r['stdout'];stderr=r['stderr'];prefix='native17-'+stage
 owner.budget.write('external_task',owner.root/'reports'/(prefix+'-stdout.bin'),stdout);owner.budget.write('external_task',owner.root/'reports'/(prefix+'-stderr.bin'),stderr)
 owner.write(prefix+'-capture.json',{'format':'aeris-native17-cold-registry-original-command','argv':argv,'pid':r['pid'],'startedHostNs':started,'finishedHostNs':time.monotonic_ns(),'exit':r['exit'],'captureComplete':r['captureComplete'],'failure':None if r['failure']is None else str(r['failure']),'stdoutSHA256':sha(stdout),'stdoutBytes':len(stdout),'stderrSHA256':sha(stderr),'stderrBytes':len(stderr)})
 need(r['failure']is None and r['captureComplete']and r['exit']==0 and not stderr,'COMPLETE_COLD_REGISTRY_VERIFIER');proof=decode(stdout)
 need(proof.get('format')=='aeris-journal17-original-archive-index-proof'and proof.get('status')=='SOURCE_BOUND_ORIGINAL_ARCHIVE_INDEX_JOIN_VERIFIED'and proof.get('sourceCandidateSHA256')==owner.digest and proof.get('nativeTARSHA256')==export['sha256']and proof.get('externalHostAnchorVerified')is True and proof.get('pendingTransactions')==0 and proof.get('allArchiveReceiversVerified')is True,'AUTHORITATIVE_FULL_REGISTRY_REPLAY')
 need(previous is None or all(type(v)is int and type(proof['counters'].get(k))is int and proof['counters'][k]>=v for k,v in previous['counters'].items()),'MONOTONIC_REGISTRY_COUNTERS')
 workspace=None if stage=='migration'else conserved_workspace17(case['backup17']['path'],export['path'],case['firstNative17']['savedWorkspace'])
 before=table(case['backup17']['path']);after=table(export['path']);moved={x['generation']for x in case['receiver17']['value']['originals']};plan=case['receiver17']['planSHA256']
 for name,row in before.items():
  if workspace is not None and name=='files/betasim-workspace01/HEAD':continue
  match=re.fullmatch('files/product-input01/([a-f0-9]{32})[.]aj02',name)
  target='files/product-input-archives17/'+plan+'/'+match[1]+'.aj02'if match and match[1]in moved else name
  need(after.get(target)==row,'ALL_OLD_PRIVATE_BYTES_PRESERVED:'+name)
  if target!=name:need(name not in after,'EXACTLY_ONE_ORIGINAL_LOCATION')
 value={'format':'aeris-native17-original-cold-stage-proof','version':1,'stage':stage,'candidateSHA256':owner.digest,'sourceOriginalBackupSHA256':case['backup17']['sha256'],'postTARSHA256':export['sha256'],'workspaceAdvance':workspace,'externalPreviousRegistryHead':head,'oldFileCount':len(before),'oldTableSHA256':sha(encoded(before)),'afterTableSHA256':sha(encoded(after)),'originalPrivateBytesConserved':True,'original8UnusedArchivedByteExact':True,'registryProofSHA256':sha(stdout),'registryHead':proof['registryHead'],'pendingTransactions':proof['pendingTransactions'],'counters':proof['counters'],'selectedClosedGenerations':list(selected_closed),'noAuthorityRestore':True,'flightAcceptance':False}
 owner.write(prefix+'-proof.json',value);case['lastRegistryProof17']=proof
 if stage=='migration':case['device'].migration17_verified=True
 if stage=='final-close':
  path=owner.root/'reports/native-journal17-archive-proof.json';ref=owner.budget.write('external_task',path,stdout);case['archiveProofRef17']={'path':str(path),'bytes':len(stdout),'sha256':sha(stdout)}
 return proof

def verify_upgrade_original(root,ref,manifest):
 """Cold installed package/source/OnceStore joins for the explicit17 migration."""
 from .once_reader import read_ref,read_receipts
 from .status15_reader import command
 domain=decode(read_ref(root,ref))
 if domain.get('nativeLifecycleAdoption17')is True:
  from .adoption17 import verify_adoption_domain17
  return verify_adoption_domain17(root,ref,manifest)
 need(domain in read_receipts(root,'diagnostic')and domain.get('nativeLifecycleMigration17')is True and domain.get('format')=='aeris-root-observed-development-application-domain'and domain.get('applicationId')==PACKAGE and domain.get('sourceSHA256')==manifest['native']['sourceSHA256']and domain.get('APKSHA256')==manifest['native']['APK_SHA256']and domain.get('serial')=='emulator-5582'and domain.get('privateFilesDirectory')=='/data/user/0/'+PACKAGE+'/files'and domain.get('candidateSHA256')==sha(__import__('aeris_runtime.candidate',fromlist=['canonical']).canonical(manifest)),'COLD_MIGRATED_APPLICATION_DOMAIN')
 q=decode(read_ref(root,domain['authorizationRef']));need(q in read_receipts(root,'diagnostic')and q.get('format')=='aeris-native17-same-package-upgrade'and q.get('oldAPKSHA256')==OLD_APK and q.get('newAPKSHA256')==manifest['native']['APK_SHA256']and q.get('noClearWipeUninstall')is True and q.get('counterResetOrRefund')is False,'COLD_UPGRADE_AUTHORIZATION')
 from .install17 import read_install17,install_success17
 install,_,remote,out=read_install17(root,q['installCommandRef'],manifest);need(remote==['install','-r',str(Path(os.environ['AERIS_CANDIDATE_DIR'])/'native.apk')]and install_success17(out),'COLD_ONCE_INSTALL_R')
 p,_,remote,out=command(root,domain['installedPathRef']);need(remote==['pm','path',PACKAGE]and out.startswith(b'package:/')and len(out.splitlines())==1,'COLD_NEW_INSTALLED_PATH');location=out.decode().strip()[8:]
 h,_,remote,out=command(root,domain['installedSHARef']);need(remote==['sha256sum',location]and out.decode().split()[0]==manifest['native']['APK_SHA256']and install['endedHostNs']<=p['startedHostNs']<=p['endedHostNs']<=h['startedHostNs'],'COLD_NEW_INSTALLED_SHA')
 _,_,remote,out=command(root,domain['actualPrivateDirectoryCommandRef']);need(remote==['run-as',PACKAGE,'pwd','-P']and out==('/data/user/0/'+PACKAGE+'\n').encode(),'COLD_SAME_PRIVATE_DIRECTORY');return domain
