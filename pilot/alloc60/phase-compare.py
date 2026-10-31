"""Same model-time interval, never silently excludes failed runs."""
from pathlib import Path
import json,struct,collections,sys
from analyze import stats
R=Path(__file__).resolve().parents[2];E=R/'evidence/alloc60';sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import unpack_intent
from readback import records
rows=[]
for i in range(1,5):
 driver=json.loads((E/f'a60R{i}-driver-result.json').read_text());out=E/'runs'/driver['owner']['run'];req=json.loads((out/'request.json').read_text());stages=json.loads((out/'backend-stages.json').read_text());first=stages[0][0];lo=first+12000;hi=first+30000;selected=[s for s in stages if lo<=s[0]<hi];assert len(selected)==18000
 meta=json.loads((out/'syscalls-meta.json').read_text());groups=collections.defaultdict(list);opnames={v:k for k,v in meta['operations'].items()};kindnames={v:k for k,v in meta['kinds'].items()}
 with(out/'syscalls.bin').open('rb')as f:
  _,n,_=struct.unpack('<8sQQ',f.read(24))
  for _ in range(n):
   v=struct.unpack('<12q',f.read(96))
   if lo<=v[3]<hi and v[1]in [1,2]:
    opname=opnames[v[1]];kind=kindnames[v[2]];groups[opname+':'+kind].append((v[7]-v[6])/1e6)
 ground=[]
 for rec in records(out/'frames.wal'):
  if rec['kind']=='INTENT'and lo<=rec['frame']<hi:
   body,_=unpack_intent(rec['body']);ground.append(json.loads(body)['modelAux']['ground'])
 assert len(ground)==18000 and all(ground),'MATCHED_INTERVAL_NOT_ALL_GROUND'
 wall=(selected[-1][1]-selected[0][1])/1e9
 rows.append({'tag':f'R{i}','run':out.name,'allocation':req['allocation'],'driverStatus':driver['status'],'modelIntervalSeconds':[10,25],'frames':len(selected),'allGround':True,'RTF':(len(selected)-1)/1200/wall,'syscallWallMs':{k:stats(v)for k,v in groups.items()},'receiveGapMs':stats([(b[1]-a[1])/1e6 for a,b in zip(selected,selected[1:])])})
with(E/'matched-model-interval.json').open('x')as f:json.dump({'status':'DESCRIPTIVE_MODEL10_TO25S_GROUND_INTERVAL','rows':rows,'scope':'Same18000frames/model interval/ground profile per run, all failures included. Two runs per variant on uncontrolled shared host; not flight performance or causality proof.'},f,indent=2)
print(json.dumps([{'tag':r['tag'],'allocation':r['allocation'],'RTF':r['RTF'],'fsyncP99Ms':r['syscallWallMs']['fsync:INTENT']['p99'],'rxWriteP99Ms':r['syscallWallMs']['write:RX']['p99']}for r in rows],indent=2))
