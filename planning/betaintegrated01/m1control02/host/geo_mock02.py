"""Unseen deterministic edge matrix and independent WGS84 ECEF/meridian references."""
from pathlib import Path
import sys,copy,json,math,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control04.geography import qualify,inverse,DATUM
CTX={'run':'mock-r','epoch':'mock-e','boot':'mock-b'}
HOME={'latE7':108540000,'lonE7':1068070000,'altMSLmm':10000,'datum':DATUM}
def row(t,kind,**x):return {**CTX,'hostNs':int(t*1e9),'kind':kind,**x}
def position(t,home=HOME,**x):return row(t,'position',bootMs=int(t*1000),latE7=home['latE7'],lonE7=home['lonE7'],altAMSLmm=10000,relativeMm=0,**x)
def base(home=HOME):
 r=[position(.1,{'latE7':0,'lonE7':0}),row(.8,'home',home=home),row(.81,'gps',fix=6,satellites=10,hdop=121),row(.82,'ekf',flags=831),row(1,'heartbeat',armed=True,mode=4),position(1.1,home)]
 r.extend([row(2,'heartbeat',armed=True,mode=5),row(2.01,'gps',fix=6,satellites=10,hdop=121),row(2.02,'ekf',flags=831),row(2.03,'home',home=home),position(2.1,home),row(2.2,'heartbeat',armed=False,mode=9)])
 return r
def run(rows,home=HOME,confirmation=True):return qualify(rows,**CTX,confirmation={'home':home,'referenceObservedHostNs':1_000_000_000}if confirmation else None)
def rejected(rows,**k):
 try:return run(rows,**k)['status']=='GEOGRAPHY_NOT_READY'
 except(ValueError,KeyError,TypeError):return True

def main():
 cases=[]
 def check(name,ok):assert ok,name;cases.append({'case':name,'status':'PASS'})
 check('startup00_retained_not_origin',run(base())['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS'and run(base())['preAuthorityPositionsRetained']==1)
 zero={**HOME,'latE7':0,'lonE7':0};check('qualified_legitimate00_home',run(base(zero),zero)['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS')
 check('missing_confirmation',rejected(base(),confirmation=False))
 for name,kind in [('missingGPS','gps'),('missingHome','home'),('missingEKF','ekf')]:check(name,rejected([r for r in base()if r['kind']!=kind]))
 for key,val in [('latE7',True),('latE7',900000001),('lonE7',1800000001),('relativeMm',float('nan')),('relativeMm',True),('bootMs',-1),('altAMSLmm',None)]:
  rows=base();rows[5][key]=val;check('schema_'+key+'_'+str(val),rejected(rows))
 rows=base();rows[5].pop('relativeMm');check('missing_position_value',rejected(rows))
 rows=base();rows[5].update(latE7=0,lonE7=0);check('armed00_jump_not_filtered',rejected(rows)and run(rows)['maximumDistanceFromConfirmedHomeM']>1000000)
 rows=base();rows[9]['home']={**HOME,'latE7':HOME['latE7']+1};check('changed_Home_after_confirmation',rejected(rows))
 rows=base();rows[9]['home']={**HOME,'datum':'AGL'};check('datum_mismatch',rejected(rows))
 rows=base();rows[5]['epoch']='foreign';check('foreign_context',rejected(rows))
 rows=base();rows[5]['hostNs']=1;check('reordered_host',rejected(rows))
 rows=base();rows[10]['bootMs']=10;check('boot_reset',rejected(rows))
 rows=base();rows[2]['hostNs']=0;rows[5]['hostNs']=1_600_000_000;rows.sort(key=lambda r:r['hostNs']);check('stale_GPS_before_first_armedposition',rejected(rows))
 rows=base();rows.insert(-1,row(2.15,'ekf',flags=167));check('new_bad_EKF_overrides_oldgood_without_future_position',rejected(rows))
 rows=base();rows.insert(-1,row(2.15,'invalid',reason='FOREIGN_AP_SOURCE'));check('foreign_AP_in_full_armed_window',rejected(rows))
 rows=base();rows[-1]['armed']=True;check('no_terminal_disarm',rejected(rows))
 rows=base();rows.append(row(2.3,'heartbeat',armed=True,mode=4));check('afterwindow_rearm_requires_new_confirmation',rejected(rows))
 rows=base();rows[5]['relativeMm']=5001;check('full_window_alt5m_no_outlier_drop',rejected(rows))
 ground=[row(0,'heartbeat',armed=False,mode=0),position(.1),row(.2,'heartbeat',armed=False,mode=0)]
 check('ground_only_no_postARM_requirement_no_flightpass',qualify(ground,**CTX,confirmation=None,ground_only=True)['status']=='GROUND_ONLY_NO_FLIGHT_AUTHORITY')
 # Independent WGS84 ECEF chord is within <1um of surface arc for these <=12m vectors.
 def ecef(lat,lon):
  lat,lon=math.radians(lat),math.radians(lon);a=6378137.;e2=(1/298.257223563)*(2-1/298.257223563);n=a/math.sqrt(1-e2*math.sin(lat)**2)
  return(n*math.cos(lat)*math.cos(lon),n*math.cos(lat)*math.sin(lon),n*(1-e2)*math.sin(lat))
 vectors=[(0,179.99999,0,-179.99999),(89.99999,179,89.99999,-179),(90,0,90,180),(-90,-180,-89.99999,180),(10.854,106.807,10.85401,106.80701)]
 for i,(a,b,c,d)in enumerate(vectors):
  one={'latE7':round(a*1e7),'lonE7':round(b*1e7)};two={'latE7':round(c*1e7),'lonE7':round(d*1e7)}
  dist,_=inverse(one,two);chord=math.dist(ecef(a,b),ecef(c,d));check('independent_ECEF_dateline_pole_'+str(i),abs(dist-chord)<1e-6)
 # Independent Simpson integration of meridian radius over 0..1degree.
 f=1/298.257223563;e2=f*(2-f);step=math.pi/180/10000
 def radius(x):return 6378137.*(1-e2)/(1-e2*math.sin(x)**2)**1.5
 ref=step/3*(radius(0)+radius(step*10000)+sum((4 if i%2 else 2)*radius(i*step)for i in range(1,10000)))
 check('independent_meridian_Simpson_1degree',abs(inverse({'latE7':0,'lonE7':0},{'latE7':10000000,'lonE7':0})[0]-ref)<1e-6)
 out=R/'evidence/betaintegrated01-m1control02/host/geo-mock02';out.mkdir()
 result={'status':'PASS_BUILDER_GEOGRAPHY_MOCK','groups':len(cases),'cases':cases,'reference':'Independent WGS84 ECEF chords for shortvectors <=12m (arc/chord difference <1um); Simpson10000 meridian integration for1deg (<1um numerical tolerance), not same-library expected outputs','APStarts':0,'AndroidStarts':0,'realSocketsCreated':0,'native00Support':'DEFERRED_PRODUCT_GAP_ORACLE_ONLY_SUPPORTED'}
 (out/'results.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'groups':len(cases)}))
if __name__=='__main__':main()
