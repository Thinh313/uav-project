"""Conditional duration prediction from closed short STAGE bytes; never flight acceptance."""
from pathlib import Path
from importlib import import_module
from collections import deque
import hashlib,json,math,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-iocommit09.flight'
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


def native_byte_rate(records):
 window=deque();window_bytes=0;first=last=None;total=count=0;maximum=None;windows=0
 for at,size in records:
  if not integer(at)or type(size)is not int or not 1<=size<=16384 or last is not None and at<last:raise ValueError('NATIVE_BYTE_RECORD_CLOCK_OR_BOUND')
  if first is None:first=at
  last=at;total+=size;count+=1;window.append((at,size));window_bytes+=size
  while len(window)>1 and at-window[1][0]>=WINDOW_NS:
   _,removed=window.popleft();window_bytes-=removed
  if at-window[0][0]>=WINDOW_NS:
   rate=window_bytes/((at-window[0][0])/NS);maximum=rate if maximum is None else max(maximum,rate);windows+=1
 if first is None or maximum is None or last<=first:raise ValueError('NATIVE_BYTE_SPAN_AT_LEAST5S_REQUIRED')
 full=total/((last-first)/NS)
 return {'totalRecordBytes':total,'records':count,'firstNativeNs':first,'lastNativeNs':last,'spanSeconds':(last-first)/NS,'fullBytesPerSecond':full,'maximumRolling5sBytesPerSecond':maximum,'chosenBytesPerSecond':max(full,maximum),'rollingWindows':windows,'countsEveryRawRecordIncludingHeadersAndTerminal':True,'boundaryPredecessorIncludedWholeNoInterpolation':True}

def native_records(path,prefix,expected_sha):
 from .native_stream import IndexedNative
 source=IndexedNative(path,prefix)
 if source.tar_sha!=expected_sha:raise ValueError('SHORT_QUALIFIED_NATIVE_TAR_SHA')
 n=0
 for ordinal in range(source.terminal['segments']):
  for line in source.read(f'segment-{ordinal:06}.jsonl').splitlines(keepends=True):
   row=json.loads(line);n+=1
   if row['n']!=n:raise ValueError('NATIVE_BYTE_RECORD_SEQUENCE')
   yield row['monotonicNs'],len(line)
 source.unchanged()
 if n!=source.terminal['records']:raise ValueError('NATIVE_BYTE_RECORD_COUNT')

def include_native_budget(projection,metrics):
 value=dict(projection);time_status=value['status'];quota=160*2**20;close_reserve=2*2**20;rate=metrics['chosenBytesPerSecond']
 if type(rate)not in(int,float)or not math.isfinite(rate)or rate<=0:raise ValueError('POSITIVE_MEASURED_NATIVE_BYTE_RATE_REQUIRED')
 projected=math.ceil(rate*value['nativeProjectionSeconds'])+close_reserve;feasible=projected<=quota
 value['nativeCapacity']={'status':'CONDITIONAL_NATIVE_BYTES_FEASIBLE'if feasible else'NATIVE_BYTES_NOT_FEASIBLE','feasible':feasible,'projectedBytes':projected,'nativeJournalQuotaBytes':quota,'closeReserveBytes':close_reserve,'nativeActiveProjectionSeconds':value['nativeProjectionSeconds'],'actualShortRecordByteRate':metrics,'quotaUnchanged':True,'shortExtrapolationNotGuarantee':True}
 value['timeOnlyStatus']=time_status
 if not feasible:value['status']='DURATION_NATIVE_BYTES_NOT_FEASIBLE_STOP_BEFORE_LONG'
 return value

def main():
 contract=import_module(H+'.contract');contract.verify_full_inputs();E=R/contract.EVIDENCE;C=E/'actual-short01/control';read=lambda p:json.loads(Path(p).read_text());resultPath=E/'qa/short-cold01/results.json';short=read(resultPath)
 if short.get('status')!='SHORT_PASS_CLOSED_RAW_ONLY':raise ValueError('ACTUAL_NEW_SHORT_CLOSED_RAW_PASS_REQUIRED')
 d=import_module(H+'.durations');metrics=stage_rtf(d.rows(E/'actual-short01/raw/journal'));hold=read(C/'assisted-window-start.json');start=read(C/'host-launch-intent.json');state=hold['state'];out=project(metrics,start['hostNs'],hold['hostNs'],state['lifecycle']['openedNs'],state['lifecycle']['activeNs']+state['lifecycle']['activeElapsedNs'])
 location=read(C/'native-export-location.json');tarSHA=short['nativeAuthority']['chain']['nativeTarSHA256']
 if location['sha256']!=tarSHA:raise ValueError('SHORT_NATIVE_EXPORT_BINDING')
 byteMetrics=native_byte_rate(native_records(location['path'],'files/control-runs/'+state['run']+'/',tarSHA));out=include_native_budget(out,byteMetrics)
 out.update(basisShortResultsSHA256=contract.sha(resultPath),run=state['run'],epoch=state['epoch'],boot=state['boot'],sourceSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='CLOSED_SHORT_CAPACITY_PLANNING_ONLY_NO_FRESHNESS_OR_SPEEDUP_WAIVER')
 target=E/'qa/duration-feasibility01.json'
 with target.open('x')as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps({'status':out['status'],'chosenRTF':metrics['chosenRTF'],'hostProjectionSeconds':out['hostProjectionSeconds'],'nativeProjectionSeconds':out['nativeProjectionSeconds']}))
if __name__=='__main__':main()
