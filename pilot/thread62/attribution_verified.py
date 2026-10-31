"""Separate local clocks and sampled CPU/runqueue counters; no invented one-way delay."""
from pathlib import Path
import json,struct,sys,collections,bisect,hashlib
from analyze import stats
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rusage(p):
 with p.open('rb')as f:
  magic,n,w=struct.unpack('<8sQQ',f.read(24));assert magic==b'AERISRU1'and w==9
  rows=[struct.unpack('<9q',f.read(72))for _ in range(n)];assert not f.read(1)
 for a,b in zip(rows,rows[1:]):assert all(y>=x for x,y in zip(a,b)),'RUSAGE_REGRESSION'
 return rows
def host_window(rows,a,b):
 ts=[r[0]for r in rows];lo=max(0,bisect.bisect_right(ts,a)-1);hi=min(len(rows)-1,bisect.bisect_left(ts,b));left,right=rows[lo],rows[hi]
 return {'sampleWindowNs':[left[0],right[0]],'coversRequested':left[0]<=a<=b<=right[0],'delta':{k:right[i]-left[i]for i,k in enumerate(['atNs','userCpuNs','systemCpuNs','minorFaults','majorFaults','voluntaryContextSwitches','involuntaryContextSwitches','blockInputs','blockOutputs'])if i},'scope':'Process aggregate sampled window includes observer threads, not exact backend-thread runnable wait'}
def run(rid):
 out=E/'runs'/rid;io=json.loads((out/'io-analysis.json').read_text());stages=json.loads((out/'backend-stages.json').read_text());frames={s[0]for s in stages};events=collections.defaultdict(dict)
 with(out/'ap-timing.bin').open('rb')as f:
  magic,cap,n,failed,w=struct.unpack('<8s4Q',f.read(40));assert magic==b'AERISD02'and failed==0 and w==64;f.seek(4096)
  for i in range(n):
   ev=struct.unpack('<QQIIQQQQq',f.read(64));assert ev[0]==i
   if ev[1]in frames and ev[2]in[10,11,13,14,24]:events[ev[1]][ev[2]]=ev
 guest=[json.loads(l)for l in(out/'guest-scheduler.jsonl').read_text().splitlines()];assert guest and [g['index']for g in guest]==list(range(len(guest)))
 for a,b in zip(guest,guest[1:]):assert b['scheduledNs']==a['scheduledNs']+(a['missedDeadlines']+1)*20000000
 series=collections.defaultdict(list);settings=set();memory=[];oom=[]
 for row in guest:
  setting=row['context'].get('/proc/sys/kernel/sched_schedstats');settings.add(setting)
  mem=row['context'].get('/sys/fs/cgroup/memory.current')
  if mem and mem.strip().isdigit():memory.append(int(mem))
  if row['context'].get('/sys/fs/cgroup/memory.events'):oom.append(row['context']['/sys/fs/cgroup/memory.events'])
  for task in row['tasks']:series[(task['tid'],task['startTicks'])].append((row['guestMonotonicNs'],task))
 summaries=[]
 for (tid,birth),rows in series.items():
  for (_,a),(_,b)in zip(rows,rows[1:]):assert all(y>=x for x,y in zip(a['schedstat'],b['schedstat'])),'GUEST_COUNTER_REGRESSION'
  a,b=rows[0][1],rows[-1][1];summaries.append({'tid':tid,'birthTicks':birth,'sampleWindowNs':[rows[0][0],rows[-1][0]],'cpuRuntimeNs':b['schedstat'][0]-a['schedstat'][0],'runqueueWaitNs':b['schedstat'][1]-a['schedstat'][1],'timeslices':b['schedstat'][2]-a['schedstat'][2],'states':dict(collections.Counter(t['state']for _,t in rows)),'minorFaultsDelta':b['minorFaults']-a['minorFaults'],'majorFaultsDelta':b['majorFaults']-a['majorFaults']})
 host=rusage(out/'wake-thread-rusage.bin');assert len(host)>3
 pairs=[json.loads(l)for l in(out/'clock-pairs.jsonl').read_text().splitlines()];pairs=[p for p in pairs if p['status']=='MATCHED'and p['freshCalibration']];assert len(pairs)>3
 details=[]
 for bad in io['worstFrames'][:20]:
  frame=bad['frame'];ev=events[frame];tid=ev[10][3];p=min(pairs,key=lambda p:abs((p['hostSendNs']+p['hostReceiveNs'])//2-bad['receiveNs']));ga=bad['receiveNs']-p['offsetHighNs'];gb=bad['sendNs']-p['offsetLowNs'];candidates=[]
  for (t,birth),rows in series.items():
   if t!=tid:continue
   ts=[x[0]for x in rows];lo=max(0,bisect.bisect_right(ts,min(ga,ev[10][4]))-1);hi=min(len(rows)-1,bisect.bisect_left(ts,max(gb,ev[14][4])));left,right=rows[lo],rows[hi];d=[y-x for x,y in zip(left[1]['schedstat'],right[1]['schedstat'])]
   candidates.append({'tid':tid,'birthTicks':birth,'sampleWindowNs':[left[0],right[0]],'cpuRuntimeDeltaNs':d[0],'runqueueWaitDeltaNs':d[1],'timeslicesDelta':d[2],'statesObserved':[r[1]['state']for r in rows[lo:hi+1]],'coversProjectedInterval':left[0]<=min(ga,ev[10][4]) and right[0]>=max(gb,ev[14][4]),'sampleIntervalMs':(right[0]-left[0])/1e6})
  assert candidates,'AP_TRACE_TID_NOT_IN_GUEST_KERNEL_SAMPLES'
  details.append({'frame':frame,'hostBackendWallMs':bad['wallMs'],'hostBackendThreadCpuMs':bad['threadCpuMs'],'apLocalServoToReceiveMs':(ev[13][4]-ev[11][4])/1e6,'guestAPTid':tid,'guestSampleWindows':candidates,'hostRusageWindow':host_window(host,bad['receiveNs'],bad['sendNs']),'nearestNonceBracket':{'id':p['id'],'hostSendNs':p['hostSendNs'],'hostReceiveNs':p['hostReceiveNs'],'widthMs':(p['offsetHighNs']-p['offsetLowNs'])/1e6,'projectedGuestIntervalNs':[ga,gb],'qualification':'Projection using nearest nonce calibration, not exact clock-drift bound or one-way network latency'}})
 apTids=sorted({e[10][3]for e in events.values()if 10 in e});req=json.loads((out/'request.json').read_text());result={'status':'MEASURED_SAMPLED_ATTRIBUTION_NOT_CAUSAL_PROOF','run':rid,'traceMode':req['traceMode'],'guestSamples':len(guest),'guestObservedWakeLatenessMs':stats([(g['guestMonotonicNs']-g['scheduledNs'])/1e6 for g in guest]),'guestMissedDeadlines':sum(g['missedDeadlines']for g in guest),'schedstatsSettings':list(settings),'runqueueWaitCounterAvailability':'POSITIVE_PER_TASK_KERNEL_COUNTER_OBSERVED'if any(s['runqueueWaitNs']>0 for s in summaries)else'NOT_PROVEN_ZERO_IS_NOT_NO_WAIT','apTraceThreadIds':apTids,'threadTotals':summaries,'guestMemoryMaxBytes':max(memory)if memory else None,'guestMemoryEventsFirstLast':[oom[0],oom[-1]]if oom else None,'hostRusage':host_window(host,host[0][0],host[-1][0]),'worstBackendFrameContext':details,'guestObserverError':json.loads((out/'guest-result.json').read_text())['error'],'scope':'Guest CPU/runqueue counters are per-task sampled deltas. Host rusage aggregates backend process incl observers. AP/backend durations remain local clocks; no subtraction inventing one-way delay or exclusive host scheduler wait. D-state alone does not prove filesystem root cause.','filesSha256':{p.name:sha(p)for p in [out/'guest-scheduler.jsonl',out/'guest-result.json',out/('guest-archive.json'if(out/'guest-archive.json').exists()else'forensic-recovery.json'),out/'wake-thread-rusage.bin',out/'ap-timing.bin']}}
 with(out/'attribution-verified.json').open('x')as f:json.dump(result,f,indent=2)
 print(json.dumps({k:result[k]for k in ['run','traceMode','guestSamples','schedstatsSettings','runqueueWaitCounterAvailability','apTraceThreadIds','guestMemoryMaxBytes']},indent=2))
if __name__=='__main__':run(sys.argv[1])
