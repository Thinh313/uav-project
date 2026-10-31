"""Conditional duration prediction from closed short STAGE bytes; never flight acceptance."""
from pathlib import Path
from importlib import import_module
from collections import deque
import hashlib,json,math,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-observer11.flight'
NS=1_000_000_000;FRAME_HZ=1200;WINDOW_NS=5*NS;TARGET_SECONDS=1802;LANDING_SECONDS=40;SAFETY_SECONDS=10

def integer(v):return type(v)is int and v>=0
def stage_rtf(rows):
 origin=None;first=last=None;previous=None;window=deque();minimum=None;windows=0;count=0;maximum_stage_gap=0
 for row in rows:
  b=row['body']
  if b['kind']!='EVENT':continue
  event=b['payload'];kind,d=event['eventKind'],event['data']
  if kind=='TIMING_ORIGIN':
   if origin is not None or not integer(d.get('hostMonotonicNs')):raise ValueError('SINGLE_QUALIFIED_ORIGIN_REQUIRED')
   origin=d['hostMonotonicNs']
  elif kind=='STAGE':
   f=d['frame'];fields=d['fields'];off=fields['receiveSinceOriginNs']
   if origin is None or not integer(f)or not integer(off)or fields['wireFrame']!=f:raise ValueError('STAGE_SCHEMA')
   p=(origin+off,f)
   if previous is not None:
    if f!=previous[1]+1 or p[0]<previous[0]:raise ValueError('CONTIGUOUS_MONOTONIC_STAGE_REQUIRED')
    maximum_stage_gap=max(maximum_stage_gap,p[0]-previous[0])
   if first is None:first=p
   last=previous=p;count+=1;window.append(p)
   while len(window)>1 and p[0]-window[1][0]>=WINDOW_NS:window.popleft()
   if p[0]-window[0][0]>=WINDOW_NS:
    seconds=(p[0]-window[0][0])/NS;rtf=(f-window[0][1])/FRAME_HZ/seconds
    minimum=rtf if minimum is None else min(minimum,rtf);windows+=1
 if first is None or minimum is None or last[0]<=first[0]:raise ValueError('MEASURED_STAGE_SPAN_AT_LEAST5S_REQUIRED')
 full=(last[1]-first[1])/FRAME_HZ/((last[0]-first[0])/NS)
 return {'fullRTF':full,'minimumRolling5sRTF':minimum,'chosenRTF':min(full,minimum),'rollingWindows':windows,'frames':count,'firstStageHostNs':first[0],'lastStageHostNs':last[0],'hostStageSpanSeconds':(last[0]-first[0])/NS,'modelSpanSeconds':(last[1]-first[1])/FRAME_HZ,'maximumStageGapNs':maximum_stage_gap,'rollingPolicy':'EVERY_STAGE_WINDOW_AT_LEAST5S_KEEP_BOUNDARY_PREDECESSOR_NO_INTERPOLATION'}

def project(metrics,host_start_ns,hold_start_ns,native_open_ns,native_hold_ns):
 for v in(host_start_ns,hold_start_ns,native_open_ns,native_hold_ns):
  if not integer(v):raise ValueError('TYPED_OBSERVED_DURATION_CLOCK_REQUIRED')
 if hold_start_ns<host_start_ns or native_hold_ns<native_open_ns:raise ValueError('STARTUP_DURATION_REGRESSION')
 rtf=metrics['chosenRTF']
 if type(rtf)not in(int,float)or not math.isfinite(rtf)or rtf<=0:raise ValueError('POSITIVE_MEASURED_RTF_REQUIRED')
 host_warm=(hold_start_ns-host_start_ns)/NS;native_warm=(native_hold_ns-native_open_ns)/NS;flight=max(float(TARGET_SECONDS),TARGET_SECONDS/rtf)
 hp=host_warm+flight+LANDING_SECONDS+SAFETY_SECONDS;np=native_warm+flight+LANDING_SECONDS+SAFETY_SECONDS
 # No extra cap500 catchup credit.250/200/500 freshness/cadence guards stay elsewhere.
 ok=hp<=1960 and np<=2000
 return {'status':'CONDITIONAL_DURATION_FEASIBLE'if ok else'DURATION_NOT_FEASIBLE_STOP_BEFORE_LONG','hostProjectionSeconds':hp,'hostMaximumSeconds':1960,'nativeProjectionSeconds':np,'nativeMaximumSeconds':2000,'observedShortHostWarmupSeconds':host_warm,'observedShortNativeWarmupSeconds':native_warm,'projected1802ModelAPSecondsAtChosenRTF':flight,'targetContinuousSeconds':TARGET_SECONDS,'landingReserveSeconds':LANDING_SECONDS,'safetyReserveSeconds':SAFETY_SECONDS,'measuredShortRTF':metrics,'assumedExtraCatchupSeconds':0,'capMsUnchanged':500,'conditionalShortToLongExtrapolationNotGuarantee':True,'actualThirtyMinuteAccepted':False,'differences':'Measured laptop/guest short workload; long-duration scheduling/IO, filesystem and power are not proven by this estimate.'}


def native_byte_rate(records,metadata_bytes=0):
 if type(metadata_bytes)is not int or metadata_bytes<0:raise ValueError('PHYSICAL_METADATA_BOUND')
 window=deque();pbytes=dbytes=0;first=last=None;total=decoded=count=windows=0;maximum=decodedMaximum=None
 for at,size,logical in records:
  if not integer(at)or type(size)is not int or not 1<=size<=8352 or type(logical)is not int or not 1<=logical<=32768 or last is not None and at<last:raise ValueError('NATIVE_PHYSICAL_RECORD_CLOCK_OR_BOUND')
  first=at if first is None else first;last=at;total+=size;decoded+=logical;count+=1;window.append((at,size,logical));pbytes+=size;dbytes+=logical
  while len(window)>1 and at-window[1][0]>=WINDOW_NS:
   _,p,d=window.popleft();pbytes-=p;dbytes-=d
  if at-window[0][0]>=WINDOW_NS:
   span=(at-window[0][0])/NS;rate=(pbytes+metadata_bytes)/span;drate=dbytes/span;maximum=rate if maximum is None else max(maximum,rate);decodedMaximum=drate if decodedMaximum is None else max(decodedMaximum,drate);windows+=1
 if first is None or maximum is None or last<=first:raise ValueError('NATIVE_BYTE_SPAN_AT_LEAST5S_REQUIRED')
 span=(last-first)/NS;full=(total+metadata_bytes)/span;dfull=decoded/span
 return dict(totalRecordBytes=total+metadata_bytes,physicalFrameBytes=total,physicalMetadataBytes=metadata_bytes,records=count,firstNativeNs=first,lastNativeNs=last,spanSeconds=span,fullBytesPerSecond=full,maximumRolling5sBytesPerSecond=maximum,chosenBytesPerSecond=max(full,maximum),rollingWindows=windows,countsEveryRawRecordIncludingHeadersAndTerminal=True,boundaryPredecessorIncludedWholeNoInterpolation=True,physicalFormatVersion=2,rollingMetadataPolicy='ALL_PHYSICAL_HEADERS_SEALS_SESSION_BYTES_CHARGED_TO_EVERY_WINDOW_CONSERVATIVE_NOT_TIMESTAMP_INFERRED',totalDecodedLogicalBytes=decoded,decodedFullBytesPerSecond=dfull,decodedMaximumRolling5sBytesPerSecond=decodedMaximum,decodedChosenBytesPerSecond=max(dfull,decodedMaximum))

def native_records(path,prefix,expected_sha,external_anchor):
 _frozen_native_stream=import_module('planning.betaintegrated01.cockpit05-compact10.flight.native_stream')
 IndexedNative=_frozen_native_stream.IndexedNative
 source=IndexedNative(path,prefix).verify(external_anchor)
 if source.tar_sha!=expected_sha:raise ValueError('SHORT_QUALIFIED_NATIVE_TAR_SHA')
 return source

def include_native_budget(projection,metrics):
 value=dict(projection);time_status=value['status'];quota=160*2**20;close_reserve=2*2**20;rate=metrics['chosenBytesPerSecond']
 if type(rate)not in(int,float)or not math.isfinite(rate)or rate<=0:raise ValueError('POSITIVE_MEASURED_NATIVE_BYTE_RATE_REQUIRED')
 projected=math.ceil(rate*value['nativeProjectionSeconds'])+close_reserve;feasible=projected<=quota
 value['nativeCapacity']={'status':'CONDITIONAL_NATIVE_BYTES_FEASIBLE'if feasible else'NATIVE_BYTES_NOT_FEASIBLE','feasible':feasible,'projectedBytes':projected,'nativeJournalQuotaBytes':quota,'closeReserveBytes':close_reserve,'nativeActiveProjectionSeconds':value['nativeProjectionSeconds'],'actualShortRecordByteRate':metrics,'quotaUnchanged':True,'shortExtrapolationNotGuarantee':True}
 decodedProjected=math.ceil(metrics['decodedChosenBytesPerSecond']*value['nativeProjectionSeconds'])+close_reserve
 value['decodedCapacity']=dict(feasible=decodedProjected<=512*2**20,projectedBytes=decodedProjected,decodedProcessingBoundBytes=512*2**20,physicalQuotaUnchanged=True)
 feasible=feasible and value['decodedCapacity']['feasible']
 value['timeOnlyStatus']=time_status
 if not feasible:value['status']='DURATION_NATIVE_BYTES_NOT_FEASIBLE_STOP_BEFORE_LONG'
 return value

def main():
 contract=import_module(H+'.contract');contract.verify_full_inputs();E=R/contract.EVIDENCE;C=E/'actual-short01/control';read=lambda p:json.loads(Path(p).read_text());resultPath=E/'qa/short-cold01/results.json';short=read(resultPath)
 if short.get('status')!='SHORT_PASS_CLOSED_RAW_ONLY':raise ValueError('ACTUAL_NEW_SHORT_CLOSED_RAW_PASS_REQUIRED')
 d=import_module(contract.COMPUTATIONAL+'.durations');metrics=stage_rtf(d.rows(E/'actual-short01/raw/journal'));hold=read(C/'assisted-window-start.json');start=read(C/'host-launch-intent.json');state=hold['state'];out=project(metrics,start['hostNs'],hold['hostNs'],state['lifecycle']['openedNs'],state['lifecycle']['activeNs']+state['lifecycle']['activeElapsedNs'])
 location=read(C/'native-export-location.json');tarSHA=short['nativeAuthority']['chain']['nativeTarSHA256']
 if location['sha256']!=tarSHA:raise ValueError('SHORT_NATIVE_EXPORT_BINDING')
 descriptor=read(C/'native-confirmation-descriptor.json');source=native_records(location['path'],'files/control-runs/'+state['run']+'/',tarSHA,descriptor['nativeExternalAnchor']);byteMetrics=native_byte_rate(source.physical_records(),source.physicalMetadataBytes);out=include_native_budget(out,byteMetrics)
 out.update(basisShortResultsSHA256=contract.sha(resultPath),run=state['run'],epoch=state['epoch'],boot=state['boot'],sourceSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='CLOSED_SHORT_CAPACITY_PLANNING_ONLY_NO_FRESHNESS_OR_SPEEDUP_WAIVER')
 target=E/'qa/duration-feasibility01.json'
 with target.open('x')as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps({'status':out['status'],'chosenRTF':metrics['chosenRTF'],'hostProjectionSeconds':out['hostProjectionSeconds'],'nativeProjectionSeconds':out['nativeProjectionSeconds']}))
if __name__=='__main__':main()
