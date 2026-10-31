"""Scoped execution of retained G17 runtime; never edits its source or receipts."""
from pathlib import Path
import hashlib,types,json,sys,shutil,os
R=Path(__file__).resolve().parents[2]
OLD=R/'pilot/beta06g17/flight/runtime.py'
source=OLD.read_text()
sys.path.insert(0,str(R/'pilot/betastability02'))
from companion import POLICY,task_usage,quota_decision
pins=json.loads((R/'evidence/betastability02/source-pins07.json').read_text())
assert hashlib.sha256(source.encode()).hexdigest()==pins['files'][str(OLD.relative_to(R))]
flightRoot=Path(os.environ['AERIS_BETA05_FLIGHT_ROOT']).resolve();assert flightRoot.is_relative_to(R/'evidence/betastability02') and flightRoot.name=='flight'
changes=[('evidence/beta06/generation17/flight',str(flightRoot.relative_to(R))),('evidence/beta06/generation17/flight-pins01.json','evidence/betastability02/source-pins07.json'),('aeris-beta06g17-','aeris-betastability02-'),('aeris.task=beta06g17','aeris.task=betastability02'),("!='beta06g17'","!='betastability02'"),("'aeris.task':'beta06g17'","'aeris.task':'betastability02'"),('5972','5984'),('if len(actual)>4:','if len(actual)>12:'),('if len(rows)>=4:','if len(rows)>=12:'),('if len(retained)>4','if len(retained)>12'),('29*2**30','20*2**30'),('free<28*2**30 or free-rate*15<20*2**30','free<10*2**30+256*2**20 or free-rate*15<10*2**30+256*2**20')]
for old,new in sorted(changes,key=lambda x:-len(x[0])):
 assert old in source,old
 source=source.replace(old,new)
entry_anchor="  created=runner.command(argv,'create');cid=created.strip()"
assert source.count(entry_anchor)==1,'EXACT_PRE_CREATE_QUOTA_SEAM'
source=source.replace(entry_anchor,"  check_entry_quota(root,rid,out)\n"+entry_anchor)
module=types.ModuleType('beta05_qualified_runtime');module.__file__=str(OLD)
exec(compile(source,str(OLD),'exec'),module.__dict__)
def quota(root):
 assert shutil.disk_usage(root).free>=10*2**30+256*2**20,'BETA05_FLOOR10_WITH_CLOSURE_RESERVE'
 return quota_decision(task_usage(root/'evidence/betastability02'))
def entry_quota(root,rid,out):
 usage=task_usage(root/'evidence/betastability02')
 try:result=quota_decision(usage,reserve=True)
 except Exception as e:
  module.put(out/'task-quota-rejection.json',{'format':'aeris-betastability02-task-quota-preallocation-rejection','run':rid,'usage':usage,'reservedFiles':POLICY['entryReserveFiles'],'reservedBytes':POLICY['entryReserveBytes'],'maxEvidenceFiles':POLICY['maxEvidenceFiles'],'evidenceBudgetBytes':POLICY['evidenceBudgetBytes'],'reason':str(e),'runtimeAllocated':False,'containerId':None,'automaticRetry':False});raise
 module.put(out/'task-quota-admission.json',{'run':rid,**result,'runtimeAllocated':False,'containerId':None})
 return result
module.check_quota=quota
module.check_entry_quota=entry_quota
if __name__=='__main__':sys.exit(module.run(sys.argv[1]))
