#!/usr/bin/env python3
"""Source-held H4 same-APK push install plus guest barrier, never boot acceptance."""
from pathlib import Path
import argparse,hashlib,json,os,signal,sys,time,traceback
P=Path(__file__).resolve();R=P.parents[3]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--candidate-sha',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--intent',required=True);ap.add_argument('--intent-sha',required=True);ap.add_argument('--inspect',action='store_true');args=ap.parse_args();candidate=Path(args.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=args.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
 from aeris_runtime.candidate import load,sha
 from aeris_runtime.entry import module_origin_receipt
 from aeris_runtime.product_inputs import validate
 from aeris_runtime.product_runtime import WorkbenchRuntime
 from aeris_runtime.preview10 import preview
 from aeris_runtime.once_reader import read_ref
 from aeris_runtime.installclosure_h4 import selected_apk,package_state,original_command,private_table,original_private_table,authorize_repair,safe_code_path,PACKAGE,PRIVATE,STAT,COLD,need
 from aeris_runtime.installclosure_h4 import PushInstallDeviceH4,verify_push_install
 from aeris_runtime.guest_sync_h4 import device_sync
 ip=Path(args.intent).resolve();need(ip.is_relative_to(R/'evidence/betarc01')and ip.is_file()and not any(p.is_symlink()for p in[ip,*ip.parents])and ip.stat().st_size<=8192,'ROOT_INTENT_SCOPE');raw=ip.read_bytes();need(hashlib.sha256(raw).hexdigest()==args.intent_sha,'ROOT_INTENT_SHA');intent=json.loads(raw);spec=Path(args.spec).resolve();files=[P,candidate/'source/aeris_runtime/installclosure_h4.py',R/'planning/betarc01/diagnostics/package_device01.py'];pins={str(p.relative_to(R)):sha(p)for p in files};m101=R/'evidence/betarc01/m201/reports/known-state-repair01.json';need(intent.get('format')=='aeris-betarc01-root-known-state-repair-intent'and intent.get('version')==1 and intent.get('status')=='ROOT_SOURCE_QUALIFIED_PERSISTENT_PUSH_INSTALL_NOT_BETA'and intent.get('slot')=='m301'and intent.get('run')=='beta-rc01-persistent-install01'and intent.get('candidateSHA256')==args.candidate_sha and intent.get('specSHA256')==sha(spec)and intent.get('filesSHA256')==pins and intent.get('m201ReportSHA256')==sha(m101)and intent.get('noClearUninstallWipe')is True and intent.get('noActivityNoAP')is True,'EXACT_ROOT_REPAIR_INTENT')
 manifest=load(candidate,args.candidate_sha);module_origin_receipt(candidate);validate(manifest['productInputClosure']);apk=selected_apk(candidate,args.candidate_sha,manifest);prior=json.loads(m101.read_bytes());oldstore=R/'evidence/betarc01/m201/sessions/beta-rc01-known-state-repair01/android-api';_,_,oldremote,oldraw=__import__('aeris_runtime.status15_reader',fromlist=['command']).command(oldstore,prior['postDumpRef']);need(oldremote==['dumpsys','package',PACKAGE],'M201_ORIGINAL_POSTDUMP');known_path=package_state(oldraw,broken=False);prior_table=original_private_table(R);evidence=R/'evidence/betarc01/m301';need(not evidence.exists(),'FRESH_M201_NO_RETRY');forecast=preview(candidate,args.candidate_sha,evidence,R/'planning/betarc01',spec,seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'PURE_REPAIR_ADMISSION')
 if args.inspect:print(json.dumps({'status':'KNOWN_STATE_REPAIR_PREVIEW_ONLY','forecast':forecast}));return
 owner=WorkbenchRuntime(candidate,args.candidate_sha,evidence=evidence,planning=R/'planning/betarc01',spec=spec,seconds=180);owner.root.mkdir(exist_ok=False);stopped=False;device=None
 def stop(sig,frame):
  nonlocal stopped
  stopped=True
 def check():need(not stopped,'TERMINATION');owner.check()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 class RepairComplete(Exception):pass
 def read(cmd,*,allow_missing=False):
  previous=device.sequence
  try:device.command(cmd,deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=device._command_bound(cmd))
  except RuntimeError:
   need(allow_missing and device.sequence==previous+1,'NO_UNQUALIFIED_FAILURE_CONTINUATION')
  ref=device.last_command_ref;row,out,kind=original_command(device.root,ref,cmd[1:],missing_path=device.current_base if allow_missing else None);return ref,out,kind
 try:
  owner.bootstrap();case=owner.create_case(intent['run'],seconds=180);owner.start_writer()
  need(case['device'].sequence==0 and not(case['device'].root/'command-stream.raw').exists(),'EMPTY_COMMAND_DOMAIN');device=PushInstallDeviceH4(case['device'].adb,'emulator-5582',case['device'].root,budget=owner.budget,observer_tag='AERIS_PRODUCT_STATUS');device.live_check=check;device.bind_current_path(known_path)
  device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000);refs={}
  for key,cmd in [('uid',['shell','id','-u']),('user',['shell','am','get-current-user']),('cold',['shell','sh','-c',COLD]),('dump',['shell','dumpsys','package',PACKAGE]),('private',['shell','sh','-c',STAT])]:refs[key],_,_=read(cmd)
  refs['codeStat'],_,kind=read(['shell','stat','-c','%F %u %g %s',device.current_base],allow_missing=True)
  if kind=='POSITIVE':refs['codeSHA'],_,_=read(['shell','sha256sum',device.current_base])
  # All initial positive predicates are checked before even the cold root export.
  for key,expected in [('uid',b'0\n'),('user',b'0\n'),('cold',b'ABSENT\n')]:need(read_ref(device.root,json.loads(read_ref(device.root,refs[key]))['stdoutRef'])==expected,'PRE_ROOT_USER_COLD')
  _,dumpraw,_=original_command(device.root,refs['dump'],['dumpsys','package',PACKAGE]);need(package_state(dumpraw,broken=True)==known_path,'CURRENT_DUMP_MATCHES_ACTUAL_PRIOR_PATH');_,priv,_=original_command(device.root,refs['private'],['sh','-c',STAT]);need(priv.startswith(b'directory 10141 10141 '),'CURRENT_PRIVATE_UID');device.diagnostic_root_cold_private=True;before=device.export_stage('before',deadline_ns=time.monotonic_ns()+60_000_000_000);refs['coldAfter'],aftercold,_=read(['shell','sh','-c',COLD]);need(aftercold==b'ABSENT\n','AFTER_BACKUP_STILL_COLD')
  pre={'format':'aeris-known-state-repair-precheck','version':1,'candidateSHA256':args.candidate_sha,'RootIntentSHA256':args.intent_sha,'currentCodePath':known_path,'commandRefs':refs,'preparationRef':device.content_reader_preparation,'backup':before,'authorityRestorable':False};auth=authorize_repair(owner,device,pre)
  dispatch=owner.root/'reports/repair-dispatch-intent01.json';need(not dispatch.exists(),'ONE_DURABLE_DISPATCH_NO_RETRY');owner.write('repair-dispatch-intent01.json',{'authorizationRef':auth,'candidateSHA256':args.candidate_sha,'attempt':1,'consumedBeforeSend':True,'RootIntentSHA256':args.intent_sha,'APKPath':str(apk),'preparedHostNs':time.monotonic_ns(),'automaticRetry':False});install_ref=device.install_push_once(apk,auth,deadline_ns=time.monotonic_ns()+70_000_000_000)
  cold_ref,cold,_=read(['shell','sh','-c',COLD]);need(cold==b'ABSENT\n','POST_COLD');path_ref,pathraw,_=read(['shell','pm','path',PACKAGE]);loc=pathraw.decode().strip();need(loc.startswith('package:')and'\n'not in loc,'POST_SINGLE_PACKAGE_PATH');postbase=loc[8:];need(postbase.endswith('/base.apk'),'POST_BASE_APK');device.bind_current_path(postbase[:-9]);sha_ref,sharaw,_=read(['shell','sha256sum',postbase]);need(sharaw.decode().split()==[manifest['native']['APK_SHA256'],postbase],'POST_SELECTED_APK_SHA');dump_ref,postdump,_=read(['shell','dumpsys','package',PACKAGE]);need(safe_code_path(package_state(postdump,broken=False))==postbase,'POST_PARSED_SAME_UID_CODEPATH');private_ref,postpriv,_=read(['shell','sh','-c',STAT]);need(postpriv.startswith(b'directory 10141 10141 '),'POST_PRIVATE_SAME_UID');after=device.export_stage('after',deadline_ns=time.monotonic_ns()+60_000_000_000);need(private_table(after['path'])==private_table(before['path'])==prior_table,'POST_FULL70_FILE5_DIRECTORY_CONSERVATION');verify_push_install(device.root,install_ref,auth,str(apk))
  sync_ref=device_sync(device)
  owner.write('persistent-install-h4.json',{'format':'aeris-h4-persistent-push-install','version':1,'status':'PUSH_INSTALL_AND_SYNC_OBSERVED_NOT_BOOT_OR_G1_ACCEPTANCE','candidateSHA256':args.candidate_sha,'RootIntentSHA256':args.intent_sha,'authorizationRef':auth,'installCommandRef':install_ref,'guestSyncCommandRef':sync_ref,'postColdRef':cold_ref,'postPathRef':path_ref,'postSHARef':sha_ref,'postDumpRef':dump_ref,'postPrivateRef':private_ref,'beforeBackup':before,'afterBackup':after,'private70File5DirectoryTableConserved':True,'APKInstalledMayDifferFromPriorUnknown':True,'oldN02InstallOutcome':'UNCONFIRMED_UNCHANGED','ActivityStarted':False,'APStarted':False,'authorityRestored':False,'flightAcceptance':False});raise RepairComplete('PUSH_INSTALL_AND_SYNC_OBSERVED_NOT_BOOT_OR_G1_ACCEPTANCE')
 except BaseException as primary:
  if device is not None:
   try:device.close_observer()
   except BaseException as secondary:primary.add_note('REPAIR_DEVICE_CLOSE:'+str(secondary))
  if owner.budget is not None:
   try:owner.persist_owner_error(traceback.format_exc());owner.fail_case(primary)
   except BaseException as secondary:primary.add_note('REPAIR_FAILED_DRAIN:'+str(secondary))
  try:
   if not owner.closed:owner.close_guardian(failed=True)
  except BaseException as secondary:primary.add_note('REPAIR_GUARDIAN_CLOSE:'+str(secondary))
  print(json.dumps({'status':'PUSH_INSTALL_AND_SYNC_OBSERVED_NOT_BOOT_OR_G1_ACCEPTANCE'if isinstance(primary,RepairComplete)else'FAILED_REPAIR_UNKNOWN_NO_RETRY','error':str(primary),'notes':getattr(primary,'__notes__',[]),'evidence':str(owner.root),'flightAcceptance':False}))
  if not isinstance(primary,RepairComplete):raise
if __name__=='__main__':main()
