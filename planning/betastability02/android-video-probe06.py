import importlib.util,time,json,os
from pathlib import Path
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
rows=[];error=None
try:
 q.prepare('polygon');q.tap('video-start');start=time.monotonic()
 while time.monotonic()-start<35:
  v=q.obs();rows.append({'at':time.time(),'viewer':v.get('viewer'),'video':v.get('video')});time.sleep(1)
 image=q.shot('android-native-video-probe06.png');print('SCREENSHOT',image,flush=True)
except BaseException as e:error=repr(e)
with(q.E/'android-video-probe06.json').open('x')as f:json.dump({'rows':rows,'error':error,'source':'OWNED_ANDROID_DEDICATED_WORKER_OFFSCREEN_NATIVE_SYNTHETIC_H264_HOST','actualFlight':False,'fullAUTOAcceptance':False},f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps({'error':error,'last':rows[-1]if rows else None}),flush=True)
