"""Cold streaming analysis of retained SIM-STABILITY03 captures. No runtime launch.

Only writes the explicit new evidence directory. Input copies, imports of old
helpers, native libraries, Docker/ADB/network, truncation and compaction are absent.
"""
from pathlib import Path
import collections,datetime,hashlib,json,math,os,struct,time,zlib,sys,re
R=Path(__file__).resolve().parents[4]
E=R/'evidence/betaintegrated01-m0/recorder'
REC=R/'.local/simstability03/receiver03'
RUNS=[('AP03','rd5d13f05d4c74563a9e2'),('AP04','rc8f9c0bfcc3a4563b492'),('AP05','rab0ab7870ac04d3bb8d8')]
WAL_HEAD=struct.Struct('<BBHIIQQ');AP_EVENT=struct.Struct('<QQIIQQQQq')
START=time.monotonic();MAX_SECONDS=180;MAX_STREAM_BYTES=4*2**30
read_bytes=0
def bounded():
 assert time.monotonic()-START<MAX_SECONDS,'COLD_ANALYSIS_DEADLINE'
 assert read_bytes<=MAX_STREAM_BYTES,'COLD_INPUT_BYTE_BUDGET'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def stat_id(p):
 s=p.stat();return {'bytes':s.st_size,'mtimeNs':str(s.st_mtime_ns),'inode':s.st_ino,'mode':s.st_mode}
def wal(p):
 global read_bytes
 chain=bytes(32);seq=0;kinds=collections.Counter();sizes=collections.Counter();maxsizes=collections.defaultdict(int);frames=0;previous=None;gaps=0;closed=0;phase='HEADER';error=None;digest=hashlib.sha256()
 with p.open('rb')as f:
  magic=f.read(8);digest.update(magic);read_bytes+=8;assert magic==b'AERISJ04'
  while True:
   bounded();head=f.read(28)
   if not head:break
   read_bytes+=len(head);digest.update(head)
   if len(head)!=28:error='TORN_HEADER';break
   kind,flags,reserved,frame,size,index,stamp=WAL_HEAD.unpack(head)
   if flags or reserved or index!=seq or size>16384:error='INVALID_HEADER';break
   body=f.read(size);tail=f.read(36);read_bytes+=len(body)+len(tail);digest.update(body);digest.update(tail)
   if len(body)!=size or len(tail)!=36:error='TORN_RECORD';break
   expected=hashlib.sha256(chain+head+body).digest()
   if tail[4:]!=expected or int.from_bytes(tail[:4],'little')!=zlib.crc32(head+body):error='CRC_OR_CHAIN';break
   chain=expected;seq+=1;kinds[kind]+=1;sizes[kind]+=size+64;maxsizes[kind]=max(maxsizes[kind],size)
   if kind==1:assert phase=='HEADER';phase='RX'
   elif kind==2:
    assert phase=='RX';gaps+=int(previous is not None and frame!=previous+1);previous=frame;phase='INTENT'
   elif kind==3:
    assert phase=='INTENT';n,snap=struct.unpack_from('<II',body);assert n+snap+8==size;phase='SENT'
   elif kind==4:assert phase=='SENT';frames+=1;phase='RX'
   elif kind==6:assert phase=='RX';closed+=1;phase='CLOSED'
   else:error='UNEXPECTED_KIND_'+str(kind);break
 assert digest.hexdigest()==sha(p),'WAL_CONTENT_CHANGED_DURING_COLD_ANALYSIS'
 return {'sha256':digest.hexdigest(),'records':seq,'kindCounts':dict(kinds),'recordBytesByKind':dict(sizes),'maxPayloadBytesByKind':dict(maxsizes),'frames':frames,'frameGaps':gaps,'closeRecords':closed,'phaseAtEOF':phase,'error':error,'headSHA256':chain.hex(),'completeHostCapture':error is None and closed==1 and phase=='CLOSED','physicalBytes':p.stat().st_size,'bytesPerAdmittedFrame':p.stat().st_size/frames}
def ap(p):
 global read_bytes
 counts=collections.Counter();group_counts=collections.Counter();frame=None;group=0;maxgroup=0;seqbad=0;first=None;last=None;minframe=None;maxframe=None;regressions=0;previous_frame=None;digest=hashlib.sha256()
 with p.open('rb')as f:
  header=f.read(4096);digest.update(header);read_bytes+=len(header);magic,cap,n,failed,size=struct.unpack('<8s4Q',header[:40]);assert magic==b'AERISD02'and size==64 and n<=cap
  left=n;expected_seq=0
  while left:
   bounded();take=min(4096,left);chunk=f.read(take*64);assert len(chunk)==take*64;read_bytes+=len(chunk);digest.update(chunk)
   for event in AP_EVENT.iter_unpack(chunk):
    seq,fr,kind,tid,begin,end,arg,extra,result=event;seqbad+=int(seq!=expected_seq);expected_seq+=1;counts[kind]+=1
    if first is None:first=begin
    last=end
    minframe=fr if minframe is None else min(minframe,fr);maxframe=fr if maxframe is None else max(maxframe,fr)
    if previous_frame is not None and fr<previous_frame:regressions+=1
    previous_frame=fr
    if frame is None or fr==frame:group+=1
    else:group_counts[group]+=1;maxgroup=max(maxgroup,group);group=1
    frame=fr
   left-=take
  if group:group_counts[group]+=1;maxgroup=max(maxgroup,group)
  tailzero=True
  for b in iter(lambda:f.read(1024*1024),b''):read_bytes+=len(b);digest.update(b);tailzero=tailzero and not any(b)
 assert digest.hexdigest()==sha(p),'AP_CONTENT_CHANGED_DURING_COLD_ANALYSIS'
 return {'sha256':digest.hexdigest(),'magic':magic.decode(),'capacityEvents':cap,'committedEvents':n,'failedFlag':failed,'eventBytes':size,'headerAreaBytes':4096,'logicalCommittedBytes':4096+n*size,'physicalBytes':p.stat().st_size,'capacityUsedFraction':n/cap,'kindCounts':dict(counts),'sequenceErrors':seqbad,'minFrame':minframe,'maxFrame':maxframe,'frameRegressions':regressions,'contiguousFrameGroupEventCountHistogram':dict(group_counts),'maxEventsInContiguousFrameGroup':maxgroup,'guestMonotonicSpanSeconds':(last-first)/1e9 if first is not None else None,'unusedTailAllZero':tailzero,'scope':'Header/committed event sequencing and grouped counts only; not full flight/required-stage acceptance'}
def stages(p):
 # Stored nested numeric arrays; bounded row buffers, never json.load whole file.
 global read_bytes
 count=0;depth=0;buf=bytearray();widths=collections.Counter();digest=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(65536),b''):
   bounded();read_bytes+=len(b);digest.update(b)
   for c in b:
    if c==91:
     depth+=1;assert depth<=2
     if depth==2:buf=bytearray(b'[')
    elif c==93:
     if depth==2:
      buf.append(c);row=json.loads(buf);assert all(type(v)is int for v in row);widths[len(row)]+=1;count+=1
     depth-=1;assert depth>=0
    elif depth==2:buf.append(c);assert len(buf)<=8192
 assert depth==0 and digest.hexdigest()==sha(p)
 return {'sha256':digest.hexdigest(),'rows':count,'rowWidthHistogram':dict(widths),'physicalBytes':p.stat().st_size,'bytesPerFrame':p.stat().st_size/count,'implementation':'Current backend accumulates all rows in a Python list until close; this analyzer does not.'}
def main():
 tag=sys.argv[1]if len(sys.argv)>1 else'01';assert re.fullmatch('[0-9]{2}',tag)
 E.mkdir(parents=True,exist_ok=True);observations=[]
 for label,rid in RUNS:
  p=REC/'evidence/simhand01/runs'/rid;before={n:stat_id(p/n)for n in ['ap-timing.bin','frames.wal','backend-stages.json','backend-result.json','closure.json','operator-review.json','launch.json','container-before-stop.json']}
  backend=json.loads((p/'backend-result.json').read_text());closure=json.loads((p/'closure.json').read_text());review=json.loads((p/'operator-review.json').read_text());launch=json.loads((p/'launch.json').read_text());w=wal(p/'frames.wal');a=ap(p/'ap-timing.bin');s=stages(p/'backend-stages.json');assert w['frames']==s['rows']==backend['frames']
  after={n:stat_id(p/n)for n in before};assert before==after
  c=json.loads((p/'container-before-stop.json').read_text());assert c['Id']==launch['containerId'];assert c['Config']['Labels']['aeris.run']==rid
  observations.append({'label':label,'run':rid,'beforeAfterStatUnchanged':True,'inputIdentity':before,'wal':w,'apTrace':a,'backendStages':s,'backendResult':backend,'runtimeClosure':closure,'containerBeforeStop':{'id':c['Id'],'state':c['State'],'metadataSHA256':sha(p/'container-before-stop.json')},'operatorReview':{'status':review['status'],'success':review['success'],'reason':review['reason']},'launchPins':{'apSHA256':launch['apSha256'],'imageID':launch['imageId'],'rateHz':launch['rateHz'],'speedup':launch['speedup'],'pacingCapUs':launch['negativeDebtCapUs']},'eventsPerAdmittedFrame':a['committedEvents']/w['frames'],'remainingCapacityAtNominal10EventsPerFrameSeconds':(a['capacityEvents']-a['committedEvents'])/(1200*10),'flightAcceptance':'NOT_INFERRED_FROM_THIS_SIZING_AUDIT'})
 sourceNames=['runtime/sim32-instrument01-build/ardupilot/libraries/SITL/SIM_StageTrace.cpp','runtime/sim32-instrument01-build/ardupilot/libraries/SITL/SIM_StageTrace.h','runtime/sim32-instrument01-build/ardupilot/libraries/SITL/SIM_JSON.cpp','runtime/sim32-instrument01-build/ardupilot/libraries/SITL/SIM_Aircraft.cpp','.local/simstability03/receiver03/pilot/simhand01/projection.py','.local/simstability03/receiver03/pilot/simhand01/server.mjs','.local/simstability03/receiver03/pilot/simhand01/guard.py','.local/simstability03/receiver03/pilot/simhand01/budget.mjs','.local/simstability03/receiver03/pilot/sim32-pipe03/clock_host.py','.local/simstability03/receiver03/pilot/sim32-journal04/wal_journal.py','.local/simstability03/receiver03/pilot/simtrain53/backend.py','.local/simstability03/receiver03/pilot/simtrain53/runtime.py','pilot/sim32-pipe03/stage_trace.py','planning/simstability03/media-ui-probe.py','planning/simstability03/full-manual-ui.py']
 pins={n:{'bytes':(R/n).stat().st_size,'sha256':sha(R/n)}for n in sourceNames}
 expected_capacity=(128*2**20-4096)//64;assert expected_capacity==2097088 and all(o['apTrace']['capacityEvents']==expected_capacity for o in observations)
 observed_max_wal_per_frame=max(o['wal']['bytesPerAdmittedFrame']for o in observations);observed_max_stage_per_frame=max(o['backendStages']['bytesPerFrame']for o in observations)
 sizing=[]
 for seconds in [1800,7200,28800,86400]:
  frames=1200*seconds
  walbytes=math.ceil(observed_max_wal_per_frame*frames);apbytes=4096+10*frames*64;stagebytes=math.ceil(observed_max_stage_per_frame*frames);video=2_000_000*seconds
  primary=walbytes+apbytes+stagebytes+video
  sizing.append({'durationSeconds':seconds,'framesAt1200Hz':frames,'walBytesEmpiricalMaxMeanAt1x':walbytes,'APTraceBytesNominal10EventsPerFrame':apbytes,'backendStageJSONBytesEmpiricalMaxMean':stagebytes,'videoBytesAssumption16MbitPerSecondAggregate':video,'primaryBytesSum':primary,'primaryGiB':primary/2**30,'originalPlusOneBackupPlusOneHandoffGiB':primary*3/2**30,'planningWith25PercentContingencyAnd256MiBReserveGiB':primary*3*1.25/2**30+.25,'WALShapeBoundWithMax16KiBPayloadPerRecordGiB':(8+(frames*3+2)*(16384+64))/2**30,'WALShapeBoundScope':'Fixed RX/INTENT/SENT plus HEADER/CLOSE only; no diagnostic/error extras. It is far more conservative than observed mean and is not the full artifact budget.','admissibleWithCurrent128MiBAPTrace':False,'scope':'EXTRAPOLATED_PLANNING_ONLY_NOT_MEASURED_LONG_RUN; observed mean byte rates are not formal upper bounds; nominal AP10events/frame excludes extra retransmit paths; video bitrate is an assumption; metadata/encoder/guest logs need additional explicit allowance.'})
 report={'format':'aeris-betaintegrated01-m0-recorder-cold-analysis','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'COLD_CAPACITY_AND_PRESERVATION_CHECKS_PASS_PRODUCT_NOT_READY','observations':observations,'sourcePins':pins,'fixedTraceLayout':{'capacityBytes':128*2**20,'headerAreaBytes':4096,'eventBytes':64,'capacityEvents':expected_capacity,'overflowBehavior':'failed=1;_exit(94)','nominalEventsPerFrame':{'withoutPacerSleep':8,'withPacerSleep':10},'capacitySecondsAt1200HzAnd8Events':expected_capacity/8/1200,'capacitySecondsAt1200HzAnd10Events':expected_capacity/10/1200,'current300sMinimumEventStorageMiB':(4096+300*1200*8*64)/2**20,'storageMiBFor300sAt10Events':(4096+300*1200*10*64)/2**20},'additionalLongRunBlockers':[{'id':'REC02','finding':'Clock Correlator.requests never evicts matched/timeout entries;limit1024;newrequest every333333333ns','nominalFailureAfterSeconds':1024/3,'source':'clock_host.py Correlator.register/ClockObserver.work','requiredAction':'Bound pending requests and bounded replay/tombstone window, stream completed rows, preserve duplicate/late/unknown classifications; bounded versioned clock protocol may roll correlation batches without resetting flight/clock epochs.'},{'id':'REC03','finding':'backend stages is an all-flight Python list serialized to JSON atclose','requiredAction':'Stream fixed-format sequenced stage chunks; do not retain full-session rows in RAM; same fields/clock/closure oracle.'},{'id':'REC04','finding':'WAL fixed768MiB under projection; recipient evidence2GiB,AP300s,host90min','requiredAction':'New explicit beta manifest/policy with admitted requested duration/capacity; do not edit old policy/pins or silently raise guards.'},{'id':'REC05','finding':'traceflush uses docker exec after AP process exits; both full-trace AP03/AP05 fail closure even with host CAPTURE_CLOSED WAL','requiredAction':'Keep parent-owned independent flush/drain observer alive until APclose; classify instrumentation failure before container disappears. Never infer accepted flight from host WAL CLOSE.'},{'id':'REC06','finding':'Legacy StageTrace binary mmap is fixed16MiB/88-byte rows (~158.84s at1200Hz)','requiredAction':'Adapt format semantics only, not fixed capacity or drop policy.'}],'sizing':sizing,'empiricalSizingInputs':{'maxObservedWalBytesPerFrame':observed_max_wal_per_frame,'maxObservedStageJSONBytesPerFrame':observed_max_stage_per_frame,'nominalFrameRateHz':1200,'videoAggregateMbpsAssumption':16,'copiesPlanningAssumption':3,'contingencyAssumption':.25,'reserveGiB':.25},'currentPolicyInvariant':{'admissionGiB':20,'floorGiB':10,'reserveMiB':256,'forecastSeconds':15,'fsyncBeforeSensor':True,'speedup':1,'pacingCapMs':500,'frameDrop':False,'automaticEvidenceDeletion':False},'retainedOldFailures':True,'runtimeStarted':False,'nativeOrAPBuildPerformed':False,'sourceMutated':False,'analysisInputBytesStreamed':read_bytes,'elapsedSeconds':time.monotonic()-START,'scriptSHA256':sha(Path(__file__)),'limitations':['No actual30min/2h/8h/24h test or compression benchmark performed.','No claim of physical power-loss survival from fsync alone.','No actual AP required-stage acceptance beyond retained earlier AP04 audit.','APsource may require single-writer/thread audit before segmented recorder implementation; emit currently uses load/write/store, not multi-writer reservation.']}
 report['priorAnalysis01Note']='Initial01 retained; final02 additionally pins exact retained container94 exits and includes HEADER/CLOSE in conservative WAL shape accounting.'
 (E/('cold-analysis'+tag+'.json')).open('x').write(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'runs':[{'label':o['label'],'frames':o['wal']['frames'],'APevents':o['apTrace']['committedEvents'],'APfailed':o['apTrace']['failedFlag'],'review':o['operatorReview']['status'],'WalBytesPerFrame':o['wal']['bytesPerAdmittedFrame']}for o in observations],'sizingPrimaryGiB':{str(s['durationSeconds']):s['primaryGiB']for s in sizing},'elapsedSeconds':report['elapsedSeconds']},indent=2))
if __name__=='__main__':main()
