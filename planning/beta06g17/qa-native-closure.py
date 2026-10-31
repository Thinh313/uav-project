"""Only approved resource-evidence predicate plus fake managed-close interface."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,tempfile,types
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation17';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((E/'qa-native-cooperation01.json').read_bytes());controller=P/'qa-root-controller.py';saved=P/'nativebuilder-controller-before-resource-guard.py';key=str(controller.relative_to(R));assert H(saved)==prior['source'][key]
addition="assert 'resourceEvidenceFailure'in value and value['resourceEvidenceFailure']is None,'HOST_RESOURCE_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';"
current=controller.read_text();assert current.count(addition)==1 and current.replace(addition,'')==saved.read_text();assert H(controller)=='4106dfdf7acd4b82075abf75f521fe11c5891a791c5c461cd04019180d82069c'
for n,h in prior['source'].items():
 if n!=key:assert H(R/n)==h,n
s=importlib.util.spec_from_file_location('qa_g17_resource_closure',controller);c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c);cases=[];removed=[]
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
for mode in ['NULL','MISSING','ERROR','FALSE']:
 with tempfile.TemporaryDirectory(prefix='codex-tmp-g17-qa-native-close-20261024-',dir=P)as tmp:
  d=Path(tmp);removed.append(str(d.relative_to(R)));v={'reason':'EXPLICIT_STOP','payloadEvidenceFailure':None,'closeIndexFailure':None,'resourceEvidenceFailure':None}
  if mode=='MISSING':v.pop('resourceEvidenceFailure')
  if mode=='ERROR':v['resourceEvidenceFailure']='WORKER_CLOSE_FAILED'
  if mode=='FALSE':v['resourceEvidenceFailure']=False
  (d/'app-closure.json').write_text(json.dumps(v));calls=[];ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:{'flight':{'run':None,'authority':None,'busy':False},'payloadLeaseObservation':{'leaseCount':0}}),observation=lambda:{'observation':{'mediaReadiness':{'active':False}}});ctl=c.Controller('32',boot_reader=lambda:'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',clock=lambda:100,ui=ui);ctl.host_process=types.SimpleNamespace(pid=123456,poll=lambda:None,terminate=lambda:calls.append('FAKE_TERMINATE'),wait=lambda timeout:(calls.append('FAKE_WAIT'),0)[1]);ctl.host_out=d;ctl.host_instances=1;ctl.host_anchor=100;ctl.host_log=types.SimpleNamespace(close=lambda:calls.append('FAKE_LOG_CLOSE'))
  try:proof=ctl.stop_host({'sourceAndViewerStoppedAndInspected':True});assert mode=='NULL';assert proof['exit']==0;accepted=True
  except AssertionError as ex:assert mode!='NULL'and str(ex)=='HOST_RESOURCE_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';assert ctl.host_stop_proof is None and not ctl.host_restart_allowed;accepted=False
  assert calls[:2]==['FAKE_TERMINATE','FAKE_WAIT'];cases.append({'case':mode,'status':'PASS','managedClosureProofAccepted':accepted,'scope':'Actual Controller.stop_host; fake process/UI plus owned tiny closure fixture, no actual PID signal or restart.'})
assert all(not(R/n).exists()for n in removed)
source={**prior['source'],key:H(controller)};report={'status':'PASS_G17_CURRENT_NATIVE_APPROVED_CLOSURE_DELTA_SOURCE_MOCK_ONLY','source':source,'amends':{'path':'evidence/beta06/generation17/qa-native-cooperation01.json','sha256':H(E/'qa-native-cooperation01.json'),'reason':'Prior20source proof remains exact except this sole approved resource-evidence predicate.'},'approvedDelta':addition,'canonicalProviderSha256':prior['canonicalProviderSha256'],'cases':cases,'removed':removed,'allScratchRemoved':True,'actualRuntimeEffects':0,'recipeSha256':H(Path(__file__))}
out=E/'qa-native-current01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'bytes':out.stat().st_size,'cases':len(cases),'sourceControllerSha':H(controller)}))
