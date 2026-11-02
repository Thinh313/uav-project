"""Independent complete-byte cold backup receiver. Never writes app files/actors.
Header-only AJ02 is UNUSED, not successful/closed input. CLOSED_VERIFIED requires
original Root STATUS/ACK/source joins and signed payload verification.
"""
from pathlib import Path
import base64,hashlib,io,json,os,re,shlex,struct,subprocess,sys,tarfile
MAGIC=b'AERIS_INPUT_JOURNAL_V2\n';TOTAL=64*2**20;PACKAGE='vn.rtr.aeris.betasim09'
def need(v,n):
 if not v:raise ValueError('JOURNAL17_RECEIVER_'+n)
def pairs(items):
 out={}
 for k,v in items:need(k not in out,'DUPLICATE_JSON');out[k]=v
 return out
def decode(b):return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in()).throw(ValueError('NONFINITE')))
def sha(b):return hashlib.sha256(b).hexdigest()
def bounded(p,maxbytes):
 p=Path(p).absolute();need(not any(x.is_symlink()for x in[p,*p.parents])and p.is_file()and p.stat().st_nlink==1 and p.stat().st_size<=maxbytes,'REGULAR_SINGLE_LINK_SOURCE');b=p.read_bytes();need(len(b)<=maxbytes,'SOURCE_GROWTH');return b
def aj02(b):
 need(b.startswith(MAGIC)and len(b)<=32*2**20,'AJ02_MAGIC_OR_CAP');at=len(MAGIC);seq=0;last=-1;head=bytes(32);pending=None;envelopes=[]
 while at<len(b):
  need(at+4<=len(b),'AJ02_TORN');n=struct.unpack_from('!I',b,at)[0];need(82<=n<=2581 and at+4+n<=len(b),'AJ02_BOUND');body=b[at+4:at+4+n-32];digest=b[at+4+n-32:at+4+n];number,clock,kind=struct.unpack_from('!QQB',body);previous=body[17:49];payload=body[49:];seq+=1
  need(seq<=24576 and number==seq and clock>=last and previous==head and hashlib.sha256(body).digest()==digest,'AJ02_CHAIN')
  if kind==1:need(pending is None and 0<len(payload)<=2500,'AJ02_INTENT_ORDER');envelopes.append({'sequence':seq,'envelope':decode(payload)});pending=seq
  else:need(kind==2 and pending is not None and re.fullmatch(rb'[1-5][0-9]{2}',payload),'AJ02_OUTCOME_ORDER');pending=None
  head=digest;last=clock;at+=4+n
 return {'records':seq,'bytes':len(b),'head':head.hex(),'unresolvedIntent':pending,'envelopes':envelopes,'disposition':'UNUSED'if b==MAGIC else'UNRESOLVED','sourceClosedStatusBound':False}
def validate_tar_shape(path):
 def text(b):return b.split(b'\0',1)[0].decode('utf-8',errors='strict')
 def octal(b):
  v=b.split(b'\0',1)[0].strip();need(re.fullmatch(rb'[0-7]+',v),'TAR_OCTAL');return int(v,8)
 seen=set();logical=0
 with Path(path).open('rb')as source:
  while True:
   h=source.read(512);need(len(h)==512,'TAR_HEADER_OR_EOA_TRUNCATED')
   if h==bytes(512):
    need(source.read(512)==bytes(512),'TAR_TWO_EOA_REQUIRED');tail=source.read(10241);need(len(tail)<=10240 and not any(tail)and source.read(1)==b'','TAR_TRAILING_NONZERO_OR_EXCESS');return
   need(sum(h[:148])+8*32+sum(h[156:])==octal(h[148:156]),'TAR_CHECKSUM');kind=h[156];need(kind in(0,48,53)and not any(h[157:257]),'TAR_NO_LINK_OR_EXTENSION');name='/'.join(x for x in(text(h[345:500]),text(h[:100]))if x);name=name[:-1]if kind==53 and name.endswith('/')else name
   need((name=='files'or name.startswith('files/'))and len(name)<=240 and not any(x in('','..','.')for x in name.split('/'))and name not in seen and len(seen)<8192,'TAR_EXACT_PATH_COMPONENTS');seen.add(name);size=octal(h[124:136]);logical+=size;need(logical<=512*2**20 and(kind!=53 or size==0),'TAR_LOGICAL512M');need(source.tell()+size<=Path(path).stat().st_size,'TAR_MEMBER_TRUNCATED');source.seek(size,1);pad=source.read((-size)%512);need(len(pad)==(-size)%512 and not any(pad),'TAR_MEMBER_PADDING')
def native_tar(path,expected_digest,*,allow_empty_active=False):
 p=Path(path);need(p.stat().st_size<=192*2**20,'FULL_TAR192M');h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 need(h.hexdigest()==expected_digest,'COMPLETE_ORIGINAL_TAR_SHA');validate_tar_shape(p)
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
 need(files and (0 if allow_empty_active else 1)<=len(journals)<=8,'ACTIVE_GENERATIONS1_8');return {'tarSHA256':expected_digest,'tarBytes':p.stat().st_size,'files':files,'journals':journals,'inputBytes':inputbytes,'logicalBytes':logical,'inputOriginals':input_originals}
def cold_originals(proof,backup):
 """Load already immutable selected candidate, then cold join original ADB refs."""
 required={'format','version','candidatePath','candidateSHA256','androidEvidenceRoot','coldBeforeRef','coldAfterRef','installedPathRef','installedSHARef','backupCaptureRef','backupSHA256','backupBytes'};need(type(proof)is dict and set(proof)==required and proof['format']=='aeris-journal17-original-cold-backup'and type(proof['version'])is int and proof['version']==1,'COLD_PROOF_SCHEMA')
 candidate=Path(proof['candidatePath']).resolve();need(re.fullmatch('[a-f0-9]{64}',proof['candidateSHA256'])and candidate.name==proof['candidateSHA256'],'COLD_CANDIDATE_IDENTITY');repo=Path(__file__).resolve().parents[2];need(candidate.is_relative_to(repo/'evidence'),'COLD_CANDIDATE_SCOPE');os.environ['AERIS_REPOSITORY_ROOT']=str(repo);sys.dont_write_bytecode=True
 for name,module in list(sys.modules.items()):
  if name=='aeris_runtime'or name.startswith('aeris_runtime.'):
   origin=getattr(module,'__file__',None);need(origin is not None and Path(origin).resolve().is_relative_to(candidate/'source/aeris_runtime'),'FOREIGN_CACHED_MODULE_REFUSED')
 sys.path[:0]=[str(candidate/'source'),str(repo)]
 from aeris_runtime.candidate import load
 from aeris_runtime.once_reader import read_ref
 from aeris_runtime.status15_reader import command
 manifest=load(candidate,proof['candidateSHA256']);root=Path(proof['androidEvidenceRoot']).resolve();need(root.is_relative_to(repo/'evidence')and manifest['native']['package']==PACKAGE,'COLD_OWNED_APP_SCOPE')
 before,_,remote,out=command(root,proof['coldBeforeRef']);need(remote==['sh','-c','if pidof '+PACKAGE+' >/dev/null; then echo RUNNING; else echo ABSENT; fi']and out==b'ABSENT\n','COLD_ABSENCE_BEFORE');after,_,remote,out=command(root,proof['coldAfterRef']);need(remote==['sh','-c','if pidof '+PACKAGE+' >/dev/null; then echo RUNNING; else echo ABSENT; fi']and out==b'ABSENT\n','COLD_ABSENCE_AFTER')
 installed_path,_,remote,out=command(root,proof['installedPathRef']);need(remote==['pm','path',PACKAGE]and out.startswith(b'package:/')and len(out.splitlines())==1,'INSTALLED_PACKAGE_PATH');apkpath=out.decode().strip()[8:];installed_sha,_,remote,out=command(root,proof['installedSHARef']);need(remote==['sha256sum',apkpath]and out.decode().split()[0]==manifest['native']['APK_SHA256'],'INSTALLED_APK_SHA')
 capture=decode(read_ref(root,proof['backupCaptureRef']));argv=decode(read_ref(root,capture['argvRef']));need(capture.get('format')=='aeris-native-export'and capture.get('fullOriginalFiles')is True and capture.get('captureComplete')is True and capture.get('failure')is None and capture.get('cleanupErrors')==[]and type(capture.get('exit'))is int and capture['exit']==0 and read_ref(root,capture['stderrRef'])==b''and argv[1:]==['-s','emulator-5582','exec-out','run-as',PACKAGE,'tar','-cf','-','files'],'COMPLETE_READONLY_BACKUP_PIPE');need(before['endedHostNs']<=installed_path['startedHostNs']<=installed_path['endedHostNs']<=installed_sha['startedHostNs']<=installed_sha['endedHostNs']<=capture['startedHostNs']<=capture['finishedHostNs']<=after['startedHostNs'],'COLD_BACKUP_CAUSAL_ORDER');need(capture['bytesRetained']==proof['backupBytes']==Path(backup).stat().st_size and capture['path']==str(Path(backup).resolve()),'ORIGINAL_BACKUP_PATH_BYTES');
 for name,module in list(sys.modules.items()):
  if name=='aeris_runtime'or name.startswith('aeris_runtime.'):
   origin=Path(getattr(module,'__file__','')).resolve();need(origin.is_relative_to(candidate/'source/aeris_runtime'),'LOADED_MODULE_ORIGIN');relative=str(origin.relative_to(candidate/'source'));need(manifest['sourceSHA256'].get(relative)==sha(origin.read_bytes()),'LOADED_MODULE_SOURCE_SHA')
 return manifest,root

def verify_closed(journal,generation,manifest,root,node):
 from aeris_runtime.product_native09 import verify_originals
 need(Path(sys.modules['aeris_runtime.product_native09'].__file__).resolve().is_relative_to(Path(sys.modules['aeris_runtime.candidate'].__file__).resolve().parents[1]),'LATE_NATIVE_MODULE_ORIGIN')
 from aeris_runtime.once_reader import read_receipts,read_ref
 verify_originals(root,manifest);candidates=[]
 for row in read_receipts(root,'request'):
  snap=decode(read_ref(root,row['snapshotRef']));inp=snap['input'];j=inp['journal']
  if j.get('generation')==generation and j.get('closed')is True and j.get('failed')is False and j.get('durablyDrained')is True and j.get('pendingOutcome')is False and j.get('bytes')==journal['bytes']and j.get('sequence')==journal['records']and j.get('head')==journal['head']:candidates.append((row,snap))
 need(candidates and journal['unresolvedIntent']is None,'ORIGINAL_CLOSED_STATUS_REQUIRED_NOT_DEFAULT');row,snapshot=candidates[-1];inp=snapshot['input'];descriptor_path=Path(root).parents[2]/'reports/product-descriptor-01.json';descriptor=decode(bounded(descriptor_path,32768));context=descriptor['context'];need(context['run']==Path(root).parent.name and all(type(context.get(k))is str for k in('run','epoch','boot','operator','generation')),'ORIGINAL_CASE_CONTEXT')
 q={'snapshot':snapshot,'context':context,'generation':generation,'envelopes':journal['envelopes'],'originalStatusRef':row['snapshotRef']};script=Path(__file__).with_name('verify-signatures17.mjs');result=subprocess.run([str(node),str(script)],input=json.dumps(q,separators=(',',':')).encode(),capture_output=True,timeout=30);need(result.returncode==0 and not result.stderr and len(result.stdout)<=4096,'ORIGINAL_P256_SIGNATURES');result=decode(result.stdout);need(result.get('verifiedInputs')==len(journal['envelopes']),'ALL_SIGNED_INTENTS');return {'disposition':'CLOSED_VERIFIED','originalStatusRef':row['snapshotRef'],'sourceClosedStatusBound':True,'verifiedSignedInputs':result['verifiedInputs']}

def receive(backup,proof_path,proof_sha,new_source,expected_head,node=None):
 proofraw=bounded(proof_path,32768);need(sha(proofraw)==proof_sha,'COLD_PROOF_SHA');proof=decode(proofraw);manifest,root=cold_originals(proof,backup);scan=native_tar(backup,proof['backupSHA256']);need(proof['backupSHA256']==scan['tarSHA256'],'COLD_BACKUP_SHA');rows=[]
 if expected_head=='ROOT':need(len(scan['journals'])==8 and all(j['raw']==MAGIC for j in scan['journals'].values()),'INITIAL_EXACT8_UNUSED_ONLY')
 for generation,j in sorted(scan['journals'].items()):
  d={'disposition':'UNUSED','sourceClosedStatusBound':False,'reason':'EXACT_MAGIC_NO_INPUT_HISTORY'}if j['raw']==MAGIC else verify_closed(j,generation,manifest,root,node)
  need(d['disposition']in('UNUSED','CLOSED_VERIFIED'),'UNRESOLVED_BLOCKS');rows.append({'generation':generation,'bytes':j['bytes'],'sha256':j['sha256'],'records':j['records'],'disposition':d['disposition'],'proofSHA256':sha(json.dumps(d,sort_keys=True,separators=(',',':')).encode()),'sourceClosedStatusBound':d['sourceClosedStatusBound']})
 report={'format':'aeris-journal17-independent-full-byte-receiver','version':1,'status':'COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT','package':PACKAGE,'oldAPKSHA256':manifest['native']['APK_SHA256'],'oldSourceSHA256':manifest['native']['sourceSHA256'],'newSourceSHA256':new_source,'backupSHA256':scan['tarSHA256'],'backupBytes':scan['tarBytes'],'coldProofSHA256':proof_sha,'expectedHostRegistryHead':expected_head,'allPrivateFiles':len(scan['files']),'allPrivateLogicalBytes':scan['logicalBytes'],'totalInputArchiveIndexControlBytes':scan['inputBytes'],'originals':rows,'authorityRestorable':False,'actualFlightAccepted':False};raw=(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n').encode();receiver_sha=sha(raw)
 need(re.fullmatch('[a-f0-9]{64}',new_source)and(expected_head=='ROOT'or re.fullmatch('[a-f0-9]{64}',expected_head)),'NEW_SOURCE_HEAD_BINDING');lines=['AERIS_JOURNAL_LIFECYCLE17\t1','package\t'+PACKAGE,'oldAPK\t'+manifest['native']['APK_SHA256'],'oldSource\t'+manifest['native']['sourceSHA256'],'newSource\t'+new_source,'backup\t'+scan['tarSHA256']+'\t'+str(scan['tarBytes']),'receiver\t'+receiver_sha,'cold\t'+proof_sha,'expectedHead\t'+expected_head]+['generation\t'+r['generation']+'\t'+str(r['bytes'])+'\t'+r['sha256']+'\t'+r['disposition']+'\t'+r['proofSHA256']for r in rows]+['end',''];plan='\n'.join(lines).encode('ascii');need(len(plan)<=16384,'PLAN16K');return raw,plan

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description='Fresh readonly cold receiver, no native/device mutation');parser.add_argument('--backup',required=True);parser.add_argument('--cold-proof',required=True);parser.add_argument('--cold-proof-sha',required=True);parser.add_argument('--new-source',required=True);parser.add_argument('--expected-head',required=True);parser.add_argument('--node');a=parser.parse_args()
 report,plan=receive(a.backup,a.cold_proof,a.cold_proof_sha,a.new_source,a.expected_head,a.node)
 result={'format':'aeris-journal17-fresh-cold-receiver-result','version':1,'reportBase64':base64.b64encode(report).decode(),'reportSHA256':sha(report),'planBase64':base64.b64encode(plan).decode(),'planSHA256':sha(plan),'readOnly':True,'actorsStarted':False,'authorityRestorable':False};encoded=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode();need(len(encoded)<=32768,'CLI_RESULT32K');sys.stdout.buffer.write(encoded)
