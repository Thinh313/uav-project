"""Read-only receiver, Python upstream dialect; never imports Java/JS flight gates."""
from pathlib import Path
import json,hashlib,base64,struct,math,sys,importlib.util,collections
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];E=R/'evidence/native95';run=sys.argv[1];D=E/'runs'/run
sha=lambda b:hashlib.sha256(b).hexdigest()
oracle=R/'pilot/apstream40/oracle-v2.py'
assert sha(oracle.read_bytes())==json.loads((D/'runtime-pins-at-start.json').read_text())['files']['pilot/apstream40/oracle-v2.py']
spec=importlib.util.spec_from_file_location('receiver95_upstream',oracle);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def chain(path,clock):
 raw=path.read_bytes();assert raw.endswith(b'\n'),'TORN_JOURNAL';previous='';rows=[];last=-1
 for line in raw.splitlines():
  d=json.loads(line);body=line.rsplit(b',"sha256":',1)[0]+b'}'
  assert d['n']==len(rows)+1 and d['previous']==previous and sha(body)==d['sha256'],'CHAIN'
  t=int(d[clock]);assert t>=last,'CLOCK_REGRESSION';last=t;previous=d['sha256'];rows.append(d)
 return rows
rows=chain(D/'android-raw.jsonl','elapsedMs');observer=chain(D/'observer.jsonl','hostMonoNs')
def payload(r):return base64.b64decode(r['dataBase64'],validate=True)
derived=[dict(r,data=json.loads(payload(r))) for r in rows if r['kind'] not in ['RX','TX_INTENT','TX_WRITTEN']]
one=lambda k:next(r for r in derived if r['kind']==k)
meta=one('META')['data'];plan=meta['document']['compiled']['plan'];review=json.loads((D/'review.json').read_text());launch=json.loads((D/'launch.json').read_text());closure=json.loads((D/'closure.json').read_text())
assert meta['ownedLaunchAssertion']=={k:launch[k] for k in meta['ownedLaunchAssertion']}
builds=[json.loads(p.read_text()) for p in E.glob('build[0-9][0-9].json')]
matching=[b for b in builds if b['sourceId']==meta['sourceId']];assert len(matching)==1
assert sha((R/matching[0]['apk']).read_bytes())==matching[0]['sha256']
assert meta['clock']=='ANDROID_ELAPSED_REALTIME_MS' and meta['notHardwareAuthenticated'] is True
assert rows[-1]['kind']=='CLOSED' and one('CLOSED')['data']['safeComplete'] is True
assert review['rawHead']==rows[-1]['sha256'] and review['rawRecords']==len(rows)
assert review['run']==run and review['planSha256']==plan['sha256'] and review['missionSha256']==plan['missionSha256']
assert review['accepted'] and review['native95']['safeComplete'] and review['failure'] is None and not review['aborted']
assert review['actualImages']==0 and review['authorityRestorable'] is False and review['sourceArchitecture95']=='ANDROID_DIRECT_TCP_NO_HOST_GCS'
intents=[r for r in rows if r['kind']=='TX_INTENT'];written=[r for r in rows if r['kind']=='TX_WRITTEN']
assert len(intents)==len(written)>0
assert all(a['n']<b['n'] and payload(a)==payload(b) for a,b in zip(intents,written)),'INTENT_WRITTEN_PAIR'
assert closure['stopped'] and not closure['error'] and not closure['observerError']
assert closure['observerRecords']==len(observer) and closure['observerHead']==observer[-1]['sha256'] and closure['observerTransmittedPayloadBytes']==0
assert launch['hostGCSController'] is False and launch['hostGCSTransmittedPayloadBytes']==0
assert closure['minFreeBytes']>=20*2**30
def frames(rs,kind=None):
 decoder=m.MAVLink(None);decoder.robust_parsing=True;result=[];noise=bytearray()
 for r in rs:
  if kind and r['kind']!=kind:continue
  data=payload(r) if kind else bytes.fromhex(r['hex'])
  for f in decoder.parse_buffer(data) or []:
   if f.get_type()=='BAD_DATA':
    noise.extend(bytes(f.data));continue
   result.append({'n':r['n'],'t':int(r['elapsedMs'] if kind else r['hostMonoNs'])/(1 if kind else 1e6),'f':f})
 assert decoder.buf_len()==0,'PARTIAL_FRAME_TAIL'
 assert len(noise)<=1088 and all(v in [9,10,13] or 32<=v<=126 for v in noise),'NON_MAVLINK_NOISE'
 return result,noise.decode()
rx,noise=frames(rows,'RX');tx,txnoise=frames(rows,'TX_INTENT');up,upnoise=frames(observer)
assert not txnoise and not upnoise
assert not noise or 'Init ArduCopter V4.7.1 (dbe79216)' in noise
selected=lambda f:f.get_srcSystem()==42 and f.get_srcComponent()==1
rx=[r for r in rx if selected(r['f'])];up=[r for r in up if selected(r['f'])]
assert all(r['f'].get_srcSystem()==255 and r['f'].get_srcComponent()==190 and r['f'].get_msgId()!=23 for r in tx)
assert all(r['f'].get_msgId()==0 or r['f'].target_system==42 and r['f'].target_component==1 for r in tx)
fw=[r['f'] for r in rx if r['f'].get_msgId()==148]
assert fw and all(f.flight_sw_version==67568127 and bytes(f.flight_custom_version)==b'dbe79216' for f in fw)
grant=one('EXPLICIT_GRANT');lease=grant['elapsedMs']+30000
parameters={r['f'].param_id:r for r in rx if r['f'].get_msgId()==22 and r['n']<grant['n']}
for rule in json.loads((E/'native-profile.json').read_text()):
 r=parameters[rule['name']];f=r['f'];assert f.param_type==rule['type'] and rule['low']<=f.param_value<=rule['high'] and 0<=grant['elapsedMs']-r['t']<=10000
for r in tx:
 f=r['f']
 if f.get_msgId() in [44,73,43,51,47] or f.get_msgId()==76 and f.command in [176,400]:assert grant['n']<r['n'] and r['t']<=lease,'VOLATILE_GRANT'
sent=[r['f'] for r in tx if r['f'].get_msgId()==73];expected=plan['compiled']['items'];assert len(sent)==len(expected)==12
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
for f,item in zip(sent,expected):
 for key in ['seq','command','frame','x','y','autocontinue','mission_type']:assert getattr(f,key)==item[key],key
 for key in ['param1','param2','param3','param4','z']:assert getattr(f,key)==f32(item[key]),key
reads=[r for r in rx if r['f'].get_msgId()==73 and r['f'].target_system==255 and r['f'].target_component==190]
assert len(reads)==2*len(expected)
for cycle in [reads[:12],reads[12:]]:
 home=next(r['f'] for r in reversed(rx) if r['n']<cycle[-1]['n'] and r['f'].get_msgId()==242)
 for r,item in zip(cycle,expected):
  f=r['f'];assert f.seq==item['seq'] and f.command==item['command']
  if f.seq==0:
   assert abs(f.x-home.latitude)<=1 and abs(f.y-home.longitude)<=1 and abs(f.z-home.altitude/1000)<.02;continue
  assert f.frame in [item['frame'],{6:3,5:0}.get(item['frame'],item['frame'])] or item['frame']==2 and f.frame==0 and f.command in [178,206,20] and f.x==f.y==f.z==0
  for key in ['x','y']:assert getattr(f,key)==item[key]
  for key in ['param1','param2','param3','param4','z']:assert abs(getattr(f,key)-f32(item[key]))<1e-5
camera=[f for f in sent if f.command==206];assert len(camera)==4 and sum(f.param1>0 for f in camera)==2
auto=next(r for r in tx if r['f'].get_msgId()==76 and r['f'].command==176 and r['f'].param2==3)
assert reads[-1]['n']<auto['n']
hr=one('POST_ARM_HOME_REVIEW_REQUIRED');ai=one('AUTO_INTENT');home=hr['data']['postArmHome']
assert hr['n']<ai['n']<auto['n'] and hr['data']['sha256']==ai['data']['homeReviewSha256'] and ai['elapsedMs']<=hr['data']['expiresAtMs']
near=lambda f:math.hypot((f.lat/1e7-home['lat'])*111319,(f.lon/1e7-home['lon'])*111319*math.cos(home['lat']*math.pi/180))
def execution(frames,threshold=None):
 if threshold is not None:frames=[r for r in frames if r['n']>threshold]
 hbs=[r for r in frames if r['f'].get_msgId()==0]
 armed=[r for r in hbs if r['f'].base_mode&128];assert armed and all(r['f'].custom_mode==3 for r in armed)
 reached={r['f'].seq for r in frames if r['f'].get_msgId()==46};assert all(i['seq'] in reached for i in expected if i['command']==16 and i['seq']>0)
 assert expected[-1]['command']==20 and any(r['f'].get_msgId() in [42,46] and r['f'].seq==len(expected)-1 for r in frames)
 end=hbs[-1];ground=next(r for r in reversed(frames) if r['f'].get_msgId()==245);pos=next(r for r in reversed(frames) if r['f'].get_msgId()==33)
 assert not end['f'].base_mode&128 and ground['f'].landed_state==1 and abs(pos['f'].relative_alt)<1000 and near(pos['f'])<5
 assert abs(end['t']-ground['t'])<1800 and abs(end['t']-pos['t'])<1800
 hb=land=current=first=previous=witness=None
 target=next(i for i in expected if i['command']==22);nav=next(i for i in expected if i['command']==16 and i['seq']>0)
 for r in frames:
  f=r['f'];t=r['t'];id=f.get_msgId()
  if id==0:hb=r
  if id==245:land=r
  if id==42:current=r
  if id!=33:continue
  usable=hb and land and current and all(0<=t-x['t']<=1500 for x in [hb,land,current]) and hb['f'].custom_mode==3 and hb['f'].base_mode&128 and land['f'].landed_state==2 and target['seq']<=current['f'].seq<=nav['seq'] and near(f)<=3 and abs(f.relative_alt/1000-target['z'])<=1 and abs(f.alt/1000-home['amsl']-f.relative_alt/1000)<=.5
  if not usable or previous and (t<=previous['t'] or t-previous['t']>1500 or f.time_boot_ms<=previous['f'].time_boot_ms):first=previous=None;continue
  first=first or r
  if t-first['t']>=300:witness=(first['f'].time_boot_ms,f.time_boot_ms);break
  previous=r
 assert witness,'TAKEOFF_GEOMETRY'
 return witness
witness=execution(rx,auto['n'])
assert witness==(review['execution']['takeoffWitness']['first']['bootMs'],review['execution']['takeoffWitness']['last']['bootMs'])
# Observer is a different serial stream and clock; qualify AUTO interval by its own observed mode.
start=next(r['n'] for r in up if r['f'].get_msgId()==0 and r['f'].custom_mode==3 and r['f'].base_mode&128)
execution(up,start-1)
for r in rx:
 f=r['f']
 if r['n']>auto['n'] and f.get_msgId()==242:assert (f.latitude,f.longitude,f.altitude)==(round(home['lat']*1e7),round(home['lon']*1e7),round(home['amsl']*1000))
result={'status':'PASS','run':run,'nativeRecords':len(rows),'nativeHead':rows[-1]['sha256'],'apkSha256':matching[0]['sha256'],'sourceId':meta['sourceId'],'nativeTxFrames':len(tx),'nativeRxFrames':len(rx),'observerRecords':len(observer),'observerFrames':len(up),'missionItems':len(sent),'readbackCycles':2,'cameraCommands':len(camera),'parameterWrites':0,'actualImages':0,'typedParameterChecks':23,'takeoffWitnessBootMs':witness,'groundDisarmNearHome':True,'nativeAndObserverExecution':True,'clockDomains':'ANDROID_ELAPSED_REALTIME_MS and HOST_MONOTONIC_NS verified separately; no clock identity claim','sourceAuthentication':'OWNED_LAUNCH_ASSERTION_NOT_HARDWARE_AUTHENTICATION','scope':'INTERNAL_QUAD_SITL_NOT_HERA_NOT_PACING','oracleSha256':sha(oracle.read_bytes()),'startupAscii':noise}
(D/'receiver95.json').open('x').write(json.dumps(result,indent=2));print(json.dumps(result))
