#!/usr/bin/env python3
"""Last fixed m202 read-only timed diagnosis. No installation or G1 retry."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,signal,sys,time,traceback
P=Path(__file__).resolve();R=P.parents[3]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--candidate-sha',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--intent',required=True);ap.add_argument('--intent-sha',required=True);ap.add_argument('--inspect',action='store_true');args=ap.parse_args();candidate=Path(args.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=args.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
 from aeris_runtime.candidate import load,sha
 from aeris_runtime.entry import module_origin_receipt
 from aeris_runtime.product_inputs import validate
 from aeris_runtime.product_runtime import WorkbenchRuntime
 from aeris_runtime.preview10 import preview
 from aeris_runtime.once_reader import read_ref
 from aeris_runtime.status15_reader import command
 dep=R/'planning/betarc01/diagnostics/package_device01.py';helper=P.with_name('probe01.py');ip=Path(args.intent).resolve();need=lambda v,n:None if v else(_ for _ in()).throw(ValueError('REBOOT_QA_'+n));need(ip.is_relative_to(R/'evidence/betarc01')and ip.is_file()and not any(p.is_symlink()for p in[ip,*ip.parents])and ip.stat().st_size<=8192,'ROOT_INTENT_SCOPE');raw=ip.read_bytes();need(hashlib.sha256(raw).hexdigest()==args.intent_sha,'ROOT_INTENT_SHA');intent=json.loads(raw);spec=Path(args.spec).resolve();m201=R/'evidence/betarc01/m201/reports/known-state-repair01.json';report=json.loads(m201.read_bytes());pins={str(p.relative_to(R)):sha(p)for p in[P,helper,dep]}
 need(intent.get('format')=='aeris-betarc01-root-reboot-readonly-intent'and intent.get('version')==1 and intent.get('status')=='ROOT_SOURCE_QUALIFIED_FINAL_READONLY_DIAGNOSTIC_NOT_BETA'and intent.get('slot')=='m202'and intent.get('run')=='beta-rc01-reboot-diagnostic01'and intent.get('candidateSHA256')==args.candidate_sha and intent.get('specSHA256')==sha(spec)and intent.get('filesSHA256')==pins and intent.get('m201ReportSHA256')==sha(m201)and intent.get('m201PostPathRef')==report['postPathRef']and intent.get('m201PostDumpRef')==report['postDumpRef']and intent.get('noInstallNoActivityNoAP')is True,'ROOT_INTENT_SOURCE_AND_ORIGINAL_M201')
 hs=importlib.util.spec_from_file_location('root_qualified_reboot_probe01',helper);mod=importlib.util.module_from_spec(hs);hs.loader.exec_module(mod)
 oldroot=R/'evidence/betarc01/m201/sessions/beta-rc01-known-state-repair01/android-api';_,_,remote,pathraw=command(oldroot,report['postPathRef']);need(remote==['pm','path',mod.PACKAGE]and pathraw.startswith(b'package:')and pathraw.count(b'\n')==1,'ORIGINAL_M201_POST_PATH');base=pathraw.decode().strip()[8:];_,_,remote,dumpraw=command(oldroot,report['postDumpRef']);need(remote==['dumpsys','package',mod.PACKAGE]and b'    pkg=null\n'not in dumpraw and ('    codePath='+base[:-9]+'\n').encode()in dumpraw,'ORIGINAL_M201_PARSED_MATCHING_CODE');need(report.get('candidateSHA256')==args.candidate_sha and report.get('status')=='REPAIR_OBSERVED_ORIGINALS_CONSERVED_NOT_G1_ACCEPTANCE','ORIGINAL_M201_SCOPE')
 manifest=load(candidate,args.candidate_sha);module_origin_receipt(candidate);validate(manifest['productInputClosure']);evidence=R/'evidence/betarc01/m202';need(not evidence.exists(),'FRESH_FINAL_SLOT_NO_RETRY');forecast=preview(candidate,args.candidate_sha,evidence,R/'planning/betarc01',spec,seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'PURE_ADMISSION')
 if args.inspect:print(json.dumps({'status':'FINAL_READONLY_REBOOT_DIAGNOSTIC_PREVIEW_ONLY','forecast':forecast}));return
 owner=WorkbenchRuntime(candidate,args.candidate_sha,evidence=evidence,planning=R/'planning/betarc01',spec=spec,seconds=180);owner.root.mkdir(exist_ok=False);device=None;stopped=False
 def stop(sig,frame):
  nonlocal stopped
  stopped=True
 def check():need(not stopped,'TERMINATED');owner.check()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 class DiagnosticComplete(Exception):pass
 try:
  owner.bootstrap();case=owner.create_case(intent['run'],seconds=180);owner.start_writer()
  need(case['device'].sequence==0 and not(case['device'].root/'command-stream.raw').exists(),'EMPTY_COMMAND_DOMAIN');device=mod.RebootReadOnlyDevice(case['device'].adb,'emulator-5582',case['device'].root,budget=owner.budget,observer_tag='AERIS_PRODUCT_STATUS');device.bind_path(base);device.live_check=check
  ready=device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);ready_value=json.loads(read_ref(device.root,ready));ready_ns=ready_value['finishedHostNs'];device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000)
  samples=mod.sample_series(device,check,ready_ns,lambda value:owner.write('reboot-sample-%02d.json'%value['offsetSeconds'],value));fixed=[]
  for cmd in mod.FIXED_COMMANDS:check();row,_=mod.observe(device,cmd);fixed.append(row)
  uidrow,uid=mod.observe(device,['shell','id','-u']);statrow,stat=mod.observe(device,['shell','sh','-c',mod.STAT]);coldrow,cold=mod.observe(device,['shell','sh','-c',mod.COLD]);preparation=json.loads(read_ref(device.root,device.content_reader_preparation));backup=None;boots=[s['kernelBootUUID']for s in samples]
  if uidrow['status']=='OBSERVED_EXIT0_EMPTY_STDERR'and uid==b'0\n'and stat.startswith(b'directory 10141 10141 ')and all(b==preparation['kernelBootUUID']for b in boots)and mod.private_export_eligible(statrow,stat,coldrow,cold,preparation):device.diagnostic_root_cold_private=True;backup=device.export_root_private(deadline_ns=time.monotonic_ns()+60_000_000_000)
  owner.write('reboot-diagnostic01.json',{'format':'aeris-final-reboot-readonly-diagnostic','version':1,'status':'TIMED_READONLY_EVIDENCE_COMPLETE_NOT_BETA','candidateSHA256':args.candidate_sha,'RootIntentSHA256':args.intent_sha,'readyRef':ready,'m201ReportSHA256':sha(m201),'originalM201CodePath':base,'sampleReports':['reports/reboot-sample-%02d.json'%s['offsetSeconds']for s in samples],'fixedObservations':fixed,'finalUIDRef':uidrow,'finalPrivateRef':statrow,'finalColdRef':coldrow,'rootPrivateBackup':backup,'evidenceWriterStarted':True,'MAVLinkWriterStarted':False,'ActivityStarted':False,'APStarted':False,'APKInstalled':False,'noInstallOrSyncOrSentinel':True,'rootCauseConcluded':False,'flightAcceptance':False});raise DiagnosticComplete('TIMED_READONLY_EVIDENCE_COMPLETE_NOT_BETA')
 except BaseException as primary:
  if device is not None:
   try:device.close_observer()
   except BaseException as secondary:primary.add_note('DIAGNOSTIC_DEVICE_CLOSE:'+str(secondary))
  if owner.budget is not None:
   try:owner.persist_owner_error(traceback.format_exc());owner.fail_case(primary)
   except BaseException as secondary:primary.add_note('DIAGNOSTIC_FAILED_DRAIN:'+str(secondary))
  try:
   if not owner.closed:owner.close_guardian(failed=True)
  except BaseException as secondary:primary.add_note('DIAGNOSTIC_GUARDIAN_CLOSE:'+str(secondary))
  print(json.dumps({'status':'TIMED_READONLY_EVIDENCE_COMPLETE_NOT_BETA'if isinstance(primary,DiagnosticComplete)else'FAILED_FINAL_DIAGNOSTIC_NOT_ACCEPTANCE','error':str(primary),'notes':getattr(primary,'__notes__',[]),'flightAcceptance':False,'evidence':str(owner.root)}))
  if not isinstance(primary,DiagnosticComplete):raise
if __name__=='__main__':main()
