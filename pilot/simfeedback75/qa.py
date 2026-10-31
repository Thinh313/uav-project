"""Run from project root with PYTHONDONTWRITEBYTECODE=1. Exclusive evidence output."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import pathlib
import random
import shutil
import sys
import time
from engine import advance, contact, digest, forward, replay, seal, speed_envelope
from corpus import physics_cases, rotation_cases, collision_cases, avoidance_cases, context, sensor, policy_fixture, pwm_fixture
import oracle

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLOOR = 20*1024**3
OUT = None


def save(name, value):
    if shutil.disk_usage(ROOT).free < FLOOR + 32*1024**2:
        raise RuntimeError('DISK_FLOOR')
    if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) > 30*1024**2:
        raise RuntimeError('EVIDENCE_BUDGET')
    with (OUT/name).open('x') as f:
        json.dump(value,f,ensure_ascii=False,allow_nan=False,indent=2)


def model_module():
    sys.path.insert(0,str(ROOT/'pilot/sim32'))
    spec = importlib.util.spec_from_file_location('sim75_frozen_reference', ROOT/'pilot/sim32/physics.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def header(profile, scene):
    return {'version':1,'assurance':'MOCK_ONLY','units':'SI','world':'NED','body':'FRD',
            'datum':'VIRTUAL_HOME_NED_METRES','clock':'MOCK_MONOTONIC_S',
            'target':'42/1','session':'mock-session75','boot':'mock-boot75',
            'profileSha256':digest(profile),'sceneSha256':digest(scene),
            'modelSha256':digest({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
                'pilot/sim32/physics.py','pilot/sim32/kernel.c','pilot/sim32/_sim32_kernel.cpython-314-darwin.so']})}


def sample(t,p,q,velocity):
    return {'t':t,'target':'42/1','session':'mock-session75','boot':'mock-boot75',
            'position':p,'quaternion':q,'velocity':velocity,'kind':'MODEL_STATE'}


def physics_run(mod, case, dt, python=False):
    m = mod.Model(mod.profile(case['load'],case['wind'],case['seed']))
    if python:
        m.derivative = m.derivative_python
    m.y[2] = -20.
    u = math.sqrt(m.mass*mod.G/88)
    m.u = [u]*4
    frames = []
    for i in range(round(case['durationS']/dt)):
        t = i*dt
        pwm = pwm_fixture(u,case['pattern'],t)
        m.step(pwm,dt)
        if m.ground:
            raise AssertionError('Fixture exited free-flight domain')
        frames.append({'state':m.y[:],'sensor':m.sensors(),'pwm':pwm})
    return m,frames


def run():
    rows = []; traces = []; mod = model_module()
    neutral_model = mod.Model(mod.profile())
    for pattern,signs in [('coupled-positive',(1,1)),('coupled-negative',(-1,-1)),
                          ('coupled-pitch-positive-yaw-negative',(1,-1)),
                          ('coupled-pitch-negative-yaw-positive',(-1,1))]:
        forces = [(p-1000)/1000 for p in pwm_fixture(.6,pattern,0)]
        _, torque, _ = neutral_model.wrench(forces)
        assert abs(torque[0]) < 1e-12 and torque[1]*signs[0]>.01 and torque[2]*signs[1]>.001
    rows.append({'id':'PY-axis-wrench-contract','pass':True,'patterns':4,'rollMomentAbsMax':1e-12})
    for c in physics_cases():
        m,a = physics_run(mod,c,c['dt'])
        p,b = physics_run(mod,c,c['dt'],True)
        fine,ff = physics_run(mod,c,c['dt']/2)
        error = max(abs(x-y) for aa,bb in zip(a,b) for x,y in zip(aa['state'],bb['state']))
        convergence = max(abs(x-y) for aa,bb in zip(a,ff[1::2]) for x,y in zip(aa['state'],bb['state']))
        norm = max(abs(sum(x*x for x in aa['state'][6:10])-1) for aa in a)
        assert error <= c['expected']['nativePythonMaxAbs']
        assert convergence <= c['expected']['dtHalfMaxAbs']
        assert norm <= c['expected']['quaternionNormError']
        assert max(abs(v) for v in m.y[10:]) > .01
        h = header(m.p,{'kind':'NO_CONTACT_REFERENCE_FREE_FLIGHT'})
        trace = seal(h,[sample(aa['sensor']['timestamp'],aa['state'][:3],aa['state'][6:10],aa['state'][3:6]) for aa in a])
        replay(trace,trace['head'],h)
        save(c['id']+'.json',{'case':c,'trace':trace,'inputs':[v['pwm'] for v in a]})
        traces.append({'id':c['id'],'head':trace['head'],'header':h,'file':c['id']+'.json'})
        rows.append({'id':c['id'],'pass':True,'frames':len(a),'nativePythonMaxAbs':error,
                     'dtHalfMaxAbs':convergence,'normError':norm,'scope':'REFERENCE_OPEN_LOOP_NOT_AP_OR_HERA'})
    for c in rotation_cases():
        q = [1.,0.,0.,0.]; R = [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]; error = 0.
        for _ in range(c['steps']):
            q = advance(q,c['rates'],c['dt']); R = oracle.matmul(R,oracle.rodrigues(c['rates'],c['dt']))
            error = max(error,max(abs(x-y) for x,y in zip(forward(q),[row[0] for row in R])))
        assert error < 1e-12
        assert max(abs(x-y) for x,y in zip(forward(q),forward([-v for v in q]))) < 1e-12
        rows.append({'id':c['id'],'pass':True,'rotationMatrixMaxAbs':error})
    for c in collision_cases():
        actual = contact(c['start'],c['end'],c['radius'],c['shape'])
        second = oracle.first_contact(c['start'],c['end'],c['radius'],c['shape'])
        expected = c['expectedFraction']
        assert (actual is None)==(expected is None)==(second is None)
        if expected is not None:
            assert abs(actual-expected)<1e-10 and abs(actual-second)<1e-7
        rows.append({'id':c['id'],'pass':True,'firstContact':actual,'scope':'DETECTION_ONLY'})
    rng = random.Random(75)
    for i in range(100):
        start = [rng.uniform(-5,5) for _ in range(3)]; end = [rng.uniform(-5,5) for _ in range(3)]
        shape = {'kind':'sphere','center':[rng.uniform(-1,1) for _ in range(3)],'radius':rng.uniform(.1,2)}
        radius = rng.uniform(.1,1)
        actual = contact(start,end,radius,shape); second = oracle.first_contact(start,end,radius,shape)
        assert (actual is None)==(second is None)
        if actual is not None:
            assert abs(actual-second)<1e-7
    rows.append({'id':'COL-seeded-oracle100','pass':True,'comparisons':100,'seed':75})
    for c in avoidance_cases():
        result = speed_envelope(c['requested'],sensor()|c['sensorPatch'],context()|c['contextPatch'],policy_fixture())
        assert result['status']==c['expected'] and result['executed'] is False
        if 'speed' in c:
            assert abs(result['radialSpeedMps']-c['speed'])<1e-12
        rows.append({'id':c['id'],'pass':True,'result':result})
    # Constant push against wall: this is a kinematic mock, no AP/physics execution.
    policy = policy_fixture(); x = 0.; minimum = 100.; motion = []
    wall = {'kind':'plane','normal':[-1.,0.,0.],'offset':-10.}
    for i in range(300):
        clearance = 10-x-.3; t = (i+1)*policy['dt']
        response = speed_envelope(4.,sensor()|{'t':t,'clearanceM':clearance},context()|{'now':t},policy)
        newx = x+response['radialSpeedMps']*policy['dt']
        assert contact([x,0,-5],[newx,0,-5],.3,wall) is None
        x = newx; minimum = min(minimum,10-x-.3)
        motion.append(sample(t,[x,0,-5],[1,0,0,0],[response['radialSpeedMps'],0,0]))
    assert minimum >= policy['marginM']-1e-10 and motion[-1]['velocity'][0] < 1e-6
    h = header(policy,wall); trace = seal(h,motion); replay(trace,trace['head'],h)
    save('AV-constant-push.json',{'policy':policy,'trace':trace,'scope':'KINEMATIC_MOCK_NOT_AP'})
    traces.append({'id':'AV-constant-push','file':'AV-constant-push.json','head':trace['head'],'header':h})
    rows.append({'id':'AV-constant-push','pass':True,'minimumClearanceM':minimum,'frames':len(motion),'finalSpeedMps':motion[-1]['velocity'][0]})
    # Integrity adversaries: externally pinned expected header/head remain unchanged.
    base = trace
    negatives = {}
    negatives['missing-frame'] = lambda t:t['rows'].pop(10)
    negatives['duplicate-frame'] = lambda t:t['rows'].insert(10,copy.deepcopy(t['rows'][10]))
    negatives['reorder'] = lambda t:t['rows'].reverse()
    negatives['tamper'] = lambda t:t['rows'][0]['sample']['position'].__setitem__(0,1.)
    negatives['wrong-header'] = lambda t:t['header'].__setitem__('boot','old-boot')
    for name,mutate in negatives.items():
        bad = copy.deepcopy(base); mutate(bad)
        try:
            replay(bad,base['head'],h)
        except (ValueError,KeyError):
            rows.append({'id':'REPLAY-'+name,'pass':True,'rejected':True})
        else:
            raise AssertionError(name)
    # Re-sealed attacks are internally consistent; only the external digest protects them.
    for name in ['wrong-identity','clock-regression','bad-quaternion','ack-only','re-sealed-position','truncated-prefix','nonfinite']:
        samples = [copy.deepcopy(r['sample']) for r in base['rows']]
        if name=='wrong-identity':samples[1]['target']='99/1'
        elif name=='clock-regression':samples[1]['t']=samples[0]['t']
        elif name=='bad-quaternion':samples[1]['quaternion']=[0,0,0,0]
        elif name=='ack-only':samples[1]['kind']='COMMAND_ACK'
        elif name=='re-sealed-position':samples[1]['position'][0]=123.
        elif name=='truncated-prefix':samples=samples[:20]
        else:samples[1]['velocity'][0]=float('nan')
        try:
            bad = seal(h,samples); replay(bad,base['head'],h)
        except (ValueError,KeyError):
            rows.append({'id':'REPLAY-'+name,'pass':True,'rejected':True})
        else:
            raise AssertionError(name)
    # Deliberate wrong algorithm outputs must disagree with declared independent references.
    angle = .6
    qp = [math.cos(angle/2),0,math.sin(angle/2),0]; qy = [math.cos(angle/2),0,0,math.sin(angle/2)]
    from engine import multiply
    expected = forward(multiply(qp,qy)); wrong = forward(multiply(qy,qp))
    assert max(abs(a-b) for a,b in zip(expected,wrong)) > .05
    assert forward([0,0,0,1])[0] == -1 # nose-in geometry, not an input inversion feature
    tunnel = collision_cases()[7]
    assert contact(tunnel['start'],tunnel['start'],tunnel['radius'],tunnel['shape']) is None
    assert contact(tunnel['end'],tunnel['end'],tunnel['radius'],tunnel['shape']) is None
    assert contact(tunnel['start'],tunnel['end'],tunnel['radius'],tunnel['shape']) is not None
    rows.append({'id':'BITES-wrong-order-and-endpoint-only','pass':True,'wrongOutputsDetected':2})
    save('corpus-index.json',{'cases':physics_cases()+rotation_cases()+collision_cases()+avoidance_cases(),'traces':traces})
    save('results.json',{'status':'PASS_MOCK_SCOPE','passed':len(rows),'total':len(rows),'rows':rows,
                         'physicsFrames':sum(r.get('frames',0) for r in rows if r['id'].startswith('PY-')),
                         'realFlightCommands':0,'actualImages':0,'heraValidated':False,'autopilotExecuted':False,
                         'notChecked':['SITL pitch/yaw/avoidance/contact','Hera calibration','stable1x pacing','HID device','impact response','full terrain mesh','renderer/audio']})
    print(json.dumps({'passed':len(rows),'total':len(rows),'physicsFrames':sum(r.get('frames',0) for r in rows if r['id'].startswith('PY-')),'status':'PASS_MOCK_SCOPE'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out',required=True); a = p.parse_args()
    OUT = pathlib.Path(a.out).resolve()
    if not OUT.is_relative_to(ROOT/'evidence/simfeedback75'):
        raise RuntimeError('OUTPUT_SCOPE')
    if shutil.disk_usage(ROOT).free < FLOOR+32*1024**2:
        raise RuntimeError('DISK_FLOOR')
    OUT.mkdir(parents=True,exist_ok=False)
    start = time.monotonic()
    try:
        run()
    except BaseException as e:
        save('failure.json',{'error':type(e).__name__,'message':str(e),'elapsedS':time.monotonic()-start})
        raise
