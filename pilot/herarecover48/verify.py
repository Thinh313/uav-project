from pathlib import Path
import json,sys,subprocess,hashlib,os
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/herarecover48';sys.path.insert(0,str(R/'pilot/apstream40'));import guard as g
checks=[]
def check(n,v):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
b=json.loads((E/'preservation-before1.json').read_text());bad=g.bad(b['files']);check('all protected bytes match after authorized restoration',not bad);check('ENDURE inventory same',g.endure()==b['endureGuardPaths']);check('host20GiB floor',g.free()>=20*2**30)
for n,c in [('tests4',72),('corpus1',24),('crash1',10),('browser5',30)]:
 j=json.loads((E/(n+'.json')).read_text());check(n+' receipt pass/count',j['status']=='PASS' and j['checks']==c)
 if 'results'in j:check(n+' every result passed',len(j['results'])==c and all(r['pass'] for r in j['results']))
syntax=[]
for p in sorted(H.glob('*.mjs')):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,r.returncode==0);syntax.append(p.name)
for name in ['tests-cleanup1','tests-cleanup2','tests-cleanup3','tests-cleanup4','crash-cleanup1','browser-cleanup3','browser-cleanup4','browser-cleanup5']:
 j=json.loads((E/(name+'.json')).read_text());check(name+' scratch removed',all(not(R/p).exists() for p in j['removed']))
check('failed start2 no scratch directory',not (R/'.local/herarecover48-browser2').exists());check('failed start1 no scratch directory',not(R/'.local/herarecover48-browser1').exists())
rest=json.loads((E/'restoration-receipt1.json').read_text());check('53 exact authorized restorations recorded',len(rest['restored'])==53 and all(g.sha(R/r['path'])==r['sha256'] for r in rest['restored']));check('incident not erased',(E/'preservation-incident1.json').exists() and rest['continuousOriginalPathPresenceClaim']is False)
allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file());check('own artifact budget32MiB',allocated<32*2**20)
obj={'status':'PASS_SCOPED_HOST_MOCK','at':datetime.now(timezone.utc).isoformat(),'requirementCoverage':{'implemented':6,'total':6,'percent':100},'scenarioChecks':136,'verificationChecks':len(checks),'results':checks,'syntaxFiles':syntax,'protectedCount':len(b['files']),'endureCount':len(g.endure()),'freeBytes':g.free(),'allocatedBytes':allocated,'notChecked':['Android/emulator/HeraHub/realMCU','Host sudden powerloss','Full-volume ENOSPC (injected failures only)','Malicious external filesystem writer','Active47/Fly integration and production cleanup'],'sourceAuthentication':False,'independentReview':False,'continuousOriginalPathPresenceClaim':False}
with(E/'verification1.json').open('x')as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in obj.items()if k not in ['results','syntaxFiles','notChecked']}))
