"""Independent fragmented joint-stream recipient fixtures. No Node actor,
Android SAF, source archive reads, extraction or large files are used."""
from pathlib import Path
import contextlib,gzip,hashlib,importlib.util,io,json,struct,tarfile
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];source=HERE.parent/'runtime/source/aeris_runtime/saf_receiver.py';pin=hashlib.sha256(source.read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('qa_saf_receiver',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda b:hashlib.sha256(b).hexdigest();encode=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode();C={'run':'qa','epoch':'e','boot':'b','operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'};candidate='c'*64;checks=[]
def aj02(unmatched=False):
 raw=b'AERIS_INPUT_JOURNAL_V2\n';head=bytes(32)
 for n,kind,payload in[(1,1,encode({'format':'aeris-native-input-signed-envelope','version':1})),*([]if unmatched else[(2,2,b'200')])]:
  body=struct.pack('!QQB',n,1000000+n,kind)+head+payload;head=hashlib.sha256(body).digest();raw+=struct.pack('!I',len(body)+32)+body+head
 return raw,{'path':'files/product-input01/'+'d'*32+'.aj02','bytes':len(raw),'sha256':sha(raw),'sequence':1 if unmatched else 2,'head':head.hex(),'unresolvedIntentSequence':1 if unmatched else None}
def tar(entries,dirs=(),bad_type=None):
 stream=io.BytesIO()
 with tarfile.open(fileobj=stream,mode='w',format=tarfile.USTAR_FORMAT)as t:
  for name in dirs:
   h=tarfile.TarInfo(name);h.type=tarfile.DIRTYPE;h.mode=0o700;t.addfile(h)
  for name,data in entries:
   h=tarfile.TarInfo(name);h.size=len(data);h.mode=0o600
   if bad_type:h.type=bad_type
   t.addfile(h,io.BytesIO(data))
 return stream.getvalue()
def parts(data,fragments=2):
 at=len(data)//fragments;pieces=[data[i*at:(i+1)*at]for i in range(fragments-1)]+[data[(fragments-1)*at:]];offset=0;table=[]
 for i,b in enumerate(pieces):table.append({'index':i,'offset':offset,'bytes':len(b),'sha256':sha(b)});offset+=len(b)
 return {'bytes':len(data),'sha256':sha(data),'parts':table},pieces
def fixture(*,native_extra=None,bad_type=None,unmatched=False,pending_mismatch=False,raw_path=None,two_generations=False,omit_g1=False,tamper_g1=False,historical=False,tamper_historical=False):
 journal,wanted=aj02(unmatched);g1path=wanted['path'];selected_entries=[]if omit_g1 else[(g1path,journal[:-1]+bytes([journal[-1]^1])if tamper_g1 else journal)]
 if two_generations:
  empty=b'AERIS_INPUT_JOURNAL_V2\n';g2={'path':'files/product-input01/'+'e'*32+'.aj02','bytes':len(empty),'sha256':sha(empty),'sequence':0,'head':'0'*64,'unresolvedIntentSequence':None};g1=dict(wanted);wanted={**g2,'generations':[g1,g2]};selected_entries.append((g2['path'],empty))
 if historical:
  path='files/product-input01/'+'f'*32+'.aj02';original=b'explicit historical unknown byte prefix';wanted['unselectedHistoricalJournals']=[{'path':path,'bytes':len(original),'sha256':sha(original)}];selected_entries.append((path,original[:-1]+b'X'if tamper_historical else original))
 native=tar(selected_entries+([]if native_extra is None else[(native_extra,b'extra')]),dirs=['files/','files/product-input01/'],bad_type=bad_type)
 if pending_mismatch:wanted['unresolvedIntentSequence']=None if unmatched else 1
 entries=[(raw_path or'raw/frame.bin',b'original frame'),('product/journal/mock.ajz01',b'explicit-byte-fixture-not-semantic-proof'),('root-management/seal.json',b'{"fixture":true}')];body={'format':'aeris-betasim-closed-raw-manifest','version':1,'context':C,'sourceCandidateSHA256':candidate,'authorityRestorable':False,'allOriginalRawAndAPStateIncluded':True,'productSemanticAndMediaIncluded':True,'files':[{'path':p,'bytes':len(b),'sha256':sha(b)}for p,b in entries],'totalOriginalBytes':sum(len(b)for _,b in entries),'nativeClosedFiles':{'journal':wanted,'export':{'bytes':len(native),'sha256':sha(native)}}};compressed=gzip.compress(tar([('closed-raw-manifest.json',encode(body)),*entries]),mtime=0);bundle,bp=parts(compressed);bundle['encoding']='TAR_GZIP_LOSSLESS';ns,np=parts(native);ns['encoding']='TAR_UNCOMPRESSED_ORIGINAL';manifest={**body,'bundle':bundle,'nativeStream':ns,'manifestKind':'SOURCE_CLOSED_RAW_EXPORT_NOT_INDEPENDENT_ACCEPTANCE'};return encode(manifest),bp,np
class Fragment(io.BytesIO):
 def read(self,n=-1):
  assert 0<=n<=65536,'no unbounded recipientread'
  return super().read(min(n,17))
def openers(parts,tracker):
 result=[]
 for b in parts:
  @contextlib.contextmanager
  def one(data=b):
   tracker['opened']+=1
   with Fragment(data)as stream:
    try:yield stream
    finally:tracker['closed']+=1
  result.append(one)
 return result
def run(name,value,*,expect=True,context=C,cand=candidate,wrong_manifest_sha=False):
 raw,bp,np=value;tracker={'opened':0,'closed':0}
 try:r=m.verify_recipient(raw,manifest_sha='f'*64 if wrong_manifest_sha else sha(raw),expected_context=context,expected_candidate=cand,bundle_openers=openers(bp,tracker),native_openers=openers(np,tracker));accepted=True;error=None
 except BaseException as e:r=None;accepted=False;error=str(e)
 checks.append({'id':name,'pass':accepted==expect and tracker['opened']==tracker['closed'],'accepted':accepted,'error':error,'managers':tracker,'result':r})
run('valid-fragmented-two-stream-allparts-exact-files-and-AJ02',fixture())
raw,bp,np=fixture();run('missing-native-part-refused',(raw,bp,np[:-1]),expect=False)
run('wrong-context-refused',fixture(),expect=False,context={**C,'boot':'foreign'})
run('wrong-candidate-refused',fixture(),expect=False,cand='f'*64)
run('wrong-original-manifestSHA-refused',fixture(),expect=False,wrong_manifest_sha=True)
raw,bp,np=fixture();run('recipient-native-part-tamper-refused',(raw,bp,[np[0][:-1]+bytes([np[0][-1]^1]),*np[1:]]),expect=False)
raw,bp,np=fixture();run('recipient-compressed-part-truncation-refused',(raw,[bp[0][:-1],*bp[1:]],np),expect=False)
run('raw-traversal-path-refused',fixture(raw_path='../escape'),expect=False)
run('native-foreign-namespace-refused-even-when-containers-rehashed',fixture(native_extra='outside/private-key'),expect=False)
run('native-symlink-type-refused',fixture(bad_type=tarfile.SYMTYPE),expect=False)
run('native-unmatched-intent-keptUNKNOWN-with-exact-source-state',fixture(unmatched=True))
run('native-pending-mismatch-refused-not-promoted-to-known-outcome',fixture(unmatched=True,pending_mismatch=True),expect=False)
run('two-selected-generations-firstactual-inputs-plus-valid-empty-current-g2',fixture(two_generations=True))
run('valid-current-g2-alone-cannot-certify-missing-selected-g1',fixture(two_generations=True,omit_g1=True),expect=False)
run('tampered-g1-not-hidden-by-valid-g2-and-rehashed-native-container',fixture(two_generations=True,tamper_g1=True),expect=False)
run('unselected-historical-original-byte-SHA-preserved-not-decoded-as-known-success',fixture(two_generations=True,historical=True))
run('unselected-historical-byte-tamper-refused-with-rehashed-container',fixture(two_generations=True,historical=True,tamper_historical=True),expect=False)
report={'format':'aeris-independent-Python-joint-SAF-recipient-fixtures','version':1,'status':'PASS_FRAGMENTED_BYTE_RECEIVER_NOT_ACTUAL_SAF'if all(c['pass']for c in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'sourceChanged':pin!=sha(source.read_bytes()),'checks':checks,'actualSAFAndroidSourceOrECDSA':False,'sourceDrainReferences':'EXPLICIT_INJECTED_QA_STUBS','fileExtractionOrWrites':False};n=1;out=REPO/'evidence/betasim-integrated01/qa'
while(out/f'saf-recipient-{n:02}.json').exists():n+=1
p=out/f'saf-recipient-{n:02}.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'failed':[c for c in checks if not c['pass']],'groups':len(checks),'path':str(p)}))
