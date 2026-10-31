"""Second mathematical path; no dependency on engine or native model.

This is computational checking by the same author, not a Hera dynamics oracle.
"""
import math


def matmul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rodrigues(rate, dt):
    length = math.sqrt(sum(x*x for x in rate))
    if length == 0:
        return [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
    x,y,z = [v/length for v in rate]; c = math.cos(length*dt); s = math.sin(length*dt); t = 1-c
    return [[c+x*x*t,x*y*t-z*s,x*z*t+y*s],
            [y*x*t+z*s,c+y*y*t,y*z*t-x*s],
            [z*x*t-y*s,z*y*t+x*s,c+z*z*t]]


def first_contact(start, end, radius, shape):
    """Closest-distance + bisection, avoiding the production quadratic root."""
    delta = [b-a for a,b in zip(start,end)]
    if shape['kind'] == 'plane':
        def gap(t):
            return sum(n*(a+t*d) for n,a,d in zip(shape['normal'],start,delta))-shape['offset']-radius
        stop = 1.
    else:
        m = [a-c for a,c in zip(start,shape['center'])]
        speed2 = sum(d*d for d in delta)
        stop = max(0.,min(1.,-sum(a*d for a,d in zip(m,delta))/speed2)) if speed2 else 0.
        def gap(t):
            return math.sqrt(sum((a+t*d)**2 for a,d in zip(m,delta)))-radius-shape['radius']
    if gap(0) <= 0:
        return 0.
    if gap(stop) > 1e-12:
        return None
    if abs(gap(stop)) < 1e-12:
        return stop
    lo,hi = 0.,stop
    for _ in range(70):
        mid = (lo+hi)/2
        if gap(mid) > 0:
            lo = mid
        else:
            hi = mid
    return hi
