"""Original-age post-action barriers and semantic UI predicates, no actors."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,hashlib,json,os,re,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.public_ui_workload import PublicUIDriver
from aeris_runtime.metadata_budget import encoded
class Device:
 def __init__(self,now):self.now=now;self.calls=[];self.kwargs=[];self.last_command_ref=None
 def command(self,args,**kwargs):self.calls.append(args);self.kwargs.append(kwargs);self.now[0]+=10_000_000;self.last_command_ref={'source':'MOCK_COMMAND_ONLY','n':len(self.calls)};return b''
def fixture(rows):
 now=[1_000_000_000];d=Device(now);o=SimpleNamespace();probe=SimpleNamespace();ui=PublicUIDriver(o,{'device':d,'native':probe},lambda:None,clock=lambda:now[0]);ui.geometry={'x':0,'y':0,'width':1280,'height':800};seen=[];rows=list(rows)
 def observation():
  spec=rows.pop(0);start=now[0];age=spec.get('age',10);q={'instance':'mock','platform':'ANDROID','viewport':{'w':1280,'h':800},'controls':{'datum':{'x':20,'y':30,'w':40,'h':50,'visible':spec.get('visible',True),'enabled':True}},**spec};raw=encoded(q);seen.append(q);return q,start,start+1,raw,age
 ui.observation=observation;ui.event=lambda *args:None
 return ui,d,now,seen

def main():
 groups=[]
 ui,d,now,seen=fixture([{'age':20,'tag':'PRE_ACTION'},{'age':10,'tag':'POST_ACTION'}]);ui.last_action_finished_ns=990_000_000
 with patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda seconds:now.__setitem__(0,now[0]+int(seconds*1e9))):row=ui.target('datum')
 assert row[1]['tag']=='POST_ACTION'and len(seen)==2 and not d.calls
 ui.last_action_finished_ns=100;assert ui.after_action(101,0.0000004)is False and ui.after_action(102,0.0000004)is True;groups.append('visible-enabled-under200ms-preaction-server-snapshot-rejected-conservative-ceil-boundary-no-ADB')
 ui,d,now,seen=fixture([{'age':20,'planSha256':'a'*64,'modal':False,'workbenchBusy':False},{'age':10,'planSha256':'b'*64,'modal':False,'workbenchBusy':True},{'age':10,'planSha256':'b'*64,'modal':False,'workbenchBusy':False}]);ui.last_action_finished_ns=990_000_000
 with patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda seconds:now.__setitem__(0,now[0]+int(seconds*1e9))):q=ui.wait_ui(lambda o:o.get('modal')is False and o.get('workbenchBusy')is False and o.get('planSha256')=='b'*64,description='COMPILE')
 assert len(seen)==3 and q['planSha256']=='b'*64 and not d.calls;groups.append('compile-predicate-waits-post-action-original-planSHA-modalclosed-notbusy-with-no-extra-nativecalls')
 ui,d,now,seen=fixture([{'age':20,'visible':False},{'age':10,'visible':True}]);ui.last_action_finished_ns=990_000_000
 with patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda seconds:now.__setitem__(0,now[0]+int(seconds*1e9))):ui.target('datum')
 assert not d.calls;groups.append('no-scroll-from-preaction-stale-invisible-control')
 ui,d,now,seen=fixture([{'age':1000,'visible':False,'scrollRegions':{'panel':{'x':0,'y':0,'w':500,'h':500}}},{'age':10,'visible':True}]);ui.last_action_finished_ns=-1
 with patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda seconds:now.__setitem__(0,now[0]+int(seconds*1e9))):ui.target('datum')
 assert len(seen)==2 and not d.calls;groups.append('post-action-but1000ms-old-hidden-control-never-dispatches-scroll')
 ui,d,now,seen=fixture([{'age':10,'visible':False,'scrollRegions':{'panel':{'x':0,'y':0,'w':500,'h':500}}},{'age':10,'visible':True}]);ui.last_action_finished_ns=900_000_000;events=[];ui.event=lambda kind,data:events.append((kind,data))
 with patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda seconds:now.__setitem__(0,now[0]+int(seconds*1e9))):ui.target('datum')
 assert len(d.calls)==1 and d.calls[0][-1]=='250'and d.kwargs[0]['dispatch_deadline_ns']==1_190_000_000 and events[0][0]=='SCROLL_ORIGINAL_OBSERVATION'and events[0][1]['actualDispatchDeadlineNs']==d.kwargs[0]['dispatch_deadline_ns'];groups.append('fresh-scroll-originalsnapshot-deadline-retained-and-forwarded-to-actualSDK-dispatchguard')
 ui,d,now,seen=fixture([{'age':10}]);ui.last_action_finished_ns=900_000_000;ui.tap('datum');assert ui.last_action_finished_ns==1_010_000_000 and ui.last_action_ref==d.last_command_ref and ui.last_action_kind=='TAP:datum';ui.pointer_event('DOWN',50,60);assert ui.last_action_kind=='NATIVE_POINTER:DOWN'and ui.last_action_finished_ns==1_020_000_000;ui.pointer_event('UP',50,60);assert ui.last_action_kind=='NATIVE_POINTER:UP'and ui.pointer is False;groups.append('successful-ADB-tap-and-pointer-record-source-return-clock-ref-only-aftercommand')
 source=ast.parse((T/'source/aeris_runtime/public_ui_workload.py').read_bytes());cls=next(n for n in source.body if isinstance(n,ast.ClassDef)and n.name=='PublicUIDriver')
 for name in('target','tap','choose','pointer_event','save_dialog'):
  method=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name==name);assert any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='complete_action'for n in ast.walk(method)),name
 old=(T/'scenario_driver.py').read_text();new=(T/'scenario-ui06.py').read_text();assert "ui.wait_ui"not in old and new.count('ui.wait_ui')==2 and 'FIXTURE_MODEL_AND_MODAL'in new and 'COMPILE_COMPLETED'in new;groups.append('all-mutating-ADB-paths-covered-newscenario-only-two-finite-state-waits-oldexternaldriver-unchanged')
 scenario=ast.parse(new);calls=[n for n in ast.walk(scenario)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='wait_ui'];assert len(calls)==2;predicates={next(k.value.value for k in n.keywords if k.arg=='description'):eval(compile(ast.Expression(n.args[0]),str(T/'scenario-ui06.py'),'eval'),{'re':re})for n in calls};fixture_ready=predicates['FIXTURE_MODEL_AND_MODAL'];compile_ready=predicates['COMPILE_COMPLETED'];base={'currentView':'plan','modal':False,'workbenchBusy':False,'planSha256':None};assert fixture_ready(base)and not compile_ready(base);assert compile_ready({**base,'planSha256':'a'*64})and not fixture_ready({**base,'planSha256':'a'*64})
 for change in({'currentView':'review'},{'modal':True},{'workbenchBusy':True},{'modal':None},{'workbenchBusy':None}):assert not fixture_ready({**base,**change})and not compile_ready({**base,'planSha256':'a'*64,**change})
 for bad in('a'*63,'A'*64,False,1,None):assert not compile_ready({**base,'planSha256':bad})
 groups.append('actual-versioned-scenario-lambda-predicates-test-all-exactmodal-busy-currentview-null-then-64hex-fields')
 report={'format':'aeris-ui-action-causality-source-mock','status':'PASS_SOURCE_MOCK_NOT_ANDROID_DOM_OR_TOUCH_ATTESTATION','groups':groups,'originalDispatchMsUnchanged':200,'nativeInputFreshnessMsUnchanged':250,'clockScope':'SERVER_RECEIVED_DOM_OBSERVATION_ROOT_REQUEST_BRACKET','actorsStarted':False};p=R/'evidence/betasim-integrated01/runtime/ui-action-causality-mock06-final03.json';assert not p.exists();p.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
