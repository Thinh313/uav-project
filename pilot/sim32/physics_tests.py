import unittest,math,json,time
from physics import *
class PhysicsTests(unittest.TestCase):
 def ideal(self,load='empty'):
  p=profile(load);p['dragCdAreaM2']=[0,0,0];p['angularDampingNms']=0;p['battery']['capacityAh']=1e12;p['battery']['internalResistanceOhm']=0;return Model(p)
 def test_freefall_analytic(self):
  m=self.ideal();m.y[2]=-100
  for _ in range(400):m.step([1000]*4,.0025)
  self.assertAlmostEqual(m.y[2],-100+G/2,places=9);self.assertAlmostEqual(m.y[5],G,places=9);self.assertLess(max(abs(x)for x in m.specific),1e-9)
 def test_hover_force_balance(self):
  m=self.ideal();m.y[2]=-10;u=math.sqrt(m.mass*G/(4*m.p['rotorMaximumThrustN']));m.u=[u]*4
  for _ in range(400):m.step([1000+1000*u]*4,.0025)
  self.assertLess(max(abs(x)for x in m.y[3:6]),1e-10);self.assertAlmostEqual(m.y[2],-10,places=9)
 def test_loaded_hover_requirement(self):
  a,b=Model(profile()),Model(profile('central'));self.assertGreater(math.sqrt(b.mass*G/88),math.sqrt(a.mass*G/88));self.assertEqual(b.mass,4)
 def test_parallel_axis_reference(self):
  m=Model(profile('offset'));self.assertEqual(m.cg,[.045,.015,.02]);self.assertAlmostEqual(m.I[0][0],.25+.75*(.06**2+.08**2));self.assertAlmostEqual(m.I[0][1],-.75*.18*.06)
 def test_inverse_tensor(self):
  m=Model(profile('offset'))
  for v in [[1,0,0],[0,1,0],[0,0,1],[2,3,4]]:
   self.assertLess(max(abs(x-y)for x,y in zip(mat(m.invI,mat(m.I,v)),v)),1e-12)
 def test_cg_wrench(self):
  m=Model(profile('offset'));F,T,ths=m.wrench([.5]*4);self.assertAlmostEqual(T[0],m.cg[1]*sum(ths));self.assertAlmostEqual(T[1],-m.cg[0]*sum(ths));self.assertAlmostEqual(T[2],0)
 def test_quad_signs(self):
  m=Model(profile());F,T,_=m.wrench([1,0,0,0]);self.assertLess(T[0],0);self.assertGreater(T[1],0);self.assertGreater(T[2],0)
 def test_actuator_analytic(self):
  m=Model(profile());m.step([2000]*4,.0025);self.assertAlmostEqual(m.u[0],1-math.exp(-.0025/.06),places=13)
 def test_pwm_saturation(self):
  m=Model(profile());m.step([0,2200,1000,2000],.0025);self.assertEqual(m.u[0],0);self.assertEqual(m.u[2],0);self.assertEqual(m.u[1],m.u[3])
 def test_ground_specific_force(self):
  m=Model(profile());m.step([1000]*4,.0025);self.assertTrue(m.ground);self.assertEqual(m.specific,[0,0,-G]);self.assertEqual(m.y[2],0)
 def test_quaternion_yaw_rotation(self):
  self.assertLess(max(abs(x-y)for x,y in zip(mat(rotation([math.sqrt(.5),0,0,math.sqrt(.5)]),[1,0,0]),[0,1,0])),1e-14)
 def test_quaternion_norm(self):
  m=self.ideal();m.y[2]=-100;m.y[10:]=[.2,.3,.1]
  for _ in range(400):m.step([1000]*4,.0025)
  self.assertAlmostEqual(dot(m.y[6:10],m.y[6:10]),1,places=12)
 def test_seed_reproducibility(self):
  a=Model(profile('central','gust',42));b=Model(profile('central','gust',42))
  for _ in range(400):a.step([1680]*4,.0025);b.step([1680]*4,.0025)
  self.assertEqual(a.snapshot(),b.snapshot());self.assertNotEqual(a.wind_at(2),Model(profile('central','gust',43)).wind_at(2))
 def test_drag_direction(self):
  m=Model(profile());m.y[2]=-10;m.y[3]=3;d=m.derivative(m.y,[0,0,0],[0,0,0],[0,0,0]);self.assertLess(d[3],0);d=m.derivative(m.y,[0,0,0],[0,0,0],[5,0,0]);self.assertGreater(d[3],0)
 def test_energy_monotonic(self):
  m=Model(profile());e=0
  for _ in range(100):m.step([1600]*4,.0025);self.assertGreater(m.energyWh,e);e=m.energyWh
 def test_battery_power_balance(self):
  m=Model(profile());m.step([2000]*4,.0025);self.assertAlmostEqual(m.voltage*m.current,m.powerW,places=10);self.assertAlmostEqual(m.lossW,m.p['battery']['internalResistanceOhm']*m.current*m.current,places=12)
 def test_voltage_thrust_scaling(self):
  m=Model(profile());F,T,_=m.wrench([.5]*4);m.voltage=12.6;f,t,_=m.wrench([.5]*4);self.assertAlmostEqual(f[2]/F[2],.25)
 def test_invalid_domain(self):
  for pwm,dt in [([1000]*4,0),([1000]*4,.01),([1000]*3,.0025),([float('nan')]*4,.0025),([2300]*4,.0025)]:
   with self.assertRaises(ValueError):Model(profile()).step(pwm,dt)
  for load,wind in [('Hera','calm'),('empty','hurricane')]:
   with self.assertRaises(ValueError):profile(load,wind)
 def test_invalid_inertia(self):
  p=profile();p['baseInertiaKgM2'][0][0]=-1
  with self.assertRaises(ValueError):Model(p)
 def test_second_order_convergence(self):
  def run(dt):
   m=self.ideal();m.y[2]=-100
   for _ in range(round(.5/dt)):m.step([1650]*4,dt)
   return m.y[2]
  a,b,c,d=[run(v)for v in [.005,.0025,.00125,.000625]];e1,e2,e3=abs(a-d),abs(b-d),abs(c-d);self.assertGreater(e1/e2,3.5);self.assertGreater(e2/e3,3.5)
if __name__=='__main__':unittest.main(verbosity=2)
