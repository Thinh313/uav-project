#!/usr/bin/env python3
"""Scenario orchestration mock, not physical/native/video acceptance."""
from pathlib import Path
import copy,importlib.util,os,sys,types,unittest
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[3];sys.path[:0]=[str(Path(__file__).parent/'source'),str(REPO)];os.environ['AERIS_REPOSITORY_ROOT']=str(REPO)
spec=importlib.util.spec_from_file_location('scenarioRC01',Path(__file__).parent/'scenario-rc01.py');scenario=importlib.util.module_from_spec(spec);spec.loader.exec_module(scenario)
class Clock:
 def __init__(self):self.ns=1_000_000_000
 def monotonic_ns(self):self.ns+=1_000_000;return self.ns
 def sleep(self,s):self.ns+=int(s*1e9)
class UI:
 instances=[];fault=None
 def __init__(self,owner,case,check):
  UI.instances.append(self);self.owner=owner;self.case=case;self.check=check;self.pointer=False;self.geometry=None;self.probe=types.SimpleNamespace(pid=10,process_epoch='a',last_ref={});case['probe']=self.probe;self.events=[];self.actions=[];self.closed=False;self.restarted=False;self.obs={'currentView':'plan','modal':False,'workbenchBusy':False,'planSha256':None,'consent':False};self.s={'flight':{'run':None,'navigationReadiness':{'phase':'DISARMED_READ_ONLY_NAVIGATION_READINESS','ready':True},'preflight':{'ready':True},'live':{'stage':'READY','readback63':None,'armed':False},'videoReadiness':{'ready':True},'latestPosition':{'relativeHomeM':5},'manual':{'phase':'HELD','failure':None},'completion':{'complete':False},'authority':None,'interruptedClosable':True},'payloadCamera':{'revision':1,'source':'MOCK_PAYLOAD_READBACK'},'reviews':[],'client':{'active':False},'latestVideoQualification':{'status':'PASS'}}
 def bind_geometry(self):self.geometry={};return {}
 def observation(self):return copy.deepcopy(self.obs),0,0,b'{}',0
 def tap(self,key):
  assert not self.pointer,'unsafe UI action during pointer';self.actions.append(key)
  f=self.s['flight']
  if key=='compile':self.obs['planSha256']='a'*64
  if key=='b-connect':f['run']='run'
  if key=='b-upload':f['live']['readback63']={1:True}
  if key=='b-grant':f['authority']={'mockOnly':True}
  if key=='b-arm':f['live'].update(stage='ARMED_HOME_REVIEW',armed=True)
  if key=='b-gimbal':self.s['payloadCamera']['revision']+=1
  if key=='b-manual-release':f['completion']['complete']=True
  if key in('b-abort','b-close-interrupted'):self.s['reviews']=[{'run':'run','accepted':False}];self.closed=True
  if key=='b-close':self.s['reviews']=[{'run':'run','accepted':True}];self.closed=True
 def checked(self,key):pass
 def choose(self,key,label):self.actions.append(key)
 def target(self,key,**kw):return None
 def wait_ui(self,predicate,**kw):
  assert predicate(self.obs),kw;return copy.deepcopy(self.obs)
 def wait(self,predicate,**kw):
  if UI.fault=='navigation'and kw.get('description')=='DISARMED_READ_ONLY_NAVIGATION_READINESS':raise TimeoutError('mock navigation neverready')
  if UI.fault=='preflight'and kw.get('description')=='TYPED_PREFLIGHT':self.s['flight']['preflight']['ready']=False
  value=self.state();assert predicate(value),kw;return value
 def state(self):
  if UI.fault=='video'and self.pointer:self.s['flight']['videoReadiness']['ready']=False
  if UI.fault=='authority'and self.pointer:self.s['flight']['manual']['phase']='REVOKED'
  if self.restarted:self.s['client']['active']=False;self.s['flight']['authority']=None
  return copy.deepcopy(self.s)
 def right_pad(self):return 200,200,100
 def pointer_event(self,action,x,y):self.pointer=action!='UP';self.s['flight']['manual']['phase']='MANUAL'if self.pointer else'HELD'
 def event(self,kind,value):self.events.append((kind,copy.deepcopy(value)))
 def native(self,*args):return {'pid':self.probe.pid,'processEpoch':self.probe.process_epoch,'input':{'failed':False,'configured':not self.closed,'closed':self.closed,'pending':False,'journal':{'durablyDrained':True}}}
 def save_workspace(self):return {'head':'h'*64,'planSHA256':'a'*64,'observation':{'consent':False}}
 def workspace_saved(self):return self.save_workspace()
class Journey(unittest.TestCase):
 def setUp(self):UI.instances=[];UI.fault=None
 def run_mock(self,seconds=180,kind='polygon'):
  self.commands=[];case={'plannedSeconds':seconds,'missionKindRC01':'polygon'if kind in('link-loss','ap-reboot','native-restart')else kind,'faultKindRC01':kind if kind in('link-loss','ap-reboot','native-restart')else None,'intervalProof':{'only':'MOCK_NOT_RAW'},'managementCommand':lambda x:None}
  device=types.SimpleNamespace(APPLICATION_PACKAGE='vn.rtr.aeris.betasim09',command=lambda argv,**kw:self.commands.append(argv));case['device']=device
  def rollover(**kw):
   ui=case['uiDriver'];ui.probe.pid=11;ui.probe.process_epoch='b';ui.restarted=True;return {'authorityRestored':False}
  owner=types.SimpleNamespace(write=lambda name,value:self.commands.append((name,value)),manifest={'native':{'package':device.APPLICATION_PACKAGE}},planned_native_rollover=rollover)
  with patch.object(scenario,'PublicUIDriver',UI),patch.object(scenario,'time',Clock()):result=scenario.run(owner,case,lambda:None)
  return result,UI.instances[-1]
 def test_nominal_short_complete_orchestration(self):
  r,u=self.run_mock();self.assertEqual(r['status'],'PUBLIC_ANDROID_UI_WORKLOAD_COMPLETED');self.assertTrue(r['androidWorkspacePersistenceAndRestart']);self.assertEqual(self.commands,[['shell','am','force-stop','vn.rtr.aeris.betasim09']]);self.assertFalse(u.pointer)
  self.assertLess(u.actions.index('b-gimbal'),u.actions.index('b-manual-grant'));self.assertIn('AP_REBOOT',r['notCovered'])
 def test_long600_continuous_segmented_not_manual600(self):
  r,u=self.run_mock(760);self.assertEqual(r['manualSeconds'],5);self.assertEqual(r['integratedRequiredSeconds'],600)
  checkpoints=[v for k,v in u.events if k=='INTEGRATED_PAYLOAD_CHECKPOINT'];self.assertEqual([v['scheduledSecond']for v in checkpoints],[200,400,590]);self.assertEqual(u.actions.count('b-payload-grant'),4)
  interval=next(v for k,v in u.events if k=='INTEGRATED_AIRBORNE_VIDEO_PAYLOAD_INTERVAL');self.assertGreaterEqual(interval['endedHostNs']-interval['startedHostNs'],600_000_000_000);self.assertEqual(interval['actualImages'],0)
 def test_corridor_uses_public_selector(self):
  r,u=self.run_mock(kind='corridor');self.assertIn('sitl-kind',u.actions);self.assertIn('NOMINAL_CORRIDOR',r['scope'])
 def mocked_fault(self,owner,case):
  ui=case['uiDriver'];ui.s['flight']['authority']=None;ui.s['payloadAuthority']={'snapshot':{'leaseCount':0}};ui.s['reviews']=[{'run':'run','accepted':False,'reason':'MOCK_EXPECTED_INTERRUPTION'}];return {'kind':case['faultKindRC01'],'mockOnly':True,'dispatched':True}
 def test_link_loss_stays_interrupted_not_nominal(self):
  with patch('aeris_runtime.fault_rc01.request',side_effect=self.mocked_fault),self.assertRaises(scenario.ExpectedInterruption):self.run_mock(kind='link-loss')
  u=UI.instances[-1];self.assertNotIn('b-manual-grant',u.actions);self.assertFalse(u.s['reviews'][0]['accepted']);self.assertEqual(u.s['payloadAuthority']['snapshot']['leaseCount'],0)
 def test_ap_reboot_observation_does_not_claim_restart_from_summary(self):
  with patch('aeris_runtime.fault_rc01.request',side_effect=self.mocked_fault),self.assertRaises(scenario.ExpectedInterruption):self.run_mock(kind='ap-reboot')
  e=next(v for k,v in UI.instances[-1].events if k=='FAULT_LINK_OR_AP_REVOCATION_OBSERVED');self.assertTrue(e['actualAPRebootStillRequiresColdPIDStageProof'])
 def test_native_restart_requires_new_pid_epoch_and_no_rights(self):
  def dispatch(owner,case):
   value=self.mocked_fault(owner,case);case['uiDriver'].closed=True;return value
  with patch('aeris_runtime.fault_rc01.request',side_effect=dispatch),self.assertRaises(scenario.ExpectedInterruption):self.run_mock(kind='native-restart')
  e=next(v for k,v in UI.instances[-1].events if k=='FAULT_NATIVE_RESTART_OBSERVED');self.assertEqual(e['newPID'],11);self.assertFalse(e['authorityRestored']);self.assertEqual(e['priorInputOutcome'],'UNKNOWN_UNTIL_COLD_REPLAY')
 def test_fault_without_existing_review_uses_explicit_incomplete_abort(self):
  def dispatch(owner,case):
   value=self.mocked_fault(owner,case);case['uiDriver'].s['reviews']=[];return value
  with patch('aeris_runtime.fault_rc01.request',side_effect=dispatch),self.assertRaises(scenario.ExpectedInterruption):self.run_mock(kind='link-loss')
  u=UI.instances[-1];self.assertIn('beta-faults',u.actions);self.assertIn('b-abort',u.actions);self.assertNotIn('b-close',u.actions)
 def test_native_restart_incomplete_close_requires_ground_new_ui_consent(self):
  def dispatch(owner,case):
   value=self.mocked_fault(owner,case);case['uiDriver'].s['reviews']=[];case['uiDriver'].closed=True;return value
  with patch('aeris_runtime.fault_rc01.request',side_effect=dispatch),self.assertRaises(scenario.ExpectedInterruption):self.run_mock(kind='native-restart')
  u=UI.instances[-1];self.assertIn('b-activate',u.actions);self.assertIn('b-close-interrupted',u.actions);self.assertNotIn('b-grant',u.actions[u.actions.index('beta-faults'):])
 def test_navigation_prevents_arm(self):
  UI.fault='navigation'
  with self.assertRaises(TimeoutError):self.run_mock()
  self.assertNotIn('b-arm',UI.instances[-1].actions)
 def test_failed_preflight_prevents_grant_and_arm(self):
  UI.fault='preflight'
  with self.assertRaises(AssertionError):self.run_mock()
  self.assertNotIn('b-grant',UI.instances[-1].actions);self.assertNotIn('b-arm',UI.instances[-1].actions)
 def test_video_loss_not_nominal_completion(self):
  UI.fault='video'
  with self.assertRaises(RuntimeError):self.run_mock()
  self.assertNotIn('b-close',UI.instances[-1].actions)
 def test_authority_loss_not_nominal_completion(self):
  UI.fault='authority'
  with self.assertRaises((RuntimeError,AssertionError)):self.run_mock()
  self.assertNotIn('b-close',UI.instances[-1].actions)
if __name__=='__main__':unittest.main(verbosity=2)
