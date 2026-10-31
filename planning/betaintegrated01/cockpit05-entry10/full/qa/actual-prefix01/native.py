from pathlib import Path
from importlib import import_module
import hashlib,json,sys,tarfile,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[6];sys.path.insert(0,str(R));E=R/'evidence/betaintegrated01-cockpit05-entry10-flight';C=E/'actual-combined01/control';A=R/'evidence/betaintegrated01-cockpit05-closure01/native-private02.tar';P='files/control-runs/cockpit05-entry10-combined-01/';O=E/'qa/actual-prefix01';began=time.monotonic()
receipt=json.loads((A.parent/'native-export02-receipt.json').read_text());source=import_module('pilot.betaintegrated01.cockpit04.revision02.native_stream').IndexedNative(A,P);anchor=hashlib.sha256(source.read('session.json')).hexdigest();binding=json.loads((C/'launch-binding.json').read_text());auth=import_module('planning.betaintegrated01.m1cockpit04.qa.native_authority02')
try:
 result=auth.audit(str(A),P,anchor,binding,scenario='INCOMPLETE_HOST_CASE_NO_INTENTIONAL_CUT')
 result.update(status='INTERNAL_NATIVE_CHAIN_AUTHORITY_CHECKED_UNATTESTED_BY_EXTERNAL_CLOSED_ANCHOR',anchorProvenance='SHA_SESSION_DERIVED_FROM_IMPORTED_BYTES_NOT_EXTERNAL_ATTESTATION',derivedSessionSHA256=anchor,archiveSHA256=source.tar_sha,archiveBytes=A.stat().st_size,archiveReceiptSHA256=hashlib.sha256((A.parent/'native-export02-receipt.json').read_bytes()).hexdigest(),coldAllRows=result['records'],externallyClosedNativeAnchorObserved=False,actualThirtyMinuteAccepted=False,wholeBetaAccepted=False,durationSeconds=time.monotonic()-began)
 (O/'native-internal.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in['status','records','inputs','secondLeaseProducerWindowNs','secondLeaseUptimeWindowNs','maxLease2ProducerGapNs','durationSeconds']}))
except BaseException as e:
 (O/'native-internal-failure.json').open('x').write(json.dumps({'status':'NATIVE_COLD_FAILURE_RETAINED_NO_ACCEPTANCE','error':repr(e),'derivedSessionSHA256':anchor,'anchorDerivedNotExternal':True,'archiveSHA256':source.tar_sha,'durationSeconds':time.monotonic()-began},indent=2)+'\n');raise
