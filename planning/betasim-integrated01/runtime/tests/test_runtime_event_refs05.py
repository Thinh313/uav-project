"""Source-realistic R02 launch payloads, lossless event references, no actors."""
from pathlib import Path
from unittest.mock import patch
import ast,hashlib,json,os,shutil,sys
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)];os.environ['AERIS_REPOSITORY_ROOT']=str(REPO)
from aeris_runtime.product_runtime import WorkbenchRuntime,event_original_files
from aeris_runtime.metadata_budget import MetadataBudget,encoded,observer_envelope
from aeris_runtime.candidate import load
LAB=REPO/'evidence/betasim-integrated01/runtime/.eventrefs05'
ACTUAL=REPO/'evidence/betasim-integrated01/r02';CASE=ACTUAL/'sessions/betasim-short02'

def rawref(ref):
 p=Path(ref['path']);raw=p.read_bytes()[ref['offset']:ref['offset']+ref['bytes']];assert len(raw)==ref['bytes']and hashlib.sha256(raw).hexdigest()==ref['sha256'];return raw
def deny(fn,phrase):
 try:fn()
 except(RuntimeError,ValueError,OSError)as e:
  assert phrase in str(e),str(e);return
 raise AssertionError('accepted '+phrase)
def owner(name):
 root=LAB/name;root.mkdir();b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();o=WorkbenchRuntime.__new__(WorkbenchRuntime);o.root=root;o.budget=b;o.events=0;o.digest='a'*64;return o

def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  backend_raw=(CASE/'raw/backend-identity.json').read_bytes();ap_raw=(CASE/'raw/ap-supervisor-launch.json').read_bytes();queries=[json.loads(x)for x in(CASE/'host-queries/queries.jsonl').read_bytes().splitlines()];info=json.loads(rawref(queries[2]['stdoutRef']))[0];exe=rawref(queries[3]['stdoutRef']).decode().split()[0]
  receipt={'backendReady':True,'APReady':True,'backend':json.loads(backend_raw),'AP':json.loads(ap_raw),'containerImage':info['Image'],'containerID':info['Id'],'actualAPExecutableSHA256':exe,'backendTiming':{'startHostNs':10000000000000,'readyHostNs':10015000000000,'gateSeconds':40},'APTiming':{'startHostNs':10015000000000,'readyHostNs':10016000000000,'gateSeconds':12},'wholeColdStartClaimed10s':False}
  oldrow={'format':'aeris-product-runtime-event','version':1,'sequence':1,'hostNs':10016000000000,'kind':'ROOT_AP_READY','detail':receipt,'candidateSHA256':'a'*64,'flightAcceptance':False};o=owner('normal');before=o.budget.snapshot()['writes'];deny(lambda:o.budget.append_json('external_task',o.root/'reports/old-rejected.jsonl',oldrow,maximum=8192),'METADATA_JSON_SOURCE_BOUND');assert o.budget.snapshot()['writes']==before;checks.append('originalR02-backend-AP-querybytes-SHAverified-declared-fixture-timings-reproduce-old8192-failure-beforewrite')
  o.event('ROOT_AP_READY',receipt);event=json.loads((o.root/'reports/runtime-events.jsonl').read_bytes());ref=event['detailRef'];payload_raw=(o.root/ref['path']).read_bytes();assert len(payload_raw)==ref['bytes']and hashlib.sha256(payload_raw).hexdigest()==ref['sha256'];payload=json.loads(payload_raw);assert payload['detail']==receipt and event['sequence']==payload['sequence']and event['kind']==payload['kind']and event['hostNs']==payload['hostNs']and event['candidateSHA256']==payload['candidateSHA256'];assert len(encoded(event))<8192 and 8192<len(payload_raw)<=32768;checks.append('full-realistic-launch-receipt-durable-before-event-exactlossless-ref-no-truncation-or-capincrease')
  for value in(None,{'APStarted':False,'readinessRef':{'sha256':'b'*64,'bytes':100}},{'guardAdmission':{'big':'x'*20000}}):
   o.event('GENERIC_AUDIT',value);row=json.loads((o.root/'reports/runtime-events.jsonl').read_bytes().splitlines()[-1]);assert json.loads((o.root/row['detailRef']['path']).read_bytes())['detail']==value
  checks.append('uniform-small-null-and-large-eventdetails-exactroundtrip-sourceidentity')
  originals=event_original_files(o.root,o.digest);assert len(originals)==5;detail=o.root/ref['path'];saved=detail.read_bytes();detail.write_bytes(saved[:-1]+b'x');deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_DETAIL_SHA_OR_AGGREGATE');detail.write_bytes(saved);journal=o.root/'reports/runtime-events.jsonl';rows=journal.read_bytes().splitlines();bad=json.loads(rows[0]);bad['detailRef']['path']='reports/runtime-event-002-detail.json';journal.write_bytes(encoded(bad)+b'\n'.join(rows[1:])+b'\n');deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_EXACT_DETAIL_REF');journal.write_bytes(b'\n'.join(rows)+b'\n');assert event_original_files(o.root,o.digest)==originals;orphan=o.root/'reports/runtime-event-099-detail.json';orphan.write_bytes(b'{}');deny(lambda:event_original_files(o.root,o.digest),'EVENT_ORIGINAL_UNREFERENCED_DETAIL');orphan.unlink();checks.append('coldreader-follows-exactoriginal-detailrefs-rejects-tamperedbytes-and-wrongref')
  q=owner('aggregate');q.budget.write('external_task',q.root/'reports/other.json',b'{}');q.budget.write('external_task',q.root/'reports/runtime-event-001-detail.json',b'x'*32768);q.budget.write('external_task',q.root/'reports/runtime-event-002-detail.json',b'x'*32768);q.events=2;assert q.budget.snapshot()['runtimeEventDetailAllocatedBytes']==65536;before=q.budget.snapshot()['writes'];q.case={'context':{'run':'SECOND_CASE'}};deny(lambda:q.event('CASE_CREATED',{}),'RUNTIME_EVENT_DETAILS_TASK64KiB_ALLOCATED');assert not(q.root/'reports/runtime-events.jsonl').exists()and q.budget.snapshot()['writes']==before;checks.append('strict64KiB-physical-taskaggregate-within1MiB-no-secondcase-reset-rejectsbeforewrite')
  q=owner('overquota')
  with q.budget._locked():
   state=q.budget._state();state['remaining']['external_task']=0;q.budget._save(state)
  deny(lambda:q.event('ROOT_AP_READY',receipt),'METADATA_OWNER_WORST_CASE_EXHAUSTED');assert not(q.root/'reports/runtime-events.jsonl').exists();checks.append('ownerquota-denies-before-event-no-reference-to-undurable-payload')
  q=owner('eio')
  with patch.object(q.budget,'write',side_effect=OSError('INJECTED_EIO')):deny(lambda:q.event('ROOT_AP_READY',receipt),'INJECTED_EIO')
  assert not(q.root/'reports/runtime-events.jsonl').exists();checks.append('payload-EIO-no-event-no-retry')
  q=owner('too-big');deny(lambda:q.event('ROOT_AP_READY',{'oversize':'x'*32768}),'REPORT_SOURCE_BOUND');assert not(q.root/'reports/runtime-events.jsonl').exists();checks.append('unchanged32KiB-report-bound-refuses-oversize-no-silentdrop')
  tree=ast.parse((R/'source/aeris_runtime/product_runtime.py').read_bytes());entry=ast.parse((R/'root-owner-ready02.py').read_bytes());event_names=sorted({call.args[0].value for source in(tree,entry)for call in ast.walk(source)if isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute)and call.func.attr=='event'and call.args and isinstance(call.args[0],ast.Constant)})
  success=[call for call in ast.walk(entry)if isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute)and call.func.attr=='write'and call.args and isinstance(call.args[0],ast.Constant)and call.args[0].value=='owner-terminal.json'];assert len(success)==1;keys={key.value for key in success[0].args[1].keys};assert not {'scenario','handoff','closure','guardian'}&keys and {'scenarioStatus','handoffStatus','caseClosurePath','guardianClosurePath'}<=keys;checks.append('all-runtime-and-selected-entry-events-normalized-success-ownerterminal-only-smallstatuses-and-originalpaths')
  manifests=[]
  for digest in('924d3c6e658f1a89243827f578c9f7d25d1cab79439585a5df843c2a1412b6b4','4ce68ada8ca0abb57d4fd11e6b5907f620623442ef7ce701a3fa4f76551737c8'):
   load(REPO/'evidence/betasim-integrated01/candidates'/digest,digest);manifests.append(digest)
  assert observer_envelope()['owners']['external_task']==2**20;checks.append('both-oldrelease-fulltransitive-loads-stillpass-original1MiB-owner-and-event8192-report32768-unchanged')
  report={'format':'aeris-runtime-event-reference-source-mock','status':'PASS_SOURCE_REALISTIC_PAYLOAD_MOCK_NOT_ANDROID_SITL','groups':checks,'mockTimingNotActualReceiptTiming':True,'actualOriginalPayloadRefs':[{'path':str(p.relative_to(REPO)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in(CASE/'raw/backend-identity.json',CASE/'raw/ap-supervisor-launch.json')],'oldRejectedEventBytes':len(encoded(oldrow)),'newEventBytes':len(encoded(event)),'losslessDetailBytes':len(payload_raw),'allAuditedEventKinds':event_names,'oldReleaseLoads':manifests,'actorsStarted':False,'capsChanged':False,'scratchRemoved':str(LAB.relative_to(REPO))}
 finally:shutil.rmtree(LAB)
 p=REPO/'evidence/betasim-integrated01/runtime/event-reference-mock05-final03.json';assert not p.exists();p.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
