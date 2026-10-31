"""Independent G14 declared namespace/history seam verification; no runtime effects."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation14';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert tuple(sys.version_info[:3])==(3,9,6)
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
config=json.loads((P/'builder-namespace-map.json').read_bytes());proof=E/'builder-native-tests01.json'
assert H(proof)=='b4f89a775d74344a3195075a49e362e03c7ab0ded2f2e71fb7c6f8d18fded44c'
prior=json.loads((R/'evidence/beta06/generation13/native-helper-freeze01.json').read_bytes());rows=[]
def namespace(s):
 for a,b in config['map']:s=s.replace(a,b)
 return s
for name in config['operationalFiles']:
 old=R/'planning/beta06g13'/name;new=P/('qa-root-live28.py'if name=='qa-root-live26.py'else name)
 assert H(old)==prior['files'][str(old.relative_to(R))]
 expected=namespace(old.read_text());actual=new.read_text()
 if name=='qa-ap-admission.py':
  expected=expected.replace("'priorGeneration12SITLRequests'];expected=[11,1,1,1,1,2,2,2]","'priorGeneration12SITLRequests','priorGeneration13SITLRequests'];expected=[11,1,1,1,1,2,2,2,1]").replace('EXACT_TWENTYONE_HISTORICAL_REQUESTS_REQUIRED','EXACT_TWENTYTWO_HISTORICAL_REQUESTS_REQUIRED').replace('len(set(runs))==21','len(set(runs))==22')
  start=actual.index('    expected_g13=');end=actual.index('    return runs\n',start);extra=actual[start:end]
  assert "'sa79cb8c8ee88488b9c8b':'595a5047aafcf3bce8e9743a763ec1f3b58b46177b87d3998f366640281f78e0'"in extra
  assert "q['mode']=='sitl'"in extra or "q.get('mode')=='sitl'"in extra
  actual=actual[:start]+actual[end:]
 assert actual==expected,name
 if new.suffix=='.py':
  values=lambda s:[n.value for n in ast.walk(ast.parse(s))if isinstance(n,ast.Constant)and type(n.value)in(int,float)]
  assert values(actual)==values(expected)
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'priorPath':str(old.relative_to(R)),'priorSha256':H(old),'delta':'Exact declared namespace only; AP admission additionally exact original G13 request/history22'if name=='qa-ap-admission.py'else'Exact declared namespace only'})
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
c=load('qa_g14_controller',P/'qa-root-controller.py');a=load('qa_g14_admission',P/'qa-ap-admission.py')
assert H(R/'pilot/beta06g14/clock_basis.py')=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s
pins=json.loads((R/'evidence/beta06/generation13/flight-pins01.json').read_bytes());pins['priorGeneration13SITLRequests']=[{'run':'sa79cb8c8ee88488b9c8b','requestSha256':'595a5047aafcf3bce8e9743a763ec1f3b58b46177b87d3998f366640281f78e0'}]
assert len(a.historical_runs(pins))==22
bad=copy.deepcopy(pins);bad['priorGeneration13SITLRequests'][0]['requestSha256']='0'*64
try:a.historical_runs(bad);raise AssertionError('WRONG_REQUEST_DIGEST_ACCEPTED')
except AssertionError as e:assert str(e)!='WRONG_REQUEST_DIGEST_ACCEPTED'
assert not [p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller28','root-controller29','root-runtime28','root-runtime29','host-app14','host-console','quota-native-ledger','workspace-first-writer'))]
report={'status':'PASS_G14_NATIVE_TARGETED_SOURCE_MOCK_ONLY','source':{r['path']:r['sha256']for r in rows},'rows':rows,'currentHistory22ExactAndWrongDigestRefused':True,'providerSha256':H(R/'pilot/beta06g14/clock_basis.py'),'effectiveControllerGuardDefaultsCanonical':True,'pristineActual28And29':True,'builderCurrentProof':{'path':str(proof.relative_to(R)),'sha256':H(proof),'groups':7},'inheritedIndependentExitSnapshotGroundEvidence':'G13 QA execution reused only after exact current whole operational source normalization; no old actual outcome pooled and no new runtime test claimed.','recipeSha256':H(Path(__file__)),'actualRuntimeEffects':0}
out=E/'qa-native-cooperation01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'files':len(rows),'sha256':H(out),'bytes':out.stat().st_size}))
