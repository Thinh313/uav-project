#!/usr/bin/env python3
"""LINUXPORT01 (team entry): one fresh read-only forensic capture m802 of the state after g106 attempt 1.
Owner root-capture-h10.py plus l12_patches.py. No initial-registry semantic decoder."""
from pathlib import Path
import argparse,hashlib,json,os,re,signal,sys,time,traceback
P=Path(__file__).resolve();R=P.parents[3]
def terminal_summary(owner):
 def ref(name):
  p=owner.root/name;raw=p.read_bytes();return{'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 return{'format':'aeris-h10-forensic-owner-terminal','version':1,'status':'FORENSIC_CAPTURE_CLOSED_AWAITING_INDEPENDENT_SEMANTICS_NOT_QUALIFICATION_NOT_G1','candidateSHA256':owner.digest,'originalEvidence':[ref(n)for n in('reports/forensic-capture-h10.json','reports/native-maintenance-case-closure.json','guardian/closure.json','diagnostics/guardian-process/close.json')],'SDKQualificationClaimed':False,'G1AcceptanceClaimed':False,'registrySemanticsChecked':False,'flightAcceptance':False,'authorityRestorable':False,'normalFlightClosureClaimed':False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--candidate-sha',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--intent',required=True);ap.add_argument('--intent-sha',required=True);ap.add_argument('--prerequisite',required=True);ap.add_argument('--prerequisite-sha',required=True);ap.add_argument('--slot',choices=('m802',),required=True);ap.add_argument('--inspect',action='store_true');a=ap.parse_args();candidate=Path(a.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=a.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
 from aeris_runtime.candidate import load,sha
 from aeris_runtime.entry import module_origin_receipt
 from aeris_runtime.product_inputs import validate
 from aeris_runtime.product_runtime import WorkbenchRuntime
 from aeris_runtime.preview10 import preview
 from aeris_runtime.once_reader import read_ref
 from aeris_runtime.status15_reader import command
 from aeris_runtime.rc01 import ref_file
 from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,PACKAGE,STAT,COLD,need
 from aeris_runtime.installclosure_h4 import safe_code_path,package_state
 class CaptureDeviceH10(ReadOnlyPackageDevice):
  def bind(self,path):self.base=safe_code_path(path)
  def _command_bound(self,args):
   need(self.serial=='emulator-5582'and self.observer.tag=='AERIS_PRODUCT_STATUS','H10_FORENSIC_DEVICE')
   if args in(['shell','pm','path',PACKAGE],['shell','sha256sum',self.base]):return 4096
   if args[:1]==['install']or args==['shell','sync']:raise ValueError('H10_FORENSIC_NO_INSTALL_SYNC')
   return super()._command_bound(args)
 def scoped(path,digest,maximum):
  path=Path(path).absolute();need(path.is_relative_to(R/'evidence/betarc01')and path.is_file()and path.stat().st_size<=maximum and not any(p.is_symlink()for p in[path,*path.parents]),'H10_ROOT_METADATA_SCOPE');raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'H10_ROOT_METADATA_SHA');return json.loads(raw)
 intent=scoped(a.intent,a.intent_sha,8192);manifest=load(candidate,a.candidate_sha);module_origin_receipt(candidate);graph=validate(manifest['productInputClosure']);need(graph['pins'].get(str(P.relative_to(R)))==sha(P),'H10_SOURCE_HELD_ENTRY');prior=scoped(a.prerequisite,a.prerequisite_sha,32768);need(prior.get('format')=='aeris-linuxport01-l12-root-forensic-prerequisite'and prior.get('version')==1 and prior.get('status')=='ROOT_COLD_VERIFIED_G106_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'and prior.get('candidateSHA256')==a.candidate_sha and prior.get('selectedAPKSHA256')==manifest['native']['APK_SHA256']and prior.get('priorSlot')=='g106'and prior.get('authorityRestorable')is False,'H10_PHYSICAL_CLOSURE_PREREQUISITE');refs=prior.get('originalEvidence');need(type(refs)is list and 4<=len(refs)<=8,'H10_ROOT_ORIGINAL_REFS');[ref_file(r)for r in refs];priorBoot=prior['priorKernelBootUUID'];need(type(priorBoot)is str and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',priorBoot)is not None,'H10_PRIOR_BOOT');path=prior['baseAPK'];safe_code_path(path)
 spec=Path(a.spec).resolve();run='beta-rc01-forensic-capture02';need(intent.get('format')=='aeris-linuxport01-l12-root-forensic-intent'and intent.get('status')=='ROOT_SOURCE_QUALIFIED_READONLY_FORENSIC_CAPTURE_NOT_QUALIFICATION'and intent.get('candidateSHA256')==a.candidate_sha and intent.get('specSHA256')==sha(spec)and intent.get('entrySHA256')==sha(P)and intent.get('slot')=='m802'and intent.get('run')==run and intent.get('prerequisiteSHA256')==a.prerequisite_sha,'EXACT_ROOT_FORENSIC_INTENT');scope=R/'evidence/betarc01/m802';need(not scope.exists(),'FRESH_FORENSIC_SLOT');forecast=preview(candidate,a.candidate_sha,scope,R/'planning/betarc01',spec,seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'H10_FORENSIC_ADMISSION')
 if a.inspect:print(json.dumps({'status':'FORENSIC_PREVIEW_NO_ACTORS_NOT_QUALIFICATION','forecast':forecast}));return
 owner=WorkbenchRuntime(candidate,a.candidate_sha,evidence=scope,planning=R/'planning/betarc01',spec=spec,seconds=180);owner.root.mkdir(exist_ok=False);device=None;stopped=False
 def stop(sig,frame):
  nonlocal stopped
  stopped=True
 def check():need(not stopped,'H10_CAPTURE_TERMINATED');owner.check()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def read(args):
  device.command(args,deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=device._command_bound(args));ref=device.last_command_ref;row,argv,remote,out=command(device.root,ref);return ref,out
 try:
  owner.bootstrap();case=owner.create_case(run,seconds=180);owner.start_writer();need(case['device'].sequence==0,'UNUSED_DEVICE');device=CaptureDeviceH10(case['device'].adb,'emulator-5582',case['device'].root,budget=owner.budget,observer_tag='AERIS_PRODUCT_STATUS');device.bind(path);device.live_check=check;ready=device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);ready_ns=json.loads(read_ref(device.root,ready))['finishedHostNs'];device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000);prep=json.loads(read_ref(device.root,device.content_reader_preparation));samples=[]
  for offset in(0,30):
   target=ready_ns+offset*1_000_000_000
   while time.monotonic_ns()<target:
    check();remaining=target-time.monotonic_ns()
    if remaining>0:time.sleep(min(.1,remaining/1e9))
   check();refs={};refs['boot'],boot=read(['shell','cat','/proc/sys/kernel/random/boot_id']);need(boot.decode().strip()==prep['kernelBootUUID']and boot.decode().strip()!=priorBoot,'NEW_STABLE_ACTUAL_BOOT');refs['user'],user=read(['shell','am','get-current-user']);need(user==b'0\n','USER0');refs['cold'],cold=read(['shell','sh','-c',COLD]);need(cold==b'ABSENT\n','NO_ACTIVITY_COLD');refs['path'],out=read(['shell','pm','path',PACKAGE]);need(out.decode().strip()=='package:'+device.base,'PERSISTED_SELECTED_CODEPATH');refs['sha'],out=read(['shell','sha256sum',device.base]);need(out.decode().split()==[manifest['native']['APK_SHA256'],device.base],'PERSISTED_SELECTED_APK');refs['dump'],out=read(['shell','dumpsys','package',PACKAGE]);need(package_state(out,broken=False)==path,'PERSISTED_PARSED_UID');value={'offsetSeconds':offset,'targetHostNs':target,'finishedHostNs':time.monotonic_ns(),'commandRefs':refs,'authorityRestorable':False};owner.write('forensic-cold-%02d.json'%offset,value);samples.append(value)
  uidref,uid=read(['shell','id','-u']);need(uid==b'0\n','ACTUAL_ROOT');statref,stat=read(['shell','sh','-c',STAT]);coldref,cold=read(['shell','sh','-c',COLD]);need(stat.startswith(b'directory 10141 10141 ')and cold==b'ABSENT\n'and prep.get('actualUID0')is True and prep.get('confirmation')=='READONLY_UID0_AND_SAME_KERNEL_BOOT_OBSERVED','FRESH_COLD_ROOT_PRIVATE');device.diagnostic_root_cold_private=True;backup=device.export_root_private(deadline_ns=time.monotonic_ns()+60_000_000_000);afterref,after=read(['shell','sh','-c',COLD]);need(after==b'ABSENT\n','COLD_AFTER_TAR');value={'format':'aeris-h10-forensic-raw-observation','version':1,'status':'COMPLETE_ORIGINAL_CAPTURE_AWAITING_GENUINE_SDK_CLOSE_AND_INDEPENDENT_SEMANTICS','disposition':'FORENSIC_NOT_QUALIFICATION_NOT_G1','candidateSHA256':a.candidate_sha,'RootIntentSHA256':a.intent_sha,'priorKernelBootUUID':priorBoot,'baseAPK':path,'samples':samples,'rootPrivateBackup':backup,'preparationRef':device.content_reader_preparation,'finalUIDRef':uidref,'finalStatRef':statref,'finalColdRef':coldref,'afterBackupColdRef':afterref,'APKInstalled':False,'ActivityStarted':False,'APStarted':False,'authorityRestorable':False,'flightAcceptance':False,'SDKQualificationClaimed':False,'registrySemanticsChecked':False};owner.write('forensic-capture-h10.json',value);device.close_observer();case['maintenanceRC01']={'forensicOnlyH10':value};closed=owner.close_forensic_only();guardian=owner.close_guardian(failed=False);owner.write('owner-terminal.json',terminal_summary(owner),closing=True);print(json.dumps({'status':'FORENSIC_CAPTURE_CLOSED_AWAITING_INDEPENDENT_SEMANTICS_NOT_QUALIFICATION_NOT_G1','flightAcceptance':False}))
 except BaseException as primary:
  if device is not None:
   try:device.close_observer()
   except BaseException as secondary:primary.add_note('H10_CAPTURE_DEVICE_CLOSE:'+str(secondary))
  if owner.budget is not None:
   try:owner.persist_owner_error(traceback.format_exc());owner.fail_case(primary)
   except BaseException as secondary:primary.add_note('H10_CAPTURE_DISPOSAL:'+str(secondary))
  try:
   if not owner.closed:owner.close_guardian(failed=True)
  except BaseException as secondary:primary.add_note('H10_CAPTURE_GUARDIAN:'+str(secondary))
  print(json.dumps({'status':'FAILED_FORENSIC_CAPTURE_NO_RETRY_NOT_QUALIFICATION','error':str(primary),'notes':getattr(primary,'__notes__',[]),'flightAcceptance':False}));raise
if __name__=='__main__':main()
