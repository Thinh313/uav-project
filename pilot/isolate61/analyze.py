"""Streaming AP phase analysis. Never changes inputs, never equates clock origins."""
from pathlib import Path
import collections,json,struct,sys,math,hashlib,datetime
R=Path(__file__).resolve().parents[2]
def stats(v):
 v=sorted(v)
 if not v:return {'n':0}
 return {'n':len(v),'mean':sum(v)/len(v),'p50':v[int((len(v)-1)*.5)],'p95':v[int((len(v)-1)*.95)],'p99':v[int((len(v)-1)*.99)],'max':v[-1]}
def signed(n):return n if n<2**63 else n-2**64
def analyze(out):
 stages=json.loads((out/'backend-stages.json').read_text());first=stages[0][1];last=stages[-1][1];by={s[0]:s for s in stages};bins=collections.defaultdict(list)
 for s in stages:bins[int((s[1]-first)//5_000_000_000)].append(s)
 events=collections.defaultdict(dict);kinds=collections.Counter()
 with(out/'ap-timing.bin').open('rb') as f:
  magic,cap,n,failed,size=struct.unpack('<8s4Q',f.read(40));assert magic==b'AERISD02' and n<=cap and failed==0 and size==64;f.seek(4096)
  for i in range(n):
   ev=struct.unpack('<QQIIQQQQq',f.read(64));assert ev[0]==i and ev[4]<=ev[5];kinds[ev[2]]+=1
   if ev[1] in by:
    assert ev[2] not in events[ev[1]],('DUPLICATE_AP_STAGE',ev[1],ev[2]);events[ev[1]][ev[2]]=ev
 def apmetrics(ids):
  rtt=[];sleep=[];overshoot=[];other=[];clips=[];debt=[];parse=[]
  for frame in ids:
   e=events[frame];next_e=events.get(frame+1,{})
   assert all(k in e for k in [10,11,12,13,14,20,21,24]),('MISSING_AP_STAGE',frame)
   rtt.append((e[13][4]-e[11][4])/1e6);parse.append((e[14][4]-e[13][4])/1e6)
   if 22 in e:
    assert 23 in e;s=(e[23][4]-e[22][4])/1e6;sleep.append(s);overshoot.append(s-signed(e[22][6])/1000)
   if 10 in next_e:other.append((next_e[10][4]-e[24][4])/1e6)
   d=signed(e[21][6]);debt.append(d)
   if d< -500000:clips.append({'frame':frame,'debtBeforeCapUs':d,'discardedDebtUs':-500000-d})
  return {'apRTTMs':stats(rtt),'apParseMs':stats(parse),'apOtherToNextServoMs':stats(other),'apSleepMs':stats(sleep),'apSleepOvershootMs':stats(overshoot),'minimumDebtBeforeCapUs':min(debt),'capClipCount':len(clips),'discardedDebtUs':sum(c['discardedDebtUs']for c in clips),'capClips':clips}
 windows=[]
 for k,ss in sorted(bins.items()):
  full=first+(k+1)*5_000_000_000<=last
  windows.append({'window':k,'fullFiveSeconds':full,'frames':len(ss),'fixedWallBucketRTF':len(ss)/6000 if full else None,'withinBucketRTF':(len(ss)-1)/1200/((ss[-1][1]-ss[0][1])/1e9) if len(ss)>1 else None,'hostComputeMs':stats([(s[3]-s[2])/1e6 for s in ss]),'hostDurableMs':stats([(s[4]-s[3])/1e6 for s in ss]),'hostPreSendMs':stats([(s[5]-s[1])/1e6 for s in ss]),**apmetrics([s[0]for s in ss])})
 phases=[(s[0]-stages[0][0])/1200-(s[1]-first)/1e9 for s in stages];sliding=[];j=0
 for i,s in enumerate(stages):
  while j<i and stages[j][1]<s[1]-1_000_000_000:j+=1
  if s[1]-first>=1e9 and s[1]>stages[j][1]:sliding.append((i-j)/1200/((s[1]-stages[j][1])/1e9))
 pairs=[json.loads(l)for l in(out/'clock-pairs.jsonl').read_text().splitlines()];matched=[p for p in pairs if p['status']=='MATCHED' and p['freshCalibration']]
 for p in matched:assert p['offsetLowNs']==p['hostSendNs']-p['guestReceiveNs']<=p['offsetHighNs']==p['hostReceiveNs']-p['guestSendNs']
 assert len(matched)>3
 return {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':out.name,'frames':len(stages),'wholeRTF':(len(stages)-1)/1200/((last-first)/1e9),'wholeRTFGe1':(len(stages)-1)/1200/((last-first)/1e9)>=1,'phaseLagMs':{'maximum':-min(phases)*1000,'end':-phases[-1]*1000,'minimum':-max(phases)*1000},'slidingOneSecondRTF':{'minimum':min(sliding),'distribution':stats(sliding)},'hostReceiveGapMs':stats([(b[1]-a[1])/1e6 for a,b in zip(stages,stages[1:])]),'windows':windows,'ap':apmetrics(list(by)),'apEventCounts':dict(kinds),'clock':{'statuses':dict(collections.Counter(p['status']for p in pairs)),'matchedBracketWidthMs':stats([(p['offsetHighNs']-p['offsetLowNs'])/1e6 for p in matched]),'cgroupFirstLast':{k:[matched[0][k],matched[-1][k]]for k in ['cgroupUsageUs','cgroupPeriods','cgroupThrottles','cgroupThrottledUs']},'clockOriginsNeverSubtractedWithoutNonceBracket':True},'speedup':1,'capUs':500000,'rateHz':1200,'fullG1Accepted':False,'windowTolerance':'NOT_APPROVED; diagnostic distributions, no invented PASS threshold'}
if __name__=='__main__':
 namespace,rid,dest=sys.argv[1:];p=R/'evidence'/namespace/'runs'/rid;r=analyze(p)
 with(R/'evidence/isolate61'/dest).open('x')as f:json.dump(r,f,indent=2);f.write('\n')
 print(json.dumps({'run':rid,'frames':r['frames'],'RTF':r['wholeRTF'],'clips':r['ap']['capClipCount'],'lostDebtUs':r['ap']['discardedDebtUs'],'minimum1sRTF':r['slidingOneSecondRTF']['minimum']}))
