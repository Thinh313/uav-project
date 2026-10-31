"""Read-only closed FAILED native recording audit, without invented Home receipts.

One selected new case only. Integrity PASS is never flight, cancellation, ground,
short or duration PASS. Original rows and receiver semantics stay mandatory.
"""
from pathlib import Path
from importlib import import_module
import json,re,sys
from . import contract
from .native_stream import closed_native
from .transactions import resolve_rows

CONTEXT=('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')

def _read(path,bound=262144):
 p=Path(path)
 if p.is_symlink()or not p.is_file()or not 1<=p.stat().st_size<=bound:raise ValueError('FAILED_RECORDING_METADATA_BOUND')
 return json.loads(p.read_bytes())

def validate_closed_failure(binding,outside,closure,location,case_root,case):
 if case not in('actual-short01','actual-combined01'):raise ValueError('NEW_SELECTED_CASE_REQUIRED')
 expected=contract.CASES['short'if case=='actual-short01'else'long']['run']
 if type(binding)is not dict or any(k not in binding for k in CONTEXT)or binding['run']!=expected:raise ValueError('FAILED_RECORDING_BINDING_CONTEXT')
 context={k:binding[k]for k in CONTEXT};journal=outside.get('journal',{});authority=outside.get('input',{})
 if any(outside.get(k)!=context[k]for k in('run','epoch','boot','generation'))or outside.get('closed')is not True or journal.get('closed')is not True or outside.get('authorityRestorable')is not False or authority.get('consent')is not False or authority.get('leaseId')is not None:raise ValueError('FAILED_RECORDING_CLOSED_REVOKED_OUTSIDE_PROOF_REQUIRED')
 if outside.get('firstFailure')is not None and type(outside.get('firstFailure'))is not str or type(closure.get('failure'))is not str or not closure['failure']:raise ValueError('FAILED_RECORDING_NOT_A_SUCCESS_PATH')
 anchor=journal.get('commitAnchor')
 if type(anchor)is not str or re.fullmatch('[a-f0-9]{64}',anchor)is None:raise ValueError('FAILED_RECORDING_OUTSIDE_ANCHOR')
 tar=Path(location.get('path',''));expected_tar=Path(case_root)/'native-private.tar'
 if tar.is_symlink()or tar.resolve()!=expected_tar.resolve()or not tar.is_file()or not 1<=tar.stat().st_size<=168*2**20 or contract.sha(tar)!=location.get('sha256'):raise ValueError('FAILED_RECORDING_EXPORT_PATH_SHA_OR_BOUND')
 return context,tar,anchor

def inspect(case='actual-short01'):
 contract.verify_full_inputs();root=contract.E/case/'control'
 binding=_read(root/'launch-binding.json');outside=_read(root/'native-last-external-observation.json');closure=_read(root/'closure.json');location=_read(root/'native-export-location.json')
 context,tar,anchor=validate_closed_failure(binding,outside,closure,location,root,case)
 receiver=import_module(contract.NAMESPACE+'.receiver05');receiver.selected_context(context);package=_read(root/'installed-package-observation.json');receiver.package_observation(package,context)
 selected=receiver.verify_selected_run(tar,'files/control-runs/'+context['run']+'/',anchor,context,packageObservation=package)
 if selected['status']!='CLOSED_FAILED_NATIVE_FORENSICS_ONLY':raise ValueError('CLOSED_FAILED_NATIVE_RECORDING_REQUIRED')
 native,rows=closed_native(tar,'files/control-runs/'+context['run']+'/',anchor);transactions={}
 for _ in resolve_rows(rows,context,transactions):pass
 if native.get('forensicOnly')is not True:raise ValueError('FAILED_NATIVE_RAW_FAILURE_REQUIRED')
 home_present=(root/'confirm-home-bracket.json').is_file()
 return dict(status='CLOSED_FAILED_RECORDING_INTEGRITY_ONLY_NOT_SHORT_OR_FLIGHT_ACCEPTANCE',context=context,native=native,transactions=transactions,selectedPackage=selected,outsideClosedProofSHA256=contract.sha(root/'native-last-external-observation.json'),closureSHA256=contract.sha(root/'closure.json'),nativeTarSHA256=contract.sha(tar),HomeBracketPresent=home_present,HomeConfirmationQualified=False,HomeDescriptorFabricated=False,requiresPreSocketRefusal=False,flightOrGroundAccepted=False,cancellationAccepted=False,shortAccepted=False,thirtyMinuteAccepted=False,noSourceOrRawWrites=True,scope='SHA_BOUND_CLOSED_FAILED_LOCAL_NATIVE_RECORDING;HOST_MODEL_AP_CLOCK_GEOGRAPHY_AND_DEVICE_RESTART_REQUIRE_SEPARATE_INDEPENDENT_AUDITS')

if __name__=='__main__':print(json.dumps(inspect(sys.argv[1]if len(sys.argv)>1 else'actual-short01'),indent=2))
