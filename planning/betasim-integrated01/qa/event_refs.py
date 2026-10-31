"""Independent real-R02 payload / durable detail / cold pre-export prefix tests.
Only own mock-budget files; no process, Android, Docker, AP or runtime retry.
"""
from pathlib import Path
import sys,os,json,hashlib,shutil,types,io,tarfile,time,gzip
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
from aeris_runtime.product_runtime import WorkbenchRuntime,event_original_files
from aeris_runtime.metadata_budget import MetadataBudget,encoded
E=R/'evidence/betasim-integrated01';LAB=R/'planning/betasim-integrated01/qa/.event-refs-fixture01';assert not LAB.exists();LAB.mkdir();checks=[];H=lambda b:hashlib.sha256(b).hexdigest();paths=['product_runtime.py','metadata_budget.py','raw_export.py'];pins={str((R/'planning/betasim-integrated01/runtime/source/aeris_runtime'/p).relative_to(R)):H((R/'planning/betasim-integrated01/runtime/source/aeris_runtime'/p).read_bytes())for p in paths};sourceRefs=[]
def original_ref(ref):
 p=Path(ref['path']);raw=p.read_bytes()[ref['offset']:ref['offset']+ref['bytes']];assert len(raw)==ref['bytes']and H(raw)==ref['sha256'];return raw
def owner(n):
 root=LAB/n;root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();o=object.__new__(WorkbenchRuntime);o.root=root;o.budget=b;o.events=0;o.digest='a'*64;o.case=None;return o
def deny(fn,code):
 try:fn()
 except BaseException as e:
  assert code in str(e),(code,type(e).__name__,str(e));return
 raise AssertionError('UNEXPECTED_ACCEPT:'+code)
def test(n,fn):
 try:fn();checks.append({'id':n,'pass':True})
 except BaseException as e:checks.append({'id':n,'pass':False,'error':type(e).__name__+':'+str(e)})
try:
 actual=E/'r02/sessions/betasim-short02';backend=(actual/'raw/backend-identity.json').read_bytes();ap=(actual/'raw/ap-supervisor-launch.json').read_bytes()
 for p,b in[(actual/'raw/backend-identity.json',backend),(actual/'raw/ap-supervisor-launch.json',ap)]:sourceRefs.append({'path':str(p.relative_to(R)),'bytes':len(b),'sha256':H(b)})
 queries=[json.loads(x)for x in(actual/'host-queries/queries.jsonl').read_bytes().splitlines()];container=json.loads(original_ref(queries[2]['stdoutRef']))[0];exe=original_ref(queries[3]['stdoutRef']).decode().split()[0]
 receipt={'backendReady':True,'APReady':True,'backend':json.loads(backend),'AP':json.loads(ap),'containerImage':container['Image'],'containerID':container['Id'],'actualAPExecutableSHA256':exe,'backendTiming':{'startHostNs':1000000000,'readyHostNs':16000000000,'gateSeconds':40},'APTiming':{'startHostNs':16000000000,'readyHostNs':17000000000,'gateSeconds':12},'wholeColdStartClaimed10s':False}
 o=owner('real-receipt');oldrow={'format':'aeris-product-runtime-event','version':1,'sequence':1,'hostNs':17000000000,'kind':'ROOT_AP_READY','detail':receipt,'candidateSHA256':o.digest,'flightAcceptance':False}
 def old_fails():
  before=o.budget.snapshot()['writes'];deny(lambda:o.budget.append_json('external_task',o.root/'reports/old.jsonl',oldrow,maximum=8192),'METADATA_JSON_SOURCE_BOUND');assert o.budget.snapshot()['writes']==before
 test('real-original-R02-payload-reproduces-old8192-error-without-writing',old_fails)
 def roundtrip():
  o.event('ROOT_AP_READY',receipt);row=json.loads((o.root/'reports/runtime-events.jsonl').read_bytes());ref=row['detailRef'];raw=(o.root/ref['path']).read_bytes();assert len(encoded(row))<8192< len(raw)<=32768;assert H(raw)==ref['sha256']and len(raw)==ref['bytes'];payload=json.loads(raw);assert payload['detail']==receipt and all(payload[k]==row[k]for k in('hostNs','kind','context','sequence','candidateSHA256'));assert o.budget.snapshot()['runtimeEventDetailAllocatedBytes']>=len(raw);assert event_original_files(o.root,o.digest)==[o.root/'reports/runtime-events.jsonl',o.root/ref['path']]
 test('full-realistic-receipt-lossless-durable-before-small-original-event-ref',roundtrip)
 def cold_mutation(which):
  rowfile=o.root/'reports/runtime-events.jsonl';saved=rowfile.read_bytes();q=json.loads(saved);detail=o.root/q['detailRef']['path'];body=detail.read_bytes()
  try:
   if which=='payload':detail.write_bytes(body[:-1]+b'x');deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_DETAIL_SHA_OR_AGGREGATE')
   elif which=='ref':q['detailRef']['path']='reports/runtime-event-002-detail.json';rowfile.write_bytes(encoded(q));deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_EXACT_DETAIL_REF')
   elif which=='candidate':q['candidateSHA256']='b'*64;rowfile.write_bytes(encoded(q));deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_ROW_SOURCE')
   elif which=='context':q['context']={'run':'incomplete'};rowfile.write_bytes(encoded(q));deny(lambda:event_original_files(o.root,o.digest),'Context.__init__')
   elif which=='orphan':
    orphan=o.root/'reports/runtime-event-099-detail.json';orphan.write_bytes(b'{}')
    try:deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_UNREFERENCED_DETAIL')
    finally:orphan.unlink()
  finally:rowfile.write_bytes(saved);detail.write_bytes(body)
 for kind in ['payload','ref','candidate','context','orphan']:test('cold-original-'+kind+'-mutation-rejected',lambda k=kind:cold_mutation(k))
 def detail_eio():
  q=owner('detail-eio')
  with patch.object(q.budget,'write',side_effect=OSError('QA_DETAIL_EIO')):deny(lambda:q.event('ROOT_AP_READY',receipt),'QA_DETAIL_EIO')
  assert not(q.root/'reports/runtime-events.jsonl').exists()and q.events==1
 test('detail-EIO-cannot-publish-event-ref-or-retry',detail_eio)
 def row_eio():
  q=owner('row-eio')
  with patch.object(q.budget,'append_json',side_effect=OSError('QA_ROW_EIO')):deny(lambda:q.event('ROOT_AP_READY',receipt),'QA_ROW_EIO')
  assert(q.root/'reports/runtime-event-001-detail.json').is_file()and not(q.root/'reports/runtime-events.jsonl').exists();deny(lambda:event_original_files(q.root,q.digest),'EVENT_ORIGINAL_JOURNAL_REQUIRED')
 test('event-EIO-preserves-orphan-detail-but-coldreader-refuses-completeness',row_eio)
 def aggregate():
  q=owner('aggregate');q.budget.write('external_task',q.root/'reports/prefund.json',b'{}');q.budget.write('external_task',q.root/'reports/runtime-event-001-detail.json',b'x'*32768);q.budget.write('external_task',q.root/'reports/runtime-event-002-detail.json',b'x'*32768);assert q.budget.snapshot()['runtimeEventDetailAllocatedBytes']==65536;q.events=2;q.case={'context':{'run':'SECOND_CASE'}};writes=q.budget.snapshot()['writes'];deny(lambda:q.event('SECOND_CASE',{}),'RUNTIME_EVENT_DETAILS_TASK64KiB_ALLOCATED');assert q.budget.snapshot()['writes']==writes and not(q.root/'reports/runtime-events.jsonl').exists()
 test('physical64KiB-source-subcap-no-case-reset-no-new-owner-or-cap',aggregate)
 def oversized():
  q=owner('oversize');deny(lambda:q.event('ROOT_AP_READY',{'x':'x'*32768}),'REPORT_SOURCE_BOUND');assert not(q.root/'reports/runtime-events.jsonl').exists()
 test('original32KiB-detail-input-bound-is-preserved',oversized)
 def prefix_cutoff():
  files=event_original_files(o.root,o.digest);snapshot={str(p.relative_to(o.root)):p.read_bytes()for p in files};o.event('SOURCE_RAW_DRAINED_EXPORT_ALLOWED',{'futureSAF':True});assert len(event_original_files(o.root,o.digest))==len(files)+1;assert json.loads(snapshot['reports/runtime-events.jsonl'])['sequence']==1 and 'runtime-event-002-detail.json'not in' '.join(snapshot);source=(R/'planning/betasim-integrated01/runtime/source/aeris_runtime/raw_export.py').read_text();assert "'rootRuntimeEventScope':'EXACT_PRE_EXPORT_COMMITTED_PREFIX_POST_EXPORT_EVENT_AND_SAF_RECEIPTS_SEPARATE'"in source and"'root-management/'+path.name"in source and'event_original_files(budget.evidence,resources.digest)'in source
 test('cold-export-prefix-excludes-later-event-explicitly-no-self-reference',prefix_cutoff)
 def gzip_prefix():
  from aeris_runtime.resources import OwnedResources
  from aeris_runtime.product_native import ProductNativeProbe
  from aeris_runtime.raw_export import prepare_export
  q=owner('gzip-prefix');q.event('ROOT_AP_READY',receipt);q.budget.tick('cases');context={'run':'qa-event','epoch':'e','boot':'b','operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'};case=q.root/'sessions/qa-event'
  (q.root/'reports/native-producer-01-registration.json').write_bytes(b'{"explicitMockRegistration":true}\n');(q.root/'reports/product-clock-proofs.jsonl').write_bytes(b'{"explicitMockClock":true}\n');q.budget.write('campaign',q.root/'attempts/attempt-01-cases/case-01.json',encoded({'context':context}))
  for d in ['raw','simulation/AP-state','product','android-api','processes']:(case/d).mkdir(parents=True)
  (case/'raw/backend-identity.json').write_bytes(backend);(case/'simulation/AP-state/fixture-state.bin').write_bytes(b'QA_APSTATE_MOCK_NO_EXECUTION\x00')
  resources=object.__new__(OwnedResources);resources.root=case/'processes';resources.digest=q.digest;resources.now=time.monotonic_ns;resources.children={name:types.SimpleNamespace(process=types.SimpleNamespace(pid=n,poll=lambda:0),started_ns=1)for n,name in enumerate(('ap','backend'),1)};resources.closure={'startedNs':2,'finishedNs':3,'children':{name:{'pid':child.process.pid,'exit':0}for name,child in resources.children.items()},'outputCapture':{'EXPLICIT_MOCK':True},'workbenchSealProof':{'EXPLICIT_MOCK_NOT_ACTUAL':True}};resources._completed_closure=resources.closure
  native_file=case/'native-closed.tar';stream=io.BytesIO()
  with tarfile.open(fileobj=stream,mode='w')as t:
   data=b'{"MOCK_NATIVE_NOT_ANDROID":true}';member=tarfile.TarInfo('files/runtime/fixture.json');member.size=len(data);t.addfile(member,io.BytesIO(data))
  native_file.write_bytes(stream.getvalue());native=object.__new__(ProductNativeProbe);native.closed_export={'export':{'path':str(native_file),'bytes':native_file.stat().st_size,'sha256':H(native_file.read_bytes()),'captureComplete':True},'EXPLICIT_MOCK_NOT_ACTUAL':True}
  prefix={str(p.relative_to(q.root)):p.read_bytes()for p in event_original_files(q.root,q.digest)};result=prepare_export(q.budget,resources,context,native);manifest=json.loads(Path(result['manifestPath']).read_bytes());bundle=Path(result['bundlePath']).read_bytes();assert H(bundle)==result['bundleSHA256'];assert manifest['rootRuntimeEventScope']=='EXACT_PRE_EXPORT_COMMITTED_PREFIX_POST_EXPORT_EVENT_AND_SAF_RECEIPTS_SEPARATE';assert manifest['independentAcceptance']=='NOT_YET_COLD_VERIFIED'
  with tarfile.open(fileobj=io.BytesIO(bundle),mode='r:gz')as t:
   for path,data in prefix.items():assert t.extractfile('root-management/'+Path(path).name).read()==data
   assert t.extractfile('raw/backend-identity.json').read()==backend
   assert len([p for p in t.getnames()if p.startswith('root-management/runtime-event-')])==1
  for part in manifest['bundle']['parts']:assert H(bundle[part['offset']:part['offset']+part['bytes']])==part['sha256']
  q.event('SOURCE_RAW_DRAINED_EXPORT_ALLOWED',{'bundleSHA256':result['bundleSHA256']});assert H(Path(result['bundlePath']).read_bytes())==result['bundleSHA256']and len(event_original_files(q.root,q.digest))==3
  try:gzip.decompress(bundle[:-12])
  except(EOFError,OSError):pass
  else:raise AssertionError('TRUNCATED_GZIP_ACCEPTED')
 test('actual-source-gzip-original-detail-and-prefix-SHA-excludes-future-events',gzip_prefix)
 report={'format':'aeris-independent-original-event-detail-references','version':1,'status':'PASS_SOURCE_REALISTIC_EVENT_AND_COLD_PREFIX_NOT_ANDROID_SITL'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourcePins':pins,'sourceOriginalRefs':sourceRefs,'actualOriginalReceiptDataButTiming':'EXPLICIT_FIXTURE_TIMINGS_NOT_ACTUAL_LAUNCH_DURATION','oldEventBytes':len(encoded(oldrow)),'checks':checks,'event8192AndReport32768AndOwner1MiBUnaffected':True,'source64KiBIsStricterSharedPhysicalSubcap':True,'actualActorsStarted':False,'scratchRemoved':str(LAB),'sourceChanged':any(H((R/p).read_bytes())!=h for p,h in pins.items())}
finally:shutil.rmtree(LAB)
n=1
while(out:=E/f'qa/event-refs-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(checks),'failed':[x for x in checks if not x['pass']],'path':str(out)}))
