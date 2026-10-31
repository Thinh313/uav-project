from pathlib import Path
import json,hashlib,datetime,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/alloc60';checks=[];deferred=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
pins=json.loads((E/'source-pins.json').read_text())['files'];ck('all launch source pins unchanged through four runs',all(sha(R/p)==h for p,h in pins.items()))
order=[];frames=0;syscalls=0;flight=0;pointFree=[]
for i in range(1,5):
 tag=f'R{i}';driver=json.loads((E/f'a60{tag}-driver-result.json').read_text());out=E/'runs'/driver['owner']['run'];launch=json.loads((out/'launch.json').read_text());req=json.loads((out/'request.json').read_text());read=json.loads((out/'readback.json').read_text());io=json.loads((out/'io-analysis.json').read_text());verify=json.loads((out/'io-verification.json').read_text());extent=json.loads((out/'extent-verification.json').read_text());closure=json.loads((out/'closure.json').read_text());browser=json.loads((E/f'{tag}-browser.json').read_text());ui=browser['qa']['metrics']['timing']
 try:draw=json.loads(browser['drawFrames']);completeUI=True
 except json.JSONDecodeError:
  assert i==2;draw=json.loads((E/'R2-ui-prefix.json').read_text());completeUI=False;deferred.append({'requirement':'REQ4 full raw UI trace','run':'R2','status':'PARTIAL','missingTailDrawRows':111,'physicsEvidenceComplete':True})
 order.append(req['allocation']);frames+=read['frames'];syscalls+=io['syscallRows'];flight+=bool(read['takeoffAndLandPhysicalObservations'])
 ck(tag+' every admitted frame exact original oracle and barrier conservation',read['frames']==read['exactOriginalSensorAndAuxFrames']==verify['frames']==io['frames']==extent['frames'] and verify['fsyncBeforeEverySensorSend'] and not io['errors'])
 ck(tag+' raw/readback current SHA',all(sha(out/p)==h for p,h in read['filesSha256'].items()))
 ck(tag+' syscall/wake/stage current SHA',all(sha(out/p)==h for p,h in io['filesSha256'].items()))
 ck(tag+' clean closure all owned processes',closure['backendExitCode']==0 and closure['backendExited'] and closure['ownedContainerStopped'] and closure['wakeProcessExitCode']==0 and closure['error']is None)
 ck(tag+' fixed optimized AP rate speedup cap',launch['speedup']==1 and launch['negativeDebtCapUs']==500000 and launch['rateHz']==1200 and req['mode']=='optimized' and launch['allocation']==req['allocation'])
 ck(tag+' UI identity viewport/no overflow',draw['run']==out.name==ui['run'] and not ui['active'] and not ui['overflow'] and browser['viewport']==[1920,1080] and not browser['qa']['errors'])
 if completeUI:
  ck(tag+' complete raw draw mean arithmetic',len(draw['rows'])==ui['frames'] and abs((len(draw['rows'])-1)*1000/(draw['rows'][-1][0]-draw['rows'][0][0])-ui['measuredHz'])<1e-8)
 else:ck(tag+' truncated export prefix retained honestly',len(draw['rows'])==4821 and draw['missingUiTailRows']==111 and ui['frames']==4932 and all(a[0]<=b[0]for a,b in zip(draw['rows'],draw['rows'][1:])))
 ck(tag+' no POST retry and failure classification retained',driver['postRetries']==0 and (driver['status']=='PASS_BOUNDED_COUPLED_CAPTURE' if i!=3 else driver['status']=='FAIL' and driver['error']=='BENCH_OBSERVATION_DEADLINE' and not read['takeoffAndLandPhysicalObservations'] and not read['prearmDecisionsIndependentlyChecked']))
 for line in(out/'host-observer.jsonl').read_text().splitlines():pointFree.append(json.loads(line)['freeBytes'])
ck('four attempts exactly ABBA',order==['none','preallocate','preallocate','none'] and len(list((E/'started').glob('*.json')))==4)
for name in ['before','after']:
 d=json.loads((E/f'preservation-{name}.json').read_text());ck(name+' 22101protected paths no mismatch',d['checked']==22101 and not d['failures'])
qa=[json.loads((E/n).read_text())for n in ['qa-allocation.json','qa-io.json','qa-extra.json','qa-crash02.json','qa-backend-q01.json']];ck('61 final scoped mock checks pass',sum(len(q['checks'])for q in qa)==61 and all(c['pass']for q in qa for c in q['checks']))
phase=json.loads((E/'matched-model-interval.json').read_text());ck('all four including failure share 18000 ground frames 10to25model seconds',len(phase['rows'])==4 and all(v['frames']==18000 and v['allGround'] and v['modelIntervalSeconds']==[10,25]for v in phase['rows']))
allocated=sum(p.stat().st_blocks*512 for p in E.rglob('*')if p.is_file());ck('budget and observed floor maintained',allocated<2.5*2**30 and min(pointFree)>20*2**30 and shutil.disk_usage(R).free>20*2**30)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_FUNCTIONAL_PREALLOCATION_VERIFIED_PERFORMANCE_NOT_ACCEPTED','requirementsImplemented':5,'requirementsTotal':5,'requirementsFullyVerified':4,'deferred':deferred,'checks':checks,'mockChecks':61,'controlEquivalenceChecks':5,'actualAttempts':4,'flightJourneysCompleted':flight,'preflightFailedUnarmed':1,'originalOracleFrames':frames,'syscallObservations':syscalls,'allocatedBytes':allocated,'freeGiB':shutil.disk_usage(R).free/2**30,'minimumHostPointFreeGiB':min(pointFree)/2**30,'selection':'NONE_EXPERIMENTAL_ONLY','stable1x':'NOT_MET','exclusiveSchedulerWait':'UNKNOWN_PROXY_ONLY','scope':'Point-in-time integrity and bounded tests, not fullG1/signature/ENDURE/Hera/powerloss acceptance'}
with(E/'verification-final.json').open('x')as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items()if k!='checks'},indent=2))
