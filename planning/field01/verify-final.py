"""Independent arithmetic/byte checks of selected host evidence, not hardware acceptance."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).resolve().parents[2];E=R/'evidence/field01'
def read(p):return json.loads((R/p).read_text())
base=read('evidence/field01/preservation-before01.json');changes=[]
for p,h in base['files'].items():
 f=R/p
 if not f.is_file()or hashlib.sha256(f.read_bytes()).hexdigest()!=h:changes.append(p)
assert not changes,changes
media=[]
for n in ['report-01.json','report-02.json']:
 p='evidence/field01/app07/media/'+n;r=read(p);assert r['durationMs']>=30000 and r['foregroundOnly']and r['visualForeground']and not r['visualCoverageFailures']
 samples=r['samples'];assert len(samples)==r['sampleCount'];fps=len(samples)/(r['durationMs']/1000);assert abs(fps-r['displayedFps'])<1e-9 and fps>=24
 lat=sorted(s['latencyUpperMs']for s in samples if s['latencyUpperMs']is not None);assert len(lat)==len(samples);p95=lat[math.ceil(len(lat)*.95)-1];assert abs(p95-r['latencyP95UpperMs'])<1e-6 and p95<=300
 assert r['actualImages']==0 and r['physicalLatency']=='NOT_MEASURED'
 faults=r['faultWindows'];assert faults
 for f in faults:
  assert f['status']=='RECOVERED'and f['configId']==r['configId']and 500<=f['recoveryMs']<=2000
  assert abs(f['recoveredDisplayBrowserMs']-f['at']-f['recoveryMs'])<.01
  assert f['recoveredSourceHostBounds']['lowerMs']>=f['serverResumeNotBeforeMs']
  assert r['measurementStartBrowserMs']<=f['at']<=r['measurementEndBrowserMs']
 media.append({'path':p,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest(),'fps':fps,'p95UpperMs':p95,'recoveryMs':[f['recoveryMs']for f in faults]})
raw=read('evidence/field01/flight02-raw-verification-sb5d91f31ba82446984dc.json');assert raw['executionVerified']and raw['missionItems']==16 and raw['readbackItems']==32 and raw['parameterWrites']==0
review=read('evidence/field01/flight/runs/sb5d91f31ba82446984dc/review.json');assert review['accepted']and not review['aborted']and review['authorityRestorable']is False
for p in ['evidence/field01/flight/runs/s19d098ad36b8435e9bf8/review.json','evidence/field01/flight/runs/sa974a3023ced42099b1b/review.json']:assert read(p)['accepted']is False
ledger=(E/'http-receiver-state01/delivery-receipts.jsonl').read_text().splitlines();assert len(ledger)==1
rec=json.loads(ledger[0]);receipt=rec.get('receipt')or rec.get('data')or rec
# Ledger shape is separately checked by receiver; locate the accepted receipt without rewriting it.
if 'status'not in receipt:
 receipt=next(v for v in rec.values()if isinstance(v,dict)and v.get('status')=='ACCEPTED_DURABLE_DELIVERY')
assert receipt['status']=='ACCEPTED_DURABLE_DELIVERY'and receipt['acceptedSimulatorExecution']and receipt['captureCount']==2 and receipt['actualImages']==0 and not receipt['authorityRestorable']
assert receipt['flightRun']==review['run']and receipt['modelSha256']==review['modelSha256']and receipt['planSha256']==review['planSha256']
size=sum(p.stat().st_size for p in E.rglob('*')if p.is_file());assert size<512*2**20
result={'status':'PASS_SELECTED_HOST_EVIDENCE_NOT_ANDROID_OR_HARDWARE','protectedFiles':len(base['files']),'protectedDifferences':changes,'media':media,'run':review['run'],'rawRecords':raw['rawRecords'],'receiverIndexSha256':receipt['indexSha256'],'syntheticJpegs':2,'actualImages':0,'evidenceBytes':size,'notChecked':['Xiaomi/ART/SAF','Hera controller/radio','physical camera/gimbal/thermal','sensor exposure GNSS synchronization','production/authenticity','new24h soak'],'preliminaryFailuresRetained':True}
print(json.dumps(result,ensure_ascii=False,indent=2))
