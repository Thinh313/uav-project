"""Independent current native-view/cross-B/late observation refusals. No ADB."""
from pathlib import Path
import hashlib,importlib.util,json
P=Path(__file__).resolve();R=P.parents[3];source=P.parent.parent/'runtime/source/aeris_runtime/public_ui_workload.py';spec=importlib.util.spec_from_file_location('qa_bound_ui',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);pin=hashlib.sha256(source.read_bytes()).hexdigest();checks=[];now=[1000000000];sent=[]
class Device:
 last_command_ref={'stub':True}
 def command(self,*a,**kw):sent.append(a);return b''
class Probe:
 source='a'*64;last_ref={'stub':True}
 def status(self,**kw):return {'processEpoch':'native-process','webGeometry':{'viewEpoch':'native-A-view','screen':{'x':0,'y':0,'width':1000,'height':500}}}
class Owner:
 def write(self,*a):pass
def driver(value):
 d=m.PublicUIDriver(Owner(),{'device':Device(),'native':Probe(),'context':{'run':'qa'}},lambda:None,clock=lambda:now[0]);d.geometry_epoch='native-process';d.geometry_view_epoch='native-A-view';d.geometry={'x':0,'y':0,'width':1000,'height':500};d.get=lambda path:(value,now[0],now[0],b'original source HTTP fixture');return d
base={'ok':True,'observationAgeMs':1,'observation':{'instance':'browser-A','platform':'ANDROID','foreground':True,'nativeViewBinding':{'instance':'native-A-view','processEpoch':'native-process','sourceSHA256':'a'*64},'viewport':{'w':1000,'h':500},'controls':{'save':{'x':50,'y':50,'w':20,'h':20,'visible':True,'enabled':True}}}}
def attempt(id,fn,expected=True):
 try:result=fn();accepted=True;error=None
 except BaseException as e:accepted=False;error=str(e)
 checks.append({'id':id,'pass':accepted==expected,'error':error})
attempt('exact-genuine-native-view-process-source-joins-readonly-observation',lambda:driver(base).observation())
for name,value in [('B-host-platform',{'platform':'NONE','nativeViewBinding':None}),('old-native-view',{'nativeViewBinding':{**base['observation']['nativeViewBinding'],'instance':'native-old-view'}}),('wrong-process',{'nativeViewBinding':{**base['observation']['nativeViewBinding'],'processEpoch':'other-process'}}),('wrong-native-source',{'nativeViewBinding':{**base['observation']['nativeViewBinding'],'sourceSHA256':'b'*64}})]:
 q=json.loads(json.dumps(base));q['observation'].update(value);attempt(name+'-cannot-be-used-for-A-ADB-controls',lambda q=q:driver(q).observation(),False)
d=driver(base);d.geometry_view_epoch=None;attempt('unbound-genuine-native-view-refuses-before-HTTP',d.observation,False)
d=driver(base);d.geometry_view_epoch='view-retired';attempt('native-view-change-even-same-process-and-rect-refused',lambda:d.native(True),False)
old_sleep=m.time.sleep
try:
 m.time.sleep=lambda seconds:now.__setitem__(0,now[0]+round(seconds*1e9));q=json.loads(json.dumps(base));q['observationAgeMs']=201;d=driver(q);attempt('late201ms-original-view-controls-never-tapped',lambda:d.tap('save'),False);checks.append({'id':'late-and-crossB-never-sent-any-ADB','pass':not sent})
finally:m.time.sleep=old_sleep
report={'format':'aeris-independent-current-native-view-observer-bindings','version':1,'status':'PASS_BOUND_OBSERVATION_STUBS_NOT_ACTUAL_NATIVE_UI'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'checks':checks,'sourceChanged':pin!=hashlib.sha256(source.read_bytes()).hexdigest(),'actualAndroidOrHTTP':False};n=1;out=R/'evidence/betasim-integrated01/qa'
while(out/f'public-ui-bindings-{n:02}.json').exists():n+=1
p=out/f'public-ui-bindings-{n:02}.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'output':str(p)}))
