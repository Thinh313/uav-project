from pathlib import Path
import copy,datetime,hashlib,json,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));sys.path.insert(0,str(Path(__file__).parent))
source_paths=list((R/'pilot/betaintegrated01/control04').glob('*.py'));before={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths}
from pilot.betaintegrated01.control04.geography import qualify,inverse,DATUM
from pilot.betaintegrated01.control04.oracles import nominal_release_observations
from geo_reference import CASES,short_distance
attempt=sys.argv[1]if len(sys.argv)>1 else'01';out=R/('evidence/betaintegrated01-m1control02/qa/geo'+attempt);out.mkdir();results=[]
CTX=('r','e','b');H={'latE7':108539999,'lonE7':1068070000,'altMSLmm':10000,'datum':DATUM}
def row(t,k,**kw):return dict(run='r',epoch='e',boot='b',hostNs=int(t*1e9),kind=k,**kw)
def pos(t,home=H,**kw):return row(t,'position',bootMs=int(t*1000),latE7=home['latE7'],lonE7=home['lonE7'],altAMSLmm=home['altMSLmm']+3000,relativeMm=3000,**kw)
def fixture(home=H):
 rows=[row(0,'position',bootMs=0,latE7=0,lonE7=0,altAMSLmm=10000,relativeMm=0),row(.9,'gps',fix=6,satellites=12,hdop=100),row(.9,'ekf',flags=55),row(.9,'home',home=copy.deepcopy(home)),row(1,'heartbeat',armed=True,mode=4),row(1.01,'home',home=copy.deepcopy(home)),pos(1.02,home),row(1.5,'heartbeat',armed=True,mode=4),pos(1.5,home),row(2,'gps',fix=6,satellites=12,hdop=100),row(2,'ekf',flags=55),row(2,'home',home=copy.deepcopy(home)),row(2,'heartbeat',armed=True,mode=4),pos(2,home),row(2.1,'heartbeat',armed=False,mode=9)]
 return rows,{'home':copy.deepcopy(home),'referenceObservedHostNs':1010000000}
def run(rows,c):return qualify(rows,*CTX,c)
def require(x,s='assertion'):
 if not x:raise AssertionError(s)
def bad(rows,c):
 try:r=run(rows,c)
 except (ValueError,TypeError,KeyError):return
 require(r['status']=='GEOGRAPHY_NOT_READY','unexpectedPASS:'+json.dumps(r))
def test(name,f):
 try:f();results.append({'id':name,'pass':True})
 except Exception as e:results.append({'id':name,'pass':False,'error':repr(e)})
def positive():
 rows,c=fixture();r=run(rows,c);require(r['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS');require(r['preAuthorityPositionsRetained']==1)
def legitimate():
 h={**H,'latE7':0,'lonE7':0};rows,c=fixture(h);require(run(rows,c)['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS')
def distance_cases():
 for n,(a,b)in CASES.items():
  d,_=inverse({'latE7':a[0],'lonE7':a[1]},{'latE7':b[0],'lonE7':b[1]});require(abs(d-short_distance(a,b))<1e-5,n)
def datum():
 rows,c=fixture()
 for r in rows:
  if r['kind']=='position'and r['hostNs']>1000000000:r['altAMSLmm']+=100000
 bad(rows,c)
def poisoned_prehome():
 rows,c=fixture();rows=[r for r in rows if not(r['kind']=='home'and r['hostNs']>=1000000000)];rows[3]['home']={**H,'datum':'UNKNOWN'};rows.insert(-2,row(1.9,'home',home=copy.deepcopy(H)));rows.sort(key=lambda r:r['hostNs']);c['referenceObservedHostNs']=1900000000;bad(rows,c)
def midjump():
 rows,c=fixture();rows[8]['latE7']=0;rows[8]['lonE7']=0;bad(rows,c)
def missinggps():
 rows,c=fixture();bad([r for r in rows if r['kind']!='gps'],c)
def missingconfirm():
 rows,c=fixture();bad(rows,None)
def changedhome():
 rows,c=fixture();rows[11]['home']['latE7']+=1;bad(rows,c)
def newerbad():
 rows,c=fixture();rows.insert(8,row(1.5,'gps',fix=0,satellites=0,hdop=65535));bad(rows,c)
def domain():
 for key,value in [('latE7',True),('latE7',900000001),('lonE7',1800000001),('relativeMm',float('nan')),('altAMSLmm','13000')]:
  rows,c=fixture();rows[8][key]=value;bad(rows,c)
def foreignboot():
 for change in ({'epoch':'foreign'},{'boot':'foreign'},{'bootMs':1}):
  rows,c=fixture();rows[8].update(change);bad(rows,c)
def rearm():
 rows,c=fixture();rows.extend([row(2.2,'heartbeat',armed=True,mode=4),pos(2.3)]);bad(rows,c)
def ground():
 rows=[row(0,'heartbeat',armed=False,mode=0),pos(.1)];r=qualify(rows,*CTX,None,ground_only=True);require(r['status']=='GROUND_ONLY_NO_FLIGHT_AUTHORITY'and r['flightAccepted']is False)
def nominalneutral():
 def w(t,channels):return {'kind':'RC_OVERRIDE','hostNs':t,'channels':channels,'forwardPitchHeld':channels[1]<1480 and channels[1]>0}
 commands=[w(1,[1500]*18),w(2,[1500,1450,1500,1500]+[65535]*14),{'kind':'COMMAND_LONG','hostNs':3,'command':176,'params':[1,17,0,0,0,0,0]},w(5,[1500]*4+[65535]*14),w(6,[0]*8+[65534]*10),{'kind':'COMMAND_LONG','hostNs':7,'command':176,'params':[1,9,0,0,0,0,0]}]
 r=nominal_release_observations({'nativeForwardedTimeline':commands,'passiveTimeline':[{'kind':'heartbeat','hostNs':4,'mode':17,'armed':True}]});require(r['status']=='HOST_RELEASE_WIRE_OBSERVATIONS_PASS','preBRAKEneutral misclassified:'+json.dumps(r))
def datum_boundary():
 for delta in (-21,-20,20,21):
  rows,c=fixture()
  for r in rows:
   if r['kind']=='position'and r['hostNs']>1000000000:r['altAMSLmm']+=delta
  if abs(delta)<=20:require(run(rows,c)['status']=='GEOGRAPHY_FULL_ARMED_WINDOW_PASS')
  else:bad(rows,c)
def armed_edge_bad_snapshot():
 for kind in ('gps','ekf','home'):
  rows,c=fixture()
  for r in rows:
   if r['kind']==kind and r['hostNs']==900000000:
    if kind=='gps':r.update(fix=0,satellites=0,hdop=65535)
    elif kind=='ekf':r['flags']=167
    else:r['home']={**H,'datum':'UNKNOWN'}
  if kind=='gps':replacement=row(1.005,'gps',fix=6,satellites=12,hdop=100)
  elif kind=='ekf':replacement=row(1.005,'ekf',flags=55)
  else:replacement=row(1.005,'home',home=copy.deepcopy(H))
  rows.append(replacement);rows.sort(key=lambda r:r['hostNs']);bad(rows,c)
for n,f in [('G01_POSITIVE_STARTUP_RETAINED',positive),('G02_LEGITIMATE_0_0',legitimate),('G03_WGS84_ECEF_DATELINE_POLES',distance_cases),('G04_DATUM_SHIFT_REFUSED',datum),('G05_INVALID_PREARM_HOME_NOT_REUSED',poisoned_prehome),('G06_NO_MIDDLE_JUMP_DELETION',midjump),('G07_MISSING_GPS',missinggps),('G08_MISSING_CONFIRM',missingconfirm),('G09_CHANGED_HOME',changedhome),('G10_NEW_BAD_OVERRIDES_OLD_GOOD',newerbad),('G11_STRICT_TYPES_DOMAINS',domain),('G12_FOREIGN_BOOT_RESET',foreignboot),('G13_REARM_NO_SUBWINDOW',rearm),('G14_GROUND_NO_FLIGHT_AUTHORITY',ground),('G15_PREBRAKE_NORMAL_NEUTRAL_NOT_CLEANUP',nominalneutral)]:test(n,f)
test('G16_PREDECLARED_SYNTHETIC_DATUM_20MM_BOUNDARY',datum_boundary)
test('G17_BAD_ARM_EDGE_CANNOT_BE_HIDDEN_BY_LATER_GOOD_PREPOSITION_FACT',armed_edge_bad_snapshot)
pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths};report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(r['pass']for r in results)and pins==before else'FAIL','results':results,'sourceBefore':before,'sourceAfter':pins,'sourceChanged':pins!=before,'scope':'Independentpurequalifiedrows+WGS84ECEFreference+wirephasefixtures, notactualexecution/confirmationtrusttest','servicesStarts':0};(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'failed':[r['id']for r in results if not r['pass']]}))
