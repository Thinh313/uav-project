"""Exact frozen angle entry by actual visible Android +/- touches, no command RPC."""
from ui01 import *
owned();run=sys.argv[1];assert re.fullmatch('s[a-f0-9]{20}',run);tap01('op-preset-oblique') # Explicit known requested base -45/0, does not send.
for identifier,count in [('op-pitch-plus',12),('op-yaw-plus',78)]:
 c=control01(identifier);x=round((c['x']+c['right'])/2);y=round((c['y']+c['bottom'])/2)
 with(E/'angle-touch-batches01.jsonl').open('a')as f:f.write(json.dumps({'atHostMonoNs':str(time.monotonic_ns()),'control':c,'count':count,'action':'actual ADB input tap repeated, no API/DOM injection or actuator RPC'})+'\n')
 for _ in range(count):adb('shell','input','tap',x,y)
 time.sleep(.1)
capture(run+'-crew-requested-angle-frozen04');print('REQUESTED_ANGLES_ENTERED_BY_TOUCH_ONLY_VERIFY_SCREENSHOT_BEFORE_SEND')
