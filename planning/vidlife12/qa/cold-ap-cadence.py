"""Read-only original transport prefix, independent SHA/CRC and MAVLink CRC.
Not a closed-recording acceptance test. No actor, command or writer API.
"""
import json,hashlib,zlib,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control01.mavlink import Framer
root=R/'evidence/hostdiag11/s01/sessions/hostdiag11-short01/raw/transport-journal'
fr={};counts={};hb={};last={};eof=[];started={};telemetry={};refs=[];head='0'*64;sequence=-1;rows=0
for p in sorted(root.glob('segment-*.jsonl')):
 rawfile=p.read_bytes();refs.append({'path':str(p.relative_to(R)),'bytes':len(rawfile),'sha256':hashlib.sha256(rawfile).hexdigest()})
 assert rawfile.endswith(b'\n')
 for s in rawfile.splitlines():
  row=json.loads(s);b=row['body'];raw=json.dumps(b,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
  assert b['previous']==head and row['crc32']==format(zlib.crc32(raw),'08x') and row['sha256']==hashlib.sha256(bytes.fromhex(head)+raw).hexdigest()
  if sequence>=0:assert b['seq']==sequence+1
  sequence=b['seq'];head=row['sha256'];rows+=1
  v=b.get('payload',{});k=v.get('eventKind');d=v.get('data',{});t=d.get('_observedHostNs')
  if k in ('AP_RELAY_RX','PASSIVE_RX') and d.get('rawHex'):
   wire=bytes.fromhex(d['rawHex'])
   if not started.get(k):
    while wire.startswith(b'0 '):wire=wire[2:]
    if not wire:continue
    started[k]=True
   f=fr.setdefault(k,Framer());counts.setdefault(k,Counter());hb.setdefault(k,[])
   for m in f.feed(wire,t):
    counts[k][m['id']]+=1;last[k]=t
    if k=='AP_RELAY_RX' and m['id'] in(30,33):telemetry.setdefault(m['id'],[]).append({'recordSequence':b['seq'],'hostNs':t,'timeBootMs':int.from_bytes(m['payload'][:4],'little')})
    if m['id']==0:hb[k].append({'recordSequence':b['seq'],'hostNs':t,'wireSequence':m['wireSequence'],'system':m['system'],'component':m['component']})
  if k=='NATIVE_PATH_EOF':eof.append({'recordSequence':b['seq'],'hostNs':t,'side':d['side']})
assert len(eof)==1 and eof[0]['side']=='native'
report={'format':'aeris-vidlife12-independent-cold-ap-cadence','status':'RETAINED_PREFIX_SHA_CRC_AND_MAVLINK_CRC_VERIFIED_NOT_RECORDING_ACCEPTANCE','recordingAccepted':False,'flightAccepted':False,'actorsStarted':False,'clockDomain':'PYTHON_ROOT_MONOTONIC_NS_ONLY','rows':rows,'retainedHead':head,'streams':{k:{'heartbeatPackets':len(hb[k]),'lastAnyMessageNs':last[k],'heartbeatTail':hb[k][-8:],'tailIntervalsMs':[(hb[k][i]['hostNs']-hb[k][i-1]['hostNs'])/1e6 for i in range(max(1,len(hb[k])-8),len(hb[k]))]}for k in hb},'EOF':eof[0],'lastRelayHeartbeatToEOFMs':(eof[0]['hostNs']-hb['AP_RELAY_RX'][-1]['hostNs'])/1e6,'telemetryCadence':{str(k):{'packets':len(v),'hostGapMs':{'median':sorted([(v[i]['hostNs']-v[i-1]['hostNs'])/1e6 for i in range(1,len(v))])[len(v)//2-1],'maximum':max((v[i]['hostNs']-v[i-1]['hostNs'])/1e6 for i in range(1,len(v))),'over250ms':sum(v[i]['hostNs']-v[i-1]['hostNs']>250000000 for i in range(1,len(v)))},'tail':[{'record':v[i]['recordSequence'],'hostNs':v[i]['hostNs'],'hostGapMs':(v[i]['hostNs']-v[i-1]['hostNs'])/1e6,'simBootGapMs':v[i]['timeBootMs']-v[i-1]['timeBootMs']}for i in range(max(1,len(v)-10),len(v))]}for k,v in telemetry.items()},'refs':refs,'caveats':['Different stream rates do not alone prove a specific AP scheduler defect.','No comparison to Node hrtime without mapping.','Source scene age250 and original JS invalidation reason remain separate unproven causes.']}
out=R/'evidence/vidlife12/qa/COLD-AP-CADENCE02.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'out':str(out.relative_to(R)),'rows':rows,'heartbeatPackets':{k:len(v)for k,v in hb.items()},'lastRelayHeartbeatToEOFMs':report['lastRelayHeartbeatToEOFMs']}))
