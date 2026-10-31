from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/herastore50';sys.path.insert(0,str(R/'pilot/apstream40'));import guard as g
checks=[]
def check(n,v):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
b=json.loads((E/'preservation-before1.json').read_text());bad=g.bad(b['files']);check('all protected bytes match',not bad);check('ENDURE inventory unchanged',g.endure()==b['endureGuardPaths']);check('host20GiB floor',g.free()>=20*2**30)
counts={'host2':90,'adversarial1':23,'crash3':26,'browser4':36,'sourceguard1':6,'markup1':3}
for n,c in counts.items():
 j=json.loads((E/(n+'.json')).read_text());check(n+' pass/count',j['status']=='PASS'and j['checks']==c);check(n+' every case pass',len(j['results'])==c and all(x['pass']for x in j['results']))
pins=json.loads((E/'final-runtime-pins2.json').read_text())['files'];check('final pinned runtime/UI unchanged',not g.bad(pins))
syntax=[]
for p in sorted(H.glob('*.mjs')):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,r.returncode==0);syntax.append(p.name)
clean=[]
for fam,ns in [('host',range(1,3)),('adversarial',range(1,2)),('crash',range(1,4)),('browser',range(1,5)),('sourceguard',range(1,2))]:
 for i in ns:
  j=json.loads((E/f'{fam}-cleanup{i}.json').read_text());check(f'{fam}{i} scratch removed',all(not(R/p).exists()for p in j['removed']));clean.extend(j['removed'])
crash=json.loads((E/'crash3.json').read_text());check('five actual owned SIGKILL',len(crash['processes'])==5 and all(x['exit']['signal']=='SIGKILL'for x in crash['processes']))
br=json.loads((E/'browser4.json').read_text());check('actual distinct server PID restart',len(br['processes'])==2 and br['processes'][0]['pid']!=br['processes'][1]['pid'] and br['processes'][0]['exit']['code']==0);check('no browser JS/external requests',not br['errors']and not br['external'])
check('failed markup browser attempt retained',(E/'browser-failure1.json').is_file());check('earlier raw host evidence retained',(E/'host-retained1').is_dir());check('final raw host evidence retained',(E/'host-retained2').is_dir());check('targeted late-source replacement proof retained',(E/'sourceguard-retained1').is_dir());check('separate importer process proof passed',any('separate receiver process' in r['name']for r in json.loads((E/'adversarial1.json').read_text())['results']))
alloc=sum(p.stat().st_blocks*512 for d in[H,E]for p in d.rglob('*')if p.is_file());decision=json.loads((E/'resource-decision1.json').read_text());check('retained artifact96MiB revised budget',alloc<decision['refinedArtifactBudgetBytes']);check('initial48MiB admission record preserved',b['budgetBytes']==48*2**20 and decision['initialArtifactBudgetBytes']==48*2**20)
obj={'status':'PASS_SCOPED_HOST_MOCK','at':datetime.now(timezone.utc).isoformat(),'requirementCoverage':{'implemented':6,'total':6,'percent':100},'scenarioChecks':sum(counts.values()),'scenarioReceipts':counts,'verificationChecks':len(checks),'results':checks,'syntaxFiles':syntax,'protectedCount':len(b['files']),'endureCount':len(g.endure()),'allocatedBytes':alloc,'freeBytes':g.free(),'cleanupRemoved':sorted(set(clean)),'notChecked':['Physical powerloss/Android/HeraHub/SDK/MCU','Actual full-volume ENOSPC','Malicious competing filesystem owner','Off-host storage durability','Live49 store integration and automatic hot restore','Published-chain pruning / cold-vault reclamation'],'hostDiskSavingsClaim':False,'softwareSignatureCreated':False,'independentReview':False}
with(E/'verification1.json').open('x')as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in obj.items()if k not in['results','syntaxFiles','cleanupRemoved','notChecked']}))
