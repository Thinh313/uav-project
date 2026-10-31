from pathlib import Path
import json,importlib.util,subprocess
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/herapersist47';s=importlib.util.spec_from_file_location('g40',R/'pilot/apstream40/guard.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks=[]
def check(n,v):
 assert v,n
 checks.append({'name':n,'pass':True})
def read(n):return json.loads((E/n).read_text())
check('initial20GiB floor',g.free()>20*2**30+2**20)
b=read('preservation-before1.json');bad=g.bad(b['files']);same=g.endure()==b['endureGuardPaths'];check('14216 protectedSHA unchanged',len(b['files'])==14216 and not bad);check('ENDURE5051 inventory/bytes same',same and len(g.endure())==5051)
check('model15 finalcommit token/revision source',read('model3.json')['checks']==15 and read('model3.json')['passed']==15)
check('25actualJVM CAS/SIGKILL/faultchecks',read('journal1.json')['checks']==25 and read('journal1.json')['status']=='PASS')
check('19adversarial/quota/orphanchecks',read('adversarial1.json')['checks']==19 and read('adversarial1.json')['passed']==19)
br=read('browser2.json');check('22actualbrowser finalsource/serverrestartchecks',br['checks']==22 and br['status']=='PASS');check('no externalrequest orJSexception',not br['errors'] and not br['external'])
for n in [1,2]:
 c=read(f'browser-cleanup{n}.json');check('browser cleanup'+str(n),c['browserClosed'] and all(p['exit']['code']==0 for p in c['processes']) and not (R/c['removed'][0]).exists())
check('JVM scratch removed andchildclosed',read('journal-cleanup1.json')['ownedChildClosed'] and not (R/'.local/herapersist47-qa1').exists())
check('orphan scratch removed',not (R/'.local/herapersist47-orphan-qa').exists())
cold=read('cold1.json');check('45corpus76/46export/47JVM coldreplay',cold['status']=='PASS' and cold['protected45Cases']==76 and cold['protected46ExportReplay'] and cold['ownJVMRestoredReplay'])
check('actualtwo finalserverPIDs',len(br['processes'])==2 and br['processes'][0]['pid']!=br['processes'][1]['pid'])
for n in ['before-restart-1280.png','restored-mapping-1280.png','review-1280.png','review-1024.png','review-360.png']:check('screenshot '+n,(E/'browser2'/n).is_file())
der=read('derivation-pins.json');check('original46assetSHAs unchanged',all(g.sha(R/x['source'])==x['sourceSha256'] for x in der['files']))
syntax=[]
for p in H.glob('*.mjs'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,r.returncode==0);syntax.append(p.name)
allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file());check('namespace16MiB and20GiB floor',allocated<16*2**20-65536 and g.free()>20*2**30+2**20)
out={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS_SCOPED_HOST_WORKSPACE_PERSISTENCE','checks':len(checks),'results':checks,'requirements':{'passed':8,'total':8,'ids':['R47-0'+str(i) for i in range(1,9)],'scope':'Host/mock only not productreadinesspercentage'},'sourceFingerprints':{str(p.relative_to(R)):g.sha(p) for p in H.rglob('*') if p.is_file()},'preservation':{'protectedCount':len(b['files']),'failures':bad,'endureCount':len(g.endure()),'endureUnchanged':same},'resources':{'freeBytes':g.free(),'allocatedBytes':allocated,'floorBytes':20*2**30,'sourceEvidenceBudgetBytes':16*2**20,'operatorStoreBudgetBytes':16*2**20},'syntaxFiles':len(syntax),'scopeLimits':{'actualAndroidHeraSDK':'NOT_CHECKED','actualPhysicalPowerLoss':'NOT_CHECKED','actualHostDiskFullENOSPC':'NOT_CHECKED','newAPK':False,'newSignature':False,'newSITL':False,'ENDURE24hAcceptance':'NOT_ACHIEVED_BY_THIS_TASK','independentReview':False}}
n=1
while (E/f'verification{n}.json').exists():n+=1
with (E/f'verification{n}.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'syntaxFiles':len(syntax),'freeGiB':g.free()/2**30,'allocatedBytes':allocated,'protectedFailures':len(bad)}))
