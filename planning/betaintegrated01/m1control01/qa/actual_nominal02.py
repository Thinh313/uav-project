from pathlib import Path
import base64,collections,hashlib,json,struct,sys,tarfile,datetime
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.verify_capture import verify_capture
from pilot.betaintegrated01.control01.oracles03 import audit_transport,control_outcome
from pilot.betaintegrated01.control01.mavlink import Framer
B=R/'evidence/betaintegrated01-m1control01/actual-nominal02';O=R/'evidence/betaintegrated01-m1control01/qa/actual-nominal02';O.mkdir()
anchors=json.loads((B/'control/external-anchors.json').read_bytes());hb=anchors['liveParentBackend'];ap=json.loads((B/'control/container-control-stdout.txt').read_text().splitlines()[-1]);n=anchors['nativeClosedCheckpoint'];run,epoch,boot=hb['run'],hb['epoch'],hb['boot']
results={'format':'aeris-independent-control01-actual-nominal02','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_PREFLIGHT_REFUSAL_NO_ARM','anchorsOutsideRaw':{'path':str(B/'control/external-anchors.json'),'sha256':hashlib.sha256((B/'control/external-anchors.json').read_bytes()).hexdigest(),'APParentSTDOUTsha256':hashlib.sha256((B/'control/container-control-stdout.txt').read_bytes()).hexdigest()}}
try:results['fullFrameModelClockAP']=verify_capture(B/'raw',run,epoch,boot,expected_host_anchor=hb['commitAnchor'],expected_stage_anchor=ap['terminalSHA256'])
except Exception as e:results['fullFrameModelClockAP']={'status':'FAIL','error':repr(e)}
try:
 wire=audit_transport(B/'raw',run,epoch,boot,expected_anchor=hb['transportCommitAnchor']);results['transport']={k:v for k,v in wire.items()if k not in('passiveTimeline','nativeForwardedTimeline')};results['groundReadOnlyOutcome']=control_outcome(wire,'ground-recovery');results['nominalOutcome']=control_outcome(wire,'nominal')
except Exception as e:results['transport']={'status':'FAIL','error':repr(e)}
l=json.loads((B/'control/native-export-location.json').read_bytes());p=Path(l['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==l['sha256']
counts=collections.Counter();seq=0;previous='';last=-1;externalSeen=False;framer=Framer();ekf=set();gps=set();params={};hb_armed=[];txids=collections.Counter();cmds=[];firmware=set()
with tarfile.open(p)as t:
 names=[m for m in t.getmembers()if m.isfile()and m.name.endswith('.jsonl')];assert len(names)==2
 has_terminal=any(m.name.endswith('/session.json')for m in t.getmembers())
 for m in sorted(names,key=lambda x:x.name):
  f=t.extractfile(m)
  for line in f:
   row=json.loads(line);stored=row['sha256'];plain=line[:-(len(stored)+len(',"sha256":""}\n'))]+b'}';assert hashlib.sha256(plain).hexdigest()==stored
   assert row['n']==seq+1 and row['previous']==previous and row['monotonicNs']>=last and row['run']==run and row['epoch']==epoch
   seq+=1;previous=stored;last=row['monotonicNs'];counts[row['kind']]+=1;b=base64.b64decode(row['base64'],validate=True)
   if seq==n['journal']['records']:assert previous==n['journal']['head'];externalSeen=True
   if row['kind']=='RX':
    for v in framer.feed(b,row['monotonicNs']):
     if v['system']!=42 or v['component']!=1:continue
     ident,q=v['id'],v['payload']
     if ident==193:ekf.add(struct.unpack_from('<H',q,20)[0])
     if ident==24:gps.add((q[28],q[29],struct.unpack_from('<H',q,20)[0]))
     if ident==0:hb_armed.append(bool(q[6]&128))
     if ident==148:firmware.add(struct.unpack_from('<I',q,8)[0])
     if ident==22:params[q[8:24].split(b'\0')[0].decode()]={'mavType':q[24],'bits':q[:4].hex()}
   if row['kind']=='TX_WRITTEN':
    ident=int.from_bytes(b[7:10],'little');txids[ident]+=1
    if ident==76:cmds.append(struct.unpack_from('<H',b,38)[0])
assert externalSeen
typed=json.loads((R/'runtime/betaintegrated01/control01/nominal/typed-profile.json').read_bytes())['parameters'];matched={k:params[k]=={'mavType':v['mavType'],'bits':v['float32Hex']}for k,v in typed.items()}
results['native']={'status':'HASHED_PREFIX_WITH_EXTERNAL_LIVE_HEAD_NO_CLOSED_COMMIT','tarSHA256':l['sha256'],'rows':seq,'lastHead':previous,'externalLivePrefixMatched':externalSeen,'closedSessionPresent':has_terminal,'counts':dict(counts),'GPSObserved':sorted(gps),'EKFFlagsObserved':[hex(x)for x in sorted(ekf)],'neverObservedArmed':bool(hb_armed)and not any(hb_armed),'typed39Matched':len(matched)==39 and all(matched.values()),'unmatchedTyped':[k for k,v in matched.items()if not v],'localTXMessageIDs':dict(txids),'localCommandLongIDs':sorted(set(cmds)),'ARMCommandSent':400 in cmds,'RCOverrideSent':txids[70]>0,'consentGrantRecords':counts['CONTROL_CONSENT'],'inputRecords':counts['CONTROL_INPUT'],'discoveryIsNotPreflightAcceptance':True,'endIsForceStopNotClosedPersistence':not has_terminal}
results['notChecked']=['manual/assistedflight','postarmHome','heldinputlinkloss/failsafe','groundAPreboot','nativeclosedcommit/restart','30min/fullBeta','physicalHID/realaircraft'];results['APForcedStopIsNotLanding']=True
(O/'results.json').open('x').write(json.dumps(results,indent=2)+'\n');print(json.dumps({'status':results['status'],'nativeRows':seq,'typed39':results['native']['typed39Matched'],'host':results['fullFrameModelClockAP'].get('status'),'transport':results['transport'].get('status')}))
