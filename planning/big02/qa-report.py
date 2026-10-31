"""Independent offline check of browser self-reported software pipeline samples.
No camera/glass-to-glass/GPU claim. Cannot independently establish unexported window bounds.
"""
import json,math,argparse
from pathlib import Path
def finite(x):return type(x)in(int,float)and math.isfinite(x)
def quantile(xs,p):
 xs=sorted(x for x in xs if finite(x));return xs[min(len(xs)-1,math.ceil(len(xs)*p)-1)]if xs else None
def check(r,targets):
 assert r['format']=='aeris-big02-browser-report'and r['sourceKind']=='SYNTHETIC'and r['actualImages']==0
 samples=r['samples'];n=len(samples);duration=r['durationMs'];assert type(samples)is list and n==r['sampleCount']and 1<=n<=4096 and finite(duration)and duration>0
 prev=None
 for s in samples:
  assert type(s['frameId'])is int and all(finite(s[k])for k in['sourceMs','displayMs','latencyMs','encodeMs','decodeMs'])
  assert s['displayMs']>=s['sourceMs']and s['encodeMs']>=0 and s['decodeMs']>=0 and abs((s['displayMs']-s['sourceMs'])-s['latencyMs'])<1e-6
  assert s['relayRoundtripMs']is None or finite(s['relayRoundtripMs'])and s['relayRoundtripMs']>=0
  if prev:assert s['frameId']>prev['frameId']and s['sourceMs']>prev['sourceMs']and s['displayMs']>=prev['displayMs']
  prev=s
 gaps=r['displayGapsMs'];assert len(gaps)==n and all(finite(x)and x>=0 for x in gaps)
 for i in range(1,n):assert abs(gaps[i]-(samples[i]['displayMs']-samples[i-1]['displayMs']))<1e-6
 assert samples[-1]['displayMs']-samples[0]['displayMs']<=duration+1e-6
 missing=sum(s['relayRoundtripMs']is None for s in samples);assert r['stageMissingCounts']['relayRoundtrip']==missing
 metrics={'displayedFps':n/(duration/1000),'latencyP50Ms':quantile([s['latencyMs']for s in samples],.5),'latencyP95Ms':quantile([s['latencyMs']for s in samples],.95),'latencyP99Ms':quantile([s['latencyMs']for s in samples],.99),'maximumDisplayGapMs':max(gaps)}
 for k,v in metrics.items():assert finite(r[k])and abs(r[k]-v)<=1e-6
 coverage=targets['minimumMeasurementMs']<=duration<=targets['maximumMeasurementMs']and r['foregroundOnly']is True and r['sampleOverflow']==0
 recovery=r.get('recoveryMs');gates={'validCoverage':coverage,'latency':coverage and metrics['latencyP95Ms']<=targets['latencyP95Ms']and metrics['latencyP99Ms']<=targets['latencyP99Ms'],'fps':coverage and metrics['displayedFps']>=targets['minimumDisplayedFps'],'noUnexplainedFreeze':coverage and metrics['maximumDisplayGapMs']<targets['maximumUnexplainedFreezeMs'],'recovery':'NOT_MEASURED'if recovery is None else finite(recovery)and recovery<=targets['recoveryMs']}
 for k,v in gates.items():assert r['engineeringGate'][k]==v,(k,r['engineeringGate'][k],v)
 return {'status':'SELF_REPORTED_SAMPLE_ARITHMETIC_VERIFIED','run':r['run'],'boot':r['boot'],'configId':r['configId'],'feed':r['feed'],'profileId':r['profileId'],'samples':n,'durationMs':duration,'derivedMetrics':metrics,'gates':gates,'missingRelayRoundtripSamples':missing,'scope':'Same-browser source→canvas proxy only. No independent sensor/GPU timing. Window start/end absent; duration/foreground remain browser-self-report. First display gap uses preceding pre-window frame and cannot be independently recomputed.'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('report',type=Path);a.add_argument('--profile',type=Path,default=Path('media/big02/profile01.json'));x=a.parse_args();print(json.dumps(check(json.loads(x.report.read_text()),json.loads(x.profile.read_text())['targets']),indent=2))
