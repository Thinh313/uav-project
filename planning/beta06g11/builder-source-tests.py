"""G11 effective shared-clock imports and bounded namespace checks. No runtime/listener."""
from pathlib import Path
import ast,hashlib,json,subprocess,tempfile
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation11';sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def ns(s):
 for a,b in [('beta06g10','beta06g11'),('generation10','generation11'),('G10','G11'),('g10_','g11_'),('aeris.g10.','aeris.g11.'),('host-app10','host-app11')]:s=s.replace(a,b)
 return s
files=['entry.mjs','flight/handoff.mjs','flight/receive-flight.mjs','flight/qualified/profile.mjs','flight/qualified/link.mjs','flight/qualified/mock.mjs','flight/qualified/verify-profile.mjs','workspace-lineage.mjs','quota.mjs','resource.mjs','proof-writer.mjs']
for n in files:
 old=(R/'pilot/beta06g10'/n).read_text();new=(R/'pilot/beta06g11'/n).read_text();assert ns(old)==new,n;rows.append({'proof':'EXACT_TARGETED_NAMESPACE_ONLY','path':'pilot/beta06g11/'+n,'sha256':sha(new.encode())})
a=json.loads((R/'pilot/beta06g10/quota-policy.json').read_bytes());b=json.loads((R/'pilot/beta06g11/quota-policy.json').read_bytes());a.pop('history');b.pop('history');a['schema']=a['schema'].replace('G10','G11');assert a==b;rows.append({'proof':'ALL_NUMERIC_POLICY_AND_FUTURE_ARITHMETIC_UNCHANGED'})
provider=R/'pilot/beta06g11/clock_basis.py';assert sha(provider.read_bytes())=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
# Normalize only the explicit approved provider bindings and pre-effect capability reads.
for n in ['quota.py','flight/runtime.py']:
 s=(R/'pilot/beta06g11'/n).read_text();prefix=s.index('import importlib.util,sys\n');end=s.index("_clock_spec.loader.exec_module(host_clock)\n",prefix)+len('_clock_spec.loader.exec_module(host_clock)\n');s=s[:prefix]+s[end:]
 if n=='quota.py':s=s.replace(' deadline=host_clock.now_s()+15\n','').replace('text=True)\n','text=True);deadline=host_clock.now_s()+15\n',1).replace(' host_clock.now_ns() # Unsupported provider cannot reach a ledger writer.\n','').replace('host_clock.now_s()',"__import__('time').monotonic()")
 else:s=s.replace(' host_clock.now_ns() # Capability check before diagnostic directory/capture writers.\n','').replace('host_clock.now_s','time.monotonic')
 assert s==ns((R/'pilot/beta06g10'/n).read_text()),n
 rows.append({'proof':'EXACT_OPERATIONAL_SOURCE_AFTER_ONLY_EXPLICIT_CLOCK_BINDING_AND_CAPABILITY_CHECK','path':'pilot/beta06g11/'+n})
# Actual effective modules in fresh Apple and PATH/Brew interpreters; zero clock monkeypatch.
program=r'''
import importlib.util,json,sys,tempfile,time
from pathlib import Path
original=time.monotonic;R=Path.cwd();p=R/'pilot/beta06g11/flight/runtime.py';s=importlib.util.spec_from_file_location('effective_g11_ap_clock',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);q=sys.modules['quota'];c=m.host_clock
assert q.host_clock is c and c is sys.modules['aeris_g11_clock'];assert m.Capture.__init__.__kwdefaults__['clock']is c.now_s;assert time.monotonic is original
before=c.now_ns();seconds=c.now_s();after=c.now_ns();assert before<=seconds*1e9<=after
assert not any(x in p.read_text()for x in ['time.monotonic','time.perf_counter'])
checks=[];saved_ns=c.now_ns;saved_popen=q.subprocess.Popen;count=[0]
def forbidden(*a,**k):count[0]+=1;raise AssertionError('Popen after unsupported provider')
def unsupported(*a,**k):raise c.ClockContractError('UNSUPPORTED_TEST_PROVIDER_NO_FALLBACK')
with tempfile.TemporaryDirectory(prefix='codex-tmp-g11-clock-20261022-',dir=R/'evidence/beta06/generation11')as temp:
 base=Path(temp);oldE=q.E;q.E=base/'forbidden-ledger-root';c.now_ns=unsupported;q.subprocess.Popen=forbidden
 try:
  for name,f in [('AP-run-before-diagnostic-writer',lambda:m.run('s'+'1'*20,root=base)),('Capture-default-before-pipe-or-file',lambda:m.Capture(['NOEXEC'],base/'capture',{})),('quota-before-Node-child',lambda:q.admit('guard',remaining_ap=0,remaining_hosts=0,closed_runs=[],claim_id='PURE_TEST')),('quota-before-ledger-writer',lambda:q.reserve_write(category='native',entries=1,bytes=1,claim_id='PURE_TEST'))]:
   try:f()
   except c.ClockContractError:checks.append(name)
   else:raise AssertionError(name)
  assert count[0]==0 and list(base.iterdir())==[]
 finally:c.now_ns=saved_ns;q.subprocess.Popen=saved_popen;q.E=oldE
assert time.monotonic is original
print(json.dumps({'interpreter':sys.executable,'version':sys.version.split()[0],'sharedIdentity':c.__name__,'provider':str(Path(c.__file__).resolve().relative_to(R)),'basis':c.BASIS,'seconds':'now_ns()/1000000000','actualRawBracketNs':[before,after],'stdlibMonotonicUnmodified':True,'unsupportedBeforeEffects':checks,'Popen':count[0],'scratchRemoved':temp}))
'''
for executable in dict.fromkeys(['/usr/bin/python3',__import__('shutil').which('python3')]):
 p=subprocess.run([executable,'-B','-c',program],cwd=R,capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr;rows.append({'proof':'ACTUAL_EFFECTIVE_APPLE_OR_BREW_MODULE_BINDING_AND_PRE_EFFECT_UNSUPPORTED_REFUSAL','result':json.loads(p.stdout)})
# Tiny filesystem namespace fixture; provider copied too, no boot/clock-body substitutions.
helper=(R/'planning/beta06g9/builder-host-binding-tests.py').read_text().split('with tempfile.TemporaryDirectory(')[0];scope={'__file__':str(__file__)};exec(helper,scope);scope['E']=E
with tempfile.TemporaryDirectory(prefix='codex-tmp-g11-binding-20261022-',dir=E)as tmp:
 root=Path(tmp)/'root';prod,active=scope['setup'](root,11);(prod/'clock_basis.py').write_bytes(provider.read_bytes());paths=[];stages=[]
 for H,name in [(2,None),(1,'host-app11'),(0,'host-app11-restart')]:
  if name:paths+=scope['host'](active,name)
  p=scope['bridge'](prod,4,H);assert p.returncode==0,p.stderr;stages.append({'A':4,'H':H,'status':'ADMITTED'})
 z=scope['inspect'](prod,active,paths);assert z['usage']['capacity']['hostProcesses']==2 and list(z['routes'].values())==['clock','media','hostJournals','hostJournals','hostOther']*2
 p=scope['bridge'](prod,4,1);assert p.returncode and 'ORIGINAL_COUNTER_CAPACITY_MISMATCH'in p.stderr
 fixture=scope['manifest'](root)
rows.append({'proof':'BOTH_CURRENT_HOSTS_REAL_FS_AND_PYTHON_NODE_BRIDGE','stages':stages,'routes':z['routes'],'fixtureManifest':fixture,'scratchRemoved':tmp,'seam':'Exact quota+provider source copies; policy.history identity only points to one fixture anchor; zero AP allocation fixtures'})
local=[]
for n in ['quota.py','flight/runtime.py']:
 p=R/'pilot/beta06g11'/n;tree=ast.parse(p.read_text());calls=[{'line':x.lineno,'call':ast.unparse(x.func)}for x in ast.walk(tree)if isinstance(x,ast.Call)and (isinstance(x.func,ast.Attribute)and x.func.attr in ['now_ns','now_s','sleep','communicate','select','poll','wait']or isinstance(x.func,ast.Name)and x.func.id=='clock')];local.append({'path':str(p.relative_to(R)),'calls':calls})
for imported in ['pilot/beta06g4/flight/readiness.py','pilot/beta06g3/prepare_executable.py']:
 text=(R/imported).read_text();assert not any(x in text for x in ['monotonic','perf_counter','clock_gettime']);local.append({'path':imported,'sha256':sha(text.encode()),'absoluteClockSites':0})
for p in (R/'pilot/beta06g11').rglob('*'):
 if p.suffix=='.mjs':subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
 elif p.suffix=='.py':ast.parse(p.read_text())
report={'status':'PASS_EFFECTIVE_G11_CLOCK_BINDING_SOURCE_MOCK_ONLY','groups':len(rows),'rows':rows,'clockSiteInventory':local,'durationOnlyInternals':'time.sleep, selectors.select timeouts and subprocess.communicate timeout use local duration only; none imports or compares parent absolute anchors. Capture/trend stamps are canonical seconds and local; basis bound by manifest. Node hrtime/performance untouched/distinct. Native alone proves parent/child absolute basis+boot contract.','providerSha256':sha(provider.read_bytes()),'APRequests':0,'listeners':0,'oldWrites':0}
with(E/'builder-source-tests01.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({'status':'PASS','groups':len(rows),'policySha256':sha((R/'pilot/beta06g11/quota-policy.json').read_bytes())}))
