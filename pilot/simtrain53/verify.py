"""Final preservation, source/evidence byte and scope checks; no simulator launch."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/simtrain53'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 baseline=json.loads((E/'preservation-before.json').read_text());changed=[{'path':p,'expected':h,'actual':sha(R/p)if(R/p).is_file()else None}for p,h in baseline['files'].items()if not(R/p).is_file()or sha(R/p)!=h]
 spec=importlib.util.spec_from_file_location('frozen_guard53',R/'pilot/apstream40/guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 same=guard.endure()==baseline['endurePaths'];run_rows=[];total=0
 for out in sorted((E/'runs').iterdir()):
  if not out.is_dir():continue
  r=json.loads((out/'readback.json').read_text());assert r['status']=='PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION'
  mismatches=[name for name,h in r['filesSha256'].items()if sha(out/name)!=h];assert not mismatches,(out.name,mismatches)
  c=json.loads((out/'closure.json').read_text());assert c['backendExited'] and c['ownedContainerStopped'] and c['error']is None
  run_rows.append({'run':out.name,'profile':r['profile'],'frames':r['frames'],'RTF':r['activeReceiveRTF'],'gapP95Ms':r['hostReceiveGapsMs']['p95'],'gapP99Ms':r['hostReceiveGapsMs']['p99'],'gapMaxMs':r['hostReceiveGapsMs']['max'],'windowMinRTF':min(w['RTF']for w in r['fiveSecondWindows']),'observedTakeoffManualLand':r['takeoffAndLandPhysicalObservations']});total+=r['frames']
 assert len(run_rows)==4 and sum(r['observedTakeoffManualLand']for r in run_rows)==3
 flows=[]
 for i in [2,3,4]:
  j=json.loads((E/f'browser{i}/receipt.json').read_text());assert j['status']=='PASS_SCOPED_CLOSED_LOOP_NOT_FULL_G1'and all(c['pass']for c in j['checks']);flows.append({'browser':i,'run':j['run'],'checks':len(j['checks'])})
 failed=json.loads((E/'browser1/failure.json').read_text());assert failed['status']=='FAIL'
 contracts=json.loads((E/'contracts1.json').read_text());handoff=json.loads((E/'handoff1/receipt.json').read_text());rejected=json.loads((E/'rejected-rx1.json').read_text());finalizer=json.loads((E/'finalizer1.json').read_text());visual=json.loads((E/'visual-final1/receipt.json').read_text())
 assert contracts['checks']==20 and all(c['pass']for c in contracts['results'])
 assert all(c['pass']for c in handoff['checks']) and all(c['pass']for c in rejected['checks'])
 assert finalizer['status']=='PASS_SCOPED_SKIP_AND_FAILURE_ONLY' and visual['status']=='PASS_FINAL_STATIC_LAYOUT_ONLY'
 allocated=sum(p.stat().st_blocks*512 for d in [R/'pilot/simtrain53',E]for p in d.rglob('*')if p.is_file());free=shutil.disk_usage(R).free
 passed=not changed and same and free>=20*2**30 and allocated<4*2**30
 report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SCOPED_BYTE_PRESERVATION_PRODUCT_PARTIAL'if passed else'FAIL','protectedCount':len(baseline['files']),'changed':changed,'endurePathSetUnchanged':same,'endurePathCount':len(guard.endure()),'runs':run_rows,'originalSensorAndAuxFramesReplayed':total,'scopedFlowPasses':flows,'retainedFailedPreflightAttempts':1,'contractChecks':20,'handoffPolicyHistoryMockUIChecks':len(handoff['checks']),'mockRejectedDatagramChecks':len(rejected['checks']),'allocatedBytes':allocated,'budgetBytes':4*2**30,'freeBytes':free,'floorBytes':20*2**30,'fullG1Accepted':False,'sourceAfterPhysicalMatrix':'Rejected-RX fault branch, history/quota/review finalizer and immediate local input-clear before LAND changed after last physical matrix; focused mock/static tests, no fifth SITL regression','nativeProjectorPerformanceAccepted':False,'heraCalibrated':False,'newSignature':False,'independentReview':False}
 with(E/'verification1.json').open('x')as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items()if k not in['runs','changed','scopedFlowPasses']}));assert passed,changed[:5]
if __name__=='__main__':main()
