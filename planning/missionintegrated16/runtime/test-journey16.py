#!/usr/bin/env python3
"""Scenario orchestration mock, not physical/native/video acceptance."""
from pathlib import Path
import copy,importlib.util,os,sys,types,unittest
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[3];sys.path[:0]=[str(Path(__file__).parent/'source'),str(REPO)];os.environ['AERIS_REPOSITORY_ROOT']=str(REPO)
spec=importlib.util.spec_from_file_location('scenario16',Path(__file__).parent/'scenario-mission16.py');scenario=importlib.util.module_from_spec(spec);spec.loader.exec_module(scenario)
class Clock:
 def __init__(self):self.ns=1_000_000_000
 def monotonic_ns(self):self.ns+=1_000_000;return self.ns
 def sleep(self,s):self.ns+=int(s*1e9)
class UI:
 instances=[];fault=None
 def __init__(self,owner,case,check):
  UI.instances.append(self);self.owner=owner;self.case=case;self.check=check;self.pointer=False;self.geometry=None;self.probe=types.SimpleNamespace(pid=10,process_epoch='a',last_ref={});case['probe']=self.probe;self.events=[];self.actions=[];self.closed=False;self.restarted=False;self.obs={'currentView':'plan','modal':False,'workbenchBusy':False,'planSha256':None,'consent':False};self.s={'flight':{'run':None,'navigationReadiness':{'phase':'DISARMED_READ_ONLY_NAVIGATION_READINESS','ready':True},'preflight':{'ready':True},'live':{'stage':'READY','readback63':None,'armed':False},'videoReadiness':{'ready':True},'latestPosition':{'relativeHomeM':5},'manual':{'phase':'HELD','failure':None},'completion':{'complete':False},'authority':None},'payloadCamera':{'revision':1,'source':'MOCK_PAYLOAD_READBACK'},'reviews':[],'client':{'active':False},'latestVideoQualification':{'status':'PASS'}}
 def bind_geometry(self):self.geometry={};return {}
 def observation(self):return copy.deepcopy(self.obs),0,0,b'{}',0
 def tap(self,key):
  assert not self.pointer,'unsafe UI action during pointer';self.actions.append(key)
  f=self.s['flight']
  if key=='compile':self.obs['planSha256']='a'*64
  if key=='b-connect':f['run']='run'
  if key=='b-upload':f['live']['readback63']={1:True}
  if key=='b-arm':f['live'].update(stage='ARMED_HOME_REVIEW',armed=True)
  if key=='b-gimbal':self.s['payloadCamera']['revision']+=1
  if key=='b-manual-release':f['completion']['complete']=True
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
 def native(self,*args):return {'input':{'failed':False,'configured':not self.closed,'closed':self.closed,'pending':False,'journal':{'durablyDrained':True}}}
 def save_workspace(self):return {'head':'h'*64,'planSHA256':'a'*64,'observation':{'consent':False}}
 def workspace_saved(self):return self.save_workspace()
class Journey(unittest.TestCase):
 def setUp(self):UI.instances=[];UI.fault=None
 def run_mock(self,seconds=180):
  self.commands=[];case={'plannedSeconds':seconds,'intervalProof':{'only':'MOCK_NOT_RAW'},'managementCommand':lambda x:None}
  device=types.SimpleNamespace(APPLICATION_PACKAGE='vn.rtr.aeris.betasim09',command=lambda argv,**kw:self.commands.append(argv));case['device']=device
  def rollover(**kw):
   ui=case['uiDriver'];ui.probe.pid=11;ui.probe.process_epoch='b';ui.restarted=True;return {'authorityRestored':False}
  owner=types.SimpleNamespace(manifest={'native':{'package':device.APPLICATION_PACKAGE}},planned_native_rollover=rollover)
  with patch.object(scenario,'PublicUIDriver',UI),patch.object(scenario,'time',Clock()):result=scenario.run(owner,case,lambda:None)
  return result,UI.instances[-1]
 def test_nominal_short_complete_orchestration(self):
  r,u=self.run_mock();self.assertEqual(r['status'],'PUBLIC_ANDROID_UI_WORKLOAD_COMPLETED');self.assertTrue(r['androidWorkspacePersistenceAndRestart']);self.assertEqual(self.commands,[['shell','am','force-stop','vn.rtr.aeris.betasim09']]);self.assertFalse(u.pointer)
  self.assertLess(u.actions.index('b-gimbal'),u.actions.index('b-manual-grant'));self.assertIn('AP_REBOOT',r['notCovered'])
 def test_long600_continuous_segmented_not_manual600(self):
  r,u=self.run_mock(760);self.assertEqual(r['manualSeconds'],5);self.assertEqual(r['integratedRequiredSeconds'],600)
  checkpoints=[v for k,v in u.events if k=='INTEGRATED_PAYLOAD_CHECKPOINT'];self.assertEqual([v['scheduledSecond']for v in checkpoints],[200,400,590]);self.assertEqual(u.actions.count('b-payload-grant'),4)
  interval=next(v for k,v in u.events if k=='INTEGRATED_AIRBORNE_VIDEO_PAYLOAD_INTERVAL');self.assertGreaterEqual(interval['endedHostNs']-interval['startedHostNs'],600_000_000_000);self.assertEqual(interval['actualImages'],0)
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
