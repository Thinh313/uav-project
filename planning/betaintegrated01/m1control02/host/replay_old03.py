"""New derived receipts from closed immutable old runs; never rewrites old outcomes."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control04.confirmation import create_confirmation_descriptor
from pilot.betaintegrated01.control04.oracles import verify_case

def main():
 out=R/'evidence/betaintegrated01-m1control02/host/old-regression03';out.mkdir()
 sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'pilot/betaintegrated01/control04').glob('*.py')}
 results=[]
 for name,scenario in [('actual-loss05','loss'),('actual-ground206','ground-recovery')]:
  old=R/'evidence/betaintegrated01-m1control01'/name;control=old/'control';anchors=json.loads((control/'external-anchors.json').read_text());binding=json.loads((control/'launch-binding.json').read_text())
  receipt=receiptsha=None
  if scenario=='loss':
   bracket={'beforeActionHostNs':66645095624833,'afterObservedConfirmedHostNs':66645334291125,**{k:binding[k]for k in('run','epoch','boot','generation')},'displayedHomeHash':'a66911aa3deecb32a22694967589fd9dfe1dd599915d33ffce8897b29f35207f'}
   native_path=json.loads((control/'native-export-location.json').read_text())['path']
   receipt,receiptsha=create_confirmation_descriptor(native_path,'files/control-runs/m1control-loss05/',anchors['nativeClosedCheckpoint']['journal']['commitAnchor'],bracket,{k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')})
   (out/'derived-loss05-confirmation-descriptor.json').open('x').write(json.dumps(receipt,indent=2)+'\n')
   provenance={'classification':'RECONSTRUCTED_FROM_EXISTING_ROOT_OBSERVATION_BOUND_AND_SEALED_DRIVER_ORDER_NOT_EXACT_CALL_START','rootConfirmedLogicalOrder':'last pending/false observation -> explicit_tap(confirm-home) -> first confirmed/true observation','canonicalDescriptorSHA256':receiptsha,'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[control/'native-live-states.jsonl',R/'planning/betaintegrated01/m1control01/actual05.py',control/'external-anchors.json',control/'launch-binding.json']},'oldRawOrReceiptsEdited':False,'notNewLiveAttestation':True}
   (out/'derived-loss05-confirmation-provenance.json').open('x').write(json.dumps(provenance,indent=2)+'\n')
  v=verify_case(old/'raw',binding['run'],binding['epoch'],binding['boot'],host_anchor=anchors['liveParentBackend']['commitAnchor'],AP_anchor=anchors['liveParentAP']['terminalSHA256'],transport_anchor=anchors['liveParentBackend']['transportCommitAnchor'],scenario=scenario,native_confirmation=receipt,confirmedHomeReceiptAnchor=receiptsha)
  (out/(name+'-new-oracle.json')).open('x').write(json.dumps(v,indent=2)+'\n')
  results.append({'case':name,'newOracleStatus':v['status'],'geographyStatus':v['geography']['status'],'failedCriteria':[k for k,vv in v['control']['criteria'].items()if not vv],'oldReceiptEdited':False,'canonicalConfirmationSHA256':receiptsha})
 assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==sha for p,sha in sources.items()),'ORACLE_SOURCE_DRIFT'
 (out/'source-before-after.json').open('x').write(json.dumps({'sourceSHA256':sources,'unchanged':True},indent=2)+'\n')
 (out/'results.json').open('x').write(json.dumps({'status':'NEW_RECEIPTS_WRITTEN_OLD_UNCHANGED','cases':results,'servicesStarted':0,'APStarts':0},indent=2)+'\n');print(json.dumps(results))
if __name__=='__main__':main()
