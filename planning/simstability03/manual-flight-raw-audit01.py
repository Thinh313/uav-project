#!/usr/bin/env python3
"""Cold read-only audit. No model replay, host, AP, APK or flight command is started."""
import collections, datetime, hashlib, importlib.util, json, math, pathlib, struct, time
ROOT=pathlib.Path(__file__).resolve().parents[2];REC=ROOT/'.local/simstability03/receiver03';RUN='rc8f9c0bfcc3a4563b492';R=REC/'evidence/simhand01/runs'/RUN
spec=importlib.util.spec_from_file_location('cold_audit',ROOT/'planning/simverify02/raw-audit01.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def stats(v):
 s=sorted(v);return {'count':len(s),'p50':s[int((len(s)-1)*.5)] if s else None,'p95':s[int((len(s)-1)*.95)] if s else None,'p99':s[int((len(s)-1)*.99)] if s else None,'max':max(s) if s else None}
def crc(data,extra):
 x=65535
 for b in data+bytes([extra]):
  t=b^(x&255);t^=(t<<4)&255;x=((x>>8)^(t<<8)^(t<<3)^(t>>4))&65535
 return x
start=time.monotonic();names=['frames.wal','ap-timing.bin','mavlink.jsonl','backend-stages.json','launch.json','closure.json','backend-result.json','operator-review.json','operator-review.receipt.json','resource-intent.json'];before={n:a.sha256_file(R/n) for n in names}
launch=json.loads((R/'launch.json').read_text());backend=json.loads((R/'backend-result.json').read_text());closure=json.loads((R/'closure.json').read_text());review=json.loads((R/'operator-review.json').read_text());commit=json.loads((R/'operator-review.receipt.json').read_text());assert commit['sha256']==before['operator-review.json'] and commit['bytes']==(R/'operator-review.json').stat().st_size and commit['fileAndDirectorySyncCompleted']
wal=a.audit_wal(R/'frames.wal');assert wal['completeCapture'] and wal['closeRecords']==1 and wal['frameGaps']==0 and wal['admittedFrames']==backend['frames'];ap=a.audit_ap(R/'ap-timing.bin',wal['admittedFrames']);assert ap['duplicateStageRecords']==0 and not any(ap['missingStageRecords'].values());mav=a.audit_mavlink(R/'mavlink.jsonl',RUN);mounts=a.audit_mounts(R,launch)
pins=json.loads((ROOT/'evidence/simstability03/source-pins03.json').read_text());pinFailures=[]
for name,p in pins['files'].items():
 f=REC/name
 if not f.is_file() or f.stat().st_size!=p['bytes'] or a.sha256_file(f)!=p['sha256']:pinFailures.append(name)
assert not pinFailures
modelPins={n:p for n,p in pins['files'].items()if any(t in n for t in ['physics.py','integrator','_sim32','wal_journal','simtrain53/backend.py'])};assert modelPins
rows=[json.loads(l)for l in(R/'mavlink.jsonl').open()];sid=set(q['session']for q in rows if q['session']);assert len(sid)==1;sid=next(iter(sid));epoch=backend['epoch'];hb=[];latestHB=None;windows=[];current=None;rc=[];commands=[];ack=[];attitudes=[];approval=None;takeoff=None;land=None;release=[];wireSeq=[]
for q in rows:
 k=q['kind'];d=q['data'];ns=int(q['nodeNs'])
 if k=='AP_RX_DECODED':
  assert d['system']==42 and d['component']==1
  if d['id']==0:latestHB=(ns,d['fields']);hb.append(ns)
  if d['id']==77:ack.append({'index':q['index'],'nodeNs':ns,**d['fields']})
  if d['id']==30:attitudes.append({'nodeNs':ns,'roll':d['fields']['roll'],'pitch':d['fields']['pitch'],'yaw':d['fields']['yaw']})
 if k=='GCS_TX_REQUEST' and d['id']!=0:
  assert d['fields']['target_system']==42 and d['fields']['target_component']==1
  if d['id']==76:commands.append({'index':q['index'],'nodeNs':ns,**d['fields']})
 if k=='OWNED_INSTANCE_ATTESTED':assert d['epoch']==epoch and d['apSha256']==launch['apSha256'] and d['containerId']==launch['containerId']
 if k=='EXPLICIT_PREFLIGHT_APPROVAL':
  approval=q;assert d['session']==sid and d['boot']==epoch and d['simulationOnly'] and d['profile']['comparison']['pass'];assert d['profile']['observation']['vehicle']=={'system':42,'component':1}
 if k=='TAKEOFF_PHYSICS_AND_GUIDED_OBSERVED':takeoff=q;assert d['physics']['position'][2]<-4.5 and d['mode']=='GUIDED'
 if k=='MANUAL_HANDOFF_REQUESTED':assert d['session']==sid and d['boot']==epoch and d['callerChallengeReserved'] and d['leaseActive'] is False
 if k=='MANUAL_HANDOFF_READY':
  assert d['state']=='NEUTRAL_REQUIRED' and d['mode']==5 and d['ttlMs']==200 and d['firstNeutralInputRequired'];assert current is None;current={'readyIndex':q['index'],'readyNodeNs':ns,'generation':d['generation'],'lease':d['lease'],'input':[]};windows.append(current)
 if k=='RC_TX_INTENT':
  assert d['boot']==epoch;b=bytes.fromhex(d['rawHex']);assert len(b)==30 and b[:2]==bytes([253,18]) and int.from_bytes(b[7:10],'little')==70 and b[26:28]==bytes([42,1]);assert struct.unpack('<8H',b[10:26])==tuple(d['channels']);assert int.from_bytes(b[-2:],'little')==crc(b[1:-2],124)
  wireSeq.append(b[4]);r={'index':q['index'],'nodeNs':ns,'reason':d['reason'],'channels':d['channels'],'wireSequence':b[4]};rc.append(r)
  if d['reason']=='EXPLICIT_KEYBOARD_SIMULATOR_INPUT':
   assert current and latestHB and latestHB[1]['custom_mode']==5 and latestHB[1]['base_mode']&128
   r['heartbeatAgeMs']=(ns-latestHB[0])/1e6;assert 0<=r['heartbeatAgeMs']<=1500
   if not current['input']:assert d['channels'][:4]==[1500]*4
   current['input'].append(r)
 if k=='MANUAL_GUIDED_RELEASE_OBSERVED':
  assert d['mode']==4 and d['authorityRestored'] is False and current;assert latestHB[1]['custom_mode']==4;current['releaseIndex']=q['index'];current['releaseNodeNs']=ns;release.append(q);current=None
 if k=='LAND_GROUND_DISARM_OBSERVED':land=q;assert d['physics']['ground'] and d['observed']['armed'] is False
assert current is None and len(windows)==2 and all(w['input']for w in windows) and approval and takeoff and land
assert all(0<(b-a)%256<128 for a,b in zip(wireSeq,wireSeq[1:]));inputs=[r for w in windows for r in w['input']];assert any(r['channels'][1]!=1500 for r in inputs)and any(r['channels'][3]!=1500 for r in inputs)
for command in commands:
 if command['command']in[176,400,22]:assert any(z['command']==command['command'] and z['result']==0 and z['nodeNs']>=command['nodeNs']for z in ack),'Required accepted ACK missing.'
assert closure['error']is None and closure['backendExited'] and closure['backendExitCode']==0 and closure['ownedContainerStopped'];assert review['status']=='COMPLETED_OBSERVED'and review['success']and review['closure']['allOwnedClosed']and review['authorityRestorable']is False and review['observedEnd']['ground']and review['observedEnd']['armed']is False
stages=json.loads((R/'backend-stages.json').read_text());assert len(stages)==wal['admittedFrames'] and all(r[0]==i for i,r in enumerate(stages));metrics={n:stats([(r[b]-r[c])/1e6 for r in stages])for n,b,c in [('receiveToComputeStartMs',2,1),('integrationMs',3,2),('computeToDurableBarrierMs',4,3),('durableBarrierToSensorReturnMs',5,4),('receiveToSensorReturnMs',5,1)]}
for n,col in [('intentOsWriteMs',6),('intentFsyncMs',7),('intentAppendMs',8)]:metrics[n]=stats([r[col]/1e6 for r in stages])
rxGaps=[(b[1]-a[1])/1e6 for a,b in zip(stages,stages[1:])];hbgaps=[(b-a)/1e6 for a,b in zip(hb,hb[1:])]
# Re-read admitted model states for observed motion only; no original-model replay is claimed.
maxAlt=0;maxXY=0;lastState=None;modelCount=0
with(R/'frames.wal').open('rb')as f:
 f.read(8)
 while True:
  h=f.read(28)
  if not h:break
  kind,_,_,frame,size,_,stamp=struct.unpack('<BBHIIQQ',h);body=f.read(size);f.read(36)
  if kind==3:
   n,_=struct.unpack_from('<II',body);q=json.loads(body[8:8+n]);m=q['modelAux'];assert q['epoch']==epoch;maxAlt=max(maxAlt,-m['position'][2]);maxXY=max(maxXY,math.hypot(*m['position'][:2]));lastState=m;modelCount+=1
assert modelCount==wal['admittedFrames'] and lastState['ground'];after={n:a.sha256_file(R/n)for n in names};assert before==after
report={'format':'aeris-simstability03-manual-flight-cold-audit','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':RUN,'receiver':str(REC),'status':'COLD_RAW_MANUAL_SEQUENCE_CHECKS_PASS_NOT_FULL_PRODUCT_ACCEPTANCE','scriptSha256':a.sha256_file(pathlib.Path(__file__)),'inputSha256':before,'inputsUnchanged':True,'wal':wal,'ap':ap,'mavlink':mav,'mounts':mounts,'sourcePins':{'manifestSHA256':pins['manifestSHA256'],'membersChecked':len(pins['files']),'failures':pinFailures,'modelPins':modelPins,'speedup':pins['speedup'],'pacingCapMs':pins['pacingCapMs']},'manual':{'session':sid,'boot':epoch,'target':{'system':42,'component':1},'acceptedCommands':[c for c in commands if c['command']in[176,400,22]],'acceptedAckCounts':[{'command':k,'count':sum(z['command']==k and z['result']==0 for z in ack)}for k in[176,400,22]],'approvalIndex':approval['index'],'homeApprovalSha256':approval['data']['home'],'typedParameters':approval['data']['profile']['observation']['parameters'],'profileComparison':approval['data']['profile']['comparison']['state'],'takeoffIndex':takeoff['index'],'takeoffAltitudeM':-takeoff['data']['physics']['position'][2],'windows':windows,'rcIntentCount':len(rc),'pitchNonNeutral':sum(r['channels'][1]!=1500 for r in inputs),'yawNonNeutral':sum(r['channels'][3]!=1500 for r in inputs),'wireSequence':'VALID_MOD256_PROGRESS_WITH_OTHER_GCS_MESSAGES_BETWEEN_RC','clientInputSequence':'NOT_EMBEDDED_IN_CAPTURE; ORIGINAL_AUTHORITY_VALIDATES_SEQUENCE_IN_CODE/MOCKS. WIRE_SEQUENCE_IS_DIFFERENT','inputReasonLabel':'Legacy EXPLICIT_KEYBOARD_SIMULATOR_INPUT label; this capture alone does not identify touch versus keyboard','releaseRecords':len(release),'landIndex':land['index'],'landGround':land['data']['physics']['ground'],'landDisarmed':land['data']['observed']['armed']is False,'maximumAdmittedAltitudeM':maxAlt,'maximumAdmittedHorizontalDistanceM':maxXY,'authorityRestored':False,'coldHostRestartAuthorityAcceptance':'NOT_INFERRED_FROM_THIS_RUN'},'heartbeatGapMs':stats(hbgaps),'receiveFrameGapMs':stats(rxGaps),'backendStageMetrics':metrics,'backend':backend,'closure':closure,'review':{'status':review['status'],'success':review['success'],'reason':review['reason'],'observedEnd':review['observedEnd'],'allOwnedClosed':review['closure']['allOwnedClosed'],'bytes':commit['bytes'],'sha256':commit['sha256']},'originalModelByteOracle':'NOT_RUN_IN_THIS_COLD_AUDIT; PINNED_REFERENCE_BYTES_CHECKED_ONLY','failedAP03':'RETAINED_SEPARATELY_NOT_PROMOTED_OR_COMBINED','physicalHeraPhoneMediaAcceptance':'NOT_ESTABLISHED_BY_RAW_MANUAL_CONTROL_AUDIT','elapsedSeconds':time.monotonic()-start}
out=ROOT/'evidence/simstability03/manual-flight-raw-audit01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'out':str(out),'frames':wal['admittedFrames'],'walClose':wal['closeRecords'],'apMissing':ap['missingStageRecords'],'rtf':backend['activeReceiveRTF'],'rcIntent':len(rc),'pitchNonNeutral':report['manual']['pitchNonNeutral'],'yawNonNeutral':report['manual']['yawNonNeutral'],'hbGapMs':stats(hbgaps),'fsync':metrics['intentFsyncMs'],'maxAlt':maxAlt,'elapsedSeconds':report['elapsedSeconds']}))
