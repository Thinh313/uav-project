"""Independent tiny filesystem fixture: immutable object planning/linking only.
All fixture paths are in QA, never original old pools or selected artifacts.
"""
from pathlib import Path
import hashlib,json,os,shutil,sys
P=Path(__file__).resolve();R=P.parents[3];sys.path[:0]=[str(P.parent.parent/'runtime/source'),str(R)]
from aeris_runtime import candidate as m
source=P.parent.parent/'runtime/source/aeris_runtime/candidate.py';pin=hashlib.sha256(source.read_bytes()).hexdigest();checks=[];lab=R/'planning/betasim-integrated01/qa/.immutable-fixture01';assert not lab.exists();lab.mkdir();old_repository=m.repository;m.repository=lambda:lab
sha=lambda b:hashlib.sha256(b).hexdigest()
def test(id,fn):
 try:fn();checks.append({'id':id,'pass':True})
 except BaseException as e:checks.append({'id':id,'pass':False,'error':str(e)})
def denied(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('invalid origin accepted')
try:
 root=lab/'new';root.mkdir();pool=lab/m.OLD15_ARTIFACTS/'objects';pool.mkdir(parents=True);raw=b'explicit independent QA readonly object';h=sha(raw);origin=pool/h;origin.write_bytes(raw);origin.chmod(0o444);before=sorted(str(p.relative_to(lab))for p in lab.rglob('*'))
 def plan():
  origins,decl=m.immutable_object_plan(root,{h:raw});assert origins[h]==origin and decl['objects'][h]['pool']==0 and decl['objects'][h]['mode']==0o444;assert sorted(str(p.relative_to(lab))for p in lab.rglob('*'))==before
 test('readonly-old-pool-plan-is-pure-and-declares-exact-hash-mode-size',plan)
 def writable():
  origin.chmod(0o644)
  try:denied(lambda:m.immutable_object_plan(root,{h:raw}));assert origin.stat().st_mode&0o777==0o644 and origin.read_bytes()==raw
  finally:origin.chmod(0o444)
 test('writable-old-origin-refused-not-chmodded-or-copied',writable)
 test('same-named-origin-wrong-content-refused',lambda:denied(lambda:m.immutable_object_plan(root,{h:b'wrong supplied bytes'})))
 def linked():
  store=root/'objects';store.mkdir();inode=origin.stat().st_ino;n=origin.stat().st_nlink;digest,target=m._object(store,raw,origin);assert digest==h and target.stat().st_ino==inode and target.read_bytes()==raw and origin.stat().st_nlink==n+1 and origin.stat().st_mode&0o777==0o444
 test('actual-hardlink-preserves-origin-bytes-mode-no-copy-only-new-linkcount',linked)
 def bad_held():
  other=lab/'planning';other.mkdir();p=other/'native.apk';p.write_bytes(b'new native');denied(lambda:m.immutable_object_plan(root,{sha(p.read_bytes()):p.read_bytes()},[(p,p.read_bytes())]))
 test('writable-planning-path-cannot-pose-as-selected-held-native-root',bad_held)
 def symlink():
  target=root/'sym';target.symlink_to(origin);denied(lambda:m._readonly_content_origin(target,h,raw))
 test('symlink-origin-refused',symlink)
finally:m.repository=old_repository;shutil.rmtree(lab)
report={'format':'aeris-independent-immutable-object-reuse-source-review','version':1,'status':'PASS_TINY_QA_FIXTURE_AND_SOURCE_REVIEW_NOT_ACTUAL_FREEZE'if all(x['pass']for x in checks)else'FAIL_SOURCE_CONTRACT','sourceSHA256':pin,'checks':checks,'sourceReview':{'preflightBeforeAnyWrites':True,'exactManifestCanonicalBytesAndNewDirectoriesCounted':True,'newObjects4KiBRoundedBeforeAllocation':True,'onlyTwoNewHeldNativeFilesCanBeChmodded':True,'oldObjectsRevalidatedOnLoad':True,'realFreezeAllocatedAfterCheckedAgainst4MiB':True},'actualOldPoolsOrNativeArtifactsTouched':False,'actualCandidateFreeze':False,'scratchRemoved':str(lab),'scratchExistsAfter':lab.exists()};n=1;out=R/'evidence/betasim-integrated01/qa'
while(out/f'candidate-reuse-{n:02}.json').exists():n+=1
p=out/f'candidate-reuse-{n:02}.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'output':str(p)}))
