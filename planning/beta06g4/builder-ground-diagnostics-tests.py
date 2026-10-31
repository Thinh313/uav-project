"""New G4 response/failure/recovery contracts with bounded mocked HTTP only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation04'
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
u=mod('g4_diag_ui','qa-ui.py');g=mod('g4_diag_ground','qa-ground-soak.py');c=mod('g4_diag_controller','qa-root-controller.py');d=mod('g4_diag_device','qa-device-actions.py');examples=[]
class HTTP:
 status=200
 def __init__(self,raw):self.raw=raw;self.reads=[]
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,n):self.reads.append(n);return self.raw[:n]
class Tests(unittest.TestCase):
 def ctl(self):return c.Controller('06',boot_reader=lambda:'BOOT',clock=lambda:100,ui=types.SimpleNamespace())
 def cmd(self,op,name,**kw):return {'op':op,'commandId':name,'rootApproved':True,**kw}
 def test_actual_stale_HTTP_prefix_retained_redacted_without_extra_request(self):
  raw=json.dumps({'ok':True,'ageMs':1201,'observation':{'seq':1,'token':'sensitive','nested':{'csrf':'secret'},'clientEpoch':1}}).encode();http=HTTP(raw)
  with patch.object(u.urllib.request,'urlopen',return_value=http)as request:
   with self.assertRaisesRegex(AssertionError,'STALE_OBSERVATION')as caught:u.observation()
   diag=caught.exception.raw_observation_diagnostic;self.assertEqual(diag['rawResponseAgeMs'],1201);self.assertEqual(diag['responsePrefixSha256'],hashlib.sha256(raw).hexdigest());self.assertNotIn('sensitive',diag['bodyRedacted']);self.assertNotIn('secret',diag['bodyRedacted']);self.assertEqual(http.reads,[65537]);self.assertEqual(request.call_count,1);examples.append(diag)
 def test_freshness1200_exact_boundary_unchanged(self):
  for age,allowed in [(1200,True),(1200.01,False),(float('nan'),False),(True,False),(-1,False)]:
   http=HTTP(json.dumps({'ok':True,'ageMs':age,'observation':{'seq':1}}).encode())
   with patch.object(u.urllib.request,'urlopen',return_value=http):
    if allowed:self.assertEqual(u.observation()['ageMs'],1200)
    else:
     with self.assertRaisesRegex(AssertionError,'STALE_OBSERVATION'):u.observation()
 def test_malformed_or_truncated_quoted_secret_keeps_only_SHA_count(self):
  for raw in [b'{"token":"sensitive",',b'{"nested":{"authorization":"Bearer sensitive"',b'cookie=sensitive&password=sensitive']:
   diag=u.redacted_http_diagnostic(raw,error='AssertionError:SECRET-IN-ERROR');self.assertNotIn('sensitive',json.dumps(diag));self.assertNotIn('SECRET-IN-ERROR',json.dumps(diag));self.assertEqual(diag['responsePrefixBytes'],len(raw));self.assertEqual(diag['bodyKind'],'UNPARSEABLE_RESPONSE_PREFIX_SHA_AND_COUNT_ONLY')
 def test_64KiB_overflow_fails_with_bounded_evidence(self):
  http=HTTP(b'{"token":"sensitive",'+b'x'*70000)
  with patch.object(u.urllib.request,'urlopen',return_value=http):
   with self.assertRaisesRegex(AssertionError,'BOUND64KIB')as caught:u.observation()
   diag=caught.exception.raw_observation_diagnostic;self.assertEqual(diag['responsePrefixBytes'],65536);self.assertTrue(diag['responseOverflow']);self.assertNotIn('sensitive',json.dumps(diag));self.assertEqual(http.reads,[65537])
 def test_nonfinite_bool_string_age_diagnostics_are_strict_JSON(self):
  for age in [float('nan'),float('inf'),True,'1201',None]:
   raw=json.dumps({'ageMs':age,'observation':{}}).encode();diag=u.redacted_http_diagnostic(raw,elapsed_ms=float('nan'));self.assertIsNone(diag['rawResponseAgeMs']);self.assertIsNone(diag['requestElapsedPythonMs']);json.dumps(diag,allow_nan=False)
 def test_HTTP_error_response_retains_bounded_redacted_actual_body(self):
  from io import BytesIO
  raw=b'{"ageMs":1444,"token":"sensitive","error":"REJECTED"}';err=u.urllib.error.HTTPError('http://127.0.0.1:8872/api/ui-observation',409,'Conflict',{},BytesIO(raw))
  with patch.object(u.urllib.request,'urlopen',side_effect=err)as request:
   with self.assertRaises(u.urllib.error.HTTPError)as caught:u.observation()
   diag=caught.exception.raw_observation_diagnostic;self.assertEqual(diag['httpStatus'],409);self.assertEqual(diag['rawResponseAgeMs'],1444);self.assertNotIn('sensitive',diag['bodyRedacted']);self.assertEqual(request.call_count,1)
 def test_actual_collect_preserves_failure_diagnostic_and_refuses_interval(self):
  diag=u.redacted_http_diagnostic(b'{"ok":true,"ageMs":1444,"observation":{"seq":7}}',status=200)
  def fail():
   e=AssertionError('STALE_OBSERVATION');e.raw_observation_diagnostic=diag;raise e
  with tempfile.TemporaryDirectory(prefix='builder-ground-diagnostic-',dir=E)as tmp:
   with patch.object(g,'E',Path(tmp)),patch.object(g,'journal_rows',return_value=(b'first\n',[{'seq':1}])):
    with self.assertRaisesRegex(AssertionError,'STALE'):g.collect('refused',Path(tmp)/'clock.jsonl',clock=lambda:10,ui=types.SimpleNamespace(observation=fail))
    report=json.loads((Path(tmp)/'refused-ground-soak.json').read_text());self.assertEqual(report['failureObservation'],diag);self.assertEqual(report['status'],'REFUSED_GROUND_ADMISSION_NO_AP');self.assertEqual(report['samples'],[]);examples.append(report['failureObservation'])
 def test_sample_failure_preserves_last_returned_raw_view_redacted(self):
  view={'ok':True,'ageMs':1500,'observation':{'seq':1,'csrf':'sensitive'}}
  with tempfile.TemporaryDirectory(prefix='builder-ground-sample-',dir=E)as tmp:
   ui=types.SimpleNamespace(observation=lambda:view,q=types.SimpleNamespace(state=lambda:{}))
   with patch.object(g,'E',Path(tmp)),patch.object(g,'journal_rows',return_value=(b'first\n',[{'seq':1}])):
    with self.assertRaisesRegex(AssertionError,'FRESH_OBSERVATION'):g.collect('refused',Path(tmp)/'clock.jsonl',clock=lambda:10,ui=ui)
    report=json.loads((Path(tmp)/'refused-ground-soak.json').read_text());diag=report['failureObservation'];self.assertEqual(diag['rawResponseAgeMs'],1500);self.assertNotIn('sensitive',diag['bodyRedacted']);self.assertEqual(diag['classification'],'EXACT_LAST_RETURNED_VIEW_REDACTED_NO_EXTRA_HTTP_REQUEST')
 def test_one_explicit_recovery_success_no_automatic_retry_or_anchor_reset(self):
  x=self.ctl();x.host_anchor=50;calls=[]
  def collect(name,*args,**kw):
   calls.append(name)
   if len(calls)==1:raise AssertionError('STALE_OBSERVATION')
   return {'status':'PASS_GROUND_INTERVAL_NOT_AP_AUTHORITY'}
  with patch.object(c,'module',return_value=types.SimpleNamespace(collect=collect)):
   with self.assertRaisesRegex(AssertionError,'STALE'):x.command(self.cmd('ground-soak','first',clockJournal='MOCK'))
   with self.assertRaisesRegex(AssertionError,'NO_AUTOMATIC_INTERVAL_RETRY'):x.command(self.cmd('ground-soak','unauthorized',clockJournal='MOCK'))
   self.assertEqual(len(calls),1)
   x.command(self.cmd('authorize-ground-recovery','explicit',rootInspectedRawGroundFailure=True,diagnosis='Read actual age failure and clock data',explicitRecovery='Root visibly recovered same current source and viewer'))
   result=x.command(self.cmd('ground-soak','second',clockJournal='MOCK'));self.assertEqual(result['status'],'PASS_GROUND_INTERVAL_NOT_AP_AUTHORITY');self.assertTrue(x.ground_recovery_used);self.assertEqual(x.host_anchor,50);self.assertEqual(x.connect_count,0)
   with self.assertRaisesRegex(AssertionError,'ONE_GROUND_RECOVERY'):x.command(self.cmd('authorize-ground-recovery','third',rootInspectedRawGroundFailure=True,diagnosis='again',explicitRecovery='again'))
 def test_second_recovery_failure_or_failure_after_AP_ends_campaign(self):
  for priorAP in [0,1]:
   x=self.ctl();x.connect_count=priorAP
   if priorAP==0:x.ground_failure={'commandId':'first'};x.ground_recovery_authorized=True
   with patch.object(c,'module',return_value=types.SimpleNamespace(collect=lambda *a,**k:(_ for _ in()).throw(AssertionError('STALE')))):
    with self.assertRaisesRegex(AssertionError,'STALE'):x.command(self.cmd('ground-soak','failed',clockJournal='MOCK'))
   self.assertTrue(x.campaign_failed)
   with self.assertRaisesRegex(AssertionError,'FAILED_CAMPAIGN'):x.command(self.cmd('ground-soak','later',clockJournal='MOCK'))
 def test_recovery_requires_actual_failure_inspection_and_concrete_diagnosis(self):
  for kw in [{},{'rootInspectedRawGroundFailure':True,'diagnosis':'','explicitRecovery':'Recovery'}]:
   x=self.ctl();x.ground_failure={'commandId':'first'}
   with self.assertRaises(AssertionError):x.command(self.cmd('authorize-ground-recovery','bad',**kw))
 def test_current_native_store_exact_vs_closed_G3_baseline_and_tamper_refusal(self):
  old=json.loads((R/d.G3_BASELINE).read_text());journal=(R/old['journalFile']).read_bytes();proof=d.retained_g3_store_decision(old['files'],journal);self.assertTrue(proof['nativeStoreExactAtRead']);self.assertEqual(proof['remainingPickerOperationsAtG3Closure'],3)
  for files,raw in [({},journal),(old['files'],b'changed\n')]:
   with self.assertRaises(AssertionError):d.retained_g3_store_decision(files,raw)
 def test_advertised45min_labels_and_pythonB_child(self):
  plan=c.plan();self.assertEqual(plan['hostBudgetSecondsAcrossBothBoots'],2700);self.assertEqual(plan['attempts'],['06','07']);self.assertEqual(plan['newConnectIntentsBoot06'],4);self.assertEqual(plan['connectIntentsBoot07'],0);self.assertEqual(plan['apBudgetSeconds'],540);self.assertIn("[sys.executable,'-B'",(P/'qa-root-controller.py').read_text());self.assertIn("+2700",(P/'qa-runtime.py').read_text());self.assertEqual(c.g.EMULATOR_BUDGET_S,2700)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'classification':'BUILDER_MOCK_NO_RUNTIME','status':'PASS_G4_BOUNDED_GROUND_FAILURE_RECOVERY_NATIVE_BASELINE'if r.wasSuccessful()else'FAIL','tests':r.testsRun,'failures':[(str(t),e)for t,e in r.failures+r.errors],'diagnosticExamples':examples,'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'qa-ui.py',P/'qa-ground-soak.py',P/'qa-root-controller.py',P/'qa-device-actions.py']},'scope':'Bounded fakeHTTP and actual pure functions/fakecontroller. Real closedG3 native baseline read-only; no actual G4 Android/AP/UI/source/listener. Exact1200ms threshold unchanged.'};out=E/(sys.argv[1]if len(sys.argv)>1 else'builder-ground-diagnostics01.json');out.open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if r.wasSuccessful()else 1)
