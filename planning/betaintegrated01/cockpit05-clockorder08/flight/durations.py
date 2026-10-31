"""Two original raw streams, no synthetic CLOCK rows or timestamp interpolation.
Call only after the selected main/AP/clock external-anchor receivers pass.
"""
from pathlib import Path
import hashlib,json,struct
NS=1_000_000_000

def integer(v):return type(v)is int and v>=0
def rows(path):
 for p in sorted(Path(path).glob('segment-*.jsonl')):
  with p.open('rb')as f:
   for line in f:yield json.loads(line)

def window_rows(main_rows,clock_rows,start,end,context):
 if not(integer(start)and integer(end)and end>=start):raise ValueError('DURATION_WINDOW_SCHEMA')
 origin=None;first_frame=last_frame=first_frame_host=last_frame_host=None;stages=0
 for row in main_rows:
  b=row['body']
  if b['kind']!='EVENT':continue
  event=b['payload'];k,d=event['eventKind'],event['data']
  if k=='TIMING_ORIGIN':
   if origin is not None or not integer(d.get('hostMonotonicNs')):raise ValueError('DURATION_TIMING_ORIGIN')
   origin=d['hostMonotonicNs']
  elif k=='STAGE':
   if origin is None:raise ValueError('DURATION_STAGE_WITHOUT_ORIGIN')
   fields=d['fields'];offset=fields['receiveSinceOriginNs'];frame=d['frame']
   if not integer(offset)or not integer(frame)or fields['wireFrame']!=frame:raise ValueError('DURATION_STAGE_FRAME_SCHEMA')
   at=origin+offset
   if start<=at<=end:
    if last_frame is not None and(frame!=last_frame+1 or at<last_frame_host):raise ValueError('DURATION_STAGE_GAP_OR_REGRESSION')
    if first_frame is None:first_frame,first_frame_host=frame,at
    last_frame,last_frame_host=frame,at;stages+=1
 first_guest_send=last_guest_receive=first_clock_host=last_clock_window_host=None;matched=0;last_clock_host=-1;last_guest=-1
 for row in clock_rows:
  b=row['body']
  if b['kind']!='EVENT':continue
  event=b['payload'];k,d=event['eventKind'],event['data']
  if k!='CLOCK'or d.get('kind')!='RESPONSE'or d.get('status')!='MATCHED':continue
  if any(d.get(key)!=context[key]for key in('run','epoch','boot')):raise ValueError('DURATION_CLOCK_CONTEXT')
  at=d.get('hostReceiveNs')
  if not integer(at)or at<last_clock_host:raise ValueError('DURATION_CLOCK_HOST_REGRESSION')
  last_clock_host=at;raw=bytes.fromhex(d['rawHex'])
  if len(raw)!=56 or hashlib.sha256(raw).hexdigest()!=d['rawSHA256']:raise ValueError('DURATION_CLOCK_RAW_SHA')
  values=struct.unpack('<7Q',raw)
  if values[1]!=d['guestReceiveNs']or values[2]!=d['guestSendNs']or values[1]>values[2]or values[1]<last_guest:raise ValueError('DURATION_CLOCK_GUEST_REGRESSION_OR_RAW')
  last_guest=values[2]
  if start<=at<=end:
   if first_guest_send is None:first_guest_send,first_clock_host=values[2],at
   last_guest_receive,last_clock_window_host=values[1],at;matched+=1
 if first_frame is None or first_guest_send is None:raise ValueError('DURATION_RAW_WINDOWS_EMPTY')
 if first_frame_host-start>500_000_000 or end-last_frame_host>500_000_000 or first_clock_host-start>500_000_000 or end-last_clock_window_host>500_000_000:raise ValueError('DURATION_RAW_ENDPOINT_GAP')
 if last_guest_receive<first_guest_send:raise ValueError('DURATION_AP_GUEST_WINDOW_NEGATIVE')
 return dict(modelWindowNs=(last_frame-first_frame)*NS//1200,APGuestWindowNs=last_guest_receive-first_guest_send,firstFrame=first_frame,lastFrame=last_frame,firstStageHostNs=first_frame_host,lastStageHostNs=last_frame_host,firstAPClockHostNs=first_clock_host,lastAPClockHostNs=last_clock_window_host,admittedStagesInWindow=stages,matchedAPGuestClockSamples=matched,source='QUALIFIED_MAIN_STAGE_FRAME_IDS_AND_SEPARATE_ORIGINAL_CLOCK_JOURNAL_RAW56B_RESPONSES',syntheticRows=0,notAClockMetadataAcceptance=True)

def raw_window(out,start,end,context):return window_rows(rows(Path(out)/'journal'),rows(Path(out)/'clock-journal'),start,end,context)
