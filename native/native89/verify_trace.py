"""Independent host receiver for Android bench logs. No extraction, control or hardware PASS."""
from pathlib import Path
import json,base64,hashlib,tarfile,math,copy,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/native89'
def strict(raw):
 def pairs(xs):
  d={}
  for k,v in xs:
   assert k not in d,'DUPLICATE_JSON_KEY';d[k]=v
  return d
 def const(x):raise ValueError('NONFINITE_JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=const)
def decode(raw,session):
 assert len(raw)<=1024*1024 and raw.endswith(b'\n'),'TORN_OR_BOUND';previous='';last=-1;out=[]
 for n,line in enumerate(raw.splitlines(),1):
  v=strict(line);assert set(v)=={'n','elapsedMs','previous','payloadBase64','sha256'};body={k:v[k]for k in ['n','elapsedMs','previous','payloadBase64']};assert type(v['n'])is int and v['n']==n and type(v['elapsedMs'])is int and v['elapsedMs']>=0 and v['elapsedMs']>=last and v['previous']==previous,'ORDER_CLOCK_CHAIN';h=hashlib.sha256(json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert h==v['sha256'],'SHA256';p=strict(base64.b64decode(v['payloadBase64'],validate=True));assert p['session']==session,'SESSION_BINDING';out.append({'elapsedMs':v['elapsedMs'],'data':p});previous=h;last=v['elapsedMs']
 assert len(out)<=512 and out[0]['data']['kind']=='SESSION';return out

def semantics(rows):
 counts={};active=None;phases={};frame_pts={};frame_times={};features=set();keys=[];ended=[];stale=[];background=False;last_owned=None;last_frame=None
 for r in rows:
  t=r['elapsedMs'];d=r['data'];k=d['kind'];counts[k]=counts.get(k,0)+1;s=d.get('snapshot',d);v=s.get('video');i=s.get('input')
  assert k not in ['VIDEO_ERROR','ART_SELF_TEST_FAILED'],'ACTUAL_ERROR'
  if s.get('flightAuthority')is not None:assert s['flightAuthority']is False
  if s.get('physicalInputVerified')is not None:assert s['physicalInputVerified']is False
  if s.get('cameraToDisplayLatencyMs','absent')!='absent':assert s['cameraToDisplayLatencyMs']is None
  if i:
   assert i['operational']is False and i['physicalMappingVerified']is False
   if i['mockOwned']:last_owned=t
  if v:assert v['cameraAgeMs']is None and v['cameraToDisplayLatencyMs']is None and v['displayScanoutMeasured']is False and v['source']=='SYNTHETIC_FIXTURE'and v['actualImages']==0
  if k=='SESSION':assert d['operational']is False and d['authorityRestorable']is False and d['source']=='SYNTHETIC_FIXTURE'and d['fixtureSha256']==hashlib.sha256((R/'native/native89/assets/synthetic.webm').read_bytes()).hexdigest()
  if k=='ART_SELF_TEST':
   expected=strict((E/'host-tests02.json').read_bytes())['model'];assert d['status']=='PASS'and d['runtime']=='ANDROID_ART'and d['checks']==expected['checks']and d['names']==expected['names'];features.add('ART_MODEL')
  if k=='FIXTURE_INVENTORY':assert d['sha256']==hashlib.sha256((R/'native/native89/assets/synthetic.webm').read_bytes()).hexdigest()and d['width']==640 and d['height']==360 and d['mime']=='video/x-vnd.on2.vp8'and d['extractorSamples']==23 and d['physicalMediaVerified']is False
  if k=='VIDEO_PREPARE':
   g=d['generation'];assert type(g)is int and(active is None or g>active);active=g;phases[g]='PREPARING';frame_pts[g]=[];frame_times[g]=[]
  if k=='VIDEO_STARTED':
   g=d['generation'];assert g==active and phases[g]=='PREPARING'and s['foreground']and s['focused']and v['generation']==g and v['frameCallbacks']==0 and v['state']=='WAITING_RENDER_CALLBACK';phases[g]='PLAYING';background=False
  if k=='FRAME_CALLBACK':
   g=d['generation'];assert active==g and phases.get(g)=='PLAYING'and not background and s['foreground']and s['focused'];pts=d['textureTimestampNs'];assert type(pts)is int and pts>=0 and(not frame_pts[g]or pts>frame_pts[g][-1]),'TEXTURE_TIMESTAMP_REPLAY';frame_pts[g].append(pts);frame_times[g].append(t);last_frame=(g,t);assert v['generation']==g and v['frameCallbacks']==len(frame_pts[g])and v['producerTimestampNs']==pts and v['state']=='RENDER_CALLBACK_OBSERVED'
  if k=='VIDEO_ENDED':
   g=d['generation'];assert active==g and phases[g]=='PLAYING'and d['callbackProof']is True and len(frame_pts[g])>=2 and frame_times[g][-1]>frame_times[g][0]and v['frameCallbacks']==len(frame_pts[g])and v['state']=='ENDED_WITH_CALLBACKS';phases[g]='ENDED';features.add('NORMAL_DECODE');ended.append({'generation':g,'callbacks':len(frame_pts[g]),'callbackSpanMs':frame_times[g][-1]-frame_times[g][0]})
  if k=='FAULT_PLAYER_PAUSED_RETAIN_FRAME':assert active is not None and phases[active]=='PLAYING';phases[active]='FROZEN'
  if k=='VIDEO_STALE':
   assert active is not None and phases[active]=='FROZEN'and v['state']=='STALLED_NO_AUTO_RESUME'and v['callbackAgeMs']>500 and v['generation']>active;stale.append({'oldGeneration':active,'blockedGeneration':v['generation'],'callbackAgeMs':v['callbackAgeMs']});phases[active]='STALE';active=v['generation'];features.add('FROZEN_RENDER_BLOCKED')
  if k=='VIDEO_STOP':
   g=v['generation'];assert active is None or g>active
   if d['reason']=='ANDROID_BACKGROUND'and active is not None and phases.get(active)=='PLAYING'and last_frame and last_frame[0]==active and t-last_frame[1]<=500:features.add('ACTIVE_VIDEO_BACKGROUND_REVOKED')
   active=g;phases[g]='STOPPED'
  if k in ['ACTIVITY_PAUSED','FOCUS_LOST']:
   assert not i['mockOwned']and not s['watchKeys']and v['state']not in ['WAITING_RENDER_CALLBACK','RENDER_CALLBACK_OBSERVED'];background=True
   if k=='ACTIVITY_PAUSED':
    features.add('ANDROID_BACKGROUND')
    if last_owned is not None and 0<=t-last_owned<=250:features.add('FRESH_MOCK_OWNERSHIP_BACKGROUND_REVOKED')
  if k in ['ACTIVITY_RESUMED_NO_RESTORE','FOCUS_GAINED_NO_RESTORE']:
   assert not i['mockOwned']and v['state']not in ['WAITING_RENDER_CALLBACK','RENDER_CALLBACK_OBSERVED'];features.add('NO_RESTORE')
  if k=='MOCK_ACQUIRED':assert d['acquired']is True and i['mockOwned']and i['neutralSamples']>=3;features.add('MOCK_NEUTRAL_DEADMAN')
  if k=='INPUT_STATE'and i['state']=='STALE_INPUT':assert not i['mockOwned']and i['axis']is None;features.add('INPUT_STALE_REVOKED')
  if k=='INVALID_AXIS_REJECTED':assert not i['mockOwned']and i['axis']is None and i['state']=='INVALID_AXIS';features.add('INVALID_AXIS_REJECTED')
  if k=='ANDROID_JOYSTICK_RAW_UNMAPPED':
   assert d['physicalMappingVerified']is False and isinstance(d['axes'],list)and len(d['axes'])<=16
   for axis in d['axes']:assert type(axis['axis'])is int and isinstance(axis['raw'],(int,float))and not isinstance(axis['raw'],bool)and math.isfinite(axis['raw'])
   features.add('ANDROID_JOYSTICK_CALLBACK_UNMAPPED')
  if k=='ANDROID_KEY_UNATTESTED':
   assert d['clockDomain']=='ANDROID_UPTIME_MILLIS'and d['noControlMapping']is True;delay=d['callbackUptimeMs']-d['eventUptimeMs'];assert d['dispatchDelayMs']==(delay if 0<=delay<=2000 else None),'KEY_CLOCK_MAPPING';keys.append(d);features.add('ANDROID_KEY_CALLBACK')
 measured=sorted(d['dispatchDelayMs']for d in keys if d['dispatchDelayMs']is not None)
 return {'counts':counts,'features':sorted(features),'normalDecode':ended,'stale':stale,'keyCallbacks':len(keys),'keyDispatchP95Ms':None if not measured else measured[math.ceil(len(measured)*.95)-1]}

def load(name):
 result={}
 with tarfile.open(E/name)as t:
  for m in t.getmembers():
   assert not m.issym()and not m.islnk();assert m.name.startswith('bench89/')or m.name=='bench89'
   if m.isfile()and m.name.endswith('.jsonl'):raw=t.extractfile(m).read();session=Path(m.name).stem;result[session]={'raw':raw,'rows':decode(raw,session)}
 return result

def run(name):
 traces=load(name);reports={s:semantics(v['rows'])for s,v in traces.items()};features=set(x for r in reports.values()for x in r['features']);required={'ART_MODEL','NORMAL_DECODE','FROZEN_RENDER_BLOCKED','ANDROID_BACKGROUND','NO_RESTORE','MOCK_NEUTRAL_DEADMAN','INPUT_STALE_REVOKED','INVALID_AXIS_REJECTED','ANDROID_KEY_CALLBACK','ACTIVE_VIDEO_BACKGROUND_REVOKED','FRESH_MOCK_OWNERSHIP_BACKGROUND_REVOKED','ANDROID_JOYSTICK_CALLBACK_UNMAPPED'};assert required<=features,('MISSING_ACTUAL_COVERAGE',required-features);assert len(traces)>=3,'RESTART_SESSION_REQUIRED';return{'status':'PASS','sessions':len(traces),'reports':reports,'requiredCoverage':sorted(required),'physicalInputVerified':False,'remoteCameraVideoVerified':False,'sourceAuthenticated':False,'scope':'ANDROID_ART_CALLBACKS_AND_SYNTHETIC_LOCAL_DECODE_NOT_HERA_OR_DISPLAY_SCANOUT'}
if __name__=='__main__':
 r=run(sys.argv[1]);(E/('trace-verification'+('-'+sys.argv[2]if len(sys.argv)>2 else'')+'.json')).open('x').write(json.dumps(r,indent=2));print(json.dumps(r))
