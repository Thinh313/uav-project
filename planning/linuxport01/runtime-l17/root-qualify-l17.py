#!/usr/bin/env python3
"""LINUXPORT01 (team entry): fresh coldboot qualification m907/m908 checked by the m803 continuation contract.
Owner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, then runtime-l17/l17_patches.py. No install, Activity, AP or automatic repair."""
from pathlib import Path
import argparse,hashlib,json,os,signal,sys,time,traceback
P=Path(__file__).resolve();R=P.parents[3]
def terminal_summary(owner):
 def ref(name):
  p=owner.root/name;raw=p.read_bytes()
  return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 return {'format':'aeris-h7-sdk-positive-owner-terminal','version':1,'status':'SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE','candidateSHA256':owner.digest,'originalEvidence':[ref(n)for n in('reports/coldboot-h7.json','reports/native-maintenance-case-closure.json','guardian/closure.json','diagnostics/guardian-process/close.json')],'flightAcceptance':False,'APGroundProven':False,'authorityRestorable':False,'normalFlightClosureClaimed':False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--candidate-sha',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--intent',required=True);ap.add_argument('--intent-sha',required=True);ap.add_argument('--install-stage-proof',required=True);ap.add_argument('--install-stage-proof-sha',required=True);ap.add_argument('--slot',choices=('m907','m908'),required=True);ap.add_argument('--inspect',action='store_true');a=ap.parse_args();candidate=Path(a.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=a.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
 from aeris_runtime.candidate import load,sha
 from aeris_runtime.entry import module_origin_receipt
 from aeris_runtime.product_inputs import validate
 from aeris_runtime.product_runtime import WorkbenchRuntime
 from aeris_runtime.preview10 import preview
 from aeris_runtime.once_reader import read_ref
 from aeris_runtime.status15_reader import command
 from aeris_runtime.rc01 import ref_file
 from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,PACKAGE,STAT,COLD,private_export_eligible,need
 from aeris_runtime.installclosure_h4 import private_table,original_private_table,safe_code_path,package_state,original_command
 class ColdBootDeviceH4(ReadOnlyPackageDevice):
  def bind(self,path):self.base=safe_code_path(path)
  def _command_bound(self,args):
   need(self.serial=='emulator-5582'and self.observer.tag=='AERIS_PRODUCT_STATUS','H4_COLD_DEVICE')
   if args in(['shell','pm','path',PACKAGE],['shell','sha256sum',self.base]):return 4096
   if args[:1]==['install']or args==['shell','sync']:raise ValueError('H4_BOOT_NO_INSTALL_SYNC')
   return super()._command_bound(args)
 intentpath=Path(a.intent).resolve();need(intentpath.is_relative_to(R/'evidence/betarc01')and intentpath.is_file()and intentpath.stat().st_size<=8192 and not any(p.is_symlink()for p in[intentpath,*intentpath.parents]),'H4_INTENT_SCOPE');raw=intentpath.read_bytes();need(hashlib.sha256(raw).hexdigest()==a.intent_sha,'H4_INTENT_SHA');intent=json.loads(raw);manifest=load(candidate,a.candidate_sha);module_origin_receipt(candidate);graph=validate(manifest['productInputClosure']);need(graph['pins'].get(str(P.relative_to(R)))==sha(P),'H4_SOURCE_HELD_BOOT_ENTRY');proofpath=Path(a.install_stage_proof).absolute();need(proofpath.is_relative_to(R/'evidence/betarc01')and proofpath.is_file()and proofpath.stat().st_size<=32768 and not any(p.is_symlink()for p in[proofpath,*proofpath.parents]),'H4_ROOT_INSTALL_STAGE_PROOF_SCOPE');raw=proofpath.read_bytes();need(hashlib.sha256(raw).hexdigest()==a.install_stage_proof_sha,'H4_ROOT_INSTALL_STAGE_SHA');proof=json.loads(raw);need(proof.get('format')=='aeris-linuxport01-l17-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M906_L16_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m907'else'ROOT_COLD_VERIFIED_NORMAL_SDK_CLOSE_NOT_FLIGHT')and proof.get('candidateSHA256')==a.candidate_sha and proof.get('selectedAPKSHA256')==manifest['native']['APK_SHA256']and proof.get('authorityRestorable')is False,'ROOT_ORIGINAL_INSTALL_AND_CLEAN_CLOSURE_REQUIRED');refs=proof.get('originalEvidence');need(type(refs)is list and 4<=len(refs)<=8,'H4_INSTALL_ORIGINAL_REFS');[ref_file(r)for r in refs]
 from aeris_runtime.continuation_l17 import m906_prior,rich_table,contract_check
 priorSlot='m906'if a.slot=='m907'else'm907';priorRun='beta-rc01-sdk-continuation06'if a.slot=='m907'else'beta-rc01-sdk-continuation07';need(proof.get('priorSlot')==priorSlot,'ROOT_PRIOR_SCOPE')
 if a.slot=='m907':
  priorBoot,path=m906_prior()
 else:
  priorPath=R/'evidence/betarc01/m907/reports/coldboot-h7.json';need(proof.get('priorReportSHA256')==sha(priorPath),'ROOT_PRIOR_REPORT');report=json.loads(priorPath.read_bytes());need(report.get('candidateSHA256')==a.candidate_sha and proof.get('normalSDKExit0NoForcedKill')is True,'SAME_H7_NORMAL_PRIOR_CLOSE');oldstore=priorPath.parents[1]/'sessions'/priorRun/'android-api';last=report['samples'][-1];_,out,_=original_command(oldstore,last['commandRefs']['dump'],['dumpsys','package',PACKAGE]);path=package_state(out,broken=False);_,out,_=original_command(oldstore,last['commandRefs']['boot'],['cat','/proc/sys/kernel/random/boot_id']);priorBoot=out.decode().strip();closure=json.loads((priorPath.parents[1]/'guardian/closure.json').read_bytes());need(type(closure.get('exit'))is int and closure['exit']==0 and closure.get('failure')is None and closure.get('exceptionalPhysicalDisposal')is False and closure.get('cleanupNotes')==[]and closure.get('durablyDrained')is True and all(v.get('captureComplete')is True and v.get('failure')is None for v in closure['outputCapture'].values()),'ORIGINAL_PRIOR_NORMAL_SDK_CLOSURE')
 need(proof.get('priorKernelBootUUID')==priorBoot,'ROOT_PRIOR_ACTUAL_BOOT')
 spec=Path(a.spec).resolve();run='beta-rc01-sdk-continuation07'if a.slot=='m907'else'beta-rc01-sdk-continuation08';need(intent.get('format')=='aeris-linuxport01-l17-root-sdk-positive-intent'and intent.get('status')=='ROOT_SOURCE_QUALIFIED_SDK_ONLY_POSITIVE_CLOSE_NOT_FLIGHT'and intent.get('candidateSHA256')==a.candidate_sha and intent.get('specSHA256')==sha(spec)and intent.get('entrySHA256')==sha(P)and intent.get('slot')==a.slot and intent.get('run')==run and intent.get('prerequisiteSHA256')==a.install_stage_proof_sha,'EXACT_ROOT_H7_INTENT');scope=R/'evidence/betarc01'/a.slot;need(not scope.exists(),'FRESH_POSITIVE_SLOT');forecast=preview(candidate,a.candidate_sha,scope,R/'planning/betarc01',spec,seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'H7_POSITIVE_ADMISSION')
 if a.inspect:print(json.dumps({'status':'H4_BOOT_PREVIEW_NO_ACTORS','forecast':forecast}));return
 owner=WorkbenchRuntime(candidate,a.candidate_sha,evidence=scope,planning=R/'planning/betarc01',spec=spec,seconds=180);owner.root.mkdir(exist_ok=False);device=None;stopped=False
 def stop(sig,frame):
  nonlocal stopped
  stopped=True
 def check():need(not stopped,'H4_BOOT_TERMINATED');owner.check()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def read(args):
  device.command(args,deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=device._command_bound(args));ref=device.last_command_ref;row,argv,remote,out=command(device.root,ref);return ref,out
 try:
  owner.bootstrap();case=owner.create_case(run,seconds=180);owner.start_writer();need(case['device'].sequence==0,'UNUSED_DEVICE');device=ColdBootDeviceH4(case['device'].adb,'emulator-5582',case['device'].root,budget=owner.budget,observer_tag='AERIS_PRODUCT_STATUS');device.bind(path);device.live_check=check;ready=device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);ready_ns=json.loads(read_ref(device.root,ready))['finishedHostNs'];device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000);prep=json.loads(read_ref(device.root,device.content_reader_preparation));samples=[]
  for offset in(0,30):
   target=ready_ns+offset*1_000_000_000
   while time.monotonic_ns()<target:
    check();remaining=target-time.monotonic_ns()
    if remaining>0:time.sleep(min(.1,remaining/1e9))
   check();refs={};refs['boot'],boot=read(['shell','cat','/proc/sys/kernel/random/boot_id']);need(boot.decode().strip()==prep['kernelBootUUID']and boot.decode().strip()!=priorBoot,'NEW_STABLE_ACTUAL_BOOT');refs['user'],user=read(['shell','am','get-current-user']);need(user==b'0\n','USER0');refs['cold'],cold=read(['shell','sh','-c',COLD]);need(cold==b'ABSENT\n','NO_ACTIVITY_COLD');refs['path'],out=read(['shell','pm','path',PACKAGE]);need(out.decode().strip()=='package:'+device.base,'PERSISTED_SELECTED_CODEPATH');refs['sha'],out=read(['shell','sha256sum',device.base]);need(out.decode().split()==[manifest['native']['APK_SHA256'],device.base],'PERSISTED_SELECTED_APK');refs['dump'],out=read(['shell','dumpsys','package',PACKAGE]);need(package_state(out,broken=False)==path,'PERSISTED_PARSED_UID');value={'offsetSeconds':offset,'targetHostNs':target,'finishedHostNs':time.monotonic_ns(),'commandRefs':refs,'authorityRestorable':False};owner.write('coldboot-%02d.json'%offset,value);samples.append(value)
  uidref,uid=read(['shell','id','-u']);need(uid==b'0\n','ACTUAL_ROOT');statref,stat=read(['shell','sh','-c',STAT]);coldref,cold=read(['shell','sh','-c',COLD]);need(stat.startswith(b'directory 10141 10141 ')and cold==b'ABSENT\n'and prep.get('actualUID0')is True and prep.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','FRESH_COLD_ROOT_PRIVATE');device.diagnostic_root_cold_private=True;backup=device.export_root_private(deadline_ns=time.monotonic_ns()+60_000_000_000);semantic=contract_check(backup['path'],backup['sha256'],manifest);need(a.slot!='m908'or rich_table(backup['path'])==rich_table(report['rootPrivateBackup']['path']),'H7_SECOND_BOOT_PRIVATE_TABLE_SAME');afterref,after=read(['shell','sh','-c',COLD]);need(after==b'ABSENT\n','COLD_AFTER_TAR');value={'format':'aeris-h7-sdk-positive-observation','version':1,'status':'SDK_ONLY_ORIGINALS_OBSERVED_AWAITING_NORMAL_CLOSE','candidateSHA256':a.candidate_sha,'RootIntentSHA256':a.intent_sha,'priorKernelBootUUID':priorBoot,'baseAPK':path,'samples':samples,'rootPrivateBackup':backup,'continuation':semantic,'tarProfileObservation':{'observation':semantic['tarTransportProfile'],'originalCaptureRef':backup['captureReceiptRef']},'preparationRef':device.content_reader_preparation,'finalUIDRef':uidref,'finalStatRef':statref,'finalColdRef':coldref,'afterBackupColdRef':afterref,'APKInstalled':False,'ActivityStarted':False,'APStarted':False,'authorityRestorable':False,'flightAcceptance':False};owner.write('coldboot-h7.json',value);device.close_observer();case['maintenanceRC01']={'sdkOnlyH7':value};closed=owner.close_sdk_only();guardian=owner.close_guardian(failed=False);owner.write('owner-terminal.json',terminal_summary(owner),closing=True);print(json.dumps({'status':'SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE','flightAcceptance':False}))
 except BaseException as primary:
  if device is not None:
   try:device.close_observer()
   except BaseException as secondary:primary.add_note('H4_BOOT_DEVICE_CLOSE:'+str(secondary))
  if owner.budget is not None:
   try:owner.persist_owner_error(traceback.format_exc());owner.fail_case(primary)
   except BaseException as secondary:primary.add_note('H4_BOOT_DISPOSAL:'+str(secondary))
  try:
   if not owner.closed:owner.close_guardian(failed=True)
  except BaseException as secondary:primary.add_note('H4_BOOT_GUARDIAN:'+str(secondary))
  print(json.dumps({'status':'FAILED_SDK_POSITIVE_QUALIFICATION_NO_RETRY','error':str(primary),'notes':getattr(primary,'__notes__',[]),'flightAcceptance':False}));raise
if __name__=='__main__':main()
