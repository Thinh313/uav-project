from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess,ast
R=Path(__file__).resolve().parents[2];H=R/'pilot/mapping51';E=R/'evidence/mapping51';sys.path.insert(0,str(R/'pilot/apstream40'));import guard as g
checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
b=json.loads((E/'preservation-before.json').read_text());check('frozen source/candidate/research/completed50 bytes unchanged',not g.bad(b['files']));check('ENDURE inventory unchanged',g.endure()==b['endurePaths']);check('host floor20GiB',g.free()>=20*2**30)
pins=json.loads((E/'runtime-pins5.json').read_text());check('tested runtime/UI/QA SHA unchanged',not g.bad(pins['files']))
counts={'host5':113,'edge3':24,'crash5':13,'browser5':49}
for name,n in counts.items():
 j=json.loads((E/name/'receipt.json').read_text());check(name+' result/count',j['status']=='PASS'and j['checks']==n and len(j['results'])==n and all(r['pass']for r in j['results']))
br=json.loads((E/'browser5/receipt.json').read_text());closed=json.loads((E/'browser5/cleanup.json').read_text())['processes'];check('real browser zero JS errors/external requests',not br['errors']and not br['external']);check('real server PID restart and closure',len(br['processes'])==2 and br['processes'][0]['pid']!=br['processes'][1]['pid']and [p['pid']for p in br['processes']]==[p['pid']for p in closed]and all(p['exit']['code']==0 for p in closed))
cr=json.loads((E/'crash5/receipt.json').read_text());check('three actual owned SIGKILL',len(cr['processes'])==3 and all(p['exit']['signal']=='SIGKILL'for p in cr['processes']))
removed=[]
for family,end in [('host',5),('edge',3),('crash',5),('browser',5)]:
 for i in range(1,end+1):
  p=E/(family+str(i))/'cleanup.json';j=json.loads(p.read_text());check(family+str(i)+' owned scratch absent',all(not(R/name).exists()for name in j['removed']));removed.extend(j['removed'])
check('earlier compiler angle failure retained',(E/'host1/failure.json').is_file());check('earlier worker top-await exit failure retained',(E/'crash1/failure.json').is_file())
for p in H.glob('*.mjs'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,r.returncode==0)
for p in H.glob('*.py'):ast.parse(p.read_text());check('syntax '+p.name,True)
for c in json.loads((E/'sources/captures.json').read_text()):check('primary reference raw SHA '+c['id'],c['status']==200 and g.sha(E/'sources'/(c['id']+'.html'))==c['sha256'])
alloc=sum(p.stat().st_blocks*512 for d in[H,E]for p in d.rglob('*')if p.is_file());check('task32MiB budget',alloc<b['budgetBytes'])
out={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS_SCOPED_MOCK_REPLAY','requirementCoverage':{'implemented':7,'total':7,'percent':100},'scenarioCounts':counts,'scenarioChecks':sum(counts.values()),'verificationChecks':len(checks),'results':checks,'protectedCount':len(b['files']),'endureCount':len(b['endurePaths']),'allocatedBytes':alloc,'freeBytes':g.free(),'cleanupRemoved':sorted(set(removed)),'independentReview':False,'softwareSignatureCreated':False,'notChecked':['SDK/HeraHub/native Android/runtime','real camera/calibration/image/capture/GNSS/base/PPK and field accuracy','real customer KML export corpus','terrain/flight dynamics/battery/obstacle/geofence/airspace clearance','physical powerloss/full-volume ENOSPC','malicious concurrent filesystem owner','cross-engine numerical portability','3D/terrain/absolute/relative altitude/hole-aware mission compiler','Fly integration and new software signing']}
with(E/'verification1.json').open('x')as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['results','cleanupRemoved','notChecked']}))
