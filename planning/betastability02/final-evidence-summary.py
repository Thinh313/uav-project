"""Cold final metadata summary. Does not turn component evidence into E2E PASS."""
from pathlib import Path
import json,sys,re,datetime,hashlib,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/betastability02'
if len(sys.argv)!=2 or not re.fullmatch('[a-zA-Z0-9-]{1,48}',sys.argv[1]):raise SystemExit('Usage: final-evidence-summary.py <unique-tag>')
if(R/'.local/betastability02/active').exists():raise SystemExit('NOT_RUN_RUNTIME_ACTIVE; run only after closure')
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def declared_status(p):
 if p.stat().st_size>2*2**20:return'PAYLOAD_TOO_LARGE_FOR_METADATA_PARSE'
 value=load(p);return value.get('status')if isinstance(value,dict)else'NON_OBJECT_RECEIPT_INDEX_ONLY'
launches=[];requests=[];apRuns=[]
for p in sorted((E/'launches').glob('*/launch.json')):
 c=p.with_name('closure.json');q=load(p);closed=load(c)if c.is_file()else None
 if not closed or any(x.get('exit')is None for x in closed.get('children',[])):raise SystemExit('NOT_RUN_UNCLOSED_COMPANION:'+str(p))
 launches.append({'launch':rel(p),'ownerId':q.get('owner',{}).get('id'),'pinsSha256':sha(p.with_name('source-pins.json'))if p.with_name('source-pins.json').is_file()else None,'closed':True,'closureError':closed.get('error'),'children':[{k:x.get(k)for k in ['pid','exit']}for x in closed.get('children',[])]})
 for req in p.parent.glob('host/flight/runs/*/request.json'):
  d=load(req);rd=req.parent;la=rd/'launch.json';re=rd/'review.json';cl=rd/'closure.json'
  requests.append({'request':rel(req),'run':rd.name,'mode':d.get('mode'),'containerAllocated':la.is_file()})
  r=load(re)if re.is_file()else None;a=load(la)if la.is_file()else None
  apRuns.append({'run':rd.name,'request':rel(req),'containerAllocated':a is not None,'containerId':a.get('containerId')if a else None,'guestPid':a.get('pid')if a else None,'reviewSource':r.get('source')if r else None,'navigationAccepted':r.get('accepted')if r else None,'reviewReason':r.get('reason')if r else None,'rawRecords':r.get('rawRecords')if r else None,'closurePresent':cl.is_file()})
campaigns=[]
for version in ['01','02','03','04']:
 p=E/('final-campaign'+version+'.json')
 if p.is_file():
  q=load(p);cases=[]
  for c in q.get('results',[]):
   receiver=c.get('receiver')or{};v=receiver.get('videoQuality')or{};t=receiver.get('traceCoverage')or{}
   cases.append({k:c.get(k)for k in ['kind','index','status','run','host','error']})
   cases[-1].update(navigationAccepted=receiver.get('accepted'),videoStatus=v.get('status'),videoFps=v.get('displayedFps'),maximumConservativeGapMs=v.get('maximumConservativeGapMs'),traceCoverage=t.get('status'))
  campaigns.append({'receipt':rel(p),'sourcePins':q.get('sourcePins'),'status':q.get('status'),'error':q.get('error'),'completedQualifiedCases':q.get('completedCases'),'cases':cases})
 else:campaigns.append({'receipt':None,'plannedScript':'planning/betastability02/final-campaign'+(''if version=='01'else version)+'.py','sourcePins':'source-pins07.json'if version=='04'else None,'status':'NOT_RUN','cases':[{'kind':k,'index':i,'status':'NOT_RUN'}for k in ['polygon','corridor']for i in [1,2,3]],'noSyntheticCampaignReceiptCreated':True})
faults=[]
for kind in ['cut','reboot']:
 p=E/('fault-component-'+kind+'07.json')
 if p.is_file():
  q=load(p);faults.append({'receipt':rel(p),**{k:q.get(k)for k in ['kind','run','status','scope','preArmedObserved','preLeaseCount','postLeaseCount','video','capture','fullNominalQualified','authorityRestored']}})
 else:faults.append({'kind':kind,'status':'NOT_CHECKED_NO_COMPONENT_RECEIPT'})
probe=E/'android-video-probe07.json';video=None
if probe.is_file():
 q=load(probe);last=q.get('rows',[])[-1]if q.get('rows')else{};v=last.get('viewer')or{}
 video={'receipt':rel(probe),'source':q.get('source'),'actualFlight':q.get('actualFlight'),'fullAUTOAcceptance':q.get('fullAUTOAcceptance'),'error':q.get('error'),'lastViewerActive':v.get('active'),'decoderErrors':v.get('counters',{}).get('decoderErrors'),'lastFailure':v.get('failure'),'workerFatal':v.get('worker',{}).get('fatal'),'decoderLastError':v.get('decoder',{}).get('lastError'),'mediaSession':v.get('session')}
# Count every retained path, including mock/failure/source-revision evidence.
files=0;size=0;symlinks=[]
for root,dirs,names in os.walk(E,followlinks=False):
 for n in list(dirs):
  p=Path(root)/n
  if p.is_symlink():files+=1;size+=p.lstat().st_size;symlinks.append(rel(p));dirs.remove(n)
 for n in names:
  p=Path(root)/n;s=p.lstat();files+=1;size+=s.st_size
  if p.is_symlink():symlinks.append(rel(p))
bareMedia=[rel(E/'source-relay01/media/launch.json'),rel(E/'source-relay02/media/launch.json')];bareMedia=[n for n in bareMedia if(R/n).is_file()]
entry=load(E/'entry01.json');elapsedSeconds=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(entry['atUTC'])).total_seconds()
budget={'taskWallBudgetMinutes':180,'taskElapsedSecondsAtSummary':elapsedSeconds,'usageSnapshotBeforeThisReceipt':True,'wholeRetainedTaskFiles':files,'wholeRetainedTaskBytes':size,'maxFiles':12000,'maxBytes':2*2**30,'allMockFailureRevisionPathsIncluded':True,'symlinksCounted':symlinks,'APRequestReceipts':len(requests),'maxAPRequests':12,'allocatedAPContainers':len([r for r in requests if r['containerAllocated']]),'observedCompanionLaunches':len(launches),'retainedBareSourceHostReceipts':bareMedia,'declaredHostStartAccounting':len(launches)+len(bareMedia),'maxHostStarts':8,'hostCountScope':'COMPANION_LAUNCHES_PLUS_TWO_DECLARED_BOUND_SOURCE_RELAYS; PURE_HTTP_HANDLER_MOCKS_NOT_BOUND_HOST_STARTS','withinObservedBudgets':files<=12000 and size<2*2**30 and len(requests)<=12 and len(launches)+len(bareMedia)<=8 and elapsedSeconds<=180*60}
artifacts=[]
for p in sorted(E.glob('*.json')):
 if any(w in p.name for w in ['saf','restart','persist','ui-','acceptance','probe07','component','preservation-final']):artifacts.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p),'declaredStatus':declared_status(p),'interpretation':'RECEIPT_INDEX_ONLY_NOT_AUTOMATIC_ACCEPTANCE'})
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'EXECUTED_VERSUS_NOT_RUN_EVIDENCE_METADATA_INVENTORY_NOT_PRODUCT_ACCEPTANCE','status':'NOT_READY','currentPins':'source-pins07.json','currentQualifiedNominal':{'passed':0,'required':6,'reason':'NO_QUALIFIED_CURRENT_FIXED_BUILD_SIX_CASE_CAMPAIGN_RECEIPT'},'priorCampaigns':campaigns,'componentFaults':faults,'integratedVideoPayloadFaults':'NOT_RUN_WITH_VALID_VIDEO','currentVideoProbe':video,'APRuns':apRuns,'budgets':budget,'launches':launches,'additionalReceiptIndex':artifacts,'actualCameraImages':0,'HeraHubHardware':'NOT_CHECKED','productionSigning':False,'ENDUREAcceptanceClaim':False,'authorityRestorable':False}
out=E/('evidence-summary-'+sys.argv[1]+'.json');encoded=json.dumps(report,indent=2)+'\n'
if files+1>12000 or size+len(encoded.encode())>=2*2**30:raise SystemExit('FINAL_RECEIPT_QUOTA_RESERVE_NOT_AVAILABLE')
out.open('x').write(encoded);print(json.dumps({'output':rel(out),'status':report['status'],'budgets':budget,'componentFaults':[{k:v for k,v in f.items()if k in ['kind','run','status']}for f in faults]},indent=2))
