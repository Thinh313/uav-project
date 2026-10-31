"""Independent effective beforeReceipt validation. Fake read-only ADB only."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,os,sys,tempfile,types
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[1];G=R/'planning/beta06g12';E=R/'evidence/beta06-heartbeat13fix'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
roots=[R/'pilot/heartbeat13fix',P,E]
files=[p for root in roots if root.exists()for p in root.rglob('*')if p.is_file()]
assert len(files)+8<=128 and sum(p.stat().st_size for p in files)+512*2**10<=16*2**20
frozen=json.loads((R/'evidence/beta06/generation12/native-helper-freeze01.json').read_bytes())
oldpath=G/'qa-device-actions.py';newpath=P/'qa-device-actions.py'
assert sha(oldpath)==frozen['files'][str(oldpath.relative_to(R))]
b=load('g12_native_writer',G/'qa-native-budget.py');old=load('qa_snapshot_old',oldpath)
original_spec=importlib.util.spec_from_file_location
def spec(name,path,*a,**kw):
 if Path(path)==P/'qa-android.py':path=G/'qa-android.py'
 return original_spec(name,path,*a,**kw)
with patch.object(importlib.util,'spec_from_file_location',side_effect=spec):new=load('qa_snapshot_candidate',newpath)
assert old.b is new.b is b
baseline=json.loads((R/old.G3_BASELINE).read_bytes());journal=(R/baseline['journalFile']).read_bytes()
assert hashlib.sha256(journal).hexdigest()==baseline['journalSha256']
boot='11111111-2222-3333-4444-555555555555';native='/data/user/0/vn.rtr.aeris.field02/files/field02';cases=[];removed=[]
scratch=P/'qa-scratch';scratch.mkdir(exist_ok=True)
def one(module,kind):
 writes=[];reads=[];result=None;failure=None;cwd=Path.cwd()
 with tempfile.TemporaryDirectory(prefix='codex-tmp-qa-heartbeat13fix-20261023-',dir=scratch)as temp:
  root=Path(temp);out=root/'evidence/beta06/after';out.mkdir(parents=True)
  jp=root/'evidence/beta06/prior-journal.jsonl';jp.write_bytes(journal)
  before=root/'evidence/beta06/before.json';body={**baseline,'guestBootId':boot,'journalFile':str(jp.relative_to(root))};before.write_text(json.dumps(body))
  selected=before
  if kind=='outside':selected=root/'outside.json';selected.write_text(json.dumps(body))
  elif kind=='symlink':selected=before.with_name('link.json');selected.symlink_to(before)
  elif kind=='malformed-json':before.write_text('{')
  elif kind=='malformed-shape':before.write_text('{}')
  elif kind=='oversized':before.write_bytes(b' '* (128*2**10+1))
  supplied=str(selected.relative_to(root))if kind=='relative'else str(selected)
  def adb(*args,**kw):
   reads.append(list(args))
   if args==('shell','cat','/proc/sys/kernel/random/boot_id'):return boot.encode()
   if args[:2]==('shell','find'):return ''.join(h+'  '+p+'\n'for p,h in baseline['files'].items()).encode()
   if args==('exec-out','cat',native+'/journal.jsonl'):return journal
   raise AssertionError('UNDECLARED_FAKE_ADB')
  q=types.SimpleNamespace(R=root,E=out,P='vn.rtr.aeris.field02',owned=lambda attempt:{'pid':12345},adb=adb)
  def sink_bytes(path,value,**kw):
   assert Path(path).is_relative_to(out)and not Path(path).exists()and len(value)<=kw.get('maximum',128*2**10)
   Path(path).write_bytes(value);writes.append({'kind':'journal','bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()})
  def sink_json(path,value,**kw):
   raw=(json.dumps(value,allow_nan=False)+'\n').encode();assert len(raw)<=128*2**10
   Path(path).write_bytes(raw);writes.append({'kind':'receipt','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  try:
   os.chdir(root)
   with patch.object(module,'q',q),patch.object(b,'write_bytes',side_effect=sink_bytes),patch.object(b,'write_json',side_effect=sink_json),contextlib.redirect_stdout(io.StringIO()):
    try:result=module.run('24','store-after','qa',before_receipt=supplied)
    except Exception as exc:failure=type(exc).__name__+':'+str(exc)
  finally:os.chdir(cwd)
  if module is old:passed=bool(failure and [x['kind']for x in writes]==['journal'])
  elif kind in ['absolute','relative']:
   passed=bool(result and not failure and result['beforeReceipt']=='evidence/beta06/before.json'and result['journalPrefixIdentical']and result['journalAppendBytes']==0 and [x['kind']for x in writes]==['journal','receipt'])
  else:passed=bool(failure and not writes)
  cases.append({'module':'frozenG12'if module is old else'prototype','input':kind,'pass':passed,'failure':failure,'writes':writes,'fakeADBReads':len(reads),'requiredOutcome':'Old relative-path partial-journal failure retained as witness'if module is old else'Complete bounded snapshot'if kind in ['absolute','relative']else'Refuse before any afterjournal or receipt write'})
  removed.append(str(root.relative_to(R)))
 assert not root.exists()
one(old,'relative')
for kind in ['absolute','relative','outside','symlink','malformed-json','malformed-shape','oversized']:one(new,kind)
scratch.rmdir();assert sha(oldpath)==frozen['files'][str(oldpath.relative_to(R))]
report={'status':'PASS_QA_EFFECTIVE_SNAPSHOT_PREVALIDATION_MOCK_ONLY'if all(c['pass']for c in cases)else'FAIL_QA_EFFECTIVE_SNAPSHOT_PREVALIDATION_MOCK_ONLY','cases':cases,'groups':len(cases),'source':{'original':str(oldpath.relative_to(R)),'originalSha256':sha(oldpath),'candidate':str(newpath.relative_to(R)),'candidateSha256':sha(newpath),'qaRecipeSha256':sha(Path(__file__))},'sharedDependencies':['Exact frozenG12 writer preloaded; sinks patched explicitly','Candidate sibling qa-android import redirected in test only to exact frozenG12','Real immutableG4 baseline journal and candidate chain/prefix predicates'],'scratchRemoved':removed,'allScratchRemoved':all(not(R/p).exists()for p in removed),'actualADBOrNetwork':False,'G12Edited':False,'limits':'Synthetic effective path/report test only, not actual Native persistence or complete after-snapshot evidence. Old actual partial artifact remains immutable.'}
E.mkdir(exist_ok=True);out=E/('qa-snapshot-paths'+(sys.argv[1]if sys.argv[1:]else'01')+'.json')
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'path':str(out.relative_to(R)),'sha256':sha(out),'status':report['status'],'failed':[c['input']for c in cases if not c['pass']]}))
