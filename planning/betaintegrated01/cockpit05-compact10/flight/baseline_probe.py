"""Read-only locality from already qualified09raw; no replay/runtime/services."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,struct
R=Path(__file__).resolve().parents[4]
def summary(v):
 s=sorted(v)
 return dict(count=len(s),total=sum(s),mean=sum(s)/len(s),p50=s[len(s)//2],p95=s[int((len(s)-1)*.95)],maximum=s[-1])if s else None
def main():
 E=R/'evidence/betaintegrated01-cockpit05-iocommit09';B=E/'actual-short01';a=json.loads((E/'host/actual-short-analysis01.json').read_text());w=a['worstPacingWindow'];first,last=w['firstFrame'],w['lastFrame'];stages=[]
 for p in sorted((B/'raw/journal').glob('segment-*.jsonl')):
  with p.open('rb')as f:
   for line in f:
    r=json.loads(line);b=r['body']
    if b['kind']=='EVENT'and b['payload']['eventKind']=='STAGE':d=b['payload']['data'];stages.append((d['frame'],d['fields']))
 host=defaultdict(list)
 for ix,(n,f)in enumerate(stages):
  if not first<=n<=last:continue
  for key,x,y in [('receiveToGroupEnd','receiveSinceOriginNs','frameGroupEndSinceOriginNs'),('beforeComputeIncludingRX','receiveSinceOriginNs','computeBeginSinceOriginNs'),('physicsCompute','computeBeginSinceOriginNs','computeEndSinceOriginNs'),('afterComputeToSocketEntryIncludingINTENTBarrier','computeEndSinceOriginNs','sendBeginSinceOriginNs'),('socketCallback','sendBeginSinceOriginNs','sendEndSinceOriginNs'),('afterSocketToGroupEndIncludingSENTBarrier','sendEndSinceOriginNs','frameGroupEndSinceOriginNs')]:host[key].append(f[y]-f[x])
  if ix+1<len(stages):host['groupEndToNextRX_INCLUDES_UNMEASURED_STAGE_AP_NETWORK_SCHEDULING'].append(stages[ix+1][1]['receiveSinceOriginNs']-f['frameGroupEndSinceOriginNs'])
 event=struct.Struct('<QQIIQQQQq');selected=defaultdict(dict);counts=Counter();duplicates=Counter()
 for p in sorted((B/'raw/ap-stage').glob('stage-*.bin')):
  with p.open('rb')as f:
   header=f.readline(4097);assert header.endswith(b'\n')and json.loads(header)['eventBytes']==64;raw=f.read()
  assert len(raw)%64==0
  for seq,n,k,tid,begin,end,arg,extra,result in event.iter_unpack(raw):
   if first<=n<=last:
    if k in selected[n]:duplicates[k]+=1
    selected[n][k]=(begin,arg,extra,result);counts[k]+=1
 assert not duplicates,'Cannotderiveuniqueperframekindwhenretriesexist; retainrawandreportunknowninstead'
 ap=defaultdict(list)
 for n,v in selected.items():
  for key,x,y in [('APServoSend',10,11),('APSensorReceiveWait_INCLUDES_HOST_NETWORK_SCHEDULING',12,13),('APSensorParse',13,14),('APSyncWallTotal',20,24),('APSleepCallObserved',22,23)]:
   if x in v and y in v:ap[key].append(v[y][0]-v[x][0])
  if 21 in v:ap['APDebtAt21SignedMicroseconds'].append(v[21][1]if v[21][1]<2**63 else v[21][1]-2**64)
 v=dict(status='READ_ONLY_CLOSED09_PACING_LOCALITY_PROPOSAL_NOT_ROOTCAUSE_PROVEN',baselineAnalysisSHA256=hashlib.sha256((E/'host/actual-short-analysis01.json').read_bytes()).hexdigest(),worstWindow=w,hostStageMetricNs={k:summary(x)for k,x in host.items()},APStageMetrics={k:summary(x)for k,x in ap.items()},APEventCounts=dict(counts),APDuplicateKinds=dict(duplicates),known=[{'source':'entry10/runtime/journal/writer.py:_record','fact':'PayloadboundedthenrawbodyencodedforhashCRC; enclosingbodyencodedagain. PotentialredundantJSONwork, notprovenprimarybottleneck.'},{'source':'clockowner02/runtime/frame_adapter.py:receive','fact':'frameGroupEnd isBEFOREappend_stage, soSTAGEserialization/fsyncnotseparatelytimed. DiagnosticIOsuccesslast8syscallsarenotpublished; nofullhostwrite/fsync/threadCPUtimelinein09closedraw.'},{'source':'entry10/runtime/journal/writer.py:record_frame/append_stage','fact':'INTENT/SENT/STAGEeachfsync; noauthorizationtodropbarrier.'}],proposedSmallestSteps=[{'action':'Boundedmeasurefirst','detail':'Newin-memorycount/hist/worst32 wall+threadCPU forserialize/guard/write/fsync/stage/recvwait; afterclosepublishonly. Nogroup/sensororderingchange, nohotextraIO.'},{'action':'Byteidenticalprepareonceonlyifbenchmarkmeasurable','detail':'Canonicalbodyonce theninjectexactrawbody intoenvelope; retainCRCSHApreviouschain/fullallframebytes/barriers andstrictdifferentialtests. No performanceguaranteefromstaticread.'},{'action':'Nativephysicalv2perrecordcodec','detail':'Rootapprovedcontractneeded; exactoriginal09rowbytes independentrandomaccessrawDEFLATEframes; strictphysical/logicalanchors, expansion/truncation/corruptionbound. Physicalcapacityoverevery5swindowwithoriginaltimes andheader/terminalbytes. No recorddrop.'}],unknown='Noexclusivefilesystemvsdescheduleattribution. APstageintervalsincludetraceemitteroverhead; crossclocksubtractionnotperformed. WorstpostLANDphaseisretainedinwholegate.',preparationError='FirstreadprobeincorrectlyunpackedJSONheaderas64Bbinary andraisedstruct.error beforeanyoutput; correctedheaderparsebasedonfrozenap_stage.py. Oldrawunchanged.',sourceOrRawModified=False,actualRuntimeLaunched=False)
 O=R/'evidence/betaintegrated01-cockpit05-compact10/host';O.mkdir(parents=True,exist_ok=True);p=O/'pacing-baseline-proposal01.json';p.open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(receipt=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),host=v['hostStageMetricNs'],AP=v['APStageMetrics'])))
if __name__=='__main__':main()
