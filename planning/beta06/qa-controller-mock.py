"""Independent persistent-controller wiring tests with fake UI, boot and monotonic clock."""
from pathlib import Path
import importlib.util,sys,json,datetime,hashlib,types
p=Path('planning/beta06/qa-root-controller.py');sp=importlib.util.spec_from_file_location('qa_beta_ctl',p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
RUN='s'+'d'*20
ref=Path('evidence/beta06/qa-controller-reference-fixture01.json')
if not ref.exists():ref.open('x').write(json.dumps({'classification':'PURE_QA_FAKE_REFERENCE_NOT_ACTUAL_SCREEN','observed':{'observation':{}}})+'\n')
original_module=m.module
m.module=lambda name,file:types.SimpleNamespace(wait_target_ready=lambda reference,ident,reader:reader())if file=='qa-airborne.py'else original_module(name,file)
class Clock:
 def __init__(self,t=0):self.t=t
 def __call__(self):return self.t
class FakeUI:
 def __init__(self,clock):self.clock=clock;self.inputs=[];self.controller=None;self.config='CONFIG';self.originRun=None;self.q=types.SimpleNamespace(state=lambda:{'flight':{'run':RUN}})
 def observation(self):return {'observation':{'seq':1,'configId':self.config,'run':self.originRun}}
 def dispatch(self,attempt,reference,ident,name,timeout,before_input,after_input,handoff_only=False,diagnostic_only=False):
  o={'observation':{'configId':self.config,'run':self.originRun}}
  before_input(ident,o)
  self.inputs.append({'target':ident,'clock':self.clock(),'anchors':self.controller.guard.snapshot()})
  self.clock.t+=.1;after_input(ident,o)
  return {'status':'ACKNOWLEDGED','targetId':ident}
def make():
 c=Clock();u=FakeUI(c);ctl=m.Controller('01',boot_reader=lambda:'BOOT',clock=c,ui=u);u.controller=ctl;return c,u,ctl
def connected():
 c,u,t=make();t.guard.anchor_emulator_before_launch('emulator-5582');c.t=100;t.command({'op':'action','rootApproved':True,'commandId':'connect-a','target':'field-connect','reference':str(ref),'groundStagedAndInspected':True});u.originRun=RUN;return c,u,t
def err(fn,text):
 try:fn()
 except (AssertionError,ValueError)as e:assert text in str(e),(text,str(e));return
 raise AssertionError('MISSING_REJECTION '+text)
rows=[]
def test(n,fn):
 try:fn();rows.append({'name':n,'status':'PASS'})
 except Exception as e:rows.append({'name':n,'status':'FAIL','error':str(e)})
def anchors():
 c,u,t=connected();a=u.inputs[0]['anchors']['connectAnchors'][0];assert a['beforeInputPythonMonoS']==100 and a['inputObservedPythonMonoS']is None and a['run']is None;final=t.guard.snapshot()['connectAnchors'][0];assert final['run']==RUN and final['inputObservedPythonMonoS']==100.1;assert final['beforeInputPythonMonoS']<final['boundPythonMonoS']
test('connect_anchor_exists_before_one_input_and_run_bound_only_after_ACK',anchors)
def staging():
 for config,flag in [('CONFIG',False),(None,True)]:
  c,u,t=make();t.guard.anchor_emulator_before_launch('emulator-5582');u.config=config
  err(lambda:t.command({'op':'action','rootApproved':True,'commandId':'stage-a','target':'field-connect','reference':str(ref),'groundStagedAndInspected':flag}),'REQUIRED');assert not u.inputs and not t.guard.snapshot()['connectAnchors']
test('missing_ground_source_config_staging_refuses_before_input',staging)
def arm():
 c,u,t=connected();c.t=200;t.command({'op':'action','rootApproved':True,'commandId':'arm-a','target':'field-arm','reference':str(ref)});assert u.inputs[-1]['target']=='field-arm';assert t.reserve(RUN)['authorityGranted']is False
 c.t=416;prior=len(u.inputs);err(lambda:t.command({'op':'action','rootApproved':True,'commandId':'arm-b','target':'field-arm','reference':str(ref)}),'AP_REMAINING_BELOW225');assert len(u.inputs)==prior
 test=True
test('reserve_guard_checked_inside_actual_before_input_callback_each_ARM',arm)
def restart():
 c,u,t=make();u.originRun=RUN;err(lambda:t.command({'op':'action','rootApproved':True,'commandId':'arm-c','target':'field-arm','reference':str(ref)}),'EMULATOR_ANCHOR_MISSING');assert not u.inputs
 c,u,t=connected();t.boot_reader=lambda:'WRONG';prior=len(u.inputs);err(lambda:t.command({'op':'action','rootApproved':True,'commandId':'arm-d','target':'field-arm','reference':str(ref)}),'BOOT_ID_MISMATCH');assert len(u.inputs)==prior
 test=True
test('controller_restart_or_changed_hostboot_cannot_arm',restart)
def commands():
 c,u,t=connected();prior=len(u.inputs);err(lambda:t.command({'op':'action','rootApproved':True,'commandId':'connect-a','target':'field-connect','reference':str(ref),'groundStagedAndInspected':True}),'COMMAND_REPLAY');assert len(u.inputs)==prior
 err(lambda:t.command({'op':'action','commandId':'no-authorize','target':'field-arm','reference':str(ref)}),'ROOT_EXPLICIT_APPROVAL');assert len(u.inputs)==prior
test('duplicate_command_or_missing_explicit_authorization_zero_additional_input',commands)
def collection():
 c,u,t=connected();c.t=1710;assert t.closure_reserve()==90;c.t=1710.0001;err(t.closure_reserve,'CLOSURE_RESERVE_BELOW90S')
test('native_collection_90s_reserve_is_same_original_emulator_budget',collection)
def source():
 s=p.read_text();ui=Path('planning/beta06/qa-ui.py').read_text();assert "if before_input is not None:before_input(ident,latest,fresh)"in ui;assert ui.index('if before_input is not None:before_input(ident,latest,fresh)')<ui.index("q.adb('shell','input','tap',*point)");assert 'dispatch=lambda target,ref,name,timeout:self.action('in s;assert "anchor_emulator_before_launch('emulator-5582')" in s and s.index("anchor_emulator_before_launch('emulator-5582')")<s.index("p=E/f'android-launch-permit");assert 'noJsonAnchorRestore' in s
 test=True
test('airborne_dispatch_and_launch_permit_have_actual_guarded_wiring',source)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_CONTROLLER_WIRING_MOCK_ONLY'if all(q['status']=='PASS'for q in rows)else'FAIL','sources':{str(q):hashlib.sha256(q.read_bytes()).hexdigest()for q in [p,Path('planning/beta06/qa-ui.py'),Path('planning/beta06/qa-deadline-guard.py')]},'rows':rows,'scope':'Actual Controller methods executed using fake clock/hostboot/UI/readiness and no journal. Readiness is separately tested; this test isolates actual guard callback wiring. No launch(), emulator, subprocess, actual UI, AP or runtime start. Threaded real prelaunch permit/liveness still requires separate source and actual evidence.'};out=Path('evidence/beta06/qa-controller-mock04.json');out.open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert r['status'].startswith('PASS')
