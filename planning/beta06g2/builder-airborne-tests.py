"""Actual choreography function with fake UI/state/dispatch; no Android/AP/network."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile,types,unittest
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation02'
spec=importlib.util.spec_from_file_location('g2_airborne_test',P/'qa-airborne.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def observation():
 return {'ageMs':0,'observation':{'seq':1,'documentId':'doc','clientId':'client','clientEpoch':2,'clientInstance':'instance','run':'s'+'a'*20,'boot':'boot','configId':'config','modelSha256':'model','planSha256':'plan','payloadSelection':{'stationId':'station','deviceId':'payload'},'tab':'flight','phase':'DISARMED','observedAtClientMonoMs':100,'mediaReadiness':{'active':True,'clockStatus':'CALIBRATED_BOUNDS','clockDegraded':False,'previewReady':True,'frameAgeMs':10,'clockMappingSampledBrowserMs':0,'clockMappingValidUntilBrowserMs':60000,'clockSessionId':'viewer'}}}
class Tests(unittest.TestCase):
 def exercise(self,scenario,bad_media=False):
  v=observation();o=v['observation'];seen=[];state={'flight':{'run':o['run'],'mode':'sitl','live':{'armed':True,'mode':'AUTO','stage':'AUTO'},'latestPosition':{'relativeHomeM':10},'positionAgeMs':10},'captures':[{'state':'COMMITTED','captureId':'capture','sidecar':{'context':{'flightRun':o['run']}}}],'payloadLeaseObservation':{'observedAtHostMonoMs':1,'leases':[{'remainingMs':59000,'untilHostMonoMs':59001,'flightRun':o['run'],'flightBoot':o['boot'],'modelSha256':o['modelSha256'],'planSha256':o['planSha256'],'clientId':o['clientId'],'clientEpoch':o['clientEpoch'],'clientInstance':o['clientInstance'],'stationId':'station','payloadId':'payload'}]}}
  if bad_media:o['mediaReadiness']['clockStatus']='UNKNOWN'
  with tempfile.TemporaryDirectory(prefix='builder-airborne-',dir=E)as tmp:
   base=Path(tmp);ref=base/'reference.json';ref.write_text(json.dumps({'observed':v}));fake=types.SimpleNamespace(E=base,state=lambda:copy.deepcopy(state));ui=types.SimpleNamespace(q=fake,observation=lambda:copy.deepcopy(v))
   def dispatch(target,*args):seen.append(target);return {'status':'ACKNOWLEDGED'}
   with patch.object(a,'ui',ui),patch.object(a.admission,'check',return_value={'status':'MOCK_ONLY'}),patch.object(a,'wait_target_ready',return_value=copy.deepcopy(v)):
    if bad_media:
     with self.assertRaisesRegex(AssertionError,'CALIBRATED_MEDIA'):a.run('02',ref,ref,'bad-media',scenario=scenario,dispatch=dispatch,reserve=lambda run:{'scope':'MOCK_ONLY'})
     self.assertNotIn('field-cut',seen);self.assertNotIn('field-reboot',seen);return
    record=a.run('02',ref,ref,scenario,scenario=scenario,dispatch=dispatch,reserve=lambda run:{'scope':'MOCK_ONLY'})
    self.assertEqual(record['status'],'UI_SEQUENCE_ACKNOWLEDGED_NOT_ACCEPTANCE');return seen,record
 def test_nominal_one_measure_capture_pause(self):
  seen,r=self.exercise('nominal');self.assertEqual([x for x in seen if x.startswith('video-')],['video-measure','video-capture','video-pause']);self.assertEqual(r['captureIds'],['capture']);self.assertNotIn('mediaBeforeFault',r)
 def test_cut_no_second_measure_or_capture(self):
  seen,r=self.exercise('cut');self.assertFalse(any(x.startswith('video-')for x in seen));self.assertEqual(seen[-1],'field-cut');self.assertEqual(r['mediaMetric'],'NOT_APPLICABLE_FAULT_SCENARIO');self.assertIn('mediaBeforeFault',r)
 def test_reboot_no_second_measure_or_capture(self):
  seen,r=self.exercise('reboot');self.assertFalse(any(x.startswith('video-')for x in seen));self.assertEqual(seen[-1],'field-reboot');self.assertEqual(r['mediaBeforeFault']['metricStatus'],'NOT_APPLICABLE_FAULT_SCENARIO')
 def test_unknown_media_stops_before_fault(self):self.exercise('reboot',True)
 def test_fault_point_context_freshness_and_clock_boundaries(self):
  original=observation();context={k:original['observation'][k]for k in ['documentId','run','boot','configId','modelSha256','planSha256','clientId','clientEpoch','clientInstance']};self.assertEqual(a.fault_media_point(original,context)['metricStatus'],'NOT_APPLICABLE_FAULT_SCENARIO')
  for key,value in [('ageMs',1201),('boot','other'),('frameAgeMs',1001),('clockMappingValidUntilBrowserMs',100),('clockDegraded',True),('clockMappingSampledBrowserMs',float('nan'))]:
   bad=copy.deepcopy(original)
   if key=='ageMs':bad[key]=value
   elif key=='boot':bad['observation'][key]=value
   else:bad['observation']['mediaReadiness'][key]=value
   with self.assertRaises(AssertionError):a.fault_media_point(bad,context)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'scope':'BUILDER_ACTUAL_CHOREOGRAPHY_FUNCTION_FAKE_UI_STATE_NO_RUNTIME','passed':result.wasSuccessful(),'tests':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors]};(E/'builder-airborne-tests01.json').open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if result.wasSuccessful()else 1)
