"""Cross-language original-byte/index replay. Host-JVM fixtures, not Android."""
from pathlib import Path
import base64,copy,hashlib,io,json,os,shutil,subprocess,struct,sys,tarfile,tempfile,unittest
HERE=Path(__file__).resolve().parent;P=HERE.parent;sys.path.insert(0,str(P));import receiver17 as r;from archive_verifier17 import verify_archive_index
JAVA='/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/java'
class Archive(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='archive-fixture-');self.addCleanup(self.tmp.cleanup);base=Path(self.tmp.name);orig=[{'generation':f'{i:032x}','bytes':23,'sha256':r.sha(r.MAGIC),'disposition':'UNUSED','proofSHA256':'a'*64,'records':0,'sourceClosedStatusBound':False}for i in range(1,9)];self.report=(json.dumps({'format':'aeris-journal17-independent-full-byte-receiver','version':1,'status':'COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT','package':r.PACKAGE,'oldAPKSHA256':'a'*64,'oldSourceSHA256':'b'*64,'newSourceSHA256':'c'*64,'backupSHA256':'d'*64,'backupBytes':10240,'coldProofSHA256':'f'*64,'expectedHostRegistryHead':'ROOT','originals':orig,'authorityRestorable':False,'modelOnly':True},sort_keys=True,separators=(',',':'))+'\n').encode();self.reports={r.sha(self.report):self.report};self.base=base
 def fixture(self,unclosed=False,initial_only=False):
  args=[JAVA,'-Xmx128m','-cp',os.environ.get('NATIVE17_QA_CLASSES',str(HERE/'host-classes')),'RegistryReplayFixture17',str(self.base),r.sha(self.report)]+(['initial-only']if initial_only else ['unclosed']if unclosed else[]);q=subprocess.run(args,capture_output=True,timeout=30);self.assertEqual(q.returncode,0,q.stderr.decode());out=json.loads(q.stdout);self.root=Path(out['root']);self.anchor=out['anchor'];self.plan=out['planSHA256'];tar=self.base/'native-model.tar'
  with tarfile.open(tar,'w',format=tarfile.USTAR_FORMAT)as t:t.add(self.root,arcname='files',recursive=True,filter=lambda member:(setattr(member,'uid',0)or setattr(member,'gid',0)or member))
  return r.native_tar(tar,r.sha(tar.read_bytes()),allow_empty_active=True)
 def verify(self,scan,**kw):return verify_archive_index(scan,self.anchor,source_candidate='a'*64,archive_receivers=self.reports,**kw)
 def append_model(self,scan,mutation=None):
  g=f'{9:032x}';name='files/product-input01/'+g+'.aj02';raw=r.MAGIC;prior=bytes(32);rows=[]
  for seq,clock,kind,payload in ((1,100,1,b'{}'),(2,101,2,b'200')):
   body=struct.pack('!QQB',seq,clock,kind)+prior+payload;head=hashlib.sha256(body).digest();row=struct.pack('!I',len(body)+32)+body+head;rows.append((row,head.hex(),clock));raw+=row;prior=head
  index='files/product-input-registry17/highwater.aj17';old=scan['inputOriginals'][index];records=[]
  for line in old.splitlines()[1:]:
   v=line.decode().split('\t');records.append([v[2],base64.b64decode(v[3]).decode().split('\t')])
  head='0'*64;encoded=old.splitlines()[0]+b'\n';ordinal=0
  def emit(kind,f):
   nonlocal head,encoded,ordinal
   ordinal+=1;p=base64.b64encode('\t'.join(f).encode()).decode();prefix='\t'.join([str(ordinal),head,kind,p]);head=r.sha(prefix.encode());encoded+=(prefix+'\t'+head+'\n').encode();return head
  for kind,f in records:
   if kind in('ENROLL_COMMIT','GEN_COMMIT','APPEND_COMMIT','ARCHIVE_COMMIT'):f[0]=head
   if kind=='CLOSE'and f[0]==g:f=[g,'2',str(len(raw)),prior.hex(),'CLOSED_VERIFIED',r.sha(raw),'0'*64]
   emit(kind,f)
   if kind=='GEN_COMMIT'and f[1]==g:
    before=len(r.MAGIC)
    for at,(row,h,clock)in enumerate(rows,1):
     ticket=emit('APPEND_BEGIN',[g,str(at),str(before),str(before+len(row)),('f'*64 if mutation=='rowSHA'and at==1 else r.sha(row)),h]);emit('APPEND_COMMIT',[ticket,str(clock+1 if mutation=='elapsed'and at==1 else clock),str(at%2)]);before+=len(row)
  scan['inputOriginals'][index]=encoded;scan['inputOriginals'][name]=raw
  for n in(index,name):scan['files'][n]={'bytes':len(scan['inputOriginals'][n]),'sha256':r.sha(scan['inputOriginals'][n])}
  self.anchor=head;return scan
 def test_original_append_row_positive(self):
  proof=self.verify(self.append_model(self.fixture()),require_selected_closed=[f'{9:032x}']);self.assertEqual(proof['counters']['committedRecords'],2)
 def test_wrong_original_append_whole_row_sha(self):
  with self.assertRaisesRegex(ValueError,'APPEND_ORIGINAL_RANGE_SHA'):self.verify(self.append_model(self.fixture(),'rowSHA'))
 def test_wrong_original_append_elapsed(self):
  with self.assertRaisesRegex(ValueError,'APPEND_ORIGINAL_ROW_BINDING'):self.verify(self.append_model(self.fixture(),'elapsed'))
 def test_archive_manifest_member_must_equal_index_reservation(self):
  scan=self.fixture();index='files/product-input-registry17/highwater.aj17';head='0'*64;out=scan['inputOriginals'][index].splitlines()[0]+b'\n'
  for ordinal,line in enumerate(scan['inputOriginals'][index].splitlines()[1:],1):
   v=line.decode().split('\t');kind=v[2];f=base64.b64decode(v[3]).decode().split('\t')
   if kind=='ARCHIVE_BEGIN':f[6]='d'*64
   # Parent transaction references must follow the changed original intent hash.
   if kind in('ENROLL_COMMIT','GEN_COMMIT','APPEND_COMMIT','ARCHIVE_COMMIT'):f[0]=head
   prefix='\t'.join([str(ordinal),head,kind,base64.b64encode('\t'.join(f).encode()).decode()]);head=r.sha(prefix.encode());out+=(prefix+'\t'+head+'\n').encode()
  scan['inputOriginals'][index]=out;self.anchor=head
  with self.assertRaisesRegex(ValueError,'PLAN_EXACT_MEMBER_JOIN'):self.verify(scan)
 def test_jvm_full_archive_and_two_explicit_unused_closes(self):
  scan=self.fixture();proof=self.verify(scan,require_selected_closed=[f'{9:032x}',f'{10:032x}']);self.assertEqual(proof['archivedJournals'],8);self.assertEqual(proof['activeJournals'],2);self.assertEqual(proof['counters']['reservedGenerations'],10);self.assertEqual(proof['counters']['committedRecords'],0);self.assertEqual(proof['counters']['reservedRequests'],1);self.assertFalse(proof['flightAcceptance'])
 def test_absent_selected_generation_refused(self):
  with self.assertRaisesRegex(ValueError,'EXACT_SELECTED_CLOSE_GENERATIONS'):self.verify(self.fixture(),require_selected_closed=['e'*32])
 def test_duplicate_selected_generation_refused(self):
  with self.assertRaisesRegex(ValueError,'EXACT_SELECTED_CLOSE_GENERATIONS'):self.verify(self.fixture(),require_selected_closed=[f'{9:032x}',f'{9:032x}'])
 def test_new_unused_open_cannot_infer_close(self):
  scan=self.fixture(True)
  with self.assertRaisesRegex(ValueError,'SELECTED_ORIGINAL_CLOSE_REQUIRED'):self.verify(scan,require_selected_closed=[f'{10:032x}'])
 def test_whole_batch_removal_refused(self):
  scan=self.fixture();scan['inputOriginals']={n:b for n,b in scan['inputOriginals'].items()if not n.startswith('files/product-input-archives17/')}
  with self.assertRaises(ValueError):self.verify(scan)
 def test_missing_index_no_fresh_reset(self):
  scan=self.fixture();scan['inputOriginals'].pop('files/product-input-registry17/highwater.aj17')
  with self.assertRaisesRegex(ValueError,'REGISTRY_REQUIRED'):self.verify(scan)
 def test_torn_index_refused(self):
  scan=self.fixture();name='files/product-input-registry17/highwater.aj17';scan['inputOriginals'][name]=scan['inputOriginals'][name][:-1]
  with self.assertRaisesRegex(ValueError,'REGISTRY_REQUIRED'):self.verify(scan)
 def test_foreign_external_head_refused(self):
  scan=self.fixture();self.anchor='f'*64
  with self.assertRaisesRegex(ValueError,'EXTERNAL_HOST_HEAD'):self.verify(scan)
 def test_zero_external_head_is_not_an_observed_anchor(self):
  scan=self.fixture();self.anchor='0'*64
  with self.assertRaisesRegex(ValueError,'EXTERNAL_HOST_HEAD'):self.verify(scan)
 def test_deleted_admin_receipt_cannot_refund(self):
  scan=self.fixture();name=next(n for n in scan['inputOriginals']if '/request-'in n);scan['inputOriginals'].pop(name)
  with self.assertRaisesRegex(ValueError,'RECEIPT_MISSING'):self.verify(scan)
 def test_manifest_corruption_even_header_journals_refused(self):
  scan=self.fixture();name=next(n for n in scan['inputOriginals']if '/intent-'in n);scan['inputOriginals'][name]+=b'x'
  with self.assertRaisesRegex(ValueError,'MANIFEST_ANCHOR'):self.verify(scan)
 def test_missing_independent_receiver_original_refused(self):
  scan=self.fixture();self.reports={}
  with self.assertRaisesRegex(ValueError,'RECEIVER_ORIGINALS'):self.verify(scan)
 def test_root_initial_receiver_still_refuses_zero_active(self):
  scan=self.fixture(initial_only=True);self.assertEqual(len(scan['journals']),0);self.assertEqual(self.verify(scan)['archivedJournals'],8)
  tar=self.base/'native-model.tar'
  with self.assertRaisesRegex(ValueError,'ACTIVE_GENERATION'):r.native_tar(tar,r.sha(tar.read_bytes()))
if __name__=='__main__':unittest.main(verbosity=2)
