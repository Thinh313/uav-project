"""Immutable AP/backend traces, same-frame overlap/jitter correlations only."""
from pathlib import Path
from array import array
import mmap,struct,json,statistics,math,hashlib,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-journal04';old=R/'evidence/sim32-pipe03';summary=json.loads((old/'pre-fix-summary.json').read_text());results=[]
def stats(a):
 b=sorted(a)
 return {'n':len(b),'meanUs':statistics.fmean(b)/1000,'p50Us':b[int((len(b)-1)*.5)]/1000,'p95Us':b[int((len(b)-1)*.95)]/1000,'p99Us':b[int((len(b)-1)*.99)]/1000,'maxUs':b[-1]/1000}
def corr(a,b):
 x=statistics.fmean(a);y=statistics.fmean(b);sa=sum((v-x)**2 for v in a);sb=sum((v-y)**2 for v in b)
 return sum((v-x)*(w-y)for v,w in zip(a,b))/math.sqrt(sa*sb)if sa and sb else None
for case in summary['cases']:
 p=old/'runs'/case['run'];proof=json.loads((p/'bounded-stage-analysis.json').read_text());n=proof['verifiedFramePrefix'];launch=json.loads((p/'launch.json').read_text());assert launch['runtimeConfiguration']['requestedSpeedup']==1 and launch['pacerPolicy']['maximumNegativeDebtUs']==500000
 assert launch['binarySha256']=='f2be1f349f84b4aedaa5912b3050f64f476f3218bc4f68b34ad4de11393c2d08'
 durations={k:array('q')for k in ['transport','backendRxSend','outsideBackendInterval','model','serialization','send','enqueue','apParse','apSync','sleepOvershoot','nextCycle']};current=None;ev={};previous=None;worst=[];cycles=[]
 with(p/'backend-stages.bin').open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as b,(p/'ap-timing.bin').open('rb')as g,mmap.mmap(g.fileno(),0,access=mmap.ACCESS_READ)as a:
  _,_,count,failed,size=struct.unpack_from('<8s4Q',a);assert failed==0 and size==64
  def consume(frame,events):
   global previous
   if frame>=n:return
   r=struct.unpack_from('<11Q',b,4096+frame*88);assert r[0]==frame
   e={k:events[k][0]for k in [10,11,13,14,20,21,24]};assert all(len(events[k])==1 for k in e)
   transport=e[13][4]-e[11][4];backend=r[6]-r[2];delta=transport-backend
   durations['transport'].append(transport);durations['backendRxSend'].append(backend);durations['outsideBackendInterval'].append(delta)
   for name,x,y in [('model',3,4),('serialization',4,5),('send',5,6),('enqueue',7,8)]:durations[name].append(r[y]-r[x])
   durations['apParse'].append(e[14][4]-e[13][4]);durations['apSync'].append(e[24][4]-e[20][4])
   if 22 in events:durations['sleepOvershoot'].append(events[23][0][4]-events[22][0][4]-events[22][0][6]*1000)
   if previous is not None:
    cycle=e[10][4]-previous[10][4];cycles.append(cycle);durations['nextCycle'].append(cycle)
   previous=e
   if len(worst)<20 or transport>worst[-1]['transportNs']:
    worst.append({'frame':frame,'transportNs':transport,'hostRxSendNs':backend,'hostModelNs':r[4]-r[3],'serializationNs':r[5]-r[4],'sendNs':r[6]-r[5]});worst.sort(key=lambda x:x['transportNs'],reverse=True);worst[:]=worst[:20]
  for i in range(count):
   row=struct.unpack_from('<QQIIQQQQq',a,4096+i*64);frame,kind=row[1:3]
   if current is not None and frame!=current:consume(current,ev);ev={}
   current=frame;ev.setdefault(kind,[]).append(row)
  if current is not None:consume(current,ev)
 assert len(durations['transport'])==n
 clocks=[json.loads(x)for x in(p/'clock-pairs.jsonl').read_text().splitlines()];matched=[x for x in clocks if x['status']in ['MATCHED','LATE_MATCHED']];low=max(x['offsetLowNs']for x in matched);high=min(x['offsetHighNs']for x in matched)
 host_ns_delta=(matched[-1]['hostSendNs']-matched[0]['hostSendNs']);guest_ns_delta=matched[-1]['guestReceiveNs']-matched[0]['guestReceiveNs'];ratio=host_ns_delta/guest_ns_delta
 row={'case':case['name'],'run':case['run'],'engine':case['engine'],'addedCpuWorkers':case['addedCpuWorkers'],'uiStatus':case['uiStatus'],'reportedRtf':case['rtf'],'exactRecordedFrames':n,'captureComplete':proof['status']=='VERIFIED_COMPLETE_CAPTURE','controllerPauseConfound':case['controllerPauseConfound'],'durations':{k:stats(v)if v else None for k,v in durations.items()},'transportVsBackendPearson':corr(durations['transport'],durations['backendRxSend']),'transportVsModelPearson':corr(durations['transport'],durations['model']),'transportOver833333ns':sum(v>833333 for v in durations['transport']),'backendOver833333ns':sum(v>833333 for v in durations['backendRxSend']),'outsideBackendNegativeCount':sum(v<0 for v in durations['outsideBackendInterval']),'clockOffsetIntersectionNs':[low,high],'constantOffsetCompatible':low<=high,'observedHostGuestElapsedRatio':ratio,'clockRatioDiagnosticOnlyNoScaleApplied':True,'worstTransportFrames':worst,'debtClipSeconds':proof['clippedTimeUs']/1e6,'apCgroupThrottleCountDelta':matched[-1]['cgroupThrottles']-matched[0]['cgroupThrottles'],'interpretation':'Difference between guest transport duration and paired host RX-to-send duration is descriptive, not isolated network latency; clocks are different, send return and guest receive boundaries can overlap. No additive stage sums, exact one-way latency or CPU causality claim.'}
 results.append(row);print(case['name'],n,'TRACE_STAGE_CORRELATION_VERIFIED',flush=True)
with(E/'trace-analysis.json').open('x')as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_OFFLINE_ALL6_CAPTURE_PREFIXES','cases':results,'rtfGate':'NOT_ESTABLISHED','oldMissingRawFrames':2,'zeroSourceOrTraceEdits':True,'recommendationOrder':['Preserve pre-send frame bytes/intent and quantify durability cost first','Preencode immutable archive row once on producer; worker does compression and snapshot only','Diagnose AP/backend/VM scheduling and datagram transit via synchronized frame-bracket instrumentation on future authorized SITL','Do not lower cap/change speedup/drop frames or attribute wait to network alone']},f,indent=2);f.write('\n')
