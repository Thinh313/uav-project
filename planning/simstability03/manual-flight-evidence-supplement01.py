#!/usr/bin/env python3
"""Read retained command acknowledgements, typed parameters and Home only."""
import hashlib,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];run='rc8f9c0bfcc3a4563b492';p=ROOT/'.local/simstability03/receiver03/evidence/simhand01/runs'/run/'mavlink.jsonl';raw=p.read_bytes();rows=[json.loads(l)for l in raw.splitlines()];pairs=[]
for q in rows:
 d=q['data']
 if q['kind']!='GCS_TX_REQUEST'or d['id']!=76 or d['fields']['command']not in[176,400,22]:continue
 c=d['fields'];nxt=next((x['index']for x in rows if x['index']>q['index']and x['kind']=='GCS_TX_REQUEST'and x['data']['id']==76 and x['data']['fields']['command']==c['command']),10**15)
 ack=next(x for x in rows if q['index']<x['index']<nxt and x['kind']=='AP_RX_DECODED'and x['data']['id']==77 and x['data']['fields']['command']==c['command']and x['data']['fields']['result']==0)
 def obs(x):
  if x['kind']!='AP_RX_DECODED'or x['data']['id']!=0:return False
  f=x['data']['fields'];return f['custom_mode']==c['param2']if c['command']==176 else bool(f['base_mode']&128)
 hb=next(x for x in rows if q['index']<x['index']<nxt and obs(x));pairs.append({'txIndex':q['index'],'command':c['command'],'requestedMode':c.get('param2'),'acceptedAckIndex':ack['index'],'observedHeartbeatIndex':hb['index'],'latencyAckMs':(int(ack['nodeNs'])-int(q['nodeNs']))/1e6,'sameCommandNextTxBoundary':nxt if nxt<10**15 else None})
approval=next(x for x in rows if x['kind']=='EXPLICIT_PREFLIGHT_APPROVAL');prior=[x for x in rows if x['index']<approval['index']and x['kind']=='AP_RX_DECODED'];parameters={}
for name,(value,typ)in {'FS_GCS_ENABLE':(1,2),'FS_GCS_TIMEOUT':(5,9),'FS_OPTIONS':(16,6),'MAV_GCS_SYSID':(255,4)}.items():
 q=next(x for x in reversed(prior)if x['data']['id']==22 and x['data']['fields']['param_id']==name);f=q['data']['fields'];assert f['param_value']==value and f['param_type']==typ;age=(int(approval['nodeNs'])-int(q['nodeNs']))/1e6;assert 0<=age<=30000;parameters[name]={'value':value,'type':typ,'rawIndex':q['index'],'ageAtApprovalMs':age}
fw=next(x for x in reversed(prior)if x['data']['id']==148);assert fw['data']['fields']['flight_sw_version']>>8==0x040701
hq=next(x for x in reversed(prior)if x['data']['id']==242);h=hq['data']['fields'];lat=h['latitude']/1e7;lon=h['longitude']/1e7;amsl=h['altitude']/1000;dx=6378137*math.cos(math.radians(10.854))*math.radians(lon-106.807);dy=6378137*math.radians(lat-10.854);distance=math.hypot(dx,dy);assert distance<=1 and abs(amsl-10)<=.5;homeAge=(int(approval['nodeNs'])-int(hq['nodeNs']))/1e6;assert 0<=homeAge<=5000
assert hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
report={'format':'aeris-simstability03-command-parameter-home-audit','status':'PASS_SCOPED_RAW_CHECKS','run':run,'inputSha256':hashlib.sha256(raw).hexdigest(),'scriptSha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'pairs':pairs,'parameters':parameters,'firmware':{'rawIndex':fw['index'],'word':fw['data']['fields']['flight_sw_version'],'version':'4.7.1'},'Home':{'rawIndex':hq['index'],'lat':lat,'lon':lon,'amsl':amsl,'distanceFromReferenceM':distance,'ageAtApprovalMs':homeAge,'approvedHash':approval['data']['home'],'approvedHashScope':'RECORDED_OPERATOR_APPROVAL_HASH; SPHERICAL_DISTANCE_INDEPENDENTLY_CHECKED_HERE'},'authorityRestoreOrHardwareAcceptance':'NOT_INFERRED'}
out=ROOT/'evidence/simstability03/manual-flight-evidence-supplement01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'pairs':len(pairs),'typedParameters':len(parameters),'HomeDistanceM':distance,'HomeAgeMs':homeAge,'out':str(out)}))
