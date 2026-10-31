"""Execute both selected source journeys using a memory UI and fake clock.
This checks argument/flow plumbing, never grants actual flight/SAF acceptance.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,importlib.util,json,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.application09 import AndroidDomain09,PACKAGE
from aeris_runtime.metadata_budget import encoded
spec=importlib.util.spec_from_file_location('scenario_app09_mock',T/'scenario-app09.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Clock:
 def __init__(self):self.ns=1
 def monotonic_ns(self):return self.ns
 def sleep(self,n):self.ns+=int(n*1e9)
class UI:
 def __init__(self,owner,case,check):self.case=case;self.probe=case['native'];self.device=case['device'];self.phase='HELD';self.compiled=False;self.geometry={};self.last_native=None;self.next_native=0;self.actions=[]
 def bind_geometry(self):pass
 def observation(self):return {}
 def target(self,*a,**kw):return None
 def tap(self,key):self.actions.append(key);self.compiled=key=='compile'or self.compiled;self.phase='HELD'if key=='b-hold'else self.phase
 def checked(self,key):self.actions.append(key)
 def choose(self,*a):self.actions.append(a)
 def wait_ui(self,p,**kw):
  q={'currentView':'plan','modal':False,'workbenchBusy':False,'planSha256':'a'*64 if self.compiled else None};assert p(q);return q
 def save_workspace(self):return {'head':'h','planSHA256':'a'*64,'observation':{}}
 def workspace_saved(self):return {'head':'h','planSHA256':'a'*64,'observation':{'consent':False}}
 def state(self):return {'flight':{'run':'case','navigationReadiness':{'phase':'DISARMED_READ_ONLY_NAVIGATION_READINESS','ready':True},'preflight':{'ready':True},'live':{'readback63':True,'stage':'ARMED_HOME_REVIEW','armed':True},'manual':{'phase':self.phase,'failure':None},'latestPosition':{'relativeHomeM':3},'completion':{'complete':True},'authority':None},'payloadCamera':{},'reviews':[{'run':'case','accepted':True}],'latestVideoQualification':{'status':'PASS'},'client':{'active':False}}
 def wait(self,p,**kw):q=self.state();assert p(q),kw;return q
 def right_pad(self):return 100,200,100
 def pointer_event(self,kind,x,y):self.phase='MANUAL'if kind=='DOWN'else'HELD'if kind=='UP'else self.phase;self.device.command(['shell','input','touchscreen','motionevent',kind,str(x),str(y)])
 def native(self,*a):return {'input':{'failed':False,'configured':False if self.actions[-1:]and self.actions[-1]=='close-modal'else True,'closed':True,'pending':False,'journal':{'durablyDrained':True}}}
 def event(self,*a):pass
class Device:
 def __init__(self):self.argv=[];self.guard=AndroidDomain09.__new__(AndroidDomain09);self.guard.serial='emulator-5582';self.guard.observer=SimpleNamespace(tag='AERIS_PRODUCT_STATUS');self.guard.status_socket=None;self.guard._install_authorization=None
 def command(self,args,**kw):self.guard._command_bound(args);self.argv.append(list(args));return b''
def main():
 source=(T/'scenario-app09.py').read_bytes();old=(T/'scenario-nav07.py').read_bytes();assert source==old.replace(b"['shell','am','force-stop','vn.rtr.aeris.mission']",b"['shell','am','force-stop','vn.rtr.aeris.betasim09']");traces=[]
 for seconds in(180,760):
  clock=Clock();m.time=clock;m.PublicUIDriver=UI;device=Device();probe=SimpleNamespace(pid=10,process_epoch='old',last_ref={});case={'device':device,'native':probe,'plannedSeconds':seconds,'intervalProof':True,'managementCommand':lambda *a:None}
  class Owner:
   def planned_native_rollover(self,**kw):probe.pid=11;probe.process_epoch='new';return {'source':'MOCK_ONLY'}
  result=m.run(Owner(),case,lambda:None);assert result['manualSeconds']==(600 if seconds==760 else 5);assert ['shell','am','force-stop',PACKAGE]in device.argv;assert not any('vn.rtr.aeris.mission'in a for row in device.argv for a in row);traces.append({'plannedSeconds':seconds,'argv':device.argv,'publicActions':case['uiDriver'].actions,'manualSeconds':result['manualSeconds'],'actualExecution':False})
 # SAF content-read is application-independent; immutable URI comes only from
 # the selected probe's source-bound success DTO. Static source handoff retains
 # both bundle/native streams and uses owned device.open_saf_document exclusively.
 tree=ast.parse(source);handoff=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='handoff');segment=ast.get_source_segment(source.decode(),handoff);assert 'device.open_saf_document'in segment and "probe.saf_document(stream,index)"in segment and "'native-closed-files'"in segment and 'vn.rtr.aeris.mission'not in segment;stream=(T/'source/aeris_runtime/saf_stream.py').read_text();assert "d.APPLICATION_PACKAGE,'cat',path"in stream and "'exec-out','content','read','--uri',cap.receipt['documentUri']"in stream
 report={'format':'aeris-selected-development-application09-driver-trace','status':'PASS_MEMORY_UI_SOURCE_FLOW_AND_TYPED_ANDROID_ALLOWLIST_NOT_DEVICE_OR_SAF_ACCEPTANCE','sourceSHA256':hashlib.sha256(source).hexdigest(),'oldScenarioUnchangedSHA256':hashlib.sha256(old).hexdigest(),'exactScenarioDelta':'ONLY_FIXED_NEW_APPLICATION_RESTART_PACKAGE','traces':traces,'SAFHandoff':'STRUCTURAL_SOURCE_ROUTE_JOIN_ONLY_INDEPENDENT_ACTUAL_BYTES_RECEIVER_NOT_RUN_HERE','actorsStarted':False,'clockIsMock':True};out=R/'evidence/betasim-integrated01/runtime/application09-driver-trace01.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps({k:v for k,v in report.items()if k!='traces'}))
if __name__=='__main__':main()
