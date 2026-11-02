"""Dual-channel causal witness; no comparison of absolute host and guest clocks."""
import base64,hashlib,itertools,struct,math
from .confirmation import verify_confirmation,_closed_native
from pilot.betaintegrated01.control01.mavlink import Framer


from .native_wire import native_wire_evidence


def release_witness(descriptor,descriptor_anchor,run,epoch,boot,wire):
    verify_confirmation(descriptor,descriptor_anchor,run,epoch,boot)
    _,rows=_closed_native(descriptor['nativeTarPath'],descriptor['prefix'],descriptor['nativeExternalAnchor'])
    tx,hb=native_wire_evidence(rows)
    return wire_release_observations(wire,tx,hb)


def wire_release_observations(wire,native_tx_by_sha,native_heartbeats):
    commands=wire['nativeForwardedTimeline'];states=wire['passiveTimeline'];ordinal={id(c):i for i,c in enumerate(commands)}
    def mode(c,value):return c['kind']=='SET_MODE'and c['mode']==value or c['kind']=='COMMAND_LONG'and c['command']==176 and c['params'][1]==value
    brakes=[c for c in commands if mode(c,17)];lands=[c for c in commands if mode(c,9)or c['kind']=='COMMAND_LONG'and c['command']==21]
    def cleanup(c):return brakes and lands and ordinal[id(brakes[0])]<ordinal[id(c)]<ordinal[id(lands[0])]
    neutral=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['channels'][:4]==[1500]*4 and cleanup(c)]
    release=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['channels'][:8]==[0]*8 and c['channels'][8:]==[65534]*10 and cleanup(c)]
    held=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['forwardPitchHeld']]
    checks={'oneBrakeOneExplicitLandOneCleanupNeutralRelease':len(brakes)==len(lands)==len(neutral)==len(release)==1,
            'noFailsafeConfounder':not any(r['kind']=='text'and'failsafe'in r['text'].lower()for r in states)}
    witnesses=[]
    if checks['oneBrakeOneExplicitLandOneCleanupNeutralRelease']:
        b,l,n,r=brakes[0],lands[0],neutral[0],release[0]
        checks['hostForwardThenBrakeNeutralReleaseLand']=bool(held)and ordinal[id(held[-1])]<=ordinal[id(b)]<ordinal[id(n)]<ordinal[id(r)]<ordinal[id(l)]
        checks['noOtherRCBetweenBrakeAndLand']=not any(c['kind']=='RC_OVERRIDE'and cleanup(c)and c not in(neutral+release)for c in commands)
        checks['passiveActualBrakeBeforeLand']=any(s['kind']=='heartbeat'and s['mode']==17 and s['armed']and b['hostNs']<=s['hostNs']<l['hostNs']for s in states)
        lists=[native_tx_by_sha.get(c.get('wireSHA256'),[])for c in(b,n,r,l)]
        if any(len(v)>16 for v in lists)or math.prod(map(len,lists))>64:raise ValueError('NATIVE_WIRE_MATCH_AMBIGUITY_BOUND')
        for bt,nt,rt,lt in itertools.product(*lists):
            # Tuple: intentRecord,intentGuestNs,writtenRecord,writtenGuestNs.
            if not bt[0]<bt[2]<nt[0]<nt[2]<rt[0]<rt[2]<lt[0]<lt[2]:continue
            modes=[]
            for intent in(nt,rt):
                prior=[h for h in native_heartbeats if h['record']<intent[0]]
                latest=prior[-1]if prior else None
                if not(latest and latest['validType']and latest['armed']and latest['mode']==17
                       and bt[2]<latest['record']and bt[3]<=latest['guestNs']and 0<=intent[1]-latest['guestNs']<=1_500_000_000):break
                modes.append(latest)
            if len(modes)==2:
                witnesses.append({'brakeNativeIntent':bt[0],'brakeNativeWritten':bt[2],
                                  'neutralNativeIntent':nt[0],'neutralNativeWritten':nt[2],
                                  'releaseNativeIntent':rt[0],'releaseNativeWritten':rt[2],'releaseNativeWrittenGuestNs':rt[3],
                                  'landNativeIntent':lt[0],'landNativeWritten':lt[2],
                                  'latestCRCModeAtNeutralIntent':modes[0],'latestCRCModeAtReleaseIntent':modes[1],
                                  'brakeSHA256':b['wireSHA256'],'neutralSHA256':n['wireSHA256'],'releaseSHA256':r['wireSHA256'],'landSHA256':l['wireSHA256']})
    checks['uniqueLatestNativeCRCMode17BeforeDurableCleanupIntentMatchedExactWireSHA']=len(witnesses)==1
    return {'status':'HOST_NATIVE_RELEASE_WITNESS_PASS'if all(checks.values())else'HOST_NATIVE_RELEASE_NOT_READY','criteria':checks,
            'nativeOrderedWitness':witnesses[0]if len(witnesses)==1 else None,
            'crossClockAbsoluteComparison':False,'nativeUPRevocationAndFreshDifferentLeaseAudit':'REQUIRED_SEPARATELY_NOT_INFERRED_FROM_MAVLINK'}
