"""Provisional reference rigid body. SI, NED earth, FRD body, IMU at combined CG."""
import math,json,copy
from _sim32_kernel import derivative as native_derivative
from _sim32_integrator import rk4
G=9.80665
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def scale(a,s):return [x*s for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def mat(a,b):return [dot(r,b)for r in a]
def transpose(a):return [list(r)for r in zip(*a)]
def inverse(a):
 A,B,C=a[0];D,E,F=a[1];H,I,J=a[2];det=A*(E*J-F*I)-B*(D*J-F*H)+C*(D*I-E*H)
 if det<=1e-12:raise ValueError('Inertia not positive definite')
 return [[(E*J-F*I)/det,(C*I-B*J)/det,(B*F-C*E)/det],[(F*H-D*J)/det,(A*J-C*H)/det,(C*D-A*F)/det],[(D*I-E*H)/det,(B*H-A*I)/det,(A*E-B*D)/det]]
def qmul(a,b):
 w,x,y,z=a;v,i,j,k=b;return [w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v]
def rotation(q):
 n=math.sqrt(dot(q,q));w,x,y,z=[a/n for a in q]
 return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
def profile(load='empty',wind='calm',seed=32):
 if load not in ['empty','central','offset']or wind not in ['calm','crosswind','gust']or not isinstance(seed,int)or not 0<=seed<=65535:raise ValueError('Unsupported reference profile')
 return {'format':'aeris-sim32-physics-profile','version':1,'id':'reference-quad-x-'+load+'-'+wind,'calibration':'PROVISIONAL_SYNTHETIC_NOT_HERA','units':'SI; NED/FRD; radians; quaternion wxyz body-to-NED','baseMassKg':3.0,'baseInertiaKgM2':[[.25,0,0],[0,.25,0],[0,0,.45]],'payloadMassKg':0 if load=='empty'else 1.,'payloadPositionBodyM':[.18,.06,.08]if load=='offset'else[0,0,.08],'armRadiusM':.5,'rotorMaximumThrustN':22.,'rotorMaximumRpm':6500.,'actuatorTauS':.06,'yawTorquePerThrustM':.025,'angularDampingNms':.08,'dragCdAreaM2':[.15,.15,.10],'airDensityKgM3':1.225,'battery':{'capacityAh':10.,'nominalV':22.2,'internalResistanceOhm':.06,'auxiliaryW':20.,'powerCoefficientWPerN15':3.0},'wind':wind,'seed':seed,'ground':'ideal flat level pad at virtual Home; no impact/bounce fidelity','provenance':'Engineering assumptions for implementation/reference tests only','unsupported':['Hera calibration','non-quad airframes','propwash','ground effect','sling dynamics','CFD','physical acoustic SPL','real media']}
class Model:
 def __init__(self,p):
  if p.get('format')!='aeris-sim32-physics-profile' or p.get('version')!=1:raise ValueError('Profile version/format')
  for key in ['baseMassKg','armRadiusM','rotorMaximumThrustN','rotorMaximumRpm','actuatorTauS','airDensityKgM3','yawTorquePerThrustM']:
   if not isinstance(p[key],(int,float)) or not math.isfinite(p[key]) or p[key]<=0:raise ValueError('Positive finite profile field: '+key)
  if not math.isfinite(p['payloadMassKg']) or p['payloadMassKg']<0 or p['wind'] not in ['calm','crosswind','gust']:raise ValueError('Payload/wind domain')
  if len(p['payloadPositionBodyM'])!=3 or not all(math.isfinite(x) and abs(x)<=2 for x in p['payloadPositionBodyM']):raise ValueError('Payload position domain')
  I=p['baseInertiaKgM2']
  if len(I)!=3 or any(len(r)!=3 for r in I) or not all(math.isfinite(I[i][j]) and abs(I[i][j]-I[j][i])<1e-12 for i in range(3) for j in range(3)):raise ValueError('Symmetric finite inertia required')
  if I[0][0]<=0 or I[0][0]*I[1][1]-I[0][1]**2<=0:raise ValueError('Positive definite base inertia')
  inverse(I)
  if len(p['dragCdAreaM2'])!=3 or not all(math.isfinite(x) and x>=0 for x in p['dragCdAreaM2']):raise ValueError('Drag domain')
  if not math.isfinite(p['angularDampingNms']) or p['angularDampingNms']<0:raise ValueError('Damping domain')
  if not all(math.isfinite(v) and (v>=0 if k=='internalResistanceOhm' else v>0) for k,v in p['battery'].items()):raise ValueError('Battery domain')
  self.p=copy.deepcopy(p);self.mass=p['baseMassKg']+p['payloadMassKg'];self.cg=scale(p['payloadPositionBodyM'],p['payloadMassKg']/self.mass);self.I=copy.deepcopy(p['baseInertiaKgM2'])
  for mass,pos in [(p['baseMassKg'],[0,0,0]),(p['payloadMassKg'],p['payloadPositionBodyM'])]:
   d=sub(pos,self.cg)
   for i in range(3):
    for j in range(3):self.I[i][j]+=mass*((dot(d,d)if i==j else 0)-d[i]*d[j])
  if self.I[0][0]<=0 or self.I[0][0]*self.I[1][1]-self.I[0][1]**2<=0:raise ValueError('Invalid inertia')
  self.invI=inverse(self.I);a=p['armRadiusM']/math.sqrt(2);self.rotors=[[a,a,0],[-a,-a,0],[a,-a,0],[-a,a,0]];self.yaw=[1,1,-1,-1];self.y=[0,0,0,0,0,0,1,0,0,0,0,0,0];self.u=[0]*4;self.t=0.;self.energyWh=0.;self.force=[0,0,0];self.torque=[0,0,0];self.specific=[0,0,-G];self.voltage=25.2;self.current=0.;self.wind=[0,0,0];self.ground=True;self.levers=[sub(r,self.cg) for r in self.rotors];self.coefficients={}
 def wind_at(self,t):
  if self.p['wind']=='calm':return [0,0,0]
  if self.p['wind']=='crosswind':return [0,3,0]
  phase=self.p['seed']*.071
  return [1.5*math.sin(.7*t+phase),3+1.5*math.sin(1.1*t+phase),.3*math.sin(.9*t+phase)]
 def wrench(self,u):
  thrust=[self.p['rotorMaximumThrustN']*v*v*(self.voltage/25.2)**2 for v in u];tau=[0,0,0]
  for r,T,s in zip(self.levers,thrust,self.yaw):tau=add(tau,add(cross(r,[0,0,-T]),[0,0,s*T*self.p['yawTorquePerThrustM']]))
  return [0,0,-sum(thrust)],tau,thrust
 def derivative(self,y,force,torque,wind):
  return native_derivative(y,force,torque,wind,self.I,self.invI,self.p['dragCdAreaM2'],self.mass,self.p['airDensityKgM3'],self.p['angularDampingNms'])
 def derivative_python(self,y,force,torque,wind):
  v=y[3:6];q=y[6:10];w=y[10:13];R=rotation(q);rel=mat(transpose(R),sub(v,wind));drag=[-.5*self.p['airDensityKgM3']*A*x*abs(x)for A,x in zip(self.p['dragCdAreaM2'],rel)];acc=add(scale(mat(R,add(force,drag)),1/self.mass),[0,0,G]);wd=mat(self.invI,sub(sub(torque,cross(w,mat(self.I,w))),scale(w,self.p['angularDampingNms'])));qd=scale(qmul(q,[0,*w]),.5);return [*v,*acc,*qd,*wd]
 def step(self,pwm,dt):
  if len(pwm)<4 or not all(isinstance(x,(int,float))and math.isfinite(x)and 0<=x<=2200 for x in pwm)or not math.isfinite(dt)or not 0<dt<=.005:raise ValueError('PWM/dt outside model domain')
  target=[max(0,min(1,(x-1000)/1000))for x in pwm[:4]]
  key=(dt,self.p['actuatorTauS'])
  if key not in self.coefficients:
   if len(self.coefficients)>=16:self.coefficients.clear()
   self.coefficients[key]=(1-math.exp(-dt/self.p['actuatorTauS']),1-math.exp(-dt/2/self.p['actuatorTauS']))
  f,half=self.coefficients[key];end=[a+(b-a)*f for a,b in zip(self.u,target)];mid=[a+(b-a)*half for a,b in zip(self.u,target)];force,torque,thrust=self.wrench(mid);wind=self.wind_at(self.t+dt/2);y=self.y;z=rk4(y,force,torque,wind,self.I,self.invI,self.p['dragCdAreaM2'],self.mass,self.p['airDensityKgM3'],self.p['angularDampingNms'],dt);qn=math.sqrt(dot(z[6:10],z[6:10]));z[6:10]=scale(z[6:10],1/qn)
  self.ground=z[2]>=0
  if self.ground:
   # Ideal level support; explicitly not a contact/impact simulator.
   yaw=math.atan2(rotation(z[6:10])[1][0],rotation(z[6:10])[0][0]);z[:6]=[z[0],z[1],0,0,0,0];z[6:10]=[math.cos(yaw/2),0,0,math.sin(yaw/2)];z[10:13]=[0,0,0]
  if not all(math.isfinite(v)for v in z)or max(abs(v)for v in z[10:])>100 or max(abs(v)for v in z[:3])>1000:raise ValueError('Model diverged/domain exceeded')
  self.y=z;self.u=end;self.t+=dt;self.force=force;self.torque=torque;self.wind=wind
  if self.ground:self.specific=[0,0,-G]
  else:
   acc=self.derivative(z,force,torque,wind)[3:6];self.specific=mat(transpose(rotation(z[6:10])),sub(acc,[0,0,G]))
  b=self.p['battery'];power=b['auxiliaryW']+b['powerCoefficientWPerN15']*sum(T**1.5 for T in thrust);soc=max(0,1-self.energyWh/(b['capacityAh']*b['nominalV']));ocv=21+4.2*soc;resistance=b['internalResistanceOhm'];disc=ocv*ocv-4*resistance*power
  if disc<0:raise ValueError('Battery power exceeds model feasible branch')
  self.current=2*power/(ocv+math.sqrt(disc));self.voltage=ocv-resistance*self.current;self.energyWh+=ocv*self.current*dt/3600;self.powerW=power;self.lossW=resistance*self.current**2
  return self.sensors()
 def sensors(self):return {'timestamp':self.t,'imu':{'gyro':self.y[10:13],'accel_body':self.specific},'position':self.y[:3],'velocity':self.y[3:6],'quaternion':self.y[6:10],'battery':{'voltage':self.voltage,'current':self.current},'velocity_wind':self.wind}
 def snapshot(self):return {**self.sensors(),'rpmEstimated':[v*self.p['rotorMaximumRpm']*(self.voltage/25.2)for v in self.u],'massKg':self.mass,'cgBodyM':self.cg,'inertiaKgM2':self.I,'energyWhEstimated':self.energyWh,'ground':self.ground,'calibration':self.p['calibration'],'profileId':self.p['id']}
