"""Contractor-only real UI sequences. Only HTTP GET observations, never flight/payload POST."""
import importlib.util,json,time,sys,math
from pathlib import Path
spec=importlib.util.spec_from_file_location('qa_android04',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

def lease_admission(state,minimum_ms=5000):
    f=state['flight'];o=state.get('payloadLeaseObservation');assert isinstance(o,dict),'CURRENT_REDACTED_LEASE_OBSERVATION_REQUIRED';assert o.get('authorityRestored')is False;assert o.get('leaseCount',0)>=1;now=o['observedAtHostMonoMs'];r=f['request'];binding=f.get('binding')or{};valid=[l for l in o['leases']if l['untilHostMonoMs']>now and l['remainingMs']>=minimum_ms and l['flightRun']==f['run'] and l['flightBoot']==r['boot'] and l['modelSha256']==binding.get('modelSha256')and l['planSha256']==binding.get('planSha256')and l['clientId']==state['client']['id']and l['clientEpoch']==state['client']['epoch']];assert valid,'NO_ACTIVE_SAME_RUN_BOOT_MODEL_CLIENT_UNEXPIRED_LEASE';return{'observation':o,'matchingLeases':valid,'flightRun':f['run'],'flightRequest':r,'client':state['client']}

def run(attempt,phase,expected_mode='sitl'):
    assert attempt in ['01','02']and phase in ['preflight-upload','arm-home','auto','payload-setup','payload-capture','reboot','nominal-close']
    assert expected_mode in ['mock','sitl'];assert phase!='reboot'or expected_mode=='sitl','REAL_REBOOT_PHASE_REQUIRES_SITL';q.owned(attempt);counter=0;rootState=q.state();initialRun=rootState['flight']['run'];assert initialRun and rootState['flight']['mode']==expected_mode and initialRun.startswith('m'if expected_mode=='mock'else's'),'EXPLICIT_EXISTING_EXPECTED_SIMULATION_MODE_REQUIRED';out=q.E/f'qa-ui-sequence-{attempt}-{expected_mode}-{initialRun}-{phase}.jsonl';assert not out.exists(),'SEQUENCE_ALREADY_RECORDED_NO_RETRY'
    def log(v):
        assert not out.exists()or out.stat().st_size<256*2**10
        with out.open('a')as f:f.write(json.dumps({'at':time.time(),'mono':time.monotonic(),'mode':expected_mode,'initialRun':initialRun,'notSITLProof':expected_mode=='mock',**v},ensure_ascii=False)+'\n')
    def observe():
        s=q.state();f=s['flight'];assert f['run']in[initialRun,None],'UNEXPECTED_RUN_SWITCH';return s
    def wait(pred,label,limit):
        end=time.monotonic()+limit
        while time.monotonic()<end:
            s=observe();f=s['flight']
            if pred(s):log({'observed':label,'flightRun':f.get('run'),'stage':(f.get('live')or{}).get('stage'),'autoGate':f.get('autoGate')});return s
            if f.get('error'):raise RuntimeError(f['error'])
            time.sleep(.15)
        raise TimeoutError(label)
    def tap(label,box=None,before=None):
        nonlocal counter
        counter+=1;name=f'android-ui-{attempt}-{expected_mode}-{initialRun}-{phase}-{counter:02d}';rows=q.ocr(attempt,name);hits=[r for r in rows if q.norm(label)in q.norm(r['text'])and r['confidence']>=.45 and(not box or box[0]<=r['x']<=box[2]and box[1]<=r['y']<=box[3])];assert len(hits)==1,{'label':label,'matches':hits};r=hits[0]
        if before:log({'immediateBeforeTap':label,'observation':before(observe())})
        x,y=round(r['x']+r['width']/2),round(r['y']+r['height']/2);assert 0<=x<1280 and 0<=y<800;q.adb('shell','input','tap',x,y);log({'uiTap':label,'OCR':r,'point':[x,y]});time.sleep(.15)
    right=(700,80,1220,680)
    if phase=='preflight-upload':
        tap('Đọc preflight',right);wait(lambda s:(s['flight'].get('live')or{}).get('preflight63',{}).get('ready')and not s['flight']['busy'],'preflight-ready',90)
        tap('Cấp quyền bay',right);wait(lambda s:bool(s['flight'].get('authority')),'explicit-flight-authority',10)
        tap('Upload / readback',right);wait(lambda s:(s['flight'].get('live')or{}).get('readback63')and not s['flight']['busy'],'readback-two-cycles',50)
        log({'result':'UPLOADED_DISARMED_START_HOST_SOURCE_AND_ANDROID_VIEWER_NOW_BEFORE_ARM'})
    elif phase=='arm-home':
        tap('Đọc preflight',right);wait(lambda s:not s['flight']['busy']and(s['flight'].get('live')or{}).get('preflight63',{}).get('ready'),'fresh-prearm-cohort',20)
        tap('Arm trên đất',right);s=wait(lambda s:(s['flight'].get('live')or{}).get('stage')=='ARMED_HOME_REVIEW'and not s['flight']['busy'],'post-arm-home-review',30);h=s['flight']['live']['homeReview'];home=h['postArmHome'];assert math.hypot((home['lat']-10.854)*111319,(home['lon']-106.807)*109300)<=1 and abs(home['amsl']-10)<=.5,'UNEXPECTED_HOME_STOP_FOR_REVIEW';log({'observedHomeReview':h,'result':'HOME_REVIEW_REQUIRES_PROMPT_EXPLICIT_AUTO_NO_GATE_EXTENSION'})
    elif phase=='auto':
        def auto_gate(s):
            f=s['flight'];assert f.get('autoGate',{}).get('eligible')is True and f['autoGate']['effectiveRemainingMs']>1800,'EXPIRED_HOME_OR_PARAMETER_GATE_NO_RETRY';return{'autoGate':f['autoGate'],'homeReviewSha256':f['live']['homeReview']['sha256']}
        tap('Duyệt Home',right,before=auto_gate);wait(lambda s:(s['flight'].get('live')or{}).get('stage')in['AUTO','FLYING','COMPLETED','RTL','GROUND']or(s['flight'].get('live')or{}).get('autoObserved'),'AUTO-observed',20);log({'result':'AUTO_UI_OBSERVED_NOT_MISSION_ACCEPTANCE'})
    elif phase=='payload-setup':
        # Contractor first selects visible Payload tab; no hidden tab state is injected.
        tap('Discovery payload',right);tap('Chọn payload',right);tap('Cấp quyền 60 giây',right)
        def ready(s):
            try:return bool(lease_admission(s))
            except AssertionError:return False
        s=wait(ready,'active-payload-lease',5);log({'activeLease':lease_admission(s),'result':'LEASE_60S_REAL_TIME_EXPIRY_NO_EXTENSION'})
    elif phase=='payload-capture':
        # Contractor may scroll visible right console if either uniquely named button is outside viewport.
        lease_admission(observe());tap('Đặt góc & đọc mock',right);log({'gimbalReadbackRequested':'ROOT_MUST_RETAIN_RESULT_OR_WAL_NOT_ACK_AS_EXECUTION'})
        tap('Chụp khung đã giải mã',right);log({'captureRequested':'ROOT_MUST_VERIFY_FRESH_NETWORK_FRAME_SAME_FEED_AND_RAW_CONTEXT','actualImages':0})
    elif phase=='reboot':
        # Contractor first exposes fault disclosure and keeps reboot button visible via actual UI.
        def fault_gate(s):
            f=s['flight'];assert(f.get('live')or{}).get('armed')is True and(f.get('latestPosition')or{}).get('relativeHomeM',0)>5 and f.get('positionAgeMs',9999)<1000,'AIRBORNE_FRESH_FLIGHT_REQUIRED';return lease_admission(s)
        tap('Restart tiến trình AP',right,before=fault_gate);s=wait(lambda s:not s['flight']['run']and not s['flight']['busy'],'fault-session-closed',60);o=s['payloadLeaseObservation'];assert o['leaseCount']==0 and not o['leases'],'POSTFAULT_LEASES_NOT_ZERO';last=s['payloadAuthority']['last'];assert last['reason']=='FLIGHT_REBOOT' and last['pre']['leaseCount']>=1 and last['post']['leaseCount']==0;assert all(l['untilHostMonoMs']>last['pre']['observedAtHostMonoMs']for l in last['pre']['leases']),'LEASE_ALREADY_EXPIRED_BEFORE_FAULT';assert not s['flight'].get('authority');log({'postFault':{'payloadLeaseObservation':o,'durableRevocation':last,'flight':s['flight']},'result':'UI_REBOOT_CLOSED_REQUIRES_INDEPENDENT_RAW_PID_AND_RECEIPT_ORDER_VERIFICATION'})
    elif phase=='nominal-close':
        s=wait(lambda s:(s['flight'].get('live')or{}).get('completion',{}).get('complete')is True,'navigation-RTL-ground-disarm-observed',540);tap('Đóng hồ sơ sau hạ cánh',right);s=wait(lambda s:not s['flight']['run']and not s['flight']['busy'],'nominal-run-closed',25);assert s['flight']['lastReview']['accepted']is True,'REVIEW_NOT_ACCEPTED';log({'review':s['flight']['lastReview'],'result':'UI_CLOSED_REQUIRES_INDEPENDENT_RAW_REPLAY'})
    q.capture(attempt,f'android-ui-{attempt}-{expected_mode}-{initialRun}-{phase}-final')

if __name__=='__main__':
    assert len(sys.argv)in[3,4]and(len(sys.argv)==3 or sys.argv[3]=='--mock'),'ATTEMPT_PHASE_OPTIONAL_EXPLICIT_MOCK_REQUIRED';run(sys.argv[1],sys.argv[2],'mock'if len(sys.argv)==4 else'sitl')
