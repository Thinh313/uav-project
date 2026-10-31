from pathlib import Path
import json,hashlib,sys,os,tempfile,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2];os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.path.insert(0,str(ROOT.parent/'02_Refinery_MethodBox'))
import refinery,bites
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)});assert ok,name
root=ROOT/'research/protocol22'
for s in json.loads((root/'sources.json').read_text()):check('Original protocol snapshot '+s['id'],sha(root/'snapshots'/s['snapshot'])==s['sha256'])
headers=json.loads((ROOT/'reference/protocol22/headers.json').read_text());check('All22 C/XML commit-pinned source hashes',len(headers['files'])==22 and all(sha(ROOT/f['path'])==f['sha256'] and headers['commit'] in f['url'] for f in headers['files']))
cfg,claims,registry,agg,canonical=refinery.run_pipeline(str(root));(root/'registry.json').write_bytes(canonical+b'\n');check('Clean registry, idempotence and derivation audit',len(claims)==4)
removed=[]
for name,fn in bites.BITES:
 if name=='DISTRIBUTION_NO_DENOMINATOR':continue
 temp=Path(tempfile.mkdtemp(prefix='codex-tmp-aeris-protocol22-20261013-'));dst=temp/'domain'
 try:
  shutil.copytree(root,dst)
  if name=='CAPTURE_MISSING':
   (dst/'snapshots'/claims[0]['capture']['snapshot']).unlink();bit,last=bites._expect_bite(dst,name)
  else:bit,last=fn(dst)
  if bit is not None:check('Applicable Refinery negative '+name,bit)
 finally:shutil.rmtree(temp);removed.append(str(temp))
check('Temporary domain copies removed',all(not p.exists() for p in map(Path,removed)))
freeze=json.loads((ROOT/'evidence/endure20/freeze.json').read_text());check('All140 frozen source payload files exact',len(freeze['files'])==140 and all(sha(ROOT/f['path'])==f['sha256'] for f in freeze['files']))
ctrl=json.loads((ROOT/'evidence/endure20/controller-pins.json').read_text());check('All5 frozen controller helpers exact',len(ctrl['files'])==5 and all(sha(ROOT/p)==h for p,h in ctrl['files'].items()))
old=json.loads((ROOT/'evidence/payload21/module-fingerprints.json').read_text());check('All25 PAYLOAD21 module files exact',len(old['files'])==25 and all(sha(ROOT/p)==h for p,h in old['files'].items()))
baseline=json.loads((ROOT/'evidence/endure20/source-manifest.json').read_text());check('All2009 prior tracked source bytes exact',all(sha(ROOT/p)==h for p,h in baseline['files'].items()))
check('Original canonical SOT fact bytes unchanged',all(sha(ROOT/p)==baseline['files'][p] for p in ['sot/source_canonical/product_truth.json','sot/source_canonical/hera_context.json','sot/source_canonical/0.BOM26.xlsx']))
data=json.loads((ROOT/'evidence/endure20/original-snapshot.json').read_text());candidate=json.loads((ROOT/'evidence/endure20/candidate.json').read_text());check('Original664 files and active generation copy intact',len(data['files'])==664 and all(sha(root/f['path'])==f['sha256'] for root in [ROOT/'runtime',Path(candidate['dataRoot'])] for f in data['files']))
actual=json.loads((ROOT/'evidence/endure20/progress.json').read_text());check('Soak continues with same candidate/manifest and0errors',actual['status']=='RUNNING_NOT_FINAL' and actual['manifestSha256']==candidate['manifestSha256'] and actual['totals']['errors']==0)
receipt={'checks':checks,'removed':removed,'notApplicable':['Distribution denominator/domain-specific unspecified gates'],'scope':'Capture/source/data endpoint hash preservation and applicable deterministic negatives, not hardware/protocol causality or24h acceptance','soak':{'status':actual['status'],'checkedAt':actual['checkedAt'],'elapsedMs':actual['elapsedMs'],'errors':actual['totals']['errors']}}
(ROOT/'evidence/protocol22/sources-qa.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
