from android_qa import *
import sys,base64
owned();run=sys.argv[1];phase=sys.argv[2]if len(sys.argv)>2 else'upload';label=sys.argv[3]if len(sys.argv)>3 else'fast'
def rows():return[json.loads(l)for l in adb('exec-out','cat','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl').splitlines()]
def events(k):return[(r,json.loads(base64.b64decode(r['dataBase64'])))for r in rows()if r['kind']==k]
def wait(k,before,seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  e=events(k)
  if len(e)>before:return e[-1]
  if events('CLOSED'):raise AssertionError('CLOSED_NO_RETRY')
  time.sleep(.08)
 raise AssertionError('UI_EVENT_DEADLINE:'+k)
# Real Android UI coordinates from inspected 1280x800 layout; no DOM/command RPC injection.
before=len(events('PREFLIGHT'));adb('shell','input','tap',470,393);p=wait('PREFLIGHT',before,9);assert p[1]['assessment']['state']=='READY_SCOPED_READONLY',p[1]['assessment'];capture(run+'-'+label+'-preflight')
g=len(events('EXPLICIT_GRANT'));adb('shell','input','tap',637,393);wait('EXPLICIT_GRANT',g,3);time.sleep(.15)
if phase=='upload':
 n=len(events('READBACK_VERIFIED'));adb('shell','input','tap',826,393);rb=wait('READBACK_VERIFIED',n,6);assert rb[1]['matches'];time.sleep(.15)
else:assert events('READBACK_VERIFIED')[-1][1]['matches']
if phase=='upload-only':raise AssertionError('USE_UPLOAD_PHASE_WITH_STOP_PARAMETER')
if len(sys.argv)>4 and sys.argv[4]=='stop-after-upload':print('VERIFIED_UPLOAD_DISARMED');sys.exit(0)
n=len(events('POST_ARM_HOME_REVIEW_REQUIRED'));adb('shell','input','tap',989,393);wait('POST_ARM_HOME_REVIEW_REQUIRED',n,6);time.sleep(.15);capture(run+'-'+label+'-home')
adb('shell','input','tap',258,449);wait('AUTO_OBSERVED',0,4);capture(run+'-'+label+'-auto');adb('shell','input','tap',1119,128);adb('shell','input','tap',52,171);time.sleep(.3);capture(run+'-'+label+'-fly');print('CREW02_AUTO_OBSERVED')
