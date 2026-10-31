"""Cold control observations from full raw, independently decoded state fields.

M1 frame/model/AP coverage is delegated to the previously accepted cold oracle.
This layer never infers movement, mode or landing from command ACKs.
"""
from pathlib import Path
from collections import deque
import json
import math
import struct
from pilot.betaintegrated01.runtime02.journal import verify_journal
from pilot.betaintegrated01.runtime02.verify_capture import verify_capture
from .mavlink import Framer


def events(root):
    for path in sorted(Path(root).glob('segment-*.jsonl')):
        with path.open('rb')as f:
            for line in f:
                body=json.loads(line)['body']
                if body['kind']=='EVENT':yield body['payload']['eventKind'],body['payload']['data']


def critical_fields(frame):
    p=frame['payload'];ident=frame['id']
    if ident==0:
        mode=struct.unpack_from('<I',p)[0]
        return {'kind':'heartbeat','mode':mode,'armed':bool(p[6]&128)}
    if ident==33:
        boot,lat,lon,amsl,relative,vx,vy,vz,heading=struct.unpack_from('<IiiiihhhH',p)
        return {'kind':'position','bootMs':boot,'latE7':lat,'lonE7':lon,'altAMSLmm':amsl,
                'relativeMm':relative,'vxCms':vx,'vyCms':vy,'vzCms':vz,'headingCentiDeg':heading}
    if ident==245:return {'kind':'landed','state':p[1]}
    if ident==1:return {'kind':'battery','milliVolt':struct.unpack_from('<H',p,14)[0]}
    if ident==253:return {'kind':'text','severity':p[0],'text':p[1:51].split(b'\0')[0].decode('utf-8','replace')}
    return None


def native_fields(frame):
    p=frame['payload'];ident=frame['id']
    if frame['system']!=255 or frame['component']!=190:raise ValueError('FOREIGN_NATIVE_COMMAND_SOURCE')
    if ident==0:return {'kind':'heartbeat'}
    if ident==70:
        channels=list(struct.unpack_from('<8H',p))+list(struct.unpack_from('<10H',p,18))
        if p[16:18]!=bytes([42,1]):raise ValueError('RC_WRONG_TARGET')
        return {'kind':'RC_OVERRIDE','channels':channels,'forwardPitchHeld':0<channels[1]<=1480}
    if ident==76:
        values=list(struct.unpack_from('<7f',p));command=struct.unpack_from('<H',p,28)[0]
        if p[30:32]!=bytes([42,1]):raise ValueError('COMMAND_WRONG_TARGET')
        if command==400 and values[0]==1 and values[1]!=0:raise ValueError('FORCE_ARM_FORBIDDEN')
        return {'kind':'COMMAND_LONG','command':command,'params':values}
    if ident==11:
        mode=struct.unpack_from('<I',p)[0]
        if p[4]!=42:raise ValueError('MODE_WRONG_TARGET')
        return {'kind':'SET_MODE','mode':mode}
    return None


def audit_transport(out,run,epoch,boot,*,expected_anchor):
    root=Path(out)/'transport-journal'
    integrity=verify_journal(root,run,epoch,expected_commit=expected_anchor)
    if integrity['state']!='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH':raise ValueError('EXTERNAL_TRANSPORT_ANCHOR_REQUIRED')
    passive=Framer();native=Framer();pending_passive=deque();pending_to_AP=b'';pending_to_native=b''
    active_intent=None;forwarded_AP=forwarded_native=0;closed_cut=None;cut_requested=False
    timeline=[];native_timeline=[];seq=None;boot_by_id={};duplicates=older=0
    for kind,data in events(root):
        if data.get('_boot')!=boot or type(data.get('_observedHostNs'))is not int:raise ValueError('TRANSPORT_BOOT_OR_CLOCK_BINDING')
        now=data['_observedHostNs']
        if kind=='PASSIVE_RX':
            if data.get('applicationTXBytes')!=0:raise ValueError('PASSIVE_TX_DECLARED')
            raw=bytes.fromhex(data['rawHex'])
            if len(raw)>4096:raise ValueError('PASSIVE_CHUNK_BOUND')
            pending_passive.extend(passive.feed(raw,data['hostNs']))
            if len(pending_passive)>512:raise ValueError('PASSIVE_DECODE_QUEUE_BOUND')
        elif kind=='PASSIVE_FRAME':
            if not pending_passive:raise ValueError('FRAME_WITHOUT_PASSIVE_RX')
            frame=pending_passive.popleft()
            if any(data.get(key)!=frame[key]for key in('id','system','component','wireSequence','wireHex','monotonicNs')):
                raise ValueError('STORED_FRAME_NOT_EQUAL_RAW')
            if frame['system']!=42 or frame['component']!=1:continue
            delta=None if seq is None else(frame['wireSequence']-seq)&255
            if delta==0:duplicates+=1;continue
            if delta is not None and delta>=128:older+=1;continue
            seq=frame['wireSequence'];fields=critical_fields(frame)
            if fields is not None:
                if 'bootMs'in fields:
                    if frame['id']in boot_by_id and fields['bootMs']<boot_by_id[frame['id']]:raise ValueError('AP_BOOT_REGRESSION_WITHIN_EPOCH')
                    boot_by_id[frame['id']]=fields['bootMs']
                timeline.append({'hostNs':frame['monotonicNs'],**fields})
                if len(timeline)>8192:raise ValueError('CONTROL_TIMELINE_BOUND_NO_SAMPLING')
        elif kind in('NATIVE_RX','AP_RELAY_RX'):
            raw=bytes.fromhex(data['rawHex'])
            if kind=='NATIVE_RX':
                if closed_cut is not None:raise ValueError('NATIVE_RX_AFTER_CUT')
                pending_to_AP+=raw
            else:pending_to_native+=raw
            if len(pending_to_AP)>16384 or len(pending_to_native)>16384:raise ValueError('FORWARD_BUFFER_BOUND')
        elif kind=='FORWARD_INTENT':
            if active_intent is not None:raise ValueError('UNRESOLVED_FORWARD_INTENT')
            direction=data['direction'];raw=bytes.fromhex(data['rawHex'])
            source=pending_to_AP if direction=='toAP'else pending_to_native
            if not raw or len(raw)>4096 or source[:len(raw)]!=raw:raise ValueError('FORWARD_BYTES_MUTATED_OR_GENERATED')
            if direction=='toAP'and closed_cut is not None:raise ValueError('SEND_AFTER_CUT')
            active_intent=(direction,raw)
        elif kind in('FORWARD_LOCAL_RETURN','FORWARD_NOT_READY'):
            if active_intent is None:raise ValueError('FORWARD_RETURN_WITHOUT_INTENT')
            direction,raw=active_intent
            if data['direction']!=direction:raise ValueError('FORWARD_DIRECTION')
            n=data['sentBytes']
            if type(n)is not int or not 0<=n<=len(raw)or(kind=='FORWARD_LOCAL_RETURN'and n==0):raise ValueError('FORWARD_COUNT')
            if direction=='toAP':
                pending_to_AP=pending_to_AP[n:];forwarded_AP+=n
                for frame in native.feed(raw[:n],now):
                    decoded=native_fields(frame)
                    if decoded:native_timeline.append({'hostNs':now,**decoded})
                    if len(native_timeline)>8192:raise ValueError('NATIVE_TIMELINE_BOUND')
            else:pending_to_native=pending_to_native[n:];forwarded_native+=n
            active_intent=None
        elif kind=='FORWARD_UNKNOWN':raise ValueError('FORWARD_UNKNOWN_NOT_COMPLETE_ACCEPTANCE')
        elif kind=='CUT_ACCEPTED':
            if cut_requested:raise ValueError('MULTIPLE_CUTS')
            cut_requested=True
        elif kind=='CUT_CONNECTIONS_CLOSED':
            if not cut_requested or closed_cut is not None:raise ValueError('CUT_CLOSE_ORDER')
            if not(type(data['closeStartedHostNs'])is int and type(data['closedHostNs'])is int and data['closeStartedHostNs']<=data['closedHostNs']<=now):
                raise ValueError('CUT_CLOSE_CLOCK')
            closed_cut=data['closedHostNs'];pending_to_AP=pending_to_native=b''
        elif kind=='NATIVE_PATH_EOF':pending_to_AP=pending_to_native=b''
        elif kind=='PASSIVE_TX':raise ValueError('PASSIVE_APPLICATION_TX_FORBIDDEN')
    if pending_passive:raise ValueError('UNCONSUMED_PASSIVE_FRAMES')
    if active_intent is not None:raise ValueError('UNRESOLVED_FINAL_FORWARD')
    return {'status':'RAW_TRANSPORT_INTEGRITY_AND_UNMODIFIED_FORWARDING_PASS','passiveApplicationTXBytes':0,
            'passiveTimeline':timeline,'nativeForwardedTimeline':native_timeline,'cutClosedHostNs':closed_cut,
            'nativeBytesForwarded':forwarded_AP,'APBytesForwarded':forwarded_native,'duplicatesIgnored':duplicates,
            'olderOrAmbiguousIgnored':older,'partialPassiveBytesAtOwnedStop':len(passive.pending),
            'partialNativeBytesAtOwnedStop':len(native.pending),'authorityGranted':False,
            'sourceAuthenticity':'LOCAL_PINNED_ORCHESTRATION_NOT_REMOTE_AUTHENTICATION'}


def displacement(a,b):
    lat=(a['latE7']+b['latE7'])/2e7*math.pi/180
    return 6371000*math.hypot((a['latE7']-b['latE7'])/1e7*math.pi/180,
                            (a['lonE7']-b['lonE7'])/1e7*math.pi/180*math.cos(lat))


def paired_ground_observations(rows,after_ns):
    # Use the latest preceding states, including contradictory observations.
    # Historical good states cannot outvote a newer armed/airborne message.
    heartbeat=landed=None;used_h=set();used_l=set();count=0
    for r in rows:
        if r['kind']=='heartbeat':heartbeat=r
        if r['kind']=='landed':landed=r
        if r['kind']!='position'or r['hostNs']<after_ns or abs(r['relativeMm'])>400:continue
        if heartbeat is None or landed is None:continue
        h,l=heartbeat,landed
        if (h['armed']or l['state']!=1 or h['hostNs']<after_ns or l['hostNs']<after_ns
            or h['hostNs']in used_h or l['hostNs']in used_l
            or not 0<=r['hostNs']-h['hostNs']<=1_500_000_000
            or not 0<=r['hostNs']-l['hostNs']<=1_000_000_000):continue
        used_h.add(h['hostNs']);used_l.add(l['hostNs']);count+=1
    return count


def observed_hover_span(rows,before_ns):
    hb=None;land=None;start=None;last=None;longest=0
    for r in rows:
        if r['hostNs']>=before_ns:break
        if r['kind']=='heartbeat':hb=r
        if r['kind']=='landed':land=r
        if r['kind']!='position':continue
        ok=(hb is not None and land is not None and hb['armed']and hb['mode']in(4,5,17)
            and r['hostNs']-hb['hostNs']<=1_500_000_000 and land['state']==2
            and r['hostNs']-land['hostNs']<=1_000_000_000 and abs(r['relativeMm']-3000)<=750
            and math.hypot(r.get('vxCms',math.inf),r.get('vyCms',math.inf))<=50)
        if not ok:start=last=None;continue
        if last is None or r['hostNs']-last>500_000_000:start=r['hostNs']
        last=r['hostNs'];longest=max(longest,last-start)
    return longest

def control_outcome(audit,scenario):
    rows=audit['passiveTimeline'];commands=audit['nativeForwardedTimeline']
    hb=[x for x in rows if x['kind']=='heartbeat'];pos=[x for x in rows if x['kind']=='position']
    landed=[x for x in rows if x['kind']=='landed'];battery=[x for x in rows if x['kind']=='battery']
    armed=[x for x in hb if x['armed']];land_mode=[x for x in hb if x['mode']==9]
    moving_input=[x for x in commands if x['kind']=='RC_OVERRIDE'and x['forwardPitchHeld']]
    arm=[x for x in commands if x['kind']=='COMMAND_LONG'and x['command']==400 and x['params'][0]==1]
    takeoff=[x for x in commands if x['kind']=='COMMAND_LONG'and x['command']==22 and abs(x['params'][6]-3)<1e-6]
    criteria={};metrics={'passiveApplicationTXBytes':audit['passiveApplicationTXBytes']}
    if scenario=='ground-recovery':
        criteria={'noArmSent':not arm,'neverObservedArmed':bool(hb)and not armed,
                  'twoFreshIndependentGroundDisarmedPositions':paired_ground_observations(rows,0)>=2}
    else:
        criteria['nativeNonforcedArmAnd3mTakeoffSent']=bool(arm)and bool(takeoff)
        criteria['armedObserved']=bool(armed)
        criteria['airborneObserved']=any(x['relativeMm']>=2000 for x in pos)and any(x['state']==2 for x in landed)
        criteria['loiterObserved']=any(x['mode']==5 and x['armed']for x in hb)
        longest_span=0;longest_count=0;streak=[]
        for item in commands:
            if item['kind']!='RC_OVERRIDE':continue
            if not item['forwardPitchHeld']:
                streak=[];continue
            if streak and item['hostNs']-streak[-1]>250000000:streak=[]
            streak.append(item['hostNs'])
            longest_span=max(longest_span,streak[-1]-streak[0]);longest_count=max(longest_count,len(streak))
        criteria['forwardInputContinuous']=longest_count>=3 and longest_span>=1000000000
        metrics['longestForwardInputSpanNs']=longest_span
        if moving_input and pos:
            first=moving_input[0]['hostNs'];last=moving_input[-1]['hostNs']
            before=[p for p in pos if p['hostNs']<=first]
            after=[p for p in pos if first<=p['hostNs']<=last+2_000_000_000]
            distance=max((displacement(before[-1],p)for p in after),default=0)if before else 0
            metrics['manualObservedDisplacementM']=distance;criteria['manualMotionObserved']=distance>=.3
            # Positive UI pitch is wire pitch<1500; project geodetic displacement
            # onto the observed pre-input aircraft heading, independently of UI labels.
            forward=0.0; heading=None
            if before and before[-1]['headingCentiDeg']!=65535:
                origin=before[-1];heading=math.radians(origin['headingCentiDeg']/100)
                latitude=math.radians(origin['latE7']/1e7)
                forward=max((6371000*((p['latE7']-origin['latE7'])/1e7*math.pi/180*math.cos(heading)
                    +(p['lonE7']-origin['lonE7'])/1e7*math.pi/180*math.cos(latitude)*math.sin(heading))for p in after),default=0.0)
            metrics['manualObservedForwardDisplacementM']=forward
            metrics['preInputHeadingRadians']=heading
            criteria['manualForwardDirectionObserved']=heading is not None and forward>=.3
        else:criteria['manualMotionObserved']=criteria['manualForwardDirectionObserved']=False
        hover_span=observed_hover_span(rows,moving_input[0]['hostNs']if moving_input else 0)
        metrics['observedPreManualHoverSpanNs']=hover_span
        criteria['threeMetreHoverObservedForOneSecond']=hover_span>=1_000_000_000
        criteria['relativeAltitudeEnvelopeAtMost5m']=bool(pos)and max(p['relativeMm']for p in pos)<=5000
        criteria['horizontalEnvelopeAtMost10m']=bool(pos)and max((displacement(pos[0],p)for p in pos),default=0)<=10
        criteria['landModeObserved']=bool(land_mode)
        if land_mode:
            when=land_mode[0]['hostNs']
            criteria['twoFreshIndependentGroundDisarmedPositionsAfterLand']=paired_ground_observations(rows,when)>=2
        else:criteria['twoFreshIndependentGroundDisarmedPositionsAfterLand']=False
        if arm:
            samples=[x for x in battery if x['hostNs']<=arm[0]['hostNs']and arm[0]['hostNs']-x['hostNs']<=1_500_000_000]
            criteria['freshWireBatteryAtLeast21VBeforeArm']=bool(samples)and 21000<=samples[-1]['milliVolt']<65535
        else:criteria['freshWireBatteryAtLeast21VBeforeArm']=False
        if scenario=='loss':
            cut=audit['cutClosedHostNs'];criteria['intentionalNativeOnlyCutObserved']=cut is not None
            if cut is not None:
                latest_pos=[x for x in pos if x['hostNs']<=cut and cut-x['hostNs']<=1_000_000_000]
                latest_hb=[x for x in hb if x['hostNs']<=cut and cut-x['hostNs']<=1_500_000_000]
                criteria['airborneAndArmedAtCut']=bool(latest_pos and latest_hb)and latest_pos[-1]['relativeMm']>=2000 and latest_hb[-1]['armed']
                criteria['forwardHeldAtCut']=bool(moving_input)and 0<=cut-moving_input[-1]['hostNs']<=200_000_000
                hearts=[x for x in commands if x['kind']=='heartbeat'and x['hostNs']<=cut]
                landing=[x for x in land_mode if x['hostNs']>cut]
                texts=[x for x in rows if x['kind']=='text'and x['hostNs']>=cut and'GCS'in x['text']and'Failsafe'in x['text']]
                criteria['GCSFailsafeTextAfterCut']=bool(texts)
                delay=(landing[0]['hostNs']-hearts[-1]['hostNs'])/1e9 if landing and hearts else None
                metrics['observedLandAfterLastForwardedHeartbeatSeconds']=delay
                criteria['GCSLandWithinDeclaredObservationWindow']=delay is not None and 4<=delay<=8
                criteria['noNativeLandCommandConfounder']=not any(x['kind']=='COMMAND_LONG'and(x['command']==21 or(x['command']==176 and x['params'][1]==9))or x['kind']=='SET_MODE'and x['mode']==9 for x in commands)
    return {'status':'CONTROL_OBSERVATIONS_PASS'if criteria and all(criteria.values())else'CONTROL_NOT_READY',
            'criteria':criteria,'metrics':metrics,'APTerminationNeverMeansSafeGround':True,
            'ACKNeverMeansExecution':True,'nativeInputAuthorityAuditStillRequired':True,'wholeM1OrBetaAccepted':False}


def verify_case(out,run,epoch,boot,*,host_anchor,AP_anchor,transport_anchor,scenario):
    physics=verify_capture(out,run,epoch,boot,expected_host_anchor=host_anchor,expected_stage_anchor=AP_anchor)
    wire=audit_transport(out,run,epoch,boot,expected_anchor=transport_anchor)
    outcome=control_outcome(wire,scenario)
    return {'status':outcome['status'],'fullFrameModelAP':physics,'control':outcome,'wireAudit':wire,
            'physicalFlightOrHeraAcceptance':False,'thirtyMinuteAcceptance':False}
