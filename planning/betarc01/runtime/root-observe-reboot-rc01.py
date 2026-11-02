#!/usr/bin/env python3
"""Root-owned separate read-only new AP context after original failed drain."""
from pathlib import Path
import argparse,hashlib,json,os,signal,sys,time,traceback
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--candidate-sha',required=True);p.add_argument('--spec',required=True);p.add_argument('--image',required=True);p.add_argument('--run',required=True);p.add_argument('--campaign-slot',choices=('r301','r302'),required=True);p.add_argument('--old-fault',required=True);p.add_argument('--old-fault-sha',required=True);p.add_argument('--inspect',action='store_true');a=p.parse_args();R=Path(__file__).resolve().parents[3];candidate=Path(a.candidate).resolve();os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(candidate),AERIS_CANDIDATE_SHA256=a.candidate_sha,PYTHONDONTWRITEBYTECODE='1');sys.path[:0]=[str(candidate/'source'),str(R)]
from aeris_runtime.candidate import load
from aeris_runtime.entry import module_origin_receipt
from aeris_runtime.product_inputs import validate
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.preview10 import preview
from aeris_runtime.reboot_rc01 import old_fault,start_probe,observe_probe,check_probe
from aeris_runtime.rc01 import need
m=load(candidate,a.candidate_sha);module_origin_receipt(candidate);graph=validate(m['productInputClosure']);entry=Path(__file__).resolve();need(graph['pins'].get(str(entry.relative_to(R)))==hashlib.sha256(entry.read_bytes()).hexdigest(),'READONLY_EXACT_HELD_ENTRY');forecast=preview(candidate,a.candidate_sha,R/'evidence/betarc01'/a.campaign_slot,R/'planning/betarc01',Path(a.spec),seconds=180);need(all(forecast[k]for k in('metadataAdmitted','artifactAdmitted','diskAdmitted')),'READONLY_FRESH_ADMISSION')
if a.inspect:print(json.dumps({'status':'READONLY_SOURCE_INSPECTED_NO_ACTORS','forecast':forecast,'actualBootObservationAccepted':False}));raise SystemExit(0)
prior=old_fault(a.old_fault,a.old_fault_sha,m,a.candidate_sha);owner=WorkbenchRuntime(candidate,a.candidate_sha,evidence=R/'evidence/betarc01'/a.campaign_slot,planning=R/'planning/betarc01',spec=a.spec,seconds=180);owner.root.mkdir(exist_ok=False);stopped=False
class ProbeDiagnosticComplete(RuntimeError):pass
def stop(sig,frame):
 global stopped
 stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
 owner.bootstrap();case=owner.create_case(a.run,seconds=180);need(not stopped,'READONLY_TERMINATED');start_probe(owner,a.image,prior,a.old_fault_sha);observation=observe_probe(owner,prior);need(not stopped,'READONLY_TERMINATED');owner.write('read-only-probe-observed-before-close.json',{'status':'ACTUAL_NEW_CONTEXT_CRC_BOOT_OBSERVED_AWAITING_INDEPENDENT_COLD_REPLAY','observation':observation,'nativeActivityStarted':False,'flightAcceptance':False});raise ProbeDiagnosticComplete('READ_ONLY_NEW_AP_BOOT_OBSERVATION_COMPLETE_NOT_FLIGHT')
except BaseException as error:
 try:owner.revoke_failure_ingress()
 except BaseException as secondary:error.add_note('PROBE_REVOKE_SECONDARY:'+str(secondary))
 if owner.budget is not None:
  try:owner.persist_owner_error(traceback.format_exc())
  except BaseException as secondary:error.add_note('PROBE_TRACE_SECONDARY:'+str(secondary))
  try:owner.fail_case(error)
  except BaseException as secondary:error.add_note('PROBE_DISPOSAL_SECONDARY:'+str(secondary))
 try:
  if not owner.closed:owner.close_guardian(failed=True)
 except BaseException as secondary:error.add_note('PROBE_GUARDIAN_SECONDARY:'+str(secondary))
 print(json.dumps({'status':'READ_ONLY_PROBE_DIAGNOSTIC_CLOSED_NOT_FLIGHT_ACCEPTANCE'if isinstance(error,ProbeDiagnosticComplete)else'READ_ONLY_PROBE_FAILED_PRESERVED','error':str(error),'notes':getattr(error,'__notes__',[]),'requiresIndependentOldNewRawClockReplay':True}));raise SystemExit(0 if isinstance(error,ProbeDiagnosticComplete)else 1)
