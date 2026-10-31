from pathlib import Path
import json,struct,statistics,hashlib,collections,datetime
R=Path(__file__).resolve().parents[2];new=R/'.local/simstability03/receiver01/evidence/simhand01/runs/rb8a62248ac6b403f8731';old=R/'.local/simverify02/receiver04/evidence/simhand01/runs/rfebb3af9a261492cabd8'
def stat(a,scale=1000):
 a=sorted(a);return {'n':len(a),'meanUs':statistics.mean(a)/scale,'p50Us':a[len(a)//2]/scale,'p95Us':a[int(len(a)*.95)]/scale,'p99Us':a[int(len(a)*.99)]/scale,'maxUs':a[-1]/scale,'sumSeconds':sum(a)/(scale*1e6)}
def backend(p):
 rows=json.loads((p/'backend-stages.json').read_text());s={n:stat([r[b]-r[a]for r in rows])for n,a,b in [('rxToComputeStart',1,2),('modelAndSensorEncode',2,3),('rowAndIntentBarrier',3,4),('barrierToSendReturn',4,5)]};s['sendReturnToNextRx']=stat([rows[i+1][1]-r[5]for i,r in enumerate(rows[:-1])]);
 if len(rows[0])>=10:
  for name,i in [('intentOsWrite',6),('intentFsyncWithHookSpan',7),('intentAppend',8)]:s[name]=stat([r[i]for r in rows])
 return {'result':json.loads((p/'backend-result.json').read_text()),'stages':s,'inputStageSHA256':hashlib.sha256((p/'backend-stages.json').read_bytes()).hexdigest()}
H=struct.Struct('<QQIIQQQQq');frames={};counts=collections.Counter();duplicate=0
with (new/'ap-timing.bin').open('rb')as f:
 magic,capacity,count,fail,size=struct.unpack('<8s4Q',f.read(40));assert magic==b'AERISD02'and size==64;f.seek(4096)
 for i in range(count):
  r=H.unpack(f.read(64));assert r[0]==i;counts[r[2]]+=1
  if r[2]in[11,13,14]:
   bucket=frames.setdefault(r[1],{});duplicate+=int(r[2]in bucket);bucket[r[2]]=r
ap={'events':count,'capacity':capacity,'recorderFailures':fail,'duplicates11_13_14':duplicate,'stageCounts':dict(counts),'clock':'GUEST_MONOTONIC_WITHIN_CLOCK_DURATIONS','servoSendToSensorReceive':stat([r[13][5]-r[11][5]for r in frames.values()if 11 in r and 13 in r]),'receiveToParse':stat([r[14][5]-r[13][5]for r in frames.values()if 13 in r and 14 in r])}
rows=[json.loads(x)for x in (new/'mavlink.jsonl').open()];hb=[r for r in rows if r['kind']=='AP_RX_DECODED'and r['data']['id']==0];gaps=[int(b['nodeNs'])-int(a['nodeNs'])for a,b in zip(hb,hb[1:])];approval=[]
for r in rows:
 if r['kind']=='EXPLICIT_PREFLIGHT_APPROVAL':approval.append({'atUTC':r['utc'],'heartbeatAgeMs':(int(r['nodeNs'])-max(int(h['nodeNs'])for h in hb if int(h['nodeNs'])<=int(r['nodeNs'])))/1e6})
m=[json.loads(x)for x in (new/'clock-pairs.jsonl').open()if 'cgroupUsageUs'in x];a,b=m[0],m[-1];cpu={k:b[k]-a[k]for k in ['cgroupUsageUs','cgroupPeriods','cgroupThrottles','cgroupThrottledUs']};cpu['hostObservationSeconds']=(b['hostReceiveNs']-a['hostReceiveNs'])/1e9
q={'format':'aeris-simstability03-pacing-diagnosis','version':1,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'CLOSED_RAW_TIMING_DIAGNOSIS_NOT_WAL_FULL_CHAIN_OR_FLIGHT_ACCEPTANCE','status':'FAIL_FLIGHT_QUALIFICATION_NO_ARM','new':backend(new),'oldComparison':backend(old),'actualAP':ap,'heartbeat':{'received':len(hb),'gap':stat(gaps),'gapsOver1500ms':sum(x>1500e6 for x in gaps),'approvalObservations':approval,'armIntents':sum(r['kind']=='GCS_TX_REQUEST'and r['data']['id']==76 and r['data'].get('fields',{}).get('command')==400 for r in rows)},'cgroup':cpu,'findings':['WAL os.write and fsync are separately measured; fsync-with-hook span is not pure kernel CPU time.','All host per-frame stages are slower than old run; unmeasured host thermal/frequency/contention differences prevent single-cause attribution.','Largest host gap is send-return to next receive. It contains AP/network/host scheduling and is not an AP-only measurement.','No cgroup throttling observed in sampled counters; this does not prove absence of host scheduling contention.','AP heartbeat gaps regularly exceed unchanged 1500ms guard; approval itself observed age1415ms. Screenshot/UI delays may reveal stale heartbeat rather than cause raw gap.','Higher authenticated/target-checked HEARTBEAT message cadence is justified; freshness guard, exact sensor bytes, fsync-before-send, speedup1 and cap500ms should remain unchanged.','No runtime preallocation or speculative physics rewrite adopted.'],'closure':json.loads((new/'closure.json').read_text()),'review':{'status':json.loads((new/'operator-review.json').read_text())['status'],'reason':json.loads((new/'operator-review.json').read_text())['reason']}}
(R/'evidence/simstability03/pacing-diagnosis01.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'status':q['status'],'APtrace':ap,'HB':q['heartbeat'],'cpu':cpu}))
