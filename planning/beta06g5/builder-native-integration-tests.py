"""Effective G5 controller/R2/visible-dispatch seam and compact restart index mocks."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,sys,tempfile,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation05'
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=mod('G5_effective_controller',P/'qa-root-controller.py');r=mod('G5_index_restart',P/'qa-restart-proof.py');a=mod('G5_admission',P/'qa-ap-admission.py');fixture=mod('G5_retained_R2_fixture',R/'planning/beta06g4r2/test_complete_nominal_policy.py');examples={}
sha=lambda b:hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
 def exercise(self,mutate=None,post_pending=False,diagnostic_failure=None):
  state=copy.deepcopy(fixture.state);view=copy.deepcopy(fixture.view);ref=copy.deepcopy(fixture.ref);calls=[];closed=[False]
  if mutate:mutate(state,view)
  def state_reader():return {'ok':True,'closeIndexFailure':{'status':'CLOSED_REVIEW_INDEX_PENDING'}if post_pending else None,'flight':{'run':None}}if closed[0]else copy.deepcopy(state)
  def dispatch(attempt,reference,target,name,**kw):
   self.assertEqual(target,'field-close');calls.append({'target':target,'name':name,'timeout':kw['timeout']});closed[0]=True;return {'status':'ACKNOWLEDGED','targetId':target}
  ui=types.SimpleNamespace(q=types.SimpleNamespace(state=state_reader),observation=lambda:copy.deepcopy(view),receipt_observation=lambda end:copy.deepcopy(view),phase_policy=fixture.ui.phase_policy,dispatch=dispatch)
  ctl=c.Controller('10',boot_reader=lambda:'MOCK_BOOT',clock=lambda:100,ui=ui);ctl.closure_reserve=lambda:90;ctl.connect_count=1
  with tempfile.TemporaryDirectory(prefix='builder-g5-close-',dir=E)as tmp:
   out=Path(tmp);reference=out/'inspected-reference.json';reference.write_text(json.dumps(ref));command={'op':'complete-nominal','rootApproved':True,'commandId':'g5-mock-complete','run':fixture.run,'reference':str(reference),'waitSeconds':1}
   with patch.object(c,'E',out):
    if diagnostic_failure:
     with patch.object(c.CompletionPollDiagnostics,'append',side_effect=OSError('MOCK_DISK_FAILURE')):
      with self.assertRaises(OSError):ctl.command(command)
    elif mutate or post_pending:
     with self.assertRaises(AssertionError):ctl.command(command)
    else:result=ctl.command(command);self.assertEqual(result['status'],'ACKNOWLEDGED')
   summary=json.loads((out/'g5-mock-complete-completion-summary.json').read_text());snap=out/'g5-mock-complete-completion-last-inputs.json';proof=json.loads(snap.read_text())if snap.exists()else None;polls=(out/'g5-mock-complete-completion-polls.jsonl').read_text();examples['lastEffectiveMock']={'summary':summary,'inputClassification':proof.get('classification')if proof else None,'pollRecords':len(polls.splitlines())}
   if proof:
    self.assertEqual(proof['state']['flight']['live']['stage'],'AUTO');self.assertNotIn('workspace',proof['state']);self.assertEqual(proof['fullViewAtReadSha256'],sha(json.dumps(view,separators=(',',':'),allow_nan=False).encode()));self.assertEqual(proof['timing']['stateReadEndPythonMonoS'],100)
   return calls,ctl,summary
 def test_effective_controller_imports_R2_policy_and_calls_unchanged_visible_dispatch_once(self):
  calls,ctl,summary=self.exercise();self.assertEqual(len(calls),1);self.assertEqual(calls[0]['timeout'],20);self.assertFalse(ctl.campaign_failed);self.assertEqual(summary['status'],'VISIBLE_CLOSE_ACKNOWLEDGED_NOT_RAW_ACCEPTANCE');self.assertEqual(summary['records'],2)
 def test_new_terminal_ACK_guard_refuses_pending_index_and_latches_without_second_effect(self):
  calls,ctl,summary=self.exercise(post_pending=True);self.assertEqual(len(calls),1);self.assertTrue(ctl.campaign_failed);self.assertEqual(summary['status'],'FAILED_OR_PARTIAL_NO_RETRY')
 def test_readiness_stale_or_changed_model_refuses_before_dispatch(self):
  for mutate in [lambda s,v:v.update(ageMs=1201),lambda s,v:s['flight']['request'].update(planSha256='WRONG')]:
   calls,ctl,summary=self.exercise(mutate=mutate);self.assertEqual(calls,[]);self.assertTrue(ctl.campaign_failed)
 def test_perpoll_diagnostic_writer_failure_blocks_input(self):
  calls,ctl,summary=self.exercise(diagnostic_failure=True);self.assertEqual(calls,[]);self.assertTrue(ctl.campaign_failed);self.assertEqual(summary['errorClass'],'OSError')
 def test_diagnostic_size_and_poll_limits_fail_loud_without_discard(self):
  with tempfile.TemporaryDirectory(prefix='builder-g5-diag-bound-',dir=E)as tmp,patch.object(c,'E',Path(tmp)):
   d=c.CompletionPollDiagnostics('size',lambda:1);d.MAX_BYTES=1
   with self.assertRaisesRegex(AssertionError,'4MIB'):d.append('POLL',{'a':1})
   self.assertEqual(d.bytes,0);d.close('REFUSED')
   d=c.CompletionPollDiagnostics('count',lambda:1);d.count=d.MAX_POLLS+4
   with self.assertRaisesRegex(AssertionError,'RECORD_BOUND'):d.append('POLL',{})
   d.close('REFUSED')
 def test_managed_host_closure_with_index_failure_cannot_authorize_restart(self):
  class Proc:
   pid=123
   def poll(self):return None
   def terminate(self):pass
   def wait(self,timeout):return 0
  ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:{'flight':{'run':None,'authority':None,'busy':False},'payloadLeaseObservation':{'leaseCount':0}}),observation=lambda:{'observation':{'mediaReadiness':{'active':False}}})
  ctl=c.Controller('10',boot_reader=lambda:'BOOT',clock=lambda:100,ui=ui);ctl.host_process=Proc()
  with tempfile.TemporaryDirectory(prefix='builder-g5-host-close-',dir=E)as tmp:
   ctl.host_out=Path(tmp);(ctl.host_out/'app-closure.json').write_text(json.dumps({'payloadEvidenceFailure':None,'reason':'EXPLICIT_STOP','closeIndexFailure':{'status':'CLOSED_REVIEW_INDEX_PENDING'}}))
   with self.assertRaisesRegex(AssertionError,'HOST_CLOSURE_UNKNOWN'):ctl.stop_host({'sourceAndViewerStoppedAndInspected':True})
  self.assertFalse(ctl.host_restart_allowed)
 def test_unchanged_namespace_only_replayers_and_shared_canonical_import(self):
  for name in ['qa-raw-flight.mjs','qa-cut-replay.mjs','qa-reboot-replay.mjs','qa-overlap-replay.mjs','qa-native-replay.py','qa-media-replay.py']:
   expected=(R/'planning/beta06g4'/name).read_text().replace('generation04','generation05').replace('beta06g4','beta06g5');self.assertEqual((P/name).read_text(),expected,name)
 def test_unchanged_guard_runtime_ground_UI_airborne_algorithms_only_namespace_attempts(self):
  for name in ['qa-runtime.py','qa-deadline-guard.py','qa-ui.py','qa-android.py','qa-airborne.py','qa-ground-soak.py']:
   expected=(R/'planning/beta06g4'/name).read_text().replace('generation04','generation05').replace('GENERATION04','GENERATION05').replace('beta06g4','beta06g5').replace('BETA06G4','BETA06G5').replace("['06','07']","['10','11']").replace('BOOT06','BOOT10').replace('BOOT07','BOOT11').replace('boot06','boot10').replace('boot07','boot11');self.assertEqual((P/name).read_text(),expected,name)
 def test_actual20file_workspacecopy_firstwriter_guard_and_drift_refusal(self):
  ctl=c.Controller('10',boot_reader=lambda:'BOOT',clock=lambda:100);proof=ctl.workspace_before_first_writer();self.assertEqual(proof['files'],20);self.assertEqual(proof['bytes'],870221)
  with patch.object(c.hashlib,'sha256',return_value=types.SimpleNamespace(hexdigest=lambda:'BAD')):
   with self.assertRaisesRegex(AssertionError,'WORKSPACE_DRIFT'):ctl.workspace_before_first_writer()
 def test_plan10_11_original2700_AP540_and_old_G4_request_in_history(self):
  plan=c.plan();self.assertEqual(plan['attempts'],['10','11']);self.assertEqual(plan['hostBudgetSecondsAcrossBothBoots'],2700);self.assertEqual(plan['apBudgetSeconds'],540);pins=json.loads((R/'evidence/beta06/generation04/flight-pins.json').read_text());pins['priorGeneration04SITLRequests']=[{'run':fixture.run,'requestSha256':sha((R/'evidence/beta06/generation04/flight/runs'/fixture.run/'request.json').read_bytes())}];self.assertEqual(len(a.historical_runs(pins)),15);pins['priorGeneration04SITLRequests'][0]['requestSha256']='0'*64
  with self.assertRaisesRegex(AssertionError,'G4_REQUEST_SHA'):a.historical_runs(pins)
 def sealed(self):
  run=fixture.run;rb=fixture.paths['review'].read_bytes();cb=fixture.paths['closure'].read_bytes();review=json.loads(rb);closure=json.loads(cb);ref={key:copy.deepcopy(review.get(key))for key in ['run','accepted','aborted','closedAt','modelSha256','planSha256','documentSha256','missionSha256','rawHead','rawRecords','execution','failure','writerError']};ref.update(format='aeris-sealed-flight-review-reference',version=1,authorityRestorable=False,review={'path':'flight/runs/'+run+'/review.json','bytes':len(rb),'sha256':sha(rb)},closure={'path':'flight/runs/'+run+'/closure.json','bytes':len(cb),'sha256':sha(cb),'containerId':closure['containerId'],'stopped':True});body={'data':{'reviewRef':ref,'authorityRestored':False},'kind':'FLIGHT_REVIEW_SEALED_REF','previousHash':'0'*64,'schemaVersion':1,'seq':1};h=sha(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode());row={**body,'hash':h};wal=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n';side={'status':'CLOSED_REVIEW_INDEXED','reviewIndexStatus':'INDEXED','effectStatus':'SEALED_OWNED_CLOSED','reviewRef':ref,'receipt':{'seq':1,'hash':h},'error':None};data={str(r.E/'flight/runs'/run/'review.json'):rb,str(r.E/'flight/runs'/run/'closure.json'):cb,str(r.E/'host-app05'/('close-index-'+run+'.json')):json.dumps(side).encode()};return run,wal,side,data
 def test_compact_restart_index_actual842keyreview_accepted_without_fullmap_canonicalization(self):
  run,wal,side,data=self.sealed()
  with patch.object(r,'blob',side_effect=lambda p,bound=0:data[str(p)]):proof=r.sealed_index_proofs(wal,[run])
  self.assertEqual(len(proof),1);self.assertEqual(proof[0]['reviewSha256'],sha(fixture.paths['review'].read_bytes()));self.assertGreater(len(json.loads(fixture.paths['review'].read_text())['filesSha256']),64)
 def test_pending_unknown_sidecar_or_tampered_bytes_refuse_restart(self):
  for mutation in ['pending','receipt','review']:
   run,wal,side,data=self.sealed();path=str(r.E/'host-app05'/('close-index-'+run+'.json'))
   if mutation=='pending':side['status']='CLOSED_REVIEW_INDEX_PENDING';data[path]=json.dumps(side).encode()
   elif mutation=='receipt':side['receipt']['hash']='0'*64;data[path]=json.dumps(side).encode()
   else:data[str(r.E/'flight/runs'/run/'review.json')]+=b' '
   with patch.object(r,'blob',side_effect=lambda p,bound=0:data[str(p)]):
    with self.assertRaises(AssertionError):r.sealed_index_proofs(wal,[run])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'classification':'G5_EFFECTIVE_CONTROLLER_R2_DISPATCH_SOURCE_MOCK_ONLY','status':'PASS_G5_NATIVE_INTEGRATION_MOCK'if result.wasSuccessful()else'FAIL','tests':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors],'sources':{str(p.relative_to(R)):sha(p.read_bytes())for p in P.glob('*')if p.is_file()},'examples':examples,'scope':'Actual new controller complete-nominal method imports immutable R2, real readiness/phase policy + fake UI visible-dispatch seam and state; retained old actual842keyreview for compactindex mock; no actualHTTP/listener/ADB/browser/AP/controllercampaign. All G5 actual scenarios USER_DEFERRED.'};out=E/(sys.argv[1]if len(sys.argv)>1 else'builder-native-integration01.json');out.open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if result.wasSuccessful()else 1)
