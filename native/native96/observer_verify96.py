from pathlib import Path
import json,sys,hashlib,importlib.util,math,base64
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];D=R/'evidence/native96/runs'/sys.argv[1];case=sys.argv[2]
spec=importlib.util.spec_from_file_location('observer96',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
head='';parser=m.MAVLink(None);parser.robust_parsing=True;frames=[];seen=False;noise=bytearray();count=0
for line in(D/'observer.jsonl').read_bytes().splitlines():
 r=json.loads(line);body=line.rsplit(b',"sha256":',1)[0]+b'}';assert r['n']==count+1 and r['previous']==head and hashlib.sha256(body).hexdigest()==r['sha256'];head=r['sha256'];count+=1
 for f in parser.parse_buffer(bytes.fromhex(r['hex']))or[]:
  if f.get_type()=='BAD_DATA':assert not seen;noise.extend(bytes(f.data));assert len(noise)<=1024 and all(v in[9,10,13]or 32<=v<=126 for v in noise);continue
  seen=True
  if f.get_srcSystem()==42 and f.get_srcComponent()==1:frames.append((int(r['hostMonoNs']),f))
closure=json.loads((D/'closure.json').read_text());assert closure['stopped']and not closure['error']and not closure['observerError']and closure['observerHead']==head and closure['observerRecords']==count and closure['observerTransmittedPayloadBytes']==0
native=[json.loads(l)for l in(D/'android-raw.jsonl').read_text().splitlines()];events={r['kind']:json.loads(base64.b64decode(r['dataBase64']))for r in native if r['kind']not in['RX','TX_INTENT','TX_WRITTEN']};meta=events['META'];plan=meta['document']['compiled']['plan'];home={'lat':10.854,'lon':106.807}
if 'POST_ARM_HOME_REVIEW_REQUIRED'in events:home=events['POST_ARM_HOME_REVIEW_REQUIRED']['postArmHome']
near=lambda f:math.hypot((f.lat/1e7-home['lat'])*111319,(f.lon/1e7-home['lon'])*111319*math.cos(home['lat']*math.pi/180))
hb=next((t,f)for t,f in reversed(frames)if f.get_msgId()==0);land=next((t,f)for t,f in reversed(frames)if f.get_msgId()==245);pos=next((t,f)for t,f in reversed(frames)if f.get_msgId()==33)
assert not hb[1].base_mode&128 and land[1].landed_state==1 and abs(pos[1].relative_alt)<1000 and near(pos[1])<3 and abs(hb[0]-land[0])<1800e6
result={'status':'PASS','case':case,'run':D.name,'observerRecords':count,'observerFrames':len(frames),'observerHead':head,'transmittedMavlinkPayloadBytes':0,'finalGroundDisarmedNearHome':True,'startupPrefixBytes':len(noise),'sourceAuthenticated':False,'actualImages':0}
if case=='nominal':
 reached={f.seq for t,f in frames if f.get_msgId()==46};assert all(i['seq']in reached for i in plan['compiled']['items']if i['command']==16 and i['seq']>0);assert any(f.get_msgId()in[42,46]and f.seq==len(plan['compiled']['items'])-1 for t,f in frames);assert any(f.get_msgId()==33 and f.relative_alt>=9000 for t,f in frames)
 auto_at=next(t for t,f in frames if f.get_msgId()==0 and f.base_mode&128 and f.custom_mode==3);assert all(f.custom_mode==3 for t,f in frames if t>=auto_at and f.get_msgId()==0 and f.base_mode&128);result['fullNavigationAndTerminal']=True
elif case=='link-loss':
 cut=json.loads((D/'fault-cut-host.json').read_text());assert events['CLOSED']['reason']=='INJECTED_LINK_LOSS96'and events['CLOSED']['safeComplete']is False
 assert any(f.get_msgId()==0 and f.custom_mode==3 and f.base_mode&128 for t,f in frames)
 failsafe=next((t,f)for t,f in frames if t>=cut['beforeTapHostNs']and f.get_msgId()==253 and ('failsafe'in f.text.lower()and'gcs'in f.text.lower()))
 rtl=next((t,f)for t,f in frames if t>=failsafe[0] and f.get_msgId()==0 and f.custom_mode==6 and f.base_mode&128);delay=(failsafe[0]-cut['beforeTapHostNs'])/1e9;assert 3.5<=delay<=20
 result.update(gcsFailsafeObserved=True,RTLWhileArmed=True,failsafeDelayFromHostTapS=delay,missionAcceptance=False,nativeOutcome='INTERRUPTED_UNKNOWN_AIRCRAFT_STATE',clockNote='Delay uses host tap and observer host clock only, no Android/host clock identity assumption')
elif case=='ap-reboot-ground':
 assert not closure['everArmedObserved'];identity=json.loads((D/'reboot-identity.json').read_text());launch=json.loads((D/'launch.json').read_text());assert identity['containerId']==launch['containerId']and identity['pid']!=launch['pid']and identity['startedAt']!=launch['startedAt'];assert events['CLOSED']['safeComplete']is False and events['CLOSED']['reason'] in['NATIVE_EOF','NATIVE_HEARTBEAT_LOST'];assert 'AUTO_INTENT'not in events
 new=json.loads((D/'reboot-new-boot.json').read_text());assert new['newBootMs']<new['oldBootMs']and new['transmittedPayloadBytes']==0
 result.update(processIdentityChanged=True,bootRegressionObserved=True,noArmOrAUTO=True,nativeSessionClosedNoReconnect=True,missionAcceptance=False,scope='GROUND_PROCESS_REBOOT_NOT_AIRBORNE_RECOVERY')
else:raise AssertionError('CASE')
(D/'observer-verification96.json').open('x').write(json.dumps(result,indent=2));print(json.dumps(result))
