"""Owned emulator taps grounded in fresh visible DOM receipts; no UI eval or control POST."""
from pathlib import Path
import importlib.util,time,json
p=Path(__file__).with_name('actual-ui-journey.py');s=importlib.util.spec_from_file_location('qa05',p);q=importlib.util.module_from_spec(s);s.loader.exec_module(q);q.step=2000
oldtap=q.tap
def tap(name):
 end=time.monotonic()+5
 while not q.obs()['controls'].get(name,{}).get('enabled',False):
  assert time.monotonic()<end,'CONTROL_DISABLED_'+name;time.sleep(.15)
 return oldtap(name)
q.tap=tap
try:
 q.tap('nav-plan');q.check('datum');q.tap('compile');q.prepare();st=q.connect();assert st['flight']['source']=='OBSERVED_OWNED_SITL';q.log('ACTUAL_CONNECT',{'run':st['flight']['run']})
 q.tap('video-start');time.sleep(8)
 for attempt in range(3):
  q.tap('b-preflight');st=q.state()
  if st['flight']['preflight']['ready']:break
  q.log('READONLY_STARTUP_ASSESSMENT_BLOCKED',{'attempt':attempt,'preflight':st['flight']['preflight']});time.sleep(10)
 else:raise RuntimeError('STARTUP_PREFLIGHT_NOT_READY_NO_GRANT')
 q.tap('b-grant');q.tap('b-upload');q.wait(lambda s:s['flight']['live']['readback63']);q.tap('b-arm');st=q.wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW');h=st['flight']['homeReview'];end=time.monotonic()+4
 while h['sha256'][:10] not in (q.obs()['homeText']or''):
  assert time.monotonic()<end,'HOME_NOT_DISPLAYED';time.sleep(.15)
 q.log('AUTOMATED_QA_HOME_REVIEW',{'shown':q.obs()['homeText'],'sha256':h['sha256'],'humanOrPhysicalApproval':False});q.check('b-home-after');q.tap('video-measure');q.tap('b-auto');q.wait(lambda s:s['flight']['live']['stage']=='AUTO');q.log('AUTO_OBSERVED',{'run':st['flight']['run']})
 q.tap('b-discover');q.tap('b-select');q.tap('b-payload-grant');q.tap('b-gimbal');q.tap('video-capture');q.wait(lambda s:len(s['captures'])>0)
 (q.E/'android-auto-video-payload01.png').open('xb').write(q.adb('exec-out','screencap','-p'))
 q.wait(lambda s:s['flight']['completion']['complete'],160)
 end=time.monotonic()+110
 while not(q.obs().get('video')or{}).get('complete'):
  v=q.obs().get('video');assert not(v or{}).get('error'),v;assert time.monotonic()<end,'FULL_AUTO_COLLECTION_INCOMPLETE';time.sleep(.5)
 q.tap('video-save');q.tap('b-close');q.wait(lambda s:len(s['reviews'])>0);q.tap('beta-quality');end=time.monotonic()+8
 while True:
  result=q.get('/api/video-quality')['result']
  if result is not None:break
  assert time.monotonic()<end,'QUALIFICATION_NOT_WRITTEN';time.sleep(.25)
 q.log('AUTO_VIDEO_QUALIFICATION',result);(q.E/'android-auto-quality01.json').open('x').write(json.dumps(result,indent=2));assert result['status']=='PASS',result
 q.tap('save');(q.E/'android-review-qualified01.png').open('xb').write(q.adb('exec-out','screencap','-p'));print('ANDROID_AUTO_FULL_VIDEO_QUALIFIED',result['displayedFps'],result['durationMs'],flush=True)
except BaseException as e:q.log('ACTUAL_UI_FAILURE',{'error':str(e)});raise
