"""Offline independent receiver: chain replay + semantic provenance/generation checks. No flight claims."""
from pathlib import Path
import json,base64,hashlib,tarfile,sys,math,copy
R=Path(__file__).resolve().parents[2];E=R/'evidence/native90'
def strict(raw):
 def pairs(xs):
  d={}
  for k,v in xs:
   assert k not in d,'DUPLICATE_KEY';d[k]=v
  return d
 def bad(v):raise ValueError('NONFINITE')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def decode(raw,session):
 assert len(raw)<=1048576 and raw.endswith(b'\n'),'TORN_BOUND';previous='';last=-1;rows=[]
 for n,l in enumerate(raw.splitlines(),1):
  v=strict(l);assert set(v)=={'n','elapsedMs','previous','payloadBase64','sha256'}
  b={k:v[k]for k in ['n','elapsedMs','previous','payloadBase64']};assert type(v['n'])is int and v['n']==n and type(v['elapsedMs'])is int and v['elapsedMs']>=last and v['elapsedMs']>=0 and v['previous']==previous,'CHAIN_ORDER_CLOCK'
  assert hashlib.sha256(json.dumps(b,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==v['sha256'],'SHA'
  p=strict(base64.b64decode(v['payloadBase64'],validate=True));assert set(p)=={'session','kind','data'}and p['session']==session,'SESSION';rows.append({'elapsedMs':v['elapsedMs'],**p});previous=v['sha256'];last=v['elapsedMs']
 assert 0<len(rows)<=512 and rows[0]['kind']=='SESSION';return rows
def semantics(rows):
 source=rows[0]['data'].get('sourceId');target=strict((E/'build08.json').read_bytes())['sourceId'];previous=strict((E/'build07.json').read_bytes())['sourceId'];assert source is None or source in[target,previous],'UNKNOWN_SOURCE_ID';qualified=source==target
 active=None;phase={};pts={};times={};features=set();counts={};end=[];stale=[];last_owned=None;last_frame=None;links=[]
 for r in rows:
  k=r['kind'];d=r['data'];t=r['elapsedMs'];counts[k]=counts.get(k,0)+1;s=d.get('snapshot',d);v=s.get('video');i=s.get('input')
  if v:assert v['cameraAgeMs']is None and v['cameraToDisplayLatencyMs']is None and v['displayScanoutMeasured']is False and v['source']=='SYNTHETIC_FIXTURE'and v['actualImages']==0,'VIDEO_PROVENANCE'
  if i:
   assert i['operational']is False and i['physicalMappingVerified']is False,'INPUT_PROVENANCE'
   if i['mockOwned']:last_owned=t
  if k=='SESSION':assert d['fixtureSha256']==hashlib.sha256((R/'native/native90/assets/synthetic.webm').read_bytes()).hexdigest()and d['source']=='SYNTHETIC_FIXTURE'and d['operational']is False and d['authorityRestorable']is False and d['mediaPath']=='ANDROID_WEBVIEW_RVFC'
  if k=='ART_SELF_TEST':
   expected=strict((E/('host-tests08.json'if source else'host-tests05.json')).read_bytes())['model'];assert d['status']=='PASS'and d['runtime']=='ANDROID_ART'and d['checks']==expected['checks']and d['names']==expected['names'];features.add('ART_GUARDS')
  if k=='VIDEO_PREPARE':
   g=d['generation'];assert type(g)is int and(active is None or g>active);active=g;phase[g]='PREPARING';pts[g]=[];times[g]=[]
  if k=='VIDEO_STARTED':
   g=d['generation'];assert g==active and phase[g]=='PREPARING'and v['generation']==g and v['frameCallbacks']==0 and s['foreground']and s['focused'];phase[g]='PLAYING'
  if k=='FRAME_CALLBACK':
   g=d['generation'];assert g==active and phase[g]=='PLAYING'and s['foreground']and s['focused'],'FRAME_AFTER_STOP_OR_WRONG_GENERATION';p=d['mediaTimeNs'];assert type(p)is int and p>=0 and(not pts[g]or p>pts[g][-1]),'MEDIA_TIMELINE_REPLAY';pts[g].append(p);times[g].append(t);assert v['generation']==g and v['frameCallbacks']==len(pts[g])and v['producerTimestampNs']==p and v['state']=='RENDER_CALLBACK_OBSERVED';last_frame=(g,t)
  if k=='VIDEO_ENDED':
   g=d['generation'];assert g==active and phase[g]=='PLAYING'and len(pts[g])>=2 and v['state']=='ENDED_WITH_CALLBACKS'and v['frameCallbacks']==len(pts[g]);phase[g]='ENDED';features.add('WEBVIEW_LOCAL_DECODE');end.append({'generation':g,'callbacks':len(pts[g]),'callbackSpanMs':times[g][-1]-times[g][0]})
  if k=='FAULT_RENDER_PAUSED':assert d['generation']==active and phase[active]=='PLAYING';phase[active]='FROZEN'
  if k=='VIDEO_STALE':
   assert active is not None and phase[active]=='FROZEN'and v['generation']>active and v['state']=='STALLED_NO_AUTO_RESUME'and v['callbackAgeMs']>500;features.add('FREEZE_BLOCKED');stale.append({'generation':active,'callbackAgeMs':v['callbackAgeMs']});phase[active]='STALE';active=v['generation']
  if k=='VIDEO_STOP':
   g=v['generation'];assert active is None or g>active
   if d['reason']in ['FOCUS_LOST','ANDROID_BACKGROUND']and active in phase and phase[active]=='PLAYING'and last_frame and last_frame[0]==active and 0<=t-last_frame[1]<=500:features.add('LIVE_VIDEO_LIFECYCLE_STOP')
   active=g;phase[g]='STOPPED'
  if k in ['ACTIVITY_PAUSED','FOCUS_LOST']:
   assert not i['mockOwned']and not s['watchKeys']and v['state']not in ['WAITING_RENDER_CALLBACK','RENDER_CALLBACK_OBSERVED'];features.add('LIFECYCLE_REVOKE')
   if last_owned is not None and 0<=t-last_owned<=250:features.add('FRESH_MOCK_OWNER_REVOKED')
  if k in ['ACTIVITY_RESUMED_NO_RESTORE','FOCUS_GAINED_NO_RESTORE']:assert not i['mockOwned']and not s['watchKeys']and v['state']not in ['WAITING_RENDER_CALLBACK','RENDER_CALLBACK_OBSERVED'];features.add('NO_AUTO_RESTORE')
  if k=='MOCK_ACQUIRED':assert d['acquired']is True and i['mockOwned']and i['neutralSamples']>=3;features.add('NEUTRAL_DEADMAN')
  if k=='INPUT_STATE'and i['state']=='STALE_INPUT':assert not i['mockOwned']and i['axis']is None;features.add('STALE_INPUT_REVOKED')
  if k=='INVALID_AXIS_REJECTED':assert not i['mockOwned']and i['axis']is None and i['state']=='INVALID_AXIS';features.add('INVALID_AXIS_REJECTED')
  if k=='ANDROID_KEY_UNATTESTED':
   delta=d['callbackUptimeMs']-d['eventUptimeMs'];assert d['clockDomain']=='ANDROID_UPTIME_MILLIS'and d['noControlMapping']is True and d['dispatchDelayMs']==(delta if 0<=delta<=2000 else None),'KEY_CLOCK';features.add('ANDROID_KEY_UNMAPPED')
  if k=='ANDROID_JOYSTICK_RAW_UNMAPPED':
   assert d['physicalMappingVerified']is False and len(d['axes'])<=16
   for a in d['axes']:assert type(a['axis'])is int and type(a['raw'])in [int,float]and math.isfinite(a['raw'])
   features.add('ANDROID_JOYSTICK_UNMAPPED')
  if k=='WORKSPACE_REVIEW_LINK':
   ref=d['reference'];assert d['actualImages']==0 and d['authorityRestorable']is False and len(ref['head'])==64 and ref['revision']>=1;assert ref['phase']=='COMPLETED_MOCK'and len(ref['missionSha256'])==64,'COMPLETED_WORKSPACE_LINK';features.add('REVIEW_HEAD_LINK');links.append(ref)
 return {'qualifiedSource':qualified,'sourceId':source,'features':sorted(features),'counts':counts,'normalDecode':end,'stale':stale,'links':links}
def load(name):
 out={}
 with tarfile.open(E/name)as t:
  for m in t.getmembers():
   assert not m.issym()and not m.islnk();assert m.name=='diagnostics90'or m.name.startswith('diagnostics90/')
   if m.isfile()and m.name.endswith('.jsonl'):
    raw=t.extractfile(m).read();session=Path(m.name).stem;out[session]={'raw':raw,'sha256':hashlib.sha256(raw).hexdigest(),'rows':decode(raw,session)}
 return out
def verify(name,required=True):
 traces=load(name);reports={s:semantics(t['rows'])for s,t in traces.items()};features=set(f for r in reports.values()if r['qualifiedSource']for f in r['features']);needed={'ART_GUARDS','WEBVIEW_LOCAL_DECODE','FREEZE_BLOCKED','LIVE_VIDEO_LIFECYCLE_STOP','FRESH_MOCK_OWNER_REVOKED','LIFECYCLE_REVOKE','NO_AUTO_RESTORE','NEUTRAL_DEADMAN','STALE_INPUT_REVOKED','INVALID_AXIS_REJECTED','ANDROID_KEY_UNMAPPED','ANDROID_JOYSTICK_UNMAPPED','REVIEW_HEAD_LINK'}
 if required:assert needed<=features,needed-features;assert sum(r['qualifiedSource']for r in reports.values())>=4,'RESTART_TRACES'
 return {'status':'PASS','sessions':len(traces),'events':sum(len(t['rows'])for t in traces.values()),'requiredCoverage':sorted(needed),'observedCoverage':sorted(features),'reports':reports,'sha256':{s:t['sha256']for s,t in traces.items()},'scope':'ANDROID_WEBVIEW_SYNTHETIC_MEDIA_AND_UNMAPPED_INPUT_NOT_HERA_OR_ACTUAL_IMAGES'}
if __name__=='__main__':
 result=verify(sys.argv[1],len(sys.argv)<3 or sys.argv[2]!='partial');(E/('trace-verification-'+sys.argv[-1]+'.json')).open('x').write(json.dumps(result,indent=2));print(json.dumps(result))
