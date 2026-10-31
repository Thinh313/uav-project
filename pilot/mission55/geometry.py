"""Pinned GeographicLib reference metrics. Not the frozen application's engine."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea
from semantic import load_plan,require,number

def metrics(raw):
    p=load_plan(raw);m=p['header']['mission'];nav=[];surveys=[]
    for seq,i in enumerate(p['executable']):
        if i['command'] not in [16,21,22]:continue
        v=i['params'];frame=i['frame']
        height=v[6]+m['plannedHomePosition'][2] if frame in [3,6] else v[6] if frame in [0,5] else None
        nav.append({'flatIndex':seq,'command':i['command'],'coordinate':v[4:6],'commandAltitudeM':v[6],
                    'frame':frame,'impliedAmslM':height,'heightReference':'file-planned-Home model only; observed Home/geoid NOT_CHECKED'})
    for i in p['plan']['mission']['items']:
        if i['type']!='ComplexItem':continue
        polygon=PolygonArea(Geodesic.WGS84,False)
        for point in i['polygon']:polygon.AddPoint(*point)
        n,perimeter,area=polygon.Compute(False,True)
        surveys.append({'geodesicAreaM2':abs(area),'signedGeodesicAreaM2':area,'perimeterM':perimeter,'points':n,
                         'metric':'ellipsoidal WGS84 PolygonArea reference; not DEM surface or measured coverage',
                         'simplePolygonValidity':'NOT_CHECKED; self-intersection/hole semantics require separate validator'})
    length=sum(Geodesic.WGS84.Inverse(*a['coordinate'],*b['coordinate'])['s12'] for a,b in zip(nav,nav[1:]))
    return {'nav':nav,'surveys':surveys,'navPolylineLengthM':length,'sourceSha256':p['rawSha256'],
            'method':'GeographicLib2.1-WGS84','flightReady':False,'regeneratedTransects':False}

def compare_geometry(before,after):
    a=metrics(before);b=metrics(after);aligned=[]
    for x,y in zip(a['nav'],b['nav']):
        distance=Geodesic.WGS84.Inverse(*x['coordinate'],*y['coordinate'])['s12']
        aligned.append({'beforeFlatIndex':x['flatIndex'],'afterFlatIndex':y['flatIndex'],
                         'horizontalDeltaM':distance,'commandChanged':x['command']!=y['command'],
                         'frameChanged':x['frame']!=y['frame'],
                         'impliedAmslDeltaM':None if x['impliedAmslM'] is None or y['impliedAmslM'] is None else y['impliedAmslM']-x['impliedAmslM']})
    return {'before':a,'after':b,'alignedNavByOrdinal':aligned,'navCountChanged':len(a['nav'])!=len(b['nav']),
            'scope':'Ordinal diagnostic only, not route-matching/regeneration or field accuracy acceptance','flightReady':False}

UNITS={'m2':('area',1),'ha':('area',10000),'km2':('area',1000000),'m':('length',1),'ft':('length',0.3048),'s':('time',1),'count':('count',1)}
def compare_measurement(expected,observed,absolute_tolerance):
    require(number(absolute_tolerance) and absolute_tolerance>=0,'TOLERANCE')
    require(expected.get('unit') in UNITS and observed.get('unit') in UNITS,'UNIT_UNKNOWN')
    a,sa=UNITS[expected['unit']];b,sb=UNITS[observed['unit']]
    require(a==b,'UNIT_DIMENSION')
    require(expected.get('metric')==observed.get('metric') and isinstance(expected.get('metric'),str),'METRIC_MISMATCH')
    if expected.get('value') is None or observed.get('value') is None:
        return {'verdict':'NOT_CHECKED','reason':'Unknown value is never numeric zero','pass':False}
    require(number(expected['value']) and number(observed['value']),'MEASUREMENT_TYPE')
    if a=='count':require(int(expected['value'])==expected['value'] and int(observed['value'])==observed['value'] and expected['value']>=0 and observed['value']>=0 and absolute_tolerance==0,'COUNT_EXACT')
    error=observed['value']*sb-expected['value']*sa
    return {'verdict':'MATCH' if abs(error)<=absolute_tolerance else 'DIFFERENT','pass':abs(error)<=absolute_tolerance,
            'errorCanonicalUnits':error,'absoluteToleranceCanonicalUnits':absolute_tolerance,
            'conversion':{'expectedScale':sa,'observedScale':sb},'metric':expected['metric']}
