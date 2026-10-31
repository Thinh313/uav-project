"""Source-owned closure gate + actual lossless gzip export, no simulator actor."""
from pathlib import Path
from types import SimpleNamespace
import gzip,hashlib,io,json,os,shutil,sys,tarfile,time
from unittest.mock import patch
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=ROOT.parents[2];sys.path[:0]=[str(ROOT/'source'),str(REPO)]
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.resources import OwnedResources
from aeris_runtime.raw_export import prepare_export
from aeris_runtime.product_native import ProductNativeProbe
from aeris_runtime.product_runtime import WorkbenchRuntime
LAB=REPO/'evidence/betasim-integrated01/runtime/.rawexport';C={'run':'mock','epoch':'e','boot':'b','operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'}
def fixture(name):
 root=LAB/name;root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();b.tick('cases');(root/'reports').mkdir();(root/'reports/native-producer-01-registration.json').write_bytes(b'{"mock":true}\n');(root/'reports/product-clock-proofs.jsonl').write_bytes(b'{"mock":true}\n');b.write('campaign',root/'attempts/attempt-01-cases/case-01.json',(json.dumps({'context':C})+'\n').encode());case=root/'sessions/mock';(case/'raw/journal').mkdir(parents=True);(case/'product').mkdir();(case/'android-api').mkdir();(case/'processes').mkdir();(case/'simulation/AP-state').mkdir(parents=True);(case/'raw/journal/segment-000000.jsonl').write_bytes(b'ORIGINAL\x00'+os.urandom(2048));(case/'simulation/AP-state/log.bin').write_bytes(b'APSTATE'+os.urandom(2048));r=object.__new__(OwnedResources);r.root=case/'processes';r.digest='a'*64;r.now=time.monotonic_ns;r.children={k:SimpleNamespace(process=SimpleNamespace(pid=i,poll=lambda:0),started_ns=1)for i,k in enumerate(('ap','backend'),1)};r.closure={'startedNs':2,'finishedNs':3,'children':{k:{'pid':v.process.pid,'exit':0}for k,v in r.children.items()},'outputCapture':{'mock':True},'workbenchSealProof':{'mockFixtureNotActual':True}};r._completed_closure=r.closure;native_path=case/'native-closed.tar';native_path.write_bytes(b'NATIVE_FULL_FILES_MOCK_NOT_REAL_TAR');native=object.__new__(ProductNativeProbe);native.closed_export={'export':{'path':str(native_path),'bytes':native_path.stat().st_size,'sha256':hashlib.sha256(native_path.read_bytes()).hexdigest(),'captureComplete':True},'mockFixtureNotActual':True};r.native_fixture=native;o=WorkbenchRuntime.__new__(WorkbenchRuntime);o.root=root;o.budget=b;o.events=0;o.digest=r.digest;o.event('ROOT_AP_READY',{'actualFixtureNotFlight':True,'deep':'x'*17000});return b,r,case

def main():
 assert not LAB.exists();LAB.mkdir(parents=True);groups=[]
 try:
  b,r,case=fixture('ok');original={str(p.relative_to(case)):p.read_bytes()for root in(case/'raw',case/'simulation/AP-state')for p in root.rglob('*')if p.is_file()};ref=prepare_export(b,r,C,r.native_fixture);manifest=json.loads(Path(ref['manifestPath']).read_bytes());bundle=Path(ref['bundlePath']).read_bytes();assert hashlib.sha256(bundle).hexdigest()==ref['bundleSHA256'];assert sum(p['bytes']for p in manifest['bundle']['parts'])==len(bundle)
  for part in manifest['bundle']['parts']:assert hashlib.sha256(bundle[part['offset']:part['offset']+part['bytes']]).hexdigest()==part['sha256']
  with tarfile.open(fileobj=io.BytesIO(bundle),mode='r:gz')as tar:
   assert set(tar.getnames())=={'closed-raw-manifest.json',*original,'root-management/native-producer-01-registration.json','root-management/product-clock-proofs.jsonl','root-management/runtime-events.jsonl','root-management/runtime-event-001-detail.json'};inside=json.loads(tar.extractfile('closed-raw-manifest.json').read());assert inside['independentAcceptance']=='NOT_YET_COLD_VERIFIED';assert all(tar.extractfile(name).read()==data for name,data in original.items());assert tar.extractfile('root-management/runtime-event-001-detail.json').read()==(b.evidence/'reports/runtime-event-001-detail.json').read_bytes();assert inside['rootRuntimeEventScope']=='EXACT_PRE_EXPORT_COMMITTED_PREFIX_POST_EXPORT_EVENT_AND_SAF_RECEIPTS_SEPARATE'
  assert b.snapshot()['exports']['sessions/mock/product-full-raw.tar.gz']['closed'];groups.append('exact-raw-andAPstate-byte-coverage-gzip-SHA-parts-sourceclosed-not-independentPASS')
  try:gzip.decompress(bundle[:-12]);raise AssertionError('truncation accepted')
  except(EOFError,OSError):pass
  groups.append('truncated-fullbundle-refused')
  b,r,case=fixture('open');r._completed_closure=None
  try:prepare_export(b,r,C,r.native_fixture);raise AssertionError('open source accepted')
  except RuntimeError:pass
  assert not(case/'product-full-raw.tar.gz').exists();groups.append('noncompleted-originalsourceclosure-zeroexport')
  b,r,case=fixture('cap')
  with patch('aeris_runtime.raw_export.MAX_EXPORT',1024):
   try:prepare_export(b,r,C,r.native_fixture);raise AssertionError('oversized export accepted')
   except ValueError as e:assert 'STREAM_LIMIT'in str(e),str(e)
  assert(case/'product-full-raw.tar.gz').exists()and not(case/'product/reports/closed-raw-export.json').exists();groups.append('downward-cap-fault-retains-partial-without-publicmanifest-orretry')
  out={'status':'PASS_RAW_EXPORT_SOURCE_CLOSURE_MOCK_NOT_ANDROID','groups':groups,'actualAndroidAP':False,'sourceClosureFixture':'IN_MEMORY_MOCK_NOT_ACTUAL_PROCESS_PROOF','scratchRemoved':str(LAB)}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/raw-export-events05-mock03.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'groups':len(groups)}))
if __name__=='__main__':main()
