"""Independent recipient-byte verifier. No source archive reads or extraction.
Part openers must stream the exact URI bytes captured from genuine Android SAF.
This module verifies transfer/completeness, not AP flight or ECDSA semantics.
"""
import base64,gzip,hashlib,io,json,re,struct
MIB=2**20

def need(v,n):
 if not v:raise ValueError('SAF_RECEIVER_'+n)
def unique(items):
 d={}
 for k,v in items:need(k not in d,'DUPLICATE_JSON');d[k]=v
 return d
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def decode(raw):return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in()).throw(ValueError('SAF_RECEIVER_NONFINITE_JSON')))
def clean(path):return type(path)is str and len(path)<=240 and not path.startswith('/')and not any(x in('','.','..')for x in path.split('/'))and not re.search(r'[\\\x00-\x1f]',path)
def exact_read(source,n):
 parts=[];remaining=n
 while remaining:
  b=source.read(min(65536,remaining));need(type(b)is bytes and 0<len(b)<=remaining,'TRUNCATED_OR_BAD_STREAM');parts.append(b);remaining-=len(b)
 return b''.join(parts)
class Parts(io.RawIOBase):
 def __init__(self,manifest,openers):
  self.manifest=manifest;self.parts=manifest['parts'];need(type(self.parts)is list and 1<=len(self.parts)<=6 and len(openers)==len(self.parts),'ALL_PARTS_REQUIRED');self.openers=openers;self.index=0;self.current=None;self.manager=None;self.count=0;self.total=0;self.part_hash=None;self.bundle_hash=hashlib.sha256();self.finished=False
  offset=0
  for i,p in enumerate(self.parts):need(type(p)is dict and p['index']==i and p['offset']==offset and type(p['bytes'])is int and 0<p['bytes']<=28*MIB and re.fullmatch('[a-f0-9]{64}',p['sha256'])is not None,'PART_MANIFEST');offset+=p['bytes']
  need(offset==manifest['bytes']and offset<=192*MIB,'STREAM_BYTE_BOUND')
 def readable(self):return True
 def _close_part(self):
  p=self.parts[self.index];need(self.count==p['bytes']and self.part_hash.hexdigest()==p['sha256'],'ORIGINAL_RECIPIENT_PART_SHA');need(self.current.read(1)==b'','RECIPIENT_PART_TRAILING_BYTES');self.manager.__exit__(None,None,None);self.manager=None;self.current=None;self.index+=1
 def read(self,n=-1):
  need(type(n)is int and n>=0,'BOUNDED_READ_REQUIRED');n=min(n,65536)
  if n==0:return b''
  if self.finished:return b''
  result=bytearray()
  while len(result)<n:
   if self.current is None:
    if self.index==len(self.parts):
     need(self.total==self.manifest['bytes']and self.bundle_hash.hexdigest()==self.manifest['sha256'],'ORIGINAL_RECIPIENT_STREAM_SHA');self.finished=True;break
    self.manager=self.openers[self.index]();self.current=self.manager.__enter__();self.count=0;self.part_hash=hashlib.sha256()
   remaining=self.parts[self.index]['bytes']-self.count
   if remaining==0:self._close_part();continue
   b=self.current.read(min(n-len(result),remaining,65536));need(type(b)is bytes and 0<len(b)<=min(n-len(result),remaining),'RECIPIENT_PART_TRUNCATED');self.count+=len(b);self.total+=len(b);self.part_hash.update(b);self.bundle_hash.update(b);result.extend(b)
  return bytes(result)
 def close(self):
  if getattr(self,'manager',None) is not None:self.manager.__exit__(RuntimeError,RuntimeError('RECIPIENT_VERIFICATION_INCOMPLETE'),None);self.manager=None;self.current=None
  super().close()
def octal(raw):
 text=raw.split(b'\0',1)[0].strip();need(re.fullmatch(rb'[0-7]+',text)is not None,'TAR_OCTAL');return int(text,8)
def tar_walk(source,*,expected=None,embedded=None,native_journal=None,capture_refs=None):
 captures={}if capture_refs is None else{k:bytearray()for k in capture_refs}
 seen=set();files=[];total=0;native={}if type(native_journal)is dict else None;first=True;native_paths=set(native_journal)if type(native_journal)is dict else{native_journal}if native_journal is not None else set()
 while True:
  header=exact_read(source,512)
  if not any(header):need(exact_read(source,512)==bytes(512),'SECOND_ZERO_TAR_HEADER');break
  need(sum(header[:148])+8*32+sum(header[156:])==octal(header[148:156]),'TAR_CHECKSUM');need(header[156]in(0,48,53)and not any(header[157:257]),'REGULAR_OR_DIRECTORY_NO_LINK')
  text=lambda b:b.split(b'\0',1)[0].decode('utf-8');name='/'.join(x for x in(text(header[345:500]),text(header[:100]))if x);name=name.rstrip('/')if header[156]==53 else name
  need(clean(name)and name not in seen and len(seen)<8192,'TAR_SAFE_UNIQUE_MEMBER');seen.add(name);size=octal(header[124:136]);need(size<=16*2**30,'TAR_FILE_BOUND')
  if native_journal is not None:need((name=='files'or name.startswith('files/'))and size<=512*MIB,'NATIVE_FILES_NAMESPACE_AND_SIZE')
  if header[156]==53:need(size==0 and expected is None,'DIRECTORY_SCOPE');first=False;continue
  is_manifest=name=='closed-raw-manifest.json'
  if expected is not None:
   need(is_manifest and first and embedded is not None and size<=256*1024 or not is_manifest and name in expected and size==expected[name]['bytes'],'EXACT_RAW_MEMBER_SET')
  h=hashlib.sha256();remaining=size;parts=[]if is_manifest or name in native_paths else None
  while remaining:
   position=size-remaining;b=exact_read(source,min(65536,remaining));h.update(b);remaining-=len(b)
   for key,ref in(capture_refs or{}).items():
    if ref['path']==name:
     a=max(position,ref['offset']);z=min(position+len(b),ref['offset']+ref['bytes'])
     if z>a:captures[key].extend(b[a-position:z-position]);need(len(captures[key])<=ref['bytes'],'HISTORICAL_SPAN_BOUND')
   if parts is not None:need(size<=32*MIB,'MANAGED_MEMBER_MEMORY_BOUND');parts.append(b)
  digest=h.hexdigest();total+=size;need(total<=16*2**30,'TAR_TOTAL_BOUND')
  if native_journal is not None:need(total<=512*MIB,'NATIVE_LOGICAL512M_BOUND')
  if is_manifest:need(canonical(decode(b''.join(parts)))==canonical(embedded),'EMBEDDED_ORIGINAL_MANIFEST')
  elif expected is not None:need(digest==expected[name]['sha256'],'RAW_FILE_SHA')
  if name in native_paths:
   if type(native_journal)is dict:native[name]=verify_aj02(b''.join(parts),native_journal[name])
   else:native={'bytes':size,'sha256':digest,'raw':b''.join(parts)}
  padding=(-size)%512
  if padding:need(exact_read(source,padding)==bytes(padding),'TAR_FILE_PADDING')
  files.append({'path':name,'bytes':size,'sha256':digest});first=False
 tail=0
 while True:
  b=source.read(65536)
  if not b:break
  tail+=len(b);need(tail<=10240 and not any(b),'TAR_TRAILING_BYTES')
 if expected is not None:need(seen==set(expected)|{'closed-raw-manifest.json'},'MISSING_RAW_MEMBERS')
 for key,ref in(capture_refs or{}).items():need(len(captures[key])==ref['bytes']and hashlib.sha256(captures[key]).hexdigest()==ref['sha256'],'HISTORICAL_ORIGINAL_SPAN_SHA')
 return {'files':files,'total':total,'native':native,'capturedRefs':{k:bytes(v)for k,v in captures.items()}}
def verify_aj02(raw,wanted):
 magic=b'AERIS_INPUT_JOURNAL_V2\n';need(raw.startswith(magic),'AJ02_MAGIC');at=len(magic);number=0;head=bytes(32);last=-1;pending=None;envelopes=0
 while at<len(raw):
  need(at+4<=len(raw),'AJ02_TORN_PREFIX');n=struct.unpack_from('!I',raw,at)[0];need(82<=n<=2581 and at+4+n<=len(raw),'AJ02_TORN_RECORD');row=raw[at+4:at+4+n];body=row[:-32];digest=row[-32:];seq,elapsed=struct.unpack_from('!QQ',body);kind=body[16];payload=body[49:]
  need(seq==number+1 and seq<=24576 and elapsed>=last and body[17:49]==head and hashlib.sha256(body).digest()==digest,'AJ02_ORIGINAL_CHAIN');need(kind==1 and pending is None and len(payload)<=2500 or kind==2 and pending is not None and re.fullmatch(rb'[1-5][0-9]{2}',payload)is not None,'AJ02_ORDER')
  if kind==1:
   q=decode(payload);need(q.get('format')=='aeris-native-input-signed-envelope'and q.get('version')==1,'AJ02_SIGNED_ENVELOPE_SHAPE');pending=seq;envelopes+=1
  else:pending=None
  number=seq;last=elapsed;head=digest;at+=4+n
 need(len(raw)==wanted['bytes']and hashlib.sha256(raw).hexdigest()==wanted['sha256']and number==wanted['sequence']and head.hex()==wanted['head']and pending==wanted.get('unresolvedIntentSequence'),'AJ02_SOURCE_CLOSED_JOURNAL_JOIN');return {'records':number,'envelopes':envelopes,'unresolvedIntent':pending,'SHA256':hashlib.sha256(raw).hexdigest(),'signatureSemanticsVerifiedHere':False}
def verify_recipient(manifest_original,*,manifest_sha,expected_context,expected_candidate,bundle_openers,native_openers):
 need(type(manifest_original)is bytes and len(manifest_original)<=256*1024 and hashlib.sha256(manifest_original).hexdigest()==manifest_sha,'ORIGINAL_MANIFEST_SHA');m=decode(manifest_original);need(m.get('format')=='aeris-betasim-closed-raw-manifest'and m.get('version')==1 and canonical(m.get('context'))==canonical(expected_context)and m.get('sourceCandidateSHA256')==expected_candidate and m.get('authorityRestorable')is False,'ORIGINAL_MANIFEST_SCOPE')
 need(m.get('allOriginalRawAndAPStateIncluded')is True and m.get('productSemanticAndMediaIncluded')is True,'FULL_SCOPE_FLAGS');expected={}
 for f in m['files']:need(clean(f['path'])and f['path'].startswith(('raw/','simulation/AP-state/','product/','android-api/','processes/','root-management/'))and f['path']not in expected,'ORIGINAL_PATH_SCOPE');expected[f['path']]=f
 need(len(expected)==len(m['files'])and sum(f['bytes']for f in expected.values())==m['totalOriginalBytes'],'ORIGINAL_FILE_TABLE');embedded={k:v for k,v in m.items()if k not in('bundle','nativeStream','manifestKind')}
 historical=m.get('retainedOriginalApplication');refs=None
 if historical is not None:
  need(type(historical)is dict and historical.get('format')=='aeris-retained-original-application-transfer'and historical.get('version')==1 and historical.get('path')=='android-api/retained-original-application.tar'and historical.get('applicationId')=='vn.rtr.aeris.mission'and historical.get('activeApplicationId')=='vn.rtr.aeris.betasim09'and historical.get('role')=='HISTORICAL_RETAINED_NOT_CURRENT_FLIGHT_INPUT'and historical.get('authorityGranted')is False,'HISTORICAL_TRANSFER_SCOPE');file=expected.get(historical['path']);need(file is not None and file['bytes']==historical['bytes']and file['sha256']==historical['sha256'],'HISTORICAL_FILE_EXACT_ORIGINAL_REF');refs=historical.get('originalRefs');need(type(refs)is dict and set(refs)=={'application','inventory','backup','du','duStdout','duArgv'},'HISTORICAL_ALL_ORIGINAL_PROOFS')
  for ref in refs.values():need(type(ref)is dict and set(ref)=={'path','offset','bytes','sha256'}and ref['path']in expected and ref['path'].startswith('android-api/')and type(ref['offset'])is int and type(ref['bytes'])is int and 0<ref['bytes']<=4096 and 0<=ref['offset']<=expected[ref['path']]['bytes']-ref['bytes'],'HISTORICAL_ORIGINAL_REF_BOUND')
  need(sum(q['bytes']for q in refs.values())<=16384,'HISTORICAL_ALL_PROOF16K')
 need(type(m['bundle']['bytes'])is int and type(m['nativeStream']['bytes'])is int and m['bundle']['bytes']+m['nativeStream']['bytes']<=192*MIB,'JOINT_RECIPIENT_BYTES192M');need(m['bundle']['encoding']=='TAR_GZIP_LOSSLESS'and m['nativeStream']['encoding']=='TAR_UNCOMPRESSED_ORIGINAL','JOINT_ENCODINGS');b=Parts(m['bundle'],bundle_openers)
 try:
  with gzip.GzipFile(fileobj=b,mode='rb')as gz:result=tar_walk(gz,expected=expected,embedded=embedded,capture_refs=refs)
  need(b.finished,'FULL_COMPRESSED_STREAM_END')
 finally:b.close()
 if historical is not None:
  original=result['capturedRefs'];application=decode(original['application']);inventory=decode(original['inventory']);backup=decode(original['backup']);du=decode(original['du']);argv=decode(original['duArgv']);du_stdout=original['duStdout'];match=re.fullmatch(rb'([0-9]+)[\t ]+files\n',du_stdout)
  need(application.get('format')=='aeris-root-observed-development-application-domain'and application.get('applicationId')==historical['activeApplicationId']and application.get('candidateSHA256')==expected_candidate and application.get('sourceSHA256')==m['nativeClosedFiles']['sourceSHA256']and application.get('APKSHA256')==m['nativeClosedFiles']['APKSHA256']and application.get('privateFilesDirectory')=='/data/user/0/vn.rtr.aeris.betasim09/files'and application.get('nativeReportedApplicationId')is False,'HISTORICAL_APPLICATION_ORIGINAL_JOIN')
  old=inventory.get('sourceOriginalTAR',{});need(inventory.get('format')=='aeris-retained-old-application-private-inventory'and inventory.get('package')=='vn.rtr.aeris.mission'and old.get('bytes')==historical['bytes']and old.get('sha256')==historical['sha256']and old.get('captureComplete')is True,'HISTORICAL_INVENTORY_ORIGINAL_JOIN')
  need(backup.get('format')=='aeris-native-export'and backup.get('fullOriginalFiles')is True and backup.get('captureComplete')is True and backup.get('failure')is None and backup.get('exit')==0 and backup.get('bytesRetained')==historical['bytes'],'HISTORICAL_COLD_BACKUP_ORIGINAL_JOIN')
  def same_original(prefix,original,selected):
   need(type(original)is dict and set(original)=={'format','version','path','offset','bytes','sha256'}and original['format']=='aeris-original-byte-ref'and type(original['version'])is int and original['version']==3 and type(original['path'])is str and clean(original['path']),'HISTORICAL_ORIGINAL_REFERENCE_SCHEMA');return {**{k:original[k]for k in('offset','bytes','sha256')},'path':prefix+original['path']}==refs[selected]
  need(same_original('android-api/',application.get('retainedInventoryRef'),'inventory')and same_original('android-api/retained-original/',inventory.get('sourceDUCommandRef'),'du')and same_original('android-api/retained-original/',inventory.get('sourceDUStdoutRef'),'duStdout')and same_original('android-api/retained-original/',inventory.get('sourceDUArgvRef'),'duArgv')and same_original('android-api/retained-original/',old.get('captureReceiptRef'),'backup')and same_original('android-api/retained-original/',du.get('stdoutRef'),'duStdout')and same_original('android-api/retained-original/',du.get('argvRef'),'duArgv'),'HISTORICAL_EXACT_CROSS_REFERENCE_JOIN')
  need(du.get('format')=='aeris-command'and du.get('captureComplete')is True and du.get('failure')is None and du.get('exit')==0 and type(argv)is list and argv[1:]==['-s','emulator-5582','shell','run-as','vn.rtr.aeris.mission','du','-k','-s','files']and match is not None and inventory.get('allocatedBytes')==int(match[1])*1024,'HISTORICAL_DU_ORIGINAL_JOIN')
 n=Parts(m['nativeStream'],native_openers);wanted=m['nativeClosedFiles']['journal'];generations=wanted.get('generations',[wanted]);need(type(generations)is list and 1<=len(generations)<=2,'SELECTED_NATIVE_GENERATION_BOUND');wanted_by_path={}
 for row in generations:need(clean(row['path'])and row['path'].startswith('files/product-input01/')and row['path']not in wanted_by_path,'EXACT_SELECTED_NATIVE_PATHS');wanted_by_path[row['path']]=row
 try:
  original=tar_walk(n,native_journal=wanted_by_path);need(n.finished and set(original['native'])==set(wanted_by_path),'ALL_SELECTED_NATIVE_GENERATIONS_RECEIVED');j={'generations':original['native'],'selectedGenerations':len(original['native']),'signatureSemanticsVerifiedHere':False}
  file_table={r['path']:r for r in original['files']}
  for row in wanted.get('unselectedHistoricalJournals',[]):need(row['path']in file_table and all(file_table[row['path']][k]==row[k]for k in('bytes','sha256')),'ORIGINAL_UNSELECTED_HISTORICAL_JOURNAL_SHA')
 finally:n.close()
 need(m['nativeStream']['bytes']==m['nativeClosedFiles']['export']['bytes']and m['nativeStream']['sha256']==m['nativeClosedFiles']['export']['sha256'],'NATIVE_ORIGINAL_CAPTURE_JOIN')
 return {'format':'aeris-independent-recipient-byte-verification','version':1,'status':'RECIPIENT_BYTES_COMPLETE_NOT_FLIGHT_CERTIFICATION','manifestSHA256':manifest_sha,'sourceCandidateSHA256':expected_candidate,'rawFiles':len(expected),'rawOriginalBytes':m['totalOriginalBytes'],'compressedBytes':m['bundle']['bytes'],'nativeDocumentBytes':m['nativeStream']['bytes'],'nativeMembers':len(original['files']),'nativeInput':j,'historicalRetainedOriginalVerified':historical is not None,'historicalOldInputAuthorityGranted':False,'originalRawComplete':True,'documentBytesVerified':True,'actualSAFOrigin':'REQUIRES_ORIGINAL_NATIVE_URI_COMMAND_JOIN','executionEvidenceVerified':False,'authorityRestorable':False}
