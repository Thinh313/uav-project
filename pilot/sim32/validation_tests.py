import unittest,copy
from physics import Model,profile
class ProfileValidation(unittest.TestCase):
 def test_invalid_mass_and_motor_domain(self):
  for key,value in [('baseMassKg',0),('payloadMassKg',-1),('actuatorTauS',0),('rotorMaximumThrustN',float('nan')),('rotorMaximumRpm',float('inf'))]:
   with self.subTest(key=key):
    p=profile();p[key]=value
    with self.assertRaises(ValueError):Model(p)
 def test_nonsymmetric_or_nonpositive_inertia(self):
  for I in [[[1,.2,0],[0,1,0],[0,0,1]],[[1,2,0],[2,1,0],[0,0,1]],[[1,0,0],[0,1,0],[0,0,-1]]]:
   p=profile();p['baseInertiaKgM2']=I
   with self.assertRaises(ValueError):Model(p)
 def test_invalid_battery_and_drag(self):
  for key in profile()['battery']:
   p=profile();p['battery'][key]=-1 if key=='internalResistanceOhm' else 0
   with self.assertRaises(ValueError):Model(p)
  p=profile();p['dragCdAreaM2']=[1,-1,1]
  with self.assertRaises(ValueError):Model(p)
 def test_valid_ideal_zeros_and_invalid_damping(self):
  p=profile();p['angularDampingNms']=0;p['battery']['internalResistanceOhm']=0;Model(p).step([1000]*4,.0025)
  for value in [-1,float('nan'),float('inf')]:
   p=profile();p['angularDampingNms']=value
   with self.assertRaises(ValueError):Model(p)
 def test_isolated_profile_copy(self):
  p=profile('offset','gust');m=Model(p);p['payloadPositionBodyM'][0]=100;p['battery']['capacityAh']=0
  self.assertAlmostEqual(m.cg[0],.045);self.assertEqual(m.p['battery']['capacityAh'],10)
if __name__=='__main__':unittest.main(verbosity=2)
