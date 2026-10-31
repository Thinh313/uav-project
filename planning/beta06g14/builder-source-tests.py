"""Bounded G14 namespace/effective-provider proof. No runtime/listener; reuse invariant G13 guard proofs."""
from pathlib import Path
import ast,hashlib,json,subprocess,tempfile
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation14';sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def ns(s):
 for a,b in [('beta06g13','beta06g14'),('generation13','generation14'),('G13','G14'),('g13_','g14_'),('aeris.g13.','aeris.g14.'),('host-app13','host-app14')]:s=s.replace(a,b)
 return s
files=['entry.mjs','flight/runtime.py','flight/handoff.mjs','flight/receive-flight.mjs','flight/qualified/profile.mjs','flight/qualified/link.mjs','flight/qualified/mock.mjs','flight/qualified/verify-profile.mjs','workspace-lineage.mjs','quota.mjs','quota.py','resource.mjs','proof-writer.mjs','sealed-history.mjs','lifecycle-phases.mjs','bootstrap.js']
for n in files:
 old=(R/'pilot/beta06g13'/n).read_text();new=(R/'pilot/beta06g14'/n).read_text();assert ns(old)==new,n;rows.append({'proof':'EXACT_NAMESPACE_ONLY_ALL_OPERATIONAL_ALGORITHMS_AND_CLOCK_BINDINGS_UNCHANGED','path':'pilot/beta06g14/'+n,'sha256':sha(new.encode())})
a=json.loads((R/'pilot/beta06g13/quota-policy.json').read_bytes());b=json.loads((R/'pilot/beta06g14/quota-policy.json').read_bytes());a.pop('history');b.pop('history');a['schema']=a['schema'].replace('G13','G14');assert a==b;rows.append({'proof':'ALL_NUMERIC_POLICY_AND_FUTURE_ARITHMETIC_UNCHANGED'})
program_recipe=r'''import fs from'node:fs';import assert from'node:assert/strict';import{RECIPES as previous,transform as old}from'./pilot/beta06g13/overlay.mjs';import{RECIPES,transform as next,sha}from'./pilot/beta06g14/overlay.mjs';import{restoreSidecarContract}from'./pilot/heartbeat13sidecarfix/route-contract.mjs';function ns(s){for(const[a,b]of[['beta06g13','beta06g14'],['generation13','generation14'],['G13','G14'],['g13_','g14_'],['aeris.g13.','aeris.g14.'],['host-app13','host-app14']])s=s.split(a).join(b);return s;}const rows=[];assert.deepEqual(Object.keys(RECIPES),Object.keys(previous));for(const p of Object.keys(RECIPES)){const src=fs.readFileSync(p,'utf8'),expected=p==='pilot/beta06g5/app.mjs'?restoreSidecarContract(ns(old(p,src))):ns(old(p,src)),actual=next(p,src);assert.equal(actual,expected,p);rows.push({path:p,sha256:sha(actual),delta:p.endsWith('/app.mjs')?'EXACT_NAMESPACE_PLUS_VERIFIED_ONE_SIDECAR_CLASSIFICATION':'EXACT_NAMESPACE_ONLY'});}console.log(JSON.stringify(rows));'''
p=subprocess.run(['node','--input-type=module','-e',program_recipe],cwd=R,capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr;rows.append({'proof':'ALL_FIVE_EFFECTIVE_OVERLAYS_EXACT_NAMESPACE_PLUS_ONLY_VERIFIED_SIDECAR_SITE','result':json.loads(p.stdout)})
provider=R/'pilot/beta06g14/clock_basis.py';assert sha(provider.read_bytes())=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
program=r'''
import importlib.util,json,sys,time
from pathlib import Path
original=time.monotonic;R=Path.cwd();p=R/'pilot/beta06g14/flight/runtime.py';s=importlib.util.spec_from_file_location('effective_g14_ap_clock',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);q=sys.modules['quota'];c=m.host_clock
assert q.host_clock is c and c is sys.modules['aeris_g14_clock'];assert m.Capture.__init__.__kwdefaults__['clock']is c.now_s;assert time.monotonic is original
before=c.now_ns();seconds=c.now_s();after=c.now_ns();assert before<=seconds*1e9<=after
print(json.dumps({'interpreter':sys.executable,'version':sys.version.split()[0],'sharedIdentity':c.__name__,'provider':str(Path(c.__file__).resolve().relative_to(R)),'basis':c.BASIS,'seconds':'now_ns()/1000000000','actualRawBracketNs':[before,after],'stdlibMonotonicUnmodified':True,'importsCreatedNoWriter':True}))
'''
for exe in dict.fromkeys(['/usr/bin/python3',__import__('shutil').which('python3')]):
 p=subprocess.run([exe,'-B','-c',program],cwd=R,capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr;rows.append({'proof':'CURRENT_EFFECTIVE_APPLE_OR_BREW_MODULE_IDENTITY_DEFAULT_AND_RAW_BASIS','result':json.loads(p.stdout)})
helper=(R/'planning/beta06g9/builder-host-binding-tests.py').read_text().split('with tempfile.TemporaryDirectory(')[0];scope={'__file__':str(__file__)};exec(helper,scope);scope['E']=E
with tempfile.TemporaryDirectory(prefix='codex-tmp-g12-binding-20261023-',dir=E)as tmp:
 root=Path(tmp)/'root';prod,active=scope['setup'](root,14);(prod/'clock_basis.py').write_bytes(provider.read_bytes());paths=[];stages=[]
 for H,name in [(2,None),(1,'host-app14'),(0,'host-app14-restart')]:
  if name:paths+=scope['host'](active,name)
  p=scope['bridge'](prod,4,H);assert p.returncode==0,p.stderr;stages.append({'A':4,'H':H,'status':'ADMITTED'})
 z=scope['inspect'](prod,active,paths);assert z['usage']['capacity']['hostProcesses']==2 and list(z['routes'].values())==['clock','media','hostJournals','hostJournals','hostOther']*2
 p=scope['bridge'](prod,4,1);assert p.returncode and 'ORIGINAL_COUNTER_CAPACITY_MISMATCH'in p.stderr
 fixture=scope['manifest'](root)
rows.append({'proof':'CURRENT_TWO_HOSTS_REAL_FS_AND_PYTHON_NODE_BRIDGE','stages':stages,'routes':z['routes'],'fixtureManifest':fixture,'scratchRemoved':tmp,'seam':'Exact quota/provider source copies; one fixture history identity only, zero AP allocation fixtures'})
for p in (R/'pilot/beta06g14').rglob('*'):
 if p.suffix=='.mjs':subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
 elif p.suffix=='.py':ast.parse(p.read_text())
footprints=[p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller','host-app14','quota-native-ledger','workspace-first-writer'))];assert footprints==[],footprints;assert not(E/'flight/runs').exists()
old_proof=R/'evidence/beta06/generation13/builder-source-tests01.json'
report={'status':'PASS_G14_NAMESPACE_CURRENT_EFFECTIVE_PROVIDER_SOURCE_MOCK_ONLY','groups':len(rows),'rows':rows,'reusedInvariantG13Proof':{'path':str(old_proof.relative_to(R)),'sha256':sha(old_proof.read_bytes()),'scope':'Unchanged unsupported-beforewriter/Popen, numeric/default/site invariant cases reused ONLY after exact13-module namespace normalization; current effective imports independently executed above. Native current effective collect/permit proofs separate.'},'actualNamespaceFootprints':footprints,'preparedUnclaimed':True,'APRequests':0,'listeners':0,'oldWrites':0,'providerSha256':sha(provider.read_bytes())}
with(E/'builder-source-tests01.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({'status':'PASS','groups':len(rows),'policySha256':sha((R/'pilot/beta06g14/quota-policy.json').read_bytes())}))
