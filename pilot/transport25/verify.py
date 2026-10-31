"""Preservation/source/test receipts for isolated TRANSPORT25; never updates frozen state."""
from pathlib import Path
import json,hashlib,datetime,re,subprocess
R=Path(__file__).resolve().parents[2];E=R/'evidence/transport25';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=json.loads((E/'preservation-before.json').read_text());checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
for name,v in before['sets'].items():
 pins=json.loads((R/v['inventory']).read_text())['files'];bad=[p for p,s in pins.items() if not (R/p).is_file() or h(R/p)!=s];check(name+' frozen/pilot baseline exact',not bad,{'count':len(pins),'mismatches':bad})
check('candidate/launch/canonical SOT/roadmap bytes unchanged',all((R/p).is_file() and h(R/p)==s for p,s in before['stable'].items()))
c=json.loads((R/'evidence/endure20/candidate.json').read_text());f=json.loads((R/'evidence/endure20/freeze.json').read_text())['files']
for label,base in [('frozen source',R),('candidate slot',Path(c['slot']))]:
 bad=[x['path'] for x in f if not (base/x['path']).is_file() or h(base/x['path'])!=x['sha256']];check(label+'140 files exact',not bad,bad)
p=json.loads((R/'evidence/endure20/progress.json').read_text());lock=json.loads((R/'.local/trust16/state/.writer.lock').read_text());check('same continuous campaign/PIDs/manifest/writer lock/0errors',p['status']=='RUNNING_NOT_FINAL' and p['startedAt']==before['progress']['startedAt'] and p['manifestSha256']==before['progress']['manifestSha256'] and p['pid']==before['progress']['pid'] and p['childPid']==before['progress']['childPid'] and lock==before['lock'] and p['totals']['errors']==0)
age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(p['checkedAt'].replace('Z','+00:00'))).total_seconds();check('progress fresh<=90s',0<=age<=90,{'ageSeconds':age});live=json.loads((E/'runtime-observation.json').read_text());check('live HTTP/process identity observed',live['statusCode']==200 and live['live']['manifestSha256']==c['manifestSha256'] and str(p['pid']) in live['processes'] and str(p['childPid']) in live['processes'])
def count(name,expected):
 s=(E/name).read_text();counts={k:int(re.search(r'(?:ℹ|#) '+k+r' (\d+)',s).group(1)) for k in ['tests','pass','fail','skipped']};check(name+' exact counts',counts=={'tests':expected,'pass':expected,'fail':0,'skipped':0},counts)
count('unit-attempt05.txt',75);count('protocol22-regression.txt',82)
qa=json.loads((E/'browser-qa.json').read_text());check('31 browser gates pass',len(qa['checks'])==31 and all(x['pass'] for x in qa['checks']))
corpus=json.loads((R/'pilot/transport25/scenarios.json').read_text());replay=json.loads((E/'corpus-replay.json').read_text());check('42 exact corpus IDs and replay expectations',len(corpus['scenarios'])==42 and [x['id'] for x in corpus['scenarios']]==[x['id'] for x in replay['scenarios']] and all(x['pass'] and x['review']['physicalMediaVerified']==False and x['review']['hardwareOrSITLTransportVerified']==False for x in replay['scenarios']))
pin=(R/'pilot/transport25/pins.mjs').read_text();check('current corpus pin exact',h(R/'pilot/transport25/scenarios.json') in pin);old=json.loads((E/'browser-review-revision01.json').read_text());check('prior40 corpus reconstruction SHA exact',h(E/'corpus-revision01.json')==old['corpusSha256'])
sources=json.loads((E/'sources.json').read_text())['sources'];check('four original official source captures exact',len(sources)==4 and all(x['status'] in ['CAPTURED','REUSED_CAPTURE'] and h(R/x['path'])==x['sha256'] for x in sources))
syntax=[]
for f in (R/'pilot/transport25').glob('*.mjs'):
 q=subprocess.run(['node','--check',str(f)],capture_output=True,text=True);syntax.append({'file':str(f.relative_to(R)),'exitCode':q.returncode,'output':q.stdout+q.stderr})
check('all JS syntax pass',all(x['exitCode']==0 for x in syntax));(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
missing=[]
for f in ['delivery/TIP-TRANSPORT25.md','docs/ADR-034-MOCK-TRANSPORT-ROUTING.md','pilot/transport25/README.md','delivery/COMPLETION-TRANSPORT25.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',(R/f).read_text()):
  if not dest.startswith(('http://','https://','#')) and not ((R/f).parent/dest).exists():missing.append((f,dest))
check('document local links valid',not missing,missing)
pins={str(f.relative_to(R)):h(f) for f in sorted((R/'pilot/transport25').rglob('*')) if f.is_file()}
for f in ['delivery/TIP-TRANSPORT25.md','docs/ADR-034-MOCK-TRANSPORT-ROUTING.md','delivery/COMPLETION-TRANSPORT25.md']:pins[f]=h(R/f)
(E/'module-fingerprints.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'scope':'New isolated module only, no frozen inventory change'},indent=2)+'\n')
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'READY_ISOLATED_MOCK_ROUTING' if all(x['pass'] for x in checks) else 'NOT_READY','requirements':{'implemented':8,'verifiedMockScope':8 if all(x['pass'] for x in checks) else None,'total':8},'tests':{'coreCorpus':75,'browser':31,'protocol22Regression':82,'canonicalTotal':188,'fail':0,'unitSkipped':0},'corpusScenarios':42,'checks':checks,'soak':{k:p[k] for k in ['status','checkedAt','elapsedMs','totals','manifestSha256','pid','childPid']},'notChecked':['Real transport/SDK/HeraHub/authentication/key custody','New actual SITL multi-payload execution/HIL/flight','Native manual input/video/physical media/installed payload count','Production continuous control/multi-link router/full RAGAS A/B'],'reviewer':'Single-agent sequential implementation/verification, no independent audit','scope':'Metadata/hash gates separate from188 tests. Endpoint fingerprint match does not establish continuous path presence; prior incidents retained.'};(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'metadata/source/preservation checks,',sum(not x['pass'] for x in checks),'failures')
if any(not x['pass'] for x in checks):print(json.dumps([x for x in checks if not x['pass']],indent=2));raise SystemExit(1)
