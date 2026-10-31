"""Independent closed-raw native flight/payload + AP router replay. Never connects or sends commands."""
from pathlib import Path
import json,base64,hashlib,math,struct,sys,importlib.util,subprocess
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];E=R/'evidence/native98';D=E/'runs'/sys.argv[1];case=sys.argv[2];assert case in ['nominal','loss'];sha=lambda b:hashlib.sha256(b).hexdigest();sp=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def chain(path):
 rows=[];head='';last=-1
 for line in path.read_bytes().splitlines():
  r=json.loads(line);body=line.rsplit(b',"sha256":',1)[0]+b'}';assert r['n']==len(rows)+1 and r['previous']==head and sha(body)==r['sha256'];head=r['sha256'];t=r.get('elapsedMs',last);assert t>=last;last=t;rows.append(r)
 return rows,head
rows,head=chain(D/'android-raw.jsonl');assert rows[0]['kind']=='META'and rows[-1]['kind']=='CLOSED';meta=json.loads(base64.b64decode(rows[0]['dataBase64']));build=json.loads((E/'build02.json').read_text());assert meta['sourceId']==build['sourceId']and meta['ownedLaunchAssertion']['run']==D.name;doc=meta['document'];plan=doc['compiled']['plan'];expected=plan['compiled']['items'];semantic=subprocess.run(['node',str(R/'native/native96/receiver_semantic96.mjs')],input=json.dumps(doc).encode(),capture_output=True,timeout=30);assert semantic.returncode==0,semantic.stderr
rx=m.MAVLink(None);rx.robust_parsing=True;incoming=[];outgoing=[];states=[];events={};bindings=[];pending=None;prevSeq=None;noise=0;admitted=False;lastState=None;lastPayloadIntent=None;hb=None;pos=None;lastNativeBinding=None;writePairs=0
for r in rows:
 b=base64.b64decode(r['dataBase64'],validate=True);kind=r['kind']
 if kind=='RX':
  for f in rx.parse_buffer(b)or[]:
   if f.get_type()=='BAD_DATA':assert not admitted and r['elapsedMs']-rows[0]['elapsedMs']<15000 and all(v in[9,10,13]or 32<=v<=126 for v in bytes(f.data));noise+=len(f.data);assert noise<=1024;continue
   incoming.append((r,f))
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:
    if f.get_msgId()==0:hb=(r,f)
    if f.get_msgId()==33:pos=(r,f)
 elif kind in ['TX_INTENT','TX_WRITTEN']:
  p=m.MAVLink(None);f=p.parse_char(b);assert f is not None and p.buf_len()==0 and f.get_srcSystem()==255 and f.get_srcComponent()==190
  if kind=='TX_WRITTEN':assert pending==b;pending=None;writePairs+=1;continue
  assert pending is None;pending=b;seq=f.get_seq();assert prevSeq is None or seq==(prevSeq+1)%256;prevSeq=seq;assert lastNativeBinding and lastNativeBinding['wireSha256']==sha(b)
  entry={'row':r,'frame':f,'bytes':b,'binding':lastNativeBinding,'stateBefore':lastState,'intent':lastPayloadIntent,'hbBefore':hb,'positionBefore':pos};outgoing.append(entry)
  if f.get_msgId()==76 and f.target_component in [100,102,101,154]:
   admitted=True;assert f.target_system==42 and f.command in [512,2000,531,532,1001,1000]and f.confirmation==0 and lastNativeBinding.get('preparedHex');prepared=bytes.fromhex(lastNativeBinding['preparedHex']);pf=m.MAVLink(None).parse_char(prepared);assert pf.get_msgId()==f.get_msgId()and prepared[5:10]==b[5:10]and prepared[10:-2]==b[10:-2]and sha(prepared)==lastNativeBinding['preparedSha256']
   if f.command!=512:
    assert lastPayloadIntent and lastState;intent=lastPayloadIntent;payload=next(p for p in lastState['payloads']if p['id']==intent['payload']);station=next(s for s in lastState['stations']if s['sid']==intent['sid']);assert payload['ownerSid']==station['sid']and station['alive']and payload['proposal']is None and payload['fresh']and r['elapsedMs']<payload['leaseUntilMs']and r['elapsedMs']-station['seenMs']<=15000;assert intent['generation']==lastState['generation']==lastState['transportGeneration']and intent['revision']==lastState['revision'];assert f.command=={'capture':2000,'zoom':531,'focus':532,'authority':1001,'gimbal':1000}[intent['operation']];assert f.target_component==(154 if intent['operation']in ['authority','gimbal']else{'front':100,'center':102,'rear':101}[intent['payload']]);assert hb and pos and hb[1].base_mode&128 and hb[1].custom_mode==3 and pos[1].relative_alt>3000 and r['elapsedMs']-hb[0]['elapsedMs']<=1500 and r['elapsedMs']-pos[0]['elapsedMs']<=1500,'NOT_AIRBORNE_AUTO_OVERLAP'
  else:
   assert 'intentSha256'in lastNativeBinding
   if f.get_msgId()!=0:assert f.target_system==42 and f.target_component==1 and f.get_msgId()in [20,76,44,73,43,51,47];assert f.get_msgId()!=76 or f.command in [511,512,176,400]
 else:
  q=json.loads(b);events.setdefault(kind,[]).append((r,q))
  if kind=='PAYLOAD_STATE':lastState=q;states.append((r,q))
  if kind=='PAYLOAD_COMMAND_INTENT':lastPayloadIntent=q
  if kind in ['FLIGHT_INTENT_BINDING','PAYLOAD_TX_BINDING']:lastNativeBinding=q
  if kind in ['EXPLICIT_GRANT','PAYLOAD_JOIN_INTENT']:admitted=True
assert pending is None and writePairs==len(outgoing)and rx.buf_len()==0
assert len(events['SOCKET_CONNECTED'])==1 and events['SOCKET_CONNECTED'][0][1]['generation']==lastState['generation'];assert lastState['phase']=='CLOSED'and not lastState['open']and all(p['ownerSid']is None for p in lastState['payloads'])and all(not s['alive']for s in lastState['stations'])and lastState['actualImages']==0 and lastState['executionProven']is False and lastState['authorityRestorable']is False
# Exact compiled upload; AP Home/readback exceptions are independently bounded as in previous receiver.
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];uploaded=[e['frame']for e in outgoing if e['frame'].get_msgId()==73];assert len(uploaded)==len(expected)
for f,e in zip(uploaded,expected):
 for key in ['seq','command','frame','x','y','autocontinue','mission_type']:assert getattr(f,key)==e[key]
 for key in ['param1','param2','param3','param4','z']:assert getattr(f,key)==f32(e[key])
assert events['PREFLIGHT'][-1][1]['assessment']['state']=='READY_SCOPED_READONLY';assert events['READBACK_VERIFIED'][-1][1]['matches']is True and events['POST_ARM_READBACK'][-1][1]['matches']is True;assert events['POST_ARM_HOME_REVIEW_REQUIRED']and events['AUTO_OBSERVED']and events['TAKEOFF_GEOMETRY_OBSERVED']
peers,peerHead=chain(D/'peers.jsonl');parsers={k:m.MAVLink(None)for k in ['A','B']};seen={k:[]for k in parsers};ptx={k:[]for k in parsers};bus={100:'A',154:'A',102:'B',101:'B'}
for p in parsers.values():p.robust_parsing=True
for r in peers:
 if r['kind']=='RX':
  for f in parsers[r['bus']].parse_buffer(bytes.fromhex(r['hex']))or[]:
   if f.get_type()!='BAD_DATA':seen[r['bus']].append(bytes(f.get_msgbuf()))
 if r['kind']=='TX':ptx[r['bus']].append(bytes.fromhex(r['hex']))
proof=[]
for e in outgoing:
 f=e['frame']
 if f.get_msgId()!=76 or f.target_component not in bus:continue
 target=bus[f.target_component];assert e['bytes']in seen[target]and e['bytes']not in seen['B'if target=='A'else'A'];binding=e['binding'];approval=next(q for _,q in events['PAYLOAD_TX_APPROVAL']if q['id']==binding['id']);assert approval['generation']==lastState['generation']and e['row']['elapsedMs']<=approval['atMs'];op=None
 if f.command!=512:
  t=next(t for t in lastState['transactions']if t['id']==binding['id']);op=t['operation'];q=e['intent'];assert approval['ownerSid']==q['sid']and approval['intentRevision']==q['revision']and approval['atMs']<next(p for p in e['stateBefore']['payloads']if p['id']==q['payload'])['leaseUntilMs']
  if case=='nominal':
   assert t['state']=='OBSERVATION_CONSISTENT_UNATTRIBUTED';frames=[(r,x)for r,x in incoming if r['n']>e['row']['n']and x.get_srcSystem()==42 and x.get_srcComponent()==f.target_component];ack=next((r,x)for r,x in frames if x.get_msgId()==77 and x.command==f.command and x.result==0 and x.target_system==255 and x.target_component==190);assert bytes(ack[1].get_msgbuf())in ptx[target]
   def match(x):
    if op=='capture':return x.get_msgId()==263 and x.camera_id==0 and x.capture_result==1
    if op=='authority':return x.get_msgId()==281 and x.gimbal_device_id==t['device']and x.primary_control_sysid==255 and x.primary_control_compid==190
    if op=='gimbal'and x.get_msgId()==285 and x.gimbal_device_id==t['device']and x.target_system==255 and x.target_component==190 and x.failure_flags==0:
     w,a,b,c=x.q;pitch=math.degrees(math.asin(max(-1,min(1,2*(w*b-c*a)))));yaw=math.degrees(math.atan2(2*(w*c+a*b),1-2*(b*b+c*c)));return abs(sum(v*v for v in x.q)-1)<.001 and abs(pitch-t['a'])<.1 and abs((yaw-t['b']+180)%360-180)<.1
    return False
   assert any(r['n']>=ack[0]['n']and match(x)and bytes(x.get_msgbuf())in ptx[target]for r,x in frames)
 proof.append({'command':f.command,'component':f.target_component,'bus':target,'operation':op,'airborneAUTO':f.command!=512})
assert any(x['operation']=='capture'for x in proof)
if case=='nominal':assert any(x['operation']=='gimbal'for x in proof)and events['CLOSED'][-1][1]['safeComplete']is True
else:
 assert events['CLOSED'][-1][1]['reason']=='INJECTED_LINK_LOSS96'and events['CLOSED'][-1][1]['safeComplete']is False;before=states[-2][1];assert any(p['ownerSid']is not None for p in before['payloads']),'NO_ACTIVE_OWNER_AT_LINK_LOSS';assert any(t['operation']=='capture'and t['state'].startswith('UNKNOWN_')for t in lastState['transactions'])
# Independent AP observer: prove final state/navigation or failsafe; never rewrite native interrupted outcome.
obs,obsHead=chain(D/'observer.jsonl');p=m.MAVLink(None);p.robust_parsing=True;frames=[]
for r in obs:
 for f in p.parse_buffer(bytes.fromhex(r['hex']))or[]:
  if f.get_type()=='BAD_DATA':assert not frames and all(v in [9,10,13]or 32<=v<=126 for v in bytes(f.data));continue
  if f.get_srcSystem()==42 and f.get_srcComponent()==1:frames.append((int(r['hostMonoNs']),f))
closure=json.loads((D/'closure.json').read_text());assert closure['stopped']and closure['error']is None and closure['observerError']is None and closure['observerHead']==obsHead and closure['hostGCSCommandBytes']==0 and closure['everArmed'];hb=next((t,f)for t,f in reversed(frames)if f.get_msgId()==0);land=next((t,f)for t,f in reversed(frames)if f.get_msgId()==245);pos=next((t,f)for t,f in reversed(frames)if f.get_msgId()==33);home=events['POST_ARM_HOME_REVIEW_REQUIRED'][-1][1]['postArmHome'];near=math.hypot((pos[1].lat/1e7-home['lat'])*111319,(pos[1].lon/1e7-home['lon'])*111319*math.cos(home['lat']*math.pi/180));assert not hb[1].base_mode&128 and land[1].landed_state==1 and abs(pos[1].relative_alt)<1000 and near<5
extra={}
if case=='nominal':
 reached={f.seq for _,f in frames if f.get_msgId()==46};assert all(e['seq']in reached for e in expected if e['seq']>0 and e['command']==16);assert any(f.get_msgId()in [42,46]and f.seq==len(expected)-1 for _,f in frames)
else:
 cut=json.loads((D/'fault-cut-host.json').read_text());fs=next((t,f)for t,f in frames if t>=cut['beforeTapHostNs']and f.get_msgId()==253 and 'gcs'in f.text.lower()and 'failsafe'in f.text.lower());assert any(t>=fs[0]and f.get_msgId()==0 and f.custom_mode==6 and f.base_mode&128 for t,f in frames);extra={'gcsFailsafe':True,'RTLWhileArmed':True,'hostTapToFailsafeS':(fs[0]-cut['beforeTapHostNs'])/1e9}
result={'status':'PASS','case':case,'run':D.name,'sourceId':meta['sourceId'],'nativeRecords':len(rows),'nativeHead':head,'nativeRawSha256':sha((D/'android-raw.jsonl').read_bytes()),'singleSocket':True,'sharedGeneration':lastState['generation'],'TXPairs':writePairs,'sharedWireSequenceCRC':True,'compiledMissionItems':len(expected),'routes':proof,'peerHead':peerHead,'observerHead':obsHead,'observerFinalGroundDisarmedNearHomeM':near,'allAuthorityRevoked':True,'actualImages':0,'physicalExecutionProven':False,'hardwareAuthenticated':False,**extra};(D/'independent-replay98.json').open('x').write(json.dumps(result,indent=2));print(json.dumps(result))
