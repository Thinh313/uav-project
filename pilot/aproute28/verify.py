"""Read old state only; write A28 receipts/fingerprints only. No signing or campaign mutation."""
from pathlib import Path
import json,hashlib,re,subprocess,datetime,ast
R=Path(__file__).resolve().parents[2];E=R/'evidence/aproute28';checks=[]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
b=json.loads((E/'preservation-before.json').read_text())
for name,v in b['sets'].items():
 files=json.loads((R/v['inventory']).read_text())['files'];bad=[p for p,s in files.items() if not (R/p).is_file() or h(R/p)!=s];check(name+' frozen inventory',not bad,{'files':len(files),'mismatches':bad})
for label,files in [('918stable',b['stable']),('oldTrust',b['oldTrust'])]:
 bad=[p for p,s in files.items() if not (R/p).is_file() or h(R/p)!=s];check(label+' original bytes retained',not bad,{'files':len(files),'mismatches':bad})
a=json.loads((R/'evidence/endure27/candidate.json').read_text());freeze=json.loads((R/'evidence/endure20/freeze.json').read_text())['files']
for label,base in [('source140',R),('slot140',Path(a['slot']))]:
 bad=[x['path'] for x in freeze if not (base/x['path']).is_file() or h(base/x['path'])!=x['sha256']];check(label+' immutable payload',not bad,bad)
counts={}
for name,total in [('unit-tests.txt',33),('transport25-regression.txt',75),('protocol22-regression.txt',82),('transport26-regression.txt',25)]:
 text=(E/name).read_text();v={k:int(re.search(r'(?:ℹ|#) '+k+r' (\d+)',text).group(1)) for k in ['tests','pass','fail','cancelled','skipped']};counts[name]=v;check(name+' exact checks',v=={'tests':total,'pass':total,'fail':0,'cancelled':0,'skipped':0},v)
q=json.loads((E/'attempt05/qa.json').read_text());corpus=json.loads((E/'attempt05/corpus.json').read_text());check('actual routing61checks/12scenarios exact corpus',q['status']=='PASS' and len(q['checks'])==61 and all(x['pass'] for x in q['checks']) and len(corpus['scenarios'])==12 and q['scenarios']==[x['id'] for x in corpus['scenarios']] and q['corpusSha256']==h(E/'attempt05/corpus.json'))
replay=json.loads((E/'attempt05/raw-replay.json').read_text());check('raw3343receipt checks12scenarios',replay['status']=='PASS' and len(replay['checks'])==3343 and all(x['pass'] for x in replay['checks']) and replay['scenarios']==12 and replay['corpusSha256']==q['corpusSha256'])
check('standalone exports exact',all(json.loads((E/'attempt05'/(x['id']+'.json')).read_text())==x for x in corpus['scenarios']))
ci=json.loads((E/'candidate-integrity.json').read_text());check('actual signature/bootstrap/trust/664endpoint observation',ci['status']=='PASS' and ci['selectedSequence']==7 and ci['oldPhase']=='CANARY_FAILED' and ci['manifestSha256']==a['manifestSha256'] and ci['packageSha256']==a['packageSha256'] and ci['bootstrapFiles']==22 and len(ci['snapshots'])==3 and all(x['pass'] and x['files']==664 and x['sha256']==a['sourceSnapshotSha256'] for x in ci['snapshots']))
sources=json.loads((E/'sources.json').read_text())['sources'];check('three primary captures exact SHA',len(sources)==3 and all(x['status']=='CAPTURED' and h(R/x['path'])==x['sha256'] for x in sources))
launches=[]
for run in ['run01','run03','run04','run05']:
 l=json.loads((E/run/'simulator-launch.json').read_text());i=json.loads((E/run/'simulator-inspect.json').read_text());ports=i['HostConfig']['PortBindings'];valid=l['containerId']==i['Id'] and i['Config']['Labels'].get('aeris.task')=='aproute28' and i['HostConfig']['NanoCpus']==1000000000 and i['HostConfig']['Memory']==268435456 and set(ports)=={'5760/tcp','5762/tcp','5763/tcp'} and all(v[0]['HostIp']=='127.0.0.1' for v in ports.values()) and l['binarySha256']==h(R/'runtime/sitl/arducopter') and l['configSha256']==h(R/'pilot/aproute28/sitl.parm') and all((E/run/f).is_file() for f in ['simulator-log.txt','simulator-inspect.json']);launches.append({'run':run,'pass':valid,'id':i['Id']})
check('owned actual router lifecycle/binary/config/ports/resource bounds',all(x['pass'] for x in launches),launches)
cleanup=json.loads((E/'cleanup.json').read_text());check('only owned simulator/peers stopped and ports closed',cleanup['ownedContainerAbsent'] and all(x['closed'] for x in cleanup['ports']) and not cleanup['scratchCreated'])
check('four earlier failed/partial attempts retained unchanged',all(json.loads((E/('attempt0'+str(n))/'qa.json').read_text())['status']=='FAIL' for n in range(1,5)))
syntax=[]
for p in sorted((R/'pilot/aproute28').glob('*.mjs')):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);syntax.append({'path':str(p.relative_to(R)),'exitCode':r.returncode,'output':r.stdout+r.stderr})
for p in (R/'pilot/aproute28').glob('*.py'):ast.parse(p.read_text())
check('new JS/Python syntax',all(x['exitCode']==0 for x in syntax));(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
ok=all(x['pass'] for x in checks)
mapping=[{'id':'A28-'+f'{n:02d}','implemented':True,'verified':ok,'evidence':paths} for n,paths in [(1,['run04/simulator-launch.json','run04/simulator-inspect.json','attempt05/discovery-roundtrip.json']),(2,['attempt05/discovery-roundtrip.json','attempt05/concurrent-camera-target-isolation.json','attempt05/raw-replay.json']),(3,['unit-tests.txt','attempt05/gimbal-manager-device-isolation.json','attempt05/second-gimbal-device.json','attempt05/corruption-duplicate-tombstone.json']),(4,['attempt05/payload-bus-close.json','attempt05/manual-reconnect-no-resume.json','attempt05/payload-reboot.json','attempt05/ap-heartbeat-silence.json','attempt05/actual-ap-stop.json','attempt05/fresh-ap-boot-no-resume.json']),(5,['unit-tests.txt','attempt05/actual-router-evidence-bound.json','attempt05/raw-replay.json']),(6,['preservation-after.json','candidate-integrity.json','cleanup.json','transport25-regression.txt','protocol22-regression.txt','transport26-regression.txt'])]]
check('REQ evidence paths exist',all((E/p).is_file() for x in mapping for p in x['evidence']));ok=all(x['pass'] for x in checks)
result={'status':'READY_ISOLATED_ACTUAL_AP_ROUTING_SYNTHETIC_PAYLOADS' if ok else 'NOT_READY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requirements':{'implemented':6,'verified':6 if ok else None,'total':6,'mapping':mapping},'functionalChecks':{'newUnit':33,'actualRouting':61,'T25Regression':75,'P22Regression':82,'T26Regression':25,'canonicalTotal':276,'finalFailures':0 if ok else None,'skips':0},'rawReplay':{'receiptAssertions':3343,'scenarios':12,'corpusSha256':q['corpusSha256']},'metadataChecks':checks,'limits':['Synthetic payloads/no actual images/causal execution/Hera capacity','Inner broker remains MOCK; outer evidence proves host AP serial routing','Peer loss inferred from heartbeat absence; remote unsigned late same-key freshness not authenticated','Raw bound scenario explicitly incomplete','No APproxy camera backend/mission flight/Fly/native/SDK/HIL/hardware/24h/release signing acceptance'],'review':'Single-agent sequential specification/build/verify, not independent audit; previous path incidents retained'}
(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
files=[p for p in (R/'pilot/aproute28').rglob('*') if p.is_file()]+[R/'delivery/TIP-APROUTE28.md',R/'delivery/COMPLETION-APROUTE28.md',R/'docs/ADR-037-ACTUAL-ARDUPILOT-PAYLOAD-ROUTING.md']
(E/'module-fingerprints.json').write_text(json.dumps({'at':result['at'],'files':{str(p.relative_to(R)):h(p) for p in sorted(files)},'scope':'New isolated module/document metadata only; no frozen baseline replacement or software signature'},indent=2)+'\n')
evidence={str(p.relative_to(R)):h(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='evidence-fingerprints.json'};(E/'evidence-fingerprints.json').write_text(json.dumps({'at':result['at'],'files':evidence},indent=2)+'\n')
print(result['status'],len(checks),'metadata gates',sum(not x['pass'] for x in checks),'failures')
if not ok:print(json.dumps([x for x in checks if not x['pass']],indent=2));raise SystemExit(1)
