"""Fresh read selection, original dispatch guard, no Android/AP actor."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,os,shutil,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.public_ui_workload import PublicUIDriver
from aeris_runtime.android import AndroidDevice
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.once_reader import read_ref
LAB=R/'evidence/betasim-integrated01/runtime/.headroom08'
class Device:
 def __init__(self):self.calls=[];self.last_command_ref=None
 def command(self,args,**kw):self.calls.append((args,kw));self.last_command_ref={'mock':len(self.calls)};return b''
def fixture(rows):
 now=[1_000_000_000];device=Device();events=[];seen=[];rows=list(rows);ui=PublicUIDriver(SimpleNamespace(),{'device':device,'native':SimpleNamespace()},lambda:None,clock=lambda:now[0]);ui.geometry={'x':0,'y':0,'width':1280,'height':800}
 def observation():
  spec=rows.pop(0)if len(rows)>1 else rows[0];start=now[0];now[0]+=spec.get('rttNs',1_000_000);q={'instance':'MOCK','platform':'ANDROID','viewport':{'w':1280,'h':800},'controls':{'datum':{'x':20,'y':30,'w':40,'h':50,'visible':spec.get('visible',True),'enabled':True}},'scrollRegions':{'panel':{'x':0,'y':0,'w':500,'h':500}}};raw=encoded(q);seen.append(spec);return q,start,now[0],raw,spec['age']
 ui.observation=observation;ui.event=lambda kind,data:events.append((kind,data));return ui,device,now,events,seen
def sleep(now):return patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda s:now.__setitem__(0,now[0]+int(s*1e9)))
def deny(fn,part):
 try:fn()
 except(Exception)as e:assert part in str(e),str(e);return
 raise AssertionError('expected '+part)
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);groups=[];source=T/'source/aeris_runtime/public_ui_workload.py';before=hashlib.sha256(source.read_bytes()).hexdigest()
 try:
  ui,d,now,events,seen=fixture([{'age':192.699583,'rttNs':964083},{'age':20}])
  with sleep(now):ui.tap('datum')
  assert len(seen)==2 and len(d.calls)==1 and len(events)==1 and events[0][1]['observationAgeMs']==20;groups.append('original-R05-age192.699583-rejected-readonly-fresh20-selected-single-TAP-intent-command')
  ui,d,now,events,seen=fixture([{'age':192.699583}]);start=now[0]
  with sleep(now):deny(lambda:ui.tap('datum'),'TARGET_NOT_READY')
  assert not d.calls and not events and 8_000_000_000<=now[0]-start<8_550_000_000 and len(seen)<30;groups.append('always-old-readonly-selection-bounded-original8s-zero-intents-zeroADB')
  ui,d,now,events,seen=fixture([{'age':99,'rttNs':2_000_000},{'age':20}])
  with sleep(now):ui.tap('datum')
  assert len(seen)==2 and len(d.calls)==1;groups.append('sourceage-under100-but-remaining99ms-rejected-before-intent-and-budget')
  ui,d,now,events,seen=fixture([{'age':192.699583,'visible':False},{'age':20,'visible':False},{'age':20}])
  with sleep(now):ui.target('datum')
  assert len(seen)==3 and len(d.calls)==1 and d.calls[0][0][2]=='swipe' and len(events)==1 and events[0][1]['observationAgeMs']==20;groups.append('SCROLL-uses-same-sourceage-and-remaining100ms-reserve-single-genuine-selected-intent')
  ui,d,now,events,seen=fixture([{'age':20},{'age':20}]);ui.last_action_finished_ns=990_000_000
  with sleep(now):ui.tap('datum')
  assert len(seen)==2 and len(d.calls)==1 and events[0][1]['serverObservationLowerRootNs']>990_000_000
  ui.last_action_finished_ns=100;assert not ui.after_action(101,.0000004)and ui.after_action(102,.0000004);groups.append('post-action-original-observation-ceil-barrier-retained-no-retimestamp')
  ui,d,now,events,seen=fixture([{'age':100,'rttNs':0}]);assert ui.dispatch_headroom(now[0],100);now[0]+=1;assert not ui.dispatch_headroom(1_000_000_000,100);groups.append('exact100ms-source-and-reserve-boundary-no-float-epsilon-relaxation')
  for stage in ('evidence','liveguard'):
   ui,_,now,events,seen=fixture([{'age':20}]);root=LAB/stage;root.mkdir();budget=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);budget.admit();d=AndroidDevice('/mock/adb','emulator-5582',root/'sessions/mock/android-api',budget=budget,observer_tag='AERIS_PRODUCT_STATUS',now=lambda:now[0]);ui.device=d;calls=[]
   if stage=='evidence':
    def event(kind,data):events.append((kind,data));now[0]+=201_000_000
    ui.event=event
   else:
    checks=[0]
    def guard():
     checks[0]+=1
     if checks[0]==2:now[0]+=201_000_000
    d.live_check=guard
   with patch('aeris_runtime.android.subprocess.Popen',side_effect=lambda *a,**k:calls.append(a)):
    deny(lambda:ui.tap('datum'),'NAVIGATION_ACTUAL_DISPATCH200MS')
   row=json.loads(read_ref(d.root,d.last_command_ref));assert not calls and len(seen)==1 and len(events)==1 and row['captureComplete']is False and row['exit']is None and d.sequence==1
  groups.append('slow-evidence-or-liveguard-after-selection-final-original200ms-rejects-zeroPopen-onefailedcommand-no-retry')
  assert hashlib.sha256(source.read_bytes()).hexdigest()==before
  report={'format':'aeris-ui-dispatch-headroom-source-causal-mock','status':'PASS_SOURCE_AND_REAL_ANDROID_COMMAND_CAPTURE_FAKE_OS_NO_ANDROID_ACTORS','groups':groups,'sourceSHA256':before,'selectionMaxSourceAgeMs':100,'selectionMinRemainingMs':100,'finalDispatchMsUnchanged':200,'nativeInputFreshnessMsUnchanged':250,'targetSecondsUnchanged':8,'observerRequestsUnchanged':1800,'noCommandRetries':True,'sourceChangedDuringMock':False,'actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))}
 finally:shutil.rmtree(LAB)
 out=R/'evidence/betasim-integrated01/runtime/ui-headroom-mock08.json';assert not out.exists();out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
