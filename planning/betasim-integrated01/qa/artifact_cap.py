"""Independent authorized artifact-cap delta and unchanged other guard boundaries."""
from pathlib import Path
import sys,os,json,hashlib,copy
R=Path(__file__).resolve().parents[3];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(R/'planning/betasim-integrated01/runtime/source'),str(R)]
from aeris_runtime import candidate,emulator,host_health,monitor,policy
E=R/'evidence/betasim-integrated01';old=E/'candidates/924d3c6e658f1a89243827f578c9f7d25d1cab79439585a5df843c2a1412b6b4';new=R/'planning/betasim-integrated01/runtime/source/aeris_runtime';H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks=[]
def test(n,fn):
 try:fn();checks.append({'id':n,'pass':True})
 except BaseException as e:checks.append({'id':n,'pass':False,'error':str(e)})
def need(v,m):
 if not v:raise AssertionError(m)
expected=['candidate.py','emulator.py','host_health.py','monitor.py','assets/resource-policy.json'];pins={str((new/n).relative_to(R)):H(new/n)for n in expected}
def exact_delta():
 hold=json.loads((E/'runtime/BUILDER-HOLD-READY03.json').read_text());changed=sorted(n for n,h in hold['sourcePins'].items()if H(R/n)!=h);need(changed==sorted(pins),'UNAUTHORIZED_PATH_CHANGED:'+str(changed))
 for name in expected[:4]:
  before=(old/'source/aeris_runtime'/name).read_text();after=(new/name).read_text()
  pairs={'candidate.py':[('CAP=4*MIB','CAP=8*MIB'),('ARTIFACT4MiB','ARTIFACT8MiB')],'monitor.py':[("'artifactBytes':4*MIB","'artifactBytes':8*MIB")],'emulator.py':[("'artifactBytes':4*2**20","'artifactBytes':8*2**20")],'host_health.py':[("'artifactBytes':4*2**20","'artifactBytes':8*2**20")]}[name]
  for a,b in pairs:before=before.replace(a,b)
  need(before==after,'NON_AUTHORIZED_PYTHON_DELTA:'+name)
test('exact-four-Python-and-one-policy-only-delta',exact_delta)
def exact_policy():
 before=json.loads((old/'source/aeris_runtime/assets/resource-policy.json').read_text());after=json.loads((new/'assets/resource-policy.json').read_text());p=copy.deepcopy(before);delta=4*2**20
 for row in p['cases'].values():
  b=row['budget'];b['categories']['newIsolatedAPKAndArchiveReserve']+=delta;b['taskHardPeakBytes']+=delta;b['requiredFreeBytes']+=delta
 p['campaign']['taskHardPeakBytes']+=delta;p['campaign']['newIsolatedAPKAndArchiveReserve']+=delta
 need(p==after,'OTHER_POLICY_FIELDS_CHANGED')
test('policy-exact-plus4MiB-reserve-derived-no-other-change',exact_policy)
test('candidate-hard-cap-exact8MiB',lambda:need(candidate.CAP==8*2**20,'CAP'))
v={'metadataBytes':0,'exportBytes':0,'AVDPositiveGrowthBytes':0,'artifactBytes':8*2**20,'taskAllocatedBytes':0,'nativePhysicalBytes':0,'nativeLogicalBytes':0,'checkpointArchiveBytes':0,'checkpointArchiveCount':0,'metadataAccountingUpperBoundAtScan':0,'metadataAccountingWriteSequenceAtScan':0}
guards={'guardian':lambda q:emulator._caps(q),'sourceHealth':lambda q:host_health._inventory_counters(q,'monitor'),'resourceMonitor':lambda q:monitor.ResourceMonitor._caps(None,q)}
for name,guard in guards.items():
 test(name+'-accepts-exact8MiB',lambda guard=guard:guard(dict(v)))
 for field,limit in {'artifactBytes':8*2**20,'metadataBytes':64*2**20,'exportBytes':192*2**20,'AVDPositiveGrowthBytes':512*2**20,'taskAllocatedBytes':policy.campaign_budget()['taskHardPeakBytes']}.items():
  def reject(guard=guard,field=field,limit=limit):
   q=dict(v);q[field]=limit+1
   if field=='metadataBytes':q['metadataAccountingUpperBoundAtScan']=limit+1
   try:guard(q)
   except (ValueError,RuntimeError):return
   raise AssertionError('BOUND_WAS_NOT_ENFORCED:'+field)
  test(name+'-rejects-'+field+'-plus1',reject)
for field,limit in {'nativePhysicalBytes':160*2**20,'nativeLogicalBytes':512*2**20,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8}.items():
 def native_reject(field=field,limit=limit):
  q=dict(v);q[field]=limit+1
  try:monitor.ResourceMonitor._caps(None,q)
  except RuntimeError:return
  raise AssertionError('OLD_NATIVE_BOUND_CHANGED')
 test('native-unchanged-'+field+'-plus1',native_reject)
def old_preserved():
 manifest=candidate.load(old,old.name);need(manifest['artifactCapBytes']==4194304,'OLD_MANIFEST_CAP_REWRITTEN');need(manifest['native']['APK_SHA256']=='77c65876eecb6d4fbc68a113bf682fa416c4272b3ed1de71f803c63df58d1b21','OLD_NATIVE_CHANGED');need(candidate.allocated_artifact_union(E/'candidates')==4145152,'ACTOR_OR_NEW_FREEZE_ALREADY_ALLOCATED');need(H(E/'qa/RUNTIME-SOURCE-GATE01.json')=='ee58d82886546173cb392657a74c1d39b3d0d29525c9dc20804f9095169e1968','OLD_GATE_CHANGED')
 raw=(E/'r01/sessions/betasim-short01/android-api/command-stream.raw').read_bytes();need(hashlib.sha256(raw[:38]).hexdigest()=='9282b7d0caa45fef8c244969139121c904c93ce6cf763f6f17a128a786fc4ff6','R01_ORIGINAL_FAILURE_CHANGED');need(H(E/'r01/guardian/health-audit.bin')=='cbc5cf63885e9093a9b08dbe71d68a1812a0d1d10e908f07de31dfbf91719294','R01_ORIGINAL_AUDIT_CHANGED')
test('old924d-gate-native-origin-and-original-r01-failure-prefix-preserved',old_preserved)
report={'format':'aeris-independent-authorized-artifact-cap-delta','version':1,'status':'PASS_AUTHORIZED8MiB_SOURCE_DELTA_NOT_ADMISSION_OR_FREEZE'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourcePins':pins,'checks':checks,'userApprovalSource':'Parent task message explicitly confirms user approved exact PROPOSAL03 artifact4→8MiB; no other guard authority.','artifactAllocationScopeUnchanged':True,'freshness250Lease200AndPhysicsGuardChange':False,'r01Scope':'selected original raw prefix/audit hash plus oldcandidate full load; no new full17117 scan or historical continuity claim','actualActorsOrFreezeByQA':False}
n=1
while(out:=E/f'qa/artifact-cap-{n:02}.json').exists():n+=1
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(checks),'failed':[x for x in checks if not x['pass']],'path':str(out)}))
