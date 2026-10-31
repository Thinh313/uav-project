"""Only G17 explicit resource closure interface, fake process/UI; no runtime."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,tempfile,types
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'evidence/beta06/generation17';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=importlib.util.spec_from_file_location('g17_closure_test',P/'qa-root-controller.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c);cases=[];scratch=[]
for mode in ['valid','missing','failed']:
 with tempfile.TemporaryDirectory(prefix='codex-tmp-g17-native-closure-20261024-',dir=P)as tmp:
  root=Path(tmp);scratch.append(root.name);value={'reason':'EXPLICIT_STOP','payloadEvidenceFailure':None,'closeIndexFailure':None,'resourceEvidenceFailure':None}
  if mode=='missing':value.pop('resourceEvidenceFailure')
  if mode=='failed':value['resourceEvidenceFailure']='OWNED_AUDIT_WORKER_CLOSE_FAILED'
  (root/'app-closure.json').write_text(json.dumps(value));ctl=c.Controller('32',boot_reader=lambda:'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',clock=lambda:100,ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:{'flight':{'run':None,'authority':None,'busy':False},'payloadLeaseObservation':{'leaseCount':0}}),observation=lambda:{'observation':{'mediaReadiness':{'active':False}}}));ctl.host_process=types.SimpleNamespace(pid=12345,poll=lambda:None,terminate=lambda:None,wait=lambda timeout:0);ctl.host_out=root;ctl.host_instances=1;ctl.host_anchor=100;ctl.host_log=types.SimpleNamespace(close=lambda:None)
  try:
   result=ctl.stop_host({'sourceAndViewerStoppedAndInspected':True});assert mode=='valid';assert result['exit']==0;cases.append({'case':mode,'status':'PASS_EXPLICIT_RESOURCE_CLOSURE_NULL'})
  except AssertionError as exc:
   assert mode!='valid'and str(exc)=='HOST_RESOURCE_CLOSURE_UNKNOWN_OR_FAILED_NO_RESTART';assert ctl.host_stop_proof is None and ctl.host_restart_allowed is False;cases.append({'case':mode,'status':'PASS_REFUSED_NO_MANAGED_RESTART','error':str(exc)})
assert all(not(P/name).exists()for name in scratch)
report={'status':'PASS_TARGETED_RESOURCE_CLOSURE_INTERFACE','source':{'path':str((P/'qa-root-controller.py').relative_to(R)),'sha256':H(P/'qa-root-controller.py')},'preservedBefore':{'path':str((P/'nativebuilder-controller-before-resource-guard.py').relative_to(R)),'sha256':H(P/'nativebuilder-controller-before-resource-guard.py')},'testSha256':H(Path(__file__)),'cases':cases,'scope':'Fake UI/process polls/wait only, tiny closureJSON ownfixtures. No product effects/socket/ADB/threads/ledger/workspace.','scratchRemoved':scratch,'runtimePerformed':False};out=E/'nativebuilder-closure01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(out),'cases':len(cases),'sourceSha256':H(P/'qa-root-controller.py')}))
