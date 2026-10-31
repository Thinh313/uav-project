"""Contractor-only visible tap harness. No eval, UIAutomator, control POST or retries.
Root must inspect --prepare screenshot, then --sequence uses that reference only if
current geometry/document/viewport still matches. Fresh screenshot per dispatch.
"""
from pathlib import Path
import importlib.util,json,urllib.request,urllib.error,time,hashlib,sys,os,math,base64,struct,re
spec=importlib.util.spec_from_file_location('q05',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

MAX_OBSERVATION_HTTP_BYTES=64*2**10
MAX_REDACTED_OBSERVATION_CHARS=64*2**10

def redacted_http_diagnostic(raw,*,status=None,elapsed_ms=None,overflow=False,error=None):
    """Keep the actual bounded response prefix and digest; redact credential fields.
    This diagnostic never supplies a fresh observation or relaxes the1200ms policy.
    """
    assert isinstance(raw,bytes)and len(raw)<=MAX_OBSERVATION_HTTP_BYTES
    def safe(value):
        if isinstance(value,dict):return {k:('[REDACTED]'if re.search(r'token|csrf|authorization|cookie|password|secret',str(k),re.I)else safe(v))for k,v in value.items()}
        if isinstance(value,list):return [safe(v)for v in value]
        if isinstance(value,str):
            value=re.sub(r'(?i)Bearer\s+[^\s"<>]+','Bearer [REDACTED]',value)
            return re.sub(r'(?i)(token|csrf|secret|password|authorization)([\s:=]+)[^\s,}]+',r'\1\2[REDACTED]',value)
        return value
    try:
        parsed=json.loads(raw);redacted=safe(parsed);body=json.dumps(redacted,separators=(',',':'),ensure_ascii=False);body_kind='PARSED_RESPONSE_REDACTED'
        age=parsed.get('ageMs')if isinstance(parsed,dict)else None
        if not isinstance(age,(int,float))or isinstance(age,bool)or not math.isfinite(age):age=None
    except (ValueError,UnicodeError,RecursionError):
        body='[UNPARSEABLE_OR_TRUNCATED_BODY_NOT_RETAINED: SHA256_AND_BYTE_COUNT_ONLY]';body_kind='UNPARSEABLE_RESPONSE_PREFIX_SHA_AND_COUNT_ONLY';age=None
    clipped=len(body)>MAX_REDACTED_OBSERVATION_CHARS;body=body[:MAX_REDACTED_OBSERVATION_CHARS]
    return {'classification':'ACTUAL_HTTP_RESPONSE_PREFIX_REDACTED_NOT_FRESHNESS_ACCEPTANCE','httpStatus':status,'requestElapsedPythonMs':elapsed_ms if isinstance(elapsed_ms,(int,float))and not isinstance(elapsed_ms,bool)and math.isfinite(elapsed_ms)else None,'responsePrefixBytes':len(raw),'responsePrefixSha256':hashlib.sha256(raw).hexdigest(),'responseOverflow':overflow,'rawResponseAgeMs':age,'bodyKind':body_kind,'bodyRedacted':body,'redactedBodyClipped':clipped,'errorClass':error.split(':',1)[0][:64]if isinstance(error,str)else None,'maximumCapturedBytes':MAX_OBSERVATION_HTTP_BYTES,'freshnessBoundMsUnchanged':1200}

def observation():
    raw=b'';status=None;overflow=False;started=time.monotonic()
    try:
        with urllib.request.urlopen('http://127.0.0.1:8872/api/ui-observation',timeout=2)as r:
            status=r.status;data=r.read(MAX_OBSERVATION_HTTP_BYTES+1);overflow=len(data)>MAX_OBSERVATION_HTTP_BYTES;raw=data[:MAX_OBSERVATION_HTTP_BYTES]
        assert not overflow,'OBSERVATION_HTTP_BOUND64KIB'
        v=json.loads(raw);assert v.get('ok')and v.get('observation'),'OBSERVATION_REQUIRED'
        assert isinstance(v.get('ageMs'),(int,float))and not isinstance(v.get('ageMs'),bool)and math.isfinite(v['ageMs'])and 0<=v['ageMs']<=1200,'STALE_OBSERVATION'
        return v
    except BaseException as e:
        if isinstance(e,urllib.error.HTTPError)and not raw:
            status=e.code
            try:
                data=e.read(MAX_OBSERVATION_HTTP_BYTES+1);overflow=len(data)>MAX_OBSERVATION_HTTP_BYTES;raw=data[:MAX_OBSERVATION_HTTP_BYTES]
            except BaseException:pass
        e.raw_observation_diagnostic=redacted_http_diagnostic(raw,status=status,elapsed_ms=(time.monotonic()-started)*1000,overflow=overflow,error=type(e).__name__);raise

def receipt_observation(deadline,reader=None,clock=time.monotonic,pause=time.sleep):
    reader=reader or observation
    while clock()<deadline:
        try:
            value=reader()
            if clock()>=deadline:
                e=AssertionError('RECEIPT_AFTER_EXISTING_DEADLINE_NO_REINPUT');e.late_observation=value;raise e
            return value
        except AssertionError as e:
            if str(e)!='STALE_OBSERVATION':raise
            pause(min(.08,max(0,deadline-clock())))
    raise AssertionError('STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT')

def post_tap_context(origin,current,ident):
    assert all(current.get(k)==origin.get(k)for k in['documentId','clientId','clientEpoch','clientInstance','modelSha256','planSha256','configId']),'POST_TAP_CONTEXT_CHANGED_NO_REINPUT'
    transition=ident in['field-connect','field-close','field-reboot','field-cut']
    assert current.get('boot')==origin.get('boot')or transition,'POST_TAP_BOOT_CHANGED_NO_ADVANCE'
    assert current.get('run')==origin.get('run')or transition,'CURRENT_RUN_CHANGED_NO_ADVANCE'

def receipt_context(origin,current,receipt,ident):
    post_tap_context(origin,current,ident)
    assert all(receipt.get(k)==origin.get(k)for k in['documentId','run','boot','clientId','clientEpoch','clientInstance','modelSha256','planSha256']),'RECEIPT_CONTEXT_MISMATCH_NO_RETRY'

def target(v,ident,phase=None):
    o=v['observation'];assert o['format']=='clockvideo05-ui-observation-v1'and o['foreground'],'FOREGROUND_OBSERVATION_REQUIRED'
    if phase is not None:assert o['phase']==phase,'PHASE_CHANGED'
    a=[t for t in o['targets']if t['id']==ident];assert len(a)==1,'TARGET_NOT_UNIQUE';t=a[0];assert all(t.get(k)is True for k in['enabled','visible','fullyVisible','unoccluded']),'TARGET_UNAVAILABLE_OR_OCCLUDED'
    r=t['rect'];assert all(isinstance(r[k],(int,float))and math.isfinite(r[k])for k in['x','y','width','height']);assert r['width']>=44 and r['height']>=44 and r['x']>=0 and r['y']>=0 and r['x']+r['width']<=o['viewport']['width']and r['y']+r['height']<=o['viewport']['height'],'TARGET_BOUNDS'
    return t

def png_size(path):
    b=Path(path).read_bytes();assert b.startswith(b'\x89PNG\r\n\x1a\n')and len(b)>=24,'PNG_HEADER_REQUIRED';return list(struct.unpack('>II',b[16:24]))

def window_frame_signature(text):
    focus=re.findall(r'^\s*mCurrentFocus=(.+)$',text,re.M);assert len(focus)==1 and 'vn.rtr.aeris.field02' in focus[0]and 'ShellActivity'in focus[0],'OWNED_SHELL_NOT_FOCUSED';blocks=re.split(r'(?=^\s*Window #\d+ Window\{)',text,flags=re.M);blocks=[b for b in blocks if re.search(r'^\s*Window #\d+ Window\{[^\n]*vn\.rtr\.aeris\.field02[^\n]*ShellActivity',b,re.M)];assert len(blocks)==1,'OWNED_SHELL_WINDOW_NOT_UNIQUE';header=re.search(r'^\s*Window #\d+ (Window\{[^}\n]+\})',blocks[0],re.M);assert header and header.group(1)==focus[0].strip(),'NATIVE_FOCUS_FRAME_WINDOW_GENERATION_MISMATCH';lines=[x.strip()for x in blocks[0].splitlines()if re.match(r'^\s*(?:mFrame=|mContentFrame=|mCompatFrame=|mFrames:|Frames:)',x)];assert lines,'OWNED_NATIVE_FRAME_LINES_REQUIRED';return {'focusedWindow':focus[0].strip(),'lines':lines,'sha256':hashlib.sha256('\n'.join(lines).encode()).hexdigest()}

def window_snapshot_signature(full_text,windows_text):
    focus=re.findall(r'^\s*mCurrentFocus=(.+)$',full_text,re.M);assert len(focus)==1,'NATIVE_FOCUS_LINE_REQUIRED';return window_frame_signature('mCurrentFocus='+focus[0]+'\n'+windows_text)

def ground_frame_signature():
    full=q.adb('shell','dumpsys','window',timeout=3);frames=q.adb('shell','dumpsys','window','windows',timeout=3);assert len(full)<=2**20 and len(frames)<=2**20,'WINDOW_DUMP_BOUND';return window_snapshot_signature(full.decode('utf-8',errors='strict'),frames.decode('utf-8',errors='strict'))

def mapping(viewport,frame,screen):
    assert isinstance(frame,list)and len(frame)==4 and all(isinstance(x,int)for x in frame),'ROOT_GROUND_NATIVE_FRAME_REQUIRED';x,y,r,b=frame;assert 0<=x<r<=screen[0]and 0<=y<b<=screen[1],'NATIVE_FRAME_SCREEN_BOUNDS';sx=(r-x)/viewport['width'];sy=(b-y)/viewport['height'];assert math.isfinite(sx)and math.isfinite(sy)and sx>0 and abs(sx-sy)<=.01 and abs(sx-viewport['dpr'])<=.02,'CSS_NATIVE_SCALE_MISMATCH';return {'frame':frame,'screen':screen,'cssViewport':viewport,'scaleX':sx,'scaleY':sy,'basis':'ROOT_DECLARED_GROUND_FRAME_BOUND_TO_ACTUAL_SCREENSHOT_AND_NATIVE_WINDOW_LINES'}

def native_point(rect,m):return [round(m['frame'][0]+(rect['x']+rect['width']/2)*m['scaleX']),round(m['frame'][1]+(rect['y']+rect['height']/2)*m['scaleY'])]

def workspace_document(ws):
    assert isinstance(ws,dict)and ws.get('ok')is True and ws.get('pending')is False and isinstance(ws.get('bodyBase64'),str)and len(ws['bodyBase64'])<=1600000,'WORKSPACE_WIRE_BODY_REQUIRED'
    raw=base64.b64decode(ws['bodyBase64'],validate=True);assert len(raw)<=1200000 and base64.b64encode(raw).decode()==ws['bodyBase64'],'WORKSPACE_CANONICAL_BASE64_BOUND';doc=json.loads(raw.decode('utf-8'));assert isinstance(doc,dict)and isinstance(doc.get('mission'),dict)and isinstance(doc['mission'].get('sha256'),str),'WORKSPACE_DOCUMENT_REQUIRED';return doc

def phase_policy(reference_phase,o,ident,s):
    f=s['flight'];l=f.get('live')or{};phase=o['phase'];assert phase==(l.get('stage')or'IDLE'),'STATE_OBSERVATION_PHASE_MISMATCH'
    age=f.get('positionAgeMs');fresh=isinstance(age,(int,float))and 0<=age<=1000
    airborne=fresh and l.get('stage')=='AUTO'and l.get('mode')=='AUTO'and l.get('armed')is True and(f.get('latestPosition')or{}).get('relativeHomeM',-1)>5
    def exact_lease():
        a=s.get('payloadLeaseObservation')or{};return any(x.get('flightRun')==o['run']and x.get('flightBoot')==o['boot']and x.get('modelSha256')==o['modelSha256']and x.get('planSha256')==o['planSha256']and x.get('clientId')==o['clientId']and x.get('clientEpoch')==o['clientEpoch']and x.get('clientInstance')==o['clientInstance']and x.get('stationId')==o['payloadSelection']['stationId']and x.get('payloadId')==o['payloadSelection']['deviceId']and x.get('untilHostMonoMs',0)>a.get('observedAtHostMonoMs',float('inf'))and x.get('remainingMs',0)>=5000 for x in a.get('leases',[]))
    if ident=='field-arm':assert phase=='DISARMED'and l.get('readback63')and f.get('authority'),'ARM_GROUND_READBACK_AUTHORITY_REQUIRED'
    if ident=='field-auto':assert phase=='ARMED_HOME_REVIEW'and f['autoGate']['eligible']and f['autoGate']['effectiveRemainingMs']>1800,'HOME_GATE_1800MS'
    if ident in['video-measure','video-capture','video-pause','field-gimbal','field-capture','field-reboot','field-cut']:assert airborne,'CURRENT_AIRBORNE_AUTO_REQUIRED'
    if ident in['video-capture','field-gimbal','field-capture','field-reboot','field-cut']:assert exact_lease(),'CURRENT_EXACT_LIVE_LEASE_REQUIRED'
    if ident=='field-close':assert fresh and l.get('armed')is False and(l.get('completion')or{}).get('complete')and(l.get('completion')or{}).get('groundDisarmed'),'COMPLETED_GROUND_DISARM_REQUIRED'
    if reference_phase==phase:return
    if reference_phase=='DISARMED'and phase=='ARMED_HOME_REVIEW'and ident=='field-auto':return
    if reference_phase=='DISARMED'and phase=='AUTO':
        if ident in['video-measure','video-capture','video-pause','field-gimbal','field-capture','field-reboot','field-cut']and airborne:return
        if ident in['video-save','field-close','field-tab-flight','field-tab-payload','field-tab-review']and fresh and(airborne or l.get('mode')=='RTL'or l.get('armed')is False):return
    raise AssertionError('REFERENCE_PHASE_TRANSITION_FORBIDDEN')

def put(name,v):
    p=q.E/(name+'.json');p.open('x').write(json.dumps(v,ensure_ascii=False,indent=2)+'\n');return p

def prepare(attempt,name,native_frame):
    deadline=time.monotonic()+5;v=receipt_observation(deadline);image=q.capture(attempt,name);v2=receipt_observation(deadline);assert v2['observation']['documentId']==v['observation']['documentId'];native_mapping=mapping(v2['observation']['viewport'],native_frame,png_size(image));native_window=ground_frame_signature();return put(name+'-reference',{'image':str(image),'imageSha256':hashlib.sha256(image.read_bytes()).hexdigest(),'observed':v2,'nativeMapping':native_mapping,'nativeWindow':native_window,'instruction':'Root must inspect this screenshot before dispatch; no action sent.'})

def dispatch(attempt,reference,ident,name,timeout=12,before_input=None,after_input=None,handoff_only=False,diagnostic_only=False):
    if diagnostic_only:assert ident=='field-qa-bad-sha','NATIVE_DIAGNOSTIC_SINGLE_TARGET_ONLY'
    if handoff_only:assert ident in ['field-export-workspace','field-import-workspace']or re.fullmatch(r'field-raw-s[a-f0-9]{20}|field-capture-export-[a-zA-Z0-9-]{1,48}-[a-f0-9]{12}|field-delivery-file-s[a-f0-9]{20}-[a-zA-Z0-9-]{1,64}',ident),'NATIVE_PICKER_HANDOFF_ALLOWLIST'
    if ident in ['field-connect','field-arm']:assert callable(before_input)and callable(after_input),'PERSISTENT_CONTROLLER_INPUT_FENCE_REQUIRED'
    assert re.fullmatch(r'field-(?:raw|delivery)-s[a-f0-9]{20}|field-capture-export-[a-zA-Z0-9-]{1,48}-[a-f0-9]{12}|field-delivery-file-s[a-f0-9]{20}-[a-zA-Z0-9-]{1,64}',ident)or ident in ['field-tab-flight','field-tab-payload','field-tab-review','field-connect','field-preflight','field-grant','field-upload','field-arm','field-auto','field-close','field-revoke','field-cut','field-reboot','field-abort','field-discover','field-select','field-pgrant','field-prevoke','field-gimbal','field-capture','field-iso','field-old-context','field-qa-bad-sha','field-export-workspace','field-import-workspace','video-start','video-stop','video-measure','video-pause','video-save','video-capture'],'VISIBLE_ACTION_ALLOWLIST';ref=json.loads(Path(reference).read_text());assert hashlib.sha256(Path(ref['image']).read_bytes()).hexdigest()==ref['imageSha256'],'REFERENCE_IMAGE_CHANGED';old=ref['observed']['observation'];v=observation();o=v['observation'];assert o['documentId']==old['documentId']and o['viewport']==old['viewport']and o['tab']==old['tab']and all(o.get(k)==old.get(k)for k in['clientId','clientEpoch','clientInstance','run','boot','configId','modelSha256','planSha256']),'REFERENCE_CONTEXT_CHANGED'
    t=target(v,ident);prior=[x for x in old['targets']if x['id']==ident];assert len(prior)==1 and prior[0]['visible']and prior[0]['fullyVisible']and prior[0]['unoccluded'],'REFERENCE_TARGET_NOT_VISIBLE'
    assert all(abs(t['rect'][k]-prior[0]['rect'][k])<=1 for k in t['rect']),'REFERENCE_GEOMETRY_CHANGED'
    s=q.state();assert (s['flight'].get('run')or None)==o['run']and s['client']['epoch']==o['clientEpoch']and s['client']['id']==o['clientId']and s['client']['instance']==o['clientInstance'],'LIVE_CONTEXT_CHANGED'
    doc=workspace_document(s['workspace']);assert doc['mission']['sha256']==o.get('modelSha256')and(doc.get('compiled')or{}).get('plan',{}).get('sha256')==o.get('planSha256'),'WORKSPACE_CONTEXT_CHANGED'
    phase_policy(old['phase'],o,ident,s)
    image=q.capture(attempt,name+'-before');native_mapping=mapping(o['viewport'],ref['nativeMapping']['frame'],png_size(image));assert native_mapping==ref['nativeMapping'],'NATIVE_MAPPING_CHANGED';assert ground_frame_signature()==ref['nativeWindow'],'NATIVE_WINDOW_INSETS_CHANGED';latest=observation();t2=target(latest,ident,o['phase']);n=latest['observation'];assert n['documentId']==o['documentId']and n['clientEpoch']==o['clientEpoch']and n['clientId']==o['clientId']and n['clientInstance']==o['clientInstance']and n['run']==o['run']and all(n.get(k)==o.get(k)for k in['boot','configId','modelSha256','planSha256'])and t2['rect']==t['rect'],'GEOMETRY_OR_CONTEXT_CHANGED_DURING_SCREENSHOT'
    fresh=q.state();assert (fresh['flight'].get('run')or None)==n['run']and(fresh['flight'].get('request')or{}).get('boot')==n['boot']and fresh['client']['id']==n['clientId']and fresh['client']['epoch']==n['clientEpoch']and fresh['client']['instance']==n['clientInstance'],'LIVE_CONTEXT_CHANGED_BEFORE_TAP';phase_policy(old['phase'],n,ident,fresh);previous=(n.get('receipt')or{}).get('id');intent={'status':'ONE_VISIBLE_DISPATCH_INTENT','id':ident,'observation':latest,'screenshot':str(image),'screenshotSha256':hashlib.sha256(image.read_bytes()).hexdigest(),'reference':str(reference),'noAutomaticRetry':True};put(name+'-intent',intent)
    r=t2['rect'];point=native_point(r,native_mapping);
    if before_input is not None:before_input(ident,latest,fresh)
    q.adb('shell','input','tap',*point);
    if after_input is not None:after_input(ident,latest)
    if diagnostic_only:
        result={'status':'ONE_NATIVE_DIAGNOSTIC_INPUT_NOT_RESULT','targetId':ident,'inputPoint':point,'noAutomaticRetry':True,'actualNativeCallbackRequired':True};put(name+'-diagnostic-input',result);return result
    if handoff_only:
        assert ident in ['field-export-workspace','field-import-workspace']or re.fullmatch(r'field-raw-s[a-f0-9]{20}|field-capture-export-[a-zA-Z0-9-]{1,48}-[a-f0-9]{12}|field-delivery-file-s[a-f0-9]{20}-[a-zA-Z0-9-]{1,64}',ident),'NATIVE_PICKER_HANDOFF_ALLOWLIST';result={'status':'ONE_NATIVE_HANDOFF_INPUT_NOT_COMPLETED','targetId':ident,'inputPoint':point,'noAutomaticRetry':True,'requiresActualPickerNativeJournalCallbackAndReceiver':True};put(name+'-handoff',result);return result
    deadline=time.monotonic()+timeout;receipt=None;late_observation=None
    while time.monotonic()<deadline:
        try:v=receipt_observation(deadline)
        except AssertionError as e:
            if str(e)in['STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT','RECEIPT_AFTER_EXISTING_DEADLINE_NO_REINPUT']:
                late_observation=getattr(e,'late_observation',None);break
            raise
        n=v['observation'];receipt=n.get('receipt');post_tap_context(o,n,ident)
        if receipt and receipt['id']!=previous and receipt['targetId']==ident:
            receipt_context(o,n,receipt,ident)
            assert receipt['status']!='UNCERTAIN','DISPATCH_UNCERTAIN_NO_RETRY'
            if receipt['status']in['ACKNOWLEDGED','REJECTED']:
                put(name+'-receipt',{'observation':v,'receipt':receipt,'notFlightAcceptance':True});assert receipt['status']=='ACKNOWLEDGED','ACTION_REJECTED_NO_ADVANCE';return receipt
        time.sleep(.08)
    put(name+'-uncertain',{'status':'NO_MATCHED_RECEIPT_NO_RETRY','lastReceipt':receipt,'lateObservation':late_observation,'originalDeadlineExpired':time.monotonic()>=deadline});raise AssertionError('NO_MATCHED_RECEIPT_NO_RETRY')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','sequence']);p.add_argument('attempt',choices=['08','09']);p.add_argument('reference_or_name');p.add_argument('prefix',nargs='?');p.add_argument('targets',nargs='*');p.add_argument('--timeout',type=float,default=12);p.add_argument('--native-frame',nargs=4,type=int);a=p.parse_args();assert 0<a.timeout<=100,'TIMEOUT_BOUND100S'
    if a.mode=='prepare':assert a.prefix is None and not a.targets;assert a.native_frame is not None,'GROUND_NATIVE_FRAME_REQUIRED';print(prepare(a.attempt,a.reference_or_name,a.native_frame))
    else:
        assert a.prefix and a.targets,'EXPLICIT_TARGET_SEQUENCE_REQUIRED'
        for i,ident in enumerate(a.targets):print(json.dumps(dispatch(a.attempt,a.reference_or_name,ident,a.prefix+'-'+str(i),timeout=a.timeout),ensure_ascii=False))
