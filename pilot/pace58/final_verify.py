"""Closed-capture verification only. No simulator start, control or old-path writes."""
from pathlib import Path
import collections,datetime,hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/pace58'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
rows=[];total=0;filesChecked=0;free=[]
for request in ['p58B1','p58B3','p58O1','p58O2','p58B2']:
 started=read(E/'started'/f'{request}.json');out=E/'runs'/started['run'];raw=read(out/'raw-diagnostic.json');driver=read(E/f'{request}-driver-result.json');a=read(E/f'{request}-analysis.json');launch=read(out/'launch.json');closure=read(out/'closure.json');result=read(out/'backend-result.json')
 assert raw['status']=='PASS_RAW_INTEGRITY_ORIGINAL_ORACLE_ONLY' and raw['frames']==result['frames']==a['frames'] and raw['exactOriginalSensorAndAuxFrames']==result['frames']
 assert raw['frameContinuity']=='NO_ADMITTED_FRAME_GAP_DUPLICATE_OR_MISSING_SEND_RETURN'
 assert raw['actualAPReceiveParseFrames']==result['frames']
 assert closure['backendExited'] and closure['backendExitCode']==0 and closure['ownedContainerStopped']
 for name,h in raw['filesSha256'].items():assert sha(out/name)==h,(request,name);filesChecked+=1
 assert launch['speedup']==1 and launch['rateHz']==1200 and launch['negativeDebtCapUs']==500000
 assert launch['apSha256']=='f2be1f349f84b4aedaa5912b3050f64f476f3218bc4f68b34ad4de11393c2d08'
 assert launch['command'][-4:]==['--rate','1200','--speedup','1']
 free.extend([launch['resourceFreeBytes'],closure['freeBytes']]);total+=raw['frames']
 samples=[]
 if(out/'host-observer.jsonl').exists():
  samples=[json.loads(l)for l in(out/'host-observer.jsonl').open()];free.extend(p['freeBytes']for p in samples)
 full=[w['fixedWallBucketRTF']for w in a['windows']if w['fullFiveSeconds']]
 rows.append({'requestId':request,'run':out.name,'mode':started['mode'],'frames':raw['frames'],'wholeRTF':a['wholeRTF'],'wholeRTFGe1':a['wholeRTFGe1'],'minimumFull5sRTF':min(full),'receiveGapMs':a['hostReceiveGapMs'],'capClips':a['ap']['capClipCount'],'discardedDebtUs':a['ap']['discardedDebtUs'],'driverStatus':driver['status'],'driverError':driver.get('error'),'controllerError':closure['error'],'takeoffAndLandObserved':raw['takeoffAndLandPhysicalObservations'],'originalSensorAndAuxExact':True,'APReceiveParseCorrelated':True,'hostObserverSamples':len(samples),'variant':'COMPACT_RECORDER_CPU_GC_HB4HZ_NOT_MATCHED_BASELINE'if request=='p58B2'else'RETAINED_EXPERIMENT'})
assert set(p.stem for p in(E/'started').glob('*.json'))==set(r['requestId']for r in rows)
assert len(list((E/'runs').iterdir()))==5
assert total==433961
source=read(E/'final-slot-v5-admission.json')
for p,h in source['files'].items():assert sha(R/p)==h,('FINAL_RUNTIME_SOURCE_DRIFT',p)
pres=read(E/'preservation-after.json');assert pres['checked']==21328 and not pres['failures'];free.append(pres['freeBytes'])
assert min(free)>20*2**30
qa=[read(E/'qa2/receipt.json'),read(E/'qa-backend-qa5.json'),read(E/'qa-ui-timing.json'),read(E/'qa-fastpath.json'),read(E/'qa-compact/receipt.json')]
assert all(x['status'].startswith('PASS')for x in qa)
checks=sum(len(x['checks'])if isinstance(x['checks'],list)else x['checks']for x in qa);assert checks==64
cpu=read(E/'p58B2-cpu-analysis.json');largest=cpu['top20'][0]
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'NOT_READY_G1_STABLE_1X','mockOfflineChecks':checks,'actualStarts':len(rows),'actualAdmittedFrames':total,'exactOriginalSensorAndAuxFrames':total,'verifiedRawFilesCurrentSha256':filesChecked,'rawIntegrityAllPass':True,'driverPasses':sum(r['driverStatus']=='PASS_BOUNDED_COUPLED_CAPTURE'for r in rows),'runs':rows,'slowestMeasuredHostFrame':largest,'gcEventsInFinalCapture':len(cpu['gc']['events']),'cpuInference':'Wall-time greatly exceeds thread CPU; non-CPU waiting is measured. IO versus scheduling/GIL cause remains unseparated. No claim that physics math caused the stall.','protectedHashes':pres['checked'],'protectedHashFailures':0,'minimumObservedFreeBytes':min(free),'freeBytesAtReport':shutil.disk_usage(R).free,'observationsAreNotContinuousDiskOrSleepProof':True,'runtimeSourceHashesMatchV5Admission':True,'speedup':1,'capUs':500000,'rateHz':1200,'admittedPhysicsFrameDrop':False,'postRetries':0,'matchedABAccepted':False,'fullG1Accepted':False,'herahubOrSDKTested':False,'newSoftwareSignature':False,'ENDUREAcceptanceChanged':False,'scope':'Isolated host engineering increment, no candidate/software selection or real aircraft control'}
with(E/'verification-final.json').open('x')as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:report[k]for k in ['status','mockOfflineChecks','actualStarts','actualAdmittedFrames','rawIntegrityAllPass','driverPasses','protectedHashes','minimumObservedFreeBytes']}))
for r in rows:print(r['requestId'],r['frames'],round(r['wholeRTF'],7),round(r['minimumFull5sRTF'],4),round(r['receiveGapMs']['p99'],3),round(r['receiveGapMs']['max'],3),r['capClips'],r['driverError'])
