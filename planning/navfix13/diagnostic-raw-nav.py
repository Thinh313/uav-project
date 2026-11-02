"""Read-only navigation diagnosis of a closed Android/SITL case, never flight acceptance."""
from pathlib import Path
import argparse,base64,collections,hashlib,importlib.util,json,struct,sys,zlib
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from pilot.betaintegrated01.control01.mavlink import Framer

def H(data):return hashlib.sha256(data).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def need(ok,why):
 if not ok:raise ValueError(why)
def read_transport(raw):
 framers={};packets=collections.defaultdict(list);refs=[];head='0'*64;sequence=-1;total=0;event_counts=collections.Counter()
 for p in sorted((raw/'transport-journal').glob('segment-*.jsonl')):
  data=p.read_bytes();refs.append({'path':str(p),'bytes':len(data),'sha256':H(data)})
  for line in data.splitlines():
   env=json.loads(line);b=env['body'];logical=canonical(b)
   need(b['previous']==head and env['crc32']==format(zlib.crc32(logical),'08x') and env['sha256']==H(bytes.fromhex(head)+logical),'TRANSPORT_CHAIN_OR_CRC')
   need(sequence<0 or b['seq']==sequence+1,'TRANSPORT_SEQUENCE');sequence=b['seq'];head=env['sha256'];total+=1
   v=b.get('payload',{});k=v.get('eventKind');d=v.get('data',{});event_counts[k]+=1
   if k not in ('PASSIVE_RX','AP_RELAY_RX'):continue
   wire=bytes.fromhex(d['rawHex']);t=d['_observedHostNs']
   f=framers.setdefault(k,Framer())
   if f.frames==0 and not f.pending:
    while wire.startswith(b'0 '):wire=wire[2:]
   for m in f.feed(wire,t):
    if m['system']!=42 or m['component']!=1:continue
    mid=m['id'];pl=m['payload'];row={'hostNs':t,'seq':sequence,'wireSequence':m['wireSequence']}
    if mid==24:
     row.update(dict(zip(['timeUsec','latitudeE7','longitudeE7','altitudeMSLmm','HDOPx100','VDOPx100','groundSpeedCms','courseCdeg','fixType','satellites'],struct.unpack('<QiiiHHHHBB',pl[:30]))))
     ext=pl.ljust(52,b'\0');row.update(dict(zip(['ellipsoidAltitudeMm','horizontalAccuracyMm','verticalAccuracyMm','velocityAccuracyMmS','headingAccuracyE5Deg','yawCdeg'],struct.unpack('<iIIIIH',ext[30:52]))))
    elif mid==33:row.update(dict(zip(['APTimeBootMs','latitudeE7','longitudeE7','altitudeMSLmm','relativeAltitudeMm','vxCms','vyCms','vzCms','headingCdeg'],struct.unpack('<IiiiihhhH',pl[:28]))))
    elif mid==30:row.update(APTimeBootMs=int.from_bytes(pl[:4],'little'))
    elif mid==193:row.update(ekfFlags=int.from_bytes(pl[20:22],'little'))
    elif mid==242:
     row.update(dict(zip(['latitudeE7','longitudeE7','altitudeMSLmm'],struct.unpack('<iii',pl[:12]))))
     row['homeTimeUsec']=int.from_bytes(pl[52:60].ljust(8,b'\0'),'little')
    elif mid==253:row.update(text=pl[1:51].rstrip(b'\0').decode(errors='strict'))
    elif mid==0:row.update(armed=bool(pl[6]&128))
    else:continue
    packets[k,mid].append(row)
 need(total>0,'NO_RAW_TRANSPORT')
 framing={k:f.snapshot()for k,f in framers.items()}
 need(all(v['failed']is None and v['pendingBytes']==0 for v in framing.values()),'MAVLINK_PARTIAL_TAIL_OR_FRAMER_FAILURE')
 summary={}
 for (kind,mid),rows in packets.items():
  item={'samples':len(rows),'first':rows[0],'last':rows[-1]}
  if mid==24:item.update(fixTypeCounts=dict(collections.Counter(v['fixType']for v in rows)),satelliteCounts=dict(collections.Counter(v['satellites']for v in rows)),coordinatesCounts={str(k):v for k,v in collections.Counter((r['latitudeE7'],r['longitudeE7'],r['altitudeMSLmm'])for r in rows).items()},maxHAccMm=max(v['horizontalAccuracyMm']for v in rows))
  if mid==193:item['flagsCounts']=dict(collections.Counter(v['ekfFlags']for v in rows))
  if mid==253:item['all']=rows
  if mid in(30,33):item.update(APElapsedMs=rows[-1]['APTimeBootMs']-rows[0]['APTimeBootMs'],hostArrivalSpanNs=rows[-1]['hostNs']-rows[0]['hostNs'],APTimelineMonotonic=all(a['APTimeBootMs']<=b['APTimeBootMs']for a,b in zip(rows,rows[1:])))
  summary[kind+':'+str(mid)]=item
 return {'rawRows':total,'crcAndChainVerified':True,'MAVLinkFramers':framing,'MAVLinkCompletePacketCRCVerified':True,'head':head,'streams':summary,'refs':refs}
def read_fdm(raw):
 codecpath=ROOT/'planning/vidlife12/runtime/source/aeris_runtime/foundation/fdm09.py';spec=importlib.util.spec_from_file_location('diagnostic_fdm09',codecpath);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 state={};head='0'*64;seq=-1;frames=collections.Counter();sensor_first=sensor_last=stage_first=stage_last=None;first_sensor_time=None;max_time_error=0.;rate=1200;refs=[];previous_time=-1.
 context=json.loads((raw/'run-config.json').read_bytes())
 for p in sorted((raw/'journal').glob('segment-*.jsonl')):
  data=p.read_bytes();refs.append({'path':str(p),'bytes':len(data),'sha256':H(data)})
  for line in data.splitlines(keepends=True):
   logical=mod.decode_line(line,context['run'],context['epoch'],head,stage_state=state);env=json.loads(logical);b=env['body'];body=canonical(b)
   need(b['previous']==head and env['crc32']==format(zlib.crc32(body),'08x')and env['sha256']==H(bytes.fromhex(head)+body),'FDM_CHAIN_OR_CRC');need(seq<0 or b['seq']==seq+1,'FDM_SEQUENCE');seq=b['seq'];head=env['sha256'];kind=b['kind'];frame=b['frame']
   if kind in('RX','INTENT','SENT'):frames[kind]+=1
   if kind=='INTENT':
    sensor=json.loads(base64.b64decode(b['payload']['base64'],validate=True));t=sensor['timestamp'];need(t>previous_time,'SENSOR_TIME_NOT_MONOTONIC');previous_time=t;err=abs(t-(frame+1)/rate);max_time_error=max(max_time_error,err)
    sample={'frame':frame,'timestampSeconds':t,'positionNedM':sensor['position'],'velocityNedMs':sensor['velocity'],'gyroBodyRadS':sensor['imu']['gyro']}
    if sensor_first is None:sensor_first=sample
    sensor_last=sample
   if kind=='EVENT' and b['payload'].get('eventKind')=='STAGE':
    frames['STAGE']+=1
    sample={'frame':b['payload']['data']['frame'],**b['payload']['data']['fields']}
    if stage_first is None:stage_first=sample
    stage_last=sample
 need(sensor_first is not None and stage_first is not None,'NO_FDM_SENSOR')
 return {'crcAndChainVerified':True,'head':head,'logicalGroups':dict(frames),'sensorFirst':sensor_first,'sensorLast':sensor_last,'maximumTimestampVsSequential1200HzErrorS':max_time_error,'allSensorTimestampMonotonic':True,'firstStage':stage_first,'lastStage':stage_last,'refs':refs,'codec':{'path':str(codecpath),'sha256':H(codecpath.read_bytes())},'fullRecordingAccepted':False}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--case',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();raw=args.case/'sessions/receiver-runtime05-short01/raw';need(raw.is_dir(),'EXACT_CLOSED_CASE_REQUIRED');need(not args.output.exists(),'OUTPUT_MUST_BE_NEW')
 transport=read_transport(raw);fdm=read_fdm(raw)
 sources={}
 for rel in ['runtime/sim32-instrument01-build/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_Control.cpp','runtime/sim32-instrument01-build/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_Measurements.cpp','runtime/sim32-instrument01-build/ardupilot/libraries/AP_NavEKF3/AP_NavEKF3_VehicleStatus.cpp','runtime/sim32-instrument01-build/ardupilot/libraries/SITL/SIM_JSON.cpp','pilot/betaintegrated01/runtime/physics.py','planning/vidlife12/runtime/source/aeris_runtime/foundation/frame_adapter.py']:
  p=ROOT/rel;sources[rel]=H(p.read_bytes())
 report={'status':'COLD_DIAGNOSIS_ONLY_NOT_GPS_FUSION_ROOT_CAUSE_PROOF','transport':transport,'fdm':fdm,'sourceRefs':sources,'findings':['GPS fix6, position/Home agree; GPS absence or mismatched geographic origin not supported by retained bytes.','Cached SHA-recorded AP reference source sets origin only after GPS quality checks; binary/source equivalence is unattested, and actual internal bias/delayed-GPS readiness remains unobserved.','Physics timestamps derive from all retained1200Hz frames; AP simulation time is about31s, not owner129s.','Do not infer delAngBiasLearned or gpsDataToFuse internal state from public MAVLink flags167.'], 'limits':['Host arrival ordering is not a cross-clock conversion or exact AP internal transition timestamp.','Source-tree relation to binary is a separate candidate build provenance gate; source predicate narrows hypothesis, not an internal-state measurement.','No actors/API/build/signing/source mutation performed.','Incomplete failed journal remains incomplete; no flight acceptance.']}
 args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'output':str(args.output),'bytes':args.output.stat().st_size,'groups':fdm['logicalGroups'],'sensorTimestampLast':fdm['sensorLast']['timestampSeconds']}))
if __name__=='__main__':main()
