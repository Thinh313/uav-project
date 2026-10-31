"""Independent G17 Native namespace/guard verification only. No subprocess/Android/runtime."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation17';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert tuple(sys.version_info[:3])==(3,9,6);assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
cfg=json.loads((P/'builder-namespace-map.json').read_bytes());expected=[['beta06g15','beta06g17'],['generation15','generation17'],['GENERATION15','GENERATION17'],['host-app15','host-app17'],['g15_','g17_'],['aeris_g15_clock','aeris_g17_clock'],['G15','G17'],["'30'","'32'"],["'31'","'33'"],['30|31','32|33'],['ROOT_LIVE30','ROOT_LIVE32'],['root-controller30','root-controller32'],['EMULATOR30','EMULATOR32'],['BOOT30','BOOT32'],['BOOT31','BOOT33'],['BEFORE31','BEFORE33'],['closure30','closure32'],['attempt31','attempt33'],['Boot30','Boot32'],['Boot31','Boot33'],['g17_frozen_root_controller_live30','g17_frozen_root_controller_live32']];assert cfg['map']==expected
prior=json.loads((R/'evidence/beta06/generation15/native-helper-freeze01.json').read_bytes());rows=[]
for name in cfg['operationalFiles']:
 old=R/'planning/beta06g15'/name;new=P/('qa-root-live32.py'if name=='qa-root-live30.py'else name);assert H(old)==prior['files'][str(old.relative_to(R))]
 want=old.read_text()
 for a,b in expected:want=want.replace(a,b)
 assert new.read_text()==want,name
 if new.suffix=='.py':
  numeric=lambda s:[n.value for n in ast.walk(ast.parse(s))if isinstance(n,ast.Constant)and type(n.value)in(int,float)]
  assert numeric(old.read_text())==numeric(new.read_text()),name+':UNCHANGED_GUARD_NUMBERS'
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'priorPath':str(old.relative_to(R)),'priorSha256':H(old)})
assert len(rows)==20
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=load('qa_g17_controller',P/'qa-root-controller.py');a=load('qa_g17_admission',P/'qa-ap-admission.py');provider=R/'pilot/beta06g17/clock_basis.py';assert H(provider)=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17';assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s
pins=json.loads((R/'evidence/beta06/generation15/flight-pins01.json').read_bytes());assert len(a.historical_runs(pins))==22
bad=copy.deepcopy(pins);bad['priorGeneration13SITLRequests'][0]['requestSha256']='0'*64
try:a.historical_runs(bad);raise AssertionError('WRONG_REQUEST_DIGEST_ACCEPTED')
except AssertionError as ex:assert str(ex)!='WRONG_REQUEST_DIGEST_ACCEPTED'
assert(P/'qa-port-guard.py').read_text().count("'-anl'")==2
assert not[p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller32','root-controller33','root-runtime32','root-runtime33','host-app17','host-console','quota-native-ledger','workspace-first-writer'))]
proof=E/'nativebuilder-tests01.json';assert H(proof)=='3c2b9ba15a727a12ee1e1c7fa10e8945209a68fe4d59d33da1712349b567af8a'
report={'status':'PASS_G17_NATIVE_NAMESPACE_GUARD_SOURCE_ONLY','source':{r['path']:r['sha256']for r in rows},'rows':rows,'allowedMapExplicitlyVerified':expected,'PythonNumericConstantsExactToFrozenG15':True,'currentHistory22ExactAndWrongDigestRefused':True,'canonicalProviderSha256':H(provider),'actualControllerAndDeadlineGuardDefaultClockIdentity':True,'portCollectorANLExact':True,'pristine32And33':True,'builderCurrentProof':{'path':str(proof.relative_to(R)),'sha256':H(proof),'groups':8},'notCoveredHere':'New effectiveG17async resource/UI application composition requires separate independent tests. Native guard equivalence is not integrated entry acceptance.','actualRuntimeEffects':0,'recipeSha256':H(Path(__file__))}
out=E/'qa-native-cooperation01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'bytes':out.stat().st_size,'files':len(rows),'status':report['status']}))
