"""LINUXPORT01 continuation admission for the team m803 state (team code, not the owner's).

continuation_l16.py (runtime-l16) for a new chain (m907/m908 qualification, G1 g109) from the
same pinned 89-file state, after g108 attempt 1 failed and the AVD was restored to the backup
taken right after m906 (the user's decision, path A, report 4zzs), with the team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m906 boot of runtime-l16) change. Replaces, for these
slots only, the three places where the owner's chain admits the private data with
reconcile_h7.reconcile (the post-g103 75-file decoder): the SDK boot check (owner: verify_sdk for
m701/m702), the G1 start (owner: resume_existing) and the cold domain check (owner:
verify_resume_domain). Each keeps the owner's original command, order, capture and closure
checks; only the data admission is the team contract planning/linuxport01/contract-l16 (pin
15039006..., unchanged), loaded from the frozen source graph. As in continuation_l13,
case['backup17'] is the owner's n02 pre-migration original. Nothing here grants archive,
resume, APPLY or flight authority, closes the open journal, or imports reconcile_h7.
runtime-l14 (team decision, kept): require_qualification bounds each boot's Private reference
(its private-files TAR) at 64 MiB instead of 256 KiB, only at that boot's capture path and
only with the pinned m803 TAR SHA-256 and size; every other reference keeps the owner's bound.
"""
from pathlib import Path
import hashlib,importlib.util,json,re
from .paths import repository
from .metadata_budget import encoded
from .native17 import decode,workspace17,table,PACKAGE
from .once_reader import read_ref,read_receipts
from .status15_reader import command
from .installclosure_h4 import original_command,safe_code_path,package_state,STAT,COLD,PRIVATE
from .tar_profile_h7 import native_tar

CONTRACT='planning/linuxport01/contract-l16/continuation_l16.py'
PIN='planning/linuxport01/contract-l16/m803-continuation-pin.json'
PIN_SHA='15039006e060302d18acf0f45ce5304bdfb78d6fa1c4b8883f4016ee2f57ac95'
M906='evidence/betarc01/m906';M906_RUN='beta-rc01-sdk-continuation06';L16_CANDIDATE='b07badbf8e31d19d62bba7133ffd9cb34634660eb963f556d132d4a87784840d'
SLOTS=('m907','m908');QUALIFICATION='aeris-linuxport01-l17-root-contract-sdk-cold-acceptance'
RUNS={'m907':'beta-rc01-sdk-continuation07','m908':'beta-rc01-sdk-continuation08'};PRIVATE_MAXIMUM=64*2**20
BOOT=['cat','/proc/sys/kernel/random/boot_id']
_loaded={}

def need(v,n):
 if not v:raise ValueError('L17_'+n)
def sha(b):return hashlib.sha256(b).hexdigest()

def contract(manifest):
 """The contract module and pin, exactly as pinned in this candidate's product-input graph."""
 repo=repository();pins=manifest['productInputClosure']['pins']
 for rel in(CONTRACT,PIN):need(pins.get(rel)==sha((repo/rel).read_bytes()),'CONTRACT_SOURCE_PIN:'+rel)
 need(sha((repo/PIN).read_bytes())==PIN_SHA,'CONTRACT_PIN_SHA');digest=pins[CONTRACT]
 if digest not in _loaded:
  spec=importlib.util.spec_from_file_location('linuxport01_continuation_l16',repo/CONTRACT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);_loaded[digest]=m
 return _loaded[digest]

def contract_check(path,digest,manifest):
 """Admit one raw private-files TAR as the pinned m803 continuation state, or raise."""
 repo=repository();proof=contract(manifest).verify(path,digest,repo/PIN,PIN_SHA,repo=repo);ind=proof['independentReceiver']
 need(proof.get('status')=='TEAM_CONTINUATION_STATE_MATCHES_PIN_NOT_AUTHORITY_NOT_G1'and proof.get('pinSHA256')==PIN_SHA and proof.get('tarSHA256')==digest and ind['pendingTransactions']==0,'CONTRACT_PROOF')
 scan=native_tar(path,digest,allow_empty_active=True)
 return {'format':'aeris-linuxport01-l17-continuation-admission','version':1,'status':'CURRENT_COLD_STATE_MATCHES_TEAM_CONTINUATION_PIN_NOT_G1','TARSHA256':digest,'pinSHA256':PIN_SHA,'registryHead':proof['registryHead'],'counters':proof['counters'],'activeJournals':ind['activeJournals'],'archivedJournals':ind['archivedJournals'],'pendingTransactions':ind['pendingTransactions'],'contractProof':proof,'tarTransportProfile':scan['transportProfile'],'decoder75FileUsed':False,'authorityRestorable':False,'flightAcceptance':False}

def rich_table(path):
 """Same table as reconcile_h7.rich_table (mode, UID, GID, size, SHA per entry), without importing reconcile_h7."""
 import tarfile
 table(path);files={};dirs={}
 with tarfile.open(path,'r:')as t:
  for m in t:
   n=m.name.rstrip('/');v={'mode':m.mode,'uid':m.uid,'gid':m.gid}
   if m.isdir():dirs[n]=v
   else:files[n]={**v,'bytes':m.size,'sha256':sha(t.extractfile(m).read())}
 return {'files':files,'directories':dirs}

def m906_prior():
 """Prior boot UUID and codePath for m907, read back with the harness readers from the team m906 qualification boot of
 runtime-l16 (candidate b07badbf...): the last boot of the pinned state, to which the AVD was restored (report 4zzs).
 Its own raw records must show a normal SDK closure, its own TAR must be the pinned m803 state TAR, and both samples
 must show the same boot (as the owner's verify_sdk requires of a qualification boot)."""
 repo=repository();root=repo/M906;j=lambda rel:decode((root/rel).read_bytes())
 report=j('reports/coldboot-h7.json');term=j('reports/owner-terminal.json');closure=j('guardian/closure.json');process=j('diagnostics/guardian-process/close.json');pin=decode((repo/PIN).read_bytes())
 need(report.get('format')=='aeris-h7-sdk-positive-observation'and report.get('status')=='SDK_ONLY_ORIGINALS_OBSERVED_AWAITING_NORMAL_CLOSE'and report.get('candidateSHA256')==L16_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L16_CANDIDATE,'M906_QUALIFICATION_SCOPE')
 need(type(closure.get('exit'))is int and closure['exit']==0 and closure.get('failure')is None and closure.get('exceptionalPhysicalDisposal')is False and closure.get('cleanupNotes')==[]and closure.get('durablyDrained')is True and all(v.get('captureComplete')is True and v.get('failure')is None for v in closure['outputCapture'].values())and type(process.get('exit'))is int and process['exit']==0,'M906_ORIGINAL_NORMAL_SDK_CLOSURE')
 backup=report['rootPrivateBackup'];tar=root/'sessions'/M906_RUN/'native-restart-metadata.tar'
 need(backup['sha256']==pin['source']['sha256']and backup['bytes']==pin['source']['bytes']and sha(tar.read_bytes())==pin['source']['sha256'],'M906_IS_PINNED_STATE')
 store=root/'sessions'/M906_RUN/'android-api';boots=[]
 for s in report['samples']:
  _,out,_=original_command(store,s['commandRefs']['boot'],BOOT);boots.append(out.decode().strip())
 _,out,_=original_command(store,report['samples'][-1]['commandRefs']['dump'],['dumpsys','package',PACKAGE]);path=package_state(out,broken=False);boot=boots[-1]
 need(len(boots)==2 and boots[0]==boot and path==report['baseAPK']and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot)is not None and boot!=report['priorKernelBootUUID'],'M906_ORIGINAL_CODEPATH_BOOT');return boot,path

def require_qualification(path,digest,candidate):
 """reconcile_h7.require_qualification with the team m907/m908 proof format instead of the owner's m701/m702.
 Each Private reference is that boot's own TAR of the pinned m803 state, bounded at 64 MiB (runtime-l14, kept)."""
 from .rc01 import ref_file
 p=Path(path).absolute();need(p.is_relative_to(repository()/'evidence/betarc01')and p.is_file()and p.stat().st_size<=32768 and not any(q.is_symlink()for q in[p,*p.parents]),'QUALIFICATION_PROOF_SCOPE');raw=p.read_bytes();need(sha(raw)==digest,'QUALIFICATION_PROOF_SHA');v=json.loads(raw)
 need(v.get('format')==QUALIFICATION and v.get('version')==1 and v.get('status')=='ROOT_COLD_VERIFIED_CONTRACT_TWO_NORMAL_SDK_BOOTS_NOT_FLIGHT'and v.get('candidateSHA256')==candidate and v.get('slots')==list(SLOTS)and v.get('contractPinSHA256')==PIN_SHA and v.get('authorityRestorable')is False and v.get('SDKExitZeroNoForcedKillBoth')is True,'TWO_SAME_CANDIDATE_CONTRACT_BOOT_PROOF')
 boots=v.get('actualKernelBootUUIDs');need(type(boots)is list and len(boots)==2 and all(type(b)is str and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',b)for b in boots)and boots[0]!=boots[1],'DISTINCT_ACTUAL_BOOTS')
 refs=v.get('originalEvidence');roles={s+k for s in SLOTS for k in('Observation','Guardian','SDKProcess','Private')};need(type(refs)is list and len(refs)==8 and{r.get('role')for r in refs}==roles,'EXACT_ORIGINAL_ROLES')
 # runtime-l14 (kept): the m803 state TAR (268,800 B) is above the owner's 256 KiB ref_file bound. Only the Private refs get
 # the 64 MiB bound of the root TAR capture, and only as each boot's own capture with the pinned TAR SHA-256 and size.
 pin=(repository()/PIN).read_bytes();need(sha(pin)==PIN_SHA,'CONTRACT_PIN_SHA');state=decode(pin)['source']
 for row in refs:
  ref=row['ref']
  if row['role'].endswith('Private'):
   slot=row['role'][:-len('Private')];need(type(ref)is dict and Path(str(ref.get('path'))).absolute()==repository()/'evidence/betarc01'/slot/'sessions'/RUNS[slot]/'native-restart-metadata.tar'and ref.get('sha256')==state['sha256']and ref.get('bytes')==state['bytes'],'PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE');ref_file(ref,maximum=PRIVATE_MAXIMUM)
  else:ref_file(ref)
 return {'status':'SOURCE_BOUND_L17_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE','authorityRestorable':False}

def verify_sdk(owner,proof):
 """reconcile_h7.verify_sdk for m907/m908: same original command checks, data admitted by the contract."""
 c=owner.case;r=c['device'].root;v=proof.get('sdkOnlyH7');need(type(v)is dict and owner.root.name in SLOTS and v.get('candidateSHA256')==owner.digest,'SDK_ONLY_EXACT_CURRENT_SOURCE')
 prep=json.loads(read_ref(r,v['preparationRef']));need(prep in read_receipts(r,'diagnostic')and prep.get('actualUID0')is True and prep.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','SDK_ONLY_ORIGINAL_ROOT_PREPARATION');path=safe_code_path(v['baseAPK']);samples=v['samples'];need(type(samples)is list and len(samples)==2 and[s['offsetSeconds']for s in samples]==[0,30],'SDK_ONLY_FIXED_SAMPLES');boots=[];need(samples[1]['targetHostNs']-samples[0]['targetHostNs']==30_000_000_000,'SDK_ONLY_ORIGINAL_FIXED_TARGETS')
 for s in samples:
  refs=s['commandRefs'];need(original_command(r,refs['boot'],BOOT)[0]['startedHostNs']>=s['targetHostNs'],'SDK_ONLY_SAMPLE_NOT_BEFORE_TARGET')
  def cmd(k,args):return original_command(r,refs[k],args)[1]
  boot=cmd('boot',BOOT).decode().strip();need(re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot)is not None,'SDK_ONLY_ACTUAL_BOOT');boots.append(boot)
  need(cmd('user',['am','get-current-user'])==b'0\n'and cmd('cold',['sh','-c',COLD])==b'ABSENT\n','SDK_ONLY_USER_AND_COLD');need(cmd('path',['pm','path',PACKAGE]).decode().strip()=='package:'+path,'SDK_ONLY_PM_PATH');need(cmd('sha',['sha256sum',path]).decode().split()==[owner.manifest['native']['APK_SHA256'],path],'SDK_ONLY_SELECTED_SHA');need(package_state(cmd('dump',['dumpsys','package',PACKAGE]),broken=False)==v['baseAPK'],'SDK_ONLY_PARSED_PM_UID')
 need(prep['kernelBootUUID']==boots[0]and boots[0]==boots[1]and boots[0]!=v['priorKernelBootUUID'],'SDK_ONLY_FRESH_STABLE_BOOT')
 need(original_command(r,v['finalUIDRef'],['id','-u'])[1]==b'0\n'and original_command(r,v['finalStatRef'],['sh','-c',STAT])[1].startswith(b'directory 10141 10141 ')and original_command(r,v['finalColdRef'],['sh','-c',COLD])[1]==b'ABSENT\n','SDK_ONLY_ACTUAL_ROOT_PRIVATE_COLD')
 backup=v['rootPrivateBackup'];p=Path(backup['path']);need(p==r.parent/'native-restart-metadata.tar'and p.is_file()and not p.is_symlink()and sha(p.read_bytes())==backup['sha256'],'SDK_ONLY_EXACT_CURRENT_BACKUP');cap=json.loads(read_ref(r,backup['captureReceiptRef']));need(cap in read_receipts(r,'diagnostic')and cap.get('captureComplete')is True and cap.get('failure')is None and type(cap.get('exit'))is int and cap['exit']==0 and cap.get('bytesRetained')==p.stat().st_size and cap.get('path')==str(p)and cap.get('fullOriginalFiles')is True and read_ref(r,cap['stderrRef'])==b'','SDK_ONLY_ORIGINAL_TAR_CAPTURE');argv=json.loads(read_ref(r,cap['argvRef']));need(argv==[c['device'].adb,'-s','emulator-5582','exec-out','tar','-C',PRIVATE,'-cf','-','files'],'SDK_ONLY_FIXED_ROOT_TAR');row,cold,_=original_command(r,v['afterBackupColdRef'],['sh','-c',COLD]);need(cold==b'ABSENT\n'and row['startedHostNs']>=cap['finishedHostNs'],'SDK_ONLY_COLD_AFTER_TAR')
 semantic=contract_check(p,backup['sha256'],owner.manifest);observed=v.get('tarProfileObservation');need(type(observed)is dict and observed.get('observation')==semantic['tarTransportProfile']and observed.get('originalCaptureRef')==backup['captureReceiptRef'],'EXPLICIT_PROFILE_OBSERVATION_AND_ORIGINAL_CAPTURE')
 if owner.root.name=='m908':
  prior=decode((owner.repo/'evidence/betarc01/m907/reports/coldboot-h7.json').read_bytes());need(rich_table(p)==rich_table(prior['rootPrivateBackup']['path']),'SECOND_BOOT_WHOLE_PRIVATE_UNCHANGED')
 return {'originalPrivateBytesConserved':True,'pendingTransactions':semantic['pendingTransactions'],'continuation':semantic,'actualKernelBootUUID':boots[0],'flightAcceptance':False}

def receiver_originals(backup_path,backup_sha):
 """The g103 archive receiver report and plan the 8 archived journals are bound to (the contract's pinned receiver).
 Read as bytes only; the plan must equal the archive intent record inside the current TAR."""
 repo=repository();pin=decode((repo/PIN).read_bytes());ref=pin['receiver'];report=(repo/ref['path']).read_bytes();need(len(report)==ref['bytes']and sha(report)==ref['sha256'],'PINNED_ARCHIVE_RECEIVER')
 plan=(repo/ref['path']).with_name('native17-plan-original.txt').read_bytes();value=decode(report);moved={x['generation']for x in value['originals']}
 need(value.get('status')=='COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT'and value.get('package')==PACKAGE and len(moved)==8,'ARCHIVE_RECEIVER_SCOPE')
 inputs=native_tar(backup_path,backup_sha,allow_empty_active=True)['inputOriginals'];need(inputs.get('files/product-input-archives17/'+sha(plan)+'/intent-0.record')==plan,'ARCHIVE_PLAN_IS_CURRENT_INTENT_RECORD')
 return {'raw':report,'value':value,'plan':plan,'reportSHA256':sha(report),'planSHA256':sha(plan)}

def continuation_observation(store,proof,manifest):
 """reconcile_h7.resume_observation with the contract as the data admission."""
 need(proof.get('format')=='aeris-linuxport01-l17-continuation-readonly-resume'and proof.get('candidateSHA256')==sha(encoded(manifest).rstrip(b'\n'))and proof.get('APKSHA256')==manifest['native']['APK_SHA256']and proof.get('nativeSourceSHA256')==manifest['native']['sourceSHA256']and proof.get('contractPinSHA256')==PIN_SHA and proof.get('installOrAdminDispatched')is False and proof.get('authorityRestorable')is False,'RESUME_IDENTITY')
 before=command(store,proof['coldBeforeRef']);p=command(store,proof['installedPathRef']);h=command(store,proof['installedSHARef']);after=command(store,proof['coldAfterRef']);need(before[2]==after[2]==['sh','-c',COLD]and before[3]==after[3]==b'ABSENT\n'and p[2]==['pm','path',PACKAGE]and p[3].startswith(b'package:/')and h[2]==['sha256sum',p[3].decode().strip()[8:]]and h[3].decode().split()[0]==manifest['native']['APK_SHA256'],'CURRENT_COLD_SELECTED_APK');backup=proof['backup'];cap=decode(read_ref(store,backup['captureReceiptRef']));need(cap in read_receipts(store,'diagnostic')and cap.get('captureComplete')is True and cap.get('failure')is None and cap.get('exit')==0 and cap.get('fullOriginalFiles')is True and cap.get('path')==backup['path']and cap.get('bytesRetained')==backup['bytes']and read_ref(store,cap['stderrRef'])==b''and decode(read_ref(store,cap['argvRef']))[1:]==['-s','emulator-5582','exec-out','run-as',PACKAGE,'tar','-cf','-','files'],'ORIGINAL_CURRENT_TAR_CAPTURE');need(Path(backup['path'])==Path(store).parent/'native-restart-metadata.tar'and before[0]['endedHostNs']<=p[0]['startedHostNs']<=p[0]['endedHostNs']<=h[0]['startedHostNs']<=h[0]['endedHostNs']<=cap['startedHostNs']<=cap['finishedHostNs']<=after[0]['startedHostNs'],'RESUME_CAPTURE_SOURCE_ORDER')
 return contract_check(backup['path'],backup['sha256'],manifest)

def resume_continuation(owner,case,*,deadline_ns):
 """reconcile_h7.resume_existing for g109: same cold reads and full TAR, admitted by the contract instead of the 75-file decoder."""
 from .rc01 import generation_forecast
 from .adoption17 import retained_originals17
 d=case['device'];need(not getattr(d,'resumeL17Attempted',False)and not getattr(d,'migration17_verified',False),'RESUME_ONCE');d.resumeL17Attempted=True;before=d._cold_absence(deadline_ns);p,h=d._installed_sha(owner.manifest['native']['APK_SHA256'],deadline_ns)
 with d.budget.operation({'commands':16385+16384,'command_receipts':4096+8192}):backup=d._export_private(case['context']['run'],case['root']/'native-restart-metadata.tar',deadline_ns=deadline_ns,metadata_only=True,maximum_bytes=64*2**20,product_full_closed=True)
 after=d._cold_absence(deadline_ns);proof={'format':'aeris-linuxport01-l17-continuation-readonly-resume','version':1,'candidateSHA256':owner.digest,'APKSHA256':owner.manifest['native']['APK_SHA256'],'nativeSourceSHA256':owner.manifest['native']['sourceSHA256'],'contractPinSHA256':PIN_SHA,'coldBeforeRef':before,'installedPathRef':p,'installedSHARef':h,'coldAfterRef':after,'backup':backup,'installOrAdminDispatched':False,'authorityRestorable':False}
 semantic=continuation_observation(d.root,proof,owner.manifest);forecast=generation_forecast(semantic['activeJournals'],owner.root.name,remaining_generations=0);receiver=receiver_originals(backup['path'],backup['sha256'])
 # The fix of continuation_l11 (g106 attempt 1): native17.archive_check keeps every file of backup17 byte-identical
 # after each stage, so, as in the owner's resume_existing, it is the n02 pre-migration original, not this capture
 # (whose append-only registry grows in every native session). The original's receiver must be the pinned one.
 retained=retained_originals17();need(retained['receiver']['reportSHA256']==receiver['reportSHA256']and retained['receiver']['planSHA256']==receiver['planSHA256'],'RETAINED_ORIGINALS_ARE_PINNED_RECEIVER')
 auth=d.store.receipt('native17-continuation-l17.json',proof);owner.write('native17-continuation-l17.json',{'original':proof,'continuation':semantic,'generationForecast':forecast})
 case['resumeL17']=proof;case['backup17']=retained['backup'];case['coldProof17']=retained['coldProof'];case['receiver17']=receiver;case['workspaceBefore17']=workspace17(retained['backup']['path']);case['admin17']={'registryHead':semantic['registryHead'],'continuationFromTeamPin':PIN_SHA,'reconciledFromOriginalG103':False,'originalReceiptTARSHA256':backup['sha256']}
 owner.budget.write('external_task',owner.root/'reports/native17-receiver-original.json',receiver['raw']);owner.budget.write('external_task',owner.root/'reports/native17-plan-original.txt',receiver['plan'])
 private=d.command(['shell','run-as',PACKAGE,'pwd','-P'],deadline_ns=deadline_ns,maximum_bytes=256);need(private==('/data/user/0/'+PACKAGE+'\n').encode(),'SAME_PRIVATE_DOMAIN')
 domain={'format':'aeris-root-observed-development-application-domain','version':1,'nativeLifecycleContinuationL17':True,'applicationId':PACKAGE,'privateFilesDirectory':'/data/user/0/'+PACKAGE+'/files','serial':d.serial,'sourceSHA256':owner.manifest['native']['sourceSHA256'],'APKSHA256':owner.manifest['native']['APK_SHA256'],'candidateSHA256':owner.digest,'authorizationRef':auth,'installedPathRef':p,'installedSHARef':h,'actualPrivateDirectoryCommandRef':d.last_command_ref,'nativeReportedApplicationId':False,'retainedInventoryRef':case['native'].retained_inventory_ref,'oldApplicationOriginalsRetained':True,'noAuthorityRestore':True}
 case['native'].application_domain=domain;case['native'].application_domain_ref=d.store.receipt('application-domain17-continuation-l17.json',domain);return backup

def verify_continuation_domain(root,ref,manifest):
 """reconcile_h7.verify_resume_domain for the continuation domain; re-runs the contract on the original TAR."""
 domain=decode(read_ref(root,ref));need(domain in read_receipts(root,'diagnostic')and domain.get('nativeLifecycleContinuationL17')is True and domain.get('applicationId')==PACKAGE and domain.get('serial')=='emulator-5582'and domain.get('privateFilesDirectory')=='/data/user/0/'+PACKAGE+'/files'and domain.get('sourceSHA256')==manifest['native']['sourceSHA256']and domain.get('APKSHA256')==manifest['native']['APK_SHA256']and domain.get('candidateSHA256')==sha(encoded(manifest).rstrip(b'\n')),'ORIGINAL_CONTINUATION_DOMAIN');proof=decode(read_ref(root,domain['authorizationRef']));need(proof in read_receipts(root,'diagnostic'),'ORIGINAL_CONTINUATION_AUTHORIZATION');continuation_observation(root,proof,manifest);retained=decode(read_ref(root,domain['retainedInventoryRef']));need(retained in read_receipts(root,'diagnostic')and retained.get('format')=='aeris-retained-old-application-private-inventory'and retained.get('package')=='vn.rtr.aeris.mission'and retained.get('sourceStopped')is True and retained.get('notNewDeviceGrowthCredit')is True and domain.get('oldApplicationOriginalsRetained')is True and domain.get('noAuthorityRestore')is True and domain.get('nativeReportedApplicationId')is False,'ORIGINAL_RETAINED_INVENTORY');legacy=Path(root).parent/'android-api-retained';_,_,duargs,du=command(legacy,retained['sourceDUCommandRef']);match=re.fullmatch(rb'([0-9]+)[\t ]+files\n',du);need(duargs==['run-as','vn.rtr.aeris.mission','du','-k','-s','files']and match is not None and int(match[1])*1024==retained['allocatedBytes'],'ORIGINAL_RETAINED_DU');backup=retained['sourceOriginalTAR'];need(Path(backup['path'])==Path(root).parent/'native-original-before-quarantine.tar'and sha(Path(backup['path']).read_bytes())==backup['sha256'],'RETAINED_FULL_ORIGINAL_TAR');oldtable=rich_table(backup['path']);need(sum(v['bytes']for v in oldtable['files'].values())==retained['plaintextFileLengthBytes']and len(oldtable['files'])+len(oldtable['directories'])==retained['entries'],'ORIGINAL_RETAINED_FILE_COUNTS');_,_,remote,out=command(root,domain['actualPrivateDirectoryCommandRef']);need(remote==['run-as',PACKAGE,'pwd','-P']and out==('/data/user/0/'+PACKAGE+'\n').encode(),'CURRENT_PRIVATE_DIRECTORY');return domain
