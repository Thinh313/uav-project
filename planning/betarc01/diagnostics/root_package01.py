#!/usr/bin/env python3
"""Root-intent-qualified package-state QA probe, never Beta/G1 acceptance."""
from pathlib import Path
import argparse,hashlib,json,os,signal,sys,time,traceback
P=Path(__file__).resolve();R=P.parents[3]
def main():
 a=argparse.ArgumentParser();a.add_argument('--candidate',required=True);a.add_argument('--candidate-sha',required=True);a.add_argument('--spec',required=True);a.add_argument('--intent',required=True);a.add_argument('--intent-sha',required=True);a.add_argument('--inspect',action='store_true');args=a.parse_args();candidate=Path(args.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=args.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
 from aeris_runtime.candidate import load
 from aeris_runtime.entry import module_origin_receipt
 from aeris_runtime.product_inputs import validate
 from aeris_runtime.product_runtime import WorkbenchRuntime
 from aeris_runtime.preview10 import preview
 from aeris_runtime.once_reader import read_ref
 from planning.betarc01.diagnostics.package_device01 import ReadOnlyPackageDevice,READ_COMMANDS,STAT,COLD,need,private_export_eligible
 ip=Path(args.intent).resolve();need(ip.is_relative_to(R/'evidence/betarc01')and ip.is_file()and not any(p.is_symlink()for p in[ip,*ip.parents])and ip.stat().st_size<=8192,'ROOT_INTENT_SCOPE');raw=ip.read_bytes();need(hashlib.sha256(raw).hexdigest()==args.intent_sha,'ROOT_INTENT_SHA');intent=json.loads(raw);spec=Path(args.spec).resolve()
 expected_files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[P,P.with_name('package_device01.py')]}
 need(intent.get('format')=='aeris-betarc01-root-package-diagnostic-intent'and intent.get('version')==1 and intent.get('status')=='ROOT_SOURCE_QUALIFIED_READONLY_DIAGNOSTIC_NOT_BETA'and intent.get('candidateSHA256')==args.candidate_sha and intent.get('specSHA256')==hashlib.sha256(spec.read_bytes()).hexdigest()and intent.get('slot')=='m101'and intent.get('run')=='beta-rc01-package-diagnostic02'and intent.get('filesSHA256')==expected_files and intent.get('noActivityNoAP')is True and intent.get('flightAcceptance')is False,'ROOT_INTENT_EXACT_SOURCE_CANDIDATE_SCOPE')
 manifest=load(candidate,args.candidate_sha);module_origin_receipt(candidate);validate(manifest['productInputClosure']);evidence=R/'evidence/betarc01/m101';need(not evidence.exists(),'FRESH_SLOT_NO_OVERWRITE');forecast=preview(candidate,args.candidate_sha,evidence,R/'planning/betarc01',spec,seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'PURE_ADMISSION_NO_ACTORS')
 if args.inspect:print(json.dumps({'status':'ROOT_PACKAGE_PROBE_PREVIEW_ONLY','forecast':forecast,'intentSHA256':args.intent_sha}));return
 owner=WorkbenchRuntime(candidate,args.candidate_sha,evidence=evidence,planning=R/'planning/betarc01',spec=spec,seconds=180);owner.root.mkdir(exist_ok=False);stopped=False;device=None
 def stop(sig,frame):
  nonlocal stopped
  stopped=True
 def check():need(not stopped,'TERMINATED');owner.check()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 class DiagnosticComplete(Exception):pass
 def observe(args):
  deadline=time.monotonic_ns()+10_000_000_000;error=None;previous=device.sequence
  try:device.command(list(args),deadline_ns=deadline,maximum_bytes=READ_COMMANDS[tuple(args)])
  except RuntimeError as exc:
   row=device.last_command
   if device.sequence!=previous+1 or row is None or row.get('sequence')!=device.sequence or row.get('captureComplete')is not True or row.get('failure')not in('RuntimeError:ANDROID_COMMAND_EXIT:'+str(row.get('exit')),'RuntimeError:ANDROID_COMMAND_STDERR_PREFIX_RETAINED_FAILURE'):raise
   error=str(exc)
  row=device.last_command;out=read_ref(device.root,row['stdoutRef']);err=read_ref(device.root,row['stderrRef']);value={'command':list(args),'commandReceiptRef':device.last_command_ref,'status':'OBSERVED_EXIT0_EMPTY_STDERR'if error is None else'UNKNOWN_NONZERO_OR_STDERR_ORIGINAL_PRESERVED','exit':row['exit'],'error':error,'stdoutBytes':len(out),'stdoutSHA256':hashlib.sha256(out).hexdigest(),'stderrBytes':len(err),'stderrSHA256':hashlib.sha256(err).hexdigest()};return value,out
 try:
  owner.bootstrap();case=owner.create_case(intent['run'],seconds=180);owner.start_writer()
  # The frozen exact ProductProbe retains its original unused Device. This
  # separate QA adapter owns the same still-empty receipt namespace only.
  need(case['device'].sequence==0 and not(case['device'].root/'command-stream.raw').exists(),'EMPTY_ORIGINAL_COMMAND_DOMAIN');device=ReadOnlyPackageDevice(case['device'].adb,'emulator-5582',case['device'].root,budget=owner.budget,observer_tag='AERIS_PRODUCT_STATUS');device.live_check=check
  device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000);rows=[];outputs={}
  for cmd in READ_COMMANDS:
   check();row,out=observe(cmd);rows.append(row);outputs[cmd]=out
  stat=outputs[('shell','sh','-c',STAT)];cold=outputs[('shell','sh','-c',COLD)];backup=None
  row_by_command={tuple(row['command']):row for row in rows};preparation=json.loads(read_ref(device.root,device.content_reader_preparation))
  if private_export_eligible(row_by_command[('shell','sh','-c',STAT)],stat,row_by_command[('shell','sh','-c',COLD)],cold,preparation):
   need(getattr(device,'content_reader_preparation',None)is not None,'ACTUAL_ROOT_RECEIPT');device.diagnostic_root_cold_private=True;backup=device.export_root_private(deadline_ns=time.monotonic_ns()+60_000_000_000)
  report={'format':'aeris-betarc01-package-state-diagnostic','version':1,'status':'SOURCE_READONLY_DIAGNOSTIC_COMPLETE_NOT_FLIGHT','candidateSHA256':args.candidate_sha,'intentSHA256':args.intent_sha,'sourceFilesSHA256':expected_files,'observations':rows,'rootPrivateBackup':backup,'privateBackupConservationClaimed':False,'originalG101EvidenceChanged':False,'evidenceWriterStarted':True,'MAVLinkWriterStarted':False,'ActivityStarted':False,'APStarted':False,'authorityRestored':False,'flightAcceptance':False,'packageAbsenceIsNotPermanentDeletionProof':True};owner.write('package-diagnostic01.json',report);raise DiagnosticComplete('SOURCE_READONLY_DIAGNOSTIC_COMPLETE_NOT_FLIGHT')
 except BaseException as primary:
  if device is not None:
   try:device.close_observer()
   except BaseException as secondary:primary.add_note('QA_DEVICE_CLOSE:'+str(secondary))
  if owner.budget is not None:
   try:owner.persist_owner_error(traceback.format_exc());owner.fail_case(primary)
   except BaseException as secondary:primary.add_note('QA_FAILED_DRAIN:'+str(secondary))
  try:
   if not owner.closed:owner.close_guardian(failed=True)
  except BaseException as secondary:primary.add_note('QA_GUARDIAN_CLOSE:'+str(secondary))
  print(json.dumps({'status':'SOURCE_READONLY_DIAGNOSTIC_COMPLETE_NOT_FLIGHT'if isinstance(primary,DiagnosticComplete)else'FAILED_READONLY_DIAGNOSTIC_NOT_ACCEPTANCE','error':str(primary),'notes':getattr(primary,'__notes__',[]),'evidence':str(owner.root),'flightAcceptance':False}))
  if not isinstance(primary,DiagnosticComplete):raise
if __name__=='__main__':main()
