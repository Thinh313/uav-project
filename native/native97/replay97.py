"""Independent upstream Python MAVLink/raw authority and two-bus routing replay. No sockets or commands."""
from pathlib import Path
import json,sys,base64,hashlib,importlib.util,math
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];E=R/'evidence/native97';D=E/'run04';sha=lambda b:hashlib.sha256(b).hexdigest();spec=importlib.util.spec_from_file_location('upstream97',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def chain(path):
 rows=[];head='';last=-1
 for line in path.read_bytes().splitlines():
  r=json.loads(line);body=line.rsplit(b',"sha256":',1)[0]+b'}';assert r['n']==len(rows)+1 and r['previous']==head and sha(body)==r['sha256'];head=r['sha256']
  if 'elapsedMs'in r:assert r['elapsedMs']>=last;last=r['elapsedMs']
  rows.append(r)
 return rows,head
case=sys.argv[1];assert case in ['camera','gimbal'];rawpath=D/(case+'-native-raw.jsonl');rows,head=chain(rawpath);assert rows[0]['kind']=='META'and rows[-1]['kind']=='CLOSED';meta=json.loads(base64.b64decode(rows[0]['dataBase64']));build=json.loads((E/'build07.json').read_text());assert meta['sourceId']==build['sourceId']and meta['actualImages']==0 and meta['authorityRestorable']is False
rx=m.MAVLink(None);rx.robust_parsing=True;frames=[];outgoing=[];txint=[];written=[];binding=None;lastcmd=None;latest=None;grants={};approval={};records={};bad=[];reject=[];states=[];admit=None;pendingWrite=None
bus={100:'A',154:'A',102:'B',101:'B'};cam={'front':100,'center':102,'rear':101};device={'front':1,'center':2,'rear':0}
for r in rows:
 b=base64.b64decode(r['dataBase64'],validate=True);kind=r['kind']
 if kind=='RX':
  for f in rx.parse_buffer(b)or[]:
   if f.get_type()=='BAD_DATA':
    assert admit is None and all(x in[9,10,13]or 32<=x<=126 for x in bytes(f.data));bad.extend(bytes(f.data));assert len(bad)<=1024
   else:frames.append((r,f))
 elif kind in['TX_INTENT','TX_WRITTEN']:
  p=m.MAVLink(None);f=p.parse_char(b);assert f and not p.buf_len()and f.get_srcSystem()==255 and f.get_srcComponent()==190 and f.get_msgId()in[0,76]
  if kind=='TX_INTENT':
   assert pendingWrite is None;pendingWrite=b;txint.append(b)
   if f.get_msgId()==76:
    admit=admit or r['n'];assert f.command in[512,531,532,2000,1000,1001]and f.target_system==42 and f.target_component in bus and f.confirmation==0
    if f.command==512:assert f.param1==(280 if f.target_component==154 else 259)and all(getattr(f,'param'+str(i))==0 for i in range(2,8));actor=None
    else:
     assert lastcmd and latest and binding;assert lastcmd['generation']==latest['generation']and lastcmd['revision']==latest['revision'];p0=lastcmd['payload'];ps=next(p for p in latest['payloads']if p['id']==p0);ss=next(s for s in latest['stations']if s['sid']==lastcmd['sid']);assert ss['alive']and ps['ownerSid']==lastcmd['sid']and ps['proposal']is None and ps['fresh'];assert r['elapsedMs']-ss['seenMs']<=15000 and ps['leaseUntilMs']>r['elapsedMs']
     op=lastcmd['operation'];expected={'capture':2000,'zoom':531,'focus':532,'authority':1001,'gimbal':1000}[op];assert f.command==expected and f.target_component==(154 if op in['gimbal','authority']else cam[p0]);actor=ss['actor']
     if op in['zoom','focus']:assert f.param1==2 and f.param2==lastcmd['a']and f.param3==0 and math.isnan(f.param4)and all(getattr(f,'param'+str(i))==0 for i in[5,6,7])
     if op=='capture':assert f.param1==0 and f.param2==0 and f.param3==1 and f.param4>=1 and f.param5==0 and f.param6==0 and math.isnan(f.param7)
     if op=='gimbal':assert f.param1==lastcmd['a']and f.param2==lastcmd['b']and math.isnan(f.param3)and math.isnan(f.param4)and f.param5==f.param6==0 and f.param7==device[p0]
     if op=='authority':assert [f.param1,f.param2,f.param3,f.param4,f.param5,f.param6,f.param7]==[255,190,0,0,0,0,device[p0]]
    assert binding['sha256']==sha(b);records[binding['id']]={'raw':b,'row':r,'frame':f,'actor':actor,'stateBefore':latest,'commandIntent':lastcmd,'binding':binding};outgoing.append(records[binding['id']])
  else:assert pendingWrite==b;pendingWrite=None;written.append(b)
 elif kind=='TX_BINDING':binding=json.loads(b)
 elif kind=='TX_APPROVAL':
  a=json.loads(b)
  if not a.get('heartbeat'):
   rec=records[a['id']];assert rec['row']['elapsedMs']<=a['atMs']<=r['elapsedMs']and a['generation']==(rec['stateBefore']or{}).get('generation',a['generation']);q=rec['commandIntent']
   if rec['frame'].command!=512:assert a['ownerSid']==q['sid']and a['intentRevision']==q['revision'];ps=next(p for p in rec['stateBefore']['payloads']if p['id']==q['payload']);assert a['atMs']<ps['leaseUntilMs']
   approval[a['id']]=a
 elif kind=='COMMAND_INTENT':lastcmd=json.loads(b)
 elif kind=='JOIN_INTENT':admit=admit or r['n']
 elif kind=='STATE':latest=json.loads(b);states.append(latest)
 elif kind=='REJECTED':reject.append(json.loads(b))
assert pendingWrite is None and txint==written and len(approval)==len(outgoing);assert all(not f.base_mode&128 for r,f in frames if f.get_msgId()==0 and f.get_srcSystem()==42 and f.get_srcComponent()==1)
peerRows,peerHead=chain(D/'peers.jsonl');peerRX={s:[]for s in['A','B']};peerTX={s:[]for s in['A','B']};dec={s:m.MAVLink(None)for s in['A','B']}
for p in dec.values():p.robust_parsing=True
for r in peerRows:
 if r['kind']=='RX':
  for f in dec[r['bus']].parse_buffer(bytes.fromhex(r['hex']))or[]:
   if f.get_type()!='BAD_DATA':peerRX[r['bus']].append(bytes(f.get_msgbuf()))
 if r['kind']=='TX':
  f=m.MAVLink(None).parse_char(bytes.fromhex(r['hex']));assert f.get_srcSystem()==42 and bus[f.get_srcComponent()]==r['bus'];peerTX[r['bus']].append(bytes(f.get_msgbuf()))
for rec in outgoing:
 f=rec['frame'];expected=bus[f.target_component];assert rec['raw']in peerRX[expected]and rec['raw']not in peerRX['B'if expected=='A'else'A'],'ROUTE_BUS_MISMATCH'
final=states[-1];assert json.loads(base64.b64decode(rows[-1]['dataBase64']))['authorityRestorable']is False and (case=='camera' or all(p['ownerSid']is None for p in final['payloads']))and final['actualImages']==0 and final['executionProven']is False
if case=='camera':
 frontZoom=next(t for t in final['transactions']if t['payload']=='front'and t['operation']=='zoom');assert frontZoom['state']=='UNKNOWN_TIMEOUT_UNCERTAIN';assert all(t['state']not in['ACK_ACCEPTED_NOT_EXECUTION','OBSERVATION_CONSISTENT_UNATTRIBUTED']for st in states for t in st['transactions']if t['id']==frontZoom['id'])
 
consistent=[t for t in final['transactions']if t['state']=='OBSERVATION_CONSISTENT_UNATTRIBUTED'];witness=[]
for t in consistent:
 rec=records[t['id']];f=rec['frame'];matches=[(r,x)for r,x in frames if r['n']>rec['row']['n']and x.get_srcSystem()==42 and x.get_srcComponent()==f.target_component]
 ack=next((r,x)for r,x in matches if x.get_msgId()==77 and x.command==f.command and x.result==0 and x.target_system==255 and x.target_component==190);assert bytes(ack[1].get_msgbuf())in peerTX[bus[f.target_component]]
 obs=[(r,x)for r,x in matches if r['n']>=ack[0]['n']and ((t['operation']=='capture'and x.get_msgId()==263 and x.camera_id==0 and x.capture_result==1)or(t['operation']in['zoom','focus']and x.get_msgId()==260 and abs(getattr(x,'zoomLevel'if t['operation']=='zoom'else'focusLevel')-t['a'])<.05)or(t['operation']=='authority'and x.get_msgId()==281 and x.gimbal_device_id==t['device']and x.primary_control_sysid==255 and x.primary_control_compid==190)or(t['operation']=='gimbal'and x.get_msgId()==285 and x.gimbal_device_id==t['device']and x.failure_flags==0))];assert obs;
 if t['operation']=='gimbal':
  def angleok(x):
   w,a,b,c=x.q;norm=sum(v*v for v in x.q);pitch=math.degrees(math.asin(max(-1,min(1,2*(w*b-c*a)))));yaw=math.degrees(math.atan2(2*(w*c+a*b),1-2*(b*b+c*c)));return abs(norm-1)<.001 and abs(pitch-t['a'])<.1 and abs((yaw-t['b']+180)%360-180)<.1
  assert any(angleok(x)for _,x in obs)
 assert any(bytes(x.get_msgbuf())in peerTX[bus[f.target_component]]for r,x in obs);witness.append({'operation':t['operation'],'payload':t['payload'],'component':t['component'],'device':t['device'],'actor':rec['actor'],'state':t['state']})
if case=='camera':
 assert set(t['payload']for t in consistent if t['operation']=='capture')=={'front','center','rear'};assert any(t['actor']=='payload-b'and t['operation']=='focus'for t in witness);assert any('EXCLUSIVE_OWNER'in e['error']for e in reject)
else:
 assert any(t['operation']=='gimbal'for t in witness)and any(t['operation']=='authority'for t in witness);assert any('AMBIGUOUS_ACK_KEY'in e['error']for e in reject)
observerRows,observerHead=chain(D/'observer.jsonl');p=m.MAVLink(None);p.robust_parsing=True;hbs=[]
for r in observerRows:
 for f in p.parse_buffer(bytes.fromhex(r['hex']))or[]:
  if f.get_type()=='BAD_DATA':assert all(v in[9,10,13]or 32<=v<=126 for v in bytes(f.data));continue
  if f.get_msgId()==0 and f.get_srcSystem()==42 and f.get_srcComponent()==1:assert not f.base_mode&128;hbs.append(f)
assert hbs;closure=json.loads((D/'closure.json').read_text());assert closure['stopped']and closure['error']is None and closure['observerError']is None and closure['hostGCSCommandBytes']==0 and closure['observerHead']==observerHead
result={'status':'PASS','scope':'ACTUAL_ANDROID_NATIVE_GCS_VIA_AP_ROUTER_WITH_SYNTHETIC_PEERS_NOT_HARDWARE','nativeRun':meta['run'],'rawRecords':len(rows),'rawHead':head,'rawSha256':sha(rawpath.read_bytes()),'nativeFrameTX':len(txint),'payloadCommands':len(outgoing),'routedCommandsCorrectBusOnly':len(outgoing),'peerRecords':len(peerRows),'peerHead':peerHead,'observerDisarmedHeartbeats':len(hbs),'consistentUnattributed':witness,'nativeRejections':len(reject),'wrongTargetZoomNeverAccepted':True if case=='camera' else None,'startupASCIIBytes':len(bad),'wireTailBytes':rx.buf_len(),'closedAuthorityRestorable':False,'actualImages':0,'executionProven':False,'remoteAuthentication':False,'sourceId':meta['sourceId'],'targetedMockChecks':55};(E/('independent-'+case+'97.json')).open('x').write(json.dumps(result,indent=2));print(json.dumps(result))
