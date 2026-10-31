"""Builder-only G4 controller/profile/native pure mocks. No runtime, ADB or network."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation04'
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
c=mod('g4_native_controller','qa-root-controller.py');a=mod('g4_native_admission','qa-ap-admission.py');d=mod('g4_native_device','qa-device-actions.py');g=c.g
class Log:
 def __init__(self):self.text='';self.closed=False
 def write(self,x):self.text+=x
 def flush(self):pass
 def fileno(self):return 0
 def close(self):self.closed=True
class FakePath:
 def __truediv__(self,k):return self
 def open(self,*args):return log
class Tests(unittest.TestCase):
 def ctl(self):return c.Controller('06',boot_reader=lambda:'BOOT',clock=lambda:100,ui=types.SimpleNamespace())
 def test_controller_no_restore_interface(self):
  x=self.ctl();self.assertIsNone(x.host_anchor);self.assertFalse(x.snapshot()['anchors']['restoreFromJsonSupported']);self.assertFalse(hasattr(x,'restore'))
 def test_deadline_anchors_cap_and_reserve(self):
  clock=[100];x=g.DeadlineGuard(host_boot_id='BOOT',clock=lambda:clock[0]);x.anchor_emulator_before_launch('emulator-5582')
  for n in range(4):
   x.anchor_before_connect(str(n));x.note_connect_input_once(str(n));x.bind_observed_run(str(n),'s'+str(n)*20)
  with self.assertRaisesRegex(ValueError,'FOUR_CONNECT'):x.anchor_before_connect('fifth')
  clock[0]=416
  with self.assertRaisesRegex(ValueError,'BELOW225'):x.before_arm(run='s'+'0'*20,emulator_id='emulator-5582',current_host_boot_id='BOOT')
 def test_boot07_no_flight_commands_before_reference(self):
  x=self.ctl();x.persistence_only=True
  for target in ['field-connect','field-preflight','field-grant','field-upload','field-arm','field-auto','field-cut','field-reboot','video-measure','video-capture']:
   with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT07'):x.action({'target':target,'commandId':target,'reference':'NEVER_READ'})
 def test_boot07_no_batch_or_airborne(self):
  for command in [{'op':'airborne'},{'op':'sequence','steps':[{'kind':'airborne'}]}]:
   x=self.ctl();x.persistence_only=True
   with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT07'):x.command({**command,'rootApproved':True,'commandId':'boot07-no-air'})
 def test_uncertain_connect_and_failed_preparation_block_next_same_controller(self):
  for target,count in [('field-connect',0),('field-preflight',1)]:
   x=self.ctl();x.connect_count=count;x.host_instances=1;x.host_anchor=100;events=[];x.emit=lambda event,**kw:events.append(event)
   ready=types.SimpleNamespace(wait_target_ready=lambda *args,**kw:{'observation':{'seq':1}})
   def fail(*args,**kw):raise AssertionError('NO_MATCHED_RECEIPT_NO_RETRY')
   x.ui=types.SimpleNamespace(observation=lambda:{},dispatch=fail)
   with patch.object(c,'module',return_value=ready),patch.object(c,'Path',return_value=types.SimpleNamespace(read_text=lambda:'{}')),patch.object(c.subprocess,'Popen') as pop:
    with self.assertRaisesRegex(AssertionError,'NO_MATCHED_RECEIPT'):x.command({'op':'action','rootApproved':True,'commandId':'failed-first','target':target,'reference':'MOCK'})
    self.assertTrue(x.campaign_failed)
    def fence(*args,**kw):kw['before_input']('field-connect',{'observation':{}},{})
    x.ui.dispatch=fence
    with self.assertRaisesRegex(AssertionError,'FAILED_OR_UNCERTAIN_CAMPAIGN'):x.command({'op':'action','rootApproved':True,'commandId':'next-attempt','target':'field-connect','reference':'MOCK'})
    pop.assert_not_called();self.assertEqual(x.connect_count,count)
 def test_failed_readiness_preparation_latches_campaign(self):
  x=self.ctl();x.connect_count=1;x.ui=types.SimpleNamespace(observation=lambda:{})
  ready=types.SimpleNamespace(wait_target_ready=lambda *args,**kw:(_ for _ in()).throw(AssertionError('TARGET_NOT_READY')))
  with patch.object(c,'module',return_value=ready),patch.object(c,'Path',return_value=types.SimpleNamespace(read_text=lambda:'{}')):
   with self.assertRaisesRegex(AssertionError,'TARGET_NOT_READY'):x.command({'op':'action','rootApproved':True,'commandId':'preparation-failed','target':'field-preflight','reference':'MOCK'})
  self.assertTrue(x.campaign_failed)
 def test_original_host_window_expires(self):
  x=self.ctl();x.host_anchor=0;x.clock=lambda:2701;self.assertLess(x.host_remaining(),0)
 def test_scenario_order(self):
  x=self.ctl()
  for n,scenario in enumerate(['nominal','cut','nominal','reboot'],1):
   x.connect_count=n;self.assertEqual(x.scenario(scenario),scenario)
   with self.assertRaisesRegex(AssertionError,'FINITE_SCENARIO_ORDER'):x.scenario('cut'if scenario!='cut'else'nominal')
 def test_failed_campaign_no_new_airborne(self):
  x=self.ctl();x.connect_count=1;x.campaign_failed=True
  with self.assertRaisesRegex(AssertionError,'FAILED_OR_UNCERTAIN'):x.scenario('nominal')
 def test_unexpected_emulator_popen_full_error_durable_and_no_retry(self):
  global log
  log=Log();x=self.ctl();x.host_anchor=100;events=[];x.emit=lambda event,**kw:events.append((event,kw))
  with patch.object(c,'E',FakePath()),patch.object(c.os,'fsync'),patch.object(c.subprocess,'Popen',side_effect=OSError('UNEXPECTED_LAUNCH_ERROR')) as pop:
   with self.assertRaisesRegex(OSError,'UNEXPECTED'):x.launch({})
   self.assertIn('UNEXPECTED_LAUNCH_ERROR',log.text);self.assertTrue(log.closed);self.assertEqual(x.launch_error,'UNEXPECTED_LAUNCH_ERROR');self.assertTrue(any(t[0]=='EMULATOR_HELPER_POPEN_FAILED_NO_RETRY'for t in events))
   with self.assertRaisesRegex(AssertionError,'CONSUMED_NO_RETRY'):x.launch({})
   self.assertEqual(pop.call_count,1)
 def fixture(self):
  run='s'+'1'*20;name='aeris-beta06g4-'+run
  opts=['--name',name,'--platform','linux/arm64','--pull','never','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1:5972:5760','--label','aeris.task=beta06g4','--label','aeris.run='+run,'-e','AERIS_DIRECT_TRACE=0','-v',str(R/a.QUALIFIED_PATH)+':/aeris/arducopter:ro']
  return {'qualifiedProfile':a.QUALIFIED_PROFILE,'binarySha256':a.QUALIFIED_BINARY,'binaryPath':a.QUALIFIED_PATH,'binaryMode':'0755','retained':True,'containerName':name,'labels':{'aeris.task':'beta06g4','aeris.run':run},'createReceipt':'diagnostics/create-result.json','platform':'linux/arm64','observerEnabled':False,'imageId':a.QUALIFIED_IMAGE,'port':5972,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'hardDeadlineS':540,'attemptTotalMaximumS':600,'pid':123,'containerId':'a'*64,'command':['/usr/local/bin/docker','create',*opts,'rtr-aeris-sim32-trace-builder@'+a.QUALIFIED_IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']}
 def test_all_fourteen_historical_requests_guard_includes_closed_G2_G3(self):
  pins={'priorSITLRequests':[{'run':'s'+format(n,'020x')}for n in range(11)],'priorBetaSITLRequests':[{'run':'s'+'b'*20}],'priorGeneration02SITLRequests':[{'run':'sb9aef33470bc49bf84ff'}],'priorGeneration03SITLRequests':[{'run':'se15994472d0e479cbaa8'}]};runs=a.historical_runs(pins);self.assertEqual(len(runs),14);self.assertIn('se15994472d0e479cbaa8',runs);self.assertIn('sb9aef33470bc49bf84ff',runs)
  for key in ['priorGeneration02SITLRequests','priorGeneration03SITLRequests']:
   bad=copy.deepcopy(pins);bad[key]=[]
   with self.assertRaisesRegex(AssertionError,'HISTORICAL_REQUESTS'):a.historical_runs(bad)
 def test_exact_g4_retained_create_profile(self):self.assertEqual(a.qualified_launch_decision(self.fixture())['profile'],a.QUALIFIED_PROFILE)
 def test_profile_refuses_wrong_metadata_and_autoremove(self):
  for key,value in [('binaryMode','0644'),('retained',False),('qualifiedProfile','beta06-native-arm64-4.7.1'),('binaryPath','evidence/sim32-instrument01/direct-uncorrected-source/arducopter'),('containerId','fake'),('containerName','aeris-other'),('observerEnabled',True),('speedup',2),('labels',{})]:
   f=self.fixture();f[key]=value
   with self.assertRaises(AssertionError,msg=key):a.qualified_launch_decision(f)
  f=self.fixture();f['command'].insert(2,'--rm')
  with self.assertRaisesRegex(AssertionError,'RETAINED_CREATE'):a.qualified_launch_decision(f)
 def test_native_remaining_three_and_wrongsha_zero_operation(self):
  snap={'journalChain':{'pickerPendingCount':13}};self.assertEqual(d.quota_decision(snap,3)['remaining'],3)
  with self.assertRaisesRegex(AssertionError,'QUOTA_INSUFFICIENT'):d.quota_decision(snap,4)
  self.assertEqual(d.quota_decision(snap,0)['used'],13)
 def test_parent_deadline_not_reset_at_permit_or_child_start(self):
  text=(P/'qa-runtime.py').read_text();self.assertIn("parent_host_deadline=permit['parentHostDeadlinePythonMonoS']",text);self.assertIn('t<parent_host_deadline',text);self.assertIn('t<emulator_deadline',text);self.assertNotIn('t-permit_child_anchor<parent_host_remaining',text)
 def test_bounded_protocol_before_json(self):
  text=(P/'qa-root-controller.py').read_text();self.assertIn('readline(8193)',text);self.assertLess(text.index('len(line)<=8192'),text.index('json.loads(line)'))
 def test_no_uiautomator_no_control_post(self):
  for file in ['qa-ui.py','qa-android.py','qa-root-controller.py','qa-airborne.py']:
   tree=ast.parse((P/file).read_text());self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['eval','execute_script']for n in ast.walk(tree)))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'classification':'MOCK_BUILDER_ONLY','status':'PASS_BUILDER_NATIVE_CONTROLLER_PROFILE_MOCK'if r.wasSuccessful()else'FAIL','tests':r.testsRun,'failures':[(str(t),e)for t,e in r.failures+r.errors],'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in P.glob('qa-*.py')},'scope':'Pure functions, fake Popen/fs/log/UI/clock. No actual Android/AP/host/Docker/listener/flight or native acceptance.'};out=E/(sys.argv[1]if len(sys.argv)>1 else'builder-native-tests01.json');out.open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if r.wasSuccessful()else 1)
