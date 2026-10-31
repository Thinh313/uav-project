"""Current G15 whole-source/portcollector normalization, no runtime or sockets."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation15';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert tuple(sys.version_info[:3])==(3,9,6)
config=json.loads((P/'builder-namespace-map.json').read_bytes());proof=E/'builder-native-tests01.json';assert H(proof)=='5202fcd12f633dc5bd24099d8535d60dc00459ea28c8741078b1f0f968e90016'
prior=json.loads((R/'evidence/beta06/generation14/native-helper-freeze02.json').read_bytes());rows=[]
def namespace(s):
 for a,b in config['map']:s=s.replace(a,b)
 return s
for name in config['operationalFiles']:
 old=R/('planning/port14fix/qa-port-guard.py'if name=='qa-port-guard.py'else'planning/beta06g14/'+name)
 new=P/('qa-root-live30.py'if name=='qa-root-live28.py'else name)
 if name=='qa-port-guard.py':assert H(old)=='115d7e46d497cdb2f9179c44637f39fdfaf42ffda8ddf6c00ad13d2214e4c472'
 else:assert H(old)==prior['files'][str(old.relative_to(R))]
 expected=namespace(old.read_text());assert new.read_text()==expected,name
 if new.suffix=='.py':
  values=lambda s:[n.value for n in ast.walk(ast.parse(s))if isinstance(n,ast.Constant)and type(n.value)in(int,float)]
  assert values(new.read_text())==values(expected)
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'priorPath':str(old.relative_to(R)),'priorSha256':H(old),'delta':'Declared namespace only; port uses separately verified exact two argv literal correction'if name=='qa-port-guard.py'else'Declared namespace only'})
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
c=load('qa_g15_controller',P/'qa-root-controller.py');a=load('qa_g15_admission',P/'qa-ap-admission.py')
provider=R/'pilot/beta06g15/clock_basis.py';assert H(provider)=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s
pins=json.loads((R/'evidence/beta06/generation14/flight-pins01.json').read_bytes());assert len(a.historical_runs(pins))==22
bad=copy.deepcopy(pins);bad['priorGeneration13SITLRequests'][0]['requestSha256']='0'*64
try:a.historical_runs(bad);raise AssertionError('WRONG_REQUEST_DIGEST_ACCEPTED')
except AssertionError as ex:assert str(ex)!='WRONG_REQUEST_DIGEST_ACCEPTED'
assert not[p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller30','root-controller31','root-runtime30','root-runtime31','host-app15','host-console','quota-native-ledger','workspace-first-writer'))]
report={'status':'PASS_G15_NATIVE_TARGETED_SOURCE_MOCK_ONLY','source':{r['path']:r['sha256']for r in rows},'rows':rows,'providerSha256':H(provider),'effectiveControllerGuardDefaultsCanonical':True,'currentHistory22ExactAndWrongDigestRefused':True,'pristineActual30And31':True,'builderCurrentProof':{'path':str(proof.relative_to(R)),'sha256':H(proof),'groups':8},'inheritedIndependentEvidence':'G14 Native source/mock guard proofs plus port14fix independent23 fake-only cases reused after exact current whole-source namespace equivalence. No real portprobe/currentruntime or actual oldsuccess pooled.','recipeSha256':H(Path(__file__)),'actualRuntimeEffects':0}
out=E/'qa-native-cooperation01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'files':len(rows),'sha256':H(out),'bytes':out.stat().st_size}))
