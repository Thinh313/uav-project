"""Read-only exact old accepted raw through selected long receiver; no raw copy."""
from pathlib import Path
import hashlib,json,resource,time
from pilot.betaintegrated01.cockpit04.oracles import verify_case_long
ROOT=Path(__file__).resolve().parents[4]
def main():
 out=ROOT/'evidence/betaintegrated01-m1cockpit04/host/regression01';out.mkdir(exist_ok=False)
 rows=[]
 for case,scenario in [('actual-loss05','loss'),('actual-ground206','ground-recovery')]:
  start=time.monotonic();base=ROOT/'evidence/betaintegrated01-m1control01'/case
  anchors=json.loads((base/'control/external-anchors.json').read_text());ctx=json.loads((base/'control/launch-binding.json').read_text())
  kwargs={}
  if scenario=='loss':
   from pilot.betaintegrated01.cockpit04.confirmation import descriptor_sha256
   d=json.loads((ROOT/'evidence/betaintegrated01-m1control02/host/old-regression04/derived-loss05-confirmation-descriptor.json').read_text());kwargs={'native_confirmation':d,'confirmedHomeReceiptAnchor':descriptor_sha256(d)}
  result=verify_case_long(base/'raw',ctx['run'],ctx['epoch'],ctx['boot'],host_anchor=anchors['liveParentBackend']['commitAnchor'],AP_anchor=anchors['liveParentAP']['terminalSHA256'],transport_anchor=anchors['liveParentBackend']['transportCommitAnchor'],scenario=scenario,**kwargs)
  target=out/(case+'.json');target.write_text(json.dumps(result,indent=2)+'\n')
  old=json.loads((ROOT/'evidence/betaintegrated01-m1control02/host/old-regression04'/(case+'-new-oracle.json')).read_text())
  compare={k:result[k]==old[k]for k in ('status','fullFrameModelAP','control','geography','confirmedHome','nominalRelease','wireAudit')}
  # New native reader report summarizes arrays; confirmation only carries same integrity marker.
  assert all(compare.values()),compare
  rows.append({'case':case,'status':result['status'],'exactComparedFields':compare,'seconds':time.monotonic()-start,'receiptSHA256':hashlib.sha256(target.read_bytes()).hexdigest()})
  (out/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
 report={'status':'PASS','cases':rows,'rawCopies':0,'servicesStarted':0,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
