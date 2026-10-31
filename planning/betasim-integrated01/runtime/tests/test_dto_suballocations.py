"""Shared original DTO owner, two case namespaces and physical-rounding caps."""
from pathlib import Path
import hashlib,json,os,shutil,sys
from unittest.mock import patch
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime.metadata_budget import MetadataBudget,_product_dto_domain
LAB=REPO/'evidence/betasim-integrated01/runtime/.dtocaps';M=2**20

def deny(f):
 try:f()
 except(ValueError,OSError):return
 raise AssertionError('not refused')
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  b=MetadataBudget(LAB/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();roots=[LAB/'sessions'/s/'product/media'for s in('first','second')]
  for root in roots:b.write('dto',root/'video-launch.json',b'{}\n')
  a=roots[0]/('video-'+'a'*36+'-proof-s01.ajz01');b.write('dto',a,b'x'*(11*M//2-4096));before=b.snapshot();bad=roots[1]/('video-'+'b'*36+'-proof-s01.ajz01');deny(lambda:b.write('dto',bad,b'z'*8192));after=b.snapshot();assert not bad.exists()and before['productDTOAllocatedBytes']==after['productDTOAllocatedBytes']and before['writes']==after['writes'];checks.append('sourceProof5.5MiB-shared-across-two-cases-denied-before-write')
  jpg=roots[0]/('capture-'+'a'*36+'-original.jpg');b.write('dto',jpg,b'j'*M);deny(lambda:b.write('dto',roots[1]/('capture-'+'b'*36+'-original.jpg'),b'j'));checks.append('JPEG1MiB-aggregate-no-new-case-reset')
  replay=roots[0]/('replay-'+'e'*64+'.json.gz');b.write('dto',replay,b'r'*(256*1024-4096));b.write('dto',roots[1]/('replay-'+'f'*64+'.json.gz'),b'r');deny(lambda:b.write('dto',roots[1]/('replay-'+'f'*64+'.json.gz'),b'r'*4096,append=True));checks.append('replay256KiB-counts-physical4KiB-rounding')
  for name,expected in[('video-'+'c'*36+'-report-01.json',('reports',4*M)),('capture-'+'d'*36+'-sidecar.json',('auxiliaryMediaMetadata',512*1024))]:assert _product_dto_domain(roots[0]/name,LAB,'dto')==expected
  assert _product_dto_domain(LAB/'sessions/first/android-api/objects'/('d'*64),LAB,'dto')is None;checks.append('source-path-domains-distinguish-reports-aux-and-native-status-owner')
  state=b.snapshot();assert state['remaining']['dto']>=0 and sum(state['productDTOAllocatedBytes'].values())<=15*M;checks.append('suballocations-never-increase-original15MiB-owner-or-add-an-owner')
  journal=LAB/'sessions/first/product/journal';b.write('lifecycle',journal/'other.jsonl',b'{}\n');clock=journal/('media-clock-'+'a'*36+'-s01.ajz01');b.write('lifecycle',clock,b'c'*(768*1024));deny(lambda:b.write('lifecycle',journal/('media-clock-'+'b'*36+'-s01.ajz01'),b'c'));assert b.snapshot()['productLifecycleAllocatedBytes']['mediaClock']==768*1024;checks.append('clock768KiB-physical-shared-lifecycle-subcap-never-DTO-or-new-owner')
  report={'status':'PASS_SHARED_SOURCE_DTO_MOCK_NOT_ANDROID','groups':checks,'sourceCapsBytes':{'proof':11*M//2,'reports':4*M,'JPEG':M,'replay':256*1024,'aux':512*1024},'actualActors':False}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/dto-suballocation-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
if __name__=='__main__':main()
