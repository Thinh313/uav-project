from pathlib import Path
import json,hashlib,shutil,datetime,subprocess,struct
from thread_analysis import load
from ui_join import join
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
pins=json.loads((E/'source-pins-v2.json').read_text())['files'];ck('all runtime/inherited/SDK source pins exact',all(sha(R/p)==h for p,h in pins.items()))
mockFiles=['qa-backend-t62c.json','qa-io.json','qa-ui.json','qa-thread.json','qa-thread-backend-join.json','qa-thread-negative.json'];mockChecks=0
for n in mockFiles:
 q=json.loads((E/n).read_text());ck(n+' scoped checks pass',q['status'].startswith('PASS')and all(c['pass']for c in q['checks']));mockChecks+=len(q['checks'])
results=[]
for label,rid in [('R1','r785bd3f297d44a748dde'),('R2','re6506ce615a2455db2bb')]:
 out=E/'runs'/rid;raw=json.loads((out/'readback.json').read_text());io=json.loads((out/'io-verification.json').read_text());tm=json.loads((E/f'timing-{label}.json').read_text());driver=json.loads((E/f's62{label.lower()}-driver-result.json').read_text());cl=json.loads((out/'closure.json').read_text());launch=json.loads((out/'launch.json').read_text());archive=json.loads((out/'guest-archive.json').read_text());meta,rows=load(out);ui,_=join(E/f'UI-{label}')
 ck(label+' original sensor+aux/AP receive-parse conservation',raw['status']=='PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION'and raw['frames']==raw['exactOriginalSensorAndAuxFrames']==raw['actualAPReceiveParseFrames']==tm['frames']==io['frames'])
 ck(label+' raw files current SHA match recorded',all(sha(out/n)==h for n,h in raw['filesSha256'].items()))
 ck(label+' syscall/barrier conserved and fsync before every sensor',io['status']=='PASS_RAW_SYSCALL_CONSERVATION_AND_BARRIER_ORDER'and io['fsyncBeforeEverySensorSend']and io['noFrameOrSyscallDropped'])
 ck(label+' same AP rate speedup/cap trace configuration',launch['speedup']==tm['speedup']==raw['speedup']==1 and launch['negativeDebtCapUs']==tm['capUs']==raw['capUs']==500000 and launch['rateHz']==1200 and launch['traceMode']=='tmpfs'and launch['allocation']=='none')
 ck(label+' immutable guest export and owned closure',archive['apWriterReaped']and all(f['sameImmutableSourceBytes']and sha(out/f['destination'])==f['sha256']for f in archive['files'])and cl['backendExitCode']==cl['wakeProcessExitCode']==0 and cl['ownedContainerStopped']and cl['error']is None)
 ck(label+' full UI chunks identity / errors / viewport',ui['run']==rid and json.loads((E/f'UI-{label}/manifest.json').read_text())['viewport']==[1920,1080]and not json.loads((E/f'UI-{label}/manifest.json').read_text()).get('errors'))
 ck(label+' sampled thread and analysis source SHA match',all(sha(out/n)==h for n,h in json.loads((out/'thread-analysis.json').read_text())['filesSha256'].items()))
 # One new servo datagram was retained on explicit stop, without model advance/sensor publication.
 tail=json.loads((out/'unadmitted-tail.json').read_text());frame=struct.unpack('<HHI16H',bytes.fromhex(tail['rawHex']))[2]
 ck(label+' unadmitted stop tail retained separately',tail['reason']=='STOP_OBSERVED'and frame==raw['frames']and raw['unadmittedAPTailFrames']==[frame])
 full=tm['wholeRTFGe1']and all(w['fixedWallBucketRTF']>=1 for w in tm['windows']if w['fullFiveSeconds'])and tm['ap']['capClipCount']==0
 ck(label+' no false stable1x acceptance',not full and raw['fullG1Accepted']is False and driver['fullG1Accepted']is False)
 ck(label+' physical LAND independently observed',raw['takeoffAndLandPhysicalObservations'])
 ck(label+' no retained own container',subprocess.run(['docker','container','inspect','aeris-thread62'],capture_output=True).returncode!=0)
 results.append({'label':label,'run':rid,'frames':raw['frames'],'RTF':tm['wholeRTF'],'minimumFull5sRTF':min(w['fixedWallBucketRTF']for w in tm['windows']if w['fullFiveSeconds']),'capClips':tm['ap']['capClipCount'],'discardedPacingDebtUs':tm['ap']['discardedDebtUs'],'threadSamples':len(rows),'uiRows':ui['rows'],'uiChunks':ui['chunks'],'uiHz':ui['measuredHz'],'driverStatus':driver['status'],'driverError':driver.get('error'),'cleanup':driver.get('cleanup'),'stopTailFrame':frame,'stable1x':full,'scope':'raw integrity distinct from driver / pacing acceptance'})
ck('R2 driver failure remains failure',results[1]['driverStatus']=='FAIL'and results[1]['driverError']=='PHYSICS_STALE_OR_FUTURE')
for label in ['before','after']:
 q=json.loads((E/f'preservation-{label}.json').read_text());ck(label+' protected frozen point-in-time hashes intact',q['checked']==22977 and q['failures']==[])
ck('20GiB final floor',shutil.disk_usage(R).free>=20*2**30)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_DIAGNOSTICS_VERIFIED_STABLE_1X_FAILED','checks':checks,'mockChecks':mockChecks,'runtimeSourcePins':len(pins),'actualRuns':results,'framesOriginalOracle':sum(x['frames']for x in results),'threadSamples':sum(x['threadSamples']for x in results),'uiRows':sum(x['uiRows']for x in results),'uiChunks':sum(x['uiChunks']for x in results),'fullG1Accepted':False,'freeBytes':shutil.disk_usage(R).free,'notEstablished':['Exclusive host runnable wait duration','Kernel filesystem wait reason','Observer-free actual A/B overhead','Stable1x under controlled equal host load','Hera calibration or hardware control'],'singleAgentReview':True,'frozenSourceCandidateENDUREUnchangedAtChecks':True}
with(E/'verification-final.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps({k:report[k]for k in ['status','mockChecks','runtimeSourcePins','framesOriginalOracle','threadSamples','uiRows','uiChunks','freeBytes']}));print({'checks':len(checks)})
