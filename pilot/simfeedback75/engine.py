"""Offline synthetic policies and analytic contacts. No autopilot or transport."""
import hashlib
import json
import math


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def number(x):
    if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x):
        raise ValueError('FINITE_NUMBER_REQUIRED')
    return x


def vector(x, length=3):
    if not isinstance(x, list) or len(x) != length:
        raise ValueError('VECTOR_SIZE')
    return [number(v) for v in x]


def quaternion(q):
    q = vector(q, 4)
    if abs(sum(v*v for v in q) - 1) > 1e-9:
        raise ValueError('UNIT_QUATERNION_REQUIRED')
    return q


def forward(q):
    w, x, y, z = quaternion(q)
    return [1-2*(y*y+z*z), 2*(x*y+w*z), 2*(x*z-w*y)]


def multiply(a, b):
    w,x,y,z = a; v,i,j,k = b
    return [w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j, w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v]


def advance(q, body_rate, dt):
    """Exact constant body-rate quaternion increment; not attitude control."""
    q = quaternion(q); rate = vector(body_rate); dt = number(dt)
    if not 0 < dt <= .1:
        raise ValueError('DT_DOMAIN')
    n = math.sqrt(sum(v*v for v in rate))
    delta = [1,0,0,0] if n == 0 else [math.cos(n*dt/2), *[v/n*math.sin(n*dt/2) for v in rate]]
    return quaternion(multiply(q, delta))


def speed_envelope(requested, sample, context, policy):
    """Mock radial approach limit only; UNAVAILABLE never means aircraft stopped."""
    for key in ['target', 'session', 'boot', 'frame', 'clock']:
        if sample.get(key) != context.get(key):
            return {'status':'UNAVAILABLE', 'reason':'IDENTITY_'+key.upper(), 'executed':False}
    now = number(context['now']); t = number(sample['t']); ttl = number(policy['ttl'])
    if now < t or now-t > ttl:
        return {'status':'UNAVAILABLE', 'reason':'SENSOR_AGE', 'executed':False}
    if context.get('mode') not in policy['modes'] or sample.get('healthy') is not True:
        return {'status':'UNAVAILABLE', 'reason':'MODE_OR_SENSOR', 'executed':False}
    requested = number(requested); distance = number(sample['clearanceM'])
    margin = number(policy['marginM']); a = number(policy['decelerationMps2']); dt = number(policy['dt'])
    if distance < 0 or margin < 0 or a <= 0 or not 0 < dt <= .1 or ttl < 0:
        raise ValueError('POLICY_DOMAIN')
    room = max(0, distance-margin)
    cap = max(0, math.sqrt((a*dt)**2 + 2*a*room)-a*dt)
    return {'status':'MOCK_LIMIT', 'radialSpeedMps':min(requested, cap), 'executed':False}


def contact(start, end, radius, shape):
    """Earliest swept sphere contact fraction [0,1]; None when clear.

    Plane normal points toward free half-space; n·x >= offset+radius.
    Sphere and infinite plane only. No response/resting/friction model.
    """
    p = vector(start); e = vector(end); radius = number(radius)
    if radius <= 0:
        raise ValueError('RADIUS_DOMAIN')
    d = [b-a for a,b in zip(p,e)]
    if shape['kind'] == 'plane':
        n = vector(shape['normal']); offset = number(shape['offset'])
        if abs(sum(v*v for v in n)-1) > 1e-9:
            raise ValueError('UNIT_NORMAL_REQUIRED')
        a = sum(x*y for x,y in zip(n,p))-offset-radius
        b = sum(x*y for x,y in zip(n,e))-offset-radius
        if a <= 0:
            return 0.0
        return a/(a-b) if b <= 0 else None
    if shape['kind'] == 'sphere':
        c = vector(shape['center']); r = number(shape['radius'])
        if r <= 0:
            raise ValueError('OBSTACLE_RADIUS_DOMAIN')
        m = [x-y for x,y in zip(p,c)]; r += radius
        cc = sum(v*v for v in m)-r*r
        if cc <= 0:
            return 0.0
        aa = sum(v*v for v in d); bb = 2*sum(x*y for x,y in zip(m,d))
        discriminant = bb*bb-4*aa*cc
        if aa == 0 or discriminant < 0:
            return None
        # Stable smaller root, including near-tangent cases.
        root = (-bb-math.sqrt(discriminant))/(2*aa)
        return root if 0 <= root <= 1 else None
    raise ValueError('UNSUPPORTED_SHAPE')


def seal(header, samples):
    head = digest(header); rows = []
    for i, s in enumerate(samples):
        body = {'seq':i, 'previous':head, 'sample':s}
        head = digest(body); rows.append({**body, 'sha256':head})
    return {'header':header, 'rows':rows, 'head':head, 'count':len(rows)}


def replay(trace, expected_head, expected_header):
    header = trace['header']
    if header != expected_header or header['assurance'] != 'MOCK_ONLY' or type(header.get('version')) is not int or header['version'] != 1:
        raise ValueError('HEADER_OR_ASSURANCE')
    if header['units'] != 'SI' or header['world'] != 'NED' or header['body'] != 'FRD' or header['datum'] != 'VIRTUAL_HOME_NED_METRES' or header['clock'] != 'MOCK_MONOTONIC_S':
        raise ValueError('FRAME_OR_DATUM')
    for key in ['profileSha256','modelSha256','sceneSha256']:
        if not isinstance(header[key], str) or len(header[key]) != 64 or any(c not in '0123456789abcdef' for c in header[key]):
            raise ValueError('PIN_REQUIRED')
    for key in ['target','session','boot']:
        if not isinstance(header.get(key), str) or not header[key] or len(header[key]) > 128:
            raise ValueError('IDENTITY_REQUIRED')
    if type(trace['count']) is not int or not 0 < trace['count'] <= 10000 or len(trace['rows']) != trace['count']:
        raise ValueError('ROW_COUNT')
    head = digest(header); last = -1
    for i, row in enumerate(trace['rows']):
        body = {k:row[k] for k in ['seq','previous','sample']}
        if type(row['seq']) is not int or row['seq'] != i or row['previous'] != head or digest(body) != row['sha256']:
            raise ValueError('CHAIN')
        s = row['sample']; t = number(s['t'])
        if t < 0 or t <= last:
            raise ValueError('CLOCK')
        last = t
        for key in ['target','session','boot']:
            if s.get(key) != header[key]:
                raise ValueError('ROW_IDENTITY')
        vector(s['position']); vector(s['velocity']); quaternion(s['quaternion'])
        if s.get('kind') != 'MODEL_STATE':
            raise ValueError('ACK_NOT_MODEL_STATE')
        head = row['sha256']
    if head != trace['head'] or head != expected_head:
        raise ValueError('EXPECTED_DIGEST')
    return {'status':'PASS_MOCK_INTEGRITY_ONLY', 'frames':len(trace['rows']), 'executed':False, 'heraValidated':False}
