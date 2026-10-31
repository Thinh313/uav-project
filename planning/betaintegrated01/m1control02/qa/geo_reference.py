"""Independent WGS84 ECEF geometry for short (<20m) oracle comparisons.

Surface geodesic vs ECEF chord differs negligibly at the 10m envelope scale;
this is independent of vendored GeographicLib and longitude-difference formulas.
It is not a general long-distance replacement for ellipsoidal geodesics.
"""
import math
A=6378137.0
F=1/298.257223563
E2=F*(2-F)

def point(lat_e7,lon_e7):
    if type(lat_e7)is not int or type(lon_e7)is not int or not -900000000<=lat_e7<=900000000 or not -1800000000<=lon_e7<=1800000000:
        raise ValueError('QA_REFERENCE_E7_DOMAIN')
    lat,lon=map(math.radians,(lat_e7/1e7,lon_e7/1e7));n=A/math.sqrt(1-E2*math.sin(lat)**2)
    return(n*math.cos(lat)*math.cos(lon),n*math.cos(lat)*math.sin(lon),n*(1-E2)*math.sin(lat))

def short_distance(a,b):
    p,q=point(*a),point(*b)
    return math.sqrt(sum((x-y)**2 for x,y in zip(p,q)))

CASES={
    'legitimate_origin':((0,0),(0,0)),
    'equator_east':((0,0),(0,500)),
    'equator_north':((0,0),(500,0)),
    'dateline_short':((0,1799999900),(0,-1799999900)),
    'high_latitude':((899999000,1799990000),(899999000,-1799990000)),
    'north_pole_same_point':((900000000,0),(900000000,1800000000)),
    'south_pole_same_point':((-900000000,-1800000000),(-900000000,0)),
    'Vietnam_profile':((108539999,1068070000),(108540559,1068069999)),
}
