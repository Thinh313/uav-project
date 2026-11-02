"""Source-held Android UI driver. Read-only HTTP observations, genuine ADB events.
No public/private flight POST, JavaScript injection or synthesized authority.
"""
import base64,hashlib,json,math,re,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET,zlib
ORIGIN='http://127.0.0.1:8896'
def need(value,code):
 if not value:raise RuntimeError('PUBLIC_UI_'+code)
def geometry_point(control,viewport,web):
 need(type(control)is dict and control.get('visible')is True and control.get('enabled')is True,'TARGET_NOT_VISIBLE_ENABLED')
 need(type(viewport)is dict and type(web)is dict,'GENUINE_VIEW_GEOMETRY_REQUIRED')
 for value in[control.get(k)for k in('x','y','w','h')]+[viewport.get(k)for k in('w','h')]+[web.get(k)for k in('x','y','width','height')]:need(type(value)in(int,float)and math.isfinite(value),'GEOMETRY_FINITE_NUMBERS')
 need(viewport['w']>0 and viewport['h']>0 and web['width']>0 and web['height']>0 and control['w']>0 and control['h']>0 and 0<=control['x']<viewport['w']and 0<=control['y']<viewport['h'],'GEOMETRY_BOUNDS')
 sx=web['width']/viewport['w'];sy=web['height']/viewport['h'];need(abs(sx-sy)<=.02*max(sx,sy),'NONUNIFORM_GEOMETRY')
 x=round(web['x']+control['x']*sx);y=round(web['y']+control['y']*sy);need(0<=x<=9999 and 0<=y<=9999,'ANDROID_POINT_BOUND');return x,y
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise RuntimeError('PUBLIC_UI_REDIRECT_REFUSED')
class PublicUIDriver:
 def __init__(self,owner,case,check,*,clock=time.monotonic_ns,opener=None):
  self.owner=owner;self.case=case;self.device=case['device'];self.probe=case['native'];self.check=check;self.clock=clock;self.opener=opener or urllib.request.build_opener(NoRedirect()).open;self.events=0;self.observer_requests=0;self.instance=None;self.geometry=None;self.geometry_epoch=None;self.geometry_view_epoch=None;self.last_native=None;self.next_native=0;self.last_point=None;self.pointer=False;self.last_ui_capture=None;self.last_state_capture=None;self.active_target=None;self.target_started_ns=None;self.failure_capture_attempted=False;self.failure_capture_ref=None;self.last_action_finished_ns=None;self.last_action_kind=None;self.last_action_ref=None
 def get(self,path,max_bytes=65536):
  need(path.startswith('/api/')and not any(x in path for x in('\n','\r','#')),'READONLY_ROUTE');need(self.observer_requests<1800,'TASK_OBSERVER_HTTP1800');self.observer_requests+=1;self.check();started=self.clock()
  with self.opener(urllib.request.Request(ORIGIN+path,headers={'Cache-Control':'no-store'}),timeout=2)as response:
   need(response.status==200,'HTTP_OBSERVATION_STATUS');raw=response.read(max_bytes+1)
  ended=self.clock()
  if path.startswith('/api/ui-observation?'):self.last_ui_capture={'path':path,'startedNs':started,'receivedNs':ended,'raw':raw,'responseComplete':len(raw)<=max_bytes,'validated':False,'ageMs':None,'observation':None}
  if path.startswith('/api/state?'):self.last_state_capture={'path':path,'startedNs':started,'receivedNs':ended,'raw':raw,'responseComplete':len(raw)<=max_bytes,'validated':False,'result':None}
  need(len(raw)<=max_bytes,'OBSERVATION_BYTE_BOUND');q=json.loads(raw);return q,started,ended,raw
 def event(self,kind,data):
  self.events+=1;need(self.events<=128,'EVENT128_BOUND');self.owner.write('ui-workload-%03d.json'%self.events,{'format':'aeris-public-android-ui-observation','version':1,'sequence':self.events,'kind':kind,'rootHostNs':self.clock(),'run':self.case['context']['run'],'data':data,'flightAcceptance':False})
 def native(self,force=False):
  self.check();t=self.clock()
  if force or t>=self.next_native:
   self.last_native=self.probe.status(deadline_ns=t+10_000_000_000)
   if self.geometry is not None:
    current=self.last_native.get('webGeometry',{});rect=current.get('screen',current);need(self.last_native['processEpoch']==self.geometry_epoch and(current.get('viewEpoch')==self.geometry_view_epoch or self.geometry_view_epoch is None)and all(rect.get(k)==self.geometry[k]for k in('x','y','width','height')),'SOURCE_NATIVE_GEOMETRY_CHANGED_REBIND_REQUIRED')
   # STATUS is an optional immutable observer, never the signed input source,
   # lease renewal or 250ms clock guard. All forced reads share the probe cap.
   self.next_native=self.clock()+4_000_000_000
  return self.last_native
 def bind_geometry(self):
  status=self.native(True);web=status.get('webGeometry');need(type(web)is dict and web.get('processEpoch')==status['processEpoch'],'SOURCE_NATIVE_WEB_GEOMETRY');rect=web.get('screen',web);need(type(rect)is dict,'SOURCE_NATIVE_WEB_RECT')
  raw=self.device.command(['exec-out','uiautomator','dump','/dev/tty'],deadline_ns=self.clock()+10_000_000_000)
  a=raw.find(b'<hierarchy');b=raw.rfind(b'</hierarchy>');need(a>=0 and b>a,'UIA_XML');tree=ET.fromstring(raw[a:b+12]);bounds=[]
  for node in tree.iter('node'):
   if node.get('class')=='android.webkit.WebView'and node.get('package')==self.device.APPLICATION_PACKAGE:
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
    if m:bounds.append(tuple(map(int,m.groups())))
  expected=(rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height']);need(expected in bounds,'UIA_NATIVE_WEB_BOUNDS_JOIN');need(type(web.get('viewEpoch'))is str and len(web['viewEpoch'])<=64,'SOURCE_NATIVE_VIEW_EPOCH');self.geometry=dict(rect);self.geometry_epoch=status['processEpoch'];self.geometry_view_epoch=web['viewEpoch'];self.event('SOURCE_NATIVE_UIA_GEOMETRY',{'webGeometry':web,'UIABounds':bounds,'sourceNativeRef':self.probe.last_ref,'UIACommandRef':self.device.last_command_ref})
 def observation(self):
  need(self.geometry_epoch is not None and self.geometry_view_epoch is not None,'BIND_GENUINE_NATIVE_VIEW_BEFORE_OBSERVATION');query=urllib.parse.urlencode({'nativeViewEpoch':self.geometry_view_epoch,'nativeProcessEpoch':self.geometry_epoch});q,start,end,raw=self.get('/api/ui-observation?'+query);o=q.get('observation');need(q.get('ok')is True and type(o)is dict,'SOURCE_UI_OBSERVATION');need(o.get('foreground')is True and o.get('platform')=='ANDROID','ACTUAL_ANDROID_FOREGROUND');binding=o.get('nativeViewBinding')or{};need(binding.get('instance')==self.geometry_view_epoch and binding.get('processEpoch')==self.geometry_epoch and binding.get('sourceSHA256')==self.probe.source,'GENUINE_NATIVE_VIEW_BINDING_JOIN');age=q.get('observationAgeMs');need(type(age)in(int,float)and math.isfinite(age)and age>=0,'ORIGINAL_OBSERVATION_AGE');self.instance=o['instance'];self.last_ui_capture.update(validated=True,ageMs=age,observation=o);return o,start,end,raw,age
 def persist_failure(self,error):
  """Last ORIGINAL poll only, no HTTP/ADB refresh while disposing a failure."""
  if self.failure_capture_attempted:return self.failure_capture_ref
  self.failure_capture_attempted=True;capture=self.last_ui_capture;failed_ns=self.clock();original=b''if capture is None else capture['raw'];observation={}if capture is None else(capture['observation']or{});controls=observation.get('controls');controls=controls if type(controls)is dict else{};control=controls.get(self.active_target);control=control if type(control)is dict else{};selected={k:control[k]for k in('x','y','w','h','visible','enabled','checked')if k in control and type(control[k])in(int,float,bool)and(not isinstance(control[k],float)or math.isfinite(control[k]))};age=None if capture is None else capture['ageMs'];upper=None if capture is None or age is None else age+max(0,failed_ns-capture['startedNs'])/1e6;regions=observation.get('scrollRegions');modal=regions.get('modal')if type(regions)is dict else None;modal={k:v for k,v in modal.items()if k in('x','y','w','h','scrollTop','scrollHeight','clientHeight')and type(v)in(int,float)and math.isfinite(v)}if type(modal)is dict else None;view=observation.get('currentView');notice=observation.get('noticeText')
  body={'format':'aeris-final-original-ui-failure','version':2,'status':'FAILED_LAST_ORIGINAL_POLL_NOT_REFRESHED','failure':str(error).encode('utf-8',errors='replace')[:768].decode('utf-8',errors='ignore'),'candidateSHA256':self.owner.digest,'context':dict(self.case['context']),'target':None if self.active_target is None else str(self.active_target)[:128],'targetStartedHostNs':self.target_started_ns,'lastADBActionFinishedRootNs':self.last_action_finished_ns,'lastADBActionKind':self.last_action_kind,'lastADBActionOriginalRef':self.last_action_ref,'causalScope':'SERVER_RECEIVED_DOM_OBSERVATION_NOT_CRYPTOGRAPHIC_MOTION_ATTESTATION','failedHostNs':failed_ns,'requestPath':None if capture is None else capture['path'],'requestStartedHostNs':None if capture is None else capture['startedNs'],'responseReceivedHostNs':None if capture is None else capture['receivedNs'],'observationAgeMsAtResponse':age,'ageUpperMsAtFailure':upper,'originalResponseCapturedBytes':len(original),'originalResponseSHA256':hashlib.sha256(original).hexdigest(),'originalHTTPResponseComplete':False if capture is None else capture['responseComplete'],'originalObservationValidated':False if capture is None else capture['validated'],'sourceTargetPresent':self.active_target in controls,'sourceTargetControl':selected,'sourceCurrentView':view[:128]if type(view)is str else None,'sourceNoticeText':notice.encode('utf-8',errors='replace')[:512].decode('utf-8',errors='ignore')if type(notice)is str else None,'sourceModalOpen':observation.get('modal')if type(observation.get('modal'))is bool else None,'sourceWorkbenchBusy':observation.get('workbenchBusy')if type(observation.get('workbenchBusy'))is bool else None,'sourceModalRegion':modal,'genuineWebGeometry':self.geometry,'nativeProcessEpoch':self.geometry_epoch,'nativeViewEpoch':self.geometry_view_epoch,'nativeSourceSHA256':self.probe.source,'lastNativeOriginalRef':self.probe.last_ref,'lastADBCommandRef':self.device.last_command_ref,'noAdditionalHTTPOrADBCalls':True,'flightAcceptance':False,'originalEncoding':'ZLIB_BASE64_LOSSLESS','originalResponseZlibBase64':base64.b64encode(zlib.compress(original)).decode(),'retainedBytes':len(original),'retainedCompleteOriginalResponse':capture is not None and capture['responseComplete']}
  from .metadata_budget import encoded
  state=self.last_state_capture;state_raw=b''if state is None else state['raw'];body['lastState']=None
  if state is not None:
   result=state['result']or{};flight=result.get('flight');flight=flight if type(flight)is dict else{};live=flight.get('live');live=live if type(live)is dict else{};summary={'error':result.get('error'),'busy':result.get('busy'),'preflight':flight.get('preflight'),'liveFailure':live.get('failure')}
   try:summary=summary if len(encoded(summary))<=2048 else{'omitted':'ORIGINAL_STATE_SUMMARY_OVER2048'}
   except(ValueError,TypeError):summary={'omitted':'UNTYPED_OR_NONFINITE_ORIGINAL_STATE_SUMMARY'}
   body['lastState']={'requestPath':state['path'],'requestStartedHostNs':state['startedNs'],'responseReceivedHostNs':state['receivedNs'],'requestRoundTripMs':(state['receivedNs']-state['startedNs'])/1e6,'ageAtFailureUpperRootMs':max(0,failed_ns-state['startedNs'])/1e6,'clockScope':'ORIGINAL_ROOT_HTTP_REQUEST_RECEIPT_NO_NEW_STATE_OR_SENSOR_TIMESTAMP','originalResponseCapturedBytes':len(state_raw),'originalResponseSHA256':hashlib.sha256(state_raw).hexdigest(),'originalHTTPResponseComplete':state['responseComplete'],'originalStateResponseValidated':state['validated'],'sourceStateSummary':summary,'originalEncoding':'ZLIB_BASE64_LOSSLESS','originalResponseZlibBase64':base64.b64encode(zlib.compress(state_raw)).decode(),'retainedBytes':len(state_raw),'retainedCompleteOriginalResponse':state['responseComplete']}
  if len(encoded(body))>32768:
   for holder,source,maximum in[(body,original,16384 if state is None else 8192),*([]if state is None else[(body['lastState'],state_raw,8192)])]:
    holder.pop('originalResponseZlibBase64');prefix=source[:maximum];holder.update(originalEncoding='BASE64_INCOMPLETE_ORIGINAL_PREFIX',originalResponsePrefixBase64=base64.b64encode(prefix).decode(),retainedBytes=len(prefix),retainedSHA256=hashlib.sha256(prefix).hexdigest(),retainedCompleteOriginalResponse=False,omittedCapturedBytes=len(source)-len(prefix))
  need(len(encoded(body))<=32768,'FINAL_ORIGINAL_UI_DIAGNOSTIC32K');self.failure_capture_ref=self.owner.persist_ui_failure(body);return self.failure_capture_ref
 def complete_action(self,kind):
  self.last_action_finished_ns=self.clock();self.last_action_kind=kind;self.last_action_ref=self.device.last_command_ref
 def after_action(self,start,age):return self.last_action_finished_ns is None or start-math.ceil(age*1_000_000)>self.last_action_finished_ns
 def dispatch_headroom(self,start,age):
  # Selection reserve only: the ORIGINAL200ms pre-Popen guard still decides
  # dispatch after evidence/budget/live-guard IO. No admitted command is retried.
  return age<=100 and start+int((200-age)*1e6)-self.clock()>=100_000_000
 def state(self):
  need(self.instance is not None,'UI_INSTANCE_BEFORE_STATE');q,*_=self.get('/api/state?instance='+urllib.parse.quote(self.instance),max_bytes=131072);need(q.get('ok')is True,'STATE_RESPONSE');result=q['result']
  if self.last_state_capture is not None:self.last_state_capture.update(validated=type(result)is dict,result=result if type(result)is dict else None)
  return result
 def wait(self,predicate,*,seconds=10,description='STATE',observe_native=True,poll_seconds=.2):
  need(poll_seconds in(.2,.5),'READONLY_POLL_CADENCE');end=self.clock()+int(seconds*1e9)
  while self.clock()<end:
   self.check()
   if observe_native:self.native()
   s=self.state()
   if predicate(s):return s
   time.sleep(poll_seconds)
  raise TimeoutError('PUBLIC_UI_WAIT_'+description)
 def target(self,key,*,seconds=8):
  self.active_target=key;self.target_started_ns=self.clock();end=self.target_started_ns+int(seconds*1e9);scrolls=0
  while self.clock()<end:
   self.check();o,start,received,raw,age=self.observation();c=o.get('controls',{}).get(key);after_action=self.after_action(start,age)
   if key=='video-measure'and after_action and isinstance(o.get('videoLifecycle12'),dict)and o['videoLifecycle12'].get('terminal')is True:
    reason=o['videoLifecycle12'].get('firstStop',{}).get('reason','UNKNOWN');raise RuntimeError('PUBLIC_UI_VIDEO_STARTUP_TERMINAL:'+str(reason)[:180])
   eligible=after_action and self.dispatch_headroom(start,age)
   if eligible and c and c.get('visible')and c.get('enabled'):return c,o,start,received,raw,age
   scrolled=False
   if eligible and c and c.get('enabled')and not c.get('visible')and scrolls<8 and not self.pointer:
    region=o.get('scrollRegions',{}).get('panel')
    if region and region.get('h',0)>100 and region.get('w',0)>100:
     x=region['x']+region['w']*.5;upper=region['y']+region['h']*.25;lower=region['y']+region['h']*.75;up=c.get('y',0)>region['y']+region['h']*.5
     def point(y):return geometry_point({'x':x,'y':y,'w':1,'h':1,'visible':True,'enabled':True},o['viewport'],self.geometry)
     a=point(lower if up else upper);b=point(upper if up else lower);deadline=start+int((200-age)*1e6)
     if not self.dispatch_headroom(start,age):
      time.sleep(min(.55,max(.025,(525-age)/1000)));continue
     self.event('SCROLL_ORIGINAL_OBSERVATION',{'target':key,'points':[a,b],'originalHTTPResponseZlibBase64':base64.b64encode(zlib.compress(raw)).decode(),'originalHTTPResponseBytes':len(raw),'observationSHA256':hashlib.sha256(raw).hexdigest(),'requestStartedNs':start,'receivedNs':received,'observationAgeMs':age,'actualDispatchDeadlineNs':deadline,'gestureDurationMs':250,'previousADBActionFinishedRootNs':self.last_action_finished_ns,'previousADBActionOriginalRef':self.last_action_ref,'serverObservationLowerRootNs':start-math.ceil(age*1_000_000),'causalScope':'SERVER_RECEIVED_DOM_OBSERVATION_PRE_POPEN_DISPATCH_NOT_MOTION_ATTESTATION'})
     self.device.command(['shell','input','swipe',str(a[0]),str(a[1]),str(b[0]),str(b[1]),'250'],deadline_ns=self.clock()+3_000_000_000,dispatch_deadline_ns=deadline);self.complete_action('SCROLL');scrolls+=1;scrolled=True
   # UI observations are emitted every500ms. Rechecking at25Hz neither makes
   # them fresher nor proves a newer touch. Wait toward the next ORIGINAL
   # emission; selection reserves100ms before evidence IO and dispatch still
   # requires the unchanged200ms final AndroidDevice pre-Popen bound.
   delay=.55 if scrolled else max(.025,(525-age)/1000)if c and c.get('enabled')and c.get('visible')else .45
   time.sleep(min(.55,delay))
  raise TimeoutError('PUBLIC_UI_TARGET_NOT_READY:'+key)
 def wait_ui(self,predicate,*,seconds=8,description='STATE'):
  end=self.clock()+int(seconds*1e9)
  while self.clock()<end:
   self.check();o,start,received,raw,age=self.observation()
   if self.after_action(start,age)and age+(received-start)/1e6<=200 and predicate(o):return o
   time.sleep(min(.55,max(.025,(525-age)/1000)))
  raise TimeoutError('PUBLIC_UI_ORIGINAL_OBSERVATION_WAIT_'+description)
 def tap(self,key):
  need(not self.pointer,'UI_ACTION_WHILE_NATIVE_POINTER_ACTIVE');need(self.geometry is not None,'GEOMETRY_NOT_BOUND');end=self.clock()+8_000_000_000
  while True:
   remaining=end-self.clock();need(remaining>0,'TARGET_HEADROOM_DEADLINE');c,o,start,received,raw,age=self.target(key,seconds=remaining/1e9);x,y=geometry_point(c,o['viewport'],self.geometry);deadline=start+int((200-age)*1e6)
   if self.dispatch_headroom(start,age):break
  # Original UI observation retained before dispatch; slow evidence IO is not
  # hidden by replacing its age. Device performs a second actual-dispatch guard.
  self.event('TAP_ORIGINAL_OBSERVATION',{'target':key,'point':[x,y],'originalHTTPResponseZlibBase64':base64.b64encode(zlib.compress(raw)).decode(),'originalHTTPResponseBytes':len(raw),'sourcePlatform':o['platform'],'sourceViewport':o['viewport'],'sourceTarget':c,'observationSHA256':hashlib.sha256(raw).hexdigest(),'requestStartedNs':start,'receivedNs':received,'observationAgeMs':age,'actualDispatchDeadlineNs':deadline,'previousADBActionFinishedRootNs':self.last_action_finished_ns,'previousADBActionOriginalRef':self.last_action_ref,'serverObservationLowerRootNs':start-math.ceil(age*1_000_000),'causalScope':'SERVER_RECEIVED_DOM_OBSERVATION_NOT_CRYPTOGRAPHIC_MOTION_ATTESTATION'})
  self.device.command(['shell','input','tap',str(x),str(y)],deadline_ns=self.clock()+3_000_000_000,dispatch_deadline_ns=deadline);self.complete_action('TAP:'+key);self.last_point=(x,y);return self.device.last_command_ref
 def checked(self,key):
  c,*_=self.target(key)
  if not c.get('checked'):self.tap(key)
 def choose(self,key,label):
  self.tap(key);raw=self.device.command(['exec-out','uiautomator','dump','/dev/tty'],deadline_ns=self.clock()+10_000_000_000);a=raw.find(b'<hierarchy');b=raw.rfind(b'</hierarchy>');need(a>=0 and b>a,'CHOICE_UIA_XML');tree=ET.fromstring(raw[a:b+12]);hits=[]
  for node in tree.iter('node'):
   if node.get('package')==self.device.APPLICATION_PACKAGE and node.get('enabled')=='true'and node.get('clickable')=='true'and node.get('text')==label:
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
    if m:hits.append(tuple(map(int,m.groups())))
  need(len(hits)==1,'EXACT_ONE_NATIVE_CHOICE');l,t,r,b=hits[0];self.event('NATIVE_SELECT_ORIGINAL_UIA',{'control':key,'label':label,'bounds':hits[0],'commandRef':self.device.last_command_ref});self.device.command(['shell','input','tap',str((l+r)//2),str((t+b)//2)],deadline_ns=self.clock()+3_000_000_000);self.complete_action('NATIVE_CHOICE:'+key)
 def workspace_saved(self,*,seconds=10,after_sequence=None):
  until=self.clock()+int(seconds*1e9)
  while self.clock()<until:
   self.check();o,*_=self.observation();head=o.get('workspaceHead');plan=o.get('planSha256')
   receipt=o.get('workspaceSaveReceipt')or{};sequence=receipt.get('completionSequence')
   completed=after_sequence is None or(type(sequence)is int and sequence>after_sequence)
   if completed and type(head)is str and re.fullmatch('[a-f0-9]{64}',head)and type(plan)is str and re.fullmatch('[a-f0-9]{64}',plan):return {'head':head,'planSHA256':plan,'observation':o}
   time.sleep(.45)
  raise TimeoutError('PUBLIC_UI_WORKSPACE_HEAD_NOT_OBSERVED')
 def save_workspace(self):
  o,*_=self.observation();receipt=o.get('workspaceSaveReceipt')or{};sequence=receipt.get('completionSequence',0);need(type(sequence)is int and sequence>=0,'WORKSPACE_COMPLETION_SEQUENCE');self.tap('workspace-save');return self.workspace_saved(after_sequence=sequence)
 def pointer_event(self,action,x,y):
  need(action in('DOWN','MOVE','UP')and all(type(v)is int and 0<=v<=9999 for v in(x,y)),'POINTER_SHAPE');self.check();self.device.command(['shell','input','touchscreen','motionevent',action,str(x),str(y)],deadline_ns=self.clock()+3_000_000_000);self.complete_action('NATIVE_POINTER:'+action);self.pointer=action!='UP';return self.device.last_command_ref
 def right_pad(self):
  s=self.native(True);need(s['processEpoch']==self.geometry_epoch,'NATIVE_PROCESS_CHANGED');inp=s['input'];need(inp.get('foreground')is True and inp.get('configured')is True and inp.get('failed')is False and inp.get('closed')is False,'NATIVE_PAD_PRODUCER_NOT_READY');layout=inp.get('layout');need(type(layout)is dict,'ORIGINAL_NATIVE_PAD_LAYOUT');p=layout['right'];need(all(type(p.get(k))in(int,float)and math.isfinite(p[k])for k in('x','y','width','height'))and p['x']>=0 and p['y']>=0 and p['width']>0 and p['height']>0,'NATIVE_PAD_RECT');return(round(p['x']+p['width']/2),round(p['y']+p['height']/2),p['width'])
 def save_dialog(self):
  need(not self.pointer,'NO_SAF_WHILE_POINTER_ACTIVE');raw=self.device.command(['exec-out','uiautomator','dump','/dev/tty'],deadline_ns=self.clock()+10_000_000_000);a=raw.find(b'<hierarchy');b=raw.rfind(b'</hierarchy>');need(a>=0 and b>a,'SAF_UIA_XML');tree=ET.fromstring(raw[a:b+12]);matches=[]
  for n in tree.iter('node'):
   if n.get('package')in('com.google.android.documentsui','com.android.documentsui')and n.get('enabled')=='true'and(n.get('resource-id','').endswith('/button1')or n.get('text','').upper()in('SAVE','LƯU')):
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
    if m:matches.append(tuple(map(int,m.groups())))
  need(len(matches)==1,'EXACT_ONE_SAF_SAVE_TARGET');l,t,r,b=matches[0];self.event('SAF_SAVE_UIA',{'bounds':matches[0],'originalCommandRef':self.device.last_command_ref});self.device.command(['shell','input','tap',str((l+r)//2),str((t+b)//2)],deadline_ns=self.clock()+3_000_000_000);self.complete_action('SAF_SAVE')
