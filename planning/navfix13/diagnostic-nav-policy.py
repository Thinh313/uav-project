"""Bounded, read-only diagnosis. Never grants authority or substitutes preflight."""
import math
CONTEXT_KEYS=('run','epoch','boot')
CLOCK_DOMAIN='PYTHON_ROOT_MONOTONIC_NS'
TELEMETRY_FRESH_NS=1_500_000_000
MAX_SAMPLES_PER_KIND=512
EKF_REQUIRED_MASK=55

def _integer(v):return type(v)is int

def _coord(v):
 return (type(v)is dict and all(_integer(v.get(k))for k in('latitudeE7','longitudeE7','altitudeMSLmm')) and abs(v['latitudeE7'])<=900_000_000 and abs(v['longitudeE7'])<=1_800_000_000 and -1_000_000<=v['altitudeMSLmm']<=100_000_000)

def _distance(a,b):
 # Great-circle distance handles antimeridian and zero/zero without sentinels.
 p,q=math.radians(a['latitudeE7']/1e7),math.radians(b['latitudeE7']/1e7)
 dl=math.radians((b['longitudeE7']-a['longitudeE7'])/1e7)
 h=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin(dl/2)**2
 return 6_371_008.8*2*math.asin(min(1.,math.sqrt(max(0.,h))))

def diagnose(snapshot,expected_context,now_host_ns):
 """Input is an original-raw-derived bounded cohort, host timestamps in one domain.

 Result is diagnostic only, including the all-observed-good case. The original
 authority/freshness/preflight gates remain the only control decision makers.
 No wallclock conversion, timer extension, GPS rewrite or command is performed.
 """
 def result(codes,facts=None):
  return {'format':'aeris-nav-diagnostic13','version':1,'codes':codes,'facts':facts or{},'scope':'READ_ONLY_DIAGNOSIS_NOT_NAVIGATION_OR_AUTHORITY_ACCEPTANCE','authorityGranted':False,'originalGateOverride':False,'internalEKFRootCause':'UNOBSERVED','hypotheses':[]}
 if not (_integer(now_host_ns)and now_host_ns>=0 and type(expected_context)is dict and set(expected_context)==set(CONTEXT_KEYS)and all(type(expected_context[k])is str and 0<len(expected_context[k])<=128 for k in CONTEXT_KEYS)):
  return result(['INVALID_EXPECTED_CONTEXT_OR_HOST_CLOCK'])
 if type(snapshot)is not dict or snapshot.get('context')!=expected_context:return result(['FOREIGN_OR_MISSING_CONTEXT'])
 if snapshot.get('clockDomain')!=CLOCK_DOMAIN:return result(['UNQUALIFIED_CLOCK_DOMAIN'])
 groups=snapshot.get('observations')
 if type(groups)is not dict or set(groups)-{'gps','home','ekf','boot'}:return result(['OBSERVATION_SCHEMA'])
 codes=[];facts={};latest={}
 for kind in('gps','home','ekf','boot'):
  rows=groups.get(kind,[])
  if type(rows)is not list or len(rows)>MAX_SAMPLES_PER_KIND:return result(['OBSERVATION_BOUND_OR_SCHEMA'])
  if not rows:codes.append(kind.upper()+'_ABSENT');continue
  prior=-1
  for row in rows:
   if type(row)is not dict or row.get('context')!=expected_context:return result(['FOREIGN_OBSERVATION_CONTEXT'])
   if row.get('system')!=42 or row.get('component')!=1 or type(row.get('system'))is not int or type(row.get('component'))is not int:return result(['FOREIGN_OBSERVATION_TARGET'])
   t=row.get('hostNs')
   if not _integer(t)or not 0<=t<=now_host_ns:return result(['INVALID_OR_FUTURE_HOST_TIME'])
   if t<prior:return result(['HOST_ARRIVAL_ROLLBACK'])
   prior=t
  latest[kind]=rows[-1];age=now_host_ns-rows[-1]['hostNs'];facts[kind+'AgeNs']=age
  if age>TELEMETRY_FRESH_NS:codes.append(kind.upper()+'_STALE_1500MS')
 if 'gps'in latest:
  gps=latest['gps']
  if not _coord(gps):codes.append('GPS_COORDINATE_OR_MSL_UNIT_DOMAIN')
  if not _integer(gps.get('fixType'))or gps['fixType']not in(3,4,5,6,8):codes.append('GPS_FIX_NOT_3D')
  if not _integer(gps.get('satellites'))or not 6<=gps['satellites']<=254:codes.append('GPS_SATELLITE_QUALITY_UNQUALIFIED')
  if not _integer(gps.get('HDOPx100'))or not 0<=gps['HDOPx100']<=200:codes.append('GPS_HDOP_UNQUALIFIED_OR_ABOVE_200')
  facts['GPSFixType']=gps.get('fixType');facts['GPSSatellites']=gps.get('satellites');facts['GPSHDOPx100']=gps.get('HDOPx100')
 if 'home'in latest and not _coord(latest['home']):codes.append('HOME_COORDINATE_OR_MSL_UNIT_DOMAIN')
 expected_home=snapshot.get('expectedHome')
 if expected_home is not None:
  if not _coord(expected_home):return result(['INVALID_DECLARED_HOME'])
  if 'home'in latest and _coord(latest['home']):
   offset=_distance(expected_home,latest['home']);alt=abs(expected_home['altitudeMSLmm']-latest['home']['altitudeMSLmm'])
   facts.update(homeHorizontalOffsetM=offset,homeMSLAltitudeDifferenceMm=alt,diagnosticHomeToleranceM=5.,diagnosticHomeAltitudeToleranceMm=5000)
   if offset>5. or alt>5000:codes.append('HOME_DIFFERS_FROM_DECLARED_SIM_ORIGIN')
 boots=groups.get('boot',[])
 if boots:
  if any(not _integer(x.get('APTimeBootMs'))or not 0<=x['APTimeBootMs']<2**32 for x in boots):codes.append('INVALID_AP_BOOT_TIME')
  else:
   facts['APObservedElapsedMs']=boots[-1]['APTimeBootMs']-boots[0]['APTimeBootMs']
   if any(a['APTimeBootMs']>b['APTimeBootMs']for a,b in zip(boots,boots[1:])):codes.append('AP_BOOT_ROLLBACK_OR_WRAP_NEW_EPOCH_REQUIRED')
 if 'ekf'in latest:
  flags=latest['ekf'].get('ekfFlags')
  if not _integer(flags)or not 0<=flags<=65535:codes.append('INVALID_EKF_FLAGS')
  else:
   facts.update(EKFFlags=flags,absoluteHorizontalPosition=bool(flags&16),constantPositionMode=bool(flags&128),originalEKFRequiredMask=EKF_REQUIRED_MASK)
   if flags&~0x037f:codes.append('EKF_FLAGS_OUTSIDE_ORIGINAL_ALLOWED_MASK')
   if flags&EKF_REQUIRED_MASK!=EKF_REQUIRED_MASK:codes.append('EKF_REQUIRED_NAVIGATION_FLAGS_MISSING')
   if flags&128:codes.append('EKF_CONSTANT_POSITION_MODE')
 if not codes:codes=['OBSERVED_PREREQUISITES_PRESENT_ORIGINAL_GATES_STILL_REQUIRED']
 out=result(codes,facts)
 if 'gps'in latest and latest['gps'].get('fixType')==6 and 'home'in latest and facts.get('EKFFlags')==167:
  out['hypotheses']=[{'id':'GYRO_BIAS_COVARIANCE_OR_DELAYED_GPS_FUSION_GATE','status':'UNPROVEN_REQUIRES_INTERNAL_STATE_OR_MEASURED_TRANSITION','gpsPresenceNotGPSFusion':True}]
 return out
