"""Additive offline close eligibility policy. Not wired into any live controller.

Stage/mode labels describe retained navigation state and are not disarm evidence.
The canonical completion result plus fresh matching state governs eligibility;
the existing frozen visible-dispatch phase policy remains a required second gate.
No HTTP/ADB/UI/process, source mutation, authority restoration or retry exists here.
"""
import math,re,time
IDENTITY_KEYS=('documentId','clientId','clientEpoch','clientInstance','run','boot','configId','modelSha256','planSha256')

def finite_age(value,maximum):
    return isinstance(value,(int,float))and not isinstance(value,bool)and math.isfinite(value)and 0<=value<=maximum

def reference_binding(reference):
    value=reference['observed']['observation'];binding={key:value.get(key)for key in IDENTITY_KEYS}
    assert isinstance(binding['run'],str)and re.fullmatch('s[a-f0-9]{20}',binding['run']),'EXACT_NOMINAL_RUN_REQUIRED'
    assert all(binding[key]is not None for key in IDENTITY_KEYS),'COMPLETE_INSPECTED_REFERENCE_BINDING_REQUIRED'
    return binding

def nominal_close_decision(state,view,binding):
    """Pure decision. Incomplete flight waits; stale/mismatched/failed state refuses.

    This consumes production canonical completion flags; it does not reimplement
    the mission/raw verifier and cannot establish acceptance from a badge or ACK.
    """
    assert isinstance(view,dict)and view.get('ok')is True and finite_age(view.get('ageMs'),1200),'FRESH_UI_OBSERVATION_REQUIRED'
    o=view.get('observation')or{};assert all(o.get(key)==binding.get(key)and binding.get(key)is not None for key in IDENTITY_KEYS),'EXACT_REFERENCE_CONTEXT_CHANGED'
    assert o.get('foreground')is True,'CURRENT_FOREGROUND_REQUIRED'
    assert isinstance(state,dict)and state.get('ok')is True,'ACTUAL_STATE_RESPONSE_REQUIRED'
    f=state.get('flight')or{};live=f.get('live')or{};request=f.get('request')or{};client=state.get('client')or{}
    assert f.get('run')==binding['run']and request.get('run')==binding['run']and request.get('boot')==binding['boot']and live.get('boot')==binding['boot'],'EXACT_LIVE_RUN_BOOT_REQUIRED'
    assert f.get('mode')=='sitl'and live.get('simulation')is True,'CURRENT_ACTUAL_SITL_REQUIRED'
    assert not f.get('error')and not f.get('writerError')and not live.get('failure'),'NOMINAL_FAILURE_REFUSED'
    assert client.get('id')==binding['clientId']and client.get('epoch')==binding['clientEpoch']and client.get('instance')==binding['clientInstance']and client.get('active')is True,'CURRENT_CLIENT_CONTEXT_REQUIRED'
    assert finite_age(client.get('ageMs'),3000)and client['ageMs']<3000,'CURRENT_CLIENT_FRESHNESS_REQUIRED'
    assert all(request.get(key)==binding[key]for key in ['modelSha256','planSha256']),'EXACT_LIVE_MODEL_PLAN_REQUIRED'
    assert finite_age(f.get('positionAgeMs'),1000)and finite_age(live.get('heartbeatAgeMs'),3000),'FRESH_CURRENT_TELEMETRY_REQUIRED'
    completion=live.get('completion')or{}
    takeoff=True
    if completion.get('takeoffAlternativeUsed')is True:
        evidence=completion.get('takeoffEvidence')or{};proof=evidence.get('proof')or{};takeoff=completion.get('completionRule')=='FIELD02_TAKEOFF01_CURRENT_CLIMB_TRANSITION_V1'and evidence.get('valid')is True and evidence.get('failed')is None and proof.get('notAckOnly')is True and proof.get('seq')==1 and proof.get('command')==22
    complete=takeoff and live.get('armed')is False and all(completion.get(key)is True for key in ['complete','autoObserved','expectedTerminalRTL','groundDisarmed','nearHome'])and completion.get('missingNavigation')==[]
    return {'eligible':complete,'run':binding['run'],'boot':binding['boot'],'armed':live.get('armed'),'canonicalCompletion':completion,'stageObserved':live.get('stage'),'modeObserved':live.get('mode'),'stageUsedAsDisarmProof':False,'sharedCanonicalCompletionConsumed':True,'authorityGranted':False,'dispatchPerformed':False}

def wait_complete_nominal(command,*,reference,state_reader,observation_reader,closure_reserve,phase_policy,dispatch,clock=time.monotonic,pause=time.sleep):
    """Future integration seam, no active installation and no internal input retry.

    Dispatch remains the existing Root-visible helper and must enforce screenshot,
    current geometry, exact context and its fresh phase_policy again before tap.
    This function calls it at most once and propagates every uncertain/error result.
    """
    binding=reference_binding(reference);assert command.get('run')==binding['run'],'COMMAND_REFERENCE_RUN_MISMATCH'
    seconds=command.get('waitSeconds',120);assert isinstance(seconds,(int,float))and not isinstance(seconds,bool)and math.isfinite(seconds)and 0<seconds<=180,'BOUNDED_WAIT180S_REQUIRED'
    ident=command.get('commandId');assert isinstance(ident,str)and re.fullmatch('[a-z0-9-]{1,58}',ident),'BOUNDED_UNIQUE_COMMAND_ID_REQUIRED'
    end=clock()+seconds;polls=0
    while clock()<end:
        polls+=1;assert polls<=721,'BOUNDED_COMPLETION_POLLS'
        closure_reserve();state=state_reader();view=observation_reader(end)
        assert clock()<end,'COMPLETION_READ_AFTER_DEADLINE_NO_INPUT'
        decision=nominal_close_decision(state,view,binding)
        if decision['eligible']:
            phase_policy(reference['observed']['observation']['phase'],view['observation'],'field-close',state)
            assert clock()<end,'COMPLETION_POLICY_AFTER_DEADLINE_NO_INPUT'
            return dispatch({'op':'action','target':'field-close','reference':command['reference'],'commandId':ident+'-close','timeout':20})
        pause(min(.25,max(0,end-clock())))
    raise AssertionError('NOMINAL_COMPLETION_TIMEOUT_NO_CLOSE_NO_RETRY')
