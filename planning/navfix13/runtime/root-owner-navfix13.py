#!/usr/bin/env python3
"""Autonomous short-only180s product workload owner. Source-held driver only.
Root invokes after independent source/native gates. No interactive wait or retry.
The scenario drives public Android UI; private control only enrolls/seals evidence.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,signal,sys,time,traceback
P=argparse.ArgumentParser();P.add_argument('--candidate',required=True);P.add_argument('--candidate-sha',required=True);P.add_argument('--spec',required=True);P.add_argument('--image',required=True);P.add_argument('--node',required=True);P.add_argument('--scenario',required=True);P.add_argument('--seconds',type=int,choices=(180,),default=180);P.add_argument('--run',required=True);P.add_argument('--campaign-slot',required=True,choices=('s01','s02'));P.add_argument('--accepted-short');P.add_argument('--accepted-short-sha');P.add_argument('--inspect',action='store_true');args=P.parse_args()
REPO=Path(__file__).resolve().parents[3];CANDIDATE=Path(args.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(REPO),AERIS_CANDIDATE_DIR=str(CANDIDATE),AERIS_CANDIDATE_SHA256=args.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(CANDIDATE/'source'),str(REPO)]
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.product_inputs import validate
from aeris_runtime.candidate import load
from aeris_runtime.metadata_budget import encoded
from aeris_runtime.product_seal import verify_product_seal

def need(v,n):
 if not v:raise RuntimeError('ROOT_OWNER_'+n)
def verify_diagnostic_disposal(owner,disposal,sentinel):
 need(not getattr(sentinel,'__notes__',[]),'DIAGNOSTIC_DISPOSAL_UNDURABLE_NOTES')
 need(owner.closed is True and disposal.get('status')=='FAILED_PHYSICAL_DISPOSAL_RECORDED_NOT_ACCEPTANCE'and disposal.get('secondaryErrors')==[],'DIAGNOSTIC_DISPOSAL_OR_GUARDIAN_NOT_CLOSED')
 def receipt(relative,maximum):
  path=owner.root/relative
  need(path.is_file()and not path.is_symlink()and path.stat().st_size<=maximum,'DIAGNOSTIC_DISPOSAL_RECEIPT_BOUND:'+relative)
  raw=path.read_bytes();need(len(raw)<=maximum,'DIAGNOSTIC_DISPOSAL_RECEIPT_GROWTH:'+relative)
  return json.loads(raw)
 terminal=receipt('reports/owner-terminal.json',4096)
 need(terminal.get('candidateSHA256')==owner.digest and terminal.get('primaryFailure')==str(sentinel)and terminal.get('status')==disposal['status']and terminal.get('secondaryErrors')==[]and terminal.get('guardianCause')is None and terminal.get('normalCompletedClosureClaimed')is False and terminal.get('flightAcceptance')is False,'DIAGNOSTIC_ORIGINAL_TERMINAL_BINDING')
 required={'writer-revoke-ingress','stop-command-producer','command-producer-EOF','interval-close','writer-close','simulator-physical-disposal','native-observer-close','resource-monitor-close','guardian-exceptional-disposal'}
 steps=terminal.get('cleanupSteps',[]);need(type(steps)is list and all(type(v)is dict and v.get('returned')is True for v in steps)and required.issubset({v.get('name')for v in steps}),'DIAGNOSTIC_ORIGINAL_CLEANUP_STEPS')
 ref=terminal.get('finalOriginalUIRef')or{};need(ref.get('path')=='reports/ui-failure-final.json'and type(ref.get('bytes'))is int and 0<ref['bytes']<=32768,'DIAGNOSTIC_FINAL_UI_REFERENCE')
 ui=owner.root/ref['path'];need(ui.is_file()and not ui.is_symlink()and ui.stat().st_size==ref['bytes']and hashlib.sha256(ui.read_bytes()).hexdigest()==ref.get('sha256'),'DIAGNOSTIC_FINAL_UI_DURABILITY')
 guardian=receipt('guardian/closure.json',262144);health=guardian.get('health')or{};audit=health.get('audit')or{}
 need(guardian.get('exit')==0 and guardian.get('failure')=='RuntimeError:SIMULATOR_FAILED_PHYSICAL_DISPOSAL_NOT_ACCEPTANCE'and guardian.get('exceptionalPhysicalDisposal')is True and guardian.get('cleanupNotes')==[]and guardian.get('flightCommands')==0 and guardian.get('flightAcceptance')is False and health.get('failure')is None and health.get('durablyDrained')is True and audit.get('durablyDrained')is True and audit.get('pendingRows')==0 and type(audit.get('producedSeq'))is int and audit['producedSeq']==audit.get('committedSeq'),'DIAGNOSTIC_GUARDIAN_CLOSURE_NOT_CLEAN')
 child=receipt('diagnostics/guardian-process/close.json',4096);need(child.get('pid')==owner.guardian.process.pid and child.get('exit')==1 and owner.guardian.process.poll()==1,'DIAGNOSTIC_EXCEPTIONAL_GUARDIAN_PROCESS_BINDING')
 capture=child.get('capture')or{};need(set(capture)=={'stdout','stderr'}and all(v.get('captureComplete')is True and v.get('failure')is None for v in capture.values()),'DIAGNOSTIC_GUARDIAN_PIPE_CAPTURE_INCOMPLETE')
 return {'status':'ORIGINAL_EXCEPTIONAL_DISPOSAL_RECEIPTS_OBSERVED_NOT_FLIGHT_ACCEPTANCE','flightAcceptance':False,'guardianExceptionalProcessExit':1}

manifest=load(CANDIDATE,args.candidate_sha);graph=validate(manifest['productInputClosure']);scenario=Path(args.scenario).resolve();need(scenario.is_relative_to(REPO),'SCENARIO_INSIDE_SOURCE_GRAPH');relative=str(scenario.relative_to(REPO));need(graph['pins'].get(relative)==hashlib.sha256(scenario.read_bytes()).hexdigest(),'EXACT_SOURCE_HELD_PUBLIC_UI_SCENARIO');need(Path(args.node).is_absolute()and Path(args.node).is_file(),'EXACT_NODE_EXECUTABLE')
if args.seconds==760:
 need(args.accepted_short and args.accepted_short_sha,'INDEPENDENT_SHORT_REQUIRED_BEFORE_TEN');proof_path=Path(args.accepted_short).resolve();need(proof_path.is_relative_to(REPO/'evidence/betasim-integrated01')and proof_path.is_file(),'SHORT_PROOF_CURRENT_MILESTONE');proof_raw=proof_path.read_bytes();need(hashlib.sha256(proof_raw).hexdigest()==args.accepted_short_sha,'SHORT_PROOF_EXACT_ORIGINAL_BYTES');proof=json.loads(proof_raw);need(proof.get('format')=='aeris-independent-betasim-short-acceptance'and proof.get('status')=='PASSED_INDEPENDENT_ANDROID_SITL_SHORT_SAME_RELEASE'and proof.get('candidateSHA256')==args.candidate_sha and proof.get('profileId')=='WORKBENCH_SIM_V1'and proof.get('simulationOnly')is True and proof.get('originalEvidence'),'INDEPENDENT_SHORT_SOURCE_CONFIG');
 for ref in proof['originalEvidence']:
  path=(REPO/ref['path']).resolve();need(path.is_relative_to(REPO/'evidence/betasim-integrated01')and path.is_file()and hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256'],'SHORT_ORIGINAL_EVIDENCE_STILL_PRESENT')
if args.inspect:
 print(json.dumps({'status':'SOURCE_GRAPH_VALIDATED_NO_ACTORS','candidateSHA256':args.candidate_sha,'scenario':relative,'provider':'WORKBENCH_SIM_V1','sourceGateStillRequired':True}));raise SystemExit(0)
owner=WorkbenchRuntime(CANDIDATE,args.candidate_sha,evidence=REPO/'evidence/navfix13'/args.campaign_slot,planning=REPO/'planning/navfix13',spec=args.spec);
from aeris_runtime.preview10 import preview
preflight=preview(CANDIDATE,args.candidate_sha,owner.root,owner.planning,Path(args.spec))
need(preflight['metadataAdmitted']and preflight['artifactAdmitted']and preflight['diskAdmitted'],'PURE_ADMISSION_PREVIEW_REFUSED_NO_SLOT_CREATED')
owner.root.mkdir(exist_ok=False);stopped=False;diagnostic_disposal=None

def stop(sig,frame):
 global stopped
 stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
def check():
 need(not stopped,'TERMINATION_REQUEST');owner.check()
def command(action):
 need(action in('NATIVE_READY','NATIVE_ROLLOVER','SEAL_PRODUCT','VERIFY_NATIVE_INPUTS','PREPARE_RAW_EXPORT','STATUS'),'PRIVATE_MANAGEMENT_ALLOWLIST');c=owner.case;c.setdefault('managementSequence',0);c['managementSequence']+=1;n=c['managementSequence'];row={'sequence':n,'ownerPID':os.getpid(),'run':c['context']['run'],'candidateSHA256':args.candidate_sha,'action':action};path=owner.root/'reports'/('companion-control-'+c['context']['run']+'.jsonl');owner.budget.append_json('external_task',path,row,maximum=2048)
 return wait_progress('COMMAND_COMPLETE',lambda v:v.get('sequence')==n,timeout=20)
def wait_progress(kind,predicate=lambda v:True,*,timeout=30):
 end=time.monotonic()+timeout;path=owner.case['root']/'product/reports/companion-progress.jsonl'
 while time.monotonic()<end:
  check()
  if path.exists():
   raw=path.read_bytes();need(len(raw)<=1024*1024 and raw.endswith(b'\n'),'COMPANION_PROGRESS_ORIGINAL_BOUND')
   for line in raw.splitlines():
    row=json.loads(line);need(row['pid']==owner.case['companion'].process.pid and row['run']==owner.case['context']['run'],'GENUINE_OWNED_COMPANION_PROGRESS')
    if row['kind']=='FAILED':raise RuntimeError('COMPANION_FAILED:'+str(row['data']))
    if row['kind']==kind and predicate(row['data']):return row
  time.sleep(.05)
 raise TimeoutError('ROOT_OWNER_FINITE_WAIT_'+kind)
try:
 owner.bootstrap();case=owner.create_case(args.run,seconds=args.seconds);descriptor=owner.start_writer();descriptor_path=owner.root/'reports/product-descriptor-01.json';case['device'].live_check=check;ready=case['device'].wait_owned_ready(deadline_ns=time.monotonic_ns()+60_000_000_000);owner.event('ANDROID_OS_READY',{'readinessRef':ready,'APStarted':False});case['device'].prepare_content_reader(deadline_ns=time.monotonic_ns()+30_000_000_000);case['native'].install_selected(CANDIDATE,args.candidate_sha,deadline_ns=time.monotonic_ns()+120_000_000_000)
 argv=[args.node,'--import',str(REPO/'planning/navfix13/runtime/verified-loader.mjs'),str(REPO/'planning/navfix13/runtime/product-companion-codec09.mjs'),'--manifest',str(CANDIDATE/'candidate.json'),'--candidate-sha',args.candidate_sha,'--descriptor',str(descriptor_path),'--owner-pid',str(os.getpid()),'--maximum-seconds',str(min(1800,args.seconds+360))];owner.start_companion(argv);wait_progress('READY',timeout=45)
 device=case['device'];case['createdReverses']=[];current=device.command(['reverse','--list'],deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=4096).decode().splitlines()
 for port in(8895,8896):
  expected='tcp:'+str(port);matches=[r.split()for r in current if expected in r.split()]
  if matches:need(all(r[-2:]==[expected,expected]for r in matches),'EXISTING_REVERSE_WRONG_TARGET')
  else:device.command(['reverse','--no-rebind',expected,expected],deadline_ns=time.monotonic_ns()+10_000_000_000,maximum_bytes=4096);case['createdReverses'].append(port)
 case['native'].start(deadline_ns=time.monotonic_ns()+20_000_000_000);case['writer'].register_native_probe(case['native']);command('NATIVE_READY');owner.start_resources(args.image);owner.event('ANDROID_UI_WORKLOAD_READY',{'URL':'http://127.0.0.1:8896','scenario':relative,'readOnlyRootManagementNoFlightCommands':True})
 case['managementCommand']=command
 spec=importlib.util.spec_from_file_location('source_held_public_ui_scenario',scenario);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=module.run(owner,case,check)
 need(type(result)is dict and result.get('status')=='DISARMED_ANDROID_NAVIGATION_OBSERVED_READY_NOT_FLIGHT_ACCEPTANCE'and result.get('manualIntervention')is False and result.get('flightAcceptance')is False and result.get('recordingAccepted')is False,'EXACT_READONLY_DIAGNOSTIC_RESULT')
 owner.write('navigation-diagnostic-result.json',result)
 # Aread-only probe deliberately has no completedflight record toseal. Keep
 # originalexceptional revocation/physicaldisposal, itsincomplete journaland
 # originalowner-terminal unchanged. Observation isreportedseparately.
 sentinel=RuntimeError('READ_ONLY_DIAGNOSTIC_COMPLETE_REQUESTED_PHYSICAL_DISPOSAL_NOT_FLIGHT_ACCEPTANCE')
 owner.revoke_failure_ingress();disposal=owner.fail_case(sentinel);diagnostic_disposal=disposal
 verify_diagnostic_disposal(owner,disposal,sentinel)
 print(json.dumps({'status':'DISARMED_NAVIGATION_OBSERVED_AND_PHYSICALLY_DISPOSED_NOT_FLIGHT_ACCEPTANCE','evidence':str(owner.root),'recordingAccepted':False,'originalExceptionalTerminalRetained':True}))
except BaseException as primary:
 try:owner.revoke_failure_ingress()
 except BaseException as secondary:primary.add_note('INGRESS_REVOKE_SECONDARY:'+type(secondary).__name__+':'+str(secondary)[:160])
 if owner.budget is not None:
  try:owner.persist_owner_error(traceback.format_exc())
  except BaseException as storage:primary.add_note('OWNER_TRACE_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:256])
  try:
   if diagnostic_disposal is None:owner.fail_case(primary)
  except BaseException as cleanup:primary.add_note('FAILURE_DISPOSAL_SECONDARY:'+str(cleanup))
 try:
  if not owner.closed:owner.close_guardian(failed=True)
 except BaseException as cleanup:primary.add_note('GUARDIAN_DISPOSAL_SECONDARY:'+str(cleanup))
 from aeris_runtime.guardian_cause11 import diagnostic
 print(json.dumps({'status':'FAILED_PRESERVED_NOT_ACCEPTANCE','guardianCause':diagnostic(primary),'error':type(primary).__name__+':'+str(primary),'notes':getattr(primary,'__notes__',[])}));raise
