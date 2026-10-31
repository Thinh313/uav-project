from pathlib import Path
import json,hashlib,subprocess,sys,shutil,datetime
ROOT=Path(__file__).resolve().parents[3]
freeze=ROOT/'evidence/integration03/source-ready03.json';f=json.loads(freeze.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=ROOT/'evidence/integration03-qa/qgc-summary03';out.mkdir(exist_ok=False);stage=ROOT/'planning/integration03/qa/.stage';assert not stage.exists();stage.mkdir();result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'NOT_RUN','sourceId':f['sourceId'],'sourceFreezeSha256':sha(freeze),'actualRuntime':False}
try:
 for p,h in f['files'].items():assert sha(ROOT/p)==h,('source drift',p)
 # Assets-only symlink view of pinned overlay, never copy a whole application/project.
 for p,h in f['files'].items():
  if not p.startswith('native/crew02/assets/'):continue
  dest=stage/Path(p).relative_to('native/crew02/assets');dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(ROOT/p)
 for p,h in f['files'].items():
  if not p.startswith('native/integration03/assets/'):continue
  dest=stage/Path(p).relative_to('native/integration03/assets');dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.is_symlink():dest.unlink()
  dest.symlink_to(ROOT/p)
 cmd=['node','--preserve-symlinks',str(ROOT/'planning/integration03/qa/qgc_summary03.mjs'),str(stage),str(ROOT/'evidence/integration03-qa/heldout-corpus01.json')]
 try:r=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=30);stdout,stderr,code=r.stdout,r.stderr,r.returncode
 except subprocess.TimeoutExpired as e:stdout,stderr,code=e.stdout or b'',e.stderr or b'',None
 (out/'stdout.txt').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr);result['command']=cmd
 if code!=0:raise RuntimeError('actual module/mock-DOM failure:'+str(code)+':'+stderr.decode(errors='replace')[-1200:])
 result.update(json.loads(stdout));result['sourceAfterPinsExact']=all(sha(ROOT/p)==h for p,h in f['files'].items())
 if not result['sourceAfterPinsExact']:raise RuntimeError('source mutated during QA')
except Exception as e:result.update(status='FAIL_OR_HARNESS_UNSUPPORTED',error=str(e),errorType=type(e).__name__)
finally:
 shutil.rmtree(stage);result['removedOwnScratch']=[str(stage)];result['runnerSha256']=sha(Path(__file__));result['adapterSha256']=sha(ROOT/'planning/integration03/qa/qgc_summary03.mjs');(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));raise SystemExit(0 if result['status'].startswith('PASS') else 2)
