"""Actual UI IDs + native row barriers. One explicit intent each; no automatic retries."""
from ui01 import *
import threading,collections
owned();run=sys.argv[1];label=sys.argv[2];assert re.fullmatch('s[a-f0-9]{20}',run) and re.fullmatch('[a-z0-9-]+',label);launch=json.loads((E/'runs'/run/'launch.json').read_text());assert launch['run']==run and launch['nativeOnlyGCS'] is True and launch['speedup']==1;meta=events98(run,'META')[0][1];assert meta['ownedLaunchAssertion']=={k:launch[k] for k in ['run','containerId','pid','startedAt','binarySha256']};binding=json.loads((E/'runs'/run/'native-viewer-binding.json').read_text());assert binding['run']==run and binding['nativeSourceId']==meta['sourceId'] and binding['planSha256']==meta['document']['compiled']['plan']['sha256'];seen=collections.defaultdict(list);failures=[];lock=threading.Lock();last_n=0;actions=[];error=None
tail=subprocess.Popen([ADB,'-s',S,'exec-out','tail','-n','+1','-f','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def consume():
 global last_n
 try:
  for line in tail.stdout:
   assert len(line)<1048576;r=json.loads(line)
   with lock:
    last_n=max(last_n,r['n'])
    if r['kind'] in ['PREFLIGHT','EXPLICIT_GRANT','READBACK_VERIFIED','POST_ARM_HOME_REVIEW_REQUIRED','AUTO_OBSERVED','CLOSED','FLIGHT_DOMAIN_FAILURE01']:
     seen[r['kind']].append({'n':r['n'],'elapsedMs':r['elapsedMs'],'data':json.loads(base64.b64decode(r['dataBase64']))})
 except Exception as ex:failures.append(str(ex))
thread=threading.Thread(target=consume,daemon=True);thread.start()
def barrier():
 raw=adb('exec-out','tail','-n','1','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl');r=json.loads(raw);end=time.monotonic()+3
 while True:
  with lock:
   assert not seen['CLOSED'] and not seen['FLIGHT_DOMAIN_FAILURE01'],'CLOSED_OR_FAILED_NO_RETRY'
   if last_n>=r['n']:return r['n']
  assert not failures and time.monotonic()<end,'PASSIVE_TAIL_NOT_CAUGHT_UP';time.sleep(.01)
def click(identifier):
 control=control01(identifier);floor=barrier();entry={'id':identifier,'barrierN':floor,'hostIntentNs':str(time.monotonic_ns()),'observedControl':control,'automaticRetry':False};actions.append(entry)
 adb('shell','input','tap',round((control['x']+control['right'])/2),round((control['y']+control['bottom'])/2));return floor
def wait(kind,floor,seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  assert not failures,failures
  with lock:
   assert not seen['CLOSED'] and not seen['FLIGHT_DOMAIN_FAILURE01'],'CLOSED_OR_FAILED_NO_RETRY'
   fresh=[r for r in seen[kind]if r['n']>floor]
   if fresh:return fresh[-1]
  time.sleep(.02)
 raise AssertionError('NEW_EVENT_DEADLINE:'+kind)
def inspect(part):
 r=wait('PREFLIGHT',click('preflight83'),10);assert r['data']['assessment']['state']=='READY_SCOPED_READONLY',r
 wait('EXPLICIT_GRANT',click('grant83'),3)
try:
 barrier();inspect('initial');r=wait('READBACK_VERIFIED',click('upload83'),10);assert r['data']['matches'],r
 inspect('post-upload');wait('POST_ARM_HOME_REVIEW_REQUIRED',click('arm83'),10)
 # Eligibility is observed again through the actual enabled control, never force clicked.
 wait('AUTO_OBSERVED',click('auto83'),6);capture(run+'-'+label+'-auto')
 tap01('close83');adb('shell','input','tap',52,171);capture(run+'-'+label+'-fly');print('ACTUAL_NEW_AUTO_OBSERVED_NO_RETRY')
except BaseException as ex:
 error=repr(ex);raise
finally:
 tail.terminate()
 try:tail.wait(timeout=3)
 except subprocess.TimeoutExpired:tail.kill();tail.wait()
 thread.join(2)
 (E/'runs'/run/('ui-auto-'+label+'.json')).open('x').write(json.dumps({'run':run,'actions':actions,'events':dict(seen),'errors':failures,'error':error,'passiveTailRowBarriers':True,'actualUIControlsOnly':True,'automaticRetries':False},indent=2)+'\n')
