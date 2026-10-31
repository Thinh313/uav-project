"""Read-only changing UI/flight states; no control or heartbeat writes."""
import urllib.request,json,time,os
from pathlib import Path
end=time.monotonic()+2700;last=None;count=0
with Path('evidence/betastability02/ui-journey-observer02.jsonl').open('x')as f:
 while time.monotonic()<end:
  try:
   with urllib.request.urlopen('http://127.0.0.1:8896/api/ui-observation',timeout=2)as r:o=json.load(r)
   with urllib.request.urlopen('http://127.0.0.1:8896/api/state',timeout=2)as r:s=json.load(r)['result']
   v=o.get('observation') or {};flight=s['flight'];q={'run':flight['run'],'stage':flight['live']['stage']if flight['live']else None,'archivePending':s['archivePending'],'committed':s['archiveCommittedRuns'],'reviewUI':'beta-review-select'in v.get('controls',{}),'foreground':v.get('foreground'),'instance':v.get('instance'),'uiAgeMs':o['ageMs'],'clientActive':s['client']['active'],'payloadLeases':s['payloadAuthority']['current']['leaseCount']}
  except Exception as e:q={'unavailable':type(e).__name__,'detail':str(e)[:200]}
  compare={k:v for k,v in q.items()if k!='uiAgeMs'}
  if compare!=last:
   last=compare;count+=1;assert count<=4096,'OBSERVER_EVENT_BOUND';f.write(json.dumps({'wallUTC':time.time(),'observation':q})+'\n');f.flush();os.fsync(f.fileno())
  time.sleep(.5)
