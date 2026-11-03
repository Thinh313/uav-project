"""Exact durable install17 authorization and cold reader. Never dispatches actors."""
from pathlib import Path
import base64,hashlib,json,os,re,sys
from .once_reader import read_ref,read_receipts,unique
from .metadata_budget import encoded
from .paths import repository
PACKAGE='vn.rtr.aeris.betasim09';OLD_APK='8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1'
INSTALL_SUCCESS17=(b'Success\n',b'Performing Streamed Install\nSuccess\n')
def install_success17(raw):return type(raw)is bytes and raw in INSTALL_SUCCESS17
FIELDS={'format','version','package','serial','candidateDir','candidateSHA256','APKPath','APKSHA256','nativeSourceSHA256','certificateSHA256','expectedOldAPKSHA256','preparedHostNs','coldBeforeCommandRef','installedPathCommandRef','installedSHACommandRef','receiverReportSHA256','receiverCaptureSHA256','coldProofSHA256','backupTARSHA256'}
def need(v,n):
 if not v:raise ValueError('INSTALL17_'+n)
def sha(b):return hashlib.sha256(b).hexdigest()
def json_bytes(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in()).throw(ValueError('INSTALL17_NONFINITE')))
def regular(p,maximum):
 p=Path(p).absolute();need(not any(v.is_symlink()for v in[p,*p.parents]),'REGULAR_PATH');st=p.stat();need(p.is_file()and st.st_nlink==1 and 0<=st.st_size<=maximum,'REGULAR_BOUND');b=p.read_bytes();need(len(b)==st.st_size,'STABLE_LENGTH');return b

def file_digest17(p,maximum):
 p=Path(p).absolute();need(not any(v.is_symlink()for v in[p,*p.parents]),'REGULAR_PATH');st=p.stat();need(p.is_file()and st.st_nlink==1 and 0<=st.st_size<=maximum,'REGULAR_BOUND');digest=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(65536),b''):size+=len(b);need(size<=maximum,'ORIGINAL_BACKUP_BOUND');digest.update(b)
 need(size==st.st_size,'ORIGINAL_BACKUP_STABLE_LENGTH');return digest.hexdigest(),size

def authorization17(root,ref,*,source=None):
 from .candidate import load,sha as file_sha,CERT
 from .status15_reader import command
 root=Path(root).absolute();need(ref.get('path')=='receipts/diagnostic.jsonl'and ref.get('version')==3,'DURABLE_AUTHORIZATION_REF');raw=read_ref(root,ref);a=json_bytes(raw);need(sum(q==a for q in read_receipts(root,'diagnostic'))==1 and type(a)is dict and set(a)==FIELDS,'EXACT_DURABLE_AUTHORIZATION_MEMBERSHIP')
 need(a['format']=='aeris-native17-development-install-authorization'and type(a['version'])is int and a['version']==1 and a['package']==PACKAGE and a['serial']=='emulator-5582'and a['expectedOldAPKSHA256']==OLD_APK and a['certificateSHA256']==CERT,'EXACT_AUTHORIZATION_SCOPE')
 need(type(a['preparedHostNs'])is int and a['preparedHostNs']>=0 and all(type(a[k])is str and re.fullmatch('[a-f0-9]{64}',a[k])for k in('candidateSHA256','APKSHA256','nativeSourceSHA256','receiverReportSHA256','receiverCaptureSHA256','coldProofSHA256','backupTARSHA256')),'TYPED_AUTHORIZATION_FIELDS')
 candidate=Path(a['candidateDir']);apk=Path(a['APKPath']);need(candidate.is_absolute()and apk.is_absolute()and candidate==candidate.resolve()and apk==candidate/'native.apk','EXACT_SELECTED_APK_PATH');m=load(candidate,a['candidateSHA256']);need(m['native']['package']==PACKAGE and m['native']['APK_SHA256']==a['APKSHA256']==file_sha(apk)and m['native']['sourceSHA256']==a['nativeSourceSHA256']and(source is None or source==a['nativeSourceSHA256']),'SELECTED_SOURCE_APK_CANDIDATE')
 need(root.name=='android-api'and root.parent.parent.name=='sessions','EXACT_ORIGINAL_STORE_SCOPE');campaign=root.parents[2];reports=campaign/'reports';receiver=regular(reports/'native17-receiver-original.json',16384);capture=regular(reports/'native17-receiver-capture.json',8192);cold=regular(reports/'native17-cold-backup-proof.json',8192);r=json_bytes(receiver);c=json_bytes(capture);p=json_bytes(cold)
 need(sha(receiver)==a['receiverReportSHA256']and sha(capture)==a['receiverCaptureSHA256']and sha(cold)==a['coldProofSHA256'],'ORIGINAL_RECEIVER_COLD_DIGESTS')
 need(r.get('status')=='COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT'and r.get('package')==PACKAGE and r.get('oldAPKSHA256')==OLD_APK and r.get('newSourceSHA256')==a['nativeSourceSHA256']and r.get('backupSHA256')==a['backupTARSHA256']and r.get('coldProofSHA256')==a['coldProofSHA256']and r.get('expectedHostRegistryHead')=='ROOT','RECEIVER_SELECTION_BINDING')
 originals=r.get('originals');need(type(originals)is list and len(originals)==8 and len({v.get('generation')for v in originals})==8 and all(re.fullmatch('[a-f0-9]{32}',v.get('generation',''))and v.get('disposition')=='UNUSED'and v.get('sourceClosedStatusBound')is False and type(v.get('bytes'))is int and v['bytes']==23 and v.get('sha256')==sha(b'AERIS_INPUT_JOURNAL_V2\n')for v in originals),'RECEIVER_EXACT8_UNUSED')
 need(c.get('format')=='aeris-native17-receiver-original-capture'and type(c.get('exit'))is int and c['exit']==0 and c.get('captureComplete')is True and c.get('failure')is None and type(c.get('pid'))is int and c['pid']>0 and c.get('stderrBytes')==0 and c.get('stderrSHA256')==sha(b''),'RECEIVER_COMPLETE_ORIGINAL_CAPTURE')
 stdout=regular(reports/'native17-receiver-stdout.bin',32768);stderr=regular(reports/'native17-receiver-stderr.bin',4096);need(not stderr and sha(stdout)==c.get('stdoutSHA256')and len(stdout)==c.get('stdoutBytes'),'RECEIVER_COMPLETE_OUTPUT_SHA');e=json_bytes(stdout);need(e.get('format')=='aeris-journal17-fresh-cold-receiver-result'and e.get('readOnly')is True and e.get('actorsStarted')is False and e.get('reportSHA256')==sha(receiver)and base64.b64decode(e['reportBase64'],validate=True)==receiver,'RECEIVER_ORIGINAL_RETURNED_BYTES')
 need(p.get('format')=='aeris-journal17-original-cold-backup'and p.get('androidEvidenceRoot')==str(root)and p.get('backupSHA256')==a['backupTARSHA256']and p.get('candidateSHA256')=='9e01e2dc55f4c1545388204674b236bb1babf1a6da97fcbc57d383ffaac0190c','COLD_BACKUP_SELECTION')
 backup=root.parent/'native-restart-metadata.tar';backup_sha,backup_size=file_digest17(backup,64*2**20);need(backup_sha==a['backupTARSHA256']and backup_size==p.get('backupBytes'),'ORIGINAL_BACKUP_FULL_BYTES')
 argv=c.get('argv');need(type(argv)is list and len(argv)==15 and argv==[sys.executable,'-B',str(repository()/'planning/nativejournal17/receiver17.py'),'--backup',str(backup),'--cold-proof',str(reports/'native17-cold-backup-proof.json'),'--cold-proof-sha',a['coldProofSHA256'],'--new-source',a['nativeSourceSHA256'],'--expected-head','ROOT','--node',argv[-1]]and Path(argv[-1]).is_absolute(),'RECEIVER_EXACT_FRESH_SOURCE_ARGV')
 pre=[]
 for k in('coldBeforeCommandRef','installedPathCommandRef','installedSHACommandRef'):pre.append(command(root,a[k]))
 location=pre[1][3].decode().strip();need(pre[0][2]==['sh','-c','if pidof '+PACKAGE+' >/dev/null; then echo RUNNING; else echo ABSENT; fi']and pre[0][3]==b'ABSENT\n'and pre[1][2]==['pm','path',PACKAGE]and location.startswith('package:/')and'\n'not in location and pre[2][2]==['sha256sum',location[8:]]and pre[2][3].decode().split()[0]==OLD_APK,'ORIGINAL_COLD_OLD_APK_PRECHECKS')
 need(pre[0][0]['endedHostNs']<=pre[1][0]['startedHostNs']<=pre[1][0]['endedHostNs']<=pre[2][0]['startedHostNs']<=pre[2][0]['endedHostNs']<=a['preparedHostNs'],'ORIGINAL_PRECHECK_ORDER');return a

def authorize_install17(device,candidate,digest,manifest,case,*,cold_ref,path_ref,sha_ref):
 from .candidate import CERT
 reports=Path(device.root).parents[2]/'reports';a={'format':'aeris-native17-development-install-authorization','version':1,'package':PACKAGE,'serial':device.serial,'candidateDir':str(candidate),'candidateSHA256':digest,'APKPath':str(Path(candidate)/'native.apk'),'APKSHA256':manifest['native']['APK_SHA256'],'nativeSourceSHA256':manifest['native']['sourceSHA256'],'certificateSHA256':CERT,'expectedOldAPKSHA256':OLD_APK,'preparedHostNs':device.now(),'coldBeforeCommandRef':cold_ref,'installedPathCommandRef':path_ref,'installedSHACommandRef':sha_ref,'receiverReportSHA256':case['receiver17']['reportSHA256'],'receiverCaptureSHA256':sha(regular(reports/'native17-receiver-capture.json',8192)),'coldProofSHA256':case['coldProof17']['sha256'],'backupTARSHA256':case['backup17']['sha256']};ref=device.store.receipt('native17-install-authorization.json',a);context={'ref':ref,'APKPath':a['APKPath'],'commandVersion':9};authorization17(device.root,ref,source=manifest['native']['sourceSHA256']);device._install_authorization=context;return ref

def install_context17(device,args,*,consume=False):
 need(device.__class__.__name__=='AndroidDomain17'and device.serial=='emulator-5582'and getattr(getattr(device,'observer',None),'tag',None)=='AERIS_PRODUCT_STATUS','EXACT_NATIVE17_OWNED_DEVICE')
 context=getattr(device,'_install_authorization',None);need(type(context)is dict and set(context)=={'ref','APKPath','commandVersion'}and type(context['commandVersion'])is int and context['commandVersion']==9,'ONE_SOURCE_BOUND_INSTALL_R_AUTHORIZATION')
 need(device.serial=='emulator-5582'and list(args)==['install','-r',context['APKPath']],'EXACT_INSTALL_ARGV');a=authorization17(device.root,context['ref']);need(a['candidateDir']==os.environ.get('AERIS_CANDIDATE_DIR')and a['candidateSHA256']==os.environ.get('AERIS_CANDIDATE_SHA256'),'LIVE_SELECTED_CANDIDATE');key=(context['ref']['path'],context['ref']['offset'],context['ref']['sha256']);used=getattr(device,'_install17_consumed',set());need(key not in used,'AUTHORIZATION_ALREADY_CONSUMED_NO_RETRY')
 if consume:device._install17_consumed=used|{key}
 return {'ref':dict(context['ref']),'APKPath':context['APKPath'],'commandVersion':9}

def verify_install17_row(root,row,remote,out,source,*,allow_failed=False):
 required={'format','version','sequence','argvRef','startedHostNs','endedHostNs','exit','stdoutRef','stderrRef','captureComplete','failure','authorizationRef'};need(type(row)is dict and set(row)==required and row['format']=='aeris-command'and type(row['version'])is int and row['version']==9 and type(row['sequence'])is int and row['sequence']>0 and sum(q==row for q in read_receipts(root,'command'))==1,'EXACT_ORIGINAL_COMMAND9_MEMBERSHIP')
 a=authorization17(root,row['authorizationRef'],source=source);need(type(row['startedHostNs'])is int and type(row['endedHostNs'])is int and a['preparedHostNs']<=row['startedHostNs']<=row['endedHostNs']and row['endedHostNs']-row['startedHostNs']<=70_000_000_000,'ORIGINAL_INSTALL_CLOCK');argv=json_bytes(read_ref(root,row['argvRef']));err=read_ref(root,row['stderrRef']);actual=read_ref(root,row['stdoutRef']);need(type(argv)is list and len(argv)==6 and argv==[argv[0],'-s','emulator-5582','install','-r',a['APKPath']]and type(argv[0])is str and remote==['install','-r',a['APKPath']]and actual==out and len(actual)<=2049 and len(err)<=2049,'ORIGINAL_INSTALL_ARGV_OUTPUT')
 need(type(row['captureComplete'])is bool and(row['exit']is None or type(row['exit'])is int)and(row['failure']is None or type(row['failure'])is str),'TYPED_COMMAND_OUTCOME')
 if not allow_failed:need(row['captureComplete']is True and row['exit']==0 and row['failure']is None and not err and install_success17(out),'INSTALL_COMPLETE_SUCCESS_REQUIRED')
 return 2048

def read_install17(root,ref,manifest,*,allow_failed=False):
 from .status15_reader import journal
 row=journal(root,ref,'command');argv=json_bytes(read_ref(root,row['argvRef']));out=read_ref(root,row['stdoutRef']);remote=argv[3:];verify_install17_row(root,row,remote,out,manifest['native']['sourceSHA256'],allow_failed=allow_failed);a=authorization17(root,row['authorizationRef'],source=manifest['native']['sourceSHA256']);need(a['candidateSHA256']==sha(__import__('aeris_runtime.candidate',fromlist=['canonical']).canonical(manifest))and a['APKSHA256']==manifest['native']['APK_SHA256'],'EXACT_COLD_SELECTED_MANIFEST');return row,argv,remote,out
