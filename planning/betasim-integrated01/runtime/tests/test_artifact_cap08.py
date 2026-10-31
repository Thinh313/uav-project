"""Explicit approved artifact-only cap change, typed boundary and full old-release read."""
from pathlib import Path
import ast,copy,hashlib,json,os,sys
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)];os.environ['AERIS_REPOSITORY_ROOT']=str(REPO)
from aeris_runtime import candidate,policy
from aeris_runtime.monitor import ResourceMonitor
from aeris_runtime.emulator import _caps
from aeris_runtime.host_health import _inventory_counters
from aeris_runtime.metadata_budget import observer_envelope,encoded
M=2**20;OLD=REPO/'evidence/betasim-integrated01/candidates/924d3c6e658f1a89243827f578c9f7d25d1cab79439585a5df843c2a1412b6b4'
def deny(fn):
 try:fn()
 except(RuntimeError,ValueError):return
 raise AssertionError('accepted invalidcap')
def main():
 checks=[];assert candidate.CAP==8*M
 v={'metadataBytes':0,'metadataAccountingUpperBoundAtScan':0,'metadataAccountingWriteSequenceAtScan':0,'exportBytes':0,'AVDPositiveGrowthBytes':0,'artifactBytes':8*M,'taskAllocatedBytes':0,'nativePhysicalBytes':0,'nativeLogicalBytes':0,'checkpointArchiveBytes':0,'checkpointArchiveCount':0}
 monitor=ResourceMonitor.__new__(ResourceMonitor)
 for check in(monitor._caps,_caps,lambda x:_inventory_counters(x,'guardian')):
  check(v.copy())
  for value in(8*M+1,True,-1,8.0*M):deny(lambda:check({**v,'artifactBytes':value}))
  for key,limit in [('metadataBytes',64*M),('exportBytes',192*M),('AVDPositiveGrowthBytes',512*M)]:deny(lambda:check({**v,key:limit+1,'metadataAccountingUpperBoundAtScan':65*M}))
 checks.append('all-three-live-inventory-guards-accept8MiB-reject-overflow-bool-negative-float-other-originalcaps-unchanged')
 old=json.loads((OLD/'source/aeris_runtime/assets/resource-policy.json').read_bytes());new=json.loads((R/'source/aeris_runtime/assets/resource-policy.json').read_bytes());expected=copy.deepcopy(old);expected['campaign']['newIsolatedAPKAndArchiveReserve']+=4*M;expected['campaign']['taskHardPeakBytes']+=4*M
 for name,row in expected['cases'].items():
  b=row['budget'];b['categories']['newIsolatedAPKAndArchiveReserve']+=4*M;b['taskHardPeakBytes']+=4*M;b['requiredFreeBytes']+=4*M
  live=policy.case_budget(maximum_seconds=int(name));assert live['taskHardPeakBytes']==b['taskHardPeakBytes']and live['requiredFreeBytes']==b['requiredFreeBytes'];assert policy.case_budget(b['requiredFreeBytes']-1,int(name))['admitted']is False and policy.case_budget(b['requiredFreeBytes'],int(name))['admitted']is True
 assert new==expected and policy.campaign_budget()['taskHardPeakBytes']==expected['campaign']['taskHardPeakBytes'];checks.append('JSON-only-approved-reserve-and-derived-peaks-freebudget-plus4MiB-with-exact-admission-boundaries')
 for name,oldtext,newtext in [('candidate.py','MIB=2**20;CAP=4*MIB;','MIB=2**20;CAP=8*MIB;'),('monitor.py',"'artifactBytes':4*MIB","'artifactBytes':8*MIB"),('emulator.py',"'artifactBytes':4*2**20","'artifactBytes':8*2**20"),('host_health.py',"'artifactBytes':4*2**20","'artifactBytes':8*2**20")]:
  before=(OLD/'source/aeris_runtime'/name).read_text();after=(R/'source/aeris_runtime'/name).read_text();want=before.replace(oldtext,newtext)
  if name=='candidate.py':want=want.replace('CANDIDATE_PREFLIGHT_ARTIFACT4MiB_DISK10GiB','CANDIDATE_PREFLIGHT_ARTIFACT8MiB_DISK10GiB').replace('ARTIFACT4MiB_FAILED_PREFIX_RETAINED','ARTIFACT8MiB_FAILED_PREFIX_RETAINED')
  assert want==after,name;ast.parse(after,name)
 checks.append('fourPython-byte-deltas-only-approved-artifactcap-and-truthful-errorlabel')
 b=observer_envelope();assert b['owners']['dto']==15*M and b['owners']['lifecycle']==8*M and b['totalFutureBytes']==60686336 and b['maximumRequests']==900 and b['maximumCommands']==3700;assert policy.DISK_POLICY['floorBytes']==10*2**30 and policy.DISK_POLICY['reserveBytes']==256*M;checks.append('metadata-counters-physical-resource-floors-and-all-nonartifact-source-numbers-identical')
 candidate.load(OLD,OLD.name);actual=candidate.allocated_artifact_union(OLD.parent);assert actual==4145152;checks.append('old924d-full-transitive-source-load-and-original-physicalunion-unchanged-no-newartifact')
 report={'format':'aeris-approved-artifact8-source-boundary-mock','status':'PASS_SOURCE_ONLY_NOT_FREEZE_OR_ANDROID_ADMISSION','groups':checks,'artifactCapBytes':8*M,'deltaBytes':4*M,'oldCandidate924dLoad':'PASS','measuredActualInodeUnionBytes':actual,'actorsStarted':False,'newSignatures':False,'newCandidateFrozen':False,'scope':'Source typed caps and budget arithmetic; no actual capacity allocation or flightacceptance.'};p=REPO/'evidence/betasim-integrated01/runtime/artifact8-boundary-mock01.json';assert not p.exists();p.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
