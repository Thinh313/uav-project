"""Root-only deadline choreography through already-observed real Android controls.
Stages payload before arm, retains all fixed gates, and measures after real climb.
No control POST or hidden JS. This is QA automation, not an app flight API.
"""
from pathlib import Path
import importlib.util,json,time,sys,subprocess
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('qa-android-v2.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
a,reference,prefY,armY=sys.argv[1:];assert a in ['03','04'];q.owned(a);v=q.state();run=v['flight']['run'];assert v['flight']['mode']=='sitl'and run and v['flight']['authority'];out=q.E/f'qa-arm-measure-v2-{a}-{run}.json';assert not out.exists();log={'run':run,'reference':reference,'mode':'sitl','source':'REAL_ANDROID_UI_HOST_VIDEO_SYNTHETIC_PAYLOAD','startPythonMono':time.monotonic(),'controlHTTP':False}
def observe():
 v=q.state();assert v['flight']['run']==run and v['flight']['mode']=='sitl';return v
def active_lease(v,minimum):
 f=v['flight'];o=v['payloadLeaseObservation'];ls=[x for x in o['leases']if x['flightRun']==run and x['flightBoot']==f['request']['boot']and x['modelSha256']==f['binding']['modelSha256']and x['planSha256']==f['binding']['planSha256']and x['remainingMs']>=minimum and x['untilHostMonoMs']>o['observedAtHostMonoMs']];assert ls,'LATE_EXPLICIT_PAYLOAD_LEASE_REQUIRED_NO_AUTORENEW';return o
try:
 log['beforeArmLease']=active_lease(v,40000)
 p=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('qa-arm-auto-v2.py')),a,reference,prefY,armY],capture_output=True,text=True,timeout=60);log['armController']={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr};assert p.returncode==0,'ARM_HOME_AUTO_NOT_CONFIRMED_NO_RETRY'
 end=time.monotonic()+15
 while time.monotonic()<end:
  v=observe();f=v['flight'];assert not f['error'],f['error']
  if f['live']['armed']and f['live']['stage']=='AUTO'and f['positionAgeMs']<1000 and f['latestPosition']['relativeHomeM']>5:break
  time.sleep(.1)
 assert f['live']['armed']and f['live']['stage']=='AUTO'and f['latestPosition']['relativeHomeM']>5,'REAL_CLIMB_NOT_OBSERVED';log['beforeMeasure']=v;active_lease(v,20000);q.capture(a,'android-airborne-before-measure-'+a)
 # Both controls are fixed, visible and identified in the supplied cockpit screenshot.
 q.adb('shell','input','tap',620,434);log['measureTapPythonMono']=time.monotonic();time.sleep(.2);q.capture(a,'android-before-global-shutter-'+a);q.adb('shell','input','tap',1227,380);end=time.monotonic()+8
 while time.monotonic()<end:
  v=observe();caps=[c for c in v['captures']if c.get('state')=='COMMITTED'and c.get('sidecar',{}).get('context',{}).get('flightRun')==run]
  if caps:break
  time.sleep(.15)
 assert caps,'NO_CURRENT_RUN_CAPTURE_NO_RETRY';assert any(c['sidecar']['position']['relativeHomeM']>5 and c['sidecar']['actualImages']==0 for c in caps);log['captures']=caps;log['afterCapture']=v;q.capture(a,'android-after-global-shutter-'+a)
 q.adb('shell','input','tap',220,490);log['pause500TapPythonMono']=time.monotonic();time.sleep(.8);q.capture(a,'android-concurrent-capture-relay-'+a);log['status']='ACTUAL_AIRBORNE_CAPTURE_MEASUREMENT_STARTED_REQUIRES_RAW_SAVE_AND_REPLAY'
except BaseException as e:log['status']='PARTIAL_NO_RETRY';log['error']=str(e);raise
finally:
 log['endPythonMono']=time.monotonic()
 with out.open('x')as f:json.dump(log,f,indent=2);f.write('\n')
 print(json.dumps({'status':log['status'],'run':run,'error':log.get('error')}))
