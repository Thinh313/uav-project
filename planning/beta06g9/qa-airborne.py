"""Root-only bounded visible-UI choreography. No control POST/eval/UIAutomator.
--plan is pure. Actual --airborne requires two previously inspected references.
"""
from pathlib import Path
import importlib.util,sys
if 'g9_native_writer'not in sys.modules:
 _w=importlib.util.spec_from_file_location('g9_native_writer',Path(__file__).with_name('qa-native-budget.py'));b=importlib.util.module_from_spec(_w);sys.modules[_w.name]=b;_w.loader.exec_module(b)
else:b=sys.modules['g9_native_writer']
import importlib.util,json,time,sys,argparse
spec=importlib.util.spec_from_file_location('ui05',Path(__file__).with_name('qa-ui.py'));ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)

specA=importlib.util.spec_from_file_location('admission05',Path(__file__).with_name('qa-ap-admission.py'));admission=importlib.util.module_from_spec(specA);specA.loader.exec_module(admission)

def wait_target_ready(reference,ident,reader=None,clock=time.monotonic,pause=time.sleep):
    """Readiness observation only; never dispatches and never retries an input."""
    reader=reader or ui.observation;origin=reference['observed']['observation'];deadline=clock()+2
    while clock()<deadline:
        try:
            value=reader();assert clock()<deadline,'TARGET_READINESS2S_DEADLINE';assert 0<=value['ageMs']<=1200,'STALE_OBSERVATION'
            current=value['observation'];assert all(current.get(k)==origin.get(k)for k in['documentId','clientId','clientEpoch','clientInstance','run','boot','configId','modelSha256','planSha256','tab','viewport']),'TARGET_READINESS_CONTEXT_CHANGED'
            ui.target(value,ident);return value
        except AssertionError as e:
            if str(e)not in['STALE_OBSERVATION','TARGET_UNAVAILABLE_OR_OCCLUDED']:raise
            pause(min(.08,max(0,deadline-clock())))
    raise AssertionError('TARGET_NOT_READY_WITHIN2S_NO_INPUT')

def plan(fault=False):
    common=['readonly AP admission exact31samples/span30s/min29GiB/peakdecline256MiB','visible tab-flight if needed','field-preflight refresh after exact lease>=40000ms','field-arm','field-auto (current Home >1800ms)','readonly wait actual AUTO/armed/height>5']
    return{'steps':common+(['field-tab-payload','field-gimbal','field-tab-flight','readonly fresh active calibrated source/viewer point','field-cut or field-reboot with exact live lease >=5000ms']if fault else['video-measure selected30s window','video-capture committed receipt','video-pause500','field-tab-payload','field-gimbal']),'mediaMetric':'NOT_APPLICABLE_FAULT_SCENARIO'if fault else'SELECTED30S_REQUIRES_INDEPENDENT_REPLAY','sourceAndViewerActiveThroughFlightRequired':True,'noControlPost':True,'noEval':True,'noUIAutomator':True,'noRetries':True,'maximumControllerSeconds':90,'requiresRootInspectedFlightAndPayloadReferences':True,'independentRawMediaLeaseReplayRequired':True}

def fault_media_point(value,context):
    """Read-only current frame/config point, not a fault-window FPS claim."""
    assert isinstance(value,dict)and 0<=value.get('ageMs',float('inf'))<=1200,'FAULT_MEDIA_OBSERVATION_STALE'
    o=value['observation'];assert all(o.get(k)==context.get(k)for k in ['documentId','run','boot','configId','modelSha256','planSha256','clientId','clientEpoch','clientInstance']),'FAULT_MEDIA_CONTEXT_CHANGED'
    m=o.get('mediaReadiness')or{};age=m.get('frameAgeMs');sample=m.get('clockMappingSampledBrowserMs');until=m.get('clockMappingValidUntilBrowserMs');now=o.get('observedAtClientMonoMs')
    assert m.get('active')is True and m.get('clockStatus')=='CALIBRATED_BOUNDS'and m.get('clockDegraded')is False and m.get('previewReady')is True,'FAULT_CURRENT_ACTIVE_CALIBRATED_MEDIA_REQUIRED'
    assert all(isinstance(v,(int,float))and not isinstance(v,bool)and __import__('math').isfinite(v)for v in [age,sample,until,now])and 0<=age<=1000 and sample<=now<until and until-sample<=60000,'FAULT_CURRENT_FRAME_AND_MAPPING_REQUIRED'
    assert isinstance(m.get('clockSessionId'),str)and m['clockSessionId'],'FAULT_VIEWER_SESSION_REQUIRED'
    return{'observationSeq':o['seq'],'ageMs':value['ageMs'],'context':{k:o.get(k)for k in context},'mediaReadiness':m,'metricStatus':'NOT_APPLICABLE_FAULT_SCENARIO','independentContinuityReplayStillRequired':True}

def run(attempt,flightref,payloadref,prefix,scenario='nominal',dispatch=None,reserve=None):
    assert scenario in ['nominal','cut','reboot']and dispatch is not None and reserve is not None,'PERSISTENT_CONTROLLER_DISPATCH_AND_RESERVE_REQUIRED';fault=scenario!='nominal'
    assert attempt in['18','19']and prefix.replace('-','').isalnum()and len(prefix)<=48
    for p in[flightref,payloadref]:assert Path(p).is_file(),'ROOT_INSPECTED_REFERENCE_REQUIRED'
    record={'status':'RUNNING_NOT_ACCEPTANCE','plan':plan(fault),'attempt':attempt,'flightReference':str(flightref),'payloadReference':str(payloadref),'actions':[],'startedPythonMono':time.monotonic()};out=ui.q.E/(prefix+'-controller.json');assert not out.exists(),'EXCLUSIVE_CONTROLLER_NO_RETRY';start=time.monotonic();step=0
    def act(ident,ref,timeout=12):
        nonlocal step
        assert time.monotonic()-start<90,'CONTROLLER90S_BOUND';name=prefix+'-'+str(step)+'-'+ident;step+=1
        ready=wait_target_ready(json.loads(Path(ref).read_text()),ident);record['actions'].append({'targetId':ident,'readinessOnly':True,'observationSeq':ready['observation']['seq'],'inputSent':False});r=dispatch(ident,ref,name,timeout);record['actions'].append({'targetId':ident,'receipt':r,'evidencePrefix':name});return r
    try:
        v=ui.observation();o=v['observation'];assert o['run']and o['phase']=='DISARMED','PREPARED_DISARMED_RUN_REQUIRED';s=ui.q.state();run=s['flight']['run'];assert s['flight']['mode']=='sitl','ACTUAL_SITL_REQUIRED';record['apAdmission']=admission.check(run,prefix+'-ap-admission');record['context']={k:o.get(k)for k in['documentId','run','boot','configId','modelSha256','planSha256','clientId','clientEpoch','clientInstance','payloadSelection']}
        if o['tab']=='payload':act('field-tab-flight',payloadref)
        else:assert o['tab']=='flight','PREPARED_FLIGHT_OR_PAYLOAD_TAB_REQUIRED'
        leaseObs=s.get('payloadLeaseObservation')or{};assert any(x.get('remainingMs',0)>=40000 and x.get('untilHostMonoMs',0)>leaseObs.get('observedAtHostMonoMs',float('inf'))and x.get('flightRun')==o['run']and x.get('flightBoot')==o['boot']and x.get('modelSha256')==o['modelSha256']and x.get('planSha256')==o['planSha256']and x.get('clientId')==o['clientId']and x.get('clientEpoch')==o['clientEpoch']and x.get('clientInstance')==o['clientInstance']and x.get('stationId')==o['payloadSelection']['stationId']and x.get('payloadId')==o['payloadSelection']['deviceId']for x in leaseObs.get('leases',[])),'LATE_EXACT_PAYLOAD_LEASE40S_REQUIRED';act('field-preflight',flightref,timeout=20);record['preArmReserve']=reserve(run);act('field-arm',flightref,timeout=20);act('field-auto',flightref)
        end=time.monotonic()+20
        while True:
            s=ui.q.state();f=s['flight'];assert f.get('run')==run and not f.get('error')and not(f.get('live')or{}).get('failure'),'FLIGHT_CONTEXT_LOST_NO_RETRY';l=f.get('live')or{};age=f.get('positionAgeMs');ready=l.get('armed')is True and l.get('mode')=='AUTO'and l.get('stage')=='AUTO'and(f.get('latestPosition')or{}).get('relativeHomeM',-1)>5 and isinstance(age,(int,float))and 0<=age<=1000
            if ready:record['airborneBeforeMedia']=s;break
            assert time.monotonic()<end,'AIRBORNE20S_BOUND_NO_RETRY';time.sleep(.1)
        if not fault:
            act('video-measure',flightref);act('video-capture',flightref);s=ui.q.state();caps=[x for x in s.get('captures',[])if x.get('state')=='COMMITTED'and x.get('sidecar',{}).get('context',{}).get('flightRun')==run];assert caps,'COMMITTED_CURRENT_RUN_CAPTURE_REQUIRED';record['captureIds']=[x['captureId']for x in caps];act('video-pause',flightref)
        record['mediaMetric']=record['plan']['mediaMetric'];act('field-tab-payload',flightref);act('field-gimbal',payloadref)
        if fault:
            act('field-tab-flight',payloadref);record['mediaBeforeFault']=fault_media_point(ui.observation(),record['context']);record['beforeFault']=ui.q.state();act('field-reboot'if scenario=='reboot'else'field-cut',flightref,timeout=35);record['afterFault']=ui.q.state()
        record['status']='UI_SEQUENCE_ACKNOWLEDGED_NOT_ACCEPTANCE';record['independentRawMediaLeaseReplayRequired']=True;return record
    except BaseException as e:record['status']='FAILED_OR_PARTIAL_NO_RETRY';record['error']=str(e);raise
    finally:
        record['endedPythonMono']=time.monotonic();b.write_json(out,record,maximum=2*2**20,kind='airborne');print(json.dumps({'status':record['status'],'evidence':str(out),'error':record.get('error')}))

if __name__=='__main__':
    assert sys.argv[1:]==['--plan'],'USE_PERSISTENT_ROOT_CONTROLLER_FOR_ALL_AIRBORNE_INPUT';print(json.dumps(plan(),indent=2))
