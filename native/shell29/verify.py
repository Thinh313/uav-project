"""Read frozen state; write only NATIVE29 verification metadata. Never sign or launch."""
from pathlib import Path
import ast, datetime, hashlib, json, re, subprocess, zipfile

R = Path(__file__).resolve().parents[2]
M = R / 'native/shell29'
E = R / 'evidence/native29'
checks = []
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def check(name, ok, detail=None): checks.append(dict(name=name, passed=bool(ok), detail=detail))
def compare(files): return [p for p,s in files.items() if not (R/p).is_file() or sha(R/p)!=s]

b=load(E/'preservation-before.json')
after={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sets':{}}
for name,v in b['sets'].items():
    files=load(R/v['inventory'])['files'];bad=compare(files)
    after['sets'][name]={'files':len(files),'mismatches':bad}
    check(name+' frozen inventory exact',not bad,after['sets'][name])
for name in ['stable','oldTrust']:
    bad=compare(b[name]);after[name]={'files':len(b[name]),'mismatches':bad}
    check(name+' original bytes retained',not bad,after[name])
a=load(R/'evidence/endure27/candidate.json')
f=load(R/'evidence/endure20/freeze.json')['files']
for name,base in [('source140',R),('slot140',Path(a['slot']))]:
    bad=[x['path'] for x in f if not (base/x['path']).is_file() or sha(base/x['path'])!=x['sha256']]
    after[name]={'files':len(f),'mismatches':bad};check(name+' exact',len(f)==140 and not bad,after[name])
after['scope']='Endpoint byte preservation only; no 24h, continuous path presence or new signature acceptance. Live ENDURE observations may advance separately.'
(E/'preservation-after.json').write_text(json.dumps(after,indent=2)+'\n')

n=load(E/'native-build.json');attempt=n['attempt'];apk=R/n['apk']
check('final source hashes exact',not compare(n['sourceHashes']))
check('sourceId binds sorted source hashes',n['sourceId']==hashlib.sha256(json.dumps(n['sourceHashes'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
check('unsigned build exact artifact and scope',n['status']=='BUILT_UNSIGNED_NATIVE_STATIC_AND_HOST_VERIFIED' and n['hostTests']==84 and n['native24Regression']==38 and n['permissions']=='NONE' and n['nativeRuntime']=='NOT_CHECKED' and sha(apk)==n['apkSha256'] and apk.stat().st_size==n['apkBytes'])
test_log=(E/f'model-tests-attempt{attempt:02d}.txt').read_text();legacy_log=(E/f'native24-regression-attempt{attempt:02d}.txt').read_text()
check('84new/38legacy host test logs',re.search(r'TOTAL 84\s*$',test_log) is not None and 'TOTAL 38 PASS; host pure-Java only; Android runtime NOT_CHECKED' in legacy_log and sum(x.startswith('PASS ') for x in test_log.splitlines())==84 and sum(x.startswith('PASS ') for x in legacy_log.splitlines())==38)
with zipfile.ZipFile(apk) as z:
    names=z.namelist();clip=z.getinfo('assets/synthetic.webm')
    check('APK native DEX/uncompressed original clip/no JAR signature','classes.dex' in names and clip.compress_type==zipfile.ZIP_STORED and hashlib.sha256(z.read(clip)).hexdigest()==sha(R/'native/shell24/assets/synthetic.webm') and not any(x.startswith('META-INF/') for x in names))
u=(E/'unsigned-verification.txt').read_text();check('apksigner refused unsigned artifact','DOES NOT VERIFY' in u or 'Missing META-INF/MANIFEST.MF' in u)
pins=json.loads((M/'walkthrough/pins.mjs').read_text().split('=',1)[1].strip().rstrip(';'))
check('browser pins exact native/catalog/replay/clip',pins['sourceId']==n['sourceId'] and pins['apkSha256']==sha(apk) and pins['catalogSha256']==sha(M/'walkthrough/catalog.json') and pins['replaysSha256']==sha(M/'walkthrough/replays.json') and pins['fixtureSha256']==sha(R/'native/shell24/assets/synthetic.webm'))
q=load(E/'browser-qa.json');c=load(E/'contract-replay.json');g=load(E/'catalog-generation.json')
check('65 final browser checks',q['status']=='PASS' and len(q['checks'])==65 and all(x['pass'] for x in q['checks']))
check('917 raw integrity assertions/10scenarios',c['status']=='PASS' and len(c['checks'])==917 and all(x['pass'] for x in c['checks']) and c['scenarios']==10 and c['plans']==6 and c['corpusSha256']==pins['replaysSha256'])
check('six core contracts frozen source parity',g['status']=='PASS' and g['plans']==6 and all(x['pass'] for x in g['checks']) and not compare(g['sourceHashes']))
for i in range(6):
    v=load(E/f'browser-review-{i}.json')
    check('final export source/mission binding '+str(i),v['sourceId']==n['sourceId'] and v['corpusSha256']==pins['replaysSha256'] and v['catalogSha256']==pins['catalogSha256'] and hashlib.sha256(v['compiledRaw'].encode()).hexdigest()==v['state']['plan']['missionSha256'] and json.loads(v['compiledRaw'])==v['compiledMission'] and v['operational'] is False and v['physicalMediaVerified'] is False and v['androidRuntime']=='NOT_CHECKED')
v=load(E/'host-video-decode.json');check('actual host synthetic decode without hardware claim',v['frames']>0 and v['width']==640 and v['height']==360 and v['fixtureSha256']==pins['fixtureSha256'] and v['androidRuntime']=='NOT_CHECKED' and v['physicalMediaVerified'] is False and v['cameraToDisplayLatencyMs'] is None)
s=load(E/'sources.json')['sources'];check('four reused primary captures exact',len(s)==4 and all(x['status']=='REUSED_ORIGINAL_CAPTURE' and sha(R/x['path'])==x['sha256'] for x in s))
cl=load(E/'cleanup-build.json');check('scratch removed/no installs/key reads/signing',not (M/'.build').exists() and cl['removed']==['native/shell29/.build'] and all(cl[x]==0 for x in ['wholeProjectCopies','dependencyInstalls','keyReads','signOperations']))
syntax=[]
for p in sorted(M.rglob('*.mjs')):
    r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);syntax.append({'path':str(p.relative_to(R)),'exitCode':r.returncode,'output':r.stdout+r.stderr})
for p in M.glob('*.py'):ast.parse(p.read_text())
check('new JS/Python syntax',all(x['exitCode']==0 for x in syntax))
(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
ok=all(x['passed'] for x in checks)
mapping={1:['catalog-generation.json','contract-replay.json'],2:[f'model-tests-attempt{attempt:02d}.txt'],3:[f'host-replays-attempt{attempt:02d}.json','contract-replay.json'],4:[f'model-tests-attempt{attempt:02d}.txt'],5:['host-video-decode.json','native-build.json'],6:[f'model-tests-attempt{attempt:02d}.txt','browser-review-0.json'],7:['native-build.json','browser-qa.json'],8:['preservation-after.json','cleanup-build.json']}
result={'at':after['at'],'status':'READY_ISOLATED_NATIVE_MOCK_PREPARATION' if ok else 'NOT_READY','requirements':{'implemented':8,'verified':8 if ok else 0,'total':8,'mapping':mapping},'functionalChecks':{'newHost':84,'N24Regression':38,'browser':65,'total':187},'rawAssertions':917,'metadataChecks':checks,'sourceId':n['sourceId'],'apkSha256':n['apkSha256'],'limits':['Android runtime/layout/input/decoder/lifecycle/SAF/durability NOT_CHECKED','Six catalogue surveys, no arbitrary native AOI authoring','Synthetic preflight/single-axis ownership/video; no physical input/media/execution','No SDK/Hera/Fly integration/transport/24h/new signing'],'review':'Single-agent sequential verification; not independent audit'}
(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
docs=[R/'delivery/TIP-NATIVE29.md',R/'delivery/COMPLETION-NATIVE29.md',R/'docs/ADR-038-NATIVE-OPERATOR-JOURNEY-MOCK-CONTRACTS.md']
files=[p for p in M.rglob('*') if p.is_file()]+docs
(E/'module-fingerprints.json').write_text(json.dumps({'at':after['at'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(files)},'scope':'New isolated files only; no frozen baseline replacement or software signature'},indent=2)+'\n')
(E/'evidence-fingerprints.json').write_text(json.dumps({'at':after['at'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='evidence-fingerprints.json'}},indent=2)+'\n')
print(result['status'],len(checks),'metadata checks',sum(not x['passed'] for x in checks),'failures')
if not ok:
    print(json.dumps([x for x in checks if not x['passed']],indent=2));raise SystemExit(1)
