"""Separate verification pass over final artifacts, with immutable Python oracle."""
from pathlib import Path
import sys,json,hashlib,importlib.util,struct,zlib,shutil
from recovery import recover,public
from wal_journal import HEADER,unpack_intent
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-journal04';spec=importlib.util.spec_from_file_location('immutable_verify',R/'evidence/sim32/source-final/pilot/sim32/physics.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
suite=json.loads((E/'fault-suite-attempt08.json').read_text());close=json.loads((E/'closure-tests-receiver-bound.json').read_text());names=[x['name']for x in suite['cases']+close['cases']];proofs=[];emergency=[]
for name in names:
 p=E/'cases'/name;before=hashlib.sha256((p/'frames.wal').read_bytes()).hexdigest();r=recover(p);model=ref.Model(json.loads((p/'profile.json').read_bytes()));computed=0
 for frame,x in sorted(r['intents'].items()):
  row=x['row'];magic,rate,count,*pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']));assert frame==count==computed and magic==18458 and rate==1200
  sensor=model.step(pwm,1/rate);assert '\n'+json.dumps(sensor,separators=(',',':'),allow_nan=False)+'\n'==row['sensorUtf8'];snap=model.snapshot();assert all(snap[k]==row['modelAux'][k]for k in ['rpmEstimated','energyWhEstimated','ground']);computed+=1
 receivers=json.loads((p/'receiver.json').read_bytes())if(p/'receiver.json').exists()else[]
 observed=len(receivers);assert all(x['sensorUtf8']in {i['row']['sensorUtf8']for i in r['intents'].values()}for x in receivers)
 assert before==hashlib.sha256((p/'frames.wal').read_bytes()).hexdigest()
 for failure in p.glob('wal-failure-*.bin'):
  data=failure.read_bytes();d=json.loads(failure.with_suffix('.json').read_bytes());kind,flags,reserved,frame,size,seq,ns=HEADER.unpack_from(data);payload=data[HEADER.size:HEADER.size+size];assert len(data)==HEADER.size+size+36 and struct.unpack_from('<I',data,HEADER.size+size)[0]==zlib.crc32(data[:HEADER.size+size])and hashlib.sha256(data).hexdigest()==d['fullAttemptedRecordSha256']
  if kind==3:
   body,snapshot=unpack_intent(payload);row=json.loads(body)
   if frame not in r['intents']:
    assert frame==computed;_,rate,count,*pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']));sensor=model.step(pwm,1/rate);assert '\n'+json.dumps(sensor,separators=(',',':'),allow_nan=False)+'\n'==row['sensorUtf8']
   assert not any(x.get('sensorUtf8')==row['sensorUtf8']for x in receivers)
  emergency.append({'case':name,'frame':frame,'kind':d['kind'],'fullAttemptedBytesVerified':True,'notCanonicalCommitOrExecutionProof':True})
 summary=json.loads((p/'summary.json').read_bytes())if(p/'summary.json').exists()else None
 if summary:
  if summary['status']=='COMPLETE_ACCEPTED_MOCK_CAPTURE':assert r['completeAcceptedCapture']
  else:assert not r['completeAcceptedCapture']
 if name.startswith('queuefull'):assert summary['computed']==256 and observed==256 and summary['queueHighwater']==256
 assert json.loads((p/'closure.json').read_bytes())['processClosed']
 proofs.append({'case':name,'status':'PASS','exactCanonicalComputedIntents':computed,'receiverObservedSensors':observed,'receiverMissingPayloads':0,'epochOutcome':summary['epochReason']if summary else'PROCESS_KILLED_NO_SUMMARY','readOnlyWalSha256':before,'recoveryStatus':r['status'],'unknownFrames':r['sendOutcomeUnknownFrames']})
result={'status':'PASS_SEPARATE_OFFLINE_VERIFICATION','processCases':len(proofs),'exactCanonicalComputedIntents':sum(x['exactCanonicalComputedIntents']for x in proofs),'receiverObservedSensors':sum(x['receiverObservedSensors']for x in proofs),'receiverMissingPayloads':0,'emergencyRecords':emergency,'proofs':proofs,'independentReviewer':False,'noNewSITL':True,'hostPowerLoss':'NOT_CHECKED','freeBytes':shutil.disk_usage(R).free}
with(E/'final-artifact-verification-receiver-bound.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
print(result['status'],result['processCases'],result['exactCanonicalComputedIntents'],result['receiverObservedSensors'],len(emergency),flush=True)
