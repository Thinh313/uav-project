"""Declarative synthetic fixtures. Numerical criteria apply only to these fixtures."""
import math


def physics_cases():
    return [{'id':f'PY-{load}-{wind}-{pattern}', 'requirement':'R75-02', 'kind':'OPEN_LOOP_PWM_REFERENCE',
             'load':load, 'wind':wind, 'seed':32, 'pattern':pattern, 'durationS':.5, 'dt':.0025,
             'expected':{'nativePythonMaxAbs':1e-9,'dtHalfMaxAbs':.002,'quaternionNormError':1e-10},
             'heraValidated':False,'autopilotExecuted':False}
            for load in ['empty','central','offset'] for wind in ['calm','gust']
            for pattern in ['coupled-positive','coupled-negative','coupled-pitch-positive-yaw-negative',
                            'coupled-pitch-negative-yaw-positive','pitch-then-yaw']]


def pwm_fixture(u, pattern, t):
    if pattern == 'pitch-then-yaw':
        pitch,yaw = (.015,0.) if t < .25-1e-10 else (0.,.015)
    else:
        pitch,yaw = {'coupled-positive':(.015,.015),'coupled-negative':(-.015,-.015),
                     'coupled-pitch-positive-yaw-negative':(.015,-.015),
                     'coupled-pitch-negative-yaw-positive':(-.015,.015)}[pattern]
    # Reference SIM32 rotor order: (+x,+y),(-x,-y),(+x,-y),(-x,+y).
    # Pitch wrench is +x*T, yaw directions +,+,-,-. Roll cancels for symmetric CG.
    # Mix squared normalized speed (reference thrust), then map to PWM. Mixing
    # PWM directly introduces a cross-axis p*y moment because thrust is quadratic.
    return [1000+1000*math.sqrt(u*u+pitch+yaw),1000+1000*math.sqrt(u*u-pitch+yaw),
            1000+1000*math.sqrt(u*u+pitch-yaw),1000+1000*math.sqrt(u*u-pitch-yaw)]


def rotation_cases():
    return [{'id':f'ROT-{i+1:02}', 'requirement':'R75-02', 'rates':rates,'dt':.05,'steps':40}
            for i,rates in enumerate([[0,0,0],[0,.3,.4],[0,-.3,.4],[0,.3,-.4],[0,-.3,-.4],
                                      [.2,.3,.4],[0,0,math.pi],[0,1.55,0]])]


def collision_cases():
    wall = {'kind':'plane','normal':[-1.,0.,0.],'offset':-10.}
    ground = {'kind':'plane','normal':[0.,0.,-1.],'offset':0.}
    slope = {'kind':'plane','normal':[2**-.5,0.,-2**-.5],'offset':0.}
    sphere = {'kind':'sphere','center':[0.,0.,0.],'radius':.5}
    def c(id,p,e,r,s,expected):
        return {'id':id,'requirement':'R75-04','start':p,'end':e,'radius':r,'shape':s,'expectedFraction':expected}
    return [c('COL-wall-cross',[0,0,-5],[20,0,-5],.5,wall,.475),
            c('COL-wall-clear',[0,0,-5],[9,0,-5],.5,wall,None),
            c('COL-wall-touch',[0,0,-5],[9.5,0,-5],.5,wall,1.),
            c('COL-wall-overlap',[9.8,0,-5],[0,0,-5],.5,wall,0.),
            c('COL-ground',[0,0,-2],[0,0,2],.5,ground,.375),
            c('COL-ground-clear',[0,0,-2],[0,0,-1],.5,ground,None),
            c('COL-slope',[0,0,-2],[0,0,2],.5,slope,(2-.5*math.sqrt(2))/4),
            c('COL-sphere-tunnel',[-10,0,0],[10,0,0],.5,sphere,.45),
            c('COL-sphere-tangent',[-2,1,0],[2,1,0],.5,sphere,.5),
            c('COL-sphere-near-miss',[-2,1.001,0],[2,1.001,0],.5,sphere,None),
            c('COL-sphere-initial',[0,0,0],[3,0,0],.5,sphere,0.),
            c('COL-sphere-stationary',[3,0,0],[3,0,0],.5,sphere,None),
            c('COL-sphere-away',[3,0,0],[5,0,0],.5,sphere,None),
            c('COL-sphere-reverse',[10,0,0],[-10,0,0],.5,sphere,.45)]


def policy_fixture():
    return {'marginM':1.,'decelerationMps2':2.,'dt':.02,'ttl':.2,'modes':['MOCK_LOITER'],
            'assurance':'SYNTHETIC_POLICY_NOT_ARDUPILOT','clearance':'surface to vehicle sphere along single approach ray'}


def context():
    return {'target':'42/1','session':'mock-session75','boot':'mock-boot75','frame':'FRD_METRES',
            'clock':'MOCK_MONOTONIC_S','mode':'MOCK_LOITER','now':1.}


def sensor():
    return {k:v for k,v in context().items() if k not in ['mode','now']} | {'t':1.,'healthy':True,'clearanceM':5.}


def avoidance_cases():
    cases = []
    for i,(key,value) in enumerate([('target','99/1'),('session','old-session'),('boot','old-boot'),
                                  ('frame','ENU_METRES'),('clock','HOST_WALL_S'),('t',.799),('t',1.001),('healthy',False)]):
        cases.append({'id':f'AV-invalid-{i+1:02}','requirement':'R75-03','sensorPatch':{key:value},'contextPatch':{},'requested':4.,'expected':'UNAVAILABLE'})
    cases.extend([
        {'id':'AV-wrong-mode','sensorPatch':{},'contextPatch':{'mode':'AUTO'},'requested':4.,'expected':'UNAVAILABLE'},
        {'id':'AV-within-margin','sensorPatch':{'clearanceM':.5},'contextPatch':{},'requested':4.,'expected':'MOCK_LIMIT','speed':0.},
        {'id':'AV-retreat','sensorPatch':{'clearanceM':.5},'contextPatch':{},'requested':-2.,'expected':'MOCK_LIMIT','speed':-2.},
        {'id':'AV-fresh-boundary','sensorPatch':{'t':.8},'contextPatch':{},'requested':1.,'expected':'MOCK_LIMIT','speed':1.},
    ])
    return [dict(requirement='R75-03',**c) if 'requirement' not in c else c for c in cases]
