"""Small offline tests only; revised live SITL not authorized by handoff steering."""
from pathlib import Path
import tempfile,json,gzip,time,sys,shutil
from guarded_journal import Journal
from epoch import Epoch
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-pipe03';root=E/'shutdown-journal-fixtures';root.mkdir();checks=[]
def check(name,ok):
 assert ok,name;checks.append({'name':name,'pass':True})
for threaded in [False,True]:
 out=root/('threaded'if threaded else'inline');out.mkdir();state=out/'state';state.mkdir()
 j=Journal(out,state,threaded,raw_limit=2048,compressed_limit=1024**2);attempted=[];failure=None
 for n in range(40):
  row={'frame':n,'mock':True,'data':'x'*400};attempted.append(row)
  try:j.submit(row,None)
  except RuntimeError as e:failure=str(e);break
 try:j.seal()
 except RuntimeError as e:failure=str(e)
 raw=[json.loads(x)for x in gzip.open(out/'physics-raw.jsonl.gz','rt')];tail=[json.loads(x)for x in(out/'journal-incomplete-tail.jsonl').read_text().splitlines()]
 check(('threaded'if threaded else'inline')+' quota refuses complete seal',bool(failure)and bool(j.error))
 check(('threaded'if threaded else'inline')+' every attempted row retained once',sorted(raw+tail,key=lambda x:x['frame'])==attempted)
 check(('threaded'if threaded else'inline')+' sticky failure admits no silent continuation',j.error is not None)
p=root/'epoch';p.mkdir();s=p/'state';s.mkdir();now=[0,0];ep=Epoch(s,p,'test',lambda:now[0],lambda:now[1]);ep.progress();ep.drain()
check('draining blocks new adapter admission by published status',json.loads((s/'epoch.json').read_text())['status']=='DRAINING')
now[:]=[1000000,1000000];ep.check();ep.progress();check('drain may complete already admitted fresh step',not ep.terminal and ep.draining)
ep.close();check('drained writer closes without recreating LIVE epoch',json.loads((s/'epoch.json').read_text())['status']=='CLOSED')
p=root/'stale-drain';p.mkdir();s=p/'state';s.mkdir();now=[0,0];ep=Epoch(s,p,'test',lambda:now[0],lambda:now[1]);ep.progress();now[:]=[3200000000,3200000000]
try:ep.drain()
except RuntimeError:pass
check('drain never bypasses3s stale/suspension gate',ep.terminal and ep.reason=='STALE_OR_SUSPENDED')
with(E/'shutdown-journal-tests.json').open('x')as f:json.dump({'status':'PASS_OFFLINE_ONLY','checks':checks,'liveRevisedSitl':'NOT_CHECKED_OWNER_REQUESTED_HANDOFF','freeBytes':shutil.disk_usage(R).free},f,indent=2);f.write('\n')
print('SHUTDOWN_JOURNAL_OFFLINE_PASS',len(checks))
