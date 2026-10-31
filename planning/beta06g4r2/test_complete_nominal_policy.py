"""Actual retained-input regression plus explicit derived/mock completion negatives."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,sys,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation04';run='sfae933b8b0fe4d6192c5'
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
m=mod('offline_r2_completion',P/'complete_nominal_policy.py');ui=mod('frozen_r1_phase_policy',R/'planning/beta06g4r1/qa-ui.py')
paths={'reference':E/'g4r1-n1-ground-close-reference.json','intent':E/'g4r1-n1-explicit-ground-close-intent.json','after':E/'g4r1-n1-close-rejection-snapshot01.json','raw':E/'flight/runs'/run/'raw.jsonl','review':E/'flight/runs'/run/'review.json','closure':E/'flight/runs'/run/'closure.json','overlap':E/'host-app04-recheck01/overlap-events.jsonl','frozenController':R/'planning/beta06g4r1/qa-root-controller.py'}
sha=lambda b:hashlib.sha256(b).hexdigest();before_hash={k:sha(p.read_bytes())for k,p in paths.items()};ref=json.loads(paths['reference'].read_text());view=json.loads(paths['intent'].read_text())['observation'];after=json.loads(paths['after'].read_text());review=json.loads(paths['review'].read_text());raw=[];head=''
for line in paths['raw'].read_bytes().splitlines():
 row=json.loads(line);match=re.search(br',"sha256":"([a-f0-9]{64})"}$',line);assert match and sha(line[:match.start()]+b'}')==row['sha256']and row['n']==len(raw)+1 and row['previous']==head;head=row['sha256'];raw.append(row)
assert head==review['rawHead']and len(raw)==review['rawRecords'];closing=next(r for r in raw if r['kind']=='FIELD01_CLOSING');observed=closing['data']['observed'];overlap=[json.loads(l)for l in paths['overlap'].read_bytes().splitlines()];beforepoints=[r for r in overlap if r['kind']=='OBSERVATION'and r['hostMonoMs']<=view['receivedAtHostMonoMs']and r['data'].get('flight',{}).get('run')==run and r['data']['flight'].get('armed')is False];point=beforepoints[-1]['data']['flight'];binding=m.reference_binding(ref)
# Explicit derived projection, not an exact original pre-close /api/state response.
state={'ok':True,'client':copy.deepcopy(after['state']['client']),'flight':{'run':run,'mode':'sitl','request':{k:binding[k]for k in ['run','boot','modelSha256','planSha256']},'error':None,'writerError':None,'positionAgeMs':point['positionAgeMs'],'live':{k:copy.deepcopy(observed[k])for k in ['armed','boot','simulation','failure','stage','mode','heartbeatAgeMs','completion']}}}
provenance={'classification':'DERIVED_PROJECTION_FROM_SEPARATE_RETAINED_ACTUAL_POINTS_NOT_EXACT_PRECLOSE_STATE','reason':'Root did not persist full pre-close q.state response. No contemporaneous whole-state replay is claimed.','sources':{k:{'path':str(p.relative_to(R)),'sha256':before_hash[k]}for k,p in paths.items()},'ui':'Actual explicit visible close intent observation, before effect.','canonicalLive':'Actual FIELD01_CLOSING.data.observed; exact raw SHA chain verified.','positionAge':'Actual nearest earlier retained overlap OBSERVATION for same run/boot/armedfalse.','client':'Actual post-close snapshot client with same retained identity; not asserted simultaneous with preclose.','after':'Actual after-effect state/UI snapshot, run null and accepted review.','rawClosingRecord':closing['n'],'overlapRecord':beforepoints[-1]['seq'],'oldBugActualDiagnostic':{'liveStage':observed['stage'],'armed':observed['armed'],'uiPhase':view['observation']['phase'],'complete':observed['completion']['complete']}}
examples={}
class Tests(unittest.TestCase):
 def test_actual_retained_proof_complete_AUTO_armedfalse_oldbranch_fails_newpredicate_passes(self):
  self.assertEqual(observed['stage'],'AUTO');self.assertFalse(observed['armed']);self.assertEqual(view['observation']['phase'],'AUTO');self.assertTrue(observed['completion']['complete']);self.assertFalse(observed['armed']is False and view['observation']['phase']=='DISARMED');decision=m.nominal_close_decision(state,view,binding);self.assertTrue(decision['eligible']);self.assertFalse(decision['stageUsedAsDisarmProof']);examples['positiveDerivedProjection']=decision
 def test_frozen_complete_nominal_actual_branch_AST_still_has_DISARMED_requirement(self):
  import ast
  tree=ast.parse(paths['frozenController'].read_text());fn=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='complete_nominal');condition=next(n.test for n in ast.walk(fn)if isinstance(n,ast.If));expr=ast.unparse(condition);self.assertIn("o.get('phase') == 'DISARMED'",expr);self.assertIn("l.get('armed') is False",expr)
 def test_existing_frozen_dispatch_phase_policy_accepts_actual_AUTO_groundcompletion(self):ui.phase_policy(ref['observed']['observation']['phase'],view['observation'],'field-close',state)
 def test_after_actual_effect_run_null_refuses_no_duplicate_close(self):
  self.assertIsNone(after['state']['flight']['run']);self.assertTrue(after['state']['flight']['lastReview']['accepted']);self.assertTrue(json.loads(paths['closure'].read_text())['stopped'])
  with self.assertRaises(AssertionError):m.nominal_close_decision(after['state'],after['ui'],binding)
 def test_each_canonical_completion_flag_false_or_missing_waits(self):
  for key in ['complete','autoObserved','expectedTerminalRTL','groundDisarmed','nearHome']:
   for change in [False,None]:
    s=copy.deepcopy(state);s['flight']['live']['completion'][key]=change;self.assertFalse(m.nominal_close_decision(s,view,binding)['eligible'],key)
 def test_missing_navigation_or_bad_takeoff_proof_cannot_close(self):
  for change in [{'missingNavigation':[1]},{'takeoffEvidence':{'valid':False}},{'takeoffEvidence':{'valid':True,'failed':None,'proof':{'notAckOnly':False,'seq':1,'command':22}}},{'completionRule':'OTHER_RULE'}]:
   s=copy.deepcopy(state);s['flight']['live']['completion'].update(change);self.assertFalse(m.nominal_close_decision(s,view,binding)['eligible'])
 def test_armedtrue_or_unknown_never_close_even_badge_DISARMED(self):
  for armed in [True,None,0]:
   s=copy.deepcopy(state);s['flight']['live']['armed']=armed;v=copy.deepcopy(view);v['observation']['phase']='DISARMED';self.assertFalse(m.nominal_close_decision(s,v,binding)['eligible'])
 def test_phase_mode_labels_alone_do_not_override_valid_ground_proof(self):
  for label in ['AUTO','RTL','DISARMED']:
   s=copy.deepcopy(state);s['flight']['live']['stage']=label;s['flight']['live']['mode']=label;v=copy.deepcopy(view);v['observation']['phase']=label;self.assertTrue(m.nominal_close_decision(s,v,binding)['eligible']);ui.phase_policy(label,v['observation'],'field-close',s)
 def test_ui_freshness_foreground_context_negatives(self):
  for change in [{'ageMs':1201},{'ageMs':-1},{'ageMs':float('nan')}]:
   v=copy.deepcopy(view);v.update(change)
   with self.assertRaises(AssertionError):m.nominal_close_decision(state,v,binding)
  for key in m.IDENTITY_KEYS:
   v=copy.deepcopy(view);v['observation'][key]='WRONG'
   with self.assertRaises(AssertionError,msg=key):m.nominal_close_decision(state,v,binding)
  v=copy.deepcopy(view);v['observation']['foreground']=False
  with self.assertRaises(AssertionError):m.nominal_close_decision(state,v,binding)
 def test_state_context_freshness_failure_writer_negatives(self):
  mutations=[lambda s:s['flight'].update(run=None),lambda s:s['flight']['request'].update(boot='WRONG'),lambda s:s['flight']['request'].update(planSha256='WRONG'),lambda s:s['flight']['live'].update(boot='WRONG'),lambda s:s['flight'].update(positionAgeMs=1001),lambda s:s['flight']['live'].update(heartbeatAgeMs=3001),lambda s:s['client'].update(ageMs=3000),lambda s:s['client'].update(active=False),lambda s:s['client'].update(instance='WRONG'),lambda s:s['flight'].update(error='WRITER_ERROR'),lambda s:s['flight'].update(writerError='FSYNC_FAILURE'),lambda s:s['flight']['live'].update(failure='INJECTED_CUT'),lambda s:s['flight'].update(mode='mock')]
  for mutate in mutations:
   s=copy.deepcopy(state);mutate(s)
   with self.assertRaises(AssertionError):m.nominal_close_decision(s,view,binding)
 def command(self):return {'run':run,'reference':'OFFLINE_RETAINED_REFERENCE_ONLY','commandId':'r2-offline-close','waitSeconds':1}
 def wait(self,**kwargs):
  return m.wait_complete_nominal(self.command(),reference=ref,state_reader=lambda:copy.deepcopy(state),observation_reader=lambda end:copy.deepcopy(view),closure_reserve=lambda:90,phase_policy=ui.phase_policy,dispatch=kwargs.pop('dispatch',lambda value:value),clock=kwargs.pop('clock',lambda:0),**kwargs)
 def test_wait_dispatches_exactly_once_after_actual_phase_policy_and_reserve(self):
  calls=[];result=self.wait(dispatch=lambda value:calls.append(value)or{'status':'MOCK_ACK_NOT_ACTUAL'});self.assertEqual(len(calls),1);self.assertEqual(calls[0]['target'],'field-close');self.assertEqual(calls[0]['timeout'],20);self.assertEqual(result['status'],'MOCK_ACK_NOT_ACTUAL')
 def test_uncertain_dispatch_error_propagates_no_second_input(self):
  calls=[]
  def dispatch(value):calls.append(value);raise AssertionError('UNCERTAIN_NO_RETRY')
  with self.assertRaisesRegex(AssertionError,'UNCERTAIN'):self.wait(dispatch=dispatch)
  self.assertEqual(len(calls),1)
 def test_late_read_or_phase_policy_rejection_no_dispatch(self):
  times=iter([0,0,2]);calls=[]
  with self.assertRaisesRegex(AssertionError,'AFTER_DEADLINE'):self.wait(clock=lambda:next(times),dispatch=lambda value:calls.append(value))
  self.assertEqual(calls,[])
  with patch.object(ui,'phase_policy',side_effect=AssertionError('EXISTING_POLICY_REJECTS')):
   with self.assertRaisesRegex(AssertionError,'EXISTING_POLICY'):self.wait(dispatch=lambda value:calls.append(value))
  self.assertEqual(calls,[])
 def test_incomplete_timeout_no_close_no_retry(self):
  s=copy.deepcopy(state);s['flight']['live']['completion']['complete']=False;clock=[0];calls=[]
  with self.assertRaisesRegex(AssertionError,'TIMEOUT'):
   m.wait_complete_nominal(self.command(),reference=ref,state_reader=lambda:s,observation_reader=lambda end:view,closure_reserve=lambda:90,phase_policy=ui.phase_policy,dispatch=lambda value:calls.append(value),clock=lambda:clock[0],pause=lambda dt:clock.__setitem__(0,clock[0]+dt))
  self.assertEqual(calls,[])
 def test_original_input_bytes_unchanged(self):self.assertEqual(before_hash,{k:sha(p.read_bytes())for k,p in paths.items()})
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'classification':'OFFLINE_SOURCE_MOCK_AND_DERIVED_RETAINED_ACTUAL_POINT_REGRESSION','status':'PASS_COMPLETION_POLICY_CORRECTION_OFFLINE_ONLY'if r.wasSuccessful()else'FAIL','tests':r.testsRun,'failures':[(str(t),e)for t,e in r.failures+r.errors],'provenance':provenance,'examples':examples,'sources':{str(p.relative_to(R)):sha(p.read_bytes())for p in [P/'complete_nominal_policy.py',P/'test_complete_nominal_policy.py']},'limits':['Not wired to any controller; no runtime/UI/AP/new campaign authorized or performed.','Derived before projection combines separately retained raw/UI/overlap/client points; no exact whole pre-close state was persisted.','Existing frozen completion/dispatch helpers remain unchanged; canonical completion is shared production result, not independently recomputed by this policy.','Post-effect archival JSON_TYPE is separate; accepted review and stopped CID do not authorize a repeated close.']};out=E/(sys.argv[1]if len(sys.argv)>1 else'g4r2-builder-completion-policy01.json');out.open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if r.wasSuccessful()else 1)
