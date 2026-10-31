from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/heraswitch49';sys.path.insert(0,str(R/'pilot/apstream40'));import guard as g
checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
b=json.loads((E/'preservation-before1.json').read_text());bad=g.bad(b['files']);check('all protected paths byte-identical',not bad);check('ENDURE inventory unchanged',g.endure()==b['endureGuardPaths']);check('20GiB free floor',g.free()>=20*2**30)
counts={'host4':68,'adversarial3':32,'crash2':24,'browser4':35}
for name,count in counts.items():
 j=json.loads((E/(name+'.json')).read_text());check(name+' final PASS/count',j['status']=='PASS' and j['checks']==count);check(name+' every scenario passes',len(j['results'])==count and all(r['pass'] for r in j['results']))
pins=json.loads((E/'final-runtime-pins2.json').read_text())['files'];check('final runtime/test pins unchanged',not g.bad(pins))
for p in sorted(H.glob('*.mjs')):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,r.returncode==0)
clean=[]
for family,ns in [('host',range(1,5)),('adversarial',range(1,4)),('crash',range(1,3)),('browser',range(1,5))]:
 for n in ns:
  j=json.loads((E/f'{family}-cleanup{n}.json').read_text());check(f'{family}{n} owned scratch absent',all(not(R/p).exists() for p in j['removed']));clean.extend(j['removed'])
for name in ['browser-failure1','browser-failure2','browser-failure3','qa-adjustment1']:
 check(name+' retained', (E/(name+'.json')).is_file())
for name in ['host-retained4','adversarial-retained3','crash-retained2','browser4/retained-store']:
 check(name+' raw evidence retained', (E/name).is_dir())
crash=json.loads((E/'crash2.json').read_text());check('four actual owned process deaths',len(crash['processes'])==4 and all(x['exit']['signal']=='SIGKILL' for x in crash['processes']))
browser=json.loads((E/'browser4.json').read_text());check('actual browser server restart',len(browser['processes'])==2 and browser['processes'][0]['pid']!=browser['processes'][1]['pid'] and browser['processes'][0]['exit']['code']==0);check('browser no externalfetch or exceptions',not browser['errors'] and not browser['external'])
allocated=sum(p.stat().st_blocks*512 for d in [E,H] for p in d.rglob('*') if p.is_file());check('own32MiB artifact budget',allocated<32*2**20)
obj={'status':'PASS_SCOPED_HOST_MOCK','at':datetime.now(timezone.utc).isoformat(),'requirementCoverage':{'implemented':6,'total':6,'percent':100},'scenarioChecks':sum(counts.values()),'scenarioReceipts':counts,'verificationChecks':len(checks),'results':checks,'protectedCount':len(b['files']),'endureCount':len(g.endure()),'allocatedBytes':allocated,'freeBytes':g.free(),'cleanupRemoved':sorted(set(clean)),'notChecked':['Android/emulator/HeraHub/SDK/physicalMCU','Sudden host powerloss','Full-volume ENOSPC (injected instead)','Malicious external filesystem owner/multi-owner operation','Production/Fly integration and cleanup/reclamation'],'softwareSignatureCreated':False,'independentReview':False}
with (E/'verification1.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in obj.items() if k not in ['results','notChecked','cleanupRemoved']}))
