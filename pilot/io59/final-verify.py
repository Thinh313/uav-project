from pathlib import Path
import json,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/io59';checks=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
pins=json.loads((E/'source-pins.json').read_text())['files'];ck('all launch source pins current',all(sha(R/p)==h for p,h in pins.items()))
summary=[]
for tag in ['D1','D2']:
 d=json.loads((E/f'i59{tag}-driver-result.json').read_text());rid=d['owner']['run'];out=E/'runs'/rid
 read=json.loads((out/'readback.json').read_text());io=json.loads((out/'io-analysis.json').read_text());pace=json.loads((E/f'{tag}-pacing.json').read_text());ver=json.loads((out/'io-verification.json').read_text());browser=json.loads((E/f'{tag}-browser.json').read_text());ui=browser['qa']['metrics']['timing'];draw=json.loads(browser['drawFrames'])
 ck(tag+' coupled takeoff hold land observed',d['status']=='PASS_BOUNDED_COUPLED_CAPTURE' and read['takeoffAndLandPhysicalObservations'])
 ck(tag+' every original oracle frame conserved',read['exactOriginalSensorAndAuxFrames']==read['frames']==ver['frames']==io['frames'])
 ck(tag+' raw readback SHA current',all(sha(out/p)==h for p,h in read['filesSha256'].items()))
 ck(tag+' syscall/wake/stage SHA current',all(sha(out/p)==h for p,h in io['filesSha256'].items()))
 ck(tag+' UI full draw trace retained',ui['run']==rid==draw['run'] and not ui['active'] and not ui['overflow'] and not draw['overflow'] and len(draw['rows'])==ui['frames'] and browser['viewport']==[1920,1080] and browser['qa']['errors']==[])
 # Independent arithmetic against raw draw times, not only DOM summary.
 dr=draw['rows'];hz=(len(dr)-1)*1000/(dr[-1][0]-dr[0][0]);ck(tag+' actual mean draw Hz arithmetic',abs(hz-ui['measuredHz'])<1e-8)
 launch=json.loads((out/'launch.json').read_text());ck(tag+' speedup/cap/rate fixed',launch['speedup']==1 and launch['negativeDebtCapUs']==500000 and launch['rateHz']==1200)
 summary.append({'tag':tag,'run':rid,'frames':read['frames'],'wholeRTF':pace['wholeRTF'],'minimumFullFiveSecondRTF':min(v['fixedWallBucketRTF']for v in pace['windows']if v['fullFiveSeconds']),'gapP99Ms':pace['hostReceiveGapMs']['p99'],'gapMaxMs':pace['hostReceiveGapMs']['max'],'capClips':pace['ap']['capClipCount'],'discardedDebtUs':pace['ap']['discardedDebtUs'],'maxWriteRXMs':io['groups']['write:RX']['wallMs']['max'],'maxFsyncMs':io['groups']['fsync:INTENT']['wallMs']['max'],'backendMaxMs':io['hostReceiveToSendMs']['max'],'backendWorstCpuMs':io['worstFrames'][0]['threadCpuMs'],'uiHz':ui['measuredHz'],'syscallRows':io['syscallRows'],'wakeThreadMaxMs':io['wake']['thread']['latenessMs']['max'],'wakeProcessMaxMs':io['wake']['process']['latenessMs']['max']})
for label in ['before','after']:
 p=json.loads((E/f'preservation-{label}.json').read_text());ck(label+' preservation no mismatch',p['checked']==21795 and not p['failures'])
qa=[json.loads((E/n).read_text())for n in ['qa-io.json','qa-extra.json','qa-backend-q02.json']];ck('35 final source mock/fault checks pass',sum(len(q['checks'])for q in qa)==35 and all(c['pass']for q in qa for c in q['checks']))
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SCOPED_DIAGNOSTICS_VERIFIED_NOT_READY_STABLE_1X','requirementsImplemented':6,'requirementsTotal':6,'stable1xAcceptance':'NOT_MET_SUBWINDOW_JITTER_AND_CAP_CLIPS','exclusiveKernelSchedulerWait':'NOT_CHECKED_PROXY_ONLY','checks':checks,'mockFinalChecks':35,'mockFinalOracleFrames':4800,'actualStarts':2,'actualFrames':sum(x['frames']for x in summary),'syscallRows':sum(x['syscallRows']for x in summary),'runs':summary,'freeGiB':shutil.disk_usage(R).free/2**30,'scope':'No matched observer-free AB or calibrated Hera, no production/signature/ENDURE acceptance'}
with(E/'verification-final.json').open('x')as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
