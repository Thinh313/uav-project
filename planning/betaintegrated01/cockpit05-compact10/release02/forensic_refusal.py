"""Closed FAILED forensic reader. Never a successful short/flight/ground oracle."""
from pathlib import Path
from importlib import import_module
import json,sys
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-compact10.release02'

def inspect(case='actual-short01'):
 C=import_module(H+'.contract');C.verify_full_inputs();root=R/C.EVIDENCE/case/'control';read=lambda n:json.loads((root/n).read_text());binding=read('launch-binding.json');ctx={k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')}
 receiver=import_module(H+'.receiver05');receiver.selected_context(ctx);package=read('installed-package-observation.json');receiver.package_observation(package,ctx)
 outside=read('native-last-external-observation.json');j=outside.get('journal',{})
 if outside.get('closed')is not True or j.get('closed')is not True or outside.get('authorityRestorable')is not False or outside.get('input',{}).get('consent')is not False or outside.get('input',{}).get('leaseId')is not None or any(outside.get(k)!=ctx[k]for k in('run','epoch','boot','generation')):raise ValueError('ACTUAL_OUTSIDE_FAILED_CLOSED_ANCHOR_REQUIRED')
 location=read('native-export-location.json');tar=Path(location['path'])
 if C.sha(tar)!=location['sha256']:raise ValueError('FORENSIC_NATIVE_EXPORT_SHA')
 result=receiver.verify_selected_run(tar,'files/control-runs/'+ctx['run']+'/',j['commitAnchor'],ctx,packageObservation=package)
 if result['status']!='CLOSED_FAILED_NATIVE_FORENSICS_ONLY' or not result['preSocketRefusals']:raise ValueError('FORENSIC_SPECIFIC_KNOWN_REFUSAL_REQUIRED')
 return {'status':'CLOSED_FAILED_PRE_SOCKET_REFUSAL_FORENSICS_ONLY','native':result,'outsideClosedProofSHA256':C.sha(root/'native-last-external-observation.json'),'APK_SHA256':C.APK_SHA256,'sourceSHA256':C.SOURCE_SHA256,'healthyClosedFailedJournalObserved':True,'socketCallbackNotEntered':'SOURCE_BOUND_DURABLE_DISPOSITION_NOT_PHYSICAL_REMOTE_ATTESTATION','flightOrGroundOrShortPass':False,'thirtyMinuteAcceptance':False,'failedRawFromEarlierPackagesRewritten':False}
if __name__=='__main__':print(json.dumps(inspect(sys.argv[1]if len(sys.argv)>1 else'actual-short01'),indent=2))
