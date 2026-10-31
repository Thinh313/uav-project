"""3 actual Android video-only sessions; no AP, no auto retry, stop first failure."""
from pathlib import Path
import importlib.util,json,time,subprocess,sys,hashlib,os
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
E=q.E;owner=json.loads((q.R/'.local/betavideo03/active/owner.json').read_text());H=Path(owner['run'])/'host';pins=E/'source-pins01.json';pinsha=hashlib.sha256(pins.read_bytes()).hexdigest();rows=[{'session':i,'status':'NOT_RUN'}for i in [1,2,3]];error=None

def save(name,value):
 with(E/name).open('x')as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def obs():return q.obs()
def await_condition(fn,seconds,label):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  v=obs()
  if fn(v):return v
  if v.get('videoCheck',{}).get('error'):raise RuntimeError(v['videoCheck']['error'])
  time.sleep(.25)
 raise RuntimeError(label)
def idle(seconds=10):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  h=q.get('/api/media-health');p=h.get('source')or{};v=p.get('lifecycle')or{}
  if p.get('failed'):raise RuntimeError('SOURCE_FAILED:'+p['failed'])
  if p.get('ready')and v.get('state')in ['WAITING','PAUSED']and v.get('outstanding')is None:return h
  time.sleep(.25)
 raise RuntimeError('SOURCE_IDLE_DEADLINE')
try:
 if 'video-check-link'in obs()['controls']:q.tap('video-check-link')
 await_condition(lambda v:'video-check-new'in v['controls'],10,'VIDEO_ONLY_PAGE_NOT_READY')
 initial=idle();time.sleep(2);stable=idle();assert initial['source']['lifecycle']['outcomes']['born']==stable['source']['lifecycle']['outcomes']['born'],'IDLE_SOURCE_PRODUCED_FRAMES';save('video-only-idle01.json',{'before':initial,'after':stable,'status':'PASS_ZERO_BORN_FRAMES_DURING_IDLE','actualFlight':False})
 for i in [1]:
  r=rows[i-1];r.update(status='RUNNING',host=str(H),sourcePinsSha256=pinsha,startedAt=time.time())
  v=obs();assert v['videoCheck']['sessionIndex']==i,'UI_SESSION_INDEX'
  if i==2:q.tap('video-check-load')
  before=idle();bodyReserve=192*2**20;traceReserve=16*2**20
  capacity={'bodyBytesRead':before['media']['bytesRead'],'bodyReserve':bodyReserve,'bodyLimit':2**30,'traceCompressedBytes':before['fullTrace']['bytes'],'traceReserve':traceReserve,'traceLimit':64*2**20,'allocation':'NO_AP','sourceState':before['source']['lifecycle']['state']}
  save(f'video-only-capacity{i:02d}.json',capacity)
  assert capacity['bodyBytesRead']+bodyReserve<2**30 and capacity['traceCompressedBytes']+traceReserve<64*2**20,'NEXT_VIDEO_SESSION_CAPACITY_REQUIRES_NEW_HOST_NOT_CAP_RAISE'
  q.tap('video-start');await_condition(lambda v:v['controls']['video-measure']['enabled'],10,'VIDEO_START_CAPABILITY_OR_COLD_START_FAILED');q.tap('video-measure');deadline=time.monotonic()+195;lastLog=0
  while True:
   v=obs();c=v.get('videoCheck',{}).get('collection')or{}
   if c.get('error'):raise RuntimeError('VIDEO_COLLECTION_FAILED:'+c['error'])
   if v.get('videoCheck',{}).get('error'):raise RuntimeError(v['videoCheck']['error'])
   if c.get('complete')is True:break
   assert time.monotonic()<deadline,'SIX_VIDEO_WINDOWS_DEADLINE'
   if time.monotonic()-lastLog>=5:q.log('VIDEO_ONLY_PROGRESS',{'session':i,'collection':c,'viewer':v.get('viewer')});lastLog=time.monotonic()
   time.sleep(.5)
  q.tap('video-save');v=await_condition(lambda v:isinstance(v['videoCheck'].get('savedReports'),list)and len(v['videoCheck']['savedReports'])==6,10,'SIX_SAVED_REPORTS_REQUIRED');reports=v['videoCheck']['savedReports'];q.tap('video-stop');idle();q.tap('video-check-seal');v=await_condition(lambda v:bool(v['videoCheck'].get('sealedTrace')),10,'VIDEO_TRACE_SEAL_DEADLINE')
  selection={'sessionIndex':i,'reports':reports,'sealedTrace':v['videoCheck']['sealedTrace'],'load':v['videoCheck']['load'],'sourcePinsSha256':pinsha,'actualFlight':False,'scope':'SIX_FULL_WINDOWS_ALL_SAMPLES_NO_AUTO_CLAIM'};inp=E/f'video-only-session{i:02d}-input.json';save(inp.name,selection);out=E/f'video-only-session{i:02d}-qualification.json'
  with(E/f'video-only-session{i:02d}-qualifier-console.txt').open('x')as f:p=subprocess.run(['node','planning/betavideo03/video-only-qualification.mjs',str(H),str(inp),str(out)],cwd=q.R,stdout=f,stderr=subprocess.STDOUT)
  r.update(qualification=str(out.relative_to(q.R)),input=str(inp.relative_to(q.R)),exit=p.returncode)
  assert p.returncode==0,'VIDEO_ONLY_PRIMARY_GATE_FAILED';r['status']='PASS_PRIMARY_PENDING_INDEPENDENT_ORACLE';r['endedAt']=time.time()
  if i<1:q.tap('video-check-new');await_condition(lambda v:v['videoCheck']['sessionIndex']==i+1,10,'NEXT_EXPLICIT_SESSION_DEADLINE')
except BaseException as e:
 error=repr(e)
 for r in rows:
  if r['status']=='RUNNING':r.update(status='FAIL',error=error)
finally:
 save('video-only-campaign01.json',{'status':'PASS_PRIMARY_PENDING_INDEPENDENT_ORACLE'if error is None and all(r['status'].startswith('PASS_PRIMARY')for r in rows)else'NOT_READY','sessions':rows,'error':error,'actualFlight':False,'fullAUTOAcceptance':False,'noAutomaticRetry':True,'sourcePinsSha256':pinsha})
 print(json.dumps({'sessions':rows,'error':error}),flush=True)
if error:sys.exit(1)
