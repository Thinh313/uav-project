"""Bounded local codec-only cost on deterministic held-out original R06 frames.
No actor, fsync, realtime, flight or freshness acceptance is inferred.
"""
from pathlib import Path
import hashlib,json,random,statistics,sys,time
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.fdm09 import logical,compact_line,decode_line
from aeris_runtime.foundation.ap_stage09 import EVENT,packed_event
from aeris_runtime.metadata_budget import encoded
ROOT=R/'evidence/betasim-integrated01/r06/sessions/betasim-short06/raw'
def distribution(a):return {'samples':len(a),'p50Ns':statistics.median(a),'p95Ns':sorted(a)[int(.95*(len(a)-1))],'maxNs':max(a),'totalNs':sum(a)}
def main():
 chosen=set(random.Random(1909).sample(range(103484),2048));frames={};aps={};source_paths=[T/'source/aeris_runtime/foundation'/x for x in('fdm09.py','ap_stage09.py')];pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths}
 for p in sorted((ROOT/'journal').glob('segment-*.jsonl')):
  with p.open('rb')as f:
   for raw in f:
    row=json.loads(raw)['body'];frame=row['frame']if row['kind']in('RX','INTENT','SENT')else row['payload']['data']['frame']if row['kind']=='EVENT'and row['payload'].get('eventKind')=='STAGE'else None
    if frame in chosen:frames.setdefault(frame,[]).append((row,raw))
 for p in sorted((ROOT/'ap-stage').glob('stage-*.bin')):
  with p.open('rb')as f:
   f.readline(4097)
   while True:
    raw=f.read(EVENT.size)
    if not raw:break
    assert len(raw)==EVENT.size;v=EVENT.unpack(raw)
    if v[1]in chosen:aps.setdefault(v[1],[]).append(raw)
 assert len(frames)==2048 and all(len(q)==4 for q in frames.values());baseline=[];encode=[];decode=[];ap=[];base_ap=[];state={};cold={};last_segment=None;input_digest=hashlib.sha256()
 for i,frame in enumerate(sorted(frames)):
  rows=frames[frame]
  if rows[0][0]['segment']!=last_segment:state.clear();cold.clear();last_segment=rows[0][0]['segment']
  t=time.perf_counter_ns()
  for row,raw in rows:assert logical(row)==raw
  baseline.append(time.perf_counter_ns()-t);t=time.perf_counter_ns();stored=[]
  for row,raw in rows:stored.append(compact_line(row,raw,stage_state=state,force_absolute_stage=i%60==0));input_digest.update(raw)
  encode.append(time.perf_counter_ns()-t);t=time.perf_counter_ns()
  for(row,raw),physical in zip(rows,stored):assert decode_line(physical,row['run'],row['epoch'],row['previous'],stage_state=cold)==raw
  decode.append(time.perf_counter_ns()-t);events=aps[frame];t=time.perf_counter_ns()
  for raw in events:EVENT.unpack(raw)
  base_ap.append(time.perf_counter_ns()-t);t=time.perf_counter_ns();prior=None
  for raw in events:packed_event(raw,prior);prior=EVENT.unpack(raw)
  ap.append(time.perf_counter_ns()-t)
 assert pins=={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths};out=R/'evidence/betasim-integrated01/runtime/codec09-local-cost02.json';assert not out.exists();report={'format':'aeris-codec09-source-local-cost','status':'LOCAL_CODEC_CPU_WALL_MEASUREMENT_NOT_RUNTIME_OR_FSYNC_ACCEPTANCE','sampleSeed':1909,'sampleOriginalFrames':2048,'sampleOriginalBytesSHA256':input_digest.hexdigest(),'sourcePins':pins,'baselineCanonicalMain':distribution(baseline),'newMainPhysicalEncodeIncludingCanonicalCheck':distribution(encode),'newMainColdDecode':distribution(decode),'baselineAPBinaryUnpack':distribution(base_ap),'newAPPhysicalEncode9IntegerFields':distribution(ap),'mainAndAPEncodeP95SumNs':distribution(encode)['p95Ns']+distribution(ap)['p95Ns'],'nominal1200HzOneFrameIntervalNs':1e9/1200,'actual1xPacingAndFreshness':'NOT_CHECKED_FILE_FSYNC_AND_SCHEDULER_NOT_IN_MEASUREMENT','worstSchema32FieldsPerformance':'NOT_MEASURED_HERE_SEPARATE_FUNCTIONAL_NEGATIVES','actorsStarted':False,'archiveFilesWritten':0};out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
