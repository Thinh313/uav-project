"""Exact selected assisted-window predicate; no scenario/orchestrator dependency."""
NS=1_000_000_000
def integer(x):return type(x)is int and x>=0

def assisted_window(rows,start,end):
 if not(integer(start)and integer(end)and end>=start):raise ValueError('WINDOW_SCHEMA')
 hb=land=None;last=-1;first=previous=None;boot_first=boot_last=None;positions=0;bad=[]
 for r in rows:
  now=r['hostNs']
  if not integer(now)or now<last:raise ValueError('TIMELINE_CLOCK')
  last=now;k=r['kind']
  if k=='heartbeat':hb=r
  if k=='landed':land=r
  if not start<=now<=end:continue
  if k=='heartbeat'and(not r['armed']or r['mode']!=17):bad.append('MODE_OR_ARMED_CONTRADICTION')
  if k=='landed'and r['state']!=2:bad.append('AIRBORNE_CONTRADICTION')
  if k!='position':continue
  valid=(hb is not None and land is not None and hb['armed']and hb['mode']==17 and land['state']==2 and 0<=now-hb['hostNs']<=1500_000_000 and 0<=now-land['hostNs']<=NS and 400<=r['relativeMm']<=5000)
  if not valid:bad.append('STALE_OR_UNQUALIFIED_POSITION')
  if previous is not None and now-previous>500_000_000:bad.append('POSITION_GAP')
  if boot_last is not None and r['bootMs']<boot_last:bad.append('AP_BOOT_REGRESSION')
  first=now if first is None else first;boot_first=r['bootMs']if boot_first is None else boot_first;boot_last=r['bootMs'];previous=now;positions+=1
 if first is None or first-start>500_000_000 or end-previous>500_000_000:bad.append('POSITION_EDGE_GAP')
 return dict(status='PASS'if not bad else'NOT_READY',failures=sorted(set(bad)),positions=positions,hostWindowNs=end-start,observedPositionSpanNs=0 if first is None else previous-first,APBootWindowNs=0 if boot_first is None else(boot_last-boot_first)*1_000_000)
