#!/usr/bin/env python3
"""Bounded RAM-only all-retained R06 TAR/gzip size model, never an export."""
from pathlib import Path
import gzip,hashlib,io,json,os,stat,sys,tarfile,time
P=Path(__file__).resolve();R=P.parents[3];sys.path[:0]=[str(P.parent/'source'),str(R)]
from aeris_runtime.foundation.fdm09 import compact_line,decode_line,frame_capacity
from aeris_runtime.metadata_budget import encoded
from aeris_runtime.foundation.ap_stage09 import EVENT,packed_event,read_event,block_bytes,records
ROOT=R/'evidence/betasim-integrated01/r06';RUN='betasim-short06';EPOCH='66ad026a6f357729fa7cded0ecd3bf53'
class Counter:
 def __init__(self):self.bytes=0;self.hash=hashlib.sha256()
 def write(self,b):
  self.bytes+=len(b)
  if self.bytes>2**30:raise ValueError('MEASUREMENT_GZIP1G_BOUND')
  self.hash.update(b);return len(b)
 def flush(self):pass
class Converted:
 def __init__(self,path):self.file=path.open('rb');self.pending=b'';self.closed=False;self.state={}
 def read(self,n):
  if not 0<=n<=65536:raise ValueError('STREAM_READ64K')
  out=bytearray()
  while len(out)<n:
   if self.pending:
    take=min(n-len(out),len(self.pending));out.extend(self.pending[:take]);self.pending=self.pending[take:];continue
   line=self.file.readline(2049)
   if not line:break
   if len(line)>2048:raise ValueError('ORIGINAL_ROW2048')
   row=json.loads(line)['body'];self.pending=physical(row,line,self.state)
  return bytes(out)
 def close(self):self.file.close();self.closed=True
class APConverted:
 def __init__(self,path):self.file=path.open('rb');self.pending=self.file.readline(4097);self.prior=None
 def read(self,n):
  if not 0<=n<=65536:raise ValueError('STREAM_READ64K')
  out=bytearray()
  while len(out)<n:
   if self.pending:
    take=min(n-len(out),len(self.pending));out.extend(self.pending[:take]);self.pending=self.pending[take:];continue
   payload=bytearray();originals=bytearray();count=0
   for _ in range(128):
    raw=self.file.read(EVENT.size)
    if not raw:break
    if len(raw)!=EVENT.size:raise ValueError('AP_ORIGINAL_PARTIAL')
    payload.extend(packed_event(raw,self.prior));originals.extend(raw);self.prior=EVENT.unpack(raw);count+=1
   if not count:break
   self.pending=block_bytes(bytes(payload),count,bytes(originals))
  return bytes(out)
 def close(self):self.file.close()
def is_ap(p):return p.parent==ROOT/'sessions'/RUN/'raw/ap-stage'and p.name.startswith('stage-')and p.suffix=='.bin'
def is_main(p):return p.parent==ROOT/'sessions'/RUN/'raw/journal'and p.name.startswith('segment-')and p.suffix=='.jsonl'
def physical(body,line,state):
 payload=body['payload'];stage=body['kind']=='EVENT'and payload.get('eventKind')=='STAGE';sample=payload['data']['fields']['computeEndSinceOriginNs']if stage else None;absolute=stage and sample>=state.get('sceneNext',0);stored=compact_line(body,line,stage_state=state,force_absolute_stage=absolute)
 if absolute:state['sceneNext']=sample+50_000_000
 return stored
def group(path):
 if '/raw/journal/'in path:return'physics_PER_FRAME'
 if '/raw/ap-stage/'in path:return'AP-stage_PER_FRAME'
 if '/raw/clock-journal/'in path:return'clock_PER_SECOND'
 if '/raw/transport-journal/'in path:return'transport_PER_SECOND_AND_ACTIONS'
 if path.endswith('.tar'):return'native-TAR_FIXED_STARTUP'
 if '/android-api/'in path:return'native-observation_SETUP_AND_STATUS'
 if '/product/'in path:return'product_PREFIX_ACTIONS_AND_VIDEO'
 if path.startswith(('guardian/','metadata-budget/'))or'/resources/'in path:return'host-health_PER_SECOND'
 return'other_ROOT_SETUP_AND_DIAGNOSTICS'
def metadata():
 files=[];nonregular=[];total=0;head='0'*64;seq=0;main_original=main_compact=0;t=time.monotonic()
 for p in sorted(ROOT.rglob('*')):
  s=p.lstat()
  if stat.S_ISDIR(s.st_mode):continue
  if not stat.S_ISREG(s.st_mode):nonregular.append({'path':str(p.relative_to(ROOT)),'mode':stat.S_IFMT(s.st_mode)});continue
  if len(files)>=8192:raise ValueError('SOURCE_FILES8192')
  total+=s.st_size
  if total>16*2**30:raise ValueError('SOURCE16G')
  h=hashlib.sha256();converted=0;original_hash=hashlib.sha256()
  encode_state={};decode_state={}
  with p.open('rb')as f:
   if is_main(p):
    for line in f:
     if len(line)>2048:raise ValueError('MAIN_ROW_BOUND')
     q=json.loads(line);b=q['body'];raw=json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False).encode();assert b['run']==RUN and b['epoch']==EPOCH and b['seq']==seq and b['previous']==head and q['sha256']==hashlib.sha256(bytes.fromhex(head)+raw).hexdigest();import zlib;assert q['crc32']==format(zlib.crc32(raw),'08x');stored=physical(b,line,encode_state);assert decode_line(stored,RUN,EPOCH,head,stage_state=decode_state)==line;h.update(stored);original_hash.update(line);converted+=len(stored);head=q['sha256'];seq+=1
    main_original+=s.st_size;main_compact+=converted
   elif is_ap(p):
    header=f.readline(4097);h.update(header);original_hash.update(header);converted=len(header);prior=None
    while True:
     originals=[];payload=bytearray()
     for _ in range(128):
      raw=f.read(EVENT.size)
      if not raw:break
      if len(raw)!=EVENT.size:raise ValueError('AP_ORIGINAL_PARTIAL')
      payload.extend(packed_event(raw,prior));prior=EVENT.unpack(raw);originals.append(raw);original_hash.update(raw)
     if not originals:break
     stored=block_bytes(bytes(payload),len(originals),b"".join(originals));h.update(stored);converted+=len(stored)
     # Decoder state persists through blocks, but the first payload record of
     # this standalone proof may use the prior segment record. Verify manually
     # after complete source CRC, then exact bytes for every record.
     import zlib,struct
     from aeris_runtime.foundation.ap_stage09 import BLOCK
     if stored.startswith(b'APS9'):assert BLOCK.unpack(stored[:BLOCK.size])[3]==zlib.crc32(stored[:BLOCK.size-4]+stored[BLOCK.size:])&0xffffffff
     reader=io.BytesIO(stored[BLOCK.size:]if stored.startswith(b'APS9')else stored);cold_prior=None if len(originals)and EVENT.unpack(originals[0])[0]==json.loads(header)['startSequence']else cold_previous
     for original in originals:
      restored,wire=read_event(reader,cold_prior);assert restored==original;cold_prior=EVENT.unpack(restored)
     assert not reader.read(1);cold_previous=cold_prior
   else:
    for chunk in iter(lambda:f.read(65536),b''):h.update(chunk);original_hash.update(chunk)
    converted=s.st_size
  assert p.stat().st_size==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns
  files.append({'path':str(p.relative_to(ROOT)),'sourceBytes':s.st_size,'sourceSHA256':original_hash.hexdigest(),'virtualBytes':converted,'virtualSHA256':h.hexdigest(),'convertedMain':is_main(p),'convertedAPStage':is_ap(p)})
 return files,nonregular,{'mainOriginalBytes':main_original,'mainVirtualBytes':main_compact,'mainLogicalRowsByteExact':seq,'mainOriginalHead':head,'scanSeconds':time.monotonic()-t}
def tar_count(files,converted):
 sink=Counter();start=time.monotonic();groups={}
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0,compresslevel=6)as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.USTAR_FORMAT)as tar:
   for i,row in enumerate(files):
    source=ROOT/row['path'];info=tarfile.TarInfo('r06/file-%04d'%i);info.size=row['virtualBytes']if converted else row['sourceBytes'];info.mode=0o600;info.mtime=0;stream=Converted(source)if converted and row['convertedMain']else APConverted(source)if converted and row['convertedAPStage']else source.open('rb')
    category=group(row['path'])
    if category not in groups:
     counter=Counter();groups[category]={'counter':counter,'gz':gzip.GzipFile(filename='',mode='wb',fileobj=counter,mtime=0,compresslevel=6),'sourceBytes':0,'virtualBytes':0,'files':0}
    g=groups[category];g['files']+=1;g['sourceBytes']+=row['sourceBytes'];g['virtualBytes']+=info.size
    class Tee:
     def read(self,n):b=stream.read(n);g['gz'].write(b);return b
    try:tar.addfile(info,Tee())
    finally:stream.close()
 for g in groups.values():g['gz'].close()
 return {'bytes':sink.bytes,'sha256':sink.hash.hexdigest(),'seconds':time.monotonic()-start,'groupsStandaloneGzipNotAdditiveTARContributions':{k:{'gzipBytes':g['counter'].bytes,'files':g['files'],'sourceBytes':g['sourceBytes'],'virtualBytes':g['virtualBytes']}for k,g in groups.items()}}
def main():
 output=R/'evidence/betasim-integrated01/runtime/fdm09-r06-allfiles-size-model08.json';assert not output.exists();codec_paths=[P.parent/'source/aeris_runtime/foundation'/n for n in('fdm09.py','ap_stage09.py')];start_pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in codec_paths};files,other,m=metadata();original=tar_count(files,False);converted=tar_count(files,True);frames=103484;cases={}
 for seconds,max_segments,quota in[(180,64,402653184),(760,320,2013265920)]:
  n=seconds*1200;meta=max_segments*(2048+4096+8192)+4*2048+2*4096+16384;maximum=n*frame_capacity()['physicalMaximumBytesPerAcceptedFrame']+meta;projected=converted['bytes']*n/frames;fixed=sum(g['gzipBytes']for k,g in converted['groupsStandaloneGzipNotAdditiveTARContributions'].items()if'FIXED_STARTUP'in k or'ROOT_SETUP'in k);scoped=(converted['bytes']-fixed)*n/frames+fixed;cases[str(seconds)]={'maximumFrames':n,'mainMaximumFrameBytes':frame_capacity()['physicalMaximumBytesPerAcceptedFrame'],'mainMetadataAnd4KAllocationRoundingBoundBytes':meta,'mainHardUpperBoundBytes':maximum,'mainOriginalQuotaBytes':quota,'mainHardFits':maximum<=quota,'allRetainedR06ConservativeLinearProjectionBytes':projected,'fixedStartupAndRootDiagnosticsStandaloneGzipBytes':fixed,'scopedRateProjectionHoldingFixedStartupOnceBytes':scoped,'scopedRateStillUsesR06ObservedHostPerFrameRatio':True,'projectionIsNotCompressionBound':True,'HOSTExportCapBytes':192*2**20,'rawBundleMaximumBytes':168*2**20,'SAFJointCapBytes':192*2**20,'knownLinearProjectedOver192MiB':projected>192*2**20,'knownLinearProjectedOverRaw168MiB':projected>168*2**20}
 assert start_pins=={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in codec_paths}
 report={'sourcePins':start_pins,'sourceChangedDuringMeasurement':False,'format':'aeris-virtual-fdm09-all-R06-retained-TAR-gzip-size-model','status':'MEASUREMENT_NOT_AN_EXPORT_OR_ACCEPTANCE','sourceRoot':str(ROOT.relative_to(R)),'allRegularFilesCount':len(files),'allSourceBytes':sum(q['sourceBytes']for q in files),'originalSourceTableFields':['path','sourceBytes','sourceSHA256'],'allSourceOriginalsManifestSHA256':hashlib.sha256(encoded([{k:r[k]for k in('path','sourceBytes','sourceSHA256')}for r in files])).hexdigest(),'virtualTableSHA256':hashlib.sha256(encoded(files)).hexdigest(),'sourceFileTable':files,'nonRegularNamespaceEntriesNotArchiveFiles':other,'original':original,'virtualFDM09':converted,'main':m,'cases':cases,'oldSourceStageSchema':True,'currentStage09AdditionalTimingEntropy':'UNMEASURED_MUST_NOT_TREAT_OLD_SCHEMA_PROJECTION_AS_ACTUAL_NEW_STAGE_TRACE','R06MissingFuturePhases':['airborne_sensor_entropy','manual20Hz_signed_inputs','AUTO_motion','qualified_video_fullcase','final_SAF_receipts'],'stageObserverAbsoluteSelection':'R06_original_computeEnd_20Hz_checkpoints_reserved_before_encoding','nativeCurrentClosedTARUnavailableInR06':True,'nativePreinstallBackupIncludedIfRetained':True,'TARNames':'INDEXED_SIZING_NAMES_ONLY_NOT_ACTUAL_EXPORT_MANIFEST','oldSegmentSeals':'OLD_ORIGINALS_IN_SIZE_MODEL_NOT_VALID_FOR_CONVERTED_STREAMS_NO_CLOSED_ARCHIVE_CLAIM','APStageCodecSHA256':hashlib.sha256((P.parent/'source/aeris_runtime/foundation/ap_stage09.py').read_bytes()).hexdigest(),'codecSHA256':hashlib.sha256((P.parent/'source/aeris_runtime/foundation/fdm09.py').read_bytes()).hexdigest(),'archiveFilesWritten':0,'maximumStreamingReadBytes':65536,'maximumRestoreRowBytes':2048,'newActorsStarted':False};output.write_bytes(encoded(report));print(json.dumps({k:report[k]for k in('status','allRegularFilesCount','allSourceBytes','original','virtualFDM09','main','cases','archiveFilesWritten')}))
if __name__=='__main__':main()
