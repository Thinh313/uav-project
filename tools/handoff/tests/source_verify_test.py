"""Execute actual Node verifier in a tiny generated repository-shaped fixture."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile
HELPER=Path(__file__).resolve().parents[1]/'verify.mjs'
def run(parent):
 checks=[]
 with tempfile.TemporaryDirectory(prefix='codex-tmp-intake01-20261031-',dir=parent)as scratch:
  base=Path(scratch);root=base/'source';(root/'tools/handoff').mkdir(parents=True);(root/'handoff').mkdir();(root/'tools/handoff/verify.mjs').write_bytes(HELPER.read_bytes());(root/'file').write_bytes(b'fixture');(root/'alias').symlink_to('file');H=lambda b:hashlib.sha256(b).hexdigest();rows=[{'path':'file','kind':'file','bytes':7,'sha256':H(b'fixture')},{'path':'alias','kind':'symlink','bytes':4,'sha256':H(b'file')}]
  def execute(rs,expected,format='uav-project-public-source-manifest'):
   (root/'handoff/SOURCE-MANIFEST.json').write_text(json.dumps({'format':format,'version':1,'files':rs,'privateSourceCommit':'fixture'}));r=subprocess.run(['node','tools/handoff/verify.mjs'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=10);assert(r.returncode==0)is(expected is None),(expected,r.stderr);assert expected is None or expected in r.stderr;checks.append(expected or'valid_regular_and_contained_symlink')
  execute(rows,None);(root/'alias').unlink();(root/'alias').write_bytes(b'file');execute(rows,'SOURCE_KIND_MISMATCH');(root/'alias').unlink();(root/'alias').symlink_to('file')
  outside=base/'outside';outside.mkdir();(outside/'payload').write_bytes(b'fixture');(root/'ext').symlink_to(outside,target_is_directory=True);execute([{'path':'ext/payload',**{k:v for k,v in rows[0].items()if k!='path'}}],'SOURCE_REALPATH_OUTSIDE_REPO')
  execute([{**rows[0],'path':'./file'}],'SOURCE_CANONICAL_RELATIVE_PATH');execute([rows[0],rows[0]],'SOURCE_DUPLICATE_PATH');execute(rows,'SOURCE_MANIFEST_SCHEMA',format='unknown');execute([{**rows[0],'bytes':8}],'SOURCE_SHA256_OR_SIZE_MISMATCH');execute([{**rows[0],'kind':'directory'}],'SOURCE_ROW_SCHEMA')
 assert not Path(scratch).exists()
 return{'format':'uav-public-source-verifier-adversarial-mock','status':'PASS','checks':len(checks),'cases':checks,'scratchRemoved':[scratch],'fixtureOnlyHelperCopied':True,'sourceOrRuntimeAcceptedAsFlight':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scratch-parent',required=True);a=p.parse_args();print(json.dumps(run(a.scratch_parent),sort_keys=True))
