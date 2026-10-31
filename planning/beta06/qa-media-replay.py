"""BETA06 independent arithmetic/clock/fault replay.
Receiver-only visual coverage is not host visibility attestation.
Topology, actual cold boot and flight overlap require separately SHA-bound root evidence.
Never launches a viewer or changes a raw report.
Adapted from prior independent repair01 replay; frozen media format unchanged.
"""
import argparse,json,math,hashlib,datetime
from pathlib import Path
def retained_startup_binding(x):
    phases=x.get('startupPhases',[])
    names=['EXPLICIT_VIEWER_REQUEST','CLIENT_BOOTSTRAP_BEGIN','CLIENT_BOOTSTRAP_DONE','VIEWER_CLOCK_CALIBRATION_BEGIN','VIEWER_CLOCK_CALIBRATION_DONE','PROFILE_AND_SESSION_DISCOVERED','FIRST_VALIDATED_NETWORK_KEY_RECEIVED','FIRST_DECODER_OUTPUT','FIRST_NETWORK_KEY_FLUSH_RESOLVED','FRESH_WARM_KEY_RECEIVED','FIRST_FRESH_WARM_KEY_READY']
    if x.get('startupMeasurementScope')!='EXPLICIT_VIEWER_START':return {'verified':False,'reason':'EXPLICIT_START_SCOPE_REQUIRED_NOT_CHECKED'}
    by={}
    for q in phases:
        if q['kind']in names:
            assert q['kind']not in by,'DUPLICATE_STARTUP_PHASE'
            by[q['kind']]=q
    if any(n not in by for n in names):return {'verified':False,'reason':'RETAINED_STARTUP_PHASE_PROOF_MISSING_NOT_CHECKED'}
    assert all(by[a]['atBrowserMs']<=by[b]['atBrowserMs']for a,b in zip(names,names[1:])),'STARTUP_PHASE_ORDER'
    assert all(q['configId']==x['configId']for q in phases if q.get('configId')is not None),'STARTUP_CONFIG_MISMATCH'
    first=by['FIRST_VALIDATED_NETWORK_KEY_RECEIVED'];output=by['FIRST_DECODER_OUTPUT'];flush=by['FIRST_NETWORK_KEY_FLUSH_RESOLVED'];warm=by['FRESH_WARM_KEY_RECEIVED'];ready=by['FIRST_FRESH_WARM_KEY_READY'];start=by['EXPLICIT_VIEWER_REQUEST']
    assert first['timestampUs']==output['timestampUs']==flush['timestampUs'],'STARTUP_OUTPUT_TIMESTAMP_MISMATCH'
    assert ready['frameId']==warm['frameId']>first['frameId'],'FRESH_WARM_FRAME_MISMATCH'
    assert ready['readyMs']==x['initialReadyMs'],'READY_VALUE_MISMATCH'
    elapsed=ready['atBrowserMs']-start['requestedAtBrowserMs'];assert math.isfinite(elapsed)and math.isfinite(x['initialReadyMs'])and elapsed>=x['initialReadyMs']>=0,'STARTUP_INTERVAL_INVALID'
    return {'verified':elapsed<=1500,'reason':'PASS_EXACT_RETAINED_PHASE_CONFIG_BINDING'if elapsed<=1500 else'CONSERVATIVE_START_READY_BOUND_EXCEEDS1500_NOT_CHECKED','conservativeElapsedMs':elapsed,'reportedInitialReadyMs':x['initialReadyMs'],'phaseTimestampExtraMs':elapsed-x['initialReadyMs'],'configId':x['configId'],'initialNetworkFrameId':first['frameId'],'freshWarmFrameId':warm['frameId'],'scope':'Explicit viewer start only; codec/app coldness requires externally bound actual cohort evidence.'}

p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('out');args=p.parse_args();src=Path(args.source);out=Path(args.out)
assert str(src).startswith('evidence/beta06/') and str(out).startswith('evidence/beta06/qa') and not out.exists()
x=json.loads(src.read_text());s=x['samples'];eps=1e-5;duration=x['measurementEndBrowserMs']-x['measurementStartBrowserMs'];fps=len(s)/(duration/1000);pct=lambda a:sorted(a)[max(0,math.ceil(len(a)*.95)-1)]
assert len(s)==x['sampleCount'] and abs(duration-x['durationMs'])<eps and abs(fps-x['displayedFps'])<eps
lastid=laststamp=-1;upper=[]
for a in s:
 assert x['measurementStartBrowserMs']<=a['displayBrowserMs']<=x['measurementEndBrowserMs'] and a['frameId']>lastid and a['sourceTimestampUs']>laststamp;lastid=a['frameId'];laststamp=a['sourceTimestampUs'];lo=a['displayHostBounds']['lowerMs']-a['sourceHostBounds']['upperMs'];hi=a['displayHostBounds']['upperMs']-a['sourceHostBounds']['lowerMs'];assert abs(lo-a['latencyLowerMs'])<eps and abs(hi-a['latencyUpperMs'])<eps and 0<=hi-lo<=40 and lo>=-20;upper.append(hi)
p95=pct(upper);assert abs(p95-x['latencyP95UpperMs'])<eps;assert x['counters']['displayed']-x['counterBaseline']['displayed']==len(s)
faults=[]
for q in x['faultWindows']:
 a=next(a for a in s if a['frameId']==q['recoveredFrameId']);delta=q['recoveredDisplayBrowserMs']-q['at'];assert abs(delta-q['recoveryMs'])<eps;assert abs(q['responseBrowserMs']-q['at']-q['apiRoundtripMs'])<eps;assert abs(a['displayBrowserMs']-q['responseBrowserMs']-q['recoveryAfterResponseMs'])<eps;assert a['sourceHostBounds']==q['recoveredSourceHostBounds'] and a['recoveryId']==q['recoveredRecoveryId']>=q['expectedRecoveryId'];assert q['configId']==x['configId'];margin=a['sourceHostBounds']['lowerMs']-q['serverResumeNotBeforeMs'];assert margin>=0 and x['measurementStartBrowserMs']<=q['at']<=q['recoveredDisplayBrowserMs']<=x['measurementEndBrowserMs'];faults.append({'recoveryMs':delta,'apiRoundtripMs':q['apiRoundtripMs'],'afterResponseMs':q['recoveryAfterResponseMs'],'durationMs':q['durationMs'],'frameId':a['frameId'],'expectedRecoveryId':q['expectedRecoveryId'],'observedRecoveryId':a['recoveryId'],'freshSourceLowerAfterResumeMarginMs':margin,'pass':q['status']=='RECOVERED' and q['durationMs']<=delta<=2000})
coverage=30000<=duration<=60050 and x['foregroundOnly'] and x['visualForeground'] and not x['visualCoverageFailures'] and not x['overflow'] and x['stopReason'] is None
gates={'coverage':bool(coverage),'fps':bool(coverage and fps>=24),'sourceToCanvasP95':bool(coverage and len(upper)==len(s) and p95<=300),'recovery':all(q['pass']for q in faults) if faults else 'NOT_CHECKED'}
ready={'valueMs':x.get('initialReadyMs'),'firstConfigMatches':False,'traceAvailable':False}
if 'initialReady' in x['engineeringGate']:
 v=x.get('initialReadyMs');gates['initialReady']=isinstance(v,(float,int)) and math.isfinite(v) and 0<=v<=1500
 trace=x.get('decoderLifecycle',[]);start=next((q for q in trace if q['kind']=='EXPLICIT_VIEWER_START'),None);configured=next((q for q in trace if q['kind']=='CONFIGURE_VALIDATED_NETWORK_KEY'),None);actual=next((q for q in trace if q['kind']=='FIRST_FRESH_WARM_KEY_READY'),None);ready['traceAvailable']=all(q is not None for q in[start,configured,actual]);ready['trace']=trace
 if ready['traceAvailable']:
  assert abs(actual['readyMs']-v)<eps;assert actual['epoch']==start['epoch']==configured['epoch'];ready['firstConfigMatches']=configured['configId']==actual['configId']==x['configId'];ready['traceAfterStartMs']=actual['atBrowserMs']-start['requestedAtBrowserMs'];ready['traceCallAfterReadyTimestampMs']=ready['traceAfterStartMs']-v;assert ready['traceCallAfterReadyTimestampMs']>=-eps
ready['retainedPhaseBinding']=retained_startup_binding(x)
assert gates==x['engineeringGate'],(gates,x['engineeringGate'])
windowPass=all(v is True for v in gates.values());initialBinding=ready['retainedPhaseBinding']['verified'] if 'initialReady' in gates else None
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SELECTED_MEDIA_WINDOW' if windowPass and initialBinding is not False else 'FAIL_OR_NOT_CHECKED_MEDIA_GATE','input':{'path':str(src),'bytes':src.stat().st_size,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()},'identity':{k:x[k]for k in['serverBoot','run','boot','configId','feed','profileId']},'recomputed':{'samples':len(s),'durationMs':duration,'fps':fps,'latencyP95UpperMs':p95,'maxDisplayGapMs':max(a['interarrivalMs']or 0 for a in s),'allSampleBoundsRecalculated':True,'gates':gates},'initialReady':ready,'startupFirstOutputMs':x.get('startupMs'),'faults':faults,'platform':x.get('platform'),'counterBaseline':x['counterBaseline'],'counters':x['counters'],'scope':'Independent arithmetic/clock/identity replay of actual root-collected browser report. No new UI/codec/network/AP run by QA. Root separately establishes cold emulator/app and host producer visibility. Receiver-only visual coverage does not attest the host surface.','limitations':['No hardware-backend, exposure/photon latency or physical camera claim.','A passing individual window is not universal cold-start reliability or sustained every-device performance.','No pooled FPS or latency across different sources/runs/CPU profiles.','BETA06 requires exact retained startupPhases config/start/fresh-frame binding; bounded decoderLifecycle pruning alone does not lose valid retained proof. Missing both proof or wrong start scope stays NOT_CHECKED.','Media performance alone does not prove actual flight execution, payload exposure, overlap, host visibility or preservation.']}
with out.open('x')as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':r['status'],'fps':fps,'p95UpperMs':p95,'initialReadyMs':x.get('initialReadyMs'),'gates':gates,'initialConfigBinding':initialBinding,'faults':faults}))
