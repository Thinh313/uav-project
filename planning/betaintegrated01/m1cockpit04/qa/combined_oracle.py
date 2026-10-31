"""Distinct QA-only LOSS_DURING_ASSISTED_BRAKE_HOLD, declared before actual.

Pure fact qualification is not an actual30-minute certificate. Real caller must
bind every fact to complete externally anchored host/AP/native raw and restart.
Old held-forward-at-cut and nominal receipts are never rewritten.
"""
from pathlib import Path
import copy,itertools,math,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
NS=1_000_000_000;MIN=1800*NS
SCENARIO='LOSS_DURING_ASSISTED_BRAKE_HOLD'
BASE={'nativeNonforcedArmAnd3mTakeoffSent','armedObserved','airborneObserved','loiterObserved','forwardInputContinuous','manualMotionObserved','manualForwardDirectionObserved','threeMetreHoverObservedForOneSecond','landModeObserved','twoFreshIndependentGroundDisarmedPositionsAfterLand','freshWireBatteryAtLeast21VBeforeArm','qualifiedFullArmedGeographyReference','intentionalNativeOnlyCutObserved','airborneAndArmedAtCut','forwardHeldAtCut','GCSFailsafeTextAfterCut','GCSLandWithinDeclaredObservationWindow','noNativeLandCommandConfounder'}
def integer(x):return type(x)is int and x>=0

def assisted_window(rows,start,end):
 if not(integer(start)and integer(end)and end>=start):raise ValueError('WINDOW_SCHEMA')
 hb=land=None;last=-1;first=previous=None;boot_first=boot_last=None;positions=0;bad=[]
 for r in rows:
  now=r['hostNs']
  if not integer(now)or now<last:raise ValueError('TIMELINE_CLOCK')
  last=now;k=r['kind']
  if k=='heartbeat':hb=r
  if k=='landed':land=r
  if not start<=now<=end:continue
  if k=='heartbeat'and(not r['armed']or r['mode']!=17):bad.append('MODE_OR_ARMED_CONTRADICTION')
  if k=='landed'and r['state']!=2:bad.append('AIRBORNE_CONTRADICTION')
  if k!='position':continue
  valid=(hb is not None and land is not None and hb['armed']and hb['mode']==17 and land['state']==2 and 0<=now-hb['hostNs']<=1500_000_000 and 0<=now-land['hostNs']<=NS and 400<=r['relativeMm']<=5000)
  if not valid:bad.append('STALE_OR_UNQUALIFIED_POSITION')
  if previous is not None and now-previous>500_000_000:bad.append('POSITION_GAP')
  if boot_last is not None and r['bootMs']<boot_last:bad.append('AP_BOOT_REGRESSION')
  first=now if first is None else first;boot_first=r['bootMs']if boot_first is None else boot_first;boot_last=r['bootMs'];previous=now;positions+=1
 if first is None or first-start>500_000_000 or end-previous>500_000_000:bad.append('POSITION_EDGE_GAP')
 return dict(status='PASS'if not bad else'NOT_READY',failures=sorted(set(bad)),positions=positions,hostWindowNs=end-start,observedPositionSpanNs=0 if first is None else previous-first,APBootWindowNs=0 if boot_first is None else(boot_last-boot_first)*1_000_000)

def cleanup_witness(wire,tx_by_sha,heartbeats):
 commands=wire['nativeForwardedTimeline'];cut=wire['cutClosedHostNs'];ordinal={id(c):i for i,c in enumerate(commands)}
 def mode(c,v):return c['kind']=='SET_MODE'and c['mode']==v or c['kind']=='COMMAND_LONG'and c['command']==176 and c['params'][1]==v
 b=[c for c in commands if mode(c,17)];land=[c for c in commands if mode(c,9)or c['kind']=='COMMAND_LONG'and c['command']==21]
 brake_index=ordinal[id(b[0])]if len(b)==1 else None
 after=lambda c:brake_index is not None and ordinal[id(c)]>brake_index and c['hostNs']<=cut
 n=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['channels']==[1500]*4+[65535]*14 and after(c)]
 r=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['channels']==[0]*8+[65534]*10 and after(c)]
 held=[c for c in commands if c['kind']=='RC_OVERRIDE'and c['forwardPitchHeld']]
 checks={'oneBrakeNeutralReleaseNoUserLAND':len(b)==len(n)==len(r)==1 and not land,'noFailsafeBeforeCut':not any(s['kind']=='text'and s['hostNs']<cut and'failsafe'in s['text'].lower()for s in wire['passiveTimeline'])};w=[]
 if checks['oneBrakeNeutralReleaseNoUserLAND']:
  b,n,r=b[0],n[0],r[0];checks['forwardThenBrakeNeutralRelease']=bool(held)and ordinal[id(held[-1])]<ordinal[id(b)]<ordinal[id(n)]<ordinal[id(r)];checks['noOtherRCAfterBrake']=not any(c['kind']=='RC_OVERRIDE'and after(c)and c is not n and c is not r for c in commands)
  options=[tx_by_sha.get(c['wireSHA256'],[])for c in(b,n,r)]
  if any(len(o)>16 for o in options)or math.prod(map(len,options))>64:raise ValueError('NATIVE_WIRE_AMBIGUITY')
  for bt,nt,rt in itertools.product(*options):
   if not bt[0]<bt[2]<nt[0]<nt[2]<rt[0]<rt[2]:continue
   modes=[]
   for intent in(nt,rt):
    prior=[h for h in heartbeats if h['record']<intent[0]];latest=prior[-1]if prior else None
    if not(latest and latest['validType']and latest['armed']and latest['mode']==17 and bt[2]<latest['record']and 0<=intent[1]-latest['guestNs']<=1500_000_000):break
    modes.append(latest)
   if len(modes)==2:w.append(dict(brakeNativeIntent=bt[0],brakeNativeWritten=bt[2],neutralNativeIntent=nt[0],neutralNativeWritten=nt[2],releaseNativeIntent=rt[0],releaseNativeWritten=rt[2],latestCRCModeAtCleanup=modes))
 checks['uniqueObservedMode17BeforeBothCleanupIntents']=len(w)==1
 return dict(status='PASS'if all(checks.values())else'NOT_READY',criteria=checks,witness=w[0]if len(w)==1 else None)

def qualify_facts(base,wire,native,window,clocks,cleanup,*,restart):
 original=base['control']['criteria'];criteria={};missing=BASE-set(original)
 criteria['allBaseCriteriaPresent']=not missing
 # Preserve the original forwardHeldAtCut value; this new result is separate.
 criteria.update({'base:'+k:v is True for k,v in original.items()if k!='forwardHeldAtCut'})
 criteria['explicitlyAssistedNotForwardHeldAtCut']=original.get('forwardHeldAtCut')is False
 criteria['passiveApplicationTXZero']=type(wire['passiveApplicationTXBytes'])is int and wire['passiveApplicationTXBytes']==0
 criteria['assistedWindowFullyChecked']=window['status']=='PASS'
 durations={'host':window['hostWindowNs'],'APboot':window['APBootWindowNs'],'nativeElapsed':native.get('secondLeaseProducerWindowNs'),'nativeUptime':native.get('secondLeaseUptimeWindowNs'),'APguest':clocks.get('APGuestWindowNs'),'model':clocks.get('modelWindowNs')}
 for k,v in durations.items():criteria['continuous1800:'+k]=integer(v)and v>=MIN
 criteria['inputGapBound']=integer(native.get('maxLease2ProducerGapNs'))and native['maxLease2ProducerGapNs']<=200_000_000
 criteria['neutralLease2EntireWindow']=native.get('lease2NeutralThroughout')is True and native.get('neutralAtFailure')is True
 criteria['exactTwoExplicitDistinctLeases']=len(native['consents'])==2 and native['consents'][0]['event']['leaseId']!=native['consents'][1]['event']['leaseId']
 criteria['nativeNoWritesAfterObservedFailure']=type(native['postFailureTXIntents'])is int and native['postFailureTXIntents']==0 and native['authorityRestored']is False
 criteria['nativeFailureRetained']=native['terminal']['event']['reason']=='CONTROL_FAILED_RESOURCES_CLOSED'and bool(native['failures'])
 criteria['noPilotBindingsAfterUP']=native.get('pilotBindingsAfterFirstRelease')==0
 criteria['linkFailureCause']=bool(native['failures'])and all(any(t in x['event'].get('reason','')for t in('CONTROL_AP_EOF','Connection reset','Broken pipe','Socket closed'))for x in native['failures'])
 criteria['cleanupWitness']=cleanup['status']=='PASS';w=cleanup.get('witness');up=native['UP'];active=[x for x in native['revokes']if native['consents']and x['event']['previouslyActive']and x['event']['previousLeaseId']==native['consents'][0]['event']['leaseId']]
 criteria['UPRevokeCleanupDistinctConsentOrder']=bool(w and len(native['consents'])==2 and len(up)==1 and len(active)==1 and up[0]['record']<=active[0]['record']<w['brakeNativeIntent']and w['releaseNativeWritten']<native['consents'][1]['record'])
 lease2=native['consents'][1]['event']['leaseId']if len(native['consents'])==2 else None;criteria['noLease2RevocationBeforeFault']=lease2 is not None and not any(x['event'].get('previouslyActive')and x['event'].get('previousLeaseId')==lease2 for x in native['revokes'])
 criteria['restartExactNoAuthority']=restart.get('exactSHA')is True and restart.get('NO_SESSION')is True and restart.get('ownerActive')is False and restart.get('bindingStagedSHA256')is None and restart.get('newViewEpoch')is True
 return dict(status='COMBINED_FACTS_PASS_REQUIRES_ACTUAL_RAW_BINDING'if all(criteria.values())else'COMBINED_NOT_READY',scenario=SCENARIO,criteria=criteria,failed=[k for k,v in criteria.items()if not v],observedDurationsNs=durations,oldHeldForwardResultPreserved=dict(status=base['status'],forwardHeldAtCut=original.get('forwardHeldAtCut')),nativeFailedRecordPreserved=criteria['nativeFailureRetained'],actualThirtyMinuteAccepted=False,wholeBetaAccepted=False,scope='Pure combined-fact qualification. Only real complete externallyanchoredraw+power/guard+restart proofs can promote scenario, never synthetictimestamps/testcounts.')

def _journal_rows(journal):
 import json
 for p in sorted(Path(journal).glob('segment-*.jsonl')):
  with p.open('rb')as f:
   for line in f:yield json.loads(line)

def raw_clock_model_window(journal,start,end,context):
 """In-place stream. Complete model/AP/journal qualification is a separate prior gate."""
 return clock_model_window_rows(_journal_rows(journal),start,end,context)

def clock_model_window_rows(rows,start,end,context):
 """Same extractor on bounded iterable for actual-layout component tests, no runtime claim."""
 import struct,hashlib
 if not(integer(start) and integer(end) and end>=start):raise ValueError('DURATION_WINDOW_SCHEMA')
 origin=None;first_frame=last_frame=None;first_guest_send=last_guest_receive=None
 first_frame_host=last_frame_host=first_clock_host=last_clock_window_host=None
 matched=stages=0;last_clock_host=-1
 for row in rows:
  b=row['body']
  if b['kind']!='EVENT':continue
  event=b['payload'];k,d=event['eventKind'],event['data']
  if k=='TIMING_ORIGIN':
   if origin is not None:raise ValueError('DURATION_MULTIPLE_ORIGIN')
   origin=d['hostMonotonicNs']
   if not integer(origin):raise ValueError('DURATION_ORIGIN_SCHEMA')
  elif k=='STAGE':
   if origin is None:raise ValueError('DURATION_STAGE_WITHOUT_ORIGIN')
   fields=d['fields'];at=origin+fields['receiveSinceOriginNs']
   if start<=at<=end:
    frame=d['frame'];assert integer(frame) and fields['wireFrame']==frame
    if last_frame is not None:assert frame==last_frame+1
    if first_frame is None:first_frame=frame;first_frame_host=at
    last_frame=frame;last_frame_host=at;stages+=1
  elif k=='CLOCK' and d['kind']=='RESPONSE' and d['status']=='MATCHED':
   for key in('run','epoch','boot'):assert d[key]==context[key]
   at=d['hostReceiveNs'];assert integer(at) and at>=last_clock_host;last_clock_host=at
   raw=bytes.fromhex(d['rawHex']);assert len(raw)==56 and hashlib.sha256(raw).hexdigest()==d['rawSHA256']
   values=struct.unpack('<7Q',raw);assert values[1]==d['guestReceiveNs'] and values[2]==d['guestSendNs'] and values[1]<=values[2]
   if start<=at<=end:
    if first_guest_send is None:first_guest_send=values[2];first_clock_host=at
    last_guest_receive=values[1];last_clock_window_host=at;matched+=1
 if first_frame is None or first_guest_send is None:raise ValueError('DURATION_RAW_WINDOWS_EMPTY')
 if first_frame_host-start>500_000_000 or end-last_frame_host>500_000_000 or first_clock_host-start>500_000_000 or end-last_clock_window_host>500_000_000:raise ValueError('DURATION_RAW_ENDPOINT_GAP')
 return dict(modelWindowNs=(last_frame-first_frame)*NS//1200,APGuestWindowNs=last_guest_receive-first_guest_send,firstFrame=first_frame,lastFrame=last_frame,firstStageHostNs=first_frame_host,lastStageHostNs=last_frame_host,firstAPClockHostNs=first_clock_host,lastAPClockHostNs=last_clock_window_host,admittedStagesInWindow=stages,matchedAPGuestClockSamples=matched,source='ALL_QUALIFIED_STAGE_FRAME_IDS_AND_RAW56B_AP_CLOCK_IN_FIXED_HOST_WINDOW',notAClockMetadataAcceptance=True)
