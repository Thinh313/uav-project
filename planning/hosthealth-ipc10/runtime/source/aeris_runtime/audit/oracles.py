"""Qualified geography reference + existing full-frame and exact-wire receivers."""
import math
verify_capture=__import__('importlib').import_module('aeris_runtime.audit.verify_capture').verify_capture
from aeris_runtime.audit.control import control_outcome as old_control_outcome
audit_transport=__import__('importlib').import_module('aeris_runtime.audit.transport').audit_transport
from aeris_runtime.audit.geocollect import collect
from .native_release import release_witness
from aeris_runtime.audit.geography import qualify,inverse,POLICY
from .confirmation import verify_confirmation


def host_home_witness(rows,confirmation,commands):
    arms=[r for r in rows if r['kind']=='heartbeat'and r['armed']]
    takeoffs=[c for c in commands if c['kind']=='COMMAND_LONG'and c['command']==22]
    if not arms or not takeoffs:raise ValueError('RAW_ARM_AND_TAKEOFF_REQUIRED')
    lo,hi=confirmation['hostBracketNs'];phase=POLICY['hostConfirmationPhaseToleranceNs']
    candidates=[r for r in rows if r['kind']=='home'and r['home']==confirmation['home']
                and arms[0]['hostNs']<=r['hostNs']<=takeoffs[0]['hostNs']and lo-phase<=r['hostNs']<=hi+phase]
    if not candidates:raise ValueError('CRC_PASSIVE_HOME_AFTER_ARM_BEFORE_TAKEOFF_WITHIN_FIXED_PHASE_BOUND_REQUIRED')
    if not arms[0]['hostNs']<=hi<takeoffs[0]['hostNs']:raise ValueError('HOST_CONFIRMATION_ARM_TAKEOFF_ORDER')
    return {**confirmation,'referenceObservedHostNs':candidates[0]['hostNs'],'passiveHomeWireSHA256':candidates[0]['wireSHA256']}


def verify_case(out,run,epoch,boot,*,host_anchor,AP_anchor,transport_anchor,scenario,native_confirmation=None,confirmedHomeReceiptAnchor=None,clock_anchor=None,source_amendment=None,maximum_seconds=1960):
    if scenario not in ('nominal','loss','ground-recovery'):raise ValueError('UNQUALIFIED_SCENARIO_REQUIRES_SEPARATE_COMBINED_ORACLE')
    physics=verify_capture(out,run,epoch,boot,expected_host_anchor=host_anchor,expected_stage_anchor=AP_anchor,expected_clock_anchor=clock_anchor,source_amendment=source_amendment,maximum_seconds=maximum_seconds)
    wire=audit_transport(out,run,epoch,boot,expected_anchor=transport_anchor)
    rows=collect(out,run,epoch,boot)
    confirmed=None
    if scenario!='ground-recovery':
        if native_confirmation is None:raise ValueError('EXPLICIT_NATIVE_CONFIRMATION_RECEIPT_REQUIRED')
        confirmed=verify_confirmation(native_confirmation,confirmedHomeReceiptAnchor,run,epoch,boot)
        confirmed=host_home_witness(rows,confirmed,wire['nativeForwardedTimeline'])
    geography=qualify(rows,run,epoch,boot,confirmed,ground_only=scenario=='ground-recovery')
    old=old_control_outcome(wire,scenario)
    # Replace precisely the defective startup-origin geography criteria, preserve all others.
    old['criteria'].pop('horizontalEnvelopeAtMost10m',None);old['criteria'].pop('relativeAltitudeEnvelopeAtMost5m',None)
    old['criteria']['qualifiedFullArmedGeographyReference']=geography['status']in('GEOGRAPHY_FULL_ARMED_WINDOW_PASS','GROUND_ONLY_NO_FLIGHT_AUTHORITY')
    # Use the same WGS84 geometry for the independent manual direction projection.
    moving=[c for c in wire['nativeForwardedTimeline']if c['kind']=='RC_OVERRIDE'and c['forwardPitchHeld']]
    if moving:
        pos=[r for r in rows if r['kind']=='position'];first,last=moving[0]['hostNs'],moving[-1]['hostNs']
        before=[r for r in pos if r['hostNs']<=first];after=[r for r in pos if first<=r['hostNs']<=last+2_000_000_000]
        forward=[];manual_distances=[]
        if before and before[-1]['headingCentiDeg']!=65535:
            for r in after:
                distance,azimuth=inverse(before[-1],r)
                manual_distances.append(distance)
                forward.append(distance*math.cos(math.radians(azimuth-before[-1]['headingCentiDeg']/100)))
        old['metrics']['manualObservedForwardDisplacementM']=max(forward,default=0)
        old['metrics']['manualObservedDisplacementM']=max(manual_distances,default=0)
        old['criteria']['manualMotionObserved']=bool(manual_distances)and max(manual_distances)>=.3
        old['criteria']['manualForwardDirectionObserved']=bool(forward)and max(forward)>=.3
    release=None if scenario!='nominal'else release_witness(native_confirmation,confirmedHomeReceiptAnchor,run,epoch,boot,wire)
    old['status']='CONTROL_OBSERVATIONS_PASS'if all(old['criteria'].values())else'CONTROL_NOT_READY'
    if release and release['status']!='HOST_NATIVE_RELEASE_WITNESS_PASS':old['status']='CONTROL_NOT_READY'
    if scenario=='ground-recovery'and old['status']=='CONTROL_OBSERVATIONS_PASS':old['status']='GROUND_RECOVERY_OBSERVATIONS_PASS_NO_FLIGHT_AUTHORITY'
    return {'status':old['status'],'fullFrameModelAP':physics,'control':old,'geography':geography,'confirmedHome':confirmed,
            'nominalRelease':release,'wireAudit':wire,'nativeInputAuthorityAuditStillRequired':True,'wholeBetaAccepted':False,
            'oldReceiptsOrAggregatesRewritten':False,'physicalFlightOrHeraAcceptance':False,'thirtyMinuteAcceptance':False,'durationQualification':'ROOT_FULL_DURATION_AND_NATIVE_INPUT_AUDIT_REQUIRED',
            'longConsumerBounds':{'geographyCollectorMaxRows':262144,'passiveTimelineMaxRows':131072,'nativeTimelineMaxRows':131072,'nativeTarMaxBytes':168*2**20,'nativeSelectedRunMaxBytes':160*2**20,'nativeSegmentMaxBytes':2**20,'inheritedGeographyPolicyMaxRows16000IsNotLongCollectorBound':True}}

verify_case_long=verify_case
