"""Final bounded source-delta check after two Root-authorized G17 interface guards."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation17';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cfg=json.loads((P/'builder-namespace-map.json').read_bytes());prior=json.loads((R/'evidence/beta06/generation15/native-helper-freeze01.json').read_bytes());rows=[]
def namespace(s):
 for a,b in cfg['map']:s=s.replace(a,b)
 return s
old_watch="   self.proof=admit('runtime',remaining_ap=remaining_ap,remaining_hosts=remaining_hosts,closed_runs=list(closed_runs),claim_id=claim,cancel_event=self.stopped);self.last=clock()"
new_watch="   assert not self.stopped.is_set(),'SHARED_QUOTA_AUDIT_CLOSED';started=clock();proof=admit('runtime',remaining_ap=remaining_ap,remaining_hosts=remaining_hosts,closed_runs=list(closed_runs),claim_id=claim,cancel_event=self.stopped);elapsed=clock()-started;assert not self.stopped.is_set()and 0<=elapsed<=load()['scanner']['staleMs']/1000,'SHARED_QUOTA_AUDIT_STALE_OR_CLOSED_AT_COMPLETION';self.proof=proof;self.last=started"
for name in cfg['operationalFiles']:
 old=R/'planning/beta06g15'/name;new=P/('qa-root-live32.py'if name=='qa-root-live30.py'else name);assert H(old)==prior['files'][str(old.relative_to(R))];got=new.read_text();delta='namespace only'
 if name=='qa-root-controller.py':
  guard="assert 'resourceEvidenceFailure'in value and value['resourceEvidenceFailure']is None,'HOST_RESOURCE_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';";assert got.count(guard)==1;got=got.replace(guard,'',1);assert hashlib.sha256(got.encode()).hexdigest()==H(P/'nativebuilder-controller-before-resource-guard.py');delta='namespace +explicit clean resource closure key/null'
 if name=='qa-native-budget.py':
  assert got.count(new_watch)==1;got=got.replace(new_watch,old_watch,1);closed=" def check(self):\n  assert not self.stopped.is_set(),'SHARED_QUOTA_AUDIT_CLOSED'\n  if self.error:raise RuntimeError('SHARED_SCOPED_QUOTA_RUNTIME_REFUSED:'";original=" def check(self):\n  if self.error:raise RuntimeError('SHARED_SCOPED_QUOTA_RUNTIME_REFUSED:'";assert got.count(closed)==1;got=got.replace(closed,original,1);assert hashlib.sha256(got.encode()).hexdigest()==H(P/'nativebuilder-budget-before-dispatch-age.py');delta='namespace +conservative dispatch age and stale/closed completion exclusion using existing15s policy'
 assert got==namespace(old.read_text()),('UNAPPROVED_DELTA',name)
 if name.endswith('.py'):
  nums=lambda t:[n.value for n in ast.walk(ast.parse(t))if isinstance(n,ast.Constant)and type(n.value)in(int,float)];assert nums(got)==nums(old.read_text());compile(new.read_text(),str(new),'exec')
 rows.append({'path':str(new.relative_to(R)),'sha256':H(new),'priorPath':str(old.relative_to(R)),'priorSha256':H(old),'delta':delta})
s=importlib.util.spec_from_file_location('g17_final_controller',P/'qa-root-controller.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c);assert c.Controller.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s;assert c.g.DeadlineGuard.__init__.__kwdefaults__['clock']is c.b.host_clock.now_s;assert H(R/'pilot/beta06g17/clock_basis.py')=='40fba1dc750f09ba042668c916547f88ef59eb05c0c9de2f07bd8defcb5bda17'
proofs=['nativebuilder-tests01.json','nativebuilder-tests02.json','nativebuilder-closure01.json','nativebuilder-quota-age-before01.json','nativebuilder-quota-age01.json','nativebuilder-ui01.json','nativebuilder-ui-app01.json'];report={'status':'PASS_FINAL20_WITH_TWO_APPROVED_GUARD_DELTAS','rows':rows,'testSha256':H(Path(__file__)),'proofs':[{'path':str((E/n).relative_to(R)),'sha256':H(E/n)}for n in proofs],'evidenceDisposition':'Earlier proofs preserve source point-in-time. Current reverse-exact whole-source test and separate targeted closure/dispatch-age proofs amend only their approved deltas; no pooled/recounted actual outcomes. Current UI fullfactory proof is explicitly effect-stubbed, no sockets/physical admission.','thresholds':'Original all numeric predicates unchanged after removal of the precise two authorized added guards; new completion check repeats only existing0..scanner.staleMs/1000 (15s).','providerDefaultIdentity':'PASS_CURRENT_IMPORT_NO_RELATIVE_CLOCK','runtimePerformed':False}
out=E/'nativebuilder-final-source01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'sourceRows':len(rows)}))
