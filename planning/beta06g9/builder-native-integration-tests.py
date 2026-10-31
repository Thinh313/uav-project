"""Effective G9 controller/R2/visible-dispatch seam and compact restart index mocks."""
from pathlib import Path
import copy,io,hashlib,importlib.util,json,re,sys,tempfile,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation09'
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=mod('G9_effective_controller',P/'qa-root-controller.py');r=mod('G9_index_restart',P/'qa-restart-proof.py');a=mod('G9_admission',P/'qa-ap-admission.py');fixture=mod('G9_retained_R2_fixture',R/'planning/beta06g4r2/test_complete_nominal_policy.py');examples={}

class FakeQuota:
 def __init__(self):self.claims=[]
 def reserve_write(self,**claim):self.claims.append(claim);return claim
 def check_native_future(self,**kwargs):return {'status':'CAPACITY_AVAILABLE',**kwargs}
 def check_png_future(self,**kwargs):return self.check_native_future(**kwargs)
 def load_policy(self):return {'categories':{'screenshots':{'perFileBytes':5*2**20}},'scanner':{'staleMs':15000}}
fakequota=FakeQuota();c.b._quota=fakequota

sha=lambda b:hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
 def exercise(self,mutate=None,post_pending=False,diagnostic_failure=None):
  state=copy.deepcopy(fixture.state);view=copy.deepcopy(fixture.view);ref=copy.deepcopy(fixture.ref);calls=[];closed=[False]
  if mutate:mutate(state,view)
  def state_reader():return {'ok':True,'closeIndexFailure':{'status':'CLOSED_REVIEW_INDEX_PENDING'}if post_pending else None,'flight':{'run':None}}if closed[0]else copy.deepcopy(state)
  def dispatch(attempt,reference,target,name,**kw):
   self.assertEqual(target,'field-close');calls.append({'target':target,'name':name,'timeout':kw['timeout']});closed[0]=True;return {'status':'ACKNOWLEDGED','targetId':target}
  ui=types.SimpleNamespace(q=types.SimpleNamespace(state=state_reader),observation=lambda:copy.deepcopy(view),receipt_observation=lambda end:copy.deepcopy(view),phase_policy=fixture.ui.phase_policy,dispatch=dispatch)
  ctl=c.Controller('18',boot_reader=lambda:'MOCK_BOOT',clock=lambda:100,ui=ui);ctl.closure_reserve=lambda:90;ctl.connect_count=1
  with tempfile.TemporaryDirectory(prefix='builder-g9-close-',dir=E)as tmp:
   out=Path(tmp);reference=out/'inspected-reference.json';reference.write_text(json.dumps(ref));command={'op':'complete-nominal','rootApproved':True,'commandId':'g9-mock-complete','run':fixture.run,'reference':str(reference),'waitSeconds':1}
   with patch.object(c,'E',out):
    if diagnostic_failure:
     with patch.object(c.CompletionPollDiagnostics,'append',side_effect=OSError('MOCK_DISK_FAILURE')):
      with self.assertRaises(OSError):ctl.command(command)
    elif mutate or post_pending:
     with self.assertRaises(AssertionError):ctl.command(command)
    else:result=ctl.command(command);self.assertEqual(result['status'],'ACKNOWLEDGED')
   summary=json.loads((out/'g9-mock-complete-completion-summary.json').read_text());snap=out/'g9-mock-complete-completion-last-inputs.json';proof=json.loads(snap.read_text())if snap.exists()else None;polls=(out/'g9-mock-complete-completion-polls.jsonl').read_text();examples['lastEffectiveMock']={'summary':summary,'inputClassification':proof.get('classification')if proof else None,'pollRecords':len(polls.splitlines())}
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
  with tempfile.TemporaryDirectory(prefix='builder-g9-diag-bound-',dir=E)as tmp,patch.object(c,'E',Path(tmp)):
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
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100,ui=ui);ctl.host_process=Proc()
  with tempfile.TemporaryDirectory(prefix='builder-g9-host-close-',dir=E)as tmp:
   ctl.host_out=Path(tmp);(ctl.host_out/'app-closure.json').write_text(json.dumps({'payloadEvidenceFailure':None,'reason':'EXPLICIT_STOP','closeIndexFailure':{'status':'CLOSED_REVIEW_INDEX_PENDING'}}))
   with self.assertRaisesRegex(AssertionError,'HOST_CLOSURE_UNKNOWN'):ctl.stop_host({'sourceAndViewerStoppedAndInspected':True})
  self.assertFalse(ctl.host_restart_allowed)
 def test_readonly_replayers_and_deadline_namespace_only_and_decision_algorithms_unchanged(self):
  import ast
  replacements=[('beta06g8', 'beta06g9'), ('generation08', 'generation09'), ('GENERATION08', 'GENERATION09'), ('host-app08', 'host-app09'), ('g8', 'g9'), ('G8', 'G9'), ("'16'", "'18'"), ("'17'", "'19'"), ('"16"', '"18"'), ('"17"', '"19"'), ('BOOT16', 'BOOT18'), ('BOOT17', 'BOOT19'), ('BEFORE17', 'BEFORE19'), ('Boot16', 'Boot18'), ('Boot17', 'Boot19'), ('EMULATOR16', 'EMULATOR18'), ('(?:16|17)', '(?:18|19)'), ('android-closure16', 'android-closure18'), ('android-closure17', 'android-closure19'), ('android-attempt17', 'android-attempt19'), ('root-controller16-live', 'root-controller18-live'), ('LIVE16', 'LIVE18'), ('_live16', '_live18')]
  for name in ['qa-root-controller.py', 'qa-runtime.py', 'qa-deadline-guard.py', 'qa-device-actions.py', 'qa-ui.py', 'qa-android.py', 'qa-airborne.py', 'qa-ground-soak.py', 'qa-restart-proof.py', 'qa-ap-admission.py', 'qa-native-replay.py', 'qa-media-replay.py', 'qa-native-budget.py', 'qa-proof-writer.py', 'qa-raw-flight.mjs', 'qa-cut-replay.mjs', 'qa-reboot-replay.mjs', 'qa-overlap-replay.mjs', 'qa-root-live16.py']:
   old=(R/"planning/beta06g8"/name).read_text();expected=old
   for before,after in replacements:expected=expected.replace(before,after)
   target=P/("qa-root-live18.py"if name=="qa-root-live16.py"else name);actual=target.read_text();self.assertEqual(actual,expected,name)
   if target.suffix==".py":
    before_numbers=[x.value for x in ast.walk(ast.parse(old))if isinstance(x,ast.Constant)and type(x.value)in(int,float)];after_numbers=[x.value for x in ast.walk(ast.parse(actual))if isinstance(x,ast.Constant)and type(x.value)in(int,float)];self.assertEqual(after_numbers,before_numbers,name+":all_numeric_constants")
  runtime=(P/"qa-runtime.py").read_text();self.assertIn("forecast=free-rate*15",runtime);self.assertIn("\'forecastSeconds\':15",runtime)
 def test_actual20file_workspacecopy_firstwriter_guard_and_drift_refusal(self):
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100);proof=ctl.workspace_before_first_writer();self.assertEqual(proof['files'],20);self.assertEqual(proof['bytes'],870221)
  with patch.object(c.hashlib,'sha256',return_value=types.SimpleNamespace(hexdigest=lambda:'BAD')):
   with self.assertRaisesRegex(AssertionError,'WORKSPACE_DRIFT'):ctl.workspace_before_first_writer()
 def test_plan18_19_original2700_AP540_and_old_G4_request_in_history(self):
  plan=c.plan();self.assertEqual(plan['attempts'],['18','19']);self.assertEqual(plan['hostBudgetSecondsAcrossBothBoots'],2700);self.assertEqual(plan['apBudgetSeconds'],540);pins=json.loads((R/'evidence/beta06/generation04/flight-pins.json').read_text());pins['priorGeneration04SITLRequests']=[{'run':fixture.run,'requestSha256':sha((R/'evidence/beta06/generation04/flight/runs'/fixture.run/'request.json').read_bytes())}];pins['priorGeneration06SITLRequests']=[{'run':p.parent.name,'requestSha256':sha(p.read_bytes())}for p in sorted((R/'evidence/beta06/generation06/flight/runs').glob('*/request.json'))if json.loads(p.read_bytes()).get('mode')=='sitl'];self.assertEqual(len(a.historical_runs(pins)),17);pins['priorGeneration04SITLRequests'][0]['requestSha256']='0'*64
  with self.assertRaisesRegex(AssertionError,'G4_REQUEST_SHA'):a.historical_runs(pins)
 def persistence_fixture(self):
  state={'ok':True,'closeIndexFailure':None,'flight':{'run':None,'authority':None,'busy':False},'payloadLeaseObservation':{'leaseCount':0}};view={'ok':True,'ageMs':1200,'observation':{'foreground':True,'run':None,'mediaReadiness':{'active':False}}};closed=[False]
  def observation():
   if closed[0]:raise AssertionError('NATIVE_EMITTER_GONE_AFTER_CLOSURE')
   return view
  ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:state),observation=observation);ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100,ui=ui);ctl.host_anchor=1;ctl.host_instances=2;ctl.host_process=types.SimpleNamespace(pid=654,poll=lambda:None);ctl.connect_count=4;ctl.campaign_runs=['N1','F1','N2','F2'];ctl.runtime=types.SimpleNamespace(poll=lambda:0 if closed[0]else None);calls=[];ctl.launch=lambda command:calls.append(command)or{'mockLaunch':True};return ctl,state,view,closed,calls
 def test_persistence_prestop_fresh_ground_inspection_refuses_without_stop_effect(self):
  for bad in ['host1','dead','stale','authority','lease','viewer','index','inspection','alreadyclosed']:
   ctl,state,view,closed,calls=self.persistence_fixture();command={'op':'stop-emulator','rootApproved':True,'commandId':'g9-stop12','sourceAndViewerStoppedAndInspected':True}
   if bad=='host1':ctl.host_instances=1
   elif bad=='dead':ctl.host_process=types.SimpleNamespace(pid=654,poll=lambda:0)
   elif bad=='stale':view['ageMs']=1201
   elif bad=='authority':state['flight']['authority']={'run':'OLD'}
   elif bad=='lease':state['payloadLeaseObservation']['leaseCount']=1
   elif bad=='viewer':view['observation']['mediaReadiness']['active']=True
   elif bad=='index':state['closeIndexFailure']={'status':'UNKNOWN'}
   elif bad=='inspection':command['sourceAndViewerStoppedAndInspected']=False
   elif bad=='alreadyclosed':closed[0]=True
   with tempfile.TemporaryDirectory(prefix='builder-g9-persistence-',dir=E)as tmp,patch.object(c,'E',Path(tmp)):
    # Cleanup remains allowed without persistence preparation; its missing proof can never launch13.
    if bad in ['host1','inspection']:
     ctl.command(command);closed[0]=True
     with self.assertRaises(AssertionError):ctl.persistence_boot({})
    else:
     with self.assertRaises(AssertionError):ctl.command(command)
     self.assertFalse((Path(tmp)/'android-stop-request18.json').exists())
    self.assertIsNone(ctl.persistence_stop_proof);self.assertEqual(calls,[])
 def test_persistence19_consumes_same_controller_proof_no_native_read_after_shutdown(self):
  for bad in [None,'missing','consumed','pid','window','unclean','rights','lease','deadline']:
   ctl,state,view,closed,calls=self.persistence_fixture()
   with tempfile.TemporaryDirectory(prefix='builder-g9-persistence-',dir=E)as tmp,patch.object(c,'E',Path(tmp)):
    ctl.command({'op':'stop-emulator','rootApproved':True,'commandId':'g9-stop12','sourceAndViewerStoppedAndInspected':True});self.assertTrue((Path(tmp)/'android-stop-request18.json').exists());proof=ctl.persistence_stop_proof;closed[0]=True;closure={'exit':0,'error':None,'explicitStop':True}
    if bad=='missing':ctl.persistence_stop_proof=None
    elif bad=='consumed':proof['consumed']=True
    elif bad=='pid':ctl.host_process.pid=655
    elif bad=='window':ctl.host_anchor=2
    elif bad=='unclean':closure['error']='FAIL'
    elif bad=='rights':state['flight']['authority']={'run':'OLD'}
    elif bad=='lease':state['payloadLeaseObservation']['leaseCount']=1
    elif bad=='deadline':ctl.host_anchor=100-2700+239;proof['hostAnchorPythonMonoS']=ctl.host_anchor
    (Path(tmp)/'android-closure18.json').write_text(json.dumps(closure))
    if bad:
     with self.assertRaises(AssertionError):ctl.persistence_boot({})
     self.assertEqual(calls,[]);self.assertEqual(ctl.attempt,'18')
    else:
     self.assertEqual(ctl.persistence_boot({}),{'mockLaunch':True});self.assertEqual(len(calls),1);self.assertTrue(proof['consumed']);self.assertEqual(ctl.attempt,'19');self.assertTrue(ctl.persistence_only);self.assertEqual(ctl.host_anchor,1);self.assertEqual(ctl.host_instances,2);self.assertEqual(ctl.host_process.pid,654);self.assertEqual(ctl.connect_count,4);self.assertEqual(ctl.campaign_runs,['N1','F1','N2','F2'])
     with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT19_NO_ARM'):ctl.reserve('NO_NEW_RUN')
     with self.assertRaisesRegex(AssertionError,'TWO_HOST'):ctl.start_host({})
     with self.assertRaises(AssertionError):ctl.persistence_boot({})
 def test_shared_budget_refusal_precedes_host_Popen_and_connect_readiness(self):
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100,ui=types.SimpleNamespace())
  with patch.object(c.b,'admit',side_effect=RuntimeError('MOCK_FULL_REMAINING_BUDGET_SHORT')),patch.object(c.subprocess,'Popen')as popen:
   with self.assertRaisesRegex(RuntimeError,'BUDGET_SHORT'):ctl.command({'op':'start-host','rootApproved':True,'commandId':'quota-host-refusal','sourceAndViewerStoppedAndInspected':True})
   popen.assert_not_called()
   with self.assertRaisesRegex(RuntimeError,'BUDGET_SHORT'):ctl.command({'op':'action','rootApproved':True,'commandId':'quota-connect-refusal','target':'field-connect'})
   self.assertEqual(ctl.connect_count,0);self.assertEqual(ctl.dispatched,set());self.assertTrue(ctl.campaign_failed)
 def test_visible_writer_preclaims_all_receipts_before_first_fresh_observation(self):
  ui=mod('g9_writer_ui_order',P/'qa-ui.py');events=[]
  with patch.object(ui.b,'preclaim',side_effect=lambda *a,**k:events.append('reserve')),patch.object(ui.b,'alias',side_effect=lambda *a:None),patch.object(ui,'observation',side_effect=lambda:events.append('fresh')or(_ for _ in()).throw(RuntimeError('STOP_BEFORE_UI'))):
   with tempfile.TemporaryDirectory(prefix='builder-g9-ui-order-',dir=E)as tmp:
    ref=Path(tmp)/'ref.json';ref.write_text(json.dumps({'image':'missing','observed':{}}))
    with self.assertRaises(Exception):ui.dispatch('18',str(ref),'field-close','g9-mock')
  self.assertEqual(events[:3],['reserve']*3)
 def test_writer_serialized_bound_replay_ancestor_scope_and_console_failure(self):
  b=c.b
  with tempfile.TemporaryDirectory(prefix='builder-g9-writers-',dir=E)as tmp:
   out=Path(tmp);file=out/'one.json';b.write_json(file,{'test':True});self.assertTrue(file.exists())
   with self.assertRaises(AssertionError):b.write_json(file,{})
   oversized=out/'huge.json'
   with self.assertRaisesRegex(AssertionError,'SERIALIZED'):b.write_json(oversized,{'x':'a'*100},maximum=8)
   self.assertFalse(oversized.exists());link=out/'link';link.symlink_to(out,target_is_directory=True)
   with self.assertRaisesRegex(AssertionError,'ANCESTOR'):b.preclaim(link/'bad.json',128)
   with self.assertRaisesRegex(AssertionError,'ACTIVE_SCOPE'):b.preclaim(R/'outside-g9.json',128)
   proc=types.SimpleNamespace(stdout=io.BytesIO(b'over-bound-data'),terminated=False)
   def terminate():proc.terminated=True
   proc.terminate=terminate;sink=b.BoundedFile(out/'console.bin',8,binary=True);capture=b.PipeCapture(proc,sink);capture.thread.join(timeout=1)
   with self.assertRaisesRegex(RuntimeError,'CAPTURE_FAILED'):capture.check()
   self.assertTrue(proc.terminated);self.assertLessEqual((out/'console.bin').stat().st_size,8)
 def test_runtime_no_global200_and_emulator_budget_watch_stale_fail_loud(self):
  text=(P/'qa-runtime.py').read_text();self.assertNotIn('EARLY_EVIDENCE200',text);self.assertNotIn("(R/'evidence/beta06').rglob",text)
  now=[1]
  with patch.object(c.b,'admit',return_value={'policySha256':'f'*64}):
   watch=c.b.QuotaWatch(clock=lambda:now[0]);self.assertEqual(watch.check()['auditAgeS'],0);now[0]=17
   with self.assertRaisesRegex(AssertionError,'STALE'):watch.check()
   watch.close()
 def test_closure_paths_and_mutually_exclusive_ticket_aliases(self):
  b=c.b
  with tempfile.TemporaryDirectory(prefix='builder-g9-closure-tickets-',dir=E)as tmp:
   out=Path(tmp)
   with self.assertRaisesRegex(AssertionError,'CLOSURE_PATH'):b.preclaim(out/'arbitrary.json',128,closure=True)
   first=out/'intent-receipt.json';other=out/'intent-uncertain.json';b.preclaim(first,128);b.alias(first,other);b.write_json(other,{},maximum=128)
   with self.assertRaisesRegex(AssertionError,'TICKET_REPLAY'):b.write_json(first,{},maximum=128)
   self.assertFalse(first.exists())
 def test_full_normal_controller_journal_does_not_prevent_owned_cleanup(self):
  class FullJournal:
   def write(self,*unused):raise OSError('MOCK_NORMAL_JOURNAL_FULL')
  proc=types.SimpleNamespace(pid=123,stopped=False)
  proc.poll=lambda:0 if proc.stopped else None
  def terminate():proc.stopped=True
  proc.terminate=terminate;proc.wait=lambda timeout:0
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100,journal=FullJournal());ctl.host_process=proc
  with tempfile.TemporaryDirectory(prefix='builder-g9-close-journal-',dir=E)as tmp,patch.object(c,'E',Path(tmp)):
   ctl.close();self.assertTrue(proc.stopped);rows=(Path(tmp)/'root-controller-closure18.jsonl').read_text().splitlines();self.assertEqual(json.loads(rows[0])['originalJournalFailure'],'MOCK_NORMAL_JOURNAL_FULL');self.assertEqual(json.loads(rows[0])['event'],'STOP_OWNED_HOST_ON_PARENT_CLOSE')
 def test_python_proof_writer_preserves_complete_serialization_and_delegates_slot_guard(self):
  writer=mod('g9_python_proof_writer',P/'qa-proof-writer.py');report={'status':'PASS_MOCK','unicode':'đúng','payload':{'allFields':[1,2,3]}};calls=[]
  def run(argv,**kwargs):calls.append((argv,kwargs));return types.SimpleNamespace(returncode=0,stdout=b'{"status":"PROOF_WRITTEN"}',stderr=b'')
  with patch.object(writer.subprocess,'run',side_effect=run):
   proof=writer.write_proof(E/'qa-n1-media01.json',report,kind='media',scenario='n1');self.assertEqual(proof['status'],'PROOF_WRITTEN');self.assertEqual(json.loads(calls[0][1]['input']),report);self.assertEqual(calls[0][0][0],'node');self.assertEqual(json.loads(calls[0][0][-1])['scenario'],'n1')
   with self.assertRaisesRegex(AssertionError,'SERIALIZATION_BOUND'):writer.write_proof(E/'qa-n1-media01.json',{'x':'a'*(2*2**20)},kind='media',scenario='n1')
   with self.assertRaisesRegex(AssertionError,'ACTIVE_SCOPE'):writer.write_proof(R/'outside.json',{},kind='campaign')
   self.assertEqual(len(calls),1)
  with patch.object(writer.subprocess,'run',return_value=types.SimpleNamespace(returncode=1,stdout=b'',stderr=b'UNIQUE_SLOT_OR_FUTURE_HEADROOM')):
   with self.assertRaisesRegex(RuntimeError,'AUTHORITATIVE_PROOF_WRITE_REFUSED'):writer.write_proof(E/'qa-n1-media01.json',report,kind='media',scenario='n1')
 def test_native_ledger_future_refusal_precedes_UI_reads_and_does_not_anchor_connect(self):
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100,ui=types.SimpleNamespace());calls=[]
  with patch.object(c.b.quota(),'check_native_future',side_effect=RuntimeError('PNG_OR_NATIVE_FUTURE_SHORT')),patch.object(c.b.quota(),'check_png_future',side_effect=RuntimeError('PNG_OR_NATIVE_FUTURE_SHORT')),patch.object(c.b,'admit',side_effect=lambda *a,**kw:calls.append('heavy')):
   with self.assertRaisesRegex(RuntimeError,'FUTURE_SHORT'):ctl.command({'op':'action','rootApproved':True,'commandId':'g9-future-short','target':'field-connect'})
  self.assertEqual(calls,[]);self.assertEqual(ctl.connect_count,0);self.assertEqual(ctl.dispatched,set());self.assertTrue(ctl.campaign_failed)
 def test_actual_shared_native_future_exact_and_one_claim_short_for_all_subtypes(self):
  q=mod('g9_actual_shared_future_quota',R/'pilot/beta06g9/quota.py')
  for kind,exact in [('native',48),('dispatch',32),('prepare',24),('direct',0)]:
   with tempfile.TemporaryDirectory(prefix='builder-g9-future-ledger-',dir=E)as tmp,patch.object(q,'E',Path(tmp)):
    for n in range(exact):q.reserve_write(category='native'if kind=='native'else'screenshots',entries=1,bytes=0,claim_id=('metadata:'if kind=='native'else'png-'+kind+':')+str(n))
    positive=q.check_native_future(remaining_ap=4,remaining_hosts=2);self.assertEqual(positive['normalFiles']['future'],464);self.assertEqual(positive['dispatch']['future'],128);self.assertEqual(positive['prepare']['future'],24);self.assertEqual(positive['direct']['future'],32)
    q.reserve_write(category='native'if kind=='native'else'screenshots',entries=1,bytes=0,claim_id=('metadata:'if kind=='native'else'png-'+kind+':')+'one-short')
    with self.assertRaisesRegex(AssertionError,'FUTURE'):q.check_native_future(remaining_ap=4,remaining_hosts=2)
 def test_emulator_admission_uses_guard_phase_without_new_host_capacity(self):
  runtime=mod('g9_emulator_guard_phase',P/'qa-runtime.py');now=[0];calls=[]
  def clock():now[0]+=1;return now[0]
  class Sock:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def bind(self,*args):pass
  def stop(phase,**kw):calls.append(phase);raise RuntimeError('STOP_BEFORE_EMULATOR_POPEN')
  with tempfile.TemporaryDirectory(prefix='builder-g9-emulator-guard-',dir=E)as tmp,patch.object(runtime,'E',Path(tmp)),patch.object(runtime,'plan',return_value={'command':['NEVER_EXECUTE']}),patch.object(runtime.time,'monotonic',side_effect=clock),patch.object(runtime.time,'sleep',return_value=None),patch.object(runtime.shutil,'disk_usage',return_value=types.SimpleNamespace(free=33*2**30)),patch.object(runtime.socket,'socket',return_value=Sock()),patch.object(runtime.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout='Hypervisor.Framework',stderr='')),patch.object(runtime.subprocess,'Popen')as popen,patch.object(runtime.b,'admit',side_effect=stop):
   with self.assertRaisesRegex(RuntimeError,'STOP_BEFORE_EMULATOR'):runtime.run('19')
   self.assertEqual(calls,['guard']);popen.assert_not_called()
 def test_initial_host_quota_refusal_latches_and_cannot_restart_same_campaign(self):
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100,ui=types.SimpleNamespace());command={'op':'start-host','rootApproved':True,'commandId':'g9-first-host-short','sourceAndViewerStoppedAndInspected':True}
  with patch.object(c.b,'admit',side_effect=RuntimeError('INITIAL_FUTURE_HEADROOM_SHORT')),patch.object(c.subprocess,'Popen')as popen:
   with self.assertRaisesRegex(RuntimeError,'HEADROOM_SHORT'):ctl.command(command)
   self.assertTrue(ctl.campaign_failed);self.assertEqual(ctl.host_instances,0);self.assertEqual(ctl.connect_count,0)
   with self.assertRaisesRegex(AssertionError,'FAILED_CAMPAIGN'):ctl.command({**command,'commandId':'g9-new-id-does-not-reset'})
   popen.assert_not_called()
 def test_original_python_memory_capacity_arguments_match_host_directory_progression(self):
  ctl=c.Controller('18',boot_reader=lambda:'BOOT',clock=lambda:100);seen=[]
  def admit(phase,**kw):seen.append((phase,kw));return {'status':'ADMITTED','remaining_ap':kw['remaining_ap'],'remaining_hosts':kw['remaining_hosts']}
  cases=[('before-host',0,0,4,2),('before-connect',0,1,4,1),('before-connect',1,1,3,1),('before-host',2,1,2,1),('before-connect',2,2,2,0),('before-connect',3,2,1,0)]
  with patch.object(c.b,'admit',side_effect=admit):
   for phase,connected,hosts,A,H in cases:
    ctl.connect_count=connected;ctl.host_instances=hosts;ctl.campaign_runs=['persisted-context']*connected
    ctl.quota_admission(phase,'g9-memory-'+str(len(seen)));actual=seen[-1][1];self.assertEqual((actual['remaining_ap'],actual['remaining_hosts']),(A,H));self.assertEqual(actual['closed_runs'],ctl.campaign_runs)
  self.assertFalse(ctl.campaign_failed);examples['capacityBridge']={'cases':[list(row)for row in cases],'scope':'Original Controller memory arguments; Flight real-filesystem Python→Node admission separately verifies actual host-app09/-restart routing and occupancy.'}
 def sealed(self):
  run=fixture.run;rb=fixture.paths['review'].read_bytes();cb=fixture.paths['closure'].read_bytes();review=json.loads(rb);closure=json.loads(cb);ref={key:copy.deepcopy(review.get(key))for key in ['run','accepted','aborted','closedAt','modelSha256','planSha256','documentSha256','missionSha256','rawHead','rawRecords','execution','failure','writerError']};ref.update(format='aeris-sealed-flight-review-reference',version=1,authorityRestorable=False,review={'path':'flight/runs/'+run+'/review.json','bytes':len(rb),'sha256':sha(rb)},closure={'path':'flight/runs/'+run+'/closure.json','bytes':len(cb),'sha256':sha(cb),'containerId':closure['containerId'],'stopped':True});body={'data':{'reviewRef':ref,'authorityRestored':False},'kind':'FLIGHT_REVIEW_SEALED_REF','previousHash':'0'*64,'schemaVersion':1,'seq':1};h=sha(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode());row={**body,'hash':h};wal=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n';side={'status':'CLOSED_REVIEW_INDEXED','reviewIndexStatus':'INDEXED','effectStatus':'SEALED_OWNED_CLOSED','reviewRef':ref,'receipt':{'seq':1,'hash':h},'error':None};data={str(r.E/'flight/runs'/run/'review.json'):rb,str(r.E/'flight/runs'/run/'closure.json'):cb,str(r.E/'host-app09'/('close-index-'+run+'.json')):json.dumps(side).encode()};return run,wal,side,data
 def test_compact_restart_index_actual842keyreview_accepted_without_fullmap_canonicalization(self):
  run,wal,side,data=self.sealed()
  with patch.object(r,'blob',side_effect=lambda p,bound=0:data[str(p)]):proof=r.sealed_index_proofs(wal,[run])
  self.assertEqual(len(proof),1);self.assertEqual(proof[0]['reviewSha256'],sha(fixture.paths['review'].read_bytes()));self.assertGreater(len(json.loads(fixture.paths['review'].read_text())['filesSha256']),64)
 def test_pending_unknown_sidecar_or_tampered_bytes_refuse_restart(self):
  for mutation in ['pending','receipt','review']:
   run,wal,side,data=self.sealed();path=str(r.E/'host-app09'/('close-index-'+run+'.json'))
   if mutation=='pending':side['status']='CLOSED_REVIEW_INDEX_PENDING';data[path]=json.dumps(side).encode()
   elif mutation=='receipt':side['receipt']['hash']='0'*64;data[path]=json.dumps(side).encode()
   else:data[str(r.E/'flight/runs'/run/'review.json')]+=b' '
   with patch.object(r,'blob',side_effect=lambda p,bound=0:data[str(p)]):
    with self.assertRaises(AssertionError):r.sealed_index_proofs(wal,[run])
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Tests(name)for name in ['test_readonly_replayers_and_deadline_namespace_only_and_decision_algorithms_unchanged', 'test_actual20file_workspacecopy_firstwriter_guard_and_drift_refusal', 'test_plan18_19_original2700_AP540_and_old_G4_request_in_history', 'test_effective_controller_imports_R2_policy_and_calls_unchanged_visible_dispatch_once', 'test_new_terminal_ACK_guard_refuses_pending_index_and_latches_without_second_effect', 'test_persistence19_consumes_same_controller_proof_no_native_read_after_shutdown', 'test_shared_budget_refusal_precedes_host_Popen_and_connect_readiness', 'test_actual_shared_native_future_exact_and_one_claim_short_for_all_subtypes', 'test_python_proof_writer_preserves_complete_serialization_and_delegates_slot_guard', 'test_emulator_admission_uses_guard_phase_without_new_host_capacity', 'test_initial_host_quota_refusal_latches_and_cannot_restart_same_campaign','test_original_python_memory_capacity_arguments_match_host_directory_progression']));report={'classification':'G9_EFFECTIVE_CONTROLLER_R2_DISPATCH_SOURCE_MOCK_ONLY','status':'PASS_G9_NATIVE_INTEGRATION_MOCK'if result.wasSuccessful()else'FAIL','tests':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors],'sources':{str(p.relative_to(R)):sha(p.read_bytes())for p in P.glob('*')if p.is_file()},'examples':examples,'scope':'Actual new controller complete-nominal method imports immutable R2, real readiness/phase policy + fake UI visible-dispatch seam and state; retained old actual842keyreview for compactindex mock; no actualHTTP/listener/ADB/browser/AP/controllercampaign. All G9 actual scenarios NOT_RUN by Builder; Root-only actual campaign requires independent gate. New writer/admission mocks do not execute authoritative runtime.'};out=E/(sys.argv[1]if len(sys.argv)>1 else'builder-native-integration01.json');out.open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if result.wasSuccessful()else 1)
