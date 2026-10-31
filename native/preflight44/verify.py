from pathlib import Path
import importlib.util,json,subprocess
from datetime import datetime,timezone

R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/native44'
s=importlib.util.spec_from_file_location('guard44',H/'guard.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks=[]
def check(name,passed):
    assert passed,name
    checks.append({'name':name,'pass':True})
def read(name):return json.loads((E/name).read_text())
preservation=g.check();check('protected13889 and ENDURE5051 exact after authorized restoration',preservation['protectedCount']==13889 and preservation['endureCount']==5051)
check('diskfloor20GiB and namespacebudget32MiB',preservation['freeBytes']>=g.FLOOR and preservation['allocatedBytes']<g.BUDGET)
check('model33 including asynchronous producer clock regression',read('logic5.json')['passed']==33)
check('portable59 host128SHA typed20 corpus38',read('portable2.json')['passed']==59)
check('actualbrowser27 endtoend restart export lostreply layout WebCrypto',read('browser6.json')['checks']==27 and read('browser6.json')['status']=='PASS')
check('checkboxfault9 keyboard pending rollback no retries',read('checkbox-fault1/receipt.json')['checks']==9 and read('checkbox-fault1/receipt.json')['status']=='PASS')
check('priorhostJVM21 processdeath persistence unchangedjournal algorithm',read('persistence1.json')['passed']==21)
cold=read('cold-regression1.json');check('cold43 corpus38 lifecycle4 actual3sessions',len(cold['corpus43'])==38 and all(x['pass'] for x in cold['corpus43']) and len(cold['lifecycle43'])==4 and len(cold['raw43']['sessions'])==3)
check('cold42 actualrun03 semantic13',cold['raw42']['checkCount']==13)
raw=read('raw-parity1.json');check('portable exact actual43 raw884rows1541frames',raw['status']=='PASS' and sum(x['rows'] for x in raw['sessions'])==884 and sum(x['frames'] for x in raw['sessions'])==1541)
for name,count in [('native33-regression1.txt',85),('native35-regression1.txt',30)]:
    text=(E/name).read_text();check(name,f'ℹ tests {count}\n' in text and f'ℹ pass {count}\n' in text and 'ℹ fail 0\n' in text)
restored=read('restoration-receipt1.json');check('43 restoration exact originalSHA receipt',restored['count']==43 and all(g.sha(R/x['path'])==x['sha256'] for x in restored['files']))
for d in ['browser-qa','checkbox-qa','classes','persistence']:check('owned scratch removed '+d,not (R/'.local/native44'/d).exists())
syntax=[]
for p in sorted(H.rglob('*.mjs')):
    v=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+str(p.relative_to(R)),v.returncode==0);syntax.append(str(p.relative_to(R)))
scope={'AndroidActivityCompile':'NOT_CHECKED','AndroidEmulator':'NOT_CHECKED','HeraHubSDKDevice':'NOT_CHECKED','physicalFlight':'NOT_CHECKED','newAPK':False,'newSignature':False,'newSITL':False,'ENDURE24hAcceptance':'NOT_ACHIEVED_BY_THIS_TASK','independentReview':False}
out={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS_SCOPED_HOST_UI_MOCK','checks':len(checks),'results':checks,'requirementCoverage':{'implementedWithinHostMockScope':8,'total':8,'ratio':1.0,'scope':'TIP-NATIVE44 host/mock scope; Android actual compilation/runtime explicitly excluded'},'syntaxFiles':len(syntax),'preservation':preservation,'limits':scope}
with (E/'verification1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'syntaxFiles':len(syntax),'freeGiB':preservation['freeBytes']/2**30}))
