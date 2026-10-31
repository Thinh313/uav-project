"""Bounded read-only host observation for actual UI runs. No control POST.

At most1Hz to avoid turning measurement into a high-load polling experiment.
"""
from pathlib import Path
import sys,time,json,urllib.request,hashlib,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/repair01'
label=sys.argv[1];assert label.replace('-','').isalnum()
seconds=int(sys.argv[2]);assert 1<=seconds<=600
out=E/('observe-'+label+'.jsonl');assert not out.exists()
started=time.monotonic();count=0
with out.open('x')as target:
 while time.monotonic()-started<seconds:
  before=time.monotonic_ns()
  try:
   raw=urllib.request.urlopen('http://127.0.0.1:8872/api/state',timeout=3).read(512*1024)
   d=json.loads(raw);f=d['flight']
   row={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observerHostMonoNs':str(before),'httpMs':(time.monotonic_ns()-before)/1e6,
     'responseSha256':hashlib.sha256(raw).hexdigest(),'client':d.get('client'),
     'flight':{k:f.get(k)for k in ['run','request','mode','busy','authority','error','positionAgeMs','latestPosition','pendingTransactions','autoGate']},
     'live':{k:(f.get('live')or{}).get(k)for k in ['stage','armed','transport','heartbeatAgeMs','boot']},
     'payload':{k:v for k,v in d.items()if k.lower().startswith('payload')},'authorityRestored':d.get('authorityRestored')}
  except Exception as ex:row={'observerHostMonoNs':str(before),'error':str(ex),'notAcceptance':True}
  target.write(json.dumps(row,ensure_ascii=False)+'\n');target.flush();count+=1
  assert target.tell()<2*2**20,'OBSERVER_LOG_BOUND'
  delay=1-(time.monotonic_ns()-before)/1e9
  if delay>0:time.sleep(delay)
print(json.dumps({'file':str(out.relative_to(R)),'records':count,'kind':'READONLY_OBSERVATION_NOT_CONTROL_OR_ACCEPTANCE'}))
