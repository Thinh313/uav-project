"""Read-only short gate. No30min claim or services; Root external anchors required."""
from pathlib import Path
from importlib import import_module
import hashlib,json,sys,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
H='planning.betaintegrated01.cockpit05-compact10.flight'
shared=import_module(H+'.actual_combined_cold');contract=import_module(H+'.contract')
from .confirmation import descriptor_sha256
from .native_authority import audit
from planning.betaintegrated01.m1cockpit04.qa.combined_oracle import assisted_window

def main():
 contract.verify_full_inputs();import_module(H+'.ledger').cold_caps(None);E=R/contract.EVIDENCE;B=E/'actual-short01';C=B/'control';O=E/'qa/short-cold01';O.mkdir(parents=True)
 read=lambda p:json.loads(Path(p).read_text())
 cfg=read(B/'raw/run-config.json');binding=read(C/'launch-binding.json');assert cfg['maximumSeconds']==180 and cfg['run']==binding['run']==contract.CASES['short']['run']
 contract.policy().validate_recording_policy(cfg);observerProof=import_module('planning.betaintegrated01.cockpit05-observer05.cold').verify_observer_capture(B/'raw',B/'AP-state',cfg);package=shared.installed_package_proof(C,binding)
 diagnostic=import_module(H+'.diagnostic').verify(C,{k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')})
 assert diagnostic.get('forensicOnly')is False,'FAILED_DIAGNOSTIC_CANNOT_QUALIFY_SHORT'
 A=read(C/'external-anchors.json');hostProfile=import_module(H+'.host_profile').verify(B/'raw',A,cfg);D=read(C/'native-confirmation-descriptor.json');DA=read(C/'native-confirmation-external-anchor.json');assert descriptor_sha256(D)==DA['canonicalSHA256']
 ap=shared.importlib.import_module(H+'.capture_external').last_receipt(C/'container-control-stdout.txt')
 base=import_module(H+'.oracles').verify_case_long(B/'raw',cfg['run'],cfg['epoch'],cfg['boot'],host_anchor=A['liveParentBackend']['commitAnchor'],AP_anchor=ap['terminalSHA256'],transport_anchor=A['liveParentBackend']['transportCommitAnchor'],scenario='nominal',native_confirmation=D,confirmedHomeReceiptAnchor=DA['canonicalSHA256'],clock_anchor=A['liveParentBackend']['clockCommitAnchor'],source_amendment=cfg['externalRecordingPolicy']['amendmentSHA256'],maximum_seconds=180)
 nativeContext={**binding,'expectedViewEpoch':json.loads((C/'staging-gate-before-AP.json').read_text())['workspace']['viewEpoch']}
 native=audit(D['nativeTarPath'],D['prefix'],D['nativeExternalAnchor'],nativeContext,scenario='nominal')
 samplerDiagnostic=import_module(H+'.diagnostic').verify_sampler_binding(C,native['dedicatedSampler'])
 start=read(C/'assisted-window-start.json')['hostNs'];end=read(C/'short-hold-finished.json')['hostNs'];window=assisted_window(base['wireAudit']['passiveTimeline'],start,end)
 observed=read(C/'short-hold-finished.json');assert min(observed[k]for k in('hostSeconds','guestSeconds','APSeconds'))>=5
 restart=shared.restart_workspace(C,D,binding,D['nativeExternalAnchor'],contract.SOURCE_SHA256,expected_status='NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION')
 guard=shared.power_guard(C,start,end)
 assert base['status']=='CONTROL_OBSERVATIONS_PASS'and native['status']=='PASS_STREAMED_NATIVE_AUTHORITY_CRC'and window['status']=='PASS'
 result={'status':'SHORT_PASS_CLOSED_RAW_ONLY','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'maximumSeconds':180,'actualThirtyMinuteAccepted':False,'wholeBetaAccepted':False,'clockOwnerVerifiedBySelectedHostReceiver':True,'base':base,'nativeAuthority':native,'assistedWindow':window,'restart':restart,'powerGuard':guard,'packageProof':package,'newR1PrivateFilesPreserved':True,'hostProfile':hostProfile,'observerProof':observerProof}
 with(O/'results.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'actualThirtyMinuteAccepted':False}))
if __name__=='__main__':main()
