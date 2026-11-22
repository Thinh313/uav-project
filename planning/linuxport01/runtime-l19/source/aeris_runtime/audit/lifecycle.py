"""Strict full proof blobs bound to original committed lifecycle journal rows."""
from pathlib import Path
import hashlib,json,re,stat,zlib
from .native_chain_json import strict_json
from pilot.betaintegrated01.runtime.ap_stage import canonical
CAP=8*2**20

def require(v,why):
 if not v:raise ValueError('LIFECYCLE_PROOF:'+why)
def allocated(root):
 total=0
 if not Path(root).exists():return 0
 for p in [Path(root),*Path(root).rglob('*')]:
  s=p.lstat();require(not stat.S_ISLNK(s.st_mode),'SYMLINK')
  if stat.S_ISREG(s.st_mode)or stat.S_ISDIR(s.st_mode):total+=s.st_blocks*512
 return total

def read_blob(root,ref,expected=None):
 require(type(ref)is dict and set(ref)=={'format','version','path','sha256','bytes'} and ref['format']=='aeris-lifecycle-proof-ref' and type(ref['version'])is int and ref['version']==1,'REF_SCHEMA')
 h=ref['sha256'];require(type(h)is str and re.fullmatch('[a-f0-9]{64}',h)is not None and ref['path']=='lifecycle-proofs/'+h+'.json' and type(ref['bytes'])is int and 0<ref['bytes']<=CAP,'REF_PATH_HASH_BOUND')
 p=Path(root)/ref['path'];s=p.lstat();require(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and s.st_size==ref['bytes'],'BLOB_REGULAR_EXACT_SIZE');raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==h,'BLOB_SHA');value=strict_json(raw);require(canonical(value)==raw,'BLOB_CANONICAL_BYTES')
 if expected is not None:
  require(type(value)is dict and set(value)==set(expected)|{'data'} and all(canonical(value[k])==canonical(v)for k,v in expected.items()),'ORIGINAL_FULL_PROOF_METADATA')
 return value

def verify_prefix(root,context,source,upto,expected_head):
 root=Path(root);require(type(upto)is int and upto>=0 and type(expected_head)is str and re.fullmatch('[a-f0-9]{64}',expected_head)is not None,'COMMITTED_PREFIX');total=allocated(root/'lifecycle')+allocated(root/'lifecycle-proofs');require(total<=CAP,'COMBINED8MiB')
 from ..lifecycle import NEXT,PHASES
 seq=-1;head='0'*64;proofs=[];sequence=0;last=-1;phase='CREATED';created=False;failed=False;closed_record=False
 for p in sorted((root/'lifecycle').glob('segment-*.jsonl')):
  with p.open('rb')as f:
   while seq<upto:
    line=f.readline(16385)
    if not line:break
    require(len(line)<=16384 and line.endswith(b'\n'),'ROW16KiB');row=strict_json(line);require(type(row)is dict and set(row)=={'body','crc32','sha256'},'ROW_SCHEMA');b=row['body'];raw=canonical(b);h=hashlib.sha256(bytes.fromhex(head)+raw).hexdigest();require(type(b.get('seq'))is int and b['seq']==seq+1 and b.get('previous')==head and b.get('run')==context['run']and b.get('epoch')==context['epoch'] and row['sha256']==h and row['crc32']==format(zlib.crc32(raw),'08x'),'ORIGINAL_CHAIN_CRC_CONTEXT');seq=b['seq'];head=h
    if b['kind']!='EVENT':
     require(b['kind']in('SEGMENT','CLOSE'),'LIFECYCLE_RECORD_KIND')
     if b['kind']=='CLOSE':require(created and phase in('CLOSED','FAILED') and not closed_record,'CLOSE_ONLY_AFTER_FINAL_PHASE');closed_record=True
     continue
    require(not closed_record,'EVENT_AFTER_JOURNAL_CLOSE')
    event=b['payload'];require(set(event)=={'eventKind','data'}and event['eventKind']=='MISSION_LIFECYCLE','MISSION_EVENT');v=event['data'];keys={'version','context','sourceSHA256','phase','lifecycleSequence','hostNs','kind','data','authorityMintedOrRenewed'};require(type(v)is dict and set(v)==keys and type(v['version'])is int and v['version']==1 and v['context']==context and v['sourceSHA256']==source and v['authorityMintedOrRenewed']is False,'COMPACT_CONTEXT');require(type(v['lifecycleSequence'])is int and v['lifecycleSequence']==sequence+1 and type(v['hostNs'])is int and v['hostNs']>=last,'LOGICAL_SEQUENCE_CLOCK');sequence=v['lifecycleSequence'];last=v['hostNs'];require(type(v['data'])is dict and set(v['data'])=={'proofBlob'},'COMPACT_PROOF_REF');expected={k:x for k,x in v.items()if k!='data'};blob=read_blob(root,v['data']['proofBlob'],expected)
    require(type(v['kind'])is str and v['phase']in PHASES and v['phase']==phase,'ORIGINAL_PHASE_MATCHES_REPLAY');kind=v['kind'];data=blob['data']
    if kind=='SESSION_CREATED':
     require(not created and sequence==1 and phase=='CREATED' and data=={},'CREATED_FIRST_ONCE');created=True
    else:
     require(created,'SESSION_CREATED_REQUIRED')
     if kind=='PHASE_COMMIT':
      require(not failed and phase not in('CLOSED','FAILED') and type(data)is dict and set(data)=={'from','to','proof'} and data['from']==phase and data['to']in NEXT.get(phase,set()) and type(data['proof'])is dict and bool(data['proof']),'EXISTING_NEXT_PHASE_PROOF');phase=data['to']
     elif kind=='SESSION_FAILED':
      require(not failed and phase!='CLOSED' and type(data)is dict and set(data)=={'reason','groundInferredFromProcessExit'} and type(data['reason'])is str and data['groundInferredFromProcessExit']is False,'FAILED_ONCE_NO_EXIT_GROUND');failed=True;phase='FAILED'
     elif kind=='INCIDENT':require(type(data)is dict and data.get('APEventHostNs')is None,'UNPROVEN_AP_EVENT_TIME_NOT_PROMOTED')
    proofs.append({'journalSequence':seq,'journalSHA256':head,'kind':v['kind'],'originalFullProofRef':v['data']['proofBlob']})
   if seq==upto:require(not f.read(1),'UNPUBLISHED_RAW_TAIL');break
 require(seq==upto and head==expected_head,'COMPLETE_EXPECTED_COMMITTED_PREFIX');names={x['originalFullProofRef']['path'].split('/')[-1]for x in proofs};actual={p.name for p in (root/'lifecycle-proofs').iterdir()if p.is_file()};require(actual==names,'ORPHAN_OR_PENDING_PROOF_NOT_NOMINAL')
 return {'status':'PASS_ORIGINAL_LIFECYCLE_PROOFS','proofs':proofs,'committedSequence':seq,'committedSHA256':head,'combinedAllocatedBytes':total,'finalPhase':phase,'failed':failed,'journalClosed':closed_record,'originalFullProofDataRetained':True,'journalBoundsIncreased':False}
