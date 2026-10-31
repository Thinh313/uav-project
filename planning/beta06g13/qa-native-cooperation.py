"""Independent declared-delta/exit/caller checks, no real processes or Native inputs."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys,tempfile,types
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation13'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
assert tuple(sys.version_info[:3])==(3,9,6)
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
builder=E/'builder-native-tests02.json';assert H(builder)=='f7a6166c0383441cf5a988a6d740ebb161a3e6574a73ef93fab26a00593e9ba4'
proof=json.loads(builder.read_bytes());rows=proof['checks']['wholeSourceNormalization']['rows']
for row in rows:assert H(R/row['path'])==row['sha256']and H(R/row['originalPath'])==row['originalSha256']
mapping=proof['checks']['wholeSourceNormalization']['namespaceMap']
def ns(s):
 for old,new in mapping:s=s.replace(old,new)
 return s
for name in ['qa-ground-soak.py','qa-ui.py','qa-airborne.py','qa-deadline-guard.py','qa-runtime.py','qa-port-guard.py']:
 assert (P/name).read_text()==ns((R/'planning/beta06g12'/name).read_text()),name
assert (P/'qa-device-actions.py').read_text()==ns((R/'planning/heartbeat13fix/qa-device-actions.py').read_text())
provider=R/'pilot/beta06g13/clock_basis.py';assert H(provider)=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
c=load('qa_independent_g13_controller',P/'qa-root-controller.py')
assert c.Controller.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s
assert c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s
exit_cases=[];cleaned=[]
for host_code,helper_code in [(0,0),(-15,-15),(None,None)]:
 ctl=c.Controller('26',boot_reader=lambda:'11111111-2222-3333-4444-555555555555',clock=lambda:100)
 events=[];calls=[];ctl.cleanup_emit=lambda event,**data:events.append({'event':event,**data})
 def process(pid,code):
  return types.SimpleNamespace(pid=pid,poll=lambda:code,wait=lambda timeout:calls.append(['wait',pid,timeout])or code,terminate=lambda:calls.append(['terminate',pid]),kill=lambda:calls.append(['kill',pid]))
 ctl.host_process=process(54321,host_code);ctl.runtime=process(12345,helper_code)
 with tempfile.TemporaryDirectory(prefix='codex-tmp-qa-g13-exit-20261023-',dir=P)as temp:
  root=Path(temp);writes=[]
  with patch.object(c,'E',root),patch.object(c.b,'write_json',side_effect=lambda *a,**kw:writes.append(str(a[0]))):ctl.close()
  assert all(Path(p).parent==root for p in writes)
 cleaned.append(str(root.relative_to(R)));assert not root.exists()
 for name,code in [('OWNED_HOST_NUMERIC_EXIT_OBSERVED',host_code),('OWNED_RUNTIME_HELPER_NUMERIC_EXIT_OBSERVED',helper_code)]:
  got=[e for e in events if e['event']==name];assert len(got)==(0 if code is None else 1)
  if got:assert type(got[0]['exitCode'])is int and got[0]['exitCode']==code
 assert not any(v[0]=='kill'for v in calls)
 exit_cases.append({'hostPoll':host_code,'helperPoll':helper_code,'events':events,'existingCleanupCalls':calls})
forwarded=[]
for relative in [True,False]:
 ctl=c.Controller('26',boot_reader=lambda:'11111111-2222-3333-4444-555555555555',clock=lambda:100);ctl.host_anchor=100;ctl.guard.anchor_emulator_before_launch('emulator-5582')
 p=E/'workspace-copy01.json';given=str(p.relative_to(R))if relative else str(p)
 with patch.object(c,'module',return_value=types.SimpleNamespace(run=lambda *a,**kw:forwarded.append(kw['before_receipt']))):ctl.command({'op':'store-after','commandId':'qa-g13-path-'+str(relative).lower(),'rootApproved':True,'beforeReceipt':given})
assert forwarded==[str((E/'workspace-copy01.json').resolve())]*2
assert not [p.name for p in E.iterdir()if p.name.startswith(('android-','root-controller26','root-controller27','root-runtime26','root-runtime27','host-app13','host-console','quota-native-ledger','workspace-first-writer'))]
report={'status':'PASS_G13_NATIVE_TARGETED_SOURCE_MOCK_ONLY','checks':{'currentBuilderProofExact':True,'listedSourceHashesExact':len(rows),'independentExactNamespaceGuardFunctions':6,'snapshotExactCorrectedPrototype':True,'providerAndEffectiveDefaultsExact':True,'numericExitCases':exit_cases,'absoluteCallerForwarded':forwarded,'actualNamespacePristine':True},'source':{row['path']:row['sha256']for row in rows},'providerSha256':H(provider),'recipeSha256':H(Path(__file__)),'scratchRemoved':cleaned,'limits':'Fake process handles and output sinks only; no runtime launch, wait/signal to real processes, ADB/network or mutable store. PhaseA effective snapshot eight cases reused after exact whole-source namespace equality. Builder full normalization reviewed with explicit declared controller/history deltas, not recounted as independent executions.'}
out=E/'qa-native-cooperation01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'sha256':H(out),'bytes':out.stat().st_size}))
