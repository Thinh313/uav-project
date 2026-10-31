from pathlib import Path
import hashlib,json,datetime,shutil
from ui_join import join
R=Path(__file__).resolve().parents[2];E=R/'evidence/isolate61';checks=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
for version in ['source-pins.json','source-pins-v2.json']:
 p=json.loads((E/version).read_text())['files'];ck(version+' remains exact',all(sha(R/n)==h for n,h in p.items()))
summary=[];minfree=[]
for i in [1,2]:
 tag=f'R{i}';d=json.loads((E/f's61{tag}-driver-result.json').read_text());out=E/'runs'/d['owner']['run'];name='forensic-raw-verification.json'if i==1 else'readback.json';raw=json.loads((out/name).read_text());io=json.loads((out/'io-analysis.json').read_text());ver=json.loads((out/'io-verification.json').read_text());attrib=json.loads((out/'attribution-verified.json').read_text());launch=json.loads((out/'launch.json').read_text());req=json.loads((out/'request.json').read_text());pace=json.loads((E/f'{tag}-pacing.json').read_text());ui,rows=join(E/f'UI-{tag}');manifest=json.loads((E/f'UI-{tag}/manifest.json').read_text());archive_name='forensic-recovery.json'if i==1 else'guest-archive.json';archive=json.loads((out/archive_name).read_text())
 ck(tag+' original sensor/aux frames and pre-send fsync',raw['frames']==raw['exactOriginalSensorAndAuxFrames']==ver['frames']==io['frames'] and ver['fsyncBeforeEverySensorSend'])
 ck(tag+' readback/raw hashes current',all(sha(out/n)==h for n,h in raw['filesSha256'].items()))
 ck(tag+' syscall observer hashes current',all(sha(out/n)==h for n,h in io['filesSha256'].items()))
 ck(tag+' immutable guest original/copy hashes current',all(sha(out/a['destination'])==a['sha256'] and(out/a['destination']).stat().st_size==a['bytes']for a in archive['files']))
 ck(tag+' attribution source hashes current',all(sha(out/n)==h for n,h in attrib['filesSha256'].items()))
 ck(tag+' UI all rows/chunks no overflow',ui['run']==out.name and ui['rows']==manifest['count']==manifest['timing']['frames'] and manifest['viewport']==[1920,1080] and not manifest['errors'])
 ck(tag+' AP fixed speedup/rate/cap and host WAL no preallocation',launch['rateHz']==1200 and launch['speedup']==1 and launch['negativeDebtCapUs']==500000 and req['allocation']=='none' and json.loads((out/'allocation.json').read_text())['status']=='DISABLED')
 ck(tag+' no POST retries',d['postRetries']==0)
 if i==1:
  closure=json.loads((out/'closure.json').read_text());ck('R1 failure not overwritten/false land claim',d['status']=='FAIL'and d['error']=='PHYSICS_STALE_OR_FUTURE'and not raw['takeoffAndLandPhysicalObservations']and closure['ownedContainerStopped']is False and 'ARCHIVE_FAILED' in closure['error'] and archive['originalClosureUntouched'])
 else:ck('R2 actual journey and clean archive/closure',d['status']=='PASS_BOUNDED_COUPLED_CAPTURE'and raw['takeoffAndLandPhysicalObservations']and json.loads((out/'closure.json').read_text())['ownedContainerStopped']and json.loads((out/'closure.json').read_text())['error']is None)
 minfree.extend(json.loads(l)['freeBytes']for l in(out/'host-observer.jsonl').read_text().splitlines())
 summary.append({'tag':tag,'run':out.name,'version':i,'traceMode':req['traceMode'],'driverStatus':d['status'],'frames':raw['frames'],'RTF':pace['wholeRTF'],'minimumFull5sRTF':min(v['fixedWallBucketRTF']for v in pace['windows']if v['fullFiveSeconds']),'capClips':pace['ap']['capClipCount'],'discardedDebtUs':pace['ap']['discardedDebtUs'],'apRTTp99Ms':pace['ap']['apRTTMs']['p99'],'apRTTmaxMs':pace['ap']['apRTTMs']['max'],'backendWallMaxMs':io['hostReceiveToSendMs']['max'],'fsyncMaxMs':io['groups']['fsync:INTENT']['wallMs']['max'],'uiRows':ui['rows'],'uiChunks':ui['chunks'],'uiHz':ui['measuredHz'],'guestSamples':attrib['guestSamples'],'guestObserverError':attrib['guestObserverError'],'guestAPSampleWindowCpuRuntimeNs':[t['cpuRuntimeNs']for t in attrib['threadTotals']if t['tid']in attrib['apTraceThreadIds']],'guestAPSampleWindowRunqueueWaitNs':[t['runqueueWaitNs']for t in attrib['threadTotals']if t['tid']in attrib['apTraceThreadIds']]})
for name in ['before','after']:
 p=json.loads((E/f'preservation-{name}.json').read_text());ck(name+' prior22575 protected paths exact',p['checked']==22575 and not p['failures'])
ck('exactly two planned actual starts',len(list((E/'started').glob('*.json')))==2)
allocated=sum(p.stat().st_blocks*512 for p in E.rglob('*')if p.is_file());ck('bounded storage and floor',allocated<=2.25*2**30 and min(minfree)>20*2**30 and shutil.disk_usage(R).free>20*2**30)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_DIAGNOSTICS_VERIFIED_STABLE1X_NOT_MET','checks':checks,'requirementsImplemented':6,'requirementsTotal':6,'fullCampaignAccepted':False,'deferred':['R1 freshness/land failure and controller archive failure preserved','R1 guest observer quota error retained despite raw forensic export','Guest scheduling is sampled; exact host runnable wait UNKNOWN','One run/mode with disclosed v1/v2 closure/quota difference; no causal performance or stable1x claim'],'actualFrames':sum(v['frames']for v in summary),'uiRows':sum(v['uiRows']for v in summary),'uiChunks':sum(v['uiChunks']for v in summary),'runs':summary,'allocatedBytes':allocated,'freeGiB':shutil.disk_usage(R).free/2**30,'minimumHostPointFreeGiB':min(minfree)/2**30,'initialMockChecks':55,'v2AdditionalMockChecks':6,'scope':'Bounded host-only simulator/evidence, no SDK/signature/frozen-source/ENDURE acceptance'}
with(E/'verification-final.json').open('x')as f:json.dump(r,f,indent=2)
print(json.dumps({k:v for k,v in r.items()if k not in ['checks']},indent=2))
