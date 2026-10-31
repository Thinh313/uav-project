"""Pure independent future deadline guard tests, not used in past live run."""
from pathlib import Path
import importlib.util,sys,json,hashlib,datetime,math,ast
p=Path('planning/clockvideo05/qa-deadline-guard.py');spec=importlib.util.spec_from_file_location('qa_future_deadline05',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class C:
 def __init__(self,t=0):self.t=t
 def __call__(self):return self.t
run='s'+'a'*20;other='s'+'b'*20;rows=[]
def test(n,fn):
 try:fn();rows.append({'name':n,'status':'PASS'})
 except Exception as e:rows.append({'name':n,'status':'FAIL','error':str(e)})
def reject(fn,text):
 try:fn()
 except m.DeadlineGuardError as e:assert text in str(e),(text,str(e));return
 raise AssertionError('MISSING_REJECTION '+text)
def ready(start=0,connect=0,note=None,bind=None):
 c=C(start);g=m.DeadlineGuard(host_boot_id='BOOT',clock=c);g.anchor_emulator_before_launch('EMU');c.t=connect;g.anchor_before_connect('INTENT');c.t=connect if note is None else note;g.note_connect_input_once('INTENT');c.t=c.t if bind is None else bind;g.bind_observed_run('INTENT',run);return c,g
def arm(c,g):return g.before_arm(run=run,emulator_id='EMU',current_host_boot_id='BOOT')
def ap_boundary():
 c,g=ready();c.t=315;r=arm(c,g);assert r['apRemainingConservativeS']==225 and r['authorityGranted']is False and r['runtimeActionPerformed']is False;c.t=315.000001;reject(lambda:arm(c,g),'AP_REMAINING_BELOW225')
test('exact_AP225_boundary_and_epsilon_failure',ap_boundary)
def emu_boundary():
 c,g=ready(connect=650);c.t=960;r=arm(c,g);assert r['emulatorRemainingConservativeS']==240;c.t=960.000001;reject(lambda:arm(c,g),'EMULATOR_REMAINING_BELOW240')
test('exact_emulator240_boundary_and_epsilon_failure',emu_boundary)
def conservative():
 c,g=ready(connect=100,note=300,bind=310);c.t=416;reject(lambda:arm(c,g),'AP_REMAINING_BELOW225')
test('AP_clock_anchored_before_input_not_late_input_or_binding',conservative)
def identity():
 c,g=ready();reject(lambda:g.before_arm(run=other,emulator_id='EMU',current_host_boot_id='BOOT'),'EXACT_RUN_CONNECT_ANCHOR_MISSING');reject(lambda:g.before_arm(run=run,emulator_id='OTHER',current_host_boot_id='BOOT'),'EMULATOR_ANCHOR_MISMATCH');reject(lambda:g.before_arm(run=run,emulator_id='EMU',current_host_boot_id='OTHER'),'BOOT_ID_MISMATCH')
test('wrong_AP_run_emulator_or_hostboot_fail_closed',identity)
def missing():
 c=C();g=m.DeadlineGuard(host_boot_id='BOOT',clock=c);reject(lambda:arm(c,g),'EMULATOR_ANCHOR_MISSING');g.anchor_emulator_before_launch('EMU');reject(lambda:g.bind_observed_run('MISSING',run),'CONNECT_ANCHOR_MISSING');g.anchor_before_connect('A');reject(lambda:g.bind_observed_run('A',run),'INPUT_NOT_OBSERVED');reject(lambda:arm(c,g),'EXACT_RUN_CONNECT_ANCHOR_MISSING');assert g.snapshot()['restoreFromJsonSupported']is False
 test=True
test('missing_preinput_or_lost_controller_state_cannot_be_reconstructed',missing)
def clocks():
 for bad in [float('nan'),float('inf'),-1,True]:
  c,g=ready();c.t=bad;reject(lambda:arm(c,g),'FINITE_NONNEGATIVE')
 c,g=ready(start=10,connect=20,note=30,bind=40);c.t=39;reject(lambda:arm(c,g),'ANCHOR_ORDER')
test('invalid_clock_and_backward_order_fail_closed',clocks)
def duplicates():
 c,g=ready();reject(lambda:g.anchor_emulator_before_launch('EMU'),'NO_RESET');reject(lambda:g.anchor_before_connect('INTENT'),'ALREADY_ANCHORED');reject(lambda:g.note_connect_input_once('INTENT'),'SECOND_CONNECT_INPUT');g.anchor_before_connect('TWO');g.note_connect_input_once('TWO');reject(lambda:g.bind_observed_run('TWO',run),'ALREADY_BOUND');reject(lambda:g.anchor_before_connect('THREE'),'TWO_CONNECT_ANCHORS_MAX')
test('no_anchor_reset_duplicate_input_run_binding_or_third_intent',duplicates)
def source():
 s=p.read_text();tree=ast.parse(s);imports=[]
 for x in tree.body:
  if isinstance(x,ast.Import):imports += [a.name for a in x.names]
  if isinstance(x,ast.ImportFrom):imports.append(x.module)
 assert set(imports)<=set(['dataclasses','math','re','time']);assert m.AP_BUDGET_S==540 and m.EMULATOR_BUDGET_S==1200 and m.MIN_AP_REMAINING_S==225 and m.MIN_EMULATOR_REMAINING_S==240;assert not hasattr(m.DeadlineGuard,'restore')
test('pure_stdlib_no_runtime_import_or_JSON_restore_and_unchanged_budgets',source)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_FUTURE_GUARD_PURE_MOCK_ONLY_NOT_INTEGRATED'if all(x['status']=='PASS'for x in rows)else'FAIL','source':str(p),'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows,'scope':'Pure trusted-clock guard API tests only. No actual run, UI, AP, runtime, old-source mutation or retroactive qualification. Correct before-emulator/before-input integration and trusted host-boot identity require future independent actual proof. Engineering225/240s reserve is not certified mission duration.'};out=Path('evidence/field02/clockvideo05/qa-deadline-adversarial01.json');out.open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert r['status'].startswith('PASS')
