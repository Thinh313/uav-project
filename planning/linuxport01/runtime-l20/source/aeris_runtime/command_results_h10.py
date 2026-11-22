"""One exact original-result reader for every Root management command consumer.
No retry, no write or command authority. Pending/forged/duplicate refs fail closed.
"""
from pathlib import Path
import hashlib,json,os,stat,math
ACTIONS={'NATIVE_READY','NATIVE_ROLLOVER','SEAL_PRODUCT','VERIFY_NATIVE_INPUTS','VERIFY_NATIVE_UNUSED17','PREPARE_RAW_EXPORT','STATUS'}
def need(v,n):
 if not v:raise ValueError('COMMAND_RESULT_H10_'+n)
def unique(items):
 out={}
 for k,v in items:need(k not in out,'DUPLICATE_JSON_FIELD');out[k]=v
 return out
def number(raw):
 v=float(raw);need(math.isfinite(v),'FINITE_JSON_NUMBER');return v
def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_float=number,parse_constant=lambda s:(_ for _ in()).throw(ValueError('COMMAND_RESULT_H10_JSON_CONSTANT')))
def original(root,relative,maximum,expected_bytes=None):
 root=Path(root);need(type(relative)is str and not Path(relative).is_absolute()and all(x not in('','.','..')for x in relative.split('/'))and'\\'not in relative,'RELATIVE_PATH');path=root/relative;need(not any(p.is_symlink()for p in[path,*path.parents]),'NO_SYMLINK')
 descriptors=[]
 try:
  fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);descriptors.append(fd)
  for n in Path(relative).parts[:-1]:fd=os.open(n,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);descriptors.append(fd)
  fd=os.open(Path(relative).name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd);descriptors.append(fd);before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and 0<before.st_size<=maximum and(expected_bytes is None or before.st_size==expected_bytes),'COMPLETE_FILE_SIZE');parts=[];remaining=before.st_size
  while remaining:
   b=os.read(fd,min(65536,remaining));need(bool(b),'TRUNCATED_FILE');parts.append(b);remaining-=len(b)
  need(os.read(fd,1)==b''and os.fstat(fd).st_size==before.st_size,'GROWING_OR_EXTRA_FILE');return b''.join(parts)
 finally:
  for fd in reversed(descriptors):os.close(fd)
def read_command_progress(owner,row,progress_raw):
 c=owner.case;need(type(row)is dict and type(row.get('version'))is int and row['version']==1 and row.get('kind')=='COMMAND_COMPLETE'and type(row.get('pid'))is int and row['pid']==c['companion'].process.pid and row.get('run')==c['context']['run']and row.get('flightAcceptance')is False,'ORIGINAL_PROGRESS_BINDING');need(type(progress_raw)is bytes and 0<len(progress_raw)<=2**20 and progress_raw.endswith(b'\n'),'PROGRESS1MiB');seen=[];matched=0
 for line in progress_raw.splitlines():
  need(0<len(line)+1<=4096,'PROGRESS4KiB');v=decode(line);need(type(v)is dict and type(v.get('version'))is int and v['version']==1 and type(v.get('pid'))is int and v['pid']==c['companion'].process.pid and v.get('run')==c['context']['run']and v.get('flightAcceptance')is False,'ALL_PROGRESS_OWNED_BINDING')
  if v.get('kind')=='COMMAND_COMPLETE':
   data=v.get('data');need(type(data)is dict and set(data)=={'sequence','action','resultRef'}and type(data['sequence'])is int and data['sequence']==len(seen)+1 and data['action']in ACTIONS,'CONTIGUOUS_UNIQUE_COMMAND_ACK');seen.append(data['sequence'])
   if v==row:matched+=1
 need(matched==1,'ORIGINAL_ACK_ONCE');data=row['data'];n=data['sequence'];action=data['action'];need(type(n)is int and 1<=n<=16 and action in ACTIONS,'FINITE_COMMAND');request_path='reports/companion-control-'+c['context']['run']+'.jsonl';requests=original(owner.root,request_path,32768);need(requests.endswith(b'\n'),'REQUEST_COMPLETE');rows=[decode(x)for x in requests.splitlines()];need(len(rows)<=16 and all(type(q)is dict and type(q.get('sequence'))is int and q['sequence']==i for i,q in enumerate(rows,1))and n<=len(rows),'ORIGINAL_REQUEST_SEQUENCE');q=rows[n-1];need(type(q.get('ownerPID'))is int and q=={'sequence':n,'ownerPID':os.getpid(),'run':c['context']['run'],'candidateSHA256':owner.digest,'action':action},'ORIGINAL_REQUEST_BINDING');ref=data['resultRef'];need(type(ref)is dict and set(ref)=={'format','version','path','bytes','sha256','finalWriteRef'}and ref['format']=='aeris-command-result-original-ref'and type(ref['version'])is int and ref['version']==1 and type(ref['bytes'])is int and 0<ref['bytes']<=2**20,'REFERENCE_SCHEMA');name='reports/command-result-%02d-%s.json'%(n,action);expected='sessions/'+c['context']['run']+'/product/'+name;need(ref['path']==expected,'EXACT_CURRENT_CASE_PATH');raw=original(owner.root,expected,2**20,ref['bytes']);digest=hashlib.sha256(raw).hexdigest();need(digest==ref['sha256']and raw.endswith(b'\n'),'FULL_RESULT_SHA_OR_FRAMING');last=ref['finalWriteRef'];offset=((len(raw)-1)//65536)*65536;part=raw[offset:];need(type(last)is dict and set(last)=={'path','offset','bytes','sha256','writeSequence'}and last['path']==expected and type(last['offset'])is int and last['offset']==offset and type(last['bytes'])is int and last['bytes']==len(part)and last['sha256']==hashlib.sha256(part).hexdigest()and type(last['writeSequence'])is int and last['writeSequence']>0,'FINAL_ORIGINAL_COMMIT');committed=c['writer'].committed_files.get(name);need(type(committed)is dict and committed=={'bytes':len(raw),'writeSequence':last['writeSequence']},'CURRENT_OWNER_COMMITTED_FILE');v=decode(raw);need(type(v)is dict and set(v)=={'format','version','context','run','candidateSHA256','ownerPID','companionPID','sequence','action','result','authorityRestorable','flightAcceptance'}and v['format']=='aeris-command-result-h10'and type(v['version'])is int and v['version']==1 and v['context']==c['context']and v['run']==c['context']['run']and v['candidateSHA256']==owner.digest and type(v['ownerPID'])is int and v['ownerPID']==os.getpid()and type(v['companionPID'])is int and v['companionPID']==c['companion'].process.pid and type(v['sequence'])is int and v['sequence']==n and v['action']==action and v['authorityRestorable']is False and v['flightAcceptance']is False,'ENVELOPE_IDENTITY');consumed=c.setdefault('commandResultsH10',{});need(n not in consumed,'NO_DUPLICATE_RESULT_CONSUMPTION');consumed[n]={'sha256':digest,'bytes':len(raw),'action':action};return{**row,'data':{'sequence':n,'action':action,'result':v['result'],'resultRef':ref}}
