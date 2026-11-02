"""Independent pure-Python wire adversaries. No TAR/device/process/fixture writes.
The positive is a structural index/byte model, not signed native actor evidence.
"""
from pathlib import Path
import base64,hashlib,json,struct,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(P))
import archive_verifier17 as verifier
H=lambda b:hashlib.sha256(b).hexdigest();MAGIC=b'AERIS_INPUT_JOURNAL_V2\n';ZERO='0'*64

def corpus(*,bad_row=False,bad_elapsed=False,bad_plan=False):
 head=ZERO;records=[]
 def row(kind,fields):
  nonlocal head
  payload=base64.b64encode('\t'.join(fields).encode()).decode();prefix=f'{len(records)+1}\t{head}\t{kind}\t{payload}'.encode();head=H(prefix);records.append(prefix+b'\t'+head.encode()+b'\n');return head
 originals=[dict(generation=f'{i:032x}',bytes=23,sha256=H(MAGIC),disposition='UNUSED',proofSHA256='d'*64)for i in range(1,9)]
 report=dict(format='aeris-journal17-independent-full-byte-receiver',version=1,status='COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT',package='vn.rtr.aeris.betasim09',oldAPKSHA256='a'*64,oldSourceSHA256='b'*64,newSourceSHA256='c'*64,backupSHA256='d'*64,backupBytes=10240,coldProofSHA256='f'*64,expectedHostRegistryHead='ROOT',originals=[dict(o,records=0,sourceClosedStatusBound=False)for o in originals],authorityRestorable=False,mockOnly=True)
 report=json.dumps(report,separators=(',',':')).encode();receiver=H(report)
 plan=['AERIS_JOURNAL_LIFECYCLE17\t1','package\tvn.rtr.aeris.betasim09','oldAPK\t'+'a'*64,'oldSource\t'+'b'*64,'newSource\t'+'c'*64,'backup\t'+'d'*64+'\t10240','receiver\t'+receiver,'cold\t'+'f'*64,'expectedHead\tROOT']
 for i,o in enumerate(originals):plan.append('generation\t'+(f'{100:032x}'if bad_plan and i==0 else o['generation'])+'\t23\t'+o['sha256']+'\tUNUSED\t'+o['proofSHA256'])
 plan=('\n'.join(plan+['end',''])).encode();plan_sha=H(plan)
 def group(fields):
  for o in originals:fields.extend([o['generation'],'23',o['sha256'],'UNUSED',o['proofSHA256']])
  return fields
 intent=row('ENROLL_BEGIN',group(['a'*64,'b'*64,'c'*64,'8']));fields=[intent]
 for i,o in enumerate(originals):fields.extend([o['generation'],'1',str(i+1)])
 row('ENROLL_COMMIT',fields);nonce=f'{999:032x}';request=row('REQUEST_RESERVE',[nonce,'APPLY','1']);intent=row('ARCHIVE_BEGIN',group([plan_sha,'8']));archive='files/product-input-archives17/'+plan_sha+'/';commit=('AERIS_JOURNAL17_COMMITTED\t'+plan_sha+'\t'+receiver+'\n').encode()
 row('ARCHIVE_COMMIT',[intent,'product-input-archives17/'+plan_sha,'intent-0.record',plan_sha,str(len(plan)),'commit-0.record',H(commit),str(len(commit))]);receipt=b'{"mockOnly":true}';receipt_path='product-input-lifecycle17/request-'+nonce+'.json';row('REQUEST_RECEIPT',[request,nonce,receipt_path,str(len(receipt)),H(receipt)])
 generation=f'{9:032x}';intent=row('GEN_BEGIN',[generation]);row('GEN_COMMIT',[intent,generation,'23',ZERO,'1','99']);raw=MAGIC;previous=ZERO
 for sequence,kind,payload,clock in[(1,1,b'{}',10),(2,2,b'200',11)]:
  body=struct.pack('!QQB',sequence,clock,kind)+bytes.fromhex(previous)+payload;body_sha=H(body);new=struct.pack('!I',len(body)+32)+body+bytes.fromhex(body_sha);intent=row('APPEND_BEGIN',[generation,str(sequence),str(len(raw)),str(len(raw)+len(new)),'e'*64 if bad_row and sequence==1 else H(new),body_sha]);raw+=new;row('APPEND_COMMIT',[intent,'9999'if bad_elapsed and sequence==1 else str(clock),'1'if kind==1 else'0']);previous=body_sha
 row('CLOSE',[generation,'2',str(len(raw)),previous,'CLOSED_VERIFIED',H(raw),ZERO]);files={archive+o['generation']+'.aj02':MAGIC for o in originals};files.update({archive+'intent-0.record':plan,archive+'commit-0.record':commit,'files/'+receipt_path:receipt,'files/product-input01/'+generation+'.aj02':raw,'files/product-input-registry17/highwater.aj17':b'AERIS_JOURNAL_REGISTRY17_V1\n'+b''.join(records)})
 scan=dict(inputOriginals=files,files={n:dict(bytes=len(b),sha256=H(b))for n,b in files.items()},tarSHA256='f'*64,inputBytes=sum(map(len,files.values())))
 return scan,head,{receiver:report},generation

def archived_closed_claim(scan,head,reports,generation):
 """Add a structurally exact used archive with JSON assertion, no raw P256 proof."""
 files=scan['inputOriginals'];name='files/product-input-registry17/highwater.aj17';rows=files[name][len(verifier.INDEX_MAGIC):].splitlines(keepends=True)
 def record(kind,f):
  nonlocal head
  prefix=f'{len(rows)+1}\t{head}\t{kind}\t'+base64.b64encode('\t'.join(f).encode()).decode();head=H(prefix.encode());rows.append(prefix.encode()+b'\t'+head.encode()+b'\n');return head
 raw=files['files/product-input01/'+generation+'.aj02'];o=dict(generation=generation,bytes=len(raw),sha256=H(raw),disposition='CLOSED_VERIFIED',proofSHA256='9'*64)
 report=dict(format='aeris-journal17-independent-full-byte-receiver',version=1,status='COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT',package='vn.rtr.aeris.betasim09',oldAPKSHA256='a'*64,oldSourceSHA256='b'*64,newSourceSHA256='c'*64,backupSHA256='d'*64,backupBytes=10240,coldProofSHA256='f'*64,expectedHostRegistryHead=head,originals=[dict(o,records=2,sourceClosedStatusBound=True)],authorityRestorable=False,mockOnly=True)
 report=json.dumps(report,separators=(',',':')).encode();receiver=H(report);plan=('\n'.join(['AERIS_JOURNAL_LIFECYCLE17\t1','package\tvn.rtr.aeris.betasim09','oldAPK\t'+'a'*64,'oldSource\t'+'b'*64,'newSource\t'+'c'*64,'backup\t'+'d'*64+'\t10240','receiver\t'+receiver,'cold\t'+'f'*64,'expectedHead\t'+head,'generation\t'+generation+'\t'+str(len(raw))+'\t'+H(raw)+'\tCLOSED_VERIFIED\t'+'9'*64,'end',''])).encode();ph=H(plan)
 nonce=f'{888:032x}';request=record('REQUEST_RESERVE',[nonce,'APPLY','0']);intent=record('ARCHIVE_BEGIN',[ph,'1',generation,str(len(raw)),H(raw),'CLOSED_VERIFIED','9'*64]);relative='product-input-archives17/'+ph;commit=('AERIS_JOURNAL17_COMMITTED\t'+ph+'\t'+receiver+'\n').encode();record('ARCHIVE_COMMIT',[intent,relative,'intent-0.record',ph,str(len(plan)),'commit-0.record',H(commit),str(len(commit))]);receipt=b'{"mockOnly":true}';rp='product-input-lifecycle17/request-'+nonce+'.json';record('REQUEST_RECEIPT',[request,nonce,rp,str(len(receipt)),H(receipt)])
 files.pop('files/product-input01/'+generation+'.aj02');files.update({'files/'+relative+'/'+generation+'.aj02':raw,'files/'+relative+'/intent-0.record':plan,'files/'+relative+'/commit-0.record':commit,'files/'+rp:receipt,name:verifier.INDEX_MAGIC+b''.join(rows)});scan.update(files={n:dict(bytes=len(b),sha256=H(b))for n,b in files.items()},inputBytes=sum(map(len,files.values())));reports[receiver]=report
 return scan,head,reports,generation

def main():
 before={p.name:H(p.read_bytes())for p in [P/'archive_verifier17.py',P/'receiver17.py']};out=[]
 for name,flags,expected in [('POSITIVE_MATCHING_STRUCTURAL_BYTES',{},None),('ZERO_GENESIS_ANCHOR',{},'EXTERNAL_HOST_HEAD_REQUIRED'),('WRONG_DECLARED_APPEND_ROW_SHA',{'bad_row':True},'APPEND_ORIGINAL_RANGE_SHA'),('WRONG_APPEND_COMMIT_ELAPSED',{'bad_elapsed':True},'APPEND_ORIGINAL_ROW_BINDING'),('PLAN_MEMBER_DIFFERS_FROM_RESERVATION',{'bad_plan':True},'ORIGINAL_ARCHIVE_PLAN_EXACT_MEMBER_JOIN'),('ARCHIVED_CLOSED_RECEIVER_JSON_WITHOUT_RAW_STATUS_P256',{'archived_closed':True},'ARCHIVED_USED_RAW_STATUS_P256_PROOF_DEFERRED')]:
  closed=flags.pop('archived_closed',False);scan,head,reports,generation=corpus(**flags)
  if closed:scan,head,reports,generation=archived_closed_claim(scan,head,reports,generation)
  try:
   proof=verifier.verify_archive_index(scan,ZERO if name=='ZERO_GENESIS_ANCHOR'else head,source_candidate='a'*64,archive_receivers=reports,require_selected_closed=[generation])
   if expected is not None:raise AssertionError(name+' was falsely accepted')
   assert proof['counters']['committedRecords']==2 and proof['counters']['reservedRequests']==1 and proof['flightAcceptance']is False
   assert proof.get('selectedCloseProofScope')=='INDEX_CLOSE_AND_ORIGINAL_AJ02_ONLY_REQUIRES_SEPARATE_SIGNED_STATUS_PROOF'
   out.append(dict(case=name,result='PASS_POSITIVE_STRUCTURAL_SCOPE_ONLY'))
  except ValueError as e:
   if expected is None or expected not in str(e):raise
   out.append(dict(case=name,result='PASS_SPECIFIC_REFUSAL',reason=str(e)))
 after={p.name:H(p.read_bytes())for p in [P/'archive_verifier17.py',P/'receiver17.py']};assert before==after,'source changed during independent review'
 print(json.dumps(dict(format='aeris-independent-mirror-bites17',cases=out,sourceSHA256=before,sourceUnchangedDuringRun=True,scope='PURE_PYTHON_SYNTHETIC_ORIGINAL_BYTES_NO_ACTORS_NO_FILESYSTEM_FIXTURES',notNativeStatusOrSignatureAcceptance=True,persistentFixtureDataWritten=False),separators=(',',':')))
if __name__=='__main__':main()
