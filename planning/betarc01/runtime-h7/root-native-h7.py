#!/usr/bin/env python3
"""Source-held native-only migration slot. Never starts AP/backend or flight."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,os,signal,sys,time,traceback
P=argparse.ArgumentParser();P.add_argument('--candidate',required=True);P.add_argument('--candidate-sha',required=True);P.add_argument('--spec',required=True);P.add_argument('--node',required=True);P.add_argument('--run',required=True);P.add_argument('--slot',required=True,choices=('g104',));P.add_argument('--install-closure-proof',required=True);P.add_argument('--install-closure-proof-sha',required=True);P.add_argument('--inspect',action='store_true');args=P.parse_args()
REPO=Path(__file__).resolve().parents[3];CANDIDATE=Path(args.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(REPO),AERIS_CANDIDATE_DIR=str(CANDIDATE),AERIS_CANDIDATE_SHA256=args.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(CANDIDATE/'source'),str(REPO)]
from aeris_runtime.candidate import load
from aeris_runtime.product_inputs import validate
from aeris_runtime.entry import module_origin_receipt
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.preview10 import preview
from aeris_runtime.native17 import preserve_legacy,admin,archive_check,need,PACKAGE
from aeris_runtime.adoption17 import adopt_existing17
from aeris_runtime.reconcile_h7 import require_qualification,resume_existing
qualification=require_qualification(args.install_closure_proof,args.install_closure_proof_sha,args.candidate_sha)
manifest=load(CANDIDATE,args.candidate_sha);module_origin_receipt(CANDIDATE);graph=validate(manifest['productInputClosure']);entry=Path(__file__).resolve();scenario=REPO/'planning/nativejournal17/runtime/scenario-native-only17.py'
for p in(entry,scenario):need(graph['pins'].get(str(p.relative_to(REPO)))==hashlib.sha256(p.read_bytes()).hexdigest(),'EXACT_SOURCE_HELD_ENTRY_AND_SCENARIO')
need(Path(args.node).is_absolute()and Path(args.node).is_file(),'EXACT_NODE');need(manifest['native'].get('journalLifecycleProtocolSHA256')is not None,'REVIEWED_NATIVE17_ONLY')
forecast=preview(CANDIDATE,args.candidate_sha,REPO/'evidence/betarc01'/args.slot,REPO/'planning/betarc01',Path(args.spec),seconds=180)
need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'PURE_ADMISSION_REFUSED_NO_SLOT')
if args.inspect:print(json.dumps({'status':'SOURCE_NATIVE_ONLY_INSPECTED_NO_ACTORS','forecast':forecast}));raise SystemExit(0)
owner=WorkbenchRuntime(CANDIDATE,args.candidate_sha,evidence=REPO/'evidence/betarc01'/args.slot,planning=REPO/'planning/betarc01',spec=args.spec,seconds=180);owner.root.mkdir(exist_ok=False);stopped=False
def stop(sig,frame):
 global stopped
 stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
def check():need(not stopped,'TERMINATION');owner.check()
def wait_progress(kind,predicate=lambda q:True,seconds=30):
 end=time.monotonic_ns()+int(seconds*1e9);c=owner.case;p=c['root']/'product/reports/companion-progress.jsonl'
 while time.monotonic_ns()<end:
  check()
  if p.exists():
   b=p.read_bytes();need(len(b)<=1024*1024 and b.endswith(b'\n'),'ORIGINAL_PROGRESS_BOUND')
   for line in b.splitlines():
    row=json.loads(line);need(row['pid']==c['companion'].process.pid and row['run']==args.run,'OWNED_COMPANION_PROGRESS')
    if row['kind']=='FAILED':raise RuntimeError('COMPANION_FAILED:'+str(row['data']))
    if row['kind']==kind and predicate(row['data']):return row
  time.sleep(.05)
 raise TimeoutError('NATIVE17_BOUNDED_PROGRESS_'+kind)
def command(action):
 need(action in('NATIVE_READY','NATIVE_ROLLOVER','SEAL_PRODUCT','VERIFY_NATIVE_UNUSED17'),'NATIVE_ONLY_MANAGEMENT_ALLOWLIST');c=owner.case;c.setdefault('managementSequence',0);c['managementSequence']+=1;n=c['managementSequence'];owner.budget.append_json('external_task',owner.root/'reports'/('companion-control-'+args.run+'.jsonl'),{'sequence':n,'ownerPID':os.getpid(),'run':args.run,'candidateSHA256':args.candidate_sha,'action':action},maximum=2048);return wait_progress('COMMAND_COMPLETE',lambda q:q.get('sequence')==n,seconds=20)['data']['result']
try:
 owner.bootstrap();case=owner.create_case(args.run,seconds=180);descriptor=owner.start_writer();device=case['device'];device.live_check=check;device.wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);device.prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000)
 preserve_legacy(owner,case,deadline_ns=time.monotonic_ns()+60_000_000_000);post=resume_existing(owner,case,deadline_ns=time.monotonic_ns()+60_000_000_000);archive_check(owner,case,post,'migration',deadline_ns=time.monotonic_ns()+30_000_000_000)
 descriptor_path=owner.root/'reports/product-descriptor-01.json';argv=[args.node,'--import',str(REPO/'planning/nativejournal17/runtime/verified-loader.mjs'),str(REPO/'planning/betarc01/runtime/product-companion-rc01.mjs'),'--manifest',str(CANDIDATE/'candidate.json'),'--candidate-sha',args.candidate_sha,'--descriptor',str(descriptor_path),'--owner-pid',str(os.getpid()),'--maximum-seconds','540'];owner.start_companion(argv);wait_progress('READY',seconds=45)
 current=device.command(['reverse','--list'],deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=4096).decode().splitlines();case['createdReverses']=[]
 for port in(8895,8896):
  endpoint='tcp:'+str(port);found=[r.split()for r in current if endpoint in r.split()]
  if found:need(all(r[-2:]==[endpoint,endpoint]for r in found),'EXISTING_REVERSE_TARGET')
  else:device.command(['reverse','--no-rebind',endpoint,endpoint],deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=4096);case['createdReverses'].append(port)
 case['native'].start(deadline_ns=time.monotonic_ns()+20_000_000_000);case['writer'].register_native_probe(case['native']);command('NATIVE_READY');case['monitor'].start();case['phase']='NATIVE_UI_READY';case['managementCommand']=command
 spec=importlib.util.spec_from_file_location('held_native_only_scenario17',scenario);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);first=module.first(owner,case,check)
 device.command(['shell','am','force-stop',PACKAGE],deadline_ns=time.monotonic_ns()+10_000_000_000);device._cold_absence(time.monotonic_ns()+10_000_000_000);first_export=device.export17('after-first-close',deadline_ns=time.monotonic_ns()+60_000_000_000);archive_check(owner,case,first_export,'first-close',deadline_ns=time.monotonic_ns()+30_000_000_000,selected_closed=[first['journalGeneration']])
 owner.planned_native_rollover(deadline_ns=time.monotonic_ns()+25_000_000_000);command('NATIVE_ROLLOVER');journey=module.second(owner,case,check);device.command(['shell','am','force-stop',PACKAGE],deadline_ns=time.monotonic_ns()+10_000_000_000);device._cold_absence(time.monotonic_ns()+10_000_000_000)
 case['productSourceSeal']=command('SEAL_PRODUCT');native=case['native'].export_closed(case['resources'],deadline_ns=time.monotonic_ns()+60_000_000_000);archive_check(owner,case,native['export'],'final-close',deadline_ns=time.monotonic_ns()+30_000_000_000,selected_closed=[first['journalGeneration'],journey['second']['journalGeneration']]);case['nativeClosedDescriptor']=case['writer'].register_closed_native(case['native']);case['writer'].native_closed_inputs['archiveProofRef']=case['archiveProofRef17'];case['nativeCryptoProof']=command('VERIFY_NATIVE_UNUSED17')
 need(case['nativeCryptoProof']['verifiedSignedInputs']==0 and case['nativeCryptoProof']['matchedRootTransactions']==0,'NO_FAKE_INPUT_OR_FLIGHT_CREDIT');closure=owner.close_native_only();guardian=owner.close_guardian()
 owner.write('owner-terminal.json',{'format':'aeris-native17-owner-terminal','version':1,'status':'NATIVE_ONLY_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE','candidateSHA256':args.candidate_sha,'primaryFailure':None,'journeyStatus':journey['status'],'normalNativeClosureClaimed':True,'normalCompletedClosureClaimed':False,'APStarted':False,'flightAcceptance':False,'authorityRestored':False,'caseClosurePath':'reports/native17-case-closure.json','guardianClosurePath':'guardian/closure.json'},closing=True);print(json.dumps({'status':'NATIVE_ONLY_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE','evidence':str(owner.root)}))
except BaseException as primary:
 try:owner.revoke_failure_ingress()
 except BaseException as secondary:primary.add_note('NATIVE17_INGRESS_SECONDARY:'+str(secondary))
 if owner.budget is not None:
  try:owner.persist_owner_error(traceback.format_exc())
  except BaseException as storage:primary.add_note('NATIVE17_TRACE_UNDURABLE:'+str(storage))
  try:owner.fail_case(primary)
  except BaseException as cleanup:primary.add_note('NATIVE17_DISPOSAL_SECONDARY:'+str(cleanup))
 try:
  if not owner.closed:owner.close_guardian(failed=True)
 except BaseException as cleanup:primary.add_note('NATIVE17_GUARDIAN_SECONDARY:'+str(cleanup))
 print(json.dumps({'status':'FAILED_PRESERVED_NATIVE_ONLY_NOT_ACCEPTANCE','error':type(primary).__name__+':'+str(primary),'notes':getattr(primary,'__notes__',[])}));raise
