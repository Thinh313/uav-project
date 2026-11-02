import copy,importlib.util,pathlib,unittest
p=pathlib.Path(__file__).with_name('diagnostic-nav-policy.py');s=importlib.util.spec_from_file_location('diagnostic_nav_policy',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
C={'run':'new-unseen-run','epoch':'e13','boot':'boot13'};N=90_000_000_000

def fixture():
 base={'context':dict(C),'system':42,'component':1,'hostNs':N-100_000_000};coord={'latitudeE7':108540000,'longitudeE7':1068070000,'altitudeMSLmm':10000}
 return {'context':dict(C),'clockDomain':m.CLOCK_DOMAIN,'expectedHome':dict(coord),'observations':{'gps':[{**base,**coord,'fixType':6,'satellites':12,'HDOPx100':121}],'home':[{**base,**coord}],'ekf':[{**base,'ekfFlags':55}],'boot':[{**base,'APTimeBootMs':12000}]}}
class PolicyTests(unittest.TestCase):
 def call(self,v):
  out=m.diagnose(v,C,N);self.assertFalse(out['authorityGranted']);self.assertFalse(out['originalGateOverride']);self.assertEqual(out['internalEKFRootCause'],'UNOBSERVED');return out
 def test_observed_good_is_not_navigation_or_authority_acceptance(self):self.assertEqual(self.call(fixture())['codes'],['OBSERVED_PREREQUISITES_PRESENT_ORIGINAL_GATES_STILL_REQUIRED'])
 def test_flags167_and_valid_GPS_are_not_fusion_or_bias_proof(self):
  v=fixture();v['observations']['ekf'][0]['ekfFlags']=167;o=self.call(v);self.assertIn('EKF_CONSTANT_POSITION_MODE',o['codes']);self.assertIn('EKF_REQUIRED_NAVIGATION_FLAGS_MISSING',o['codes']);self.assertEqual(o['hypotheses'][0]['status'],'UNPROVEN_REQUIRES_INTERNAL_STATE_OR_MEASURED_TRANSITION')
 def test_missing_gps(self):
  v=fixture();v['observations'].pop('gps');self.assertIn('GPS_ABSENT',self.call(v)['codes'])
 def test_stale_gps_even_good_ekf(self):
  v=fixture();v['observations']['gps'][0]['hostNs']=N-1_500_000_001;self.assertIn('GPS_STALE_1500MS',self.call(v)['codes'])
 def test_freshness_boundary_unchanged(self):
  v=fixture();v['observations']['gps'][0]['hostNs']=N-1_500_000_000;self.assertNotIn('GPS_STALE_1500MS',self.call(v)['codes'])
 def test_stale_ekf_55_not_ready(self):
  v=fixture();v['observations']['ekf'][0]['hostNs']=N-2_000_000_000;self.assertIn('EKF_STALE_1500MS',self.call(v)['codes'])
 def test_home_mismatch(self):
  v=fixture();v['observations']['home'][0]['latitudeE7']+=10000;self.assertIn('HOME_DIFFERS_FROM_DECLARED_SIM_ORIGIN',self.call(v)['codes'])
 def test_home_msl_altitude_mismatch(self):
  v=fixture();v['observations']['home'][0]['altitudeMSLmm']+=6000;self.assertIn('HOME_DIFFERS_FROM_DECLARED_SIM_ORIGIN',self.call(v)['codes'])
 def test_invalid_coordinate(self):
  v=fixture();v['observations']['gps'][0]['latitudeE7']=900000001;self.assertIn('GPS_COORDINATE_OR_MSL_UNIT_DOMAIN',self.call(v)['codes'])
 def test_zero_zero_valid_coordinate(self):
  v=fixture();v['expectedHome'].update(latitudeE7=0,longitudeE7=0)
  for key in('gps','home'):v['observations'][key][0].update(latitudeE7=0,longitudeE7=0)
  self.assertEqual(self.call(v)['codes'],['OBSERVED_PREREQUISITES_PRESENT_ORIGINAL_GATES_STILL_REQUIRED'])
 def test_boot_rollback_requires_new_epoch(self):
  v=fixture();r=v['observations']['boot'][0];v['observations']['boot']=[{**r,'hostNs':r['hostNs']-1,'APTimeBootMs':13000},r];self.assertIn('AP_BOOT_ROLLBACK_OR_WRAP_NEW_EPOCH_REQUIRED',self.call(v)['codes'])
 def test_foreign_session(self):
  v=fixture();v['context']['epoch']='foreign';self.assertEqual(self.call(v)['codes'],['FOREIGN_OR_MISSING_CONTEXT'])
 def test_foreign_boot_in_single_packet(self):
  v=fixture();v['observations']['ekf'][0]['context']={**C,'boot':'reboot'};self.assertEqual(self.call(v)['codes'],['FOREIGN_OBSERVATION_CONTEXT'])
 def test_foreign_target(self):
  v=fixture();v['observations']['gps'][0]['component']=100;self.assertEqual(self.call(v)['codes'],['FOREIGN_OBSERVATION_TARGET'])
 def test_clock_domain_not_mixed(self):
  v=fixture();v['clockDomain']='NODE_HRTIME';self.assertEqual(self.call(v)['codes'],['UNQUALIFIED_CLOCK_DOMAIN'])
 def test_future_host_time(self):
  v=fixture();v['observations']['home'][0]['hostNs']=N+1;self.assertEqual(self.call(v)['codes'],['INVALID_OR_FUTURE_HOST_TIME'])
 def test_host_order_rollback(self):
  v=fixture();r=v['observations']['boot'][0];v['observations']['boot']=[{**r,'hostNs':r['hostNs']+1},r];self.assertEqual(self.call(v)['codes'],['HOST_ARRIVAL_ROLLBACK'])
 def test_sample_bound(self):
  v=fixture();v['observations']['gps']*=513;self.assertEqual(self.call(v)['codes'],['OBSERVATION_BOUND_OR_SCHEMA'])
 def test_boolean_timestamp_not_integer(self):
  v=fixture();v['observations']['home'][0]['hostNs']=True;self.assertEqual(self.call(v)['codes'],['INVALID_OR_FUTURE_HOST_TIME'])
 def test_boolean_ekf_not_flags(self):
  v=fixture();v['observations']['ekf'][0]['ekfFlags']=True;self.assertIn('INVALID_EKF_FLAGS',self.call(v)['codes'])
 def test_gps_fix2_cannot_substitute_for_3d(self):
  v=fixture();v['observations']['gps'][0]['fixType']=2;self.assertIn('GPS_FIX_NOT_3D',self.call(v)['codes'])
 def test_unknown_satellite_count(self):
  v=fixture();v['observations']['gps'][0]['satellites']=255;self.assertIn('GPS_SATELLITE_QUALITY_UNQUALIFIED',self.call(v)['codes'])
 def test_fix7_static_not_allowed_by_original_geography(self):
  v=fixture();v['observations']['gps'][0]['fixType']=7;self.assertIn('GPS_FIX_NOT_3D',self.call(v)['codes'])
 def test_uninitialized_flags_never_observed_good(self):
  v=fixture();v['observations']['ekf'][0]['ekfFlags']=55|1024;self.assertIn('EKF_FLAGS_OUTSIDE_ORIGINAL_ALLOWED_MASK',self.call(v)['codes'])
 def test_HDOP_missing_unknown_boolean_and_boundary(self):
  for value in(None,True,65535,201,-1):
   with self.subTest(value=value):
    v=fixture();v['observations']['gps'][0]['HDOPx100']=value;self.assertIn('GPS_HDOP_UNQUALIFIED_OR_ABOVE_200',self.call(v)['codes'])
  for value in(0,200):
   with self.subTest(value=value):
    v=fixture();v['observations']['gps'][0]['HDOPx100']=value;self.assertNotIn('GPS_HDOP_UNQUALIFIED_OR_ABOVE_200',self.call(v)['codes'])
 def test_source_objects_not_mutated(self):
  v=fixture();old=copy.deepcopy(v);self.call(v);self.assertEqual(v,old)
 def test_constantpos_with_healthy_mask_still_not_good(self):
  v=fixture();v['observations']['ekf'][0]['ekfFlags']=55|128;self.assertIn('EKF_CONSTANT_POSITION_MODE',self.call(v)['codes'])
if __name__=='__main__':unittest.main(verbosity=2)
