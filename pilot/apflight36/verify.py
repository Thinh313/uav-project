"""Small source/receipt verification only; no SDK, build, simulator or socket."""
from pathlib import Path
import hashlib,json,datetime,subprocess,re,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/apflight36';P=R/'pilot/apflight36';checks=[]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,v):checks.append({'name':name,'pass':bool(v)})
def latest(prefix):
    ps=[p for p in E.glob(prefix+'*.json') if re.fullmatch(prefix+r'\d+\.json',p.name)]
    return max(ps,key=lambda p:int(re.search(r'\d+',p.stem).group()))
logicPath=latest('logic');logic=json.loads(logicPath.read_text());replayPath=latest('replay');replay=json.loads(replayPath.read_text());n=int(re.search(r'\d+',replayPath.stem).group());corpusPath=E/f'corpus{n}.json';corpus=json.loads(corpusPath.read_text())
check('latest161logic checks PASS',logic['status']=='MOCK_HOST_PASS' and logic['checks']==logic['passed']==161)
check('logic hashes exact current code',all(h(R/p)==v for p,v in logic['sourceHashes'].items()))
check('latest33scenarios and5semantic bites PASS',replay['status']=='MOCK_PASS' and replay['replay']['caseCount']==33 and all(x['matched'] for x in replay['replay']['results']) and len(replay['bites'])==5 and all(b['rejected'] for b in replay['bites']))
check('replay code hashes exact current source',all(h(R/p)==v for p,v in replay['sourceHashes'].items()))
check('corpus IDs unique/bounded',len(corpus['cases'])==len({c['id'] for c in corpus['cases']})==33)
check('replay result operational flags false',all(r['operational'] is False for r in replay['replay']['results']))
out=subprocess.run(['node','--input-type=module','-e',"import{readFile}from'node:fs/promises';import{replayCorpus}from'./pilot/apflight36/corpus.mjs';const c=JSON.parse(await readFile(process.argv[1],'utf8'));console.log(JSON.stringify(await replayCorpus(c)));",str(corpusPath.relative_to(R))],cwd=R,text=True,capture_output=True)
check('independent invocation recomputes full replay (same-agent verification)',out.returncode==0)
if out.returncode==0:check('recomputed replay byte-equivalent to receipt',json.loads(out.stdout)==replay['replay'])
for name in ['common.mjs','geometry.mjs']:check('exact A35 base reuse '+name,h(P/'vendor'/name)==h(R/'pilot/airspace35/core'/name))
for name in ['qgc-created-geofence.plan','qgc-created-amsl-fence.plan']:check('exact actual QGC file reuse '+name,h(P/'fixtures'/name)==h(R/'app/fixtures/qgc/desktop'/name))
wire=json.loads((P/'wire-boundary.json').read_text());check('pinned XML schema source exact',h(R/wire['sourcePath'])==wire['sourceSha256']);check('no invented mockUUID on real wire',wire['mockTokenOnMAVLinkWire'] is False and wire['MAVLinkEncoderDecoder']=='NOT_IMPLEMENTED_APFLIGHT36' and wire['enums']['MAV_MISSION_TYPE_FENCE']=='1')
syntax=[]
for p in P.rglob('*.mjs'):
    o=subprocess.run(['node','--check',str(p)],text=True,capture_output=True);syntax.append({'path':str(p.relative_to(R)),'exit':o.returncode,'stderr':o.stderr})
check('all new JS syntax checks PASS',all(x['exit']==0 for x in syntax))
runtime='\n'.join(p.read_text() for p in P.glob('*.mjs') if p.name not in ['tests.mjs','replay.mjs','corpus.mjs'])
check('core has no socket/process/emulator/SITL/build import',not any(s in runtime for s in ['node:net','node:http','node:child_process','exec_command','createServer','spawn(']))
before=json.loads((E/'state-before.json').read_text());expected=json.loads((E/'preservation-before.json').read_text())['files'];deltas=[];historicalFailures=[]
for p,was in before['files'].items():
    q=R/p;now=h(q) if q.is_file() else None
    if now!=was:deltas.append({'path':p,'beforeSha256':was,'afterSha256':now})
    if now!=expected[p]:historicalFailures.append({'path':p,'expectedSha256':expected[p],'afterSha256':now,'status':'MISSING' if now is None else 'SHA_CHANGED'})
preserve={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'paths':len(before['files']),'observedBeforeToAfter':'PASS' if not deltas else 'FAIL','deltas':deltas,'historicalExpectedStatus':'FAIL' if historicalFailures else 'PASS','historicalDiscrepancies':historicalFailures,'restoredByTask':False,'continuousOriginalPaths':'NOT_CLAIMED'}
(E/'preservation-after.json').write_text(json.dumps(preserve,indent=2)+'\n')
check('no task-time changes to observed protected state',not deltas)
allocated=sum(p.stat().st_blocks*512 for root in [P,E] for p in root.rglob('*') if p.is_file())
check('source/corpus/evidence below8MiB budget',allocated<8*1024**2)
check('no owned build/runtime scratch',not any(P.glob('.build*')) and not any(P.glob('.qa*')))
status='MOCK_SCOPE_VERIFIED_WITH_PREEXISTING_PROTECTED_GAP' if all(c['pass'] for c in checks) and historicalFailures else 'MOCK_SCOPE_VERIFIED' if all(c['pass'] for c in checks) else 'FAIL'
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'checks':checks,'logicReceipt':str(logicPath.relative_to(R)),'replayReceipt':str(replayPath.relative_to(R)),'hostCheckCount':161+33+5,'syntax':syntax,'preservation':{'paths':len(before['files']),'newDeltas':len(deltas),'historicalDiscrepancies':len(historicalFailures),'fullHistoricalGate':'FAIL' if historicalFailures else 'PASS'},'operationalAllowed':False,'actualAPWireSITLAndroid':'NOT_CHECKED','newBuildAPK_Runtime_Signing':False,'wholeProjectCopies':0,'dependencyInstalls':0,'allocatedBytes':allocated,'freeBytes':shutil.disk_usage(R).free,'sameAgentReview':True}
attempt=1
while (E/f'verification{attempt}.json').exists():attempt+=1
(E/f'verification{attempt}.json').write_text(json.dumps(report,indent=2)+'\n');(E/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({**report,'checks':len(checks),'syntax':len(syntax)}));raise SystemExit(0 if all(c['pass'] for c in checks) else 1)
