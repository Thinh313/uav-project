"""Independent pure boundary checks; no priming/device/process execution."""
from pathlib import Path
from importlib import import_module
import json,hashlib,ast,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-entry10.host';p=import_module(H+'.policy');a=import_module(H+'.admission');old=import_module('pilot.betaintegrated01.runtime02.journal.admission');G=2**30;M=2**20;tests=[]
def ok(name,v):assert v,name;tests.append({'id':name,'pass':True})
source=(R/'pilot/betaintegrated01/runtime02/journal/admission.py').read_text();new=(R/'planning/betaintegrated01/cockpit05-entry10/host/admission.py').read_text();expected=source.replace('free_bytes>=20*GIB','free_bytes>=10*GIB').replace('free_bytes<20*GIB','free_bytes<10*GIB').replace('ENTRY_BELOW20_GIB','ENTRY_BELOW10_GIB').replace("'entryBytes': 20*GIB","'entryBytes': 10*GIB")
ok('guardonlyexplicitentryconstantcomparisonlabels',new==expected);ok('allotherdiskpolicyexact',{k:v for k,v in a.DISK_POLICY.items()if k!='entryBytes'}=={k:v for k,v in old.DISK_POLICY.items()if k!='entryBytes'})
b=p.task_budget();u=p.ui_budget();ok('wholequotaformula',b['requiredFreeBytes']==b['taskHardPeakBytes']+10*G+256*M);ok('whole30notadmittedat13point2',p.task_budget(132*G//10)['admitted']is False);ok('runtimeentry10notyetwired',b['selectedRuntimeMigration'].startswith('NOT_WIRED'))
for label,fn,r in [('long',p.task_budget,b['requiredFreeBytes']),('UI',p.ui_budget,u['requiredFreeBytes'])]:
 for d in(-1,0,1):ok(label+'exactboundary'+str(d),fn(r+d)['admitted']is(d>=0))
 for v in(True,False,10.2,'13',None,-1,2**63):
  if v is None:continue
  try:fn(v);reject=False
  except ValueError:reject=True
  ok(label+'badtypevalue'+repr(v),reject)
ok('UIentryis10butfloorbudgethigher',u['entryBytes']==10*G and u['requiredFreeBytes']>10*G+256*M and u['APOrFlightAuthorizedByThisBudget']is False and u['maximumSeconds']==900)
for label,free,prime,reason in [('belowreserve',10*G+256*M-1,True,'FLOOR10_RESERVE256'),('notprimed',13*G,False,'NOT_REAL_15S_PRIMED')]:
 try:a.ForecastWindow().observe(0,free,priming=prime);reject=False
 except a.DiskGuardError as e:reject=reason in str(e)
 ok(label,reject)
x=old.ForecastWindow();y=a.ForecastWindow()
for tick in range(152):
 ns=tick*100000000;free=13*G-tick*1000;one=x.observe(ns,free,priming=tick<=150);two=y.observe(ns,free,priming=tick<=150);assert one==two
ok('forecastsame152puremathobservations',True)
paths=[R/'planning/betaintegrated01/cockpit05-entry10/host'/n for n in('policy.py','admission.py')];r={'status':'PASS_PURE_ENTRY10_POLICY_NOT_RUNTIME_ADMISSION','tests':tests,'longRequiredBytes':b['requiredFreeBytes'],'longRequiredGiB':b['requiredFreeBytes']/G,'UIRequiredBytes':u['requiredFreeBytes'],'UIRequiredGiB':u['requiredFreeBytes']/G,'sourcePins':{str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest()for x in paths},'actualPrimeRuns':0,'servicesOrADB':0,'actualThirtyMinuteAccepted':False,'scope':'Puremath/sourceequivalence only; newguard retainsreal15sprime requirement but thisQAdoesnotexecuteit. Full30mstillbudgetnotfitat13.2GiB andruntimeentry10migrationunwired.'};(R/'evidence/betaintegrated01-cockpit05-entry10/qa/policy01.json').open('x').write(json.dumps(r,indent=2)+'\n');print(r['status'],len(tests),r['longRequiredGiB'],r['UIRequiredGiB'])
