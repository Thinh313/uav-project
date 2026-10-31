"""Actual Android UI only. Single passive raw tail instead of repeated whole-file pulls.
Fresh preflight after upload is a separate explicit intent, no command retries.
"""
from android_qa import *
import sys,base64,threading,collections
owned();run=sys.argv[1];label=sys.argv[2];seen=collections.defaultdict(list);failure=[];lock=threading.Lock()
p=subprocess.Popen([ADB,'-s',S,'exec-out','tail','-n','+1','-f','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def consume():
 try:
  for line in p.stdout:
   assert len(line)<1048576,'RAW_LINE_BOUND';r=json.loads(line)
   if r['kind'] in ['PREFLIGHT','EXPLICIT_GRANT','READBACK_VERIFIED','POST_ARM_HOME_REVIEW_REQUIRED','AUTO_OBSERVED','CLOSED','FLIGHT_DOMAIN_FAILURE01']:
    q=json.loads(base64.b64decode(r['dataBase64']))
    with lock:
     seen[r['kind']].append((r['elapsedMs'],q));assert sum(map(len,seen.values()))<1000
 except Exception as e:failure.append(str(e))
t=threading.Thread(target=consume,daemon=True);t.start()
def n(k):
 with lock:return len(seen[k])
def wait(k,before,seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  assert not failure,failure
  with lock:
   if len(seen[k])>before:return seen[k][-1]
   assert not seen['CLOSED'],'CLOSED_NO_RETRY'
  time.sleep(.025)
 raise AssertionError('UI_EVENT_DEADLINE:'+k)
def inspect(labelpart):
 before=n('PREFLIGHT');adb('shell','input','tap',470,393);v=wait('PREFLIGHT',before,10);assert v[1]['assessment']['state']=='READY_SCOPED_READONLY';capture(run+'-'+label+'-'+labelpart)
 g=n('EXPLICIT_GRANT');adb('shell','input','tap',637,393);wait('EXPLICIT_GRANT',g,3)
try:
 time.sleep(.25);inspect('initial-preflight');before=n('READBACK_VERIFIED');adb('shell','input','tap',826,393);rb=wait('READBACK_VERIFIED',before,8);assert rb[1]['matches']
 # Upload/readback can consume the10second extra-param freshness. Explicit new cohort before arm.
 inspect('post-upload-preflight');before=n('POST_ARM_HOME_REVIEW_REQUIRED');adb('shell','input','tap',989,393);home=wait('POST_ARM_HOME_REVIEW_REQUIRED',before,8);capture(run+'-'+label+'-home')
 adb('shell','input','tap',258,449);wait('AUTO_OBSERVED',0,5);capture(run+'-'+label+'-auto');adb('shell','input','tap',1119,128);adb('shell','input','tap',52,171);capture(run+'-'+label+'-fly');print('CREW02_AUTO_OBSERVED')
finally:
 p.terminate()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.kill();p.wait()
 t.join(2)
 with(E/(run+'-'+label+'-passive-ui-observer.json')).open('x')as f:json.dump({'singlePassiveADBStream':True,'automaticRetries':False,'events':dict(seen),'errors':failure},f,indent=2)
