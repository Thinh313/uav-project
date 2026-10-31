"""Independent selection-only UI08 adversarial tests; no Android actors."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,json,os,sys
R=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.public_ui_workload import PublicUIDriver,geometry_point
from aeris_runtime.metadata_budget import encoded
checks=[]
def fixture(specs):
 now=[1_000_000_000];calls=[];events=[];seen=[];specs=list(specs)
 device=SimpleNamespace(last_command_ref=None)
 def command(args,**kwargs):calls.append((args,kwargs));device.last_command_ref={'QA':len(calls)};return b''
 device.command=command
 ui=PublicUIDriver(SimpleNamespace(),{'device':device,'native':SimpleNamespace()},lambda:None,clock=lambda:now[0]);ui.geometry={'x':0,'y':0,'width':1280,'height':800}
 def observe():
  s=specs.pop(0)if len(specs)>1 else specs[0];start=now[0];now[0]+=s.get('rtt',0);seen.append(s)
  o={'instance':'QA','platform':'ANDROID','viewport':{'w':1280,'h':800},'controls':{'grant':{'x':20,'y':30,'w':40,'h':40,'enabled':True,'visible':s.get('visible',True)}},'scrollRegions':{'panel':{'x':0,'y':0,'w':500,'h':500}}}
  return o,start,now[0],encoded(o),s['age']
 ui.observation=observe;ui.event=lambda k,d:events.append((k,d))
 return ui,now,calls,events,seen
def sleep(now):return patch('aeris_runtime.public_ui_workload.time.sleep',side_effect=lambda s:now.__setitem__(0,now[0]+int(s*1e9)))
def run(name,fn):fn();checks.append(name)
def old_then_new():
 u,t,c,e,s=fixture([{'age':192.699583,'rtt':964083},{'age':0,'rtt':1_000_000}])
 with sleep(t):u.tap('grant')
 assert len(s)==2 and len(c)==len(e)==1 and e[0][1]['observationAgeMs']==0
 assert c[0][1]['dispatch_deadline_ns']==e[0][1]['actualDispatchDeadlineNs']
def boundaries():
 u,t,*_=fixture([{'age':0}]);start=t[0]
 assert u.dispatch_headroom(start,100);t[0]+=1;assert not u.dispatch_headroom(start,100)
 t[0]=start;assert not u.dispatch_headroom(start,100.000001)
 assert u.dispatch_headroom(start,99);t[0]+=1_000_001;assert not u.dispatch_headroom(start,99)
def rtt_headroom():
 u,t,c,e,s=fixture([{'age':95,'rtt':6_000_000},{'age':0,'rtt':2_000_000}])
 with sleep(t):u.tap('grant')
 assert len(s)==2 and len(c)==len(e)==1 and e[0][1]['observationAgeMs']==0
def geometry_reselect(scroll):
 u,t,c,e,s=fixture([{'age':0,'visible':not scroll},{'age':0,'visible':not scroll},{'age':0}]);n=[0]
 def geometry(*args):
  n[0]+=1
  if n[0]==1:t[0]+=101_000_000
  return geometry_point(*args)
 with sleep(t),patch('aeris_runtime.public_ui_workload.geometry_point',side_effect=geometry):
  if scroll:u.target('grant')
  else:u.tap('grant')
 assert len(c)==len(e)==1 and len(s)>=2
 assert c[0][0][2]==('swipe'if scroll else'tap')
def bounded_old():
 u,t,c,e,s=fixture([{'age':192.699583}]);start=t[0]
 with sleep(t):
  try:u.tap('grant')
  except TimeoutError as err:assert 'TARGET_NOT_READY' in str(err)
  else:raise AssertionError('old observation acted')
 assert not c and not e and 8_000_000_000<=t[0]-start<8_550_000_000 and len(s)<30
def barrier():
 u,t,c,e,s=fixture([{'age':0}]);prior=t[0];u.last_action_finished_ns=prior
 with sleep(t):u.tap('grant')
 assert len(s)>1 and len(c)==1 and e[0][1]['serverObservationLowerRootNs']>prior
 u.last_action_finished_ns=100
 assert not u.after_action(101,.0000004)
 assert u.after_action(102,.0000004)
source=R/'planning/betasim-integrated01/runtime/source/aeris_runtime/public_ui_workload.py';pin=hashlib.sha256(source.read_bytes()).hexdigest()
run('R05_old_observation_no_action_then_one_fresh_intent',old_then_new)
run('exact_source_and_remaining_100ms_boundary',boundaries)
run('round_trip_consumes_original_reserve_not_retimed',rtt_headroom)
run('tap_geometry_cost_reselects_before_any_intent',lambda:geometry_reselect(False))
run('scroll_geometry_cost_reselects_before_any_intent',lambda:geometry_reselect(True))
run('always_old_8s_bounded_no_intent_no_ADB',bounded_old)
run('original_after_action_ceil_barrier_remains',barrier)
assert hashlib.sha256(source.read_bytes()).hexdigest()==pin
out=R/'evidence/betasim-integrated01/qa/ui-headroom08-01.json';assert not out.exists()
out.write_bytes(encoded({'format':'aeris-independent-ui-headroom08-source-qa','status':'PASS_SCOPED_MOCK_NOT_ANDROID_TIMING_ACCEPTANCE','checks':checks,'sourceSHA256':pin,'actorsStarted':False,'sourceSelectionMaxMs':100,'minimumOriginalDispatchReserveMs':100,'finalDispatchMsUnchanged':200,'nativeFreshnessMsUnchanged':250,'noActualR05Retry':True}))
print(json.dumps({'status':'PASS','checks':len(checks),'sourceSHA256':pin}))
