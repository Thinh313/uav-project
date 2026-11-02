"""WGS84 full armed-window checks. Raw startup coordinates are retained, not origins."""
from pathlib import Path
import sys,math,struct
from pilot.betaintegrated01.control01.mavlink import Framer
from aeris_runtime.audit.control import events
# Exact existing vendored GeographicLib2.1, MIT; no dependency installation.
from aeris_runtime.paths import repository
sys.path.insert(0,str(repository()/'pilot/mission55/vendor'))
from geographiclib.geodesic import Geodesic
DATUM='AP_HOME_MSL_IN_SYNTHETIC_EXTERNAL_PROFILE'
POLICY={'horizontalLimitM':10.,'relativeAltitudeLimitMm':5000,'positionFreshNs':1_500_000_000,
        'heartbeatFreshNs':1_500_000_000,'GPSFreshNs':1_500_000_000,'EKFFreshNs':1_500_000_000,
        'HomeFreshNs':3_000_000_000,'hostConfirmationPhaseToleranceNs':1_500_000_000,
        'maximumConfirmationBracketNs':5_000_000_000,'maxRows':16000,'syntheticAPDatumToleranceMm':20,
        'geodesic':'GeographicLib2.1 WGS84 a6378137 f1/298.257223563; double precision; E7 quantization retained'}


def integer(x,lo,hi,name):
    if type(x)is not int or not lo<=x<=hi:raise ValueError('INVALID_'+name)
    return x


def home_fields(h):
    if type(h)is not dict or set(h)!={'latE7','lonE7','altMSLmm','datum'}:raise ValueError('HOME_SCHEMA')
    integer(h['latE7'],-900000000,900000000,'HOME_LAT_E7');integer(h['lonE7'],-1800000000,1800000000,'HOME_LON_E7')
    integer(h['altMSLmm'],-10000000,10000000,'HOME_MSL_MM')
    if h['datum']!=DATUM:raise ValueError('HOME_DATUM')
    return h


def inverse(a,b):
    for p in(a,b):
        integer(p['latE7'],-900000000,900000000,'LAT_E7');integer(p['lonE7'],-1800000000,1800000000,'LON_E7')
    result=Geodesic.WGS84.Inverse(a['latE7']/1e7,a['lonE7']/1e7,b['latE7']/1e7,b['lonE7']/1e7)
    if not all(math.isfinite(result[k])for k in('s12','azi1')):raise ValueError('NONFINITE_GEODESIC')
    return result['s12'],result['azi1']


def collect(out,run,epoch,boot):
    """Additional CRC reconstruction, including bad/foreign/reordered observations."""
    framer=Framer();rows=[];seq=None;last_host=-1;last_boot=None
    for kind,data in events(Path(out)/'transport-journal'):
        if data.get('_boot')!=boot:raise ValueError('FOREIGN_TRANSPORT_BOOT')
        now=data.get('_observedHostNs');integer(now,0,2**63-1,'TRANSPORT_CLOCK')
        if now<last_host:raise ValueError('TRANSPORT_CLOCK_REORDER')
        last_host=now
        if kind!='PASSIVE_RX':continue
        for frame in framer.feed(bytes.fromhex(data['rawHex']),data['hostNs']):
            row={'run':run,'epoch':epoch,'boot':boot,'hostNs':frame['monotonicNs'],'wireSHA256':__import__('hashlib').sha256(bytes.fromhex(frame['wireHex'])).hexdigest()}
            if frame['system']!=42 or frame['component']!=1:row.update(kind='invalid',reason='FOREIGN_AP_SOURCE')
            else:
                delta=None if seq is None else(frame['wireSequence']-seq)&255
                if delta==0 or delta is not None and delta>=128:
                    row.update(kind='invalid',reason='AP_DUPLICATE_OR_REORDER')
                else:
                    seq=frame['wireSequence'];p=frame['payload'];ident=frame['id'];row['wireSequence']=seq
                    if ident==0:row.update(kind='heartbeat',mode=struct.unpack_from('<I',p)[0],armed=bool(p[6]&128))
                    elif ident==33:
                        b,lat,lon,amsl,rel,vx,vy,vz,hdg=struct.unpack_from('<IiiiihhhH',p)
                        row.update(kind='position',bootMs=b,latE7=lat,lonE7=lon,altAMSLmm=amsl,relativeMm=rel,vxCms=vx,vyCms=vy,vzCms=vz,headingCentiDeg=hdg)
                        if last_boot is not None and b<last_boot:row.update(kind='invalid',reason='BOOT_REGRESSION')
                        last_boot=b
                    elif ident==24:row.update(kind='gps',fix=p[28],satellites=p[29],hdop=struct.unpack_from('<H',p,20)[0])
                    elif ident==193:row.update(kind='ekf',flags=struct.unpack_from('<H',p,20)[0])
                    elif ident==242:
                        lat,lon,alt=struct.unpack_from('<iii',p);row.update(kind='home',home={'latE7':lat,'lonE7':lon,'altMSLmm':alt,'datum':DATUM})
                    else:continue
            rows.append(row)
            if len(rows)>POLICY['maxRows']:raise ValueError('GEOGRAPHY_ROWS_BOUND')
    return rows


def qualify(rows,run,epoch,boot,confirmation,*,ground_only=False):
    """Pure schema/state gate; every selected position in full armed episode checked."""
    latest={};last_time=-1;start=end=None;armed=False;positions=[];pre_authority=0;last_position=None;last_boot=None;failures=[]
    home=None if confirmation is None else home_fields(confirmation['home'])
    def fail(reason,row):failures.append({'reason':reason,'hostNs':row.get('hostNs')})
    for r in rows:
        if any(r.get(k)!=v for k,v in [('run',run),('epoch',epoch),('boot',boot)]):raise ValueError('GEOGRAPHY_CONTEXT')
        now=integer(r.get('hostNs'),0,2**63-1,'GEOGRAPHY_CLOCK')
        if now<last_time:raise ValueError('GEOGRAPHY_REORDER')
        last_time=now;kind=r.get('kind')
        if kind=='heartbeat':
            if type(r.get('armed'))is not bool:raise ValueError('ARMED_TYPE')
            if r['armed']and not armed:
                if end is not None:fail('REARM_REQUIRES_NEW_CASE_CONFIRMATION',r)
                elif start is None:start=now
            if armed and not r['armed']and end is None:end=now
            armed=r['armed']
        if start is None:
            if kind=='position':pre_authority+=1
            latest[kind]=r;continue
        if end is not None and now>end:
            # All later observations retained. New ARM is already fenced above.
            continue
        if kind=='invalid':fail(r['reason'],r);continue
        if kind=='home':
            try:observed=home_fields(r['home'])
            except(ValueError,KeyError,TypeError):fail('HOME_SCHEMA_OR_DATUM',r);continue
            if home is not None and observed!=home and now>=confirmation.get('referenceObservedHostNs',0):fail('HOME_CHANGED_FROM_CONFIRMED_REFERENCE',r)
        latest[kind]=r
        if kind=='heartbeat':
            for sensor,limit in [('gps',POLICY['GPSFreshNs']),('ekf',POLICY['EKFFreshNs']),('home',POLICY['HomeFreshNs'])]:
                prior=latest.get(sensor)
                if prior is None or not 0<=now-prior['hostNs']<=limit:fail('ARM_EDGE_MISSING_OR_STALE_'+sensor.upper(),r)
            at_gps=latest.get('gps',{});at_flags=latest.get('ekf',{}).get('flags')
            if(type(at_gps.get('fix'))is not int or at_gps['fix']not in(3,4,5,6,8)
               or type(at_gps.get('satellites'))is not int or not 6<=at_gps['satellites']<=254
               or type(at_gps.get('hdop'))is not int or not 0<=at_gps['hdop']<=200):fail('ARM_EDGE_UNQUALIFIED_GPS',r)
            if type(at_flags)is not int or at_flags&~0x037f or at_flags&55!=55:fail('ARM_EDGE_UNQUALIFIED_EKF',r)
            try:home_fields(latest.get('home',{}).get('home'))
            except(ValueError,KeyError,TypeError):fail('ARM_EDGE_HOME_SCHEMA_OR_DATUM',r)
        if kind=='gps'and(type(r.get('fix'))is not int or r['fix']not in(3,4,5,6,8)or type(r.get('satellites'))is not int or not 6<=r['satellites']<=254 or type(r.get('hdop'))is not int or not 0<=r['hdop']<=200):fail('LATEST_GPS_CONTRADICTION',r)
        if kind=='ekf'and(type(r.get('flags'))is not int or r['flags']&~0x037f or r['flags']&55!=55):fail('LATEST_EKF_CONTRADICTION',r)
        if kind!='position':continue
        try:
            integer(r['latE7'],-900000000,900000000,'LAT_E7');integer(r['lonE7'],-1800000000,1800000000,'LON_E7')
            integer(r['relativeMm'],-10000000,10000000,'RELATIVE_MM');integer(r['altAMSLmm'],-10000000,10000000,'AMSL_MM')
            integer(r['bootMs'],0,2**32-1,'AP_BOOT_MS')
            if last_boot is not None and r['bootMs']<=last_boot:fail('AP_BOOT_TIME_NOT_STRICTLY_NEW',r)
            last_boot=r['bootMs']
            if now-(start if last_position is None else last_position)>POLICY['positionFreshNs']:fail('ARMED_POSITION_COVERAGE_GAP',r)
            last_position=now
            for name,limit in [('heartbeat',POLICY['heartbeatFreshNs']),('gps',POLICY['GPSFreshNs']),('ekf',POLICY['EKFFreshNs']),('home',POLICY['HomeFreshNs'])]:
                v=latest.get(name)
                if v is None or not 0<=now-v['hostNs']<=limit:fail('MISSING_OR_STALE_'+name.upper(),r)
            gps=latest.get('gps',{});ekf=latest.get('ekf',{});observed_home=latest.get('home',{}).get('home')
            if observed_home is not None:home_fields(observed_home)
            if gps.get('fix')not in(3,4,5,6,8)or type(gps.get('fix'))is not int or type(gps.get('satellites'))is not int or not 6<=gps['satellites']<=254 or type(gps.get('hdop'))is not int or not 0<=gps['hdop']<=200:fail('UNQUALIFIED_GPS',r)
            flags=ekf.get('flags')
            if type(flags)is not int or flags&~0x037f or flags&55!=55:fail('UNQUALIFIED_EKF',r)
            if home is None:fail('EXPLICIT_NATIVE_CONFIRMATION_MISSING',r)
            elif observed_home is None:fail('HOME_SCHEMA_OR_DATUM',r)
            elif observed_home!=home and now>=confirmation.get('referenceObservedHostNs',0):fail('LATEST_HOME_NOT_CONFIRMED_REFERENCE',r)
            else:
                distance,_=inverse(home,r)
                if abs(r['altAMSLmm']-home['altMSLmm']-r['relativeMm'])>POLICY['syntheticAPDatumToleranceMm']:fail('AMSL_HOME_RELATIVE_DATUM_INCONSISTENT',r)
                if distance>POLICY['horizontalLimitM']:fail('HORIZONTAL_ENVELOPE_10M',r)
                if r['relativeMm']>POLICY['relativeAltitudeLimitMm']:fail('ALTITUDE_ENVELOPE_5M',r)
                positions.append({'hostNs':now,'distanceFromConfirmedHomeM':distance,'relativeMm':r['relativeMm']})
        except(KeyError,TypeError,ValueError,OverflowError)as exc:fail('POSITION_SCHEMA:'+str(exc),r)
    if ground_only:
        if start is not None:failures.append({'reason':'ARMED_IN_GROUND_ONLY_CASE'})
        return {'status':'GROUND_ONLY_NO_FLIGHT_AUTHORITY'if not failures else'GEOGRAPHY_NOT_READY','failures':failures,'preAuthorityPositionsRetained':pre_authority,'flightAccepted':False}
    if start is None or end is None:failures.append({'reason':'COMPLETE_ARM_TO_DISARM_WINDOW_REQUIRED'})
    if start is not None and(last_position is None or end is not None and end-last_position>POLICY['positionFreshNs']):failures.append({'reason':'ARMED_TERMINAL_POSITION_GAP'})
    if not positions:failures.append({'reason':'NO_QUALIFIED_ARMED_POSITIONS'})
    return {'status':'GEOGRAPHY_FULL_ARMED_WINDOW_PASS'if not failures else'GEOGRAPHY_NOT_READY','failures':failures,
            'armedStartHostNs':start,'terminalDisarmHostNs':end,'checkedArmedPositions':len(positions),
            'preAuthorityPositionsRetained':pre_authority,'maximumDistanceFromConfirmedHomeM':max((p['distanceFromConfirmedHomeM']for p in positions),default=None),
            'maximumRelativeAltitudeMm':max((p['relativeMm']for p in positions),default=None),'reference':home,'policy':POLICY,'wholeBetaAccepted':False}
