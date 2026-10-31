#!/usr/bin/env python3
"""Read retained files only; no runtime start or flight mutation. Exclusive receipt."""
import collections, datetime, importlib.util, json, pathlib, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('retained_audit',ROOT/'planning/simverify02/raw-audit01.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
RUN='rb8a62248ac6b403f8731';R=ROOT/'.local/simstability03/receiver01/evidence/simhand01/runs'/RUN
OUT=ROOT/'evidence/simstability03/raw-heartbeat-audit01.json'
def stats(values):
 s=sorted(values)
 return {'count':len(s),'p50':s[int((len(s)-1)*.50)] if s else None,'p95':s[int((len(s)-1)*.95)] if s else None,'p99':s[int((len(s)-1)*.99)] if s else None,'max':max(s) if s else None}
start=time.monotonic();names=['frames.wal','ap-timing.bin','mavlink.jsonl','backend-stages.json','launch.json','closure.json','backend-result.json','operator-review.json','operator-review.receipt.json']
before={n:a.sha256_file(R/n) for n in names};wal=a.audit_wal(R/'frames.wal');ap=a.audit_ap(R/'ap-timing.bin',wal['admittedFrames']);mav=a.audit_mavlink(R/'mavlink.jsonl',RUN)
hb=[];requests=[];commands=collections.Counter();acks=collections.Counter()
for line in (R/'mavlink.jsonl').open():
 q=json.loads(line);d=q['data']
 if q['kind']=='AP_RX_DECODED' and d['id']==0:hb.append(int(q['nodeNs']))
 if q['kind']=='AP_RX_DECODED' and d['id']==77:acks[(d['fields']['command'],d['fields']['result'])]+=1
 if q['kind']=='GCS_TX_REQUEST' and d['id']==76:
  f=d['fields'];commands[f['command']]+=1
  if f['command']==511:requests.append(f)
gaps=[(b-a)/1e6 for a,b in zip(hb,hb[1:])]
stages=json.loads((R/'backend-stages.json').read_text());assert len(stages)==wal['admittedFrames'];assert all(len(r)==10 and r[0]==i for i,r in enumerate(stages))
stageMetrics={name:stats([(r[b]-r[c])/1e6 for r in stages])for name,b,c in [('receiveToIntegrateStartMs',2,1),('integrationMs',3,2),('computeToDurableBarrierMs',4,3),('durableBarrierToSensorSentMs',5,4),('receiveToSensorSentMs',5,1)]}
for name,col in [('intentOsWriteMs',6),('intentFsyncMs',7),('intentAppendMs',8)]:stageMetrics[name]=stats([r[col]/1e6 for r in stages])
backend=json.loads((R/'backend-result.json').read_text());closure=json.loads((R/'closure.json').read_text());review=json.loads((R/'operator-review.json').read_text());launch=json.loads((R/'launch.json').read_text());mounts=a.audit_mounts(R,launch)
after={n:a.sha256_file(R/n)for n in names};assert before==after
report={'format':'aeris-simstability03-raw-heartbeat-audit','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':RUN,'status':'FAILED_FLIGHT_NOT_ACCEPTED','inputsUnchanged':True,'inputSha256':before,'scriptSha256':a.sha256_file(pathlib.Path(__file__)),'wal':wal,'ap':ap,'mavlink':mav,'heartbeat':{'observations':len(hb),'wallGapMs':stats(gaps),'gapsAbove1500Ms':sum(g>1500 for g in gaps),'currentGuardMs':1500,'initialMessageIntervalRequests':requests,'heartbeatIntervalRequested':any(r.get('param1')==0 for r in requests),'acks':[{'command':k[0],'result':k[1],'count':v}for k,v in sorted(acks.items())]},'backendStageMetrics':stageMetrics,'backend':backend,'closure':closure,'review':{'status':review['status'],'success':review['success'],'reason':review['reason'],'observedEnd':review['observedEnd'],'allOwnedClosed':review['closure']['allOwnedClosed']},'mounts':mounts,'causalInference':'Observed HB gaps exceed retained 1500ms wall guard. AP default heartbeat cadence is1000ms AP model time; observed RTF0.6166 can make wall cadence exceed guard. UI stalls and scheduling may also contribute; high-rate request must be measured, not presumed to fix.','recommendation':{'scope':'SUCCESSOR_ADAPTER_ONLY_READ_STREAM_CONFIGURATION','command':511,'param1':0,'param2':100000,'requestedModelHz':10,'targetSystem':42,'targetComponent':1,'guardMsUnchanged':1500,'modelSpeedupUnchanged':1,'capMsUnchanged':500,'acceptance':'Actual owned AP command ACK and measured fresh HB distribution under UI load plus normal preflight/takeoff required; this audit does not establish a fix.'},'elapsedSeconds':time.monotonic()-start}
with OUT.open('x')as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'out':str(OUT),'frames':wal['admittedFrames'],'walClose':wal['closeRecords'],'hbGapMs':stats(gaps),'above1500':sum(g>1500 for g in gaps),'rtf':backend['activeReceiveRTF'],'stage':stageMetrics,'arm':mav['command400Intents']}))
