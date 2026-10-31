"""Stream original-model oracle, hash-chain, authority and AP observer evidence."""
from pathlib import Path
import collections, hashlib, importlib.util, json, math, struct, sys, zlib
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import MAGIC, HEADER, NAMES, unpack_intent


def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()


def percentile(values):
 s=sorted(values)
 if not s:return {'n':0}
 return {'n':len(s),'p50':s[int((len(s)-1)*.5)],'p95':s[int((len(s)-1)*.95)],'p99':s[int((len(s)-1)*.99)],'max':max(s)}


def records(path):
 chain=bytes(32);seq=0
 with path.open('rb')as f:
  assert f.read(8)==MAGIC
  while True:
   h=f.read(HEADER.size)
   if not h:break
   assert len(h)==HEADER.size,'TORN_HEADER'
   kind,flags,reserved,frame,size,index,ns=HEADER.unpack(h)
   assert kind in NAMES and flags==reserved==0 and size<=16384 and index==seq,'WAL_HEADER'
   body=f.read(size);tail=f.read(36);assert len(body)==size and len(tail)==36,'TORN_BODY'
   digest=hashlib.sha256(chain+h+body).digest()
   assert struct.unpack_from('<I',tail)[0]==zlib.crc32(h+body) and tail[4:]==digest,'CRC_CHAIN'
   yield {'kind':NAMES[kind],'frame':frame,'body':body,'seq':seq,'ns':ns}
   seq+=1;chain=digest


def run(rid):
 assert rid.isalnum() and len(rid)<=24
 out=R/'evidence/simtrain53/runs'/rid;assert not(out/'readback.json').exists()
 config=json.loads((out/'request.json').read_text());result=json.loads((out/'backend-result.json').read_text());closure=json.loads((out/'closure.json').read_text())
 spec=importlib.util.spec_from_file_location('oracle53',R/'evidence/sim32/source-final/pilot/sim32/physics.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
 model=original.Model(original.profile(config['load'],config['wind']))
 phase='HEADER';frames=[];received=None;intent=None;times=[];kinds=collections.Counter();first_frame=None;last=None
 for rec in records(out/'frames.wal'):
  k=rec['kind'];kinds[k]+=1
  if k=='HEADER':assert phase=='HEADER';phase='RX';continue
  if k=='CLOSE':
   assert phase=='RX' and json.loads(rec['body'])['intentAndSentFrames']==len(frames);phase='CLOSED';continue
  assert k==phase,(k,phase)
  if k=='RX':
   received=json.loads(rec['body']);assert received['source']=='ACTUAL_SIMTRAIN53_AP_EXTERNAL_PHYSICS'
   raw=bytes.fromhex(received['rawHex']);assert len(raw)==40
   magic,rate,frame,*pwm=struct.unpack('<HHI16H',raw);assert magic==18458 and rate==1200 and frame==rec['frame']
   if last is not None:assert frame==last+1,'FRAME_DISCONTINUITY'
   if first_frame is None:first_frame=frame
   phase='INTENT'
  elif k=='INTENT':
   body,snapshot=unpack_intent(rec['body']);assert not snapshot
   row=json.loads(body);assert row['frame']==frame and row['servoHex']==received['rawHex'] and row['rate']==1200
   sensors=model.step(pwm,1/1200);expected='\n'+json.dumps(sensors,separators=(',',':'),allow_nan=False)+'\n'
   assert row['sensorUtf8']==expected,('ORIGINAL_SENSOR_BYTES',rid,frame)
   assert json.dumps(row['modelAux'],separators=(',',':'))==json.dumps(model.snapshot(),separators=(',',':')),('ORIGINAL_AUX_BYTES',rid,frame)
   assert row['epoch']==result['epoch'];assert row['hostReceiveNs']<=row['computeStartNs']<=row['computeEndNs']<=rec['ns']
   intent=rec;phase='SENT'
  elif k=='SENT':
   sent=json.loads(rec['body']);assert rec['frame']==frame and rec['seq']>intent['seq'] and sent['returnedBytes']==sent['expectedBytes']==len(expected.encode())
   assert sent['hostSendReturnNs']>=intent['ns'] and rec['ns']>=sent['hostSendReturnNs']
   frames.append(frame);times.append(row['hostReceiveNs']);last=frame;phase='RX'
 assert phase=='CLOSED' and len(frames)==result['frames'] and result['error'] is None
 assert closure['backendExited'] and closure['backendExitCode']==0 and closure['ownedContainerStopped'] and closure['error'] is None
 stages=json.loads((out/'backend-stages.json').read_text());assert len(stages)==len(frames)
 for frame,stage in zip(frames,stages):assert stage[0]==frame and stage[1:]==sorted(stage[1:])
 # Independently parse the closed AP trace; unadmitted shutdown tails stay separate.
 ap_frames=collections.defaultdict(lambda:collections.defaultdict(list));event_kinds=collections.Counter()
 with(out/'ap-timing.bin').open('rb')as f:
  magic,cap,n,failed,size=struct.unpack('<8s4Q',f.read(40));assert magic==b'AERISD02' and n<=cap and failed==0 and size==64
  f.seek(4096)
  for i in range(n):
   ev=struct.unpack('<QQIIQQQQq',f.read(64));assert ev[0]==i and ev[4]<=ev[5];event_kinds[ev[2]]+=1
   if ev[2]in[11,13,14]:ap_frames[ev[1]][ev[2]].append((ev[4],ev[-1]))
 ap_rtt=[]
 for frame in frames:
  g=ap_frames[frame];assert len(g[11])==len(g[13])==len(g[14])==1,('AP_CORRELATION',frame)
  assert g[11][0][1]==40 and g[13][0][1]>0
  ap_rtt.append((g[13][0][0]-g[11][0][0])/1e6)
 pairs=[json.loads(line)for line in(out/'clock-pairs.jsonl').read_text().splitlines()];matched=[p for p in pairs if p['status']=='MATCHED' and p['freshCalibration']]
 assert len(matched)>3
 for p in matched:
  assert p['offsetLowNs']==p['hostSendNs']-p['guestReceiveNs'] and p['offsetHighNs']==p['hostReceiveNs']-p['guestSendNs']
  assert p['offsetLowNs']<=p['offsetHighNs']
 latest={};params={};arms=0;rc_active=0;rc_release=collections.Counter();land=False;takeoff=False;node_brackets=[];command_names=[]
 for line in(out/'mavlink.jsonl').open():
  m=json.loads(line);kind=m['kind'];d=m['data'];at=int(m['nodeNs'])
  if kind=='AP_RX_DECODED':
   assert d['system']==42 and d['component']==1
   latest[d['id']]={'f':d['fields'],'at':at}
   if d['id']==22:params[d['fields']['param_id']]={'f':d['fields'],'at':at}
  elif kind=='GCS_TX_REQUEST':
   if d['id']!=0:assert d['fields']['target_system']==42 and d['fields']['target_component']==1
   f=d['fields']
   if d['id']==76:command_names.append(f['command'])
   if d['id']==76 and f['command']==400 and f['param1']==1:
    arms+=1
    def fresh(mid,limit=3000):assert mid in latest and 0<=(at-latest[mid]['at'])/1e6<=limit
    for mid in [0,1,24,193,242]:fresh(mid)
    fresh(148,30000)
    assert latest[0]['f']['custom_mode']==4 and not(latest[0]['f']['base_mode']&128)
    health=latest[1]['f'];assert health['onboard_control_sensors_enabled']&0x10000000 and health['onboard_control_sensors_health']&0x10000000
    assert health['onboard_control_sensors_health']&39==39
    assert latest[193]['f']['flags']&55==55 and not(latest[193]['f']['flags']&1024)
    assert latest[24]['f']['fix_type']>=3 and latest[24]['f']['satellites_visible']>=6
    assert latest[148]['f']['flight_sw_version']>>8==0x040701
    for name,value,typ in [('FS_GCS_ENABLE',1,2),('FS_GCS_TIMEOUT',5,9),('FS_OPTIONS',16,6),('MAV_GCS_SYSID',255,4)]:
     v=params[name];assert 0<=(at-v['at'])/1e6<=30000 and v['f']['param_value']==value and v['f']['param_type']==typ
    home=latest[242]['f'];assert abs(home['latitude']/1e7-10.854)<1/111320 and abs(home['longitude']/1e7-106.807)<1/111320 and abs(home['altitude']/1000-10)<=.5
  elif kind=='RC_TX_INTENT':
   b=bytes.fromhex(d['rawHex']);assert b[0]==253 and b[1]==18 and b[7:10]==bytes([70,0,0]) and b[26:28]==bytes([42,1])
   assert list(struct.unpack('<8H',b[10:26]))==d['channels']
   if d['channels'][:4]==[0,0,0,0]:rc_release[d['reason']]+=1
   else:
    assert latest[0]['f']['custom_mode']==5 and latest[0]['f']['base_mode']&128
    if d['channels'][:4]!=[1500]*4:rc_active+=1
  elif kind=='TAKEOFF_PHYSICS_AND_LOITER_OBSERVED':takeoff=True;assert d['mode']=='LOITER' and d['physics']['position'][2]<-4.5
  elif kind=='LAND_GROUND_DISARM_OBSERVED':land=True;assert d['physics']['ground'] and d['observed']['armed'] is False
  elif kind=='CLOCK_NODE_BACKEND_BRACKET' and d['status']=='MATCHED':
   assert int(d['nodeMinusBackendLowNs'])==int(d['nodeSendNs'])-int(d['backendReceiveNs']) and int(d['nodeMinusBackendHighNs'])==int(d['nodeReceiveNs'])-int(d['backendSendNs'])
   assert int(d['nodeMinusBackendLowNs'])<=int(d['nodeMinusBackendHighNs']);node_brackets.append((int(d['nodeMinusBackendHighNs'])-int(d['nodeMinusBackendLowNs']))/1e6)
 assert node_brackets
 wall=(times[-1]-times[0])/1e9;rtf=(len(frames)-1)/1200/wall
 assert abs(rtf-result['activeReceiveRTF'])<1e-12
 windows=collections.defaultdict(list)
 for i,t in enumerate(times):windows[(t-times[0])//5_000_000_000].append((i,t))
 report={'status':'PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION','run':rid,'profile':config,
  'frames':len(frames),'exactOriginalSensorAndAuxFrames':len(frames),'walRecords':dict(kinds),'frameContinuity':'NO_ADMITTED_FRAME_GAP_DUPLICATE_OR_MISSING_SEND_RETURN',
  'actualAPReceiveParseFrames':len(frames),'apEvents':n,'apEventKinds':dict(event_kinds),'unadmittedAPTailFrames':sorted(set(ap_frames)-set(frames)),
  'activeReceiveRTF':rtf,'wholeRunRTFGe1':rtf>=1,'wallSeconds':wall,'modelSeconds':len(frames)/1200,
  'fiveSecondWindows':[{'window':int(k),'frames':len(v),'RTF':(v[-1][0]-v[0][0])/1200/((v[-1][1]-v[0][1])/1e9)}for k,v in windows.items()if len(v)>1],
  'hostReceiveGapsMs':percentile([(b-a)/1e6 for a,b in zip(times,times[1:])]),
  'hostComputeMs':percentile([(s[3]-s[2])/1e6 for s in stages]),'hostDurableIntentMs':percentile([(s[4]-s[3])/1e6 for s in stages]),
  'apServoToSensorReceiveMs':percentile(ap_rtt),'guestHostClock':{'statuses':dict(collections.Counter(p['status']for p in pairs)),'offsetIntervalWidthMs':percentile([(p['offsetHighNs']-p['offsetLowNs'])/1e6 for p in matched])},
  'nodeBackendClockIntervalWidthMs':percentile(node_brackets),'prearmDecisionsIndependentlyChecked':arms,'manualNonNeutralRCFrames':rc_active,'releaseReasons':dict(rc_release),
  'takeoffAndLandPhysicalObservations':takeoff and land,'scope':'Scoped simulator control/raw integrity; not full G1/pacing/projector/Hera/council acceptance',
  'rateHz':1200,'speedup':1,'capUs':500000,'fullG1Accepted':False,'actualImages':0,
  'filesSha256':{p.name:sha(p)for p in[out/'frames.wal',out/'mavlink.jsonl',out/'ap-timing.bin',out/'backend-stages.json',out/'clock-pairs.jsonl']}}
 with(out/'readback.json').open('x')as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items()if k in['run','frames','status','activeReceiveRTF','prearmDecisionsIndependentlyChecked','manualNonNeutralRCFrames','takeoffAndLandPhysicalObservations']}),flush=True)


if __name__=='__main__':
 for rid in sys.argv[1:]:run(rid)
