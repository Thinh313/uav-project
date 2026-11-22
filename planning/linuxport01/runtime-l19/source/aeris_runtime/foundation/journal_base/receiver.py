"""Cold streaming decoder implemented separately from writer serialization helpers.

This validates recording bytes/chronology, not flight execution, signer identity,
hardware durability after power loss or complete AP-stage capture.
"""
from pathlib import Path
import json,os,stat,hashlib,zlib,base64,re

class VerificationError(ValueError):pass
def require(ok,reason):
    if not ok:raise VerificationError(reason)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def number(n):return type(n)is int and 0<=n<2**63
def raw_small(path,bound=16384):
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and s.st_size<=bound,'METADATA_TYPE_OR_BOUND')
        with os.fdopen(fd,'rb',closefd=False)as f:b=f.read(bound+1)
        require(len(b)<=bound,'METADATA_TYPE_OR_BOUND')
    finally:os.close(fd)
    return b
def read_small(path,bound=16384):
    b=raw_small(path,bound)
    try:return load(b)
    except Exception as e:raise VerificationError('METADATA_JSON')from e
def no_duplicate(pairs):
    out={}
    for k,v in pairs:
        require(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
    return out
def load(b):
    try:return json.loads(b,object_pairs_hook=no_duplicate,parse_constant=lambda x:(_ for _ in ()).throw(VerificationError('NONFINITE_JSON')))
    except VerificationError:raise
    except Exception as e:raise VerificationError('JSON_ENCODING')from e

def verify_journal(root,expected_run,expected_epoch,expected_commit=None,*,expected_physical_codec=None):
    root=Path(os.path.abspath(root))
    for p in [root,*root.parents]:require(not p.is_symlink(),'SYMLINK_ROOT')
    require(root.is_dir(),'ROOT_DIRECTORY')
    require(type(expected_run)is str and type(expected_epoch)is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',expected_run)and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',expected_epoch),'EXPECTED_CONTEXT_ID')
    from ..fdm09 import CODEC,decode_line
    require(expected_physical_codec in(None,CODEC),'EXPLICIT_MAIN_CODEC_ONLY');manifest=read_small(root/'manifest.json');coded=expected_physical_codec==CODEC;require(not coded or root.name=='journal','FDM09_MAIN_JOURNAL_NAMESPACE_ONLY');require(type(manifest)is dict and (manifest.get('physicalCodec')==CODEC if coded else'physicalCodec'not in manifest)and set(manifest)==({'format','version','run','epoch','policy','scope','diskGuardPolicy','diskGuardPriming'}|({'physicalCodec'}if coded else set()))and manifest['format']=='aeris-beta-journal-runtime02'and type(manifest['version'])is int and manifest['version']==2 and manifest['scope']=='HOST_RECORDING_FOUNDATION_NOT_AP_STAGE_OR_FLIGHT_ACCEPTANCE','MANIFEST_FORMAT')
    require(manifest['run']==expected_run and manifest['epoch']==expected_epoch,'FOREIGN_CONTEXT')
    gp=manifest['diskGuardPolicy'];require(type(gp)is dict and canonical(gp)==canonical({'version':2,'entryBytes':10*2**30,'floorBytes':10*2**30,'reserveBytes':256*2**20,'horizonNs':15000000000,'samplePeriodNs':100000000,'maximumCheckGapNs':2000000000,'maximumSamples':192,'requiresRealPriming':True,'sampling':'CADENCE_CAPPED_KEEP_WINDOW_BOUNDARY_PREDECESSOR','perWriteFloorAndForecast':True}),'DISK_GUARD_POLICY')
    priming=manifest['diskGuardPriming'];require(type(priming)is dict and type(priming.get('elapsedRealMonotonicNs'))is int and priming['elapsedRealMonotonicNs']>=15000000000 and type(priming.get('historySpanNs'))is int and priming['historySpanNs']>=15000000000 and priming.get('primed')is True and priming.get('source')=='ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED'and type(priming.get('sampleCount'))is int and 2<=priming['sampleCount']<=192,'DISK_GUARD_PRIMING_SCHEMA')
    pol=manifest['policy'];require(type(pol)is dict and set(pol)=={'segment_bytes','quota_bytes','max_record_bytes','max_segments','termination_reserve_bytes'}and all(number(v)and v>0 for v in pol.values()),'POLICY_SCHEMA')
    require(1024<=pol['max_record_bytes']<=65536 and 1<=pol['max_segments']<=4096 and pol['segment_bytes']>=4*pol['max_record_bytes']+4096 and pol['termination_reserve_bytes']>=8192 and pol['quota_bytes']>=pol['segment_bytes']+pol['termination_reserve_bytes'],'POLICY_BOUND')
    names=[]
    with os.scandir(root)as it:
        for p in it:
            require(len(names)<2*pol['max_segments']+3,'DIRECTORY_ENTRY_BOUND');require(p.is_file(follow_symlinks=False),'UNEXPECTED_PATH_TYPE');s=p.stat(follow_symlinks=False);require(s.st_nlink==1,'HARDLINK_NOT_ALLOWED');names.append(p.name)
    allowed=lambda n:n in ['manifest.json','session.json','failure.json']or re.fullmatch(r'segment-[0-9]{6}\.(?:jsonl|seal\.json)',n)
    require(all(allowed(n)for n in names),'UNLISTED_PATH')
    indices=sorted(int(n[8:14])for n in names if re.fullmatch(r'segment-[0-9]{6}\.jsonl',n));require(indices==list(range(len(indices)))and len(indices)<=pol['max_segments'],'SEGMENT_ORDER_OR_MISSING')
    require(sum((root/n).stat().st_size for n in names)<=pol['quota_bytes'],'TOTAL_QUOTA')
    session=read_small(root/'session.json')if'session.json'in names else None
    failure=read_small(root/'failure.json')if'failure.json'in names else None
    if failure:require(failure.get('run')==expected_run and failure.get('epoch')==expected_epoch and failure.get('complete')is False,'FAILURE_CONTEXT')
    if session:require(session.get('segments')==len(indices),'SESSION_SEGMENT_COUNT')
    sequence=0;head='0'*64;previousFile='0'*64;frame=0;phase='BETWEEN';close_seen=False;rx_seen=0;intents=0;sent=0;unknown=0;events=0;tail=False;unsealed=False;stageRows=0;summary={};seal_shas=[]
    for ordinal in indices:
        name='segment-%06d.jsonl'%ordinal;p=root/name;s=p.stat();require(s.st_size<=pol['segment_bytes'],'SEGMENT_BYTE_BOUND');sealed=name[:-6]+'.seal.json'in names
        require(not unsealed,'UNSEALED_NONFINAL_SEGMENT')
        fileHash=hashlib.sha256();first=sequence;lines=0;codec_state={}
        with os.fdopen(os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)),'rb')as f:
            opened=os.fstat(f.fileno());require(stat.S_ISREG(opened.st_mode)and opened.st_nlink==1 and opened.st_size==s.st_size and (opened.st_dev,opened.st_ino)==(s.st_dev,s.st_ino),'SEGMENT_OPEN_CHANGED')
            while True:
                line=f.readline(pol['max_record_bytes']+1)
                if not line:break
                require(len(line)<=pol['max_record_bytes'],'RECORD_SIZE_BOUND')
                fileHash.update(line)
                if not line.endswith(b'\n'):
                    require(not sealed and ordinal==indices[-1],'TRUNCATED_SEALED_RECORD');tail=True;break
                if coded:
                    line=decode_line(line,expected_run,expected_epoch,head,stage_state=codec_state);require(len(line)<=pol['max_record_bytes'],'DECODED_RECORD_BOUND')
                row=load(line);require(type(row)is dict and set(row)=={'body','crc32','sha256'},'ENVELOPE_SCHEMA');b=row['body'];require(type(b)is dict and set(b)=={'v','run','epoch','segment','seq','previous','kind','frame','payload'},'BODY_SCHEMA')
                raw=canonical(b);require(b['v']==2 and b['run']==expected_run and b['epoch']==expected_epoch and b['segment']==ordinal and b['seq']==sequence and b['previous']==head,'CONTEXT_OR_SEQUENCE')
                require(type(b['v'])is int and b['v']==2 and number(b['segment'])and number(b['seq']),'NUMERIC_SCHEMA')
                require(row['crc32']==format(zlib.crc32(raw),'08x')and row['sha256']==hashlib.sha256(bytes.fromhex(head)+raw).hexdigest(),'CRC_OR_CHAIN')
                require(not close_seen,'APPEND_AFTER_CLOSE');kind=b['kind'];payload=b['payload'];require(type(payload)is dict,'PAYLOAD_SCHEMA')
                if lines==0:
                    require(kind=='SEGMENT'and b['frame']is None and phase=='BETWEEN'and canonical(payload)==canonical({'ordinal':ordinal,'startSequence':sequence,'previousSegmentSHA256':previousFile}),'SEGMENT_HEADER')
                elif kind=='RX':
                    require(phase=='BETWEEN'and number(b['frame'])and b['frame']==frame and set(payload)=={'base64'},'RX_ORDER')
                    try:base64.b64decode(payload['base64'],validate=True)
                    except Exception as e:raise VerificationError('RX_BASE64')from e
                    phase='RX';rx_seen+=1
                elif kind=='INTENT':
                    require(phase=='RX'and number(b['frame'])and b['frame']==frame and set(payload)=={'base64'},'INTENT_ORDER')
                    try:intent=base64.b64decode(payload['base64'],validate=True)
                    except Exception as e:raise VerificationError('INTENT_BASE64')from e
                    phase='INTENT';intents+=1
                elif kind=='SENT':
                    require(phase=='INTENT'and number(b['frame'])and b['frame']==frame and canonical(payload)==canonical({'returnedBytes':len(intent),'expectedBytes':len(intent),'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'}),'SENT_ORDER_OR_LENGTH');sent+=1;frame+=1;phase='BETWEEN'
                elif kind=='UNKNOWN':
                    require(phase=='INTENT'and number(b['frame'])and b['frame']==frame and payload.get('sendCalled')is True,'UNKNOWN_ORDER');unknown+=1;phase='UNKNOWN'
                elif kind=='EVENT':
                    require(phase=='BETWEEN'and b['frame']is None and set(payload)=={'eventKind','data'}and type(payload['eventKind'])is str and 1<=len(payload['eventKind'])<=48,'EVENT_ORDER');events+=1
                    if payload['eventKind']=='STAGE':
                        d=payload['data'];require(type(d)is dict and set(d)=={'frame','fields'}and number(d['frame'])and d['frame']<frame and type(d['fields'])is dict and len(d['fields'])<=32,'STAGE_SCHEMA');require(len(set(summary)|set(d['fields']))<=32,'STAGE_FIELDS_BOUND')
                        for k,v in d['fields'].items():
                            require(type(k)is str and 1<=len(k)<=48 and number(v),'STAGE_VALUE');z=summary.setdefault(k,{'count':0,'sum':0,'max':0});z['count']+=1;z['sum']+=v;z['max']=max(z['max'],v);require(number(z['sum'])and number(z['count']),'STAGE_AGGREGATE_BOUND')
                        stageRows+=1
                elif kind=='CLOSE':require(phase=='BETWEEN'and b['frame']is None and canonical(payload)==canonical({'completedFrames':frame,'scope':'RECORDING_ONLY_NOT_FLIGHT'}),'CLOSE_SCOPE');close_seen=True
                else:raise VerificationError('KIND_OR_HEADER_ORDER')
                head=row['sha256'];sequence+=1;lines+=1
        require(lines>0 or not sealed,'EMPTY_SEALED_SEGMENT')
        if sealed:
            seal=read_small(root/(name[:-6]+'.seal.json'));state='SESSION_CLOSED'if close_seen else'ROTATED'
            expected={'version':2,'run':expected_run,'epoch':expected_epoch,'segment':ordinal,'startSequence':first,'endSequence':sequence-1,'fileBytes':s.st_size,'fileSHA256':fileHash.hexdigest(),'head':head,'previousSegmentSHA256':previousFile,'state':state}
            require(canonical(seal)==canonical(expected)and phase=='BETWEEN','SEGMENT_SEAL');previousFile=seal['fileSHA256']
            seal_shas.append(hashlib.sha256(raw_small(root/(name[:-6]+'.seal.json'))).hexdigest())
        else:unsealed=True
    for n in names:
        if n.endswith('.seal.json'):require(int(n[8:14])in indices,'ORPHAN_SEAL')
    complete=bool(session is not None and failure is None and close_seen and not unsealed and not tail and phase=='BETWEEN')
    if session:
        expected={'version':2,'run':expected_run,'epoch':expected_epoch,'segments':len(indices),'records':sequence,'head':head,'lastSegmentSHA256':previousFile,'frames':frame,'state':'COMPLETE_RECORDING','APExecutionAccepted':False}
        require(canonical(session)==canonical(expected),'SESSION_RECEIPT')
    anchored=False
    if expected_commit is not None:
        require(complete,'ANCHOR_REQUIRES_COMPLETE_BYTES')
        anchor={'version':1,'run':expected_run,'epoch':expected_epoch,'manifestSHA256':hashlib.sha256(raw_small(root/'manifest.json')).hexdigest(),'sessionSHA256':hashlib.sha256(raw_small(root/'session.json')).hexdigest(),'sealSHA256':seal_shas,'head':head}
        require(canonical(expected_commit)==canonical(anchor),'EXTERNAL_COMMIT_ANCHOR_MISMATCH');anchored=True
    return {'state':('COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'if anchored else'COMPLETE_BYTES_UNATTESTED')if complete else'INCOMPLETE_RECORDING','byteSequenceComplete':complete,'run':expected_run,'epoch':expected_epoch,'segments':len(indices),'records':sequence,'frames':frame,'receivedFrames':rx_seen,'intents':intents,'localSends':sent,'unknownSends':unknown,'events':events,'stageRows':stageRows,'stageSummary':summary,'pendingPhase':phase,'partialTail':tail,'failureMarker':failure is not None,'head':head,'APExecutionAccepted':False,'writerCommitAttested':anchored,'publicationAllowed':False,'durability':'EXTERNAL_ANCHOR_MATCH_NOT_SOURCE_AUTH_OR_POWERLOSS_PROOF'if anchored else'UNATTESTED_BY_COLD_BYTES','scope':'BYTE_SEQUENCE_AND_RECORDING_COMPLETENESS_ONLY_NOT_ACTUAL_SENSOR_SEND_OR_FLIGHT_PROOF'}
