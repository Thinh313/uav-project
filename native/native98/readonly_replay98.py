"""Independent verification of retained read-only cases. Cannot produce mission PASS."""
from pathlib import Path
import json,base64,hashlib,sys,importlib.util,collections
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];E=R/'evidence/native98';sp=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);sha=lambda b:hashlib.sha256(b).hexdigest();build=json.loads((E/'build01.json').read_text());results=[]
def chain(path):
 rows=[];head='';last=-1
 for line in path.read_bytes().splitlines():
  r=json.loads(line);body=line.rsplit(b',"sha256":',1)[0]+b'}';assert r['n']==len(rows)+1 and r['previous']==head and sha(body)==r['sha256'];head=r['sha256'];t=r.get('elapsedMs',last);assert t>=last;last=t;rows.append(r)
 return rows,head
for letter in ['a','b','c']:
 run='s098'+letter+'2c41e36548be9071';D=E/'runs'/run;rows,head=chain(D/'android-raw.jsonl');assert rows[0]['kind']=='META'and rows[-1]['kind']=='CLOSED';rx=m.MAVLink(None);rx.robust_parsing=True;events={};intents=[];writes=[];packets=[];noise=0;admitted=False;incoming=[];lastBinding=None;lastSeq=None
 for r in rows:
  b=base64.b64decode(r['dataBase64'],validate=True);k=r['kind']
  if k=='RX':
   for f in rx.parse_buffer(b)or[]:
    if f.get_type()=='BAD_DATA':assert not admitted and all(v in [9,10,13]or 32<=v<=126 for v in bytes(f.data));noise+=len(f.data);assert noise<=1024;continue
    incoming.append(f)
    if f.get_msgId()==0 and f.get_srcSystem()==42 and f.get_srcComponent()==1:assert not f.base_mode&128
  elif k in ['TX_INTENT','TX_WRITTEN']:
   (intents if k=='TX_INTENT'else writes).append(b)
   if k=='TX_WRITTEN':continue
   f=m.MAVLink(None).parse_char(b);assert f.get_srcSystem()==255 and f.get_srcComponent()==190 and f.get_msgId()in [0,20,76];assert lastBinding and lastBinding['wireSha256']==sha(b);seq=f.get_seq();assert lastSeq is None or seq==(lastSeq+1)%256;lastSeq=seq
   if f.get_msgId()==20:assert f.target_system==42 and f.target_component==1 and f.param_index==-1
   if f.get_msgId()==76:assert f.target_system==42 and f.command in [511,512]and f.target_component in [1,100,102,101,154]
   packets.append((f,b))
  else:
   q=json.loads(b);events.setdefault(k,[]).append(q)
   if k in ['FLIGHT_INTENT_BINDING','PAYLOAD_TX_BINDING']:lastBinding=q
   if k in ['PAYLOAD_JOIN_INTENT','PAYLOAD_TX_BINDING','EXPLICIT_GRANT']:admitted=True
 assert intents==writes and 'EXPLICIT_GRANT'not in events and 'AUTO_INTENT'not in events;assert events['META'][0]['sourceId']==build['sourceId'];assert len(events['SOCKET_CONNECTED'])==1;gen=events['SOCKET_CONNECTED'][0]['generation'];final=events['PAYLOAD_STATE'][-1];assert final['generation']==final['transportGeneration']==gen and final['phase']=='CLOSED'and all(x['ownerSid']is None for x in final['payloads'])and all(not x['alive']for x in final['stations']);assert events['CLOSED'][-1]['safeComplete']is False
 peers,peerHead=chain(D/'peers.jsonl');dec={b:m.MAVLink(None)for b in ['A','B']};seen={b:[]for b in dec}
 for p in dec.values():p.robust_parsing=True
 for r in peers:
  if r['kind']=='RX':
   for f in dec[r['bus']].parse_buffer(bytes.fromhex(r['hex']))or[]:
    if f.get_type()!='BAD_DATA':seen[r['bus']].append(bytes(f.get_msgbuf()))
 routed=0
 for f,b in packets:
  if f.get_msgId()==76 and f.target_component in [100,102,101,154]:
   bus='A'if f.target_component in [100,154]else'B';assert b in seen[bus]and b not in seen['B'if bus=='A'else'A'];routed+=1
 closure=json.loads((D/'closure.json').read_text());assert closure['stopped']and closure['error']is None and closure['observerError']is None and not closure['everArmed'];results.append({'run':run,'status':'PASS_READONLY_INTEGRITY_ONLY','nativeRecords':len(rows),'nativeHead':head,'rawSha256':sha((D/'android-raw.jsonl').read_bytes()),'TXpairs':len(intents),'routedDiscovery':routed,'singleSocketGeneration':gen,'noGrantArmAUTO':True,'rolesRevokedAtClose':True,'wireTailBytes':rx.buf_len(),'close':events['CLOSED'][-1],'kindCounts':dict(collections.Counter(r['kind']for r in rows)),'scope':'APK01 read-only captures; not APK02 runtime or mission acceptance'})
result={'status':'PASS_READONLY_INTEGRITY_ONLY','cases':results,'requiredAirborneMission':'NOT_CHECKED','requiredAirborneCameraGimbal':'NOT_CHECKED','requiredOwnedPayloadLossDuringFlight':'NOT_CHECKED','actualImages':0,'hardwareAuthenticated':False};(E/'readonly-independent98.json').open('x').write(json.dumps(result,indent=2));print(json.dumps({'status':result['status'],'cases':len(results),'records':sum(x['nativeRecords']for x in results),'routedDiscovery':sum(x['routedDiscovery']for x in results)}))
