"""Builder pure controller/guard/store/phase tests; no subprocess/ADB/runtime."""
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,sys,types,unittest,tempfile
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation02';E.mkdir(parents=True,exist_ok=True)
def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
ctl=load('beta_ctl_test','qa-root-controller.py');device=load('beta_store_test','qa-device-actions.py');ui=load('beta_ui_test','qa-ui.py');runtime=load('beta_runtime_test','qa-runtime.py')
class Clock:
 def __init__(self):self.t=100.
 def __call__(self):return self.t
class Tests(unittest.TestCase):
 def setUp(self):
  self.clock=Clock();self.c=ctl.Controller('02',boot_reader=lambda:'hostboot',clock=self.clock);self.c.host_anchor=self.clock();self.c.host_process=types.SimpleNamespace(pid=888,poll=lambda:None,terminate=lambda:None,wait=lambda **k:0);self.run='s'+'a'*20;ref=E/'builder-test-reference01.json'
  if not ref.exists():ref.open('x').write(json.dumps({'observed':{'observation':{'configId':'config','run':None}}}))
 def bound(self):
  self.c.guard.anchor_emulator_before_launch('emulator-5582');self.c.guard.anchor_before_connect('c1');self.c.guard.note_connect_input_once('c1');self.c.guard.bind_observed_run('c1',self.run)
 def test_reserve_boundaries(self):
  self.bound();self.clock.t=415.;self.assertEqual(self.c.reserve(self.run)['apRemainingConservativeS'],225.);self.clock.t+=.0001
  with self.assertRaisesRegex(ValueError,'BELOW225'):self.c.reserve(self.run)
 def test_missing_restart_wrongrun(self):
  self.bound()
  for c,run in[(ctl.Controller('02',boot_reader=lambda:'hostboot',clock=self.clock),self.run),(self.c,'s'+'b'*20)]:
   with self.assertRaises((AssertionError,ValueError)):c.reserve(run)
 def test_wrongboot(self):
  self.bound();self.c.boot_reader=lambda:'otherboot'
  with self.assertRaisesRegex(ValueError,'BOOT_ID_MISMATCH'):self.c.reserve(self.run)
 def test_future_nan_and_duplicate(self):
  self.bound();self.clock.t=99
  with self.assertRaises((AssertionError,ValueError)):self.c.reserve(self.run)
  self.clock.t=float('nan')
  with self.assertRaises((AssertionError,ValueError)):self.c.reserve(self.run)
  with self.assertRaises((AssertionError,ValueError)):self.c.guard.note_connect_input_once('c1')
 def test_command_replay(self):
  self.c.approved({'op':'action','rootApproved':True,'commandId':'once'})
  with self.assertRaisesRegex(AssertionError,'COMMAND_REPLAY'):self.c.approved({'op':'action','rootApproved':True,'commandId':'once'})
 def test_ui_actual_callback_order_source(self):
  source=(P/'qa-ui.py').read_text();body=source[source.index('def dispatch('):source.index("if __name__=='__main__':")];self.assertLess(body.index('before_input(ident,latest,fresh)'),body.index("q.adb('shell','input','tap'"));self.assertLess(body.index("q.adb('shell','input','tap'"),body.index('after_input(ident,latest)'));self.assertIn('PERSISTENT_CONTROLLER_INPUT_FENCE_REQUIRED',body)
 def test_controller_real_action_wiring(self):
  self.c.guard.anchor_emulator_before_launch('emulator-5582');self.c.ground_admission={'binding':{'configId':'config'},'baselineCounts':{},'clockSessionId':'viewer-test'};events=[];obs={'configId':'config','run':None};ref=E/'builder-test-reference01.json'
  if not ref.exists():ref.open('x').write(json.dumps({'observed':{'observation':obs}}))
  def dispatch(attempt,reference,target,name,**kw):
   kw['before_input'](target,{'observation':obs});events.append(('before',len(self.c.guard.snapshot()['connectAnchors'])));events.append(('one_physical_tap',target));kw['after_input'](target,{'observation':obs});return {'status':'ACKNOWLEDGED'}
  fake=types.SimpleNamespace(dispatch=dispatch,observation=lambda:{},q=types.SimpleNamespace(state=lambda:{'flight':{'run':self.run}}));self.c.ui=fake
  orig=ctl.module
  def mods(name,file):
   if file=='qa-airborne.py':return types.SimpleNamespace(wait_target_ready=lambda *a,**k:{'observation':{'seq':1}})
   if file=='qa-ground-soak.py':return types.SimpleNamespace(sample_decision=lambda*a,**k:{})
   return orig(name,file)
  with patch.object(ctl,'module',side_effect=mods):self.c.action({'target':'field-connect','reference':str(ref),'commandId':'connect','groundStagedAndInspected':True})
  self.assertEqual(events,[('before',1),('one_physical_tap','field-connect')]);self.assertEqual(self.c.reserve(self.run)['run'],self.run)
  with patch.object(ctl,'module',side_effect=mods):
   with self.assertRaisesRegex(AssertionError,'INPUT_INTENT_REPLAY'):self.c.action({'target':'field-connect','reference':str(ref),'commandId':'connect','groundStagedAndInspected':True})
 def test_arm_guard_immediately_before_input(self):
  self.bound();self.clock.t=416.;events=[];ref=E/'builder-test-reference01.json'
  def dispatch(attempt,reference,target,name,**kw):
   kw['before_input'](target,{'observation':{'run':self.run}});events.append('tap');kw['after_input'](target,{})
  self.c.ui=types.SimpleNamespace(dispatch=dispatch,observation=lambda:{})
  with patch.object(ctl,'module',return_value=types.SimpleNamespace(wait_target_ready=lambda*a,**k:{'observation':{'seq':1}})):
   with self.assertRaisesRegex(ValueError,'BELOW225'):self.c.action({'target':'field-arm','reference':str(ref),'commandId':'arm-late'})
  self.assertEqual(events,[])
 def test_parent_prelaunch_anchor_before_child_permit(self):
  class FakeThread:
   def __init__(self,target,**kw):self.target=target
   def start(self):self.target()
  class FakeProc:
   pid=1234
   def poll(self):return None
  with tempfile.TemporaryDirectory(prefix='builder-handshake-',dir=E)as tmp:
   root=Path(tmp);(root/'android-ready-to-launch02.json').write_text('{}')
   with patch.object(ctl,'E',root),patch.object(ctl.subprocess,'Popen',return_value=FakeProc())as popen,patch.object(ctl.threading,'Thread',FakeThread):
    self.c.launch({});permit=json.loads((root/'android-launch-permit02.json').read_text());self.assertEqual(permit['anchorProof']['anchors']['emulatorBeforeLaunchPythonMonoS'],100.);self.assertEqual(permit['rootControllerPid'],__import__('os').getpid());self.assertIn('--require-permit',popen.call_args.args[0]);self.assertFalse((root/'android-launch02.json').exists());self.c.close()
 def test_sequence_stop_first_failure(self):
  seen=[]
  def action(c):
   seen.append(c['target']);raise AssertionError('UNCERTAIN_NO_RETRY')
  self.c.action=action
  with self.assertRaisesRegex(AssertionError,'UNCERTAIN'):
   self.c.command({'op':'sequence','rootApproved':True,'commandId':'batch','steps':[{'target':'first'},{'target':'second'}]})
  self.assertEqual(seen,['first'])
 def test_journal_crossboot_no_global_order(self):
  head='ROOT';rows=[]
  for n,t in enumerate([1000,2000,10],1):
   body=json.dumps({'seq':n,'previous':head,'kind':'PICKER_PENDING'if n==1 else'MIRROR_COMMITTED','elapsedMs':t,'data':{}});head=hashlib.sha256(body.encode()).hexdigest();rows.append(json.dumps({'body':body,'sha256':head}))
  raw=('\n'.join(rows)+'\n').encode();v=device.journal_chain(raw);self.assertEqual(v['records'],3);self.assertEqual(v['remainingLifetimePickerOperations'],15)
  with self.assertRaisesRegex(AssertionError,'KNOWN_BOOT'):device.journal_chain(raw,ordered=True)
  with self.assertRaises(AssertionError):device.journal_chain(raw.replace(b'ROOT',b'BAD!'))
 def test_cut_policy_exactlease(self):
  o={'phase':'AUTO','run':self.run,'boot':'boot','modelSha256':'m','planSha256':'p','clientId':'c','clientEpoch':1,'clientInstance':'i','payloadSelection':{'stationId':'station','deviceId':'cam'}};lease={'flightRun':self.run,'flightBoot':'boot','modelSha256':'m','planSha256':'p','clientId':'c','clientEpoch':1,'clientInstance':'i','stationId':'station','payloadId':'cam','untilHostMonoMs':7000,'remainingMs':5000};s={'flight':{'positionAgeMs':1,'latestPosition':{'relativeHomeM':6},'live':{'stage':'AUTO','mode':'AUTO','armed':True}},'payloadLeaseObservation':{'observedAtHostMonoMs':1000,'leases':[lease]}};ui.phase_policy('DISARMED',o,'field-cut',s)
  for key,value in [('remainingMs',4999),('clientInstance','other'),('payloadId','other')]:
   old=lease[key];lease[key]=value
   with self.assertRaisesRegex(AssertionError,'EXACT_LIVE_LEASE'):ui.phase_policy('DISARMED',o,'field-cut',s)
   lease[key]=old
  s['flight']['latestPosition']['relativeHomeM']=0
  with self.assertRaisesRegex(AssertionError,'AIRBORNE'):ui.phase_policy('DISARMED',o,'field-cut',s)
 def test_advertised_native_handoff_allowlists_before_input(self):
  # Execute actual dispatch until reference read, proving both real allowlists accept advertised IDs.
  allowed=['field-export-workspace','field-import-workspace','field-raw-'+self.run,'field-capture-export-abc123-'+'a'*12,'field-delivery-file-'+self.run+'-index-json']
  for ident in allowed:
   with self.assertRaises(FileNotFoundError):ui.dispatch('01','/nonexistent-beta-reference',ident,'mock',handoff_only=True)
  with self.assertRaisesRegex(AssertionError,'HANDOFF_ALLOWLIST'):ui.dispatch('01','/nonexistent-beta-reference','field-arm','mock',handoff_only=True)
 def test_actual_ui_dispatch_native_diagnostic_no_web_ack(self):
  # Real ui.dispatch through reference/state/frame/target checks and one mocked physical input.
  from copy import deepcopy
  import struct
  with tempfile.TemporaryDirectory(prefix='builder-native-dispatch-',dir=E)as tmp:
   base=Path(tmp);png=base/'screen.png';png.write_bytes(b'\x89PNG\r\n\x1a\n'+b'0'*8+struct.pack('>II',100,100));v={'ok':True,'ageMs':0,'observation':{'format':'clockvideo05-ui-observation-v1','foreground':True,'phase':'IDLE','seq':1,'documentId':'doc','viewport':{'width':100,'height':100,'dpr':1},'tab':'review','clientId':'c','clientEpoch':1,'clientInstance':'i','run':None,'boot':None,'configId':'config','modelSha256':'m','planSha256':'p','nativeResult':{'seq':0},'targets':[{'id':'field-qa-bad-sha','enabled':True,'visible':True,'fullyVisible':True,'unoccluded':True,'rect':{'x':10,'y':10,'width':44,'height':44}}]}};doc={'mission':{'sha256':'m'},'compiled':{'plan':{'sha256':'p'}}};state={'flight':{'run':None,'request':{},'authority':None},'client':{'id':'c','epoch':1,'instance':'i'},'workspace':{'ok':True,'pending':False,'bodyBase64':base64.b64encode(json.dumps(doc).encode()).decode()},'payloadLeaseObservation':{'leaseCount':0}};frame={'frame':[0,0,100,100],'screen':[100,100],'cssViewport':v['observation']['viewport'],'scaleX':1.,'scaleY':1.,'basis':'ROOT_DECLARED_GROUND_FRAME_BOUND_TO_ACTUAL_SCREENSHOT_AND_NATIVE_WINDOW_LINES'};ref=base/'ref.json';ref.write_text(json.dumps({'image':str(png),'imageSha256':hashlib.sha256(png.read_bytes()).hexdigest(),'observed':v,'nativeMapping':frame,'nativeWindow':{'owned':True}}));taps=[];puts=[]
   q=types.SimpleNamespace(state=lambda:state,capture=lambda *a:png,adb=lambda*a,**k:taps.append(a));callback=deepcopy(v);callback['observation']['nativeResult']={'seq':1,'ok':False,'code':'OPERATION_NOT_CONFIRMED','message':'SHA256_MISMATCH'};self.c.ui=ui
   with patch.object(ui,'q',q),patch.object(ui,'observation',return_value=v),patch.object(ui,'ground_frame_signature',return_value={'owned':True}),patch.object(ui,'put',side_effect=lambda n,b:puts.append((n,b))),patch.object(ui,'receipt_observation',return_value=callback):
    value=self.c.native_negative({'reference':str(ref),'commandId':'native-negative'})
   self.assertEqual(len(taps),1);self.assertEqual(taps[0][:3],('shell','input','tap'));self.assertEqual(value['uiDispatchIntentNotNativeResult']['status'],'ONE_NATIVE_DIAGNOSTIC_INPUT_NOT_RESULT');self.assertFalse(value['nativeCallback']['ok']);self.assertFalse(value['providerProof'])
   self.assertFalse(any('receipt'in name for name,_ in puts))
 def test_native_quota_and_known_boot_append(self):
  self.assertEqual(device.quota_decision({'journalChain':{'pickerPendingCount':10}},6)['remaining'],6)
  with self.assertRaisesRegex(AssertionError,'QUOTA_INSUFFICIENT'):device.quota_decision({'journalChain':{'pickerPendingCount':10}},7)
  head='a'*64;rows=[]
  for n,t in [(28,10),(29,11)]:
   body=json.dumps({'seq':n,'previous':head,'kind':'MIRROR_COMMITTED','elapsedMs':t,'data':{}});head=hashlib.sha256(body.encode()).hexdigest();rows.append(json.dumps({'body':body,'sha256':head}))
  v=device.journal_chain(('\n'.join(rows)+'\n').encode(),previous='a'*64,start_seq=27,ordered=True);self.assertEqual(v['firstElapsedMs'],10)
 def test_emulator_reserve_boundary(self):
  self.c.guard.anchor_emulator_before_launch('emulator-5582');self.clock.t=1600.;self.c.guard.anchor_before_connect('late');self.c.guard.note_connect_input_once('late');self.c.guard.bind_observed_run('late',self.run);self.clock.t=1660.;self.assertEqual(self.c.reserve(self.run)['emulatorRemainingConservativeS'],240.)
  self.clock.t=1660.01
  with self.assertRaisesRegex((AssertionError,ValueError),'BELOW240'):self.c.reserve(self.run)
 def test_four_connects_only(self):
  self.bound();[self.c.guard.anchor_before_connect('c'+str(i))for i in range(2,5)]
  with self.assertRaisesRegex(ValueError,'FOUR_CONNECT'):self.c.guard.anchor_before_connect('c5')
 def test_host_anchor_once_actual_method(self):
  c=ctl.Controller('02',boot_reader=lambda:'hostboot',clock=self.clock)
  class Thread:
   def __init__(self,*a,**kw):pass
   def start(self):pass
  with patch.object(ctl.threading,'Thread',Thread):
   c.anchor_host();self.assertEqual(c.host_anchor,100.)
   with self.assertRaisesRegex(AssertionError,'SINGLE'):c.anchor_host()
  self.clock.t=200.;self.assertEqual(c.host_remaining(),1700.)
 def test_persistence_boot_denies_all_flight_paths_before_input(self):
  self.c.persistence_only=True
  for ident in ['field-connect','field-preflight','field-grant','field-upload','field-arm','field-auto','field-cut','field-reboot']:
   with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT03'):self.c.action({'target':ident,'commandId':'deny-'+ident})
  with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT03'):self.c.command({'op':'airborne','rootApproved':True,'commandId':'deny-airborne'})
  with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT03'):self.c.command({'op':'sequence','rootApproved':True,'commandId':'deny-sequence','steps':[{'kind':'airborne'}]})
 def test_host_reserve_boundary_and_closure90(self):
  self.bound();self.clock.t=1660.;self.c.guard._intents={};self.c.guard._runs={};self.c.guard.anchor_before_connect('new');self.c.guard.note_connect_input_once('new');self.c.guard.bind_observed_run('new',self.run);self.assertEqual(self.c.reserve(self.run)['hostRemainingConservativeS'],240.);self.clock.t=1810.;self.assertEqual(self.c.closure_reserve(),90.);self.clock.t=1810.1
  with self.assertRaisesRegex(AssertionError,'BELOW90'):self.c.closure_reserve()
 def test_runtime_plan_guards(self):
  v=runtime.plan();self.assertEqual(v['hardDurationS'],1800);self.assertEqual(v['guardBytes'],28*2**30);self.assertEqual(v['floorBytes'],20*2**30)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'scope':'BUILDER_MOCK_ONLY_NO_RUNTIME_ADB_AP','passed':result.wasSuccessful(),'tests':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors]};p=E/'builder-helper-tests05.json';p.open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if result.wasSuccessful()else 1)
