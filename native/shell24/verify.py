"""Read-only checks of frozen baselines; writes NATIVE24 verification receipts only."""
from pathlib import Path
import json,hashlib,datetime,re,subprocess
R=Path(__file__).resolve().parents[2];E=R/'evidence/native24';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=json.loads((E/'preservation-before.json').read_text());checks=[]
def check(name,condition,detail=None):checks.append({'name':name,'pass':bool(condition),'detail':detail})
for name,v in before['sets'].items():
 pins=json.loads((R/v['inventory']).read_text())['files'];bad=[p for p,s in pins.items() if not (R/p).is_file() or h(R/p)!=s];check(name+' baseline exact',not bad,{'count':len(pins),'mismatches':bad})
check('candidate/canonical SOT/roadmap baseline exact',all((R/p).is_file() and h(R/p)==s for p,s in before['stable'].items()))
c=json.loads((R/'evidence/endure20/candidate.json').read_text());f=json.loads((R/'evidence/endure20/freeze.json').read_text())['files']
for label,base in [('frozen source',R),('immutable slot',Path(c['slot']))]:
 bad=[x['path'] for x in f if not (base/x['path']).is_file() or h(base/x['path'])!=x['sha256']];check(label+'140 files exact',not bad,bad)
p=json.loads((R/'evidence/endure20/progress.json').read_text());lock=json.loads((R/'.local/trust16/state/.writer.lock').read_text());check('same continuous campaign/PID/manifest/lock, running0errors',p['status']=='RUNNING_NOT_FINAL' and p['startedAt']==before['progress']['startedAt'] and p['manifestSha256']==before['progress']['manifestSha256'] and p['pid']==before['progress']['pid'] and p['childPid']==before['progress']['childPid'] and lock==before['lock'] and p['totals']['errors']==0)
fresh=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(p['checkedAt'].replace('Z','+00:00'))).total_seconds();check('progress fresh<=90s',0<=fresh<=90,{'ageSeconds':fresh})
b=json.loads((E/'native-build.json').read_text());check('latest native source/APK exact',all(h(R/f)==s for f,s in b['sourceHashes'].items()) and h(R/b['apk'])==b['apkSha256']);check('development package/zero permission/static-only scope',b['package']=='vn.rtr.aeris.shell24' and b['permissions']=='NONE' and b['nativeRuntime']=='NOT_CHECKED' and 'uses-permission:' not in (E/'apk-permissions.txt').read_text());check('38 host Java checks',b['hostTestCount']==38 and 'TOTAL 38 PASS' in (E/f"model-tests-attempt{b['attempt']:02}.txt").read_text())
qa=json.loads((E/'browser-qa.json').read_text());check('32 browser checks exact/no failures',len(qa['checks'])==32 and all(x['pass'] for x in qa['checks']));clip=json.loads((E/'fixture.json').read_text());decode=json.loads((E/'host-video-decode.json').read_text());check('encoded fixture/source and actual host decode',h(R/'native/shell24/assets/synthetic.webm')==clip['sha256']==decode['fixtureSha256'] and decode['frames']>0 and decode['physicalMediaVerified']==False)
sources=json.loads((E/'sources.json').read_text())['sources'];check('four original Android source captures match',len(sources)==4 and all(x['status'] in ['CAPTURED','REUSED_CAPTURE'] and h(R/x['path'])==x['sha256'] for x in sources))
syntax=[]
for f in ['make-fixture.mjs','browser-qa.mjs','walkthrough/shell.mjs','walkthrough/server.mjs']:
 z=subprocess.run(['node','--check',str(R/'native/shell24'/f)],capture_output=True,text=True);syntax.append({'file':f,'exitCode':z.returncode,'output':z.stdout+z.stderr})
check('JS syntax',all(x['exitCode']==0 for x in syntax));(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
check('build scratch removed',(R/'native/shell24/.build').exists()==False)
missing=[]
for f in ['delivery/TIP-NATIVE24.md','docs/ADR-033-ISOLATED-NATIVE-SHELL.md','native/shell24/README.md','delivery/COMPLETION-NATIVE24.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',(R/f).read_text()):
  if not dest.startswith(('http://','https://','#')) and not ((R/f).parent/dest).exists():missing.append((f,dest))
check('local document links exist',not missing,missing)
runtime=json.loads((E/'runtime-observation.json').read_text());check('live HTTP identity observed',runtime['httpStatus']==200 and runtime['live']['manifestSha256']==c['manifestSha256'] and str(p['pid']) in runtime['processes'] and str(p['childPid']) in runtime['processes'])
pins={str(f.relative_to(R)):h(f) for f in sorted((R/'native/shell24').rglob('*')) if f.is_file() and '.build' not in f.parts}
for f in ['delivery/TIP-NATIVE24.md','docs/ADR-033-ISOLATED-NATIVE-SHELL.md','delivery/COMPLETION-NATIVE24.md']:pins[f]=h(R/f)
(E/'module-fingerprints.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'scope':'New isolated preparation files; no frozen inventory update'},indent=2)+'\n')
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'READY_HOST_PREPARATION_NATIVE_RUNTIME_NOT_CHECKED' if all(x['pass'] for x in checks) else 'NOT_READY','requirements':{'implemented':7,'verifiedPreparationScope':7 if all(x['pass'] for x in checks) else None,'total':7},'checks':checks,'canonicalHostTests':{'java':38,'browser':32,'total':70,'fail':sum(not x['pass'] for x in qa['checks'])},'soak':{k:p[k] for k in ['status','checkedAt','elapsedMs','totals','manifestSha256','pid','childPid']},'nativeBuild':{'sourceId':b['sourceId'],'apkSha256':b['apkSha256'],'bytes':b['apkBytes']},'notChecked':['Android install/launch/native UI/SAF/lifecycle/provider/power-loss','Physical inputs/manual flight mapping/RC path','HeraHub decoder/thermal/live video/frame age/camera latency','Real transport/SDK/HIL/flight/physical capture','Production stack/official signing/runtime A/B'],'reviewer':'Single agent, not independent audit','scope':'Metadata/hash checks are separate from70 host tests. Fingerprint endpoints do not assert continuous path presence; old preservation incidents remain retained.'}
(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'preservation/build/receipt checks,',sum(not x['pass'] for x in checks),'failures');
if any(not x['pass'] for x in checks):print(json.dumps([x for x in checks if not x['pass']],indent=2));raise SystemExit(1)
