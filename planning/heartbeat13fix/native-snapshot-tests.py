"""Effective snapshot-path prototype tests. Fake read-only ADB; no device/runtime."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,os,sys,tempfile,types
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];G=R/'planning/beta06g12';E=R/'evidence/beta06-heartbeat13fix'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
frozen=json.loads((R/'evidence/beta06/generation12/native-helper-freeze01.json').read_bytes());original=G/'qa-device-actions.py';candidate=P/'qa-device-actions.py';assert H(original)==frozen['files'][str(original.relative_to(R))]
b=load('g12_native_writer',G/'qa-native-budget.py');old=load('heartbeat_snapshot_old',original)
spec_original=importlib.util.spec_from_file_location
def exact_dependency(name,path,*a,**kw):
 if Path(path)==P/'qa-android.py':path=G/'qa-android.py'
 return spec_original(name,path,*a,**kw)
with patch.object(importlib.util,'spec_from_file_location',side_effect=exact_dependency):new=load('heartbeat_snapshot_candidate',candidate)
assert old.b is new.b is b
baseline=json.loads((R/old.G3_BASELINE).read_bytes());journal=(R/baseline['journalFile']).read_bytes();boot='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';native_root='/data/user/0/vn.rtr.aeris.field02/files/field02';cases=[];scratch=[]
assert hashlib.sha256(journal).hexdigest()==baseline['journalSha256']
def one(module,form,expect,*,fail_write=False):
 before_cwd=Path.cwd();result=None;failure=None;writes=[];reads=[]
 with tempfile.TemporaryDirectory(prefix='codex-tmp-heartbeat13fix-20261023-',dir=P)as tmp:
  root=Path(tmp);scratch.append(root);out=root/'evidence/beta06/mock-snapshot';out.mkdir(parents=True);before=root/'evidence/beta06/before.json';jp=root/'evidence/beta06/mock-before-journal.jsonl';jp.write_bytes(journal);body={**baseline,'guestBootId':boot,'journalFile':str(jp.relative_to(root))};before.write_text(json.dumps(body));outside=root/'outside.json';outside.write_text(json.dumps(body))
  supplied=str(before)if form=='absolute'else str(before.relative_to(root))if form=='relative'else str(outside)
  def adb(*args,**kw):
   reads.append(list(args))
   if args==('shell','cat','/proc/sys/kernel/random/boot_id'):return boot.encode()
   if args[:2]==('shell','find'):return ''.join(h+'  '+n+'\n'for n,h in baseline['files'].items()).encode()
   if args==('exec-out','cat',native_root+'/journal.jsonl'):return journal
   raise AssertionError('UNEXPECTED_FAKE_ADB:'+str(args))
  q=types.SimpleNamespace(R=root,E=out,P='vn.rtr.aeris.field02',owned=lambda attempt:{'pid':12345},adb=adb)
  def write_bytes(path,value,**kwargs):
   p=Path(path);assert p.is_relative_to(out)and not p.exists()and len(value)<=kwargs.get('maximum',128*2**10)
   p.write_bytes(value);writes.append({'kind':'journal','bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()})
  def write_json(path,value,**kwargs):
   if fail_write:raise OSError('INJECTED_FINAL_METADATA_WRITE_FAILURE')
   raw=(json.dumps(value,allow_nan=False)+'\n').encode();assert len(raw)<=128*2**10;Path(path).write_bytes(raw);writes.append({'kind':'receipt','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  try:
   os.chdir(root)
   with patch.object(module,'q',q),patch.object(b,'write_bytes',side_effect=write_bytes),patch.object(b,'write_json',side_effect=write_json),contextlib.redirect_stdout(io.StringIO()):
    try:result=module.run('24','store-after','mock',before_receipt=supplied)
    except Exception as exc:failure=type(exc).__name__+':'+str(exc)
   if expect=='old':assert failure and 'relative' in failure and [x['kind']for x in writes]==['journal']
   elif expect=='outside':assert failure and 'MATCHED_REGULAR_BOUNDED_BEFORE_SNAPSHOT_REQUIRED'in failure and not writes
   elif expect=='writer':assert failure and 'INJECTED_FINAL_METADATA_WRITE_FAILURE'in failure and [x['kind']for x in writes]==['journal']
   else:
    assert failure is None and result['beforeReceipt']=='evidence/beta06/before.json'and result['journalPrefixIdentical']and result['oldArtifactShaUnchanged']and result['journalAppendBytes']==0 and result['fileCount']==19
    assert [x['kind']for x in writes]==['journal','receipt'];assert result['sameKnownGuestBoot']is True
   cases.append({'module':'original'if module is old else'candidate','form':form,'expected':expect,'pass':True,'failure':failure,'writes':writes,'readOnlyADBCalls':len(reads),'beforeReceipt':result.get('beforeReceipt')if result else None})
  finally:os.chdir(before_cwd)
 assert not root.exists()
one(old,'relative','old');one(new,'absolute','success');one(new,'relative','success');one(new,'outside','outside');one(new,'absolute','writer',fail_write=True)
assert all(not p.exists()for p in scratch);assert H(original)==frozen['files'][str(original.relative_to(R))]
E.mkdir(exist_ok=True);paths=list(E.rglob('*'));assert len(paths)+1<=128 and sum(p.stat().st_size for p in paths if p.is_file())+128*2**10<=16*2**20
report={'status':'PASS_SNAPSHOT_PATH_PROTOTYPE_EFFECTIVE_MOCK_ONLY','cases':cases,'groups':len(cases),'source':{'original':str(original.relative_to(R)),'originalSha256':H(original),'candidate':str(candidate.relative_to(R)),'candidateSha256':H(candidate),'writerSha256':H(G/'qa-native-budget.py'),'testSha256':H(Path(__file__))},'loading':'Preloaded exact frozen G12 writer; candidate missing-sibling spec redirected in test only to exact frozen G12 qa-android.py. Both effective modules run with explicitly injected fake read-only ADB and bounded file sinks. Real journal-chain/native-prefix predicates use immutable G4 baseline bytes.','scratchCleanup':{'removed':len(scratch),'names':[p.name for p in scratch],'allRemovedIncludingInjectedFailure':True},'unchangedSourceG12':True,'actualADBCalls':0,'runtimeEffects':False,'noRetry':True,'limits':'Path/report regression only, not actual Android snapshot/persistence proof. Injection after journal write deliberately leaves modeled partial evidence until own scratch cleanup; live artifacts must remain retained, never retried.'}
out=E/'native-snapshot01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(cases),'sha256':H(out),'receipt':str(out)}))
