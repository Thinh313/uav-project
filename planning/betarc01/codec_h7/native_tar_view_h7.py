"""Strict GNU-longname transport -> separate lossless USTAR view, never raw acceptance.
No extraction, links, SDK calls or native authority. Existing strict readers stay unchanged.
"""
from pathlib import Path
import hashlib,json,os,re
RAW_LIMIT=64*2**20;LOGICAL_LIMIT=512*2**20;ENTRY_LIMIT=8192;PATH_LIMIT=240;BLOCK=512
PROFILE='GNU_REGULAR_OR_DIRECTORY_PLUS_SINGLE_EXACT_LONGNAME_TO_USTAR_V1'
class CodecError(ValueError):pass
def need(value,name):
 if not value:raise CodecError('H7_'+name)
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
def text(raw,*,optional=False):
 first,sep,tail=raw.partition(b'\0');need(not sep or not any(tail),'TEXT_NUL_PADDING')
 try:value=first.decode('utf8')
 except UnicodeError as e:raise CodecError('H7_TEXT_UTF8')from e
 need(optional or bool(value),'TEXT_REQUIRED');need(not any(ord(x)<32 or ord(x)==127 for x in value),'TEXT_CONTROL');return value

def octal(raw,*,optional=False):
 head,sep,tail=raw.partition(b'\0');need(not sep or all(x in(0,32)for x in tail),'NUMBER_NUL_PADDING');value=head.strip(b' ')
 if optional and not value:return 0
 need(re.fullmatch(rb'[0-7]+',value)is not None,'OCTAL_ONLY_NO_BASE256');n=int(value,8);need(n<2**63,'INTEGER_BOUND');return n

def pathname(raw,directory):
 name=text(raw)
 if directory and name.endswith('/'):name=name[:-1]
 need(name=='files'or name.startswith('files/'),'PRIVATE_PATH_ROOT');need(len(name.encode())<=PATH_LIMIT and not any(p in('','.','..')for p in name.split('/'))and '\\'not in name,'SAFE_PATH_COMPONENTS');return name

def split_ustar(name):
 raw=name.encode('utf8')
 if len(raw)<=100:return raw,b''
 for i in range(len(raw)-1,-1,-1):
  if raw[i:i+1]==b'/'and i<=155 and 0<len(raw)-i-1<=100:return raw[i+1:],raw[:i]
 raise CodecError('H7_PATH_NOT_REPRESENTABLE_IN_USTAR_NO_TRUNCATION')

def hash_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for raw in iter(lambda:f.read(65536),b''):h.update(raw)
 return h.hexdigest()

def scan(raw_path):
 p=Path(raw_path);need(p.is_file()and not p.is_symlink()and 1024<=p.stat().st_size<=RAW_LIMIT,'RAW_REGULAR64M');entries=[];names=set();logical=0;carrier=None;at=0;headers=0;rawhash=hashlib.sha256()
 with p.open('rb')as f:
  while True:
   offset=f.tell();h=f.read(BLOCK);rawhash.update(h);need(len(h)==BLOCK,'HEADER_TRUNCATED')
   if h==bytes(BLOCK):
    need(carrier is None,'ORPHAN_LONGNAME');second=f.read(BLOCK);rawhash.update(second);need(second==bytes(BLOCK),'TWO_EOA_REQUIRED');tail=f.read(10241);rawhash.update(tail);need(len(tail)<=10240 and not any(tail)and f.read(1)==b'','TRAILING_PADDING_ONLY');break
   headers+=1;need(headers<=ENTRY_LIMIT*2,'TRANSPORT_HEADER_COUNT');need(octal(h[148:156])==sum(h[:148])+8*32+sum(h[156:]),'CHECKSUM');kind=h[156];need(not any(h[157:257]),'NO_LINK_TARGET');magic=h[257:265];need(magic in(b'ustar  \0',b'ustar\00000'),'EXACT_GNU_OR_USTAR_MAGIC');need(not any(h[500:]),'NO_RESERVED_EXTENSION');need(not magic==b'ustar  \0'or not any(h[345:]),'NO_GNU_SPARSE_OR_EXTRA_FIELDS');need(octal(h[329:337],optional=True)==octal(h[337:345],optional=True)==0,'NO_DEVICE_METADATA');meta={k:octal(h[a:b])for k,a,b in [('mode',100,108),('uid',108,116),('gid',116,124),('mtime',136,148)]};text(h[265:297],optional=True);text(h[297:329],optional=True);size=octal(h[124:136]);need(size<=LOGICAL_LIMIT,'MEMBER_SIZE_BOUND');prefix=text(h[345:500],optional=True);start=f.tell();bodyhash=hashlib.sha256()
   if kind==76:
    need(carrier is None and magic==b'ustar  \0'and text(h[:100])=='././@LongLink'and not prefix and 102<=size<=PATH_LIMIT+1,'EXACT_SINGLE_GNU_LONGNAME_HEADER');data=f.read(size);rawhash.update(data);need(len(data)==size and data[-1:]==b'\0'and b'\0'not in data[:-1],'LONGNAME_EXACT_TERMINAL_NUL');name=pathname(data[:-1],False);need(len(data[:-1])>100,'LONGNAME_NEEDED');carrier={'headerOffset':offset,'headerSHA256':sha(h),'payloadOffset':start,'payloadBytes':size,'payloadSHA256':sha(data),'nameBytes':data[:-1],'path':name}
   else:
    need(kind in(0,48,53),'NO_LINK_K_PAX_SPARSE_DEVICE_FIFO_OR_EXTENSION');directory=kind==53;need(not directory or size==0,'DIRECTORY_ZERO_BYTES')
    if carrier is not None:
     need(not directory and not prefix and h[:100]==carrier['nameBytes'][:100],'LONGNAME_MUST_IMMEDIATELY_MATCH_REGULAR_TRUNCATED_PREFIX');name=carrier['path']
    else:
     name=pathname((prefix+'/'if prefix else'').encode()+h[:100].split(b'\0',1)[0],directory);text(h[:100])
    need(name not in names and len(names)<ENTRY_LIMIT,'NO_DUPLICATE_ENTRIES');names.add(name);split_ustar(name);logical+=size;need(logical<=LOGICAL_LIMIT,'TOTAL_LOGICAL512M');remaining=size
    while remaining:
     data=f.read(min(65536,remaining));need(bool(data),'BODY_TRUNCATED');rawhash.update(data);bodyhash.update(data);remaining-=len(data)
    entry={'path':name,'type':'directory'if directory else'regular','typeflag':kind,'mode':octal(h[100:108]),'uid':octal(h[108:116]),'gid':octal(h[116:124]),'mtime':octal(h[136:148]),'bytes':size,'sha256':bodyhash.hexdigest(),'uname':text(h[265:297],optional=True),'gname':text(h[297:329],optional=True),'headerOffset':offset,'headerSHA256':sha(h),'bodyOffset':start,'longname':carrier};entries.append(entry);carrier=None
   pad=f.read((-size)%BLOCK);rawhash.update(pad);need(len(pad)==(-size)%BLOCK and not any(pad),'EXACT_ZERO_MEMBER_PADDING')
 need(bool(entries),'NONEMPTY_EXPORT');return {'rawPath':str(p.absolute()),'rawBytes':p.stat().st_size,'rawSHA256':rawhash.hexdigest(),'transportHeaders':headers,'entries':entries,'logicalBytes':logical,'longnameHeaders':sum(e['longname']is not None for e in entries)}

def number(value,width):
 raw=('%0*o'%(width-1,value)).encode();need(len(raw)==width-1,'USTAR_NUMBER_REPRESENTABLE');return raw+b'\0'
def header(entry):
 name,prefix=split_ustar(entry['path']);out=bytearray(BLOCK);out[:len(name)]=name;out[100:108]=number(entry['mode'],8);out[108:116]=number(entry['uid'],8);out[116:124]=number(entry['gid'],8);out[124:136]=number(entry['bytes'],12);out[136:148]=number(entry['mtime'],12);out[148:156]=b' '*8;out[156]=entry['typeflag'];out[257:265]=b'ustar\00000'
 for key,start in[('uname',265),('gname',297)]:
  raw=entry[key].encode();need(len(raw)<=32,'USTAR_OWNER_TEXT_BOUND');out[start:start+len(raw)]=raw
 out[329:337]=number(0,8);out[337:345]=number(0,8);out[345:345+len(prefix)]=prefix;out[148:156]=('%06o'%sum(out)).encode()+b'\0 ';return bytes(out)

def convert(raw_path,view_path):
 raw_path=Path(raw_path);view_path=Path(view_path);need(raw_path.absolute()!=view_path.absolute()and not any(p.is_symlink()for p in[view_path,*view_path.parents])and not view_path.exists(),'SEPARATE_EXCLUSIVE_DERIVED_VIEW');scan_result=scan(raw_path);raw_identity=raw_path.stat();proof_rows=[];viewhash=hashlib.sha256();view_size=0
 with raw_path.open('rb')as src,view_path.open('xb')as dst:
  def emit(raw):
   nonlocal view_size
   dst.write(raw);viewhash.update(raw);view_size+=len(raw);need(view_size<=RAW_LIMIT,'VIEW64M')
  for e in scan_result['entries']:
   view_header=view_size;emit(header(e));body_start=view_size;src.seek(e['bodyOffset']);remaining=e['bytes'];bodyhash=hashlib.sha256()
   while remaining:
    data=src.read(min(65536,remaining));need(bool(data),'SOURCE_CHANGED_OR_TRUNCATED');emit(data);bodyhash.update(data);remaining-=len(data)
   need(bodyhash.hexdigest()==e['sha256'],'SOURCE_BODY_CHANGED');emit(bytes((-e['bytes'])%BLOCK));row={**e,'viewHeaderOffset':view_header,'viewBodyOffset':body_start}
   if row['longname']is not None:row['longname']={k:v for k,v in row['longname'].items()if k!='nameBytes'}
   proof_rows.append(row)
  emit(bytes(BLOCK*2));dst.flush();os.fsync(dst.fileno())
 final=raw_path.stat();need((raw_identity.st_dev,raw_identity.st_ino,raw_identity.st_size)==(final.st_dev,final.st_ino,final.st_size)and hash_file(raw_path)==scan_result['rawSHA256'],'RAW_CHANGED_DURING_VIEW');need(view_size<=scan_result['rawBytes'],'VIEW_MUST_NOT_EXCEED_RAW');logical={e['path']:{k:e[k]for k in('type','typeflag','mode','uid','gid','mtime','bytes','sha256','uname','gname')}for e in proof_rows};return {'format':'aeris-h7-raw-ustar-view-binding','version':1,'profile':PROFILE,'status':'HOST_DERIVED_VIEW_OFFLINE_NOT_M501_ACCEPTANCE','raw':{'path':str(raw_path.absolute()),'bytes':scan_result['rawBytes'],'sha256':scan_result['rawSHA256']},'view':{'path':str(view_path.absolute()),'bytes':view_size,'sha256':viewhash.hexdigest(),'kind':'HOST_DERIVED_LOSSLESS_USTAR_VIEW_NOT_ORIGINAL_DEVICE_TAR'},'codecSourceSHA256':hash_file(__file__),'entryCount':len(proof_rows),'longnameCarrierCount':scan_result['longnameHeaders'],'logicalBytes':scan_result['logicalBytes'],'rawMap':proof_rows,'logicalTable':logical,'logicalTableSHA256':sha(canonical(logical)),'originalRawUnchanged':True,'oldStrictRawAcceptance':False,'m501Acceptance':False,'authorityRestorable':False,'flightAcceptance':False}
