from ui94 import *
import base64
run='s095f2c41e36548be9071';owned()
def rows():return [json.loads(x) for x in adb('exec-out','cat','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl').splitlines()]
def events(k):return [(r,json.loads(base64.b64decode(r['dataBase64']))) for r in rows() if r['kind']==k]
# Observed UI coordinates, restored by real scroll. No DOM or command API.
adb('shell','input','tap',340,190)
for _ in range(4):adb('shell','input','swipe',1146,330,1146,610,150)
capture('03-before-fresh-preflight')
before=len(events('PREFLIGHT'));adb('shell','input','tap',470,393)
end=time.monotonic()+9
while time.monotonic()<end:
 p=events('PREFLIGHT')
 if len(p)>before:break
 time.sleep(.1)
else:raise AssertionError('NEW_PREFLIGHT_NOT_OBSERVED')
assert p[-1][1]['assessment']['state']=='READY_SCOPED_READONLY',p[-1][1]['assessment']
capture('03-fresh-preflight-visible')
adb('shell','input','tap',637,393);time.sleep(.25)
assert len(events('EXPLICIT_GRANT'))==1,'UI_GRANT_NOT_OBSERVED'
capture(run+'-preflight-ready');adb('shell','input','tap',826,393)
end=time.monotonic()+6
while time.monotonic()<end:
 if events('READBACK_VERIFIED'):break
 time.sleep(.1)
else:raise AssertionError('READBACK_NOT_OBSERVED')
capture(run+'-upload-readback');adb('shell','input','tap',989,393)
end=time.monotonic()+6
while time.monotonic()<end:
 if events('POST_ARM_HOME_REVIEW_REQUIRED'):break
 time.sleep(.1)
else:raise AssertionError('POST_ARM_HOME_NOT_OBSERVED')
capture(run+'-post-arm-home-review');adb('shell','input','tap',258,449)
end=time.monotonic()+4
while time.monotonic()<end:
 if events('AUTO_OBSERVED'):break
 time.sleep(.1)
else:raise AssertionError('AUTO_NOT_OBSERVED')
capture(run+'-auto-observed');adb('shell','input','tap',1119,128);adb('shell','input','tap',52,171);time.sleep(.5);capture(run+'-fly-main')
print('APK03_DIRECT_AUTO_OBSERVED')
