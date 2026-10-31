"""Prelaunch evidence only; no24h PASS or old receipt rewrite."""
from pathlib import Path
import json,hashlib,re,datetime,subprocess,ast
R=Path(__file__).resolve().parents[2];E=R/'evidence/endure27';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
b=json.loads((E/'preservation-before.json').read_text())
for name,v in b['sets'].items():
 pins=json.loads((R/v['inventory']).read_text())['files'];bad=[p for p,s in pins.items() if not (R/p).is_file() or h(R/p)!=s];check(name+'existing inventory exact',not bad,{'files':len(pins),'mismatches':bad})
bad=[p for p,s in b['stable'].items() if not (R/p).is_file() or h(R/p)!=s];check('all914oldattempt/data/stable bytes retained',not bad,{'count':len(b['stable']),'mismatches':bad})
bad=[p for p,s in b['oldTrust'].items() if not (R/p).is_file() or h(R/p)!=s];check('oldtrust events never rewritten',not bad,bad)
diagnosis=json.loads((E/'diagnosis.json').read_text());check('macOS sleep source capture bound to original failed request',diagnosis['powerSourceSha256']==h(E/'power-log-incident.txt') and diagnosis['originalRequest']['error']=='fetch failed' and diagnosis['originalRequest']['expectedDisconnect']==False)
u=(E/'unit-attempt02.txt').read_text();check('22new guard/actualHTTP tests PASS',all(re.search(r'ℹ '+key+' '+str(value)+r'\b',u) for key,value in [('tests',22),('pass',22),('fail',0),('skipped',0)]))
core=(E/'core-regression.txt').read_text();check('387core tests PASS/0fail/0skip',all(re.search(r'ℹ '+key+' '+str(value)+r'\b',core) for key,value in [('tests',387),('pass',387),('fail',0),('skipped',0)]))
control=json.loads((E/'controls-regression.json').read_text());check('99layout/offline controls PASS',len(control['checks'])==99 and all(c['pass'] for c in control['checks']))
build=json.loads((E/'power-build.json').read_text());check('native C source/binary exact successful compile',h(R/'pilot/endure27/power-observer')==build['binarySha256'] and h(R/'pilot/endure27/power-observer.c')==build['sourceSha256'])
smoke=json.loads((E/'native-role-smoke.json').read_text());check('actual IOKit READY/HEARTBEAT/process/fsync/cleanstop',smoke['before']['last']['kind']=='READY' and smoke['fresh']['last']['kind']=='HEARTBEAT' and smoke['end']=={'code':0,'signal':None})
injected=[json.loads(l) for l in (E/'native-injected.jsonl').read_text().splitlines()];check('synthetic native events labeled testMode and never promoted',all(x['testMode'] for x in injected) and [x['kind'] for x in injected]==['READY','SYSTEM_WILL_SLEEP','SYSTEM_HAS_POWERED_ON','STOPPED'])
death=json.loads((E/'native-death-test.json').read_text());check('actual ownobserver death causes failclosed',death['pass'] and death['end']['signal']=='SIGKILL')
probe=json.loads((E/'probe02-qa.json').read_text());check('6shortcanary checks PASS/156records/120reads/27packages',len(probe['checks'])==6 and all(c['pass'] for c in probe['checks']) and len(json.loads((E/'probe02-packages.json').read_text()))==27 and json.loads((E/'probe02-http.json').read_text())['attempts']==120)
prepare=json.loads((E/'campaign-prepare-qa.json').read_text());check('fresh generation05prepare exact signed9/664source/copy validated',len(prepare['checks'])==6 and all(c['pass'] for c in prepare['checks']))
candidate=json.loads((E/'candidate.json').read_text());old=json.loads((R/'evidence/endure20/candidate.json').read_text());check('same signed9/no signature change/new generation05',candidate['packageSha256']==old['packageSha256'] and candidate['manifestSha256']==old['manifestSha256'] and candidate['updateDirectory'].endswith('generation05') and candidate['planSha256']!=old['planSha256'])
syntax=[]
for p in (R/'pilot/endure27').glob('*.mjs'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);syntax.append({'path':str(p.relative_to(R)),'exitCode':r.returncode,'output':r.stdout+r.stderr})
for p in (R/'pilot/endure27').glob('*.py'):ast.parse(p.read_text())
check('allnewJS/Python syntax pass',all(x['exitCode']==0 for x in syntax));(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
check('scratch removed/probe01failure preserved',not (R/'.local/endure27/test-scratch').exists() and (E/'probe-attempt01/probe-qa.json').exists() and any(not x['pass'] for x in json.loads((E/'probe-attempt01/probe-qa.json').read_text())['checks']))
sources=json.loads((E/'sources.json').read_text())['sources'];check('originalApple source captured/hash',len(sources)==1 and all(h(R/x['path'])==x['sha256'] for x in sources))
pins={str(p.relative_to(R)):h(p) for p in sorted((R/'pilot/endure27').rglob('*')) if p.is_file()}
oldpins=json.loads((R/'evidence/endure20/controller-pins.json').read_text())['files'];pins.update(oldpins)
(E/'controller-pins.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'scope':'New externalcontroller/nativebinary plus5unchangedlegacyhelpers; app140/signed9 unchanged'},indent=2)+'\n')
result={'status':'READY_NEW_CAMPAIGN_PENDING_LIVE_POWER' if all(x['pass'] for x in checks) else 'NOT_READY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requirements':{'implemented':6,'verifiedPreparation':5 if all(x['pass'] for x in checks) else None,'total':6,'pending':'E27-06 liveAC/openlid/native admission and actual new24h run'},'canonicalPrelaunchChecks':{'newUnit':22,'core':387,'controls':99,'shortCanaryAssertions':6,'total':514,'finalFailure':0},'checks':checks,'notChecked':['Actual24h with new native sleepguard','Physical forced sleep under guard/HeraHubSDK/HIL/flight','Flyintegration/newsoftware-signature'],'scope':'Prelaunch preparation only, not24h acceptance; oldintervals excluded, hostsleep observed/exactoldsocketcause unknown. Single-agent review.'};(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'metadata gates',sum(not x['pass'] for x in checks),'failures')
if any(not x['pass'] for x in checks):print(json.dumps([x for x in checks if not x['pass']],indent=2));raise SystemExit(1)
