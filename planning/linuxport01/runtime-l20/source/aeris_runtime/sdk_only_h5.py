"""Original cold command/TAR joins for SDK-only close, never archive pending-state proof."""
from pathlib import Path
import hashlib,json,re
from .installclosure_h4 import original_command,private_table,original_private_table,package_state,safe_code_path,need,PACKAGE,PRIVATE,COLD,STAT
from .once_reader import read_ref,read_receipts
from .status15_reader import journal

def verify(owner,proof):
 c=owner.case;r=c['device'].root;v=proof.get('sdkOnlyH5');need(type(v)is dict and owner.root.name in('m401','m402')and v.get('candidateSHA256')==owner.digest,'SDK_ONLY_EXACT_CURRENT_SOURCE')
 prep=json.loads(read_ref(r,v['preparationRef']));need(prep in read_receipts(r,'diagnostic')and prep.get('actualUID0')is True and prep.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','SDK_ONLY_ORIGINAL_ROOT_PREPARATION');path=safe_code_path(v['baseAPK']);samples=v['samples'];need(type(samples)is list and len(samples)==2 and[s['offsetSeconds']for s in samples]==[0,30],'SDK_ONLY_FIXED_SAMPLES');boots=[];need(samples[1]['targetHostNs']-samples[0]['targetHostNs']==30_000_000_000,'SDK_ONLY_ORIGINAL_FIXED_TARGETS')
 for s in samples:
  refs=s['commandRefs'];need(original_command(r,refs['boot'],['cat','/proc/sys/kernel/random/boot_id'])[0]['startedHostNs']>=s['targetHostNs'],'SDK_ONLY_SAMPLE_NOT_BEFORE_TARGET')
  def cmd(k,args):return original_command(r,refs[k],args)[1]
  boot=cmd('boot',['cat','/proc/sys/kernel/random/boot_id']).decode().strip();need(re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot)is not None,'SDK_ONLY_ACTUAL_BOOT');boots.append(boot)
  need(cmd('user',['am','get-current-user'])==b'0\n'and cmd('cold',['sh','-c',COLD])==b'ABSENT\n','SDK_ONLY_USER_AND_COLD');need(cmd('path',['pm','path',PACKAGE]).decode().strip()=='package:'+path,'SDK_ONLY_PM_PATH');need(cmd('sha',['sha256sum',path]).decode().split()==[owner.manifest['native']['APK_SHA256'],path],'SDK_ONLY_SELECTED_SHA');need(package_state(cmd('dump',['dumpsys','package',PACKAGE]),broken=False)==v['baseAPK'],'SDK_ONLY_PARSED_PM_UID')
 need(prep['kernelBootUUID']==boots[0]and boots[0]==boots[1]and boots[0]!=v['priorKernelBootUUID'],'SDK_ONLY_FRESH_STABLE_BOOT')
 need(original_command(r,v['finalUIDRef'],['id','-u'])[1]==b'0\n'and original_command(r,v['finalStatRef'],['sh','-c',STAT])[1].startswith(b'directory 10141 10141 ')and original_command(r,v['finalColdRef'],['sh','-c',COLD])[1]==b'ABSENT\n','SDK_ONLY_ACTUAL_ROOT_PRIVATE_COLD')
 backup=v['rootPrivateBackup'];p=Path(backup['path']);need(p==r.parent/'native-restart-metadata.tar'and p.is_file()and not p.is_symlink()and hashlib.sha256(p.read_bytes()).hexdigest()==backup['sha256'],'SDK_ONLY_EXACT_CURRENT_BACKUP');cap=json.loads(read_ref(r,backup['captureReceiptRef']));need(cap in read_receipts(r,'diagnostic')and cap.get('captureComplete')is True and cap.get('failure')is None and type(cap.get('exit'))is int and cap['exit']==0 and cap.get('bytesRetained')==p.stat().st_size and cap.get('path')==str(p)and cap.get('fullOriginalFiles')is True and read_ref(r,cap['stderrRef'])==b'','SDK_ONLY_ORIGINAL_TAR_CAPTURE');argv=json.loads(read_ref(r,cap['argvRef']));need(argv==[c['device'].adb,'-s','emulator-5582','exec-out','tar','-C',PRIVATE,'-cf','-','files'],'SDK_ONLY_FIXED_ROOT_TAR');row,cold,_=original_command(r,v['afterBackupColdRef'],['sh','-c',COLD]);need(cold==b'ABSENT\n'and row['startedHostNs']>=cap['finishedHostNs'],'SDK_ONLY_COLD_AFTER_TAR');need(private_table(p)==original_private_table(owner.repo),'SDK_ONLY_PRIMARY70FILES5DIRS_CONSERVED')
 return {'originalPrivateBytesConserved':True,'pendingTransactions':'NOT_CLAIMED_SDK_ONLY','actualKernelBootUUID':boots[0],'flightAcceptance':False}

def require_qualification(path,digest,candidate):
 from .paths import repository
 from .rc01 import ref_file
 p=Path(path).absolute();need(p.is_relative_to(repository()/'evidence/betarc01')and p.is_file()and p.stat().st_size<=32768 and not any(q.is_symlink()for q in[p,*p.parents]),'H5_ROOT_PROOF_SCOPE');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'H5_ROOT_PROOF_SHA');v=json.loads(raw);need(v.get('format')=='aeris-h5-root-positive-sdk-cold-acceptance'and v.get('version')==1 and v.get('status')=='ROOT_COLD_VERIFIED_TWO_NORMAL_SDK_BOOTS_NOT_FLIGHT'and v.get('candidateSHA256')==candidate and v.get('slots')==['m401','m402']and v.get('authorityRestorable')is False and v.get('SDKExitZeroNoForcedKillBoth')is True,'H5_TWO_SAME_RELEASE_POSITIVE_BOOT_PROOF');boots=v.get('actualKernelBootUUIDs');need(type(boots)is list and len(boots)==2 and all(type(b)is str and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',b)for b in boots)and boots[0]!=boots[1],'H5_DISTINCT_ACTUAL_BOOTS');refs=v.get('originalEvidence');roles={'m401Observation','m401Guardian','m401SDKProcess','m401Private','m402Observation','m402Guardian','m402SDKProcess','m402Private'};need(type(refs)is list and len(refs)==8 and{r.get('role')for r in refs}==roles,'H5_EXACT_ORIGINAL_ROLES')
 for row in refs:ref_file(row['ref'])
 return {'status':'SOURCE_BOUND_H5_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE','authorityRestorable':False}
