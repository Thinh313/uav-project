"""Real own readonly-file hardlinks; no old project or candidate inode mutated."""
from pathlib import Path
from unittest.mock import patch
import hashlib,json,os,shutil,stat,sys
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime import candidate as c
LAB=REPO/'evidence/betasim-integrated01/runtime/.immutable';
def deny(f):
 try:f()
 except ValueError:return
 raise AssertionError('not rejected')
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  root=LAB/'new';root.mkdir();pool=LAB/c.OLD15_ARTIFACTS/'objects';pool.mkdir(parents=True);raw=b'unchanged original immutable fixture bytes';h=hashlib.sha256(raw).hexdigest();source=pool/h;source.write_bytes(raw);source.chmod(0o444);before=source.stat()
  with patch.object(c,'repository',return_value=LAB):
   origins,proof=c.immutable_object_plan(root,{h:raw});assert origins[h]==source and proof['objects'][h]['bytes']==len(raw);(root/'objects').mkdir();digest,target=c._object(root/'objects',raw,origins[h]);after=source.stat();assert digest==h and os.path.samefile(source,target)and source.read_bytes()==raw and stat.S_IMODE(after.st_mode)==0o444 and after.st_nlink==before.st_nlink+1;checks.append('exactreadonlyoldpoolinodelinkedwithoutcopy-chmod-or-bytechange')
   bad=b'changed';deny(lambda:c.immutable_object_plan(root,{h:bad}));checks.append('matchingfilenamewrongbytes-or-size-refused')
   writable=b'writable planning must not link';wh=hashlib.sha256(writable).hexdigest();wp=pool/wh;wp.write_bytes(writable);deny(lambda:c.immutable_object_plan(root,{wh:writable}));checks.append('writableoldobjectrefused-before-anynewlink')
   sy=pool/('e'*64);sy.symlink_to(source);deny(lambda:c.immutable_object_plan(root,{'e'*64:raw}));checks.append('symlinkoriginrefused')
   own=root/'new.apk';own.write_bytes(b'new independently held native');nh=hashlib.sha256(own.read_bytes()).hexdigest();origins,proof=c.immutable_object_plan(root,{nh:own.read_bytes()},[(own,own.read_bytes())]);assert origins[nh]==own and stat.S_IMODE(own.stat().st_mode)&0o222;checks.append('preflightnewheldnativeplanperformsNOchmod-or-write')
  report={'status':'PASS_OWN_READONLY_INODE_FIXTURE_NOT_OLD_CANDIDATE_MUTATION','groups':checks,'actualCandidateFrozen':False,'realOldObjectsChanged':False,'oldImmutableHardlinkOnlyRootL2':True}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/immutable-reuse-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
if __name__=='__main__':main()
