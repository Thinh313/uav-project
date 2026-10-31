"""Focused G13 preparation proof. No product runtime/ADB/ports or actual launch names."""
from pathlib import Path
import ast,contextlib,copy,hashlib,importlib.util,io,json,os,subprocess,sys,tempfile,types
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];G=R/'planning/beta06g12';E=R/'evidence/beta06/generation13';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
b=load('g13_native_writer',P/'qa-native-budget.py');k=b.host_clock;r=load('g13_test_runtime',P/'qa-runtime.py');ui=load('g13_test_ui',P/'qa-ui.py')
if sys.argv[1:]==['--clock-child']:
 raw=sys.stdin.buffer.read(4097);assert len(raw)<=4096;permit=json.loads(raw);boot=r.validate_bootstrap();bound=r.validate_parent_permit(permit,'26');calls=[]
 try:ui.receipt_observation(permit['hostBeforeLaunchPythonMonoS']-1,reader=lambda:calls.append(True));raise AssertionError('EXPIRED_DEFAULT_ACCEPTED')
 except AssertionError as exc:assert str(exc)=='STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT'
 assert not calls;print(json.dumps({'bootstrap':boot,'binding':bound,'expiredReaderCalls':0}));sys.exit(0)
assert not sys.argv[1:]and tuple(sys.version_info[:3])==(3,9,6)
freeze=json.loads((R/'evidence/beta06/generation12/native-helper-freeze01.json').read_bytes())
mapping=[('beta06g12','beta06g13'),('generation12','generation13'),('GENERATION12','GENERATION13'),('host-app12','host-app13'),('g12_','g13_'),('aeris_g12_clock','aeris_g13_clock'),('G12','G13'),("'24'","'26'"),("'25'","'27'"),('24|25','26|27'),('ROOT_LIVE24','ROOT_LIVE26'),('root-controller24','root-controller26'),('EMULATOR24','EMULATOR26'),('BOOT24','BOOT26'),('BOOT25','BOOT27'),('BEFORE25','BEFORE27'),('closure24','closure26'),('attempt25','attempt27'),('Boot24','Boot26'),('Boot25','Boot27'),('g13_frozen_root_controller_live24','g13_frozen_root_controller_live26')]
def namespace(s):
 for old,new in mapping:s=s.replace(old,new)
 return s
ops=['qa-root-controller.py','qa-runtime.py','qa-deadline-guard.py','qa-device-actions.py','qa-ui.py','qa-android.py','qa-airborne.py','qa-ground-soak.py','qa-restart-proof.py','qa-ap-admission.py','qa-native-replay.py','qa-media-replay.py','qa-native-budget.py','qa-proof-writer.py','qa-raw-flight.mjs','qa-cut-replay.mjs','qa-reboot-replay.mjs','qa-overlap-replay.mjs','qa-root-live24.py','qa-port-guard.py'];rows=[]
for name in ops:
 old=G/name;new=P/('qa-root-live26.py'if name=='qa-root-live24.py'else name);assert H(old)==freeze['files'][str(old.relative_to(R))];expected=namespace(old.read_text());got=new.read_text();delta='namespace only'
 if name=='qa-device-actions.py':expected=namespace((R/'planning/heartbeat13fix/qa-device-actions.py').read_text());delta='namespace of QA-verified full beforeSnapshot prevalidation prototype'
 if name=='qa-root-controller.py':
  start="  helper_exit=self.runtime.poll()if self.runtime is not None else None;assert self.attempt=='26'and self.runtime is not None and helper_exit==0,'BOOT26_MUST_BE_CLOSED_BEFORE27';self.emit('OWNED_RUNTIME_HELPER_NUMERIC_EXIT_OBSERVED',runtimePid=self.runtime.pid,exitCode=helper_exit,observedBy='PERSISTENCE_PREREQUISITE_POLL');"
  original="  assert self.attempt=='26'and self.runtime is not None and self.runtime.poll()==0,'BOOT26_MUST_BE_CLOSED_BEFORE27';";assert got.count(start)==1;got=got.replace(start,original,1)
  for block in ["  if self.host_process is not None:\n   host_exit=self.host_process.poll()\n   if host_exit is not None:self.cleanup_emit('OWNED_HOST_NUMERIC_EXIT_OBSERVED',pid=self.host_process.pid,exitCode=host_exit,observedBy='POLL_AFTER_EXISTING_CLOSE')\n","   helper_exit=self.runtime.poll()\n   if helper_exit is not None:self.cleanup_emit('OWNED_RUNTIME_HELPER_NUMERIC_EXIT_OBSERVED',runtimePid=self.runtime.pid,exitCode=helper_exit,observedBy='POLL_AFTER_EXISTING_WAIT')\n"]:assert got.count(block)==1;got=got.replace(block,'',1)
  caller_new="   d=module('beta_device','qa-device-actions.py');before_receipt=c.get('beforeReceipt')\n   if op=='store-after'and before_receipt is not None:before_receipt=str(Path(before_receipt).resolve())\n   return d.run(self.attempt,op,c.get('variant',''),before_receipt=before_receipt)"
  caller_old="   d=module('beta_device','qa-device-actions.py');return d.run(self.attempt,op,c.get('variant',''),before_receipt=c.get('beforeReceipt'))";assert got.count(caller_new)==1;got=got.replace(caller_new,caller_old,1)
  delta='namespace plus numeric exit observations from existing poll/wait paths, no new wait/signal; canonical absolute snapshot caller'
 if name=='qa-ap-admission.py':
  expected=expected.replace("'priorGeneration09SITLRequests'];expected=[11,1,1,1,1,2,2]","'priorGeneration09SITLRequests','priorGeneration12SITLRequests'];expected=[11,1,1,1,1,2,2,2]").replace('EXACT_NINETEEN_HISTORICAL_REQUESTS_REQUIRED','EXACT_TWENTYONE_HISTORICAL_REQUESTS_REQUIRED').replace('len(set(runs))==19','len(set(runs))==21')
  begin=got.index("    expected_g12=");end=got.index('    return runs\n',begin);block=got[begin:end];assert "'sc0dc57bafd5d41d186f0':'a82e523ee15fa5608a12e6561b70fe75eacb6757bc7b056e5799227bf4051eff'"in block and "'s982daac712214515a0d3':'8477147b25cfa96c2c586b53deccd5e2f88275e1385e9247df8f9e14edef6c68'"in block;got=got[:begin]+got[end:];delta='namespace plus explicit 21 historical actual requests and bounded original G12 SHA/mode/run checks'
 assert got==expected,('UNDECLARED_DELTA',name)
 if name.endswith('.py'):
  nums=lambda t:[n.value for n in ast.walk(ast.parse(t))if isinstance(n,ast.Constant)and type(n.value)in(int,float)]
  assert nums(got)==nums(expected)
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'originalPath':str(old.relative_to(R)),'originalSha256':H(old),'delta':delta})
checks={'wholeSourceNormalization':{'rows':rows,'namespaceMap':mapping,'status':'PASS_DECLARED_DELTAS_ONLY'}}
c=load('g13_test_controller',P/'qa-root-controller.py');a=load('g13_test_airborne',P/'qa-airborne.py');ground=load('g13_test_ground',P/'qa-ground-soak.py');pg=load('g13_test_ports',P/'qa-port-guard.py')
assert c.b is r.b is ui.b is a.b is ground.b is b and c.g.host_clock is pg.host_clock is k
assert c.Controller.__init__.__kwdefaults__['clock']is c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is r.validate_parent_permit.__kwdefaults__['clock']is ui.receipt_observation.__defaults__[1]is a.wait_target_ready.__defaults__[1]is ground.collect.__kwdefaults__['clock']is pg.probe_host_ports.__kwdefaults__['clock']is k.now_s
boot=k.boot_id();ctl=c.Controller('26',boot_reader=lambda:boot);ctl.host_anchor=k.now_s()-1;ctl.guard.anchor_emulator_before_launch('emulator-5582');proof=ctl.emit('MOCK_CLOCK_ONLY_ANCHOR',anchors=ctl.guard.snapshot());permit={'attempt':'26','clockBasis':k.BASIS,'hostBootId':boot,'rootControllerPid':os.getpid(),'anchorProof':proof,'parentHostRemainingS':ctl.host_remaining(),'hostBeforeLaunchPythonMonoS':ctl.host_anchor,'parentHostDeadlinePythonMonoS':ctl.host_anchor+2700};before=k.now_s()
child=subprocess.run(['/usr/bin/python3','-B',str(Path(__file__).resolve()),'--clock-child'],input=json.dumps(permit).encode(),capture_output=True,timeout=5,env={**os.environ,'BETA06_CLOCK_BASIS':k.BASIS,'BETA06_HOST_BOOT_UUID':boot,'BETA06_ROOT_CONTROLLER_PID':str(os.getpid())});after=k.now_s();assert child.returncode==0,(child.returncode,child.stderr[:2048]);answer=json.loads(child.stdout);assert before<=answer['binding']['receivedPythonMonoS']<=after and answer['binding']['parentHostDeadlinePythonMonoS']==ctl.host_anchor+2700
checks['clockDefaultsAndChild']={'status':'PASS_CURRENT_G13_CANONICAL_IDENTITY_AND_REAL_CLOCK_ONLY_CHILD','child':answer,'parentBeforeS':before,'parentAfterS':after,'noControllerLaunchThread':True}
# Reuse the declared snapshot test recipe, with new effective G13 module and its own sink.
recipe=R/'planning/heartbeat13fix/native-snapshot-tests02.py';tree=ast.parse(recipe.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='one');body=ast.get_source_segment(recipe.read_text(),fn).replace("patch.object(b,'write_bytes'","patch.object(module.b,'write_bytes'").replace("patch.object(b,'write_json'","patch.object(module.b,'write_json'").replace("module.run('24'","module.run('24'if module is old else'26'").replace('codex-tmp-heartbeat13fix-20261023-','codex-tmp-beta06g13-20261023-')
old=load('g13_snapshot_old_witness',G/'qa-device-actions.py');new=load('g13_snapshot_current',P/'qa-device-actions.py');baseline=json.loads((R/old.G3_BASELINE).read_bytes());journal=(R/baseline['journalFile']).read_bytes();native_root='/data/user/0/vn.rtr.aeris.field02/files/field02';boot='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';cases=[];scratch=[];exec(compile(body,str(recipe),'exec'),globals())
one(old,'relative','old');one(new,'absolute','success');one(new,'relative','success');one(new,'outside','outside');one(new,'absolute','invalid',mutation='empty-object');one(new,'absolute','invalid',mutation='chain')
assert all(not p.exists()for p in scratch);checks['effectiveCurrentSnapshot']={'status':'PASS_OLD_WITNESS_CURRENT_ABSOLUTE_RELATIVE_AND_ZERO_WRITE_NEGATIVES','cases':cases,'sharedRecipe':str(recipe.relative_to(R)),'sharedRecipeSha256':H(recipe),'scratchRemoved':[p.name for p in scratch]}
ad=load('g13_test_admission',P/'qa-ap-admission.py');pins=json.loads((R/'evidence/beta06/generation12/flight-pins01.json').read_bytes());pins['priorGeneration12SITLRequests']=[{'run':run,'requestSha256':H(R/'evidence/beta06/generation12/flight/runs'/run/'request.json')}for run in ['sc0dc57bafd5d41d186f0','s982daac712214515a0d3']];assert len(ad.historical_runs(pins))==21
for mode in ['missing','bad-sha','duplicate']:
 bad=copy.deepcopy(pins)
 if mode=='missing':bad.pop('priorGeneration12SITLRequests')
 elif mode=='bad-sha':bad['priorGeneration12SITLRequests'][0]['requestSha256']='0'*64
 else:bad['priorGeneration12SITLRequests'][1]=bad['priorGeneration12SITLRequests'][0]
 try:ad.historical_runs(bad);raise AssertionError('BAD_HISTORY_ACCEPTED')
 except AssertionError as exc:assert str(exc)!='BAD_HISTORY_ACCEPTED'
checks['history21']='PASS_ORIGINAL_TWO_G12_FILES_AND_MISSING_SHA_DUPLICATE_NEGATIVES'
# Observe only numeric poll results. Existing cleanup calls are fake, never product signals.
observed=[]
for code in [0,-15,None]:
 ctl=c.Controller('26',boot_reader=lambda:'11111111-2222-3333-4444-555555555555');events=[];ctl.cleanup_emit=lambda event,**data:events.append({'event':event,**data})
 def wait(timeout):
  if code is None:raise subprocess.TimeoutExpired('mock-runtime',timeout)
  return code
 fake=types.SimpleNamespace(pid=12345,poll=lambda:code,wait=wait,terminate=lambda:None);ctl.runtime=fake
 if code is not None:ctl.host_process=types.SimpleNamespace(pid=54321,poll=lambda:code)
 with tempfile.TemporaryDirectory(prefix='codex-tmp-beta06g13-20261023-',dir=P)as tmp,patch.object(c,'E',Path(tmp)),patch.object(b,'write_json',return_value=None):ctl.close()
 nums=[e for e in events if e['event']=='OWNED_RUNTIME_HELPER_NUMERIC_EXIT_OBSERVED'];assert len(nums)==(0 if code is None else 1)
 if nums:assert nums[0]['exitCode']==code
 hosts=[e for e in events if e['event']=='OWNED_HOST_NUMERIC_EXIT_OBSERVED'];assert len(hosts)==(0 if code is None else 1)
 if hosts:assert hosts[0]['exitCode']==code
 observed.append({'poll':code,'events':events})
checks['numericHelperExitObservation']={'status':'PASS_ONLY_ACTUAL_NUMERIC_POLL_NO_PID_INFERENCE','cases':observed}
forwarded=[]
for name in ['relative','absolute']:
 ctl=c.Controller('26',boot_reader=lambda:'11111111-2222-3333-4444-555555555555',clock=lambda:100);ctl.host_anchor=100;ctl.guard.anchor_emulator_before_launch('emulator-5582');reference=E/'workspace-copy01.json';value=str(reference.relative_to(R))if name=='relative'else str(reference)
 fake_device=types.SimpleNamespace(run=lambda *a,**kw:forwarded.append(kw['before_receipt']))
 with patch.object(c,'module',return_value=fake_device):ctl.command({'op':'store-after','commandId':'mock-path-'+name,'rootApproved':True,'beforeReceipt':value})
assert forwarded==[str(reference.resolve())]*2
checks['snapshotCallerAbsolute']='PASS_RELATIVE_AND_ABSOLUTE_CANONICAL_BEFORE_DEVICE_DISPATCH'
inventory=[]
for name in ops:
 path=P/('qa-root-live26.py'if name=='qa-root-live24.py'else name)
 if path.suffix=='.py':assert not[n for n in ast.walk(ast.parse(path.read_text()))if isinstance(n,ast.Attribute)and n.attr in ['monotonic','monotonic_ns','perf_counter','perf_counter_ns']];inventory.append({'path':str(path.relative_to(R)),'sha256':H(path)})
checks['staticClockSites']={'status':'PASS_CURRENT_NATIVE_NO_RELATIVE_CLOCK_ATTRIBUTE','rows':inventory,'groundReuse':'Current ground byteexact namespace of G12 actual75s/mock151-case proof; not recounted here.'}
actual=[p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller26','root-controller27','root-runtime26','root-runtime27','host-app13','host-console','quota-native-ledger','workspace-first-writer'))];assert not actual;checks['actualNamespacePristine']='PASS_NO_MOCK_ARTIFACTS'
report={'status':'PASS_G13_NATIVE_FOCUSED_SOURCE_MOCK_ONLY','groups':len(checks),'checks':checks,'providerSha256':H(R/'pilot/beta06g13/clock_basis.py'),'testSha256':H(Path(__file__)),'scope':'No product host/emulator/Android/AP/ADB/browser/network/listener/build/install/sign. Only one bounded real clock-only Apple child, fake snapshot ADB/sinks and fake cleanup processes; no preparedworkspace/operational ledger access.','inheritedEvidence':'G12 and PhaseA corrected snapshot/clock/ground/observer evidence reused only after exact stated source normalization; no old actual outcomes pooled.','runtimePerformed':False}
out=E/'builder-native-tests02.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(checks),'sha256':H(out),'path':str(out)}))
