"""New TRANSPORT26 receipts only; existing inventories/state are read-only."""
from pathlib import Path
import json,hashlib,re,subprocess,datetime,ast
R=Path(__file__).resolve().parents[2];E=R/'evidence/transport26';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
b=json.loads((E/'preservation-before.json').read_text())
for name,v in b['sets'].items():
 pins=json.loads((R/v['inventory']).read_text())['files'];bad=[p for p,s in pins.items() if not (R/p).is_file() or h(R/p)!=s];check(name+' existing inventory exact',not bad,{'files':len(pins),'mismatches':bad})
bad=[p for p,s in b['stable'].items() if not (R/p).is_file() or h(R/p)!=s];check('candidate/controller/failure/raw/trust/SOT/roadmap bytes exact',not bad,{'files':len(b['stable']),'mismatches':bad})
c=json.loads((R/'evidence/endure20/candidate.json').read_text());freeze=json.loads((R/'evidence/endure20/freeze.json').read_text())['files']
for label,base in [('source',R),('immutable candidate slot',Path(c['slot']))]:
 bad=[x['path'] for x in freeze if not (base/x['path']).is_file() or h(base/x['path'])!=x['sha256']];check(label+'140frozen files exact',not bad,bad)
failure=json.loads((E/'endure-failure-preservation.json').read_text());progress=json.loads((R/'evidence/endure20/progress.json').read_text());check('failed campaign retained/selected7/full664endpoint SHA preserved',progress==b['progress'] and progress['status']=='FAILED' and failure['selectedSequence']==7 and failure['match'] and failure['originalSha256']==c['sourceSnapshotSha256'] and failure['copySha256']==c['sourceSnapshotSha256'])
check('no acceptance/selected9/writer recovery',all(not (R/'evidence/endure20'/x).exists() for x in ['acceptance.json','raw-replay.json','post-soak-packages.json']) and not (R/'.local/trust16/state/.writer.lock').exists())
def count(n,expected):
 s=(E/n).read_text();v={k:int(re.search(r'(?:ℹ|#) '+k+r' (\d+)',s).group(1)) for k in ['tests','pass','fail','skipped']};check(n+' exact test result',v=={'tests':expected,'pass':expected,'fail':0,'skipped':0},v)
for n,total in [('unit-attempt03.txt',25),('transport25-regression.txt',75),('protocol22-regression.txt',67),('protocol22-gate-regression.txt',15)]:count(n,total)
q=json.loads((E/'network-qa.json').read_text());corpus=json.loads((E/'network-corpus.json').read_text());check('45functional network checks/8scenario IDs and SHA',q['status']=='PASS' and len(q['checks'])==45 and all(x['pass'] for x in q['checks']) and len(corpus['scenarios'])==8 and q['scenarios']==[x['id'] for x in corpus['scenarios']] and q['corpusSha256']==h(E/'network-corpus.json'))
replay=json.loads((E/'raw-replay.json').read_text());check('raw receipt replay2288assertions/8scenarios exact corpus SHA',replay['status']=='PASS' and replay['scenarios']==8 and len(replay['checks'])==2288 and all(x['pass'] for x in replay['checks']) and replay['corpusSha256']==h(E/'network-corpus.json'))
check('scenario exports match corpus exactly',all(json.loads((E/(x['id']+'.json')).read_text())==x for x in corpus['scenarios']))
check('actual fresh disarmed heartbeat each scenario/no aircraft writes or media',all(x['review']['aircraft'] and x['review']['aircraft']['system']==42 and not x['review']['aircraft']['fields']['base_mode']&128 and x['review']['aircraftWrites']==0 and not x['review']['physicalMediaVerified'] and not x['review']['causalExecutionProven'] for x in corpus['scenarios']))
sources=json.loads((E/'sources.json').read_text())['sources'];check('two official original source captures/SHA',len(sources)==2 and all(h(R/x['path'])==x['sha256'] for x in sources))
cleanup=json.loads((E/'cleanup.json').read_text());check('only owned simulator stopped/portsclosed/bytecode removed',cleanup['ownedContainerAbsent'] and cleanup['taskPycacheAbsent'] and all(x['closed'] for x in cleanup['ports']))
check('earlier failed/partial receipts retained',all((E/x).exists() for x in ['network-attempt01.txt','network-attempt03.txt','raw-replay-attempt01.txt','raw-replay-attempt02.txt','attempt01/network-corpus.json','attempt03/network-corpus.json','attempt04/network-corpus.json']))
syntax=[]
for p in (R/'pilot/transport26').glob('*.mjs'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);syntax.append({'path':str(p.relative_to(R)),'exitCode':r.returncode,'output':r.stdout+r.stderr})
for p in (R/'pilot/transport26').glob('*.py'):ast.parse(p.read_text())
check('JS/Python syntax without compiled scratch',all(x['exitCode']==0 for x in syntax));(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
pins={str(p.relative_to(R)):h(p) for p in sorted((R/'pilot/transport26').rglob('*')) if p.is_file()}
for n in ['delivery/TIP-TRANSPORT26.md','docs/ADR-035-LOOPBACK-SITL-PAYLOAD-TRANSPORT.md','delivery/COMPLETION-TRANSPORT26.md','delivery/ENDURE20-FAILED-G04-20261013.md']:pins[n]=h(R/n)
(E/'module-fingerprints.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'scope':'New isolated module only; does not replace frozen/old inventories'},indent=2)+'\n')
result={'status':'READY_ISOLATED_LOOPBACK_SITL_HEARTBEAT_SYNTHETIC_NETWORK_PAYLOAD' if all(x['pass'] for x in checks) else 'NOT_READY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requirements':{'implemented':6,'verified':6 if all(x['pass'] for x in checks) else None,'total':6,'scope':'Host loopback only; camera/gimbal are network fixtures, noAPpayload execution'},'functionalTests':{'newUnit':25,'networkAssertions':45,'transport25Regression':75,'protocol22Regression':82,'canonicalTotal':227,'finalFailures':0,'skipped':0},'rawReplayReceiptAssertions':2288,'rawReplayScenarios':8,'metadataChecks':checks,'endureStatus':'FAILED_NO24H_ACCEPTANCE','selectedSequence':7,'notChecked':['AP same-component proxy/network multi-link/authenticated radio transport','HeraHub/nativeinstalled/SDK/physical input/video/images/payload capacity','Airborne payload/HIL/flight execution/RAGASsame-deviceAB','ENDURE20recovery/new campaign/24h acceptance/Fly integration/signing'],'review':'Single-agent sequential implementation and verification, not independent audit','scope':'Endpoint byte identity only, no continuous original-path assertion; failed/incomplete evidence retained'};(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'metadata gates',sum(not x['pass'] for x in checks),'failures')
if any(not x['pass'] for x in checks):print(json.dumps([x for x in checks if not x['pass']],indent=2));raise SystemExit(1)
