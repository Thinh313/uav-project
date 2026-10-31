"""Independent public UI geometry, readonly HTTP and late-IO dispatch tests.
No browser/ADB/device/process actor; all actuators are recording stubs."""
from pathlib import Path
import importlib.util,hashlib,json
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];source=HERE.parent/'runtime/source/aeris_runtime/public_ui_workload.py';pin=hashlib.sha256(source.read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('qa_public_ui',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);checks=[]
def outcome(fn):
 try:return {'accepted':True,'value':fn()}
 except BaseException as e:return {'accepted':False,'error':str(e)}
c={'x':100,'y':50,'w':40,'h':30,'visible':True,'enabled':True};v={'w':500,'h':250};web={'x':0,'y':20,'width':1000,'height':500}
r=outcome(lambda:m.geometry_point(c,v,web));checks.append({'id':'sourceCSScenter-converts-through-matched-native-web-scale','pass':r['accepted']and r['value']==(200,120),'result':r})
for title,control,viewport,rect in [('disabled',{**c,'enabled':False},v,web),('notvisible',{**c,'visible':False},v,web),('boolcoordinate',{**c,'x':True},v,web),('nan',{**c,'x':float('nan')},v,web),('outsideviewport',{**c,'x':501},v,web),('nonuniform',c,v,{**web,'height':750}),('zeroViewport',c,{**v,'h':0},web),('zeroNative',c,v,{**web,'width':0}),('androidpointbound',c,v,{**web,'x':9990})]:
 r=outcome(lambda:m.geometry_point(control,viewport,rect));checks.append({'id':title+'-refused','pass':not r['accepted'],'error':r.get('error')})
now=[1000000000]
class Owner:
 def __init__(self):self.delay=0
 def write(self,*a):now[0]+=self.delay
class Device:
 def __init__(self):self.sent=[];self.last_command_ref={'stub':True}
 def command(self,args,*,deadline_ns,dispatch_deadline_ns=None,**kw):
  if dispatch_deadline_ns is not None and now[0]>dispatch_deadline_ns:raise TimeoutError('NAVIGATION_ACTUAL_DISPATCH200MS')
  self.sent.append(args);return b''
class Probe:
 last_ref={'stub':True}
 def __init__(self):self.value={'processEpoch':'e','webGeometry':{'processEpoch':'e','viewEpoch':'view1','screen':web},'input':{'foreground':True,'configured':True,'closed':False,'failed':False,'pending':False,'layout':{'right':{'x':200,'y':200,'width':132,'height':132}}}}
 def status(self,**kw):return self.value
owner=Owner();device=Device();probe=Probe();d=m.PublicUIDriver(owner,{'device':device,'native':probe,'context':{'run':'qa'}},lambda:None,clock=lambda:now[0]);d.geometry=web;d.geometry_epoch='e';o={'viewport':v,'platform':'ANDROID'};d.target=lambda key:(c,o,now[0],now[0],b'{"source":"QA"}',0)
owner.delay=201000000;r=outcome(lambda:d.tap('test-control'));checks.append({'id':'evidence-IO201ms-beforetap-refuses-original-deadline-no-actuator','pass':not r['accepted']and r.get('error')=='NAVIGATION_ACTUAL_DISPATCH200MS'and len(device.sent)==0,'result':r})
owner.delay=0;r=outcome(lambda:d.tap('test-control'));checks.append({'id':'fresh-target-forwards-genuineADBtap-only','pass':r['accepted']and device.sent[-1]==['shell','input','tap','200','120'],'result':r})
class Response:
 def __init__(self,req,*,url=None,body=b'{"ok":true}',status=200):self.status=status;self.url=url or req.full_url;self.body=body
 def read(self,n):return self.body[:n]
 def geturl(self):return self.url
 def __enter__(self):return self
 def __exit__(self,*a):pass
requests=[]
def opening(req,**kw):requests.append((req.full_url,req.get_method()));return Response(req)
d.opener=opening;r=outcome(lambda:d.get('/api/ui-observation'));checks.append({'id':'HTTPobservation-always-local-GET-not-flightPOST','pass':r['accepted']and requests[-1]==('http://127.0.0.1:8896/api/ui-observation','GET')})
for path in ['https://foreign.invalid/','/api/state\nPOST /api/flight','/api/state#fragment']:
 n=len(requests);r=outcome(lambda:d.get(path));checks.append({'id':'foreign-or-invalid-observation-route-refused','path':path,'pass':not r['accepted']and len(requests)==n})
r=outcome(lambda:m.NoRedirect().redirect_request(None,None,None,None,None,None));original=m.PublicUIDriver(owner,{'device':device,'native':probe,'context':{'run':'qa'}},lambda:None);checks.append({'id':'default-opener-installs-noRedirect-handler-and-refuses-before-follow','pass':not r['accepted']and any(type(h)is m.NoRedirect for h in original.opener.__self__.handlers),'result':r})
r=outcome(d.right_pad);checks.append({'id':'genuine-ready-pad-current-native-rect-positive','pass':r['accepted']and r['value']==(266,266,132),'result':r})
for field,value in [('foreground',False),('configured',False),('failed',True),('closed',True)]:
 probe.value['input']={'foreground':True,'configured':True,'closed':False,'failed':False,'pending':False,'layout':{'right':{'x':200,'y':200,'width':132,'height':132}},field:value};r=outcome(d.right_pad);checks.append({'id':'unready-'+field+'-pad-no-pointerpoint','pass':not r['accepted'],'result':r})
# Held-out observer/call budget tests. This does not change signed input timing.
class CountingProbe(Probe):
 def __init__(self):super().__init__();self.calls=0
 def status(self,**kw):self.calls+=1;return self.value
p4=CountingProbe();q4=m.PublicUIDriver(owner,{'device':device,'native':p4,'context':{'run':'qa'}},lambda:None,clock=lambda:now[0]);t0=now[0];q4.native();now[0]=t0+3999999999;q4.native();n=p4.calls;now[0]=t0+4000000000;q4.native();q4.native(True);checks.append({'id':'STATUS4seconds-is-observer-cache-forced-read-still-source-and-no-input-invention','pass':n==1 and p4.calls==3 and q4.last_native is p4.value and 'originalHostBracket'not in p4.value['input']})
q4.opener=opening;q4.observer_requests=1799;n=len(requests);a=outcome(lambda:q4.get('/api/state'));b=outcome(lambda:q4.get('/api/state'));checks.append({'id':'TOTAL-observer-HTTP1800-refuses1801-before-open-no-reset','pass':a['accepted']and not b['accepted']and q4.observer_requests==1800 and len(requests)==n+1,'error':b.get('error')})
old_sleep=m.time.sleep
try:
 m.time.sleep=lambda seconds:now.__setitem__(0,now[0]+round(seconds*1e9))
 q5=m.PublicUIDriver(owner,{'device':device,'native':Probe(),'context':{'run':'qa'}},lambda:None,clock=lambda:now[0]);observations=[{'workspaceHead':'a'*64,'planSha256':'b'*64,'workspaceSaveReceipt':{'completionSequence':2}},{'workspaceHead':'c'*64,'planSha256':'b'*64,'workspaceSaveReceipt':{'completionSequence':3}}];seen=[]
 def observe_ack():
  o=observations.pop(0);seen.append(o);return o,now[0],now[0],b'{}',0
 q5.observation=observe_ack;a=outcome(lambda:q5.workspace_saved(after_sequence=2));checks.append({'id':'workspace-save-requires-new-completion-not-prior-cached-head','pass':a['accepted']and len(seen)==2 and a['value']['head']=='c'*64})
 q5.observation=lambda:({'workspaceHead':'a'*64,'planSha256':'b'*64,'workspaceSaveReceipt':{'completionSequence':2}},now[0],now[0],b'{}',0);a=outcome(lambda:q5.workspace_saved(after_sequence=2,seconds=1));checks.append({'id':'workspace-save-no-new-ACK-times-out-never-promotes-old-head','pass':not a['accepted'],'error':a.get('error')})
 q6=m.PublicUIDriver(owner,{'device':device,'native':Probe(),'context':{'run':'qa'}},lambda:None,clock=lambda:now[0]);calls=[0];waits=[]
 def observations_adaptive():
  calls[0]+=1;return {'viewport':v,'platform':'ANDROID','controls':{'a':c}},now[0],now[0],b'{}',400 if calls[0]==1 else 0
 q6.observation=observations_adaptive;m.time.sleep=lambda seconds:(waits.append(seconds),now.__setitem__(0,now[0]+round(seconds*1e9)));a=outcome(lambda:q6.target('a'));checks.append({'id':'target-waits-for-next-original500ms-emission-then-rechecks200ms','pass':a['accepted']and calls[0]==2 and waits==[.125]})
finally:m.time.sleep=old_sleep
report={'format':'aeris-independent-public-UI-driver-contract','version':1,'status':'PASS_GEOMETRY_AND_SOURCE_DISPATCH_STUBS_NOT_ACTUAL_UI'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'sourceChanged':pin!=hashlib.sha256(source.read_bytes()).hexdigest(),'checks':checks,'actuators':'RECORDING_STUBS_NEVER_ADB','actualAndroidUIOrControl':False};n=1;out=REPO/'evidence/betasim-integrated01/qa'
while(out/f'public-ui-{n:02}.json').exists():n+=1
p=out/f'public-ui-{n:02}.json';p.write_text(json.dumps(report,indent=2,default=lambda v:{'originalBytesHex':v.hex()}if isinstance(v,bytes)else repr(v))+'\n');print(json.dumps({'status':report['status'],'failed':[x for x in checks if not x['pass']],'groups':len(checks),'path':str(p)},default=lambda v:{'originalBytesHex':v.hex()}if isinstance(v,bytes)else repr(v)))
