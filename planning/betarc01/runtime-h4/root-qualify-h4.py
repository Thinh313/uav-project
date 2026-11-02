#!/usr/bin/env python3
"""Fresh coldboot qualification only; no install, Activity, AP or automatic repair."""
from pathlib import Path
import argparse,hashlib,json,os,signal,sys,time,traceback
P=Path(__file__).resolve();R=P.parents[3]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--candidate-sha',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--intent',required=True);ap.add_argument('--intent-sha',required=True);ap.add_argument('--install-stage-proof',required=True);ap.add_argument('--install-stage-proof-sha',required=True);ap.add_argument('--inspect',action='store_true');a=ap.parse_args();candidate=Path(a.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=a.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
 from aeris_runtime.candidate import load,sha
 from aeris_runtime.entry import module_origin_receipt
 from aeris_runtime.product_inputs import validate
 from aeris_runtime.product_runtime import WorkbenchRuntime
 from aeris_runtime.preview10 import preview
 from aeris_runtime.once_reader import read_ref
 from aeris_runtime.status15_reader import command
 from aeris_runtime.rc01 import ref_file
 from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,PACKAGE,STAT,COLD,private_export_eligible,need
 from aeris_runtime.installclosure_h4 import private_table,original_private_table,safe_code_path,package_state
 class ColdBootDeviceH4(ReadOnlyPackageDevice):
  def bind(self,path):self.base=safe_code_path(path)
  def _command_bound(self,args):
   need(self.serial=='emulator-5582'and self.observer.tag=='AERIS_PRODUCT_STATUS','H4_COLD_DEVICE')
   if args in(['shell','pm','path',PACKAGE],['shell','sha256sum',self.base]):return 4096
   if args[:1]==['install']or args==['shell','sync']:raise ValueError('H4_BOOT_NO_INSTALL_SYNC')
   return super()._command_bound(args)
 intentpath=Path(a.intent).resolve();need(intentpath.is_relative_to(R/'evidence/betarc01')and intentpath.is_file()and intentpath.stat().st_size<=8192 and not any(p.is_symlink()for p in[intentpath,*intentpath.parents]),'H4_INTENT_SCOPE');raw=intentpath.read_bytes();need(hashlib.sha256(raw).hexdigest()==a.intent_sha,'H4_INTENT_SHA');intent=json.loads(raw);manifest=load(candidate,a.candidate_sha);module_origin_receipt(candidate);graph=validate(manifest['productInputClosure']);need(graph['pins'].get(str(P.relative_to(R)))==sha(P),'H4_SOURCE_HELD_BOOT_ENTRY');proofpath=Path(a.install_stage_proof).absolute();need(proofpath.is_relative_to(R/'evidence/betarc01')and proofpath.is_file()and proofpath.stat().st_size<=32768 and not any(p.is_symlink()for p in[proofpath,*proofpath.parents]),'H4_ROOT_INSTALL_STAGE_PROOF_SCOPE');raw=proofpath.read_bytes();need(hashlib.sha256(raw).hexdigest()==a.install_stage_proof_sha,'H4_ROOT_INSTALL_STAGE_SHA');proof=json.loads(raw);need(proof.get('format')=='aeris-h4-root-m301-cold-acceptance'and proof.get('status')=='ROOT_COLD_VERIFIED_PUSH_INSTALL_SYNC_AND_SDK_EXIT0_NOT_FLIGHT'and proof.get('candidateSHA256')==a.candidate_sha and proof.get('SDKExitZeroNoForcedKill')is True and proof.get('authorityRestorable')is False,'ROOT_ORIGINAL_INSTALL_AND_CLEAN_CLOSURE_REQUIRED');refs=proof.get('originalEvidence');need(type(refs)is list and 4<=len(refs)<=8,'H4_INSTALL_ORIGINAL_REFS');[ref_file(r)for r in refs]
 install=R/'evidence/betarc01/m301/reports/persistent-install-h4.json';report=json.loads(install.read_bytes());need(report.get('candidateSHA256')==a.candidate_sha and report.get('status')=='PUSH_INSTALL_AND_SYNC_OBSERVED_NOT_BOOT_OR_G1_ACCEPTANCE'and proof.get('installReportSHA256')==sha(install),'SAME_RELEASE_OBSERVED_PUSH_SYNC');oldstore=R/'evidence/betarc01/m301/sessions/beta-rc01-persistent-install01/android-api';_,_,remote,out=command(oldstore,report['postDumpRef']);need(remote==['dumpsys','package',PACKAGE],'ORIGINAL_INSTALLED_DUMP');path=package_state(out,broken=False);spec=Path(a.spec).resolve();need(intent.get('format')=='aeris-h4-root-coldboot-intent'and intent.get('status')=='ROOT_SOURCE_QUALIFIED_COLD_BOOT_NO_ACTIVITY'and intent.get('candidateSHA256')==a.candidate_sha and intent.get('specSHA256')==sha(spec)and intent.get('entrySHA256')==sha(P)and intent.get('slot')=='m302'and intent.get('run')=='beta-rc01-coldboot01'and intent.get('installStageProofSHA256')==a.install_stage_proof_sha,'EXACT_ROOT_COLD_BOOT_INTENT');scope=R/'evidence/betarc01/m302';need(not scope.exists(),'FRESH_COLD_BOOT_SLOT');forecast=preview(candidate,a.candidate_sha,scope,R/'planning/betarc01',spec,seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'H4_BOOT_ADMISSION')
 if a.inspect:print(json.dumps({'status':'H4_BOOT_PREVIEW_NO_ACTORS','forecast':forecast}));return
 owner=WorkbenchRuntime(candidate,a.candidate_sha,evidence=scope,planning=R/'planning/betarc01',spec=spec,seconds=180);owner.root.mkdir(exist_ok=False);device=None;stopped=False
 def stop(sig,frame):
  nonlocal stopped
  stopped=True
 def check():need(not stopped,'H4_BOOT_TERMINATED');owner.check()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 class QualifiedDiagnostic(Exception):pass
 def read(args):
  device.command(args,deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=device._command_bound(args));ref=device.last_command_ref;row,argv,remote,out=command(device.root,ref);return ref,out
 try:
  owner.bootstrap();case=owner.create_case('beta-rc01-coldboot01',seconds=180);owner.start_writer();need(case['device'].sequence==0,'UNUSED_DEVICE');device=ColdBootDeviceH4(case['device'].adb,'emulator-5582',case['device'].root,budget=owner.budget,observer_tag='AERIS_PRODUCT_STATUS');device.bind(path);device.live_check=check;ready=device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);ready_ns=json.loads(read_ref(device.root,ready))['finishedHostNs'];device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000);prep=json.loads(read_ref(device.root,device.content_reader_preparation));samples=[]
  for offset in(0,30):
   target=ready_ns+offset*1_000_000_000
   while time.monotonic_ns()<target:
    check();remaining=target-time.monotonic_ns()
    if remaining>0:time.sleep(min(.1,remaining/1e9))
   check();refs={};refs['boot'],boot=read(['shell','cat','/proc/sys/kernel/random/boot_id']);need(boot.decode().strip()==prep['kernelBootUUID'],'SAME_QUALIFICATION_BOOT');refs['user'],user=read(['shell','am','get-current-user']);need(user==b'0\n','USER0');refs['cold'],cold=read(['shell','sh','-c',COLD]);need(cold==b'ABSENT\n','NO_ACTIVITY_COLD');refs['path'],out=read(['shell','pm','path',PACKAGE]);need(out.decode().strip()=='package:'+device.base,'PERSISTED_SELECTED_CODEPATH');refs['sha'],out=read(['shell','sha256sum',device.base]);need(out.decode().split()==[manifest['native']['APK_SHA256'],device.base],'PERSISTED_SELECTED_APK');refs['dump'],out=read(['shell','dumpsys','package',PACKAGE]);need(package_state(out,broken=False)==path,'PERSISTED_PARSED_UID');value={'offsetSeconds':offset,'targetHostNs':target,'finishedHostNs':time.monotonic_ns(),'commandRefs':refs,'authorityRestorable':False};owner.write('coldboot-%02d.json'%offset,value);samples.append(value)
  uidref,uid=read(['shell','id','-u']);need(uid==b'0\n','ACTUAL_ROOT');statref,stat=read(['shell','sh','-c',STAT]);coldref,cold=read(['shell','sh','-c',COLD]);need(stat.startswith(b'directory 10141 10141 ')and cold==b'ABSENT\n'and prep.get('actualUID0')is True and prep.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','FRESH_COLD_ROOT_PRIVATE');device.diagnostic_root_cold_private=True;backup=device.export_root_private(deadline_ns=time.monotonic_ns()+60_000_000_000);need(private_table(backup['path'])==original_private_table(R),'FRESH_BOOT_PRIVATE70_CONSERVED');owner.write('coldboot-h4.json',{'format':'aeris-h4-coldboot-qualification','version':1,'status':'FRESH_BOOT_SELECTED_APK_PRIVATE_OBSERVED_NOT_G1_ACCEPTANCE','candidateSHA256':a.candidate_sha,'RootIntentSHA256':a.intent_sha,'samples':samples,'rootPrivateBackup':backup,'finalUIDRef':uidref,'finalStatRef':statref,'finalColdRef':coldref,'APKInstalled':False,'ActivityStarted':False,'APStarted':False,'authorityRestorable':False,'flightAcceptance':False});raise QualifiedDiagnostic('FRESH_BOOT_SELECTED_APK_PRIVATE_OBSERVED_NOT_G1_ACCEPTANCE')
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
  print(json.dumps({'status':'FRESH_BOOT_SELECTED_APK_PRIVATE_OBSERVED_NOT_G1_ACCEPTANCE'if isinstance(primary,QualifiedDiagnostic)else'FAILED_FRESH_BOOT_QUALIFICATION_NO_RETRY','error':str(primary),'notes':getattr(primary,'__notes__',[]),'flightAcceptance':False}))
  if not isinstance(primary,QualifiedDiagnostic):raise
if __name__=='__main__':main()
