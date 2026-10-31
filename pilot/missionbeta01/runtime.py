"""Scoped execution of retained G17 runtime; never edits its source or receipts."""
from pathlib import Path
import hashlib,types,json,sys,shutil,os
R=Path(__file__).resolve().parents[2]
OLD=R/'pilot/beta06g17/flight/runtime.py'
source=OLD.read_text()
pins=json.loads((R/'evidence/missionbeta01/source-pins07.json').read_text())
assert hashlib.sha256(source.encode()).hexdigest()==pins['files'][str(OLD.relative_to(R))]
flightRoot=Path(os.environ['AERIS_BETA05_FLIGHT_ROOT']).resolve();assert flightRoot.is_relative_to(R/'evidence/missionbeta01') and flightRoot.name=='flight'
changes=[('evidence/beta06/generation17/flight',str(flightRoot.relative_to(R))),('evidence/beta06/generation17/flight-pins01.json','evidence/missionbeta01/source-pins07.json'),('aeris-beta06g17-','aeris-missionbeta01-'),('aeris.task=beta06g17','aeris.task=missionbeta01'),("!='beta06g17'","!='missionbeta01'"),("'aeris.task':'beta06g17'","'aeris.task':'missionbeta01'"),('5972','5984'),('if len(actual)>4:','if len(actual)>12:'),('if len(rows)>=4:','if len(rows)>=12:'),('if len(retained)>4','if len(retained)>12'),('29*2**30','20*2**30'),('free<28*2**30 or free-rate*15<20*2**30','free<10*2**30+256*2**20 or free-rate*15<10*2**30+256*2**20')]
for old,new in sorted(changes,key=lambda x:-len(x[0])):
 assert old in source,old
 source=source.replace(old,new)
module=types.ModuleType('beta05_qualified_runtime');module.__file__=str(OLD)
exec(compile(source,str(OLD),'exec'),module.__dict__)
def quota(root):
 e=root/'evidence/missionbeta01'
 assert shutil.disk_usage(root).free>=10*2**30+256*2**20,'BETA05_FLOOR10_WITH_CLOSURE_RESERVE'
 files=[p for p in e.rglob('*') if p.is_file()]
 assert len(files)<=5000 and sum(p.stat().st_size for p in files)<2048*2**20,'BETA05_TASK_QUOTA'
module.check_quota=quota
if __name__=='__main__':sys.exit(module.run(sys.argv[1]))
