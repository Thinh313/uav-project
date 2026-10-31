# GENERATION02 QA-only variant; old helper retained unchanged.
"""Root-only real observed-coordinate gestures. No control HTTP, no retry.

Coordinates are supplied by the Contractor from a current screenshot. Evidence
records that screenshot and fresh before/after images. All host calls are GET.
"""
from pathlib import Path
import importlib.util,json,time,sys
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('qa-android-v2.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
attempt,phase,reference=sys.argv[1:4];coords=list(map(int,sys.argv[4:]));assert phase in ['payload-grant','measure-payload','measure-capture','reboot']
q.owned(attempt);assert(q.E/reference).is_file();v=q.state();run=v['flight']['run'];assert run and v['flight']['mode']=='sitl';out=q.E/f'qa-live-{phase}-{attempt}-{run}.json';assert not out.exists()
log={'phase':phase,'run':run,'uiReference':reference,'coordinates':coords,'startPythonMono':time.monotonic(),'provenance':'REAL_ADB_UI_GESTURES_READONLY_HTTP_OBSERVATIONS_NO_API_CONTROL','actions':[]}
def snap(label):return str(q.capture(attempt,f'android-live-{attempt}-{run}-{phase}-{label}').relative_to(q.R))
def observe():
 v=q.state();assert v['flight']['run']in[run,None];return v
def tap(x,y,label):
 assert 0<=x<1280 and 0<=y<800;log['actions'].append({'label':label,'beforeImage':snap(label+'-before'),'pythonMono':time.monotonic()});q.adb('shell','input','tap',x,y);time.sleep(.35)
def lease(v,minimum=5000):
 f=v['flight'];o=v['payloadLeaseObservation'];ls=[l for l in o['leases']if l['flightRun']==run and l['flightBoot']==f['request']['boot']and l['modelSha256']==f['binding']['modelSha256']and l['planSha256']==f['binding']['planSha256']and l['untilHostMonoMs']>o['observedAtHostMonoMs']and l['remainingMs']>=minimum];assert ls,'ACTIVE_EXACT_UNEXPIRED_PAYLOAD_LEASE_REQUIRED';return o
try:
 if phase=='payload-grant':
  assert len(coords)==3;dy,sy,gy=coords;tap(960,dy,'discovery');tap(862,sy,'select');tap(1057,gy,'explicit-grant');v=observe();log['lease']=lease(v,50000)
 elif phase in ['measure-payload','measure-capture']:
  assert len(coords)==(2 if phase=='measure-payload'else 1);gimbalY,captureY=coords if phase=='measure-payload'else(None,coords[0]);v=observe();log['before']=v;lease(v,20000);f=v['flight'];assert f['live']['armed'] and f['live']['stage']=='AUTO' and f['latestPosition']['relativeHomeM']>5,'AIRBORNE_AUTO_REQUIRED'
  tap(620,434,'measure30s')
  if gimbalY is not None:tap(862,gimbalY,'gimbal-readback')
  tap(1057,captureY,'decoded-capture');end=time.monotonic()+8
  while time.monotonic()<end:
   v=observe();caps=[c for c in v['captures']if c.get('state')=='COMMITTED'and c.get('sidecar',{}).get('context',{}).get('flightRun')==run]
   if caps:break
   time.sleep(.2)
  assert caps,'CURRENT_RUN_COMMITTED_CAPTURE_REQUIRED';log['captures']=caps;log['afterCapture']=v;tap(220,490,'relay-pause500');time.sleep(.8);log['measuredWindowStillRequiresRawSaveAndReplay']=True
 elif phase=='reboot':
  assert len(coords)==2;v=observe();f=v['flight'];assert f['live']['armed']and f['latestPosition']['relativeHomeM']>5 and f['positionAgeMs']<1000;log['preFault']=v;lease(v,5000);tap(*coords,'owned-ap-reboot');end=time.monotonic()+35
  while time.monotonic()<end:
   v=observe()
   if not v['flight']['run']and not v['flight']['busy']:break
   time.sleep(.2)
  o=v['payloadLeaseObservation'];last=v['payloadAuthority']['last'];assert not v['flight']['run']and not v['flight']['authority']and o['leaseCount']==0;assert last['reason']=='FLIGHT_REBOOT'and last['pre']['leaseCount']>=1 and last['post']['leaseCount']==0;assert all(l['untilHostMonoMs']>last['pre']['observedAtHostMonoMs']for l in last['pre']['leases']);log['postFault']=v;log['requiresRawPidAndReceiptOrderReplay']=True
 log['status']='OBSERVED_REQUIRES_INDEPENDENT_REPLAY';log['finalImage']=snap('final')
except BaseException as e:log['status']='FAILED_OR_PARTIAL_NO_RETRY';log['error']=str(e);raise
finally:
 log['endPythonMono']=time.monotonic()
 with out.open('x')as f:json.dump(log,f,indent=2);f.write('\n')
 print(json.dumps({'status':log['status'],'phase':phase,'run':run,'error':log.get('error')}))
