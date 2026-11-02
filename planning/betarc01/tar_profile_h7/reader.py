"""Explicit SAFE_GNU_LONGNAME_L_V1 readonly original-device TAR profile.
No extraction, links, SDK calls or native authority. Existing strict readers stay unchanged.
"""
from pathlib import Path
import hashlib,json,os,re,tarfile
RAW_LIMIT=192*2**20;LOGICAL_LIMIT=512*2**20;ENTRY_LIMIT=8192;PATH_LIMIT=240;BLOCK=512
PROFILE='SAFE_GNU_LONGNAME_L_V1'
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

def hash_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for raw in iter(lambda:f.read(65536),b''):h.update(raw)
 return h.hexdigest()

def scan(raw_path):
 p=Path(raw_path);need(p.is_file()and not p.is_symlink()and 1024<=p.stat().st_size<=RAW_LIMIT,'RAW_REGULAR192M');entries=[];names=set();logical=0;carrier=None;at=0;headers=0;rawhash=hashlib.sha256()
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
    need(name not in names and len(names)<ENTRY_LIMIT,'NO_DUPLICATE_ENTRIES');names.add(name);logical+=size;need(logical<=LOGICAL_LIMIT,'TOTAL_LOGICAL512M');remaining=size
    while remaining:
     data=f.read(min(65536,remaining));need(bool(data),'BODY_TRUNCATED');rawhash.update(data);bodyhash.update(data);remaining-=len(data)
    entry={'path':name,'type':'directory'if directory else'regular','typeflag':kind,'mode':octal(h[100:108]),'uid':octal(h[108:116]),'gid':octal(h[116:124]),'mtime':octal(h[136:148]),'bytes':size,'sha256':bodyhash.hexdigest(),'uname':text(h[265:297],optional=True),'gname':text(h[297:329],optional=True),'headerOffset':offset,'headerSHA256':sha(h),'bodyOffset':start,'longname':carrier};entries.append(entry);carrier=None
   pad=f.read((-size)%BLOCK);rawhash.update(pad);need(len(pad)==(-size)%BLOCK and not any(pad),'EXACT_ZERO_MEMBER_PADDING')
 need(bool(entries),'NONEMPTY_EXPORT');return {'rawPath':str(p.absolute()),'rawBytes':p.stat().st_size,'rawSHA256':rawhash.hexdigest(),'transportHeaders':headers,'entries':entries,'logicalBytes':logical,'longnameHeaders':sum(e['longname']is not None for e in entries)}


def validate_tar_shape(path):return scan(path)

from planning.nativejournal17.receiver17 import aj02,TOTAL
def native_tar(path,expected_digest,*,allow_empty_active=False):
 p=Path(path);need(p.stat().st_size<=192*2**20,'FULL_TAR192M');h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 need(h.hexdigest()==expected_digest,'COMPLETE_ORIGINAL_TAR_SHA');shape=validate_tar_shape(p)
 files={};journals={};input_originals={};logical=0;inputbytes=0;seen=set()
 with tarfile.open(p,'r:')as t:
  for member in t:
   name=member.name.rstrip('/');need(name=='files'or name.startswith('files/'),'WHOLE_PRIVATE_FILES_SCOPE');need(not any(x in('','..','.')for x in name.split('/'))and name not in seen and len(seen)<8192 and not member.pax_headers and not member.issym()and not member.islnk()and(member.isdir()or member.isfile()),'TAR_MEMBER_SHAPE');seen.add(name)
   if member.isdir():continue
   logical+=member.size;need(logical<=512*2**20,'WHOLE_NATIVE_LOGICAL512M');relevant=any(name.startswith('files/'+prefix+'/')for prefix in('product-input01','product-input-archives17','product-input-registry17','product-input-lifecycle17'))
   if relevant:inputbytes+=member.size;need(inputbytes<=TOTAL,'ALL_INPUT_ARCHIVE_INDEX_CONTROL64M')
   digest=hashlib.sha256();parts=[];size=0;source=t.extractfile(member)
   while True:
    block=source.read(65536)
    if not block:break
    size+=len(block);need(size<=member.size,'TAR_ORIGINAL_GROWTH');digest.update(block)
    if relevant:parts.append(block)
   need(size==member.size,'TAR_ORIGINAL_BYTES');files[name]={'bytes':size,'sha256':digest.hexdigest()};data=b''.join(parts)if relevant else None
   if relevant:input_originals[name]=data
   m=re.fullmatch('files/product-input01/([a-f0-9]{32})[.]aj02',name)
   if m:journals[m[1]]={'raw':data,**files[name],**aj02(data)}
 need(files and (0 if allow_empty_active else 1)<=len(journals)<=8,'ACTIVE_GENERATIONS1_8');return {'tarSHA256':expected_digest,'tarBytes':p.stat().st_size,'files':files,'journals':journals,'inputBytes':inputbytes,'logicalBytes':logical,'inputOriginals':input_originals,'transportProfile':observation(shape)}

def observation(result):
 return {'format':'aeris-original-native-tar-profile-observation','version':1,'profile':PROFILE,'readerSourceSHA256':hash_file(__file__),'rawBytes':result['rawBytes'],'rawSHA256':result['rawSHA256'],'logicalMembers':len(result['entries']),'physicalHeaders':result['transportHeaders'],'longnameMetadataCarriers':result['longnameHeaders'],'logicalBytes':result['logicalBytes'],'originalDeviceBytesUnmodified':True,'derivedViewCreated':False,'flightAcceptance':False,'authorityRestorable':False}
