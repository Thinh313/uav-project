"""Dual-channel causal witness, compared only within each channel's own clock/order."""
import base64,hashlib,itertools,struct,math
from pilot.betaintegrated01.control04.confirmation import verify_confirmation,_closed_native
from pilot.betaintegrated01.control01.mavlink import Framer


def release_witness(descriptor,descriptor_anchor,run,epoch,boot,wire):
    verify_confirmation(descriptor,descriptor_anchor,run,epoch,boot)
    _,rows=_closed_native(descriptor['nativeTarPath'],descriptor['prefix'],descriptor['nativeExternalAnchor'])
    tx={};mode17=[];rx=Framer();seq=None
    for row in rows:
        payload=base64.b64decode(row['base64'],validate=True)
        if row['kind']=='TX_WRITTEN':tx.setdefault(hashlib.sha256(payload).hexdigest(),[]).append((row['n'],row['monotonicNs']))
        if row['kind']!='RX':continue
        for f in rx.feed(payload,row['monotonicNs']):
            if f['system']!=42 or f['component']!=1:continue
            delta=None if seq is None else(f['wireSequence']-seq)&255
            if delta==0 or delta is not None and delta>=128:continue
            seq=f['wireSequence']
            if f['id']==0 and f['payload'][4:6]==bytes([2,3]) and struct.unpack_from('<I',f['payload'])[0]==17 and f['payload'][6]&128:
                mode17.append((row['n'],row['monotonicNs'],hashlib.sha256(bytes.fromhex(f['wireHex'])).hexdigest()))
    return wire_release_observations(wire,tx,mode17)


def wire_release_observations(wire,native_tx_by_sha,native_rx17):
    commands=wire['nativeForwardedTimeline'];states=wire['passiveTimeline']
    def mode(c,value):return c['kind']=='SET_MODE'and c['mode']==value or c['kind']=='COMMAND_LONG'and c['command']==176 and c['params'][1]==value
    brakes=[c for c in commands if mode(c,17)];lands=[c for c in commands if mode(c,9)or c['kind']=='COMMAND_LONG'and c['command']==21]
    neutral=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['channels'][:4]==[1500]*4 and brakes and lands and brakes[0]['hostNs']<c['hostNs']<lands[0]['hostNs']]
    release=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['channels'][:8]==[0]*8 and c['channels'][8:]==[65534]*10 and brakes and lands and brakes[0]['hostNs']<c['hostNs']<lands[0]['hostNs']]
    held=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['forwardPitchHeld']]
    checks={'oneBrakeOneExplicitLandOneCleanupNeutralRelease':len(brakes)==len(lands)==len(neutral)==len(release)==1,
            'noFailsafeConfounder':not any(r['kind']=='text'and'failsafe'in r['text'].lower()for r in states)}
    native_candidates=[]
    if checks['oneBrakeOneExplicitLandOneCleanupNeutralRelease']:
        b,l,n,r=brakes[0],lands[0],neutral[0],release[0]
        checks['hostForwardThenBrakeNeutralReleaseLand']=bool(held)and held[-1]['hostNs']<=b['hostNs']<n['hostNs']<r['hostNs']<l['hostNs']
        checks['passiveActualBrakeBeforeLand']=any(s['kind']=='heartbeat'and s['mode']==17 and s['armed']and b['hostNs']<=s['hostNs']<l['hostNs']for s in states)
        lists=[native_tx_by_sha.get(c.get('wireSHA256'),[])for c in(b,n,r,l)]
        if any(len(v)>16 for v in lists)or math.prod(map(len,lists))>64:raise ValueError('NATIVE_WIRE_MATCH_AMBIGUITY_BOUND')
        for bt,nt,rt,lt in itertools.product(*lists):
            if bt[0]<nt[0]<rt[0]<lt[0]and any(bt[0]<m[0]<nt[0]and 0<=nt[1]-m[1]<=1_500_000_000 for m in native_rx17):
                native_candidates.append({'brakeNativeRecord':bt[0],'neutralNativeRecord':nt[0],'releaseNativeRecord':rt[0],'landNativeRecord':lt[0],
                                          'brakeSHA256':b['wireSHA256'],'neutralSHA256':n['wireSHA256'],'releaseSHA256':r['wireSHA256'],'landSHA256':l['wireSHA256']})
    checks['uniqueNativeCRCMode17BeforeCleanupMatchedExactWireSHA']=len(native_candidates)==1
    return {'status':'HOST_NATIVE_RELEASE_WITNESS_PASS'if all(checks.values())else'HOST_NATIVE_RELEASE_NOT_READY','criteria':checks,
            'nativeOrderedWitness':native_candidates[0]if len(native_candidates)==1 else None,
            'crossClockAbsoluteComparison':False,'nativeUPRevocationAndFreshDifferentLeaseAudit':'REQUIRED_SEPARATELY_NOT_INFERRED_FROM_MAVLINK'}
