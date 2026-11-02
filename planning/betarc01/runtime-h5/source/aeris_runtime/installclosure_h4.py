"""Source-held push-install11 and cold qualification. No automatic retry or authority."""
from pathlib import Path
import hashlib,json,os,re,tarfile
from .once_reader import read_ref,read_receipts,unique
from .status15_reader import journal
from .candidate import load,sha as file_sha,CERT
from .native17 import table as strict_native_table
from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,PACKAGE,PRIVATE,COLD,STAT,need
KNOWN_UID=10141
N02_TAR_SHA='1cfcf1b2cceab0f94563f900c71dd643590285783a1086ffde848587b71ddb08'
import shlex

# adb_install.cpp566bdb531f + file_sync_client.cpp11dde9c5 + LinePrinter9a08113f.
# Non-TTY progress is one stderr summary, bound to the one exact APK and size.
def push_result(out,err,apk,size):
 if out!=b'Performing Push Install\nSuccess\n'or type(err)is not bytes or len(err)>2048:return False
 pattern=re.escape(str(apk).encode())+rb': 1 file pushed, 0 skipped\. [0-9]+\.[0-9] MB/s \('+str(size).encode()+rb' bytes in [0-9]+\.[0-9]{3}s\)\n'
 return re.fullmatch(pattern,err)is not None

class PushInstallDeviceH4(ReadOnlyPackageDevice):
 def bind_current_path(self,path):self.current_base=safe_code_path(path)
 def _command_bound(self,args):
  need(self.serial=='emulator-5582'and self.observer.tag=='AERIS_PRODUCT_STATUS','EXACT_PUSH_SYNC_OWNED_DEVICE')
  if args==['shell','sync']:return 64
  if args in(['shell','pm','path',PACKAGE],['shell','sha256sum',self.current_base],['shell','stat','-c','%F %u %g %s',self.current_base]):return 4096
  if args[:2]==['install','-r']:
   need(getattr(self,'repair_dispatch_active',False)is True and getattr(self,'repair_consumed',False)is True and type(self._install_authorization)is dict and args==['install','-r','--no-streaming','--no-incremental',self._install_authorization['APKPath']],'EXACT_PUSH_INSTALL11_ONCE');return 2048
  return super()._command_bound(args)
 def export_stage(self,stage,*,deadline_ns):
  need(stage in('before','after')and getattr(self,'diagnostic_root_cold_private',False)is True,'ROOT_COLD_FIXED_EXPORT');self._check_budget_actor();target=self.root.parent/('native-original-before-quarantine.tar'if stage=='before'else'native-restart-metadata.tar');need(not target.exists()and not any(p.is_symlink()for p in[target,*target.parents]),'EXCLUSIVE_STAGE_EXPORT')
  with self.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):return self._root_tar(target,self.root.parent.name,64*2**20,True,False,True,deadline_ns)
 def install_push_once(self,apk,auth_ref,*,deadline_ns):
  need(not getattr(self,'repair_consumed',False)and not os.environ.get('ANDROID_PRODUCT_OUT'),'PUSH_ONCE_AND_EXACT_PROGRESS_PATH_ENV');a=verify_authorization(self.root,auth_ref);need(a['APKPath']==str(apk)and deadline_ns<=self.now()+70_000_000_000,'PUSH_EXACT_AUTHORIZED_APK_DEADLINE');verify_dispatch(self.root,auth_ref,a);self.repair_consumed=True;self.repair_dispatch_active=True;self._install_authorization={'ref':auth_ref,'APKPath':str(apk),'commandVersion':11}
  try:
   try:self.command(['install','-r','--no-streaming','--no-incremental',str(apk)],deadline_ns=deadline_ns,maximum_bytes=2048)
   except RuntimeError:
    row=self.last_command
    need(row is not None and row.get('version')==11 and row.get('authorizationRef')==auth_ref and row.get('failure')=='RuntimeError:ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE','ONLY_EXACT_SOURCE_BACKED_PROGRESS_NOTICE')
   ref=self.last_command_ref;verify_push_install(self.root,ref,auth_ref,str(apk));return ref
  finally:self.repair_dispatch_active=False;self._install_authorization=None

def verify_push_install(root,ref,auth_ref,apk):
 a=verify_authorization(root,auth_ref);dispatch=verify_dispatch(root,auth_ref,a);row=journal(root,ref,'command');need(row.get('version')==11 and row.get('authorizationRef')==auth_ref and row.get('captureComplete')is True and type(row.get('exit'))is int and row['exit']==0 and row.get('failure')=='RuntimeError:ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE','PUSH11_ORIGINAL_COMPLETE_PROGRESS_ROW');argv=json.loads(read_ref(root,row['argvRef']));need(argv[1:]==['-s','emulator-5582','install','-r','--no-streaming','--no-incremental',apk]and push_result(read_ref(root,row['stdoutRef']),read_ref(root,row['stderrRef']),apk,Path(apk).stat().st_size),'PUSH11_EXACT_ORIGINAL_ARGV_PROGRESS_SUCCESS');need(dispatch['preparedHostNs']<=row['startedHostNs']<=row['endedHostNs']and row['endedHostNs']-row['startedHostNs']<=70_000_000_000,'PUSH11_ORIGINAL_CLOCK');return row

def require_qualification(path,digest,candidate):
 from .paths import repository
 from .rc01 import ref_file
 p=Path(path).absolute();need(p.is_relative_to(repository()/'evidence/betarc01')and p.is_file()and p.stat().st_size<=32768 and not any(q.is_symlink()for q in[p,*p.parents]),'ROOT_FRESH_BOOT_PROOF_SCOPE');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'ROOT_FRESH_BOOT_PROOF_SHA');v=json.loads(raw);need(v.get('format')=='aeris-h4-root-persistent-install-cold-acceptance'and v.get('version')==1 and v.get('status')=='ROOT_COLD_VERIFIED_PERSISTENT_INSTALL_AND_FRESH_BOOT_NOT_FLIGHT'and v.get('candidateSHA256')==candidate and v.get('slots')==['m301','m302']and v.get('authorityRestorable')is False and v.get('SDKExitZeroNoForcedKillBoth')is True,'ROOT_FRESH_BOOT_QUALIFICATION_REQUIRED');refs=v.get('originalEvidence');roles={'installCommand','guestSync','m301SDKClosure','m301Private','m302Package0','m302Package30','m302SDKClosure','m302Private'};need(type(refs)is list and len(refs)==8 and all(type(r)is dict and set(r)=={'role','ref'}for r in refs)and {r['role']for r in refs}==roles,'ORIGINAL_INSTALL_BOOT_CLOSURE_EVIDENCE');[ref_file(r['ref'])for r in refs];return v


def safe_code_path(value):
 need(type(value)is str and re.fullmatch(r'/data/app/~~[A-Za-z0-9_=-]{1,96}/vn[.]rtr[.]aeris[.]betasim09-[A-Za-z0-9_=-]{1,96}',value)is not None,'SAFE_CURRENT_CODE_PATH');return value+'/base.apk'

def package_state(raw,*,broken):
 text=raw.decode('utf-8');need(len(raw)<=65536 and text.count('Package ['+PACKAGE+'] (')==1,'EXACT_PACKAGE_DUMP');ids=re.findall(r'^    userId=(\d+)$',text,re.M);paths=re.findall(r'^    codePath=(.+)$',text,re.M);need(ids==[str(KNOWN_UID)]and len(paths)==1 and '    versionCode=13017' in text and re.search(r'^    User 0: .* installed=true .*hidden=false .*suspended=false ',text,re.M)is not None,'CURRENT_PACKAGE_UID_VERSION_USER0');safe_code_path(paths[0]);need(('    pkg=null\n'in text)is broken and(broken or re.search(r'^    pkg=(?!null$)\S.+$',text,re.M)is not None),'PACKAGE_PARSE_STATE');return paths[0]

def private_table(path):
 p=Path(path);need(p.is_file()and not p.is_symlink()and p.stat().st_size<=64*2**20,'BOUNDED_PRIVATE_TAR');strict_native_table(p);rows={};dirs={}
 with tarfile.open(p,'r:')as t:
  for m in t:
   n=m.name.rstrip('/');need(n not in rows and n not in dirs and(n=='files'or n.startswith('files/'))and'..'not in Path(n).parts and not Path(n).is_absolute()and(m.isfile()or m.isdir()),'PRIVATE_TAR_EXACT_SAFE_TYPE')
   value={'mode':m.mode,'uid':m.uid,'gid':m.gid}
   if m.isdir():dirs[n]=value
   else:
    need(m.size<=64*2**20,'PRIVATE_FILE_BOUND');raw=t.extractfile(m).read();rows[n]={**value,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 need(len(rows)==70 and len(dirs)==5,'EXACT70FILES5DIRS');return {'files':rows,'directories':dirs}

def selected_apk(candidate,digest,manifest):
 actual=load(candidate,digest);need(actual==manifest and manifest['native']['package']==PACKAGE,'SAME_SELECTED_CANDIDATE');apk=Path(candidate)/'native.apk';receipt_path=Path(candidate)/'native-build-receipt.json';receipt=json.loads(receipt_path.read_bytes());need(hashlib.sha256(receipt_path.read_bytes()).hexdigest()==manifest['native']['buildReceiptSHA256']and receipt['certificateSHA256']==CERT and receipt['package']==PACKAGE and receipt['sourceSHA256']==manifest['native']['sourceSHA256']and receipt['sha256']==manifest['native']['APK_SHA256']==file_sha(apk),'SAME_APK_SOURCE_CERT');return apk

def original_command(root,ref,remote,*,missing_path=None):
 row=journal(root,ref,'command');argv=json.loads(read_ref(root,row['argvRef']),object_pairs_hook=unique);need(argv[:3]==[argv[0],'-s','emulator-5582'],'ORIGINAL_REPAIR_ADB_TARGET');actual=shlex.split(argv[4])if len(argv)==5 and argv[3]=='shell'else argv[3:];need(actual==remote and row.get('version')==3 and row.get('captureComplete')is True,'ORIGINAL_REPAIR_COMMAND_COMPLETE');out=read_ref(root,row['stdoutRef']);err=read_ref(root,row['stderrRef'])
 if missing_path is not None and type(row.get('exit'))is int and row['exit']==1:
  expected=[("stat: '"+missing_path+"': No such file or directory\n").encode(),('stat: '+missing_path+': No such file or directory\n').encode()];need(out==b''and err in expected and row.get('failure')=='RuntimeError:ANDROID_COMMAND_EXIT:1','EXACT_CURRENT_PATH_ENOENT');return row,out,'MISSING_CURRENT_CODE_FILE'
 need(type(row.get('exit'))is int and row['exit']==0 and row.get('failure')is None and err==b'','ORIGINAL_REPAIR_POSITIVE_COMMAND');return row,out,'POSITIVE'

def validate_precheck(device,pre,manifest,prior_table):
 r=device.root;refs=pre['commandRefs'];prep=json.loads(read_ref(r,pre['preparationRef']));need(prep in read_receipts(r,'diagnostic')and prep.get('actualUID0')is True and prep.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','ORIGINAL_ROOT_PREPARATION');_,boot1,_=original_command(r,prep['bootBeforeRef'],['cat','/proc/sys/kernel/random/boot_id']);_,boot2,_=original_command(r,prep['bootAfterRef'],['cat','/proc/sys/kernel/random/boot_id']);need(boot1==boot2 and boot1.decode().strip()==prep['kernelBootUUID'],'ROOT_PREPARATION_SAME_BOOT');_,out,_=original_command(r,refs['user'],['am','get-current-user']);need(out==b'0\n','CURRENT_USER0');_,out,_=original_command(r,refs['cold'],['sh','-c',COLD]);need(out==b'ABSENT\n','COLD_NO_ACTIVITY');_,out,_=original_command(r,refs['uid'],['id','-u']);need(out==b'0\n','ACTUAL_UID0');_,out,_=original_command(r,refs['dump'],['dumpsys','package',PACKAGE]);code=package_state(out,broken=True);need(code==pre['currentCodePath'],'CURRENT_PATH_FROM_RAW_DUMP');base=safe_code_path(code)
 _,stat,_=original_command(r,refs['private'],['sh','-c',STAT]);need(stat.startswith(b'directory 10141 10141 '),'RETAINED_PRIVATE_UID');row,out,kind=original_command(r,refs['codeStat'],['stat','-c','%F %u %g %s',base],missing_path=base)
 if kind=='POSITIVE':
  need(out.startswith(b'regular file '),'CURRENT_CODE_REGULAR');_,out,_=original_command(r,refs['codeSHA'],['sha256sum',base]);need(out.decode().split()==[manifest['native']['APK_SHA256'],base],'CURRENT_CODE_ONLY_SELECTED_BYTES')
 backup=pre['backup'];p=Path(backup['path']);need(p==r.parent/'native-original-before-quarantine.tar'and file_sha(p)==backup['sha256'],'ORIGINAL_PRECHECK_TAR');cap=json.loads(read_ref(r,backup['captureReceiptRef']));need(cap in read_receipts(r,'diagnostic')and cap.get('captureComplete')is True and cap.get('failure')is None and cap.get('exit')==0 and cap.get('bytesRetained')==p.stat().st_size and cap.get('path')==str(p)and cap.get('fullOriginalFiles')is True and read_ref(r,cap['stderrRef'])==b'','ORIGINAL_FULL_PRIVATE_CAPTURE');argv=json.loads(read_ref(r,cap['argvRef']));need(argv==[device.adb if hasattr(device,'adb')else argv[0],'-s','emulator-5582','exec-out','tar','-C',PRIVATE,'-cf','-','files'],'ORIGINAL_ROOT_TAR_ARGV');after_row,after,_=original_command(r,refs['coldAfter'],['sh','-c',COLD]);need(after==b'ABSENT\n'and cap['finishedHostNs']<=after_row['startedHostNs'],'POST_BACKUP_COLD_AND_ORDER');need(private_table(p)==prior_table,'PRE_PRIVATE70_TABLE_CONSERVATION');return kind

def verify_authorization(root,ref):
 from aeris_runtime.paths import repository
 root=Path(root);a=json.loads(read_ref(root,ref),object_pairs_hook=unique);need(sum(v==a for v in read_receipts(root,'diagnostic'))==1 and a.get('format')=='aeris-h4-persistent-push-install-authorization'and a.get('version')==1 and a.get('serial')=='emulator-5582'and a.get('certificateSHA256')==CERT and a.get('noClearUninstallWipe')is True,'DISTINCT_DURABLE_REPAIR_AUTHORIZATION');candidate=Path(a['candidateDir']);manifest=load(candidate,a['candidateSHA256']);apk=selected_apk(candidate,a['candidateSHA256'],manifest);need(a['APKPath']==str(apk)and a['APKSHA256']==manifest['native']['APK_SHA256']and a['nativeSourceSHA256']==manifest['native']['sourceSHA256'],'AUTHORIZED_SELECTED_APK_SOURCE');prepath=root.parents[2]/'reports/repair-precheck01.json';raw=prepath.read_bytes();need(len(raw)<=32768 and not any(p.is_symlink()for p in[prepath,*prepath.parents])and hashlib.sha256(raw).hexdigest()==a['precheckSHA256'],'AUTHORIZATION_ORIGINAL_PRECHECK');pre=json.loads(raw,object_pairs_hook=unique);need(a.get('RootIntentSHA256')==pre.get('RootIntentSHA256')and re.fullmatch('[a-f0-9]{64}',str(a.get('RootIntentSHA256')))is not None,'EXACT_ROOT_INTENT_BINDING');validate_precheck(type('ColdDeviceReference',(),{'root':root})(),pre,manifest,original_private_table(repository()));return a

def authorize_repair(owner,device,pre):
 selected_apk(owner.candidate,owner.digest,owner.manifest);validate_precheck(device,pre,owner.manifest,original_private_table(owner.repo));path=owner.root/'reports/repair-precheck01.json';need(not path.exists(),'ONE_PRECHECK_NO_OVERWRITE');owner.write('repair-precheck01.json',pre);a={'format':'aeris-h4-persistent-push-install-authorization','version':1,'serial':'emulator-5582','candidateDir':str(owner.candidate),'candidateSHA256':owner.digest,'APKPath':str(owner.candidate/'native.apk'),'APKSHA256':owner.manifest['native']['APK_SHA256'],'nativeSourceSHA256':owner.manifest['native']['sourceSHA256'],'certificateSHA256':CERT,'precheckSHA256':file_sha(path),'RootIntentSHA256':pre['RootIntentSHA256'],'preparedHostNs':device.now(),'noClearUninstallWipe':True,'authorityRestorable':False};ref=device.store.receipt('known-state-repair-authorization.json',a);verify_authorization(device.root,ref);return ref

def verify_dispatch(root,auth_ref,auth):
 path=Path(root).parents[2]/'reports/repair-dispatch-intent01.json';need(path.is_file()and path.stat().st_size<=8192 and not any(p.is_symlink()for p in[path,*path.parents]),'DURABLE_DISPATCH_INTENT');v=json.loads(path.read_bytes(),object_pairs_hook=unique);need(v.get('authorizationRef')==auth_ref and v.get('candidateSHA256')==auth['candidateSHA256']and v.get('APKPath')==auth['APKPath']and v.get('RootIntentSHA256')==auth['RootIntentSHA256']and type(v.get('attempt'))is int and v['attempt']==1 and v.get('consumedBeforeSend')is True and v.get('automaticRetry')is False and type(v.get('preparedHostNs'))is int and auth['preparedHostNs']<=v['preparedHostNs'],'EXACT_DURABLE_CONSUMED_DISPATCH');return v

def original_private_table(repo):
 # N02 is the primary original byte source. M101 is retained corroborative
 # historical evidence, no longer read by this H4 runtime or counted as input.
 p=Path(repo)/'evidence/nativejournal17/n02/sessions/nativejournal17-only02/native-restart-metadata.tar';need(file_sha(p)==N02_TAR_SHA,'PRIMARY_N02_ORIGINAL_TAR_SHA');return private_table(p)
